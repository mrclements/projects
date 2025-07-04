import librosa
import numpy as np
from typing import Dict, Any, List
from loguru import logger
from models.analysis_models import WaveformData

class WaveformGenerator:
    """
    Service for generating waveform visualization data from audio files
    """
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
    
    async def generate_waveform(self, audio_path: str, num_peaks: int = 1000) -> Dict[str, Any]:
        """
        Generate waveform peaks data for visualization
        
        Args:
            audio_path: Path to audio file
            num_peaks: Number of peaks to generate for waveform display
            
        Returns:
            Dictionary containing waveform data
        """
        try:
            logger.info(f"Generating waveform for {audio_path}")
            
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Get duration in seconds
            duration = len(y) / sr
            
            # Generate peaks for waveform display
            peaks = self._generate_peaks(y, num_peaks)
            
            # Extract basic metadata
            metadata = self._extract_metadata(y, sr)
            
            waveform_data = {
                "peaks": peaks,
                "duration": duration,
                "sample_rate": sr,
                "metadata": metadata
            }
            
            logger.info(f"Waveform generation completed - Duration: {duration:.2f}s, Peaks: {len(peaks)}")
            
            return waveform_data
            
        except Exception as e:
            logger.error(f"Error generating waveform: {str(e)}")
            raise Exception(f"Failed to generate waveform: {str(e)}")
    
    def _generate_peaks(self, audio_data: np.ndarray, num_peaks: int) -> List[float]:
        """
        Generate waveform peaks by downsampling audio data
        """
        try:
            # Calculate chunk size for downsampling
            chunk_size = len(audio_data) // num_peaks
            
            if chunk_size < 1:
                # If audio is shorter than desired peaks, use all samples
                return audio_data.tolist()
            
            peaks = []
            
            # Process audio in chunks and find max amplitude in each chunk
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                if len(chunk) > 0:
                    # Use RMS for smoother visualization
                    rms = np.sqrt(np.mean(chunk ** 2))
                    peaks.append(float(rms))
            
            # Normalize peaks to 0-1 range
            if peaks:
                max_peak = max(peaks)
                if max_peak > 0:
                    peaks = [p / max_peak for p in peaks]
            
            return peaks
            
        except Exception as e:
            logger.error(f"Error generating peaks: {str(e)}")
            raise
    
    def _extract_metadata(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Extract basic audio metadata
        """
        try:
            metadata = {
                "length_samples": len(audio_data),
                "sample_rate": sample_rate,
                "duration_seconds": len(audio_data) / sample_rate,
                "channels": 1,  # We load as mono
                "bit_depth": 32,  # float32
            }
            
            # Basic audio statistics
            metadata["max_amplitude"] = float(np.max(np.abs(audio_data)))
            metadata["rms_amplitude"] = float(np.sqrt(np.mean(audio_data ** 2)))
            metadata["zero_crossing_rate"] = float(np.mean(librosa.feature.zero_crossing_rate(audio_data)))
            
            # Spectral features for basic characterization
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sample_rate)
            metadata["spectral_centroid_mean"] = float(np.mean(spectral_centroids))
            
            return metadata
            
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            return {
                "length_samples": len(audio_data),
                "sample_rate": sample_rate,
                "duration_seconds": len(audio_data) / sample_rate,
            }
    
    def generate_detailed_waveform(self, audio_path: str, start_time: float, end_time: float) -> Dict[str, Any]:
        """
        Generate high-resolution waveform for a specific time range
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Detailed waveform data for the specified segment
        """
        try:
            logger.info(f"Generating detailed waveform for {audio_path} ({start_time}-{end_time}s)")
            
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Convert time to sample indices
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Extract segment
            segment = y[start_sample:end_sample]
            
            # Generate high-resolution peaks (more points for detailed view)
            num_peaks = min(2000, len(segment) // 10)  # More detail for shorter segments
            peaks = self._generate_peaks(segment, num_peaks)
            
            return {
                "peaks": peaks,
                "duration": end_time - start_time,
                "sample_rate": sr,
                "start_time": start_time,
                "end_time": end_time
            }
            
        except Exception as e:
            logger.error(f"Error generating detailed waveform: {str(e)}")
            raise Exception(f"Failed to generate detailed waveform: {str(e)}")
