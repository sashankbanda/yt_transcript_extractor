"""
Production-Ready YouTube Transcript Extractor (With Proper Logging)

Features:
- Accepts a YouTube URL
- Tries official captions first
- Falls back to Whisper transcription if captions unavailable
- Stores final transcript as .txt file inside /output folder
- Detailed logs for debugging

Requirements:
pip install youtube-transcript-api yt-dlp faster-whisper ffmpeg-python
System requirement: ffmpeg must be installed and added to PATH

Usage:
python youtube_transcript_extractor.py "https://www.youtube.com/watch?v=VIDEO_ID"
"""

import os
import sys
import tempfile
import logging
from urllib.parse import urlparse, parse_qs
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp
from faster_whisper import WhisperModel


# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


class YouTubeTranscriptExtractor:
    def __init__(self, whisper_model_size: str = "base"):
        logger.info(f"Loading Whisper model: {whisper_model_size}")
        self.whisper_model = WhisperModel(whisper_model_size, device="cpu", compute_type="int8")
        logger.info("Whisper model loaded successfully")

    # -------------------------
    # Public API
    # -------------------------
    def extract_text(self, youtube_url: str) -> str:
        logger.info(f"Processing URL: {youtube_url}")

        video_id = self._extract_video_id(youtube_url)
        logger.info(f"Extracted Video ID: {video_id}")

        # Step 1: Try official captions
        transcript = self._get_official_captions(video_id)
        if transcript:
            logger.info("Official captions found")
            return transcript

        # Step 2: Fallback to speech-to-text
        logger.warning("No captions found. Falling back to Whisper transcription")
        return self._transcribe_via_whisper(youtube_url)

    # -------------------------
    # Helpers
    # -------------------------
    def _extract_video_id(self, url: str) -> str:
        parsed_url = urlparse(url)

        if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
            video_id = parse_qs(parsed_url.query).get("v", [None])[0]
            if not video_id:
                raise ValueError("Could not extract video ID from watch URL")
            return video_id

        if parsed_url.hostname == "youtu.be":
            video_id = parsed_url.path.lstrip("/")
            if not video_id:
                raise ValueError("Could not extract video ID from short URL")
            return video_id

        raise ValueError("Invalid YouTube URL format")

    def _get_official_captions(self, video_id: str) -> Optional[str]:
        try:
            logger.info("Attempting to fetch official captions...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Collect all available transcripts
            available = []
            for t in transcript_list:
                available.append(t)

            if not available:
                logger.warning("No transcripts available")
                return None

            # Log available languages
            for t in available:
                tag = "(auto-generated)" if t.is_generated else "(manual)"
                logger.info(f"  Available: {t.language} [{t.language_code}] {tag}")

            # Priority: English first
            selected = None

            # Try English (manual first, then auto-generated)
            for t in available:
                if t.language_code.startswith("en") and not t.is_generated:
                    selected = t
                    break
            if not selected:
                for t in available:
                    if t.language_code.startswith("en"):
                        selected = t
                        break

            # If only one language available, use it directly
            if not selected and len(available) == 1:
                selected = available[0]

            # Multiple non-English languages: prompt user
            if not selected:
                print("\nMultiple transcript languages found:")
                for i, t in enumerate(available):
                    tag = "(auto-generated)" if t.is_generated else "(manual)"
                    print(f"  [{i + 1}] {t.language} [{t.language_code}] {tag}")

                while True:
                    choice = input(f"\nSelect language (1-{len(available)}): ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(available):
                        selected = available[int(choice) - 1]
                        break
                    print("Invalid choice. Try again.")

            logger.info(f"Using transcript: {selected.language} [{selected.language_code}]")
            transcript_data = selected.fetch()
            return " ".join(entry["text"] for entry in transcript_data)

        except TranscriptsDisabled:
            logger.warning("Transcripts are disabled for this video")
            return None
        except NoTranscriptFound:
            logger.warning("No transcript found for this video")
            return None
        except Exception as e:
            logger.error(f"Caption extraction failed: {e}")
            return None

    def _download_audio(self, youtube_url: str) -> str:
        logger.info("Downloading audio via yt-dlp...")

        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "audio.%(ext)s")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "quiet": False,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        audio_path = os.path.join(temp_dir, "audio.mp3")

        if not os.path.exists(audio_path):
            raise FileNotFoundError("Audio file was not created after download")

        logger.info(f"Audio downloaded to: {audio_path}")
        return audio_path

    def _transcribe_via_whisper(self, youtube_url: str) -> str:
        audio_file = self._download_audio(youtube_url)

        logger.info("Starting Whisper transcription...")
        segments, info = self.whisper_model.transcribe(audio_file)
        logger.info(f"Detected language: {info.language}")

        transcript_text = ""
        for segment in segments:
            transcript_text += segment.text + " "

        logger.info("Transcription completed")
        return transcript_text.strip()


# -------------------------
# Save Output
# -------------------------

def save_to_file(video_id: str, text: str):
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{video_id}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    logger.info(f"Transcript saved to: {file_path}")


# -------------------------
# CLI Entry
# -------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python youtube_transcript_extractor.py <youtube_url>")
        sys.exit(1)

    youtube_url = sys.argv[1]

    try:
        extractor = YouTubeTranscriptExtractor(whisper_model_size="base")
        video_id = extractor._extract_video_id(youtube_url)
        text = extractor.extract_text(youtube_url)

        if not text:
            raise ValueError("Transcript extraction returned empty text")

        save_to_file(video_id, text)
        logger.info("Process completed successfully")

    except Exception as e:
        logger.exception(f"Fatal error occurred: {e}")
        sys.exit(1)