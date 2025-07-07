import asyncio
from pathlib import Path
from loguru import logger
import subprocess

class AudioExtractor:
    """
    Service for extracting audio from YouTube URLs using yt-dlp CLI
    """

    def __init__(self, temp_dir: str = "/tmp/audio"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True, parents=True)

    async def extract_audio(self, youtube_url: str, job_id: str) -> str:
        """
        Extract audio from YouTube URL and convert to WAV using yt-dlp CLI.
        Returns the path to the WAV file.
        """
        logger.info(f"Starting audio extraction for {youtube_url}")
        loop = asyncio.get_event_loop()
        path = await loop.run_in_executor(None, self._run_cli, youtube_url, job_id)
        logger.info(f"Audio extraction completed: {path}")
        return path

    def _run_cli(self, youtube_url: str, job_id: str) -> str:
        # Build output template for yt-dlp
        output_template = str(self.temp_dir / f"{job_id}.%(ext)s")
        # Build command to use system yt-dlp binary
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "-q",
            "-x",
            "--audio-format", "wav",
            "-o", output_template,
            youtube_url
        ]
        logger.info(f"Running yt-dlp CLI: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        # Verify WAV exists
        wav_path = self.temp_dir / f"{job_id}.wav"
        if not wav_path.exists():
            raise FileNotFoundError(f"Expected WAV not found: {wav_path}")
        return str(wav_path)

    def cleanup_file(self, file_path: str) -> None:
        try:
            p = Path(file_path)
            if p.exists():
                p.unlink()
                logger.info(f"Cleaned up {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

    def cleanup_job_files(self, job_id: str) -> None:
        for p in self.temp_dir.glob(f"{job_id}.*"):
            try:
                p.unlink()
            except Exception:
                pass
