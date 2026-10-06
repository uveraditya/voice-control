Sistem kontrol PC berbasis suara interaktif menggunakan Python yang terintegrasi dengan Ollama Local LLM, VOICEVOX API, dan otomatisasi desktop.

🚀 Fitur Utama
Voice-Controlled Desktop Navigation: Kontrol aplikasi, browser, tab, dan sistem Windows menggunakan perintah suara sederhana.

Continuous Auto-Scrolling: Fitur skrol otomatis ke atas/bawah di latar belakang menggunakan multi-threading.

Ollama Local AI Integration: Dukungan berbagai model lokal (Qwen, DeepSeek, Llama, dll.) dengan respons suara langsung.

Interactive Market Analysis Mode: Analisis data ekonomi/pasar berbasis file JSON interaktif selayaknya pakar profesional.

Japanese Native Kaiwa Partner: Mode latihan percakapan bahasa Jepang interaktif dengan dukungan Furigana dan terjemahan otomatis.

VOICEVOX Speech Synthesis: Output suara respons natural menggunakan engine VOICEVOX (Shikoku Metan).

🛠️ Tech Stack
Language: Python

Audio & Speech: sounddevice, scipy, SpeechRecognition

Automation & UI: pyautogui, subprocess

AI & NLP: Ollama API (/api/generate, /api/chat)

Text-to-Speech: VOICEVOX Local API (/audio_query, /synthesis)

📋 Prasyarat
Sebelum menjalankan skrip, pastikan Anda telah menyiapkan:

Python terinstal di komputer.

Aplikasi VOICEVOX aktif di port 50021.

Server Ollama lokal aktif di port 11434 dengan model yang diinginkan (misal: qwen3:8b).

⚙️ Instalasi & Menjalankan
Clone repository ini:

Bash
git clone https://github.com/username/repository-name.git
cd repository-name
Instal dependensi yang diperlukan:

Bash
pip install requests pyautogui sounddevice numpy scipy SpeechRecognition
Jalankan program utama:

Bash
python vocal_control.py
