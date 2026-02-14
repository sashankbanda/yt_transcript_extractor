# YouTube Transcript Extractor

Extracts transcript from any YouTube video. Tries official captions first, falls back to Whisper speech-to-text if unavailable. Saves output as `.txt` in the `output/` folder.

## Prerequisites

- Python 3.11+
- [FFmpeg](https://ffmpeg.org/download.html) installed and added to PATH

## Setup

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate          # Linux/Mac

pip install -r requirements.txt
```

## Usage

```bash
python youtube_transcript_extractor.py "<youtube_url>"
```

**Example:**
```bash
python youtube_transcript_extractor.py "https://www.youtube.com/watch?v=WWEs82u37Mw"
```

Output saved to: `output/<video_id>.txt`

## Language Support

- **English videos** → captions are picked automatically (no prompt)
- **Single language (non-English)** → picked automatically
- **Multiple languages** → you'll be prompted to choose
- **No captions at all** → Whisper auto-detects the spoken language

## How It Works

1. Extracts video ID from the URL
2. Lists all available caption languages
3. Auto-selects English if available, otherwise prompts user
4. If no captions → downloads audio via `yt-dlp` → transcribes with `faster-whisper` (CPU, int8)
5. Saves transcript to `output/<video_id>.txt`
