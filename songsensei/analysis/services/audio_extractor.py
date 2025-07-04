import os
import asyncio
import tempfile
from pathlib import Path
from typing import Optional
from loguru import logger
import yt_dlp
import librosa
import soundfile as sf

class AudioExtractor:
    """
    Service for extracting audio from YouTube URLs using yt-dlp
    """
    
    def __init__(self, temp_dir: str = "/tmp/audio"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # yt-dlp configuration
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(self.temp_dir / '%(id)s.%(ext)s'),
            'extractaudio': True,
            'audioformat': 'wav',
            'audioquality': '192K',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
    
    async def extract_audio(self, youtube_url: str, job_id: str) -> str:
        """
        Extract audio from YouTube URL and convert to WAV
        
        Args:
            youtube_url: YouTube video URL
            job_id: Unique job identifier
            
        Returns:
            Path to extracted WAV file
        """
        try:
            logger.info(f"Starting audio extraction for {youtube_url}")
            
            # Run yt-dlp in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            audio_path = await loop.run_in_executor(
                None, 
                self._extract_with_ytdlp, 
                youtube_url, 
                job_id
            )
            
            logger.info(f"Audio extraction completed: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise Exception(f"Failed to extract audio: {str(e)}")
    
    def _extract_with_ytdlp(self, youtube_url: str, job_id: str) -> str:
        """
        Internal method to run yt-dlp extraction
        """
        try:
            # Create job-specific output path
            output_path = self.temp_dir / f"{job_id}.wav"
            
            # Update output template for this specific job
            opts = self.ydl_opts.copy()
            opts['outtmpl'] = str(self.temp_dir / f'{job_id}.%(ext)s')
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Extract info first to get video details
                info = ydl.extract_info(youtube_url, download=False)
                video_id = info.get('id', job_id)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                
                logger.info(f"Video info: {title} ({duration}s)")
                
                # Download the audio
                ydl.download([youtube_url])
                
                # Find the downloaded file (might have different extension)
                downloaded_files = list(self.temp_dir.glob(f"{job_id}.*"))
                if not downloaded_files:
                    raise Exception("No audio file was downloaded")
                
                downloaded_path = downloaded_files[0]
                
                # Convert to WAV if not already
                if downloaded_path.suffix.lower() != '.wav':
                    wav_path = self._convert_to_wav(downloaded_path, output_path)
                    # Remove original file
                    downloaded_path.unlink()
                    return str(wav_path)
                else:
                    return str(downloaded_path)
                
        except Exception as e:
            logger.error(f"yt-dlp extraction failed: {str(e)}")
            raise
    
    def _convert_to_wav(self, input_path: Path, output_path: Path) -> Path:
        """
        Convert audio file to WAV format using librosa
        """
        try:
            logger.info(f"Converting {input_path} to WAV")
            
            # Load audio with librosa (handles most formats)
            y, sr = librosa.load(str(input_path), sr=None)
            
            # Save as WAV
            sf.write(str(output_path), y, sr)
            
            logger.info(f"Conversion completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            raise Exception(f"Failed to convert audio to WAV: {str(e)}")
    
    def cleanup_file(self, file_path: str) -> None:
        """
        Remove temporary audio file
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")
    
    def cleanup_job_files(self, job_id: str) -> None:
        """
        Remove all files associated with a job
        """
        try:
            pattern = f"{job_id}.*"
            files = list(self.temp_dir.glob(pattern))
            for file_path in files:
                file_path.unlink()
                logger.info(f"Cleaned up job file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup job files for {job_id}: {str(e)}")
