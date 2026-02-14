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

## How It Works

1. Extracts video ID from the URL
2. Attempts to fetch official YouTube captions
3. If no captions → downloads audio via `yt-dlp` → transcribes with `faster-whisper` (CPU, int8)
4. Saves transcript to `output/<video_id>.txt`
