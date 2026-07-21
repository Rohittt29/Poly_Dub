# 🎬 Poly_Dub

> **A lightweight AI-powered YouTube video dubbing pipeline that automatically downloads videos, transcribes speech, translates content, generates AI voiceovers, and produces synchronized dubbed videos.**

---

## 🚀 Features

- 📥 Download videos directly from YouTube
- 🎙️ Speech-to-Text using Faster-Whisper
- 🌍 Automatic language translation
- 🗣️ AI-generated voiceovers using Microsoft Edge-TTS
- 🎞️ Merge translated audio back into the original video
- ⚡ Lightweight implementation with minimal dependencies
- 💻 Simple command-line interface
- 🆓 Built entirely using free and open-source tools

---

## 🏗️ Project Architecture

```text
                YouTube URL
                     │
                     ▼
              📥 yt-dlp Downloader
                     │
                     ▼
            🎙️ Faster-Whisper
          (Speech Transcription)
                     │
                     ▼
      🌍 Google Translate (deep-translator)
                     │
                     ▼
          🗣️ Microsoft Edge-TTS
          (AI Voice Generation)
                     │
                     ▼
              🎬 FFmpeg Remixer
                     │
                     ▼
          ✅ Final Dubbed Video
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Video Download | yt-dlp |
| Speech Recognition | Faster-Whisper |
| Translation | deep-translator |
| Text-to-Speech | Microsoft Edge-TTS |
| Video Processing | FFmpeg |

---

## 📂 Project Structure

```
Poly_Dub/
│
├── main.py
├── downloader.py
├── transcriber.py
├── translator.py
├── tts.py
├── remixer.py
├── config.py
├── logger.py
├── state_manager.py
├── progress.py
├── utils.py
├── requirements.txt
├── README.md
└── outputs/
```

---

## ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/Rohittt29/Poly_Dub.git
cd Poly_Dub
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment

### Windows

```bash
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the application with a YouTube URL.

```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

The pipeline will automatically:

1. Download the video
2. Extract audio
3. Generate transcript
4. Translate transcript
5. Generate AI voice
6. Merge dubbed audio
7. Save the final output

---

## 📦 Output

The generated files are stored inside the `outputs/` directory.

Example:

```
outputs/
└── video_xxxxxxxx/
    ├── original_transcript.txt
    ├── translated_transcript.txt
    ├── english_subtitles.srt
    ├── processing.json
    └── final_dubbed_video.mp4
```

---

## 💡 Use Cases

- 🌍 Multilingual content creation
- 🎓 Educational videos
- 🎥 Video localization
- 📚 Learning foreign languages
- 🤖 AI automation workflows

---

## 🔮 Future Improvements

- Support multiple target languages
- Voice cloning
- Speaker diarization
- Lip-sync integration
- GUI/Desktop application
- Docker support
- Batch video processing

---

## 🤝 Contributing

Contributions are welcome!

Feel free to fork the repository, open issues, or submit pull requests to improve the project.

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Rohit Kumbhar**

- GitHub: https://github.com/Rohittt29

---

⭐ If you found this project useful, consider giving it a star!