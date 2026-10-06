import os
import subprocess
import time
import io
import requests
import pyautogui
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

# Variabel global untuk menyimpan status perintah terakhir (untuk fitur "lagi")
last_command_type = None

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
                "stream": False # Set True jika ingin model merespon secara streaming
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

# --- EKSEKUTOR PERINTAH KONTROL PC & SETTINGS ---
def execute_command(command_text):
    global last_command_type
    text = command_text.lower()
    print(f"\n[Perintah Diterima]: {text}")

    # 1. Kontrol Mouse (Scroll) & Navigasi Jendela / Tab
    if "scroll bawah" in text or "turunkan" in text or "ke bawah" in text:
        last_command_type = "down"
        speak_response("ゆっくり下にスクロールしています。")
        for _ in range(15):
            pyautogui.scroll(-30)
            time.sleep(0.05)

    elif "scroll atas" in text or "naikkan" in text or "ke atas" in text:
        last_command_type = "up"
        speak_response("ゆっくり上にスクロールしています。")
        for _ in range(15):
            pyautogui.scroll(30)
            time.sleep(0.05)

    elif "lagi" in text:
        if last_command_type == "down":
            speak_response("続けて下にスクロールします。")
            for _ in range(15):
                pyautogui.scroll(-30)
                time.sleep(0.05)
        elif last_command_type == "up":
            speak_response("続けて上にスクロールします。")
            for _ in range(15):
                pyautogui.scroll(30)
                time.sleep(0.05)
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
        
    # 2. Web & Aplikasi Shortcut (Desktop & Web)
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
            ask_ollama_and_speak("qwen2.5-coder:14b", command_text)
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

    # 3. Fungsi Windows Settings
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
    print("\n--- Mendengarkan suara Anda (Silakan bicara selama 10 detik)... ---")
    
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