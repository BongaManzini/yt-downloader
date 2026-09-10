# 🚀 Ultimate Media Cloud Syncer Pro

A powerful, high-performance desktop application built with **CustomTkinter** and **yt-dlp** for downloading media (videos, audio, transcripts, metadata) and distributing them across **Local Storage**, **MEGA.nz**, and **Telegram Cloud**.

---

## ✨ Features

- **📥 Multi-Format Workflows**:
  - **Video Only**: Best Quality (4K/8K), 1080p Full HD, 720p HD, 480p.
  - **Audio Only**: Extraction to MP3, M4A, WAV, or FLAC.
  - **Transcript Only**: Subtitle extraction in SRT, VTT, or TXT format with language filtering (`en`, `es`, `fr`, `de`, `zh`, `all`).
  - **Everything Combo**: Video + Audio + Subtitles + Thumbnail + Info JSON metadata.
- **☁️ Flexible Distribution & Cloud Sync**:
  - **Local Disk**: Direct saving to custom output directories.
  - **MEGA.nz**: Automatic cloud upload with public share link generation.
  - **Telegram Cloud**: Direct uploading via **Telegram Bot API** (no SMS/2FA interactive terminal login needed) or **Pyrogram User Client**.
  - **Local + Cloud**: Multi-destination routing.
- **⚡ Thread-Safe & Responsive UI**:
  - Built with **CustomTkinter** (Dark / Light mode support).
  - Real-time dual progress bars (overall batch progress + current file percentage, speed in MB/s, ETA, and downloaded size).
  - Non-blocking background worker threads.
- **📋 Batch & Queue Manager**: Multi-link URL batch paste for queuing playlists, channels, or multiple videos.
- **🔒 Credentials & Preferences Persistence**: Secure local saving of settings and cloud credentials in `config.json`.
- **🛑 Cancellation Support**: Graceful interruption of ongoing downloads and cloud uploads.

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- [FFmpeg](https://ffmpeg.org/) (optional but recommended for audio extraction and video format merging)

### 2. Clone & Install Dependencies

```bash
# Clone repository
git clone https://github.com/BongaManzini/yt_down.git
cd yt_down

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install customtkinter yt-dlp mega.py pyrogram tgcrypto Pillow requests ffmpeg-python tenacity
```

---

## 🚀 Running the Application

```bash
python main.py
```

---

## 🧪 Running Automated Tests

```bash
python test_suite.py
```

---

## 📁 Repository Structure

```
yt_down/
├── main.py               # Main GUI application entrypoint
├── opp.py                # Backward-compatible wrapper pointing to main.py
├── downloader_engine.py  # yt-dlp wrapper with progress hooks & cancellation
├── cloud_syncer.py       # Cloud uploader (Local, MEGA.nz, Telegram Bot/User API)
├── config_manager.py     # Configuration & credentials persistence manager
├── test_suite.py         # Automated unit test suite
├── .gitignore            # Git ignore file
└── README.md             # Project documentation
```

---

## 📜 License

MIT License
