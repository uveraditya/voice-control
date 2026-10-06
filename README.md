# voice-control
Sistem kontrol PC berbasis suara (Voice Control) menggunakan Python yang memungkinkan Anda menjalankan berbagai perintah desktop, membuka aplikasi, mengontrol browser, hingga berinteraksi secara lisan dengan Model Bahasa Lokal (Ollama) yang dilengkapi dengan sintesis suara Bahasa Jepang (VOICEVOX).
🛠️ Daftar Tools dan Pustaka (Libraries) yang Digunakan
Skrip ini memanfaatkan berbagai pustaka Python pihak ketiga serta layanan lokal eksternal untuk menangani perekaman audio, pengenalan suara, otomatisasi sistem, dan integrasi kecerdasan buatan.

1. Pustaka Python (Python Libraries)
sounddevice: Digunakan untuk merekam suara dari mikrofon secara real-time (sd.rec) dan memutar kembali audio hasil sintesis (playback) dengan latensi rendah.

numpy: Berfungsi untuk menangani pemrosesan array data audio numerik yang direkam dari perangkat input.

scipy (scipy.io.wavfile): Digunakan untuk membaca dan menulis file audio berformat .wav guna keperluan pemrosesan sementara (temporary audio file).

pyautogui: Pustaka otomatisasi GUI untuk mengontrol perangkat input seperti mouse (untuk fungsi scroll atas/bawah) dan keyboard (untuk hotkeys seperti Ctrl+W, Alt+F4, dll.).

requests: Digunakan untuk melakukan HTTP requests (GET/POST) guna berinteraksi dengan API lokal dari Ollama dan VOICEVOX.

speech_recognition: Berfungsi sebagai pembungkus (wrapper) untuk menerjemahkan file audio rekaman suara menjadi teks melalui Google Web Speech API (recognize_google) dalam bahasa Indonesia.

2. Layanan & Aplikasi Eksternal (External Tools & Services)
Ollama: Berjalan secara lokal di port 11434 untuk menjalankan berbagai Model Bahasa Besar (LLMs), seperti qwen2.5-coder, deepseek-r1, gemma2, llama3.2, dan model kustom lainnya untuk menjawab perintah berbasis teks maupun kode.

VOICEVOX: Perangkat lunak TTS (Text-to-Speech) gratis berbasis AI asal Jepang yang berjalan di port lokal 50021. Digunakan untuk memberikan umpan balik suara (audio feedback) kepada pengguna menggunakan karakter suara seperti Shikoku Metan.

Windows Command Line / OS Module: Memanfaatkan modul bawaan Python (os dan subprocess) untuk menjalankan perintah tingkat sistem operasi, seperti meluncurkan aplikasi desktop, membuka tautan URL di browser default, mengatur Windows Settings, hingga mematikan komputer (shutdown).

📋 Fitur Utama
Voice Command to Text: Merekam suara Anda via mikrofon dan mengubahnya menjadi teks perintah berbahasa Indonesia.

PC & Browser Automation: Mengontrol navigasi jendela, scroll halaman, menutup aplikasi, membuka tab, hingga meluncurkan shortcut aplikasi desktop dan situs web favorit.

Local AI Integration: Mengirimkan prompt langsung ke model Ollama lokal dan mendengarkan jawabannya secara instan.

Japanese Voice Assistant (VOICEVOX): Memberikan respons suara interaktif bernuansa Jepang setiap kali perintah diterima atau diproses oleh sistem.
