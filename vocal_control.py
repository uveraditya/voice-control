import os
import subprocess
import time
import io
import requests
import pyautogui
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import threading  # Ditambahkan untuk menangani thread skrol di latar belakang
import datetime
import json

# Variabel global untuk menyimpan status perintah terakhir (untuk fitur "lagi")
last_command_type = None
# Variabel global tambahan
is_scrolling_continuous = False
scroll_thread = None

# --- FUNGSI OUTPUT SUARA MENGGUNAKAN VOICEVOX API (BAHASA JEPANG) ---
def speak_response(message):
    print(f"[VOICEVOX Response]: {message}")
    try:
        # ID Speaker untuk Shikoku Metan (Normal) di VOICEVOX adalah 2
        speaker_id = 2  
        
        # 1. Membuat Audio Query ke server lokal VOICEVOX
        query_url = f"http://localhost:50021/audio_query"
        params = {"text": message, "speaker": speaker_id}
        query_res = requests.post(query_url, params=params)
        
        if query_res.status_code != 200:
            print("Gagal membuat query VOICEVOX, pastikan aplikasi VOICEVOX sedang dibuka.")
            return
            
        query_data = query_res.json()

        # 2. Melakukan sintesis suara menjadi file audio WAV
        synthesis_url = f"http://localhost:50021/synthesis"
        synth_params = {"speaker": speaker_id}
        synth_res = requests.post(synthesis_url, params=synth_params, json=query_data)
        
        if synth_res.status_code == 200:
            # 3. Memutar audio hasil sintesis menggunakan sounddevice
            audio_stream = io.BytesIO(synth_res.content)
            samplerate, data = wav.read(audio_stream)
            sd.play(data, samplerate)
            sd.wait()
        else:
            print("Gagal melakukan sintesis audio VOICEVOX.")
            
    except Exception as e:
        print(f"Gagal terhubung ke server VOICEVOX (Pastikan aplikasi VOICEVOX menyala): {e}")

# --- FUNGSI OLLAMA UNTUK MENGAMBIL JAWABAN DAN MEMBACAKANNYA ---
def ask_ollama_and_speak(model_name, prompt_text):
    print(f"Mengirim prompt ke model {model_name}...")
    try:
        # Mengirim permintaan ke API lokal Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt_text,
                "stream": False # Diubah menjadi False agar JSON response terbaca utuh
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            answer_text = result.get("response", "")
            print(f"Jawaban Ollama: {answer_text}")
            
            # Suarakan jawaban menggunakan VOICEVOX
            speak_response(answer_text)
        else:
            speak_response("オラマからの応答を取得できませんでした。")
    except Exception as e:
        print(f"Error koneksi ke Ollama: {e}")
        speak_response("オラマとの接続に失敗しました。")
        
# --- FUNGSI ANALISIS PASAR (MODE INTERAKTIF SEPERTI KAIWA) ---
def analyze_market_json(file_path, model_name="qwen3:8b"):
    print(f"Membaca data pasar dari {file_path}...")
    try:
        if not os.path.exists(file_path):
            speak_response("ファイルが見つかりませんでした。")
            print(f"File {file_path} tidak ditemukan.")
            return

        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            
        # Format data JSON menjadi string untuk konteks sistem
        data_string = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        speak_response("市場分析モードを開始します。経済データについて何でも聞いてください！")
        print("\n--- Memulai Mode Analisis Pasar Interaktif (Katakan 'stop', 'selesai', atau 'keluar' untuk kembali) ---")
        
        # Inisialisasi riwayat percakapan dengan role system pakar ekonomi
        market_history = [
            {
                "role": "system", 
                "content": (
                    "Anda adalah seorang pakar ekonomi profesional dan analis pasar yang berpengalaman. "
                    "Anda memiliki akses ke data pasar berikut:\n\n"
                    f"{data_string}\n\n"
                    "Rules:\n"
                    "1. Jawab pertanyaan pengguna berdasarkan data pasar di atas secara mendalam, objektif, dan komprehensif.\n"
                    "2. Berikan wawasan mengenai tren, risiko, peluang, serta rekomendasi strategis.\n"
                    "3. Berikan respons dalam bahasa Indonesia yang profesional namun mudah dipahami."
                )
            },
            {
                "role": "assistant",
                "content": "Halo! Saya telah membaca data pasar dari market_data.json. Ada bagian tren, risiko, atau strategi tertentu yang ingin Anda diskusikan?"
            }
        ]
        
        while True:
            print("\n[Pasar Analisis Mendengarkan...] Silakan bicara...")
            duration = 6 
            sample_rate = 18000
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait() 
            
            filename = "temp_market.wav"
            wav.write(filename, sample_rate, audio_data)

            user_speech = ""
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                with sr.AudioFile(filename) as source:
                    audio = r.record(source)
                    user_speech = r.recognize_google(audio, language="id-ID")
                    print(f"Anda (Analisis Pasar): \"{user_speech}\"")
            except Exception:
                print("Gagal mengenali suara, silakan coba lagi...")
                if os.path.exists(filename):
                    os.remove(filename)
                continue
                
            if os.path.exists(filename):
                os.remove(filename)
                
            # Periksa perintah keluar
            lower_user_speech = user_speech.lower()
            exit_keywords = ["stop", "selesai", "keluar", "nonaktifkan", "hentikan", "non aktifkan"]
            if any(keyword in lower_user_speech for keyword in exit_keywords):
                speak_response("市場分析モードを終了します。")
                print("--- Keluar dari Mode Analisis Pasar ---")
                break
                
            # Tambahkan input pengguna ke riwayat JSON
            market_history.append({"role": "user", "content": user_speech})
            
            print(f"Mengirim data ke model ({model_name})...")
            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": model_name,
                        "messages": market_history,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    res_json = response.json()
                    reply_text = res_json.get("message", {}).get("content", "")
                    
                    # Simpan respon asisten ke riwayat JSON
                    market_history.append({"role": "assistant", "content": reply_text})
                    
                    print(f"\n[Hasil Analisis Pakar Ekonomi]:\n{reply_text}")
                    
                    # Bacakan ringkasan awal hasil analisis menggunakan VOICEVOX
                    speak_response(reply_text[:150] + "...") 
                else:
                    print("Gagal mendapatkan respons JSON dari Ollama.")
                    speak_response("経済分析の取得に失敗しました。")
            except Exception as e:
                print(f"Error koneksi JSON Ollama: {e}")
                speak_response("オラマとの接続に失敗しました。")
            
    except Exception as e:
        print(f"Error saat menganalisis file JSON: {e}")
        speak_response("JSONファイルの読み込みまたは分析中にエラーが発生しました。")

# --- FUNGSI WORKER UNTUK SKROL DI LATAR BELAKANG ---
def continuous_scroll_worker(direction):
    global is_scrolling_continuous
    scroll_amount = -30 if direction == "down" else 30
    while is_scrolling_continuous:
        pyautogui.scroll(scroll_amount)
        time.sleep(0.05)

def start_scrolling(direction):
    global is_scrolling_continuous, scroll_thread
    # Jika sudah berjalan, matikan dulu thread sebelumnya
    if is_scrolling_continuous:
        is_scrolling_continuous = False
        if scroll_thread and scroll_thread.is_alive():
            scroll_thread.join()
            
    is_scrolling_continuous = True
    scroll_thread = threading.Thread(target=continuous_scroll_worker, args=(direction,))
    scroll_thread.daemon = True
    scroll_thread.start()

# --- EKSEKUTOR PERINTAH KONTROL PC & SETTINGS ---
def execute_command(command_text):
    global last_command_type, is_scrolling_continuous
    text = command_text.lower()
    print(f"\n[Perintah Diterima]: {text}")

    # Deteksi perintah untuk menghentikan skrol
    if "stop" in text or "yamete" in text or "berhenti" in text:
        is_scrolling_continuous = False
        speak_response("スクロールを停止します。")
        return

    # 1. Fitur Waktu, Tanggal, dan Jadwal
    elif "jam berapa" in text or "waktu" in text or "pukul" in text:
        now = datetime.datetime.now()
        jam = now.strftime("%H:%M")
        speak_response(f"現在の時刻は {jam} です。")
        print(f"Jam saat ini: {jam}")

    elif "tanggal berapa" in text or "hari apa" in text:
        now = datetime.datetime.now()
        hari = now.strftime("%A, %d %B %Y")
        speak_response(f"今日は {hari} です。")
        print(f"Hari ini: {hari}")

    elif "jadwal" in text or "agenda" in text:
        try:
            with open("jadwal.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                agenda_hari_ini = data.get("hari_ini", "Tidak ada agenda hari ini.")
                speak_response("本日のスケジュールをお伝えします。")
                ask_ollama_and_speak("qwen3:8b", f"Ringkas dan bacakan jadwal berikut untuk kantor: {agenda_hari_ini}")
        except FileNotFoundError:
            speak_response("スケジュールファイルが見つかりませんでした。")
    # Integrasi Analisis Pasar Interaktif dari market_data.json
    elif "analisis pasar" in text or "analisa pasar" in text or "analisis ekonomi" in text or "analisis json" in text:
        target_file = "market_data.json"
        analyze_market_json(target_file, model_name="qwen3:8b")

    # Integrasi Analisis Pasar Interaktif dari market_data.json
    elif "analisis pasar" in text or "analisis ekonomi" in text or "analisis json" in text:
        target_file = "market_data.json"
        analyze_market_json(target_file, model_name="qwen3:8b")

    # Integrasi Kaiwa Partner - Mode Penutur Asli Jepang (Native Speaker Style) dengan Perbaikan Keluar Mode
    elif "aktifkan percakapan ai" in text or "kaiwa" in text:
        speak_response("日本語の会話モードを開始します。ネイティブのように話しましょう！")
        print("\n--- Memulai Mode Kaiwa Native Speaker (Katakan 'stop', 'selesai', 'nonaktifkan percakapan', atau 'hentikan kaiwa' untuk keluar) ---")
        
        # Inisialisasi riwayat percakapan dengan role system native Jepang
        kaiwa_history = [
            {
                "role": "system", 
                "content": (
                    "You are a native Japanese speaker and a warm, natural conversation partner. "
                    "Your goal is to converse with the user just like a real Japanese person in daily life.\n"
                    "Rules:\n"
                    "1. Always respond in authentic, natural Japanese (1-3 sentences) using conversational phrasing, idioms, and native reactions (e.g., えー、マジで？, なるほどね, よね～, etc.) where appropriate.\n"
                    "2. Insert Furigana for ALL Kanji using the format Kanji[furigana]. Example: 私[わたし]は 日本[にほん]に 住[す]んでいます。\n"
                    "3. Insert commas (、) frequently for natural pacing and pauses.\n"
                    "4. Gently and naturally correct any user grammar or vocabulary mistakes by incorporating the corrected form smoothly in your response or explaining it briefly.\n"
                    "5. Provide a clear, natural Indonesian translation and a brief natural nuance/grammar note after the delimiter '---TRANSLATION---'."
                )
            }
        ]
        
        while True:
            print("\n[Kaiwa Mendengarkan...] Silakan bicara...")
            duration = 6 
            sample_rate = 18000
            audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait() 
            
            filename = "temp_kaiwa.wav"
            wav.write(filename, sample_rate, audio_data)

            user_speech = ""
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                with sr.AudioFile(filename) as source:
                    audio = r.record(source)
                    user_speech = r.recognize_google(audio, language="id-ID")
                    print(f"Anda (Kaiwa): \"{user_speech}\"")
            except Exception:
                print("Gagal mengenali suara, silakan coba lagi...")
                if os.path.exists(filename):
                    os.remove(filename)
                continue
                
            if os.path.exists(filename):
                os.remove(filename)
                
            # Periksa perintah keluar yang lebih komprehensif (termasuk nonaktifkan/hentikan)
            lower_user_speech = user_speech.lower()
            exit_keywords = ["stop", "selesai", "keluar", "nonaktifkan", "hentikan", "non aktifkan"]
            if any(keyword in lower_user_speech for keyword in exit_keywords):
                speak_response("会話モードを終了します。お疲れ様でした！またおしゃべりしましょうね。")
                print("--- Keluar dari Mode Kaiwa ---")
                break
                
            # Tambahkan input pengguna ke riwayat JSON
            kaiwa_history.append({"role": "user", "content": user_speech})
            
            print("Mengirim data ke model (qwen3:8b) dengan gaya native...")
            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "qwen3:8b",
                        "messages": kaiwa_history,
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    res_json = response.json()
                    reply_text = res_json.get("message", {}).get("content", "")
                    
                    # Simpan respon asisten ke riwayat JSON
                    kaiwa_history.append({"role": "assistant", "content": reply_text})
                    
                    print(f"\n[AI Native Kaiwa Response]:\n{reply_text}")
                    
                    # Pisahkan teks bahasa Jepang dan terjemahan Indonesia
                    parts = reply_text.split("---TRANSLATION---")
                    japanese_part = parts[0].strip()
                    
                    # Bersihkan format furigana Kanji[...] untuk dibaca VOICEVOX
                    import re
                    clean_speech = re.sub(r'\[[^\]]+\]', '', japanese_part)
                    clean_speech = clean_speech.replace('\n', ' ')
                    
                    # Ucapkan hanya bagian bahasa Jepang menggunakan VOICEVOX
                    speak_response(clean_speech)
                else:
                    print("Gagal mendapatkan respons JSON dari Ollama.")
            except Exception as e:
                print(f"Error koneksi JSON Ollama: {e}")

    # 2. Kontrol Mouse (Scroll) & Navigasi Jendela / Tab
    elif "scroll bawah" in text or "turunkan" in text or "ke bawah" in text:
        last_command_type = "down"
        speak_response("下にスクロールし続けます。「ストップ」と言うまで続きます。")
        start_scrolling("down")

    elif "scroll atas" in text or "naikkan" in text or "ke atas" in text:
        last_command_type = "up"
        speak_response("上にスクロールし続けます。「ストップ」と言うまで続きます。")
        start_scrolling("up")

    elif "lagi" in text:
        if last_command_type == "down":
            speak_response("続けて下にスクロールします。")
            start_scrolling("down")
        elif last_command_type == "up":
            speak_response("続けて上にスクロールします。")
            start_scrolling("up")
        else:
            speak_response("繰り返すスクロールの履歴がありません。")
            
    elif "tutup tab" in text or "close tab" in text:
        speak_response("ブラウザのタブを閉じます。")
        pyautogui.hotkey('ctrl', 'w')

    elif "tutup chrome" in text or "tutup browser" in text:
        speak_response("クロームを終了します。")
        os.system("taskkill /f /im chrome.exe")

    elif "tutup terminal" in text or "tutup cmd" in text:
        speak_response("コマンドプロンプトを閉じます。")
        os.system("taskkill /f /im cmd.exe")
        
    elif "buka chrome" in text or "chrome" in text:
        speak_response("グーグルクロームを開きます。")
        os.system("start chrome")

    elif "tutup task manager" in text or "tutup tugas" in text:
        speak_response("タスクマネージャーを閉じます。")
        os.system("taskkill /f /im Taskmgr.exe")
        
    # 3. Web & Aplikasi Shortcut (Desktop & Web)
    elif "vocalvox" in text or "vocal" in text or "vox" in text:
        speak_response("ボイスボックスを開きます。")
        os.system('start "" "C:\\Program Files\\VOICEVOX\\VOICEVOX.exe"')

    elif "godot" in text:
        speak_response("ゴドーを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\Godot.exe"')

    elif "4k downloader" in text or "video downloader" in text:
        speak_response("4Kビデオダウンローダーを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\4K Video Downloader+.lnk"')

    elif "bluestacks" in text or "blue" in text or "stack" in text:
        speak_response("ブルースタックスを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\BlueStacks 5.lnk"')

    elif "capcut" in text:
        speak_response("キャップカットを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\CapCut.lnk"')

    elif "cheat engine" in text or "cheat" in text:
        speak_response("チートエンジンを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\Cheat Engine.lnk"')

    elif "paradox launcher" in text or "paradox" in text:
        speak_response("パラドックスランチャーを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\Paradox Launcher v2.lnk"')

    elif "obs" in text or "obs studio" in text: 
        speak_response("オービーエススタジオを開きます。")
        subprocess.Popen("start /b obs64", shell=True)

    elif "comfy" in text or "comfy desktop" in text:
        speak_response("コンフィデスクトップを開きます。")
        os.system('start "" "C:\\Users\\aditya\\Desktop\\Comfy Desktop.lnk"')

    elif "iggames" in text or "ig games" in text:
        speak_response("アイジージーゲームズを開きます。")
        os.system("start https://igg-games.com/")

    elif "whatsapp" in text or "wa" in text:
        speak_response("ワッツアップを開きます。")
        os.system("start https://web.whatsapp.com/")

    elif "gemini" in text or "google gemini" in text:
        speak_response("グーグルジェミニを開きます。")
        os.system("start https://gemini.google.com/")

    elif "fitgirl" in text or "fitgirl repacks" in text:
        speak_response("フィットガールリパックを開きます。")
        os.system("start https://fitgirl-repacks.site/")

    elif "save editor" in text or "editor" in text:
        speak_response("セーブエディターを開きます。")
        os.system("start https://www.google.com")

    elif "tutup notepad" in text:
        speak_response("メモ帳を閉じます。")
        os.system("taskkill /f /im notepad.exe")

    elif "tutup aplikasi" in text or "tutup jendela" in text:
        speak_response("アクティブなウィンドウを閉じます。")
        pyautogui.hotkey('alt', 'f4')

    elif "explorer" in text or ("buka" in text and "file" in text):
        speak_response("ファイルエクスプローラーを開きます。")
        subprocess.Popen("explorer")

    elif "youtube" in text or ("nonton" in text and "anime" not in text):
        speak_response("ユーチューブを開きます。")
        os.system("start https://www.youtube.com")

    elif "buat postingan" in text or ("facebook" in text and "post" in text):
        speak_response("フェイスブックの投稿ページを開きます。")
        os.system("start https://www.facebook.com/post/create")

    elif "marketplace" in text or ("facebook" in text and "marketplace" in text):
        speak_response("フェイスブックマーケットプレイスを開きます。")
        os.system("start https://www.facebook.com/marketplace/?ref=app_tab")

    elif "facebook" in text:
        speak_response("フェイスブックを開きます。")
        os.system("start https://www.facebook.com")

    elif "tokopedia" in text:
        speak_response("トコペディアを開きます。")
        os.system("start https://www.tokopedia.com")

    elif "shopee" in text:
        speak_response("ショッピーを開きます。")
        os.system("start https://www.shopee.co.id")

    elif "alibaba" in text:
        speak_response("アリババを開きます。")
        os.system("start https://www.alibaba.com")

    elif "manga" in text or "komik" in text or "baca manga" in text:
        speak_response("コミックサイトを開きます。")
        os.system("start https://komiku.org/")

    elif "suno" in text or "lagu" in text:
        speak_response("スノAIを開きます。")
        os.system("start https://suno.com/@uveraditya")

    elif "anime" in text or "nonton anime" in text:
        speak_response("アニメ視聴サイトを開きます。")
        os.system("start https://s13.nontonanimeid.boats/")

    elif "email" in text or "gmail" in text or "surat" in text:
        speak_response("メールを開きます。")
        os.system("start https://mail.google.com/mail/u/0/?service=mail&flowName=GlifWebSignIn&flowEntry=AccountChooser&ec=asw-gmail-globalnav-signin#inbox")

    elif "task manager" in text or "tugas" in text:
        speak_response("タスクマネージャーを開きます。")
        subprocess.Popen(['powershell', 'Start-Process', 'taskmgr', '-Verb', 'runAs'])

    elif "matikan" in text or "shutdown" in text:
        speak_response("警告。5秒後にパソコンをシャットダウンします。")
        time.sleep(2)
        os.system("shutdown /s /t 5")

    elif "pause" in text or "jeda" in text:
        speak_response("動画を一時停止します。")
        pyautogui.press('space')

    # Integrasi Model Ollama dengan VOICEVOX (Membacakan hasil respon AI secara lisan)
    elif "ollama" in text or "ai" in text or "model" in text:
        if "qwen" in text or "kuen" in text:
            speak_response("Qwenモデルに聞いています。")
            ask_ollama_and_speak("qwen3:8b", command_text)
        elif "deepseek" in text or "ディープシーク" in text:
            speak_response("DeepSeekモデルに聞いています。")
            ask_ollama_and_speak("deepseek-r1:14b", command_text)
        elif "gemma" in text or "ジェマ" in text:
            speak_response("Gemmaモデルに聞いています。")
            ask_ollama_and_speak("gemma2:9b", command_text)
        elif "llama" in text or "ラマ" in text:
            speak_response("Llamaモデルに聞いています。")
            ask_ollama_and_speak("llama3.2:3b", command_text)
        elif "sensei" in text or "seni" in text:
            speak_response("Senseiモデルに聞いています。")
            ask_ollama_and_speak("sensei-jp:latest", command_text)
        elif "math" in text or "matematika" in text:
            speak_response("Mathモデルに聞いています。")
            ask_ollama_and_speak("aditya-math:latest", command_text)
        elif "pentest" in text or "penetrasi" in text:
            speak_response("Pentestモデルに聞いています。")
            ask_ollama_and_speak("aditya-pentest:latest", command_text)
        elif "lyricist" in text or "lirik" in text:
            speak_response("Lyricistモデルに聞いています。")
            ask_ollama_and_speak("aditya-lyricist:latest", command_text)
        elif "hermes" in text:
            speak_response("Hermesモデルに聞いています。")
            ask_ollama_and_speak("hermes3:latest", command_text)
        else:
            speak_response("Ollamaサーバーはすでに実行されています。")

    elif "terminal" in text or "cmd" in text or ("buka" in text and "command" in text):
        speak_response("コマンドプロンプトを開きます。")
        subprocess.Popen("start cmd", shell=True)

    # 4. Fungsi Windows Settings
    elif "setting" in text or "pengaturan" in text:
        if "system" in text or "sistem" in text:
            speak_response("システム設定を開きます。")
            os.system("start ms-settings:display")
        elif "device" in text or "perangkat" in text:
            speak_response("デバイス設定を開きます。")
            os.system("start ms-settings:bluetooth")
        elif "mobile" in text or "hp" in text:
            speak_response("モバイルデバイス設定を開きます。")
            os.system("start ms-settings:mobile-devices")
        elif "network" in text or "internet" in text or "wifi" in text:
            speak_response("ネットワーク設定を開きます。")
            os.system("start ms-settings:network-status")
        elif "personalization" in text or "tampilan" in text or "wallpaper" in text:
            speak_response("パーソナライズ設定を開きます。")
            os.system("start ms-settings:personalization")
        elif "app" in text or "aplikasi" in text:
            speak_response("アプリ設定を開きます。")
            os.system("start ms-settings:appsfeatures")
        elif "account" in text or "akun" in text:
            speak_response("アカウント設定を開きます。")
            os.system("start ms-settings:yourinfo")
        elif "time" in text or "waktu" in text or "bahasa" in text:
            speak_response("日付と時刻・言語設定を開きます。")
            os.system("start ms-settings:dateandtime")
        elif "gaming" in text or "game" in text:
            speak_response("ゲーム設定を開きます。")
            os.system("start ms-settings:gaming-gamebar")
        elif "accessibility" in text or "ease of access" in text:
            speak_response("簡単アクセス設定を開きます。")
            os.system("start ms-settings:easeofaccess-display")
        elif "search" in text or "pencarian" in text:
            speak_response("検索設定を開きます。")
            os.system("start ms-settings:search")
        elif "privacy" in text or "privasi" in text:
            speak_response("プライバシー設定を開きます。")
            os.system("start ms-settings:privacy")
        elif "update" in text or "security" in text or "keamanan" in text:
            speak_response("アップデートとセキュリティ設定を開きます。")
            os.system("start ms-settings:windowsupdate")
        else:
            speak_response("設定パネルを開きます。")
            os.system("start ms-settings:")

    else:
        speak_response("すみません、コマンドが認識できません。")

# --- PEREKAM SUARA MENGGUNAKAN SOUNDDEVICE ---
def record_and_transcribe():
    duration = 5 
    sample_rate = 18000
    print("\n--- Mendengarkan suara Anda (Silakan bicara selama 5 detik)... ---")
    
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait() 
    print("Memproses suara...")

    filename = "temp_audio.wav"
    wav.write(filename, sample_rate, audio_data)

    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="id-ID")
            print(f"Anda berkata: \"{text}\"")
            execute_command(text)
    except sr.UnknownValueError:
        print("Suara tidak dapat dikenali, coba ulangi.")
    except sr.RequestError as e:
        print(f"Gagal terhubung ke layanan pengenalan suara: {e}")
    except Exception as ex:
        print(f"Terjadi kesalahan: {ex}")
    
    if os.path.exists(filename):
        os.remove(filename)

if __name__ == "__main__":
    speak_response("アデチアィータのPC音声制御システムを有効化しました。")
    
    while True:
        try:
            record_and_transcribe()
            time.sleep(1)
        except KeyboardInterrupt:
            speak_response("プログラムを終了します。")
            break