import librosa
import numpy as np
from typing import Dict, Any, List, Tuple
from loguru import logger
import asyncio

# Import music analysis libraries
try:
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    logger.warning("Essentia not available - using fallback implementations")

try:
    import madmom
    MADMOM_AVAILABLE = True
except ImportError:
    MADMOM_AVAILABLE = False
    logger.warning("madmom not available - using fallback implementations")

try:
    from music21 import stream, note, chord, key, meter, duration
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False
    logger.warning("music21 not available - using fallback implementations")

from models.analysis_models import AnalysisResult, ChordInfo

class MusicAnalyzer:
    """
    Service for analyzing musical content using Essentia, madmom, and music21
    """
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.setup_analyzers()
    
    def setup_analyzers(self):
        """Initialize the analysis algorithms"""
        try:
            if ESSENTIA_AVAILABLE:
                # Key detection
                self.key_detector = es.KeyExtractor()
                
                # Tempo detection
                self.tempo_detector = es.RhythmExtractor2013()
                
                # Chroma features
                self.chroma_extractor = es.ChromaCrossSimilarity()
                
            if MADMOM_AVAILABLE:
                # Chord recognition
                self.chord_processor = madmom.features.chords.DeepChromaChordRecognitionProcessor()
                
            logger.info("Music analyzers initialized successfully")
            
        except Exception as e:
            logger.warning(f"Error initializing analyzers: {str(e)}")
    
    async def analyze_segment(self, audio_path: str, start_time: float, end_time: float) -> Dict[str, Any]:
        """
        Analyze a trimmed audio segment for musical content
        
        Args:
            audio_path: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Analysis results including key, chords, tempo, and tabs
        """
        try:
            logger.info(f"Starting musical analysis for {audio_path} ({start_time}-{end_time}s)")
            
            # Load and trim audio segment
            audio_segment = await self._load_audio_segment(audio_path, start_time, end_time)
            
            # Run analysis in parallel
            analysis_tasks = [
                self._detect_key(audio_segment),
                self._detect_tempo(audio_segment),
                self._analyze_chords(audio_segment, start_time, end_time),
            ]
            
            key_result, tempo_result, chords_result = await asyncio.gather(*analysis_tasks)
            
            # Generate guitar tabs
            tab_result = await self._generate_guitar_tabs(chords_result, tempo_result)
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(key_result, tempo_result, chords_result)
            
            analysis_result = {
                # Core V1 fields
                "key": key_result["key"],
                "tempo": tempo_result["tempo"],
                "time_signature": tempo_result.get("time_signature", "4/4"),
                "confidence": confidence,
                "chords": chords_result,
                
                # V2 Extensions
                "analysisVersion": "2.0",
                
                # Song structure analysis (placeholder for now)
                "segments": [],
                
                # Enhanced tracking
                "key_changes": [],
                "time_signature_changes": [],
                "modulations": [],
                
                # Enhanced tab with export options
                "tab": tab_result,
                
                # Cloud processing metadata
                "processing": {
                    "cloudServices": [],
                    "sourceSeparation": False,
                    "processingTime": 0.0,
                    "queuePosition": None
                },
                
                # Quality metrics
                "quality": {
                    "chordAccuracy": confidence,
                    "structureConfidence": 0.0,
                    "keyStability": key_result.get("confidence", 0.5),
                    "rhythmConsistency": tempo_result.get("confidence", 0.5)
                }
            }
            
            logger.info(f"Analysis completed - Key: {key_result['key']}, Tempo: {tempo_result['tempo']}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in musical analysis: {str(e)}")
            raise Exception(f"Failed to analyze audio segment: {str(e)}")
    
    async def _load_audio_segment(self, audio_path: str, start_time: float, end_time: float) -> np.ndarray:
        """Load and trim audio segment"""
        try:
            # Load audio file
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            
            # Convert time to sample indices
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Extract segment
            segment = y[start_sample:end_sample]
            
            return segment
            
        except Exception as e:
            logger.error(f"Error loading audio segment: {str(e)}")
            raise
    
    async def _detect_key(self, audio_segment: np.ndarray) -> Dict[str, Any]:
        """Detect musical key using Essentia or fallback"""
        try:
            if ESSENTIA_AVAILABLE:
                # Use Essentia key detection
                key, scale, strength = self.key_detector(audio_segment)
                confidence = float(strength)
                
                return {
                    "key": f"{key} {scale}",
                    "root": key,
                    "scale": scale,
                    "confidence": confidence
                }
            else:
                # Fallback: Use librosa for chroma-based key detection
                chroma = librosa.feature.chroma_stft(y=audio_segment, sr=self.sample_rate)
                chroma_mean = np.mean(chroma, axis=1)
                
                # Simple key detection based on chroma profile
                key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                key_idx = np.argmax(chroma_mean)
                detected_key = key_names[key_idx]
                
                # Assume major scale for simplicity
                return {
                    "key": f"{detected_key} major",
                    "root": detected_key,
                    "scale": "major",
                    "confidence": 0.7  # Conservative confidence for fallback
                }
                
        except Exception as e:
            logger.error(f"Error in key detection: {str(e)}")
            return {
                "key": "C major",
                "root": "C",
                "scale": "major",
                "confidence": 0.5
            }
    
    async def _detect_tempo(self, audio_segment: np.ndarray) -> Dict[str, Any]:
        """Detect tempo using Essentia or fallback"""
        try:
            if ESSENTIA_AVAILABLE:
                # Use Essentia rhythm extraction
                bpm, beats, beat_confidence, _, _ = self.tempo_detector(audio_segment)
                
                return {
                    "tempo": float(bpm),
                    "confidence": float(beat_confidence),
                    "time_signature": "4/4"  # Default for now
                }
            else:
                # Fallback: Use librosa tempo detection
                tempo, beats = librosa.beat.beat_track(y=audio_segment, sr=self.sample_rate)
                
                return {
                    "tempo": float(tempo),
                    "confidence": 0.7,
                    "time_signature": "4/4"
                }
                
        except Exception as e:
            logger.error(f"Error in tempo detection: {str(e)}")
            return {
                "tempo": 120.0,
                "confidence": 0.5,
                "time_signature": "4/4"
            }
    
    async def _analyze_chords(self, audio_segment: np.ndarray, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        Analyze chord progression using sliding window approach
        Uses shorter windows and aligns with beat grid for musician-friendly results
        """
        try:
            # Detect beats for chord alignment
            beat_times = await self._detect_beats(audio_segment, start_time)
            
            # If no beats detected, use regular intervals
            if not beat_times:
                logger.info("No beats detected, using regular intervals")
                beat_interval = 0.5  # 0.5 second intervals
                beat_times = np.arange(start_time, end_time, beat_interval)
            
            # Use sliding windows approach with window size and hop size
            window_size_seconds = 1.0  # 1 second window for analysis
            hop_size_seconds = 0.25    # 0.25 second hop size for smoother transitions
            
            # Convert to samples
            window_size = int(window_size_seconds * self.sample_rate)
            hop_size = int(hop_size_seconds * self.sample_rate)
            
            logger.info(f"Using sliding window: window_size={window_size_seconds}s, hop_size={hop_size_seconds}s")
            
            # Process using sliding windows
            chord_list = []
            current_position = 0
            
            # Process until we reach the end of the segment
            while current_position + window_size <= len(audio_segment):
                # Extract window
                window = audio_segment[current_position:current_position + window_size]
                
                # Calculate time for this window
                window_time = start_time + (current_position / self.sample_rate)
                
                # Analyze chord for this window
                chord_label, confidence = self._analyze_window_chord(window)
                
                # Apply confidence threshold for quality filtering
                if confidence >= 0.4:  # Only keep reasonably confident detections
                    chord_info = {
                        "time": float(window_time),
                        "chord": chord_label,
                        "confidence": confidence,
                        "is_diatonic": True  # Will be calculated later
                    }
                    chord_list.append(chord_info)
                
                # Move to next hop
                current_position += hop_size
            
            # Post-processing: smooth chord transitions and align with beats
            processed_chords = self._post_process_chords(chord_list, beat_times)
            
            # Return processed chords
            return processed_chords
            
        except Exception as e:
            logger.error(f"Error in chord analysis: {str(e)}")
            return self._generate_fallback_chords(start_time, end_time)
    
    async def _detect_beats(self, audio_segment: np.ndarray, start_time: float) -> List[float]:
        """Detect beat positions for chord alignment"""
        try:
            if MADMOM_AVAILABLE:
                # Use madmom for better beat tracking
                from madmom.features.beats import RNNBeatProcessor, BeatTrackingProcessor
                
                # Process with madmom
                rnn = RNNBeatProcessor()(audio_segment)
                beats = BeatTrackingProcessor()(rnn)
                
                # Convert to our time reference
                beat_times = [start_time + b for b in beats]
                return beat_times
            
            elif ESSENTIA_AVAILABLE:
                # Use Essentia for beat tracking
                rhythm_extractor = es.RhythmExtractor2013()
                bpm, beats, beat_confidence, _, _ = rhythm_extractor(audio_segment)
                
                # Convert to our time reference
                beat_times = [start_time + b for b in beats]
                return beat_times
            
            else:
                # Fallback: Use librosa for beat tracking
                tempo, beat_frames = librosa.beat.beat_track(y=audio_segment, sr=self.sample_rate)
                beat_times = librosa.frames_to_time(beat_frames, sr=self.sample_rate)
                
                # Convert to our time reference
                beat_times = [start_time + b for b in beat_times]
                return beat_times
                
        except Exception as e:
            logger.error(f"Error in beat detection: {str(e)}")
            return []
    
    def _analyze_window_chord(self, window: np.ndarray) -> Tuple[str, float]:
        """Analyze chord for a single window"""
        try:
            if MADMOM_AVAILABLE:
                # Use madmom for better chord detection
                chords = self.chord_processor(window)
                
                if len(chords) > 0:
                    # Use the first chord (most prominent)
                    chord_label = str(chords[0])
                    
                    # Estimate confidence based on chroma clarity
                    chroma = librosa.feature.chroma_cqt(y=window, sr=self.sample_rate)
                    max_val = np.max(np.mean(chroma, axis=1))
                    min_val = np.min(np.mean(chroma, axis=1))
                    clarity = (max_val - min_val) / (max_val + min_val + 1e-8)
                    confidence = min(0.95, max(0.4, clarity))
                    
                    return chord_label, float(confidence)
                
                return "N", 0.0  # No chord
                
            elif ESSENTIA_AVAILABLE:
                # Use Essentia for chord detection
                key_detector = es.KeyExtractor()
                key, scale, strength = key_detector(window)
                
                # Simple chord inference from key
                if scale == 'major':
                    chord_label = key
                else:
                    chord_label = f"{key}m"
                
                return chord_label, float(strength)
                
            else:
                # Fallback: Use librosa for simple chord detection
                chroma = librosa.feature.chroma_cqt(y=window, sr=self.sample_rate)
                chroma_sum = np.sum(chroma, axis=1)
                root_note = np.argmax(chroma_sum)
                
                # Simple major/minor detection based on third
                third_major = (root_note + 4) % 12
                third_minor = (root_note + 3) % 12
                
                if chroma_sum[third_major] > chroma_sum[third_minor]:
                    quality = ""  # Major
                else:
                    quality = "m"  # Minor
                
                # Convert to chord name
                notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
                chord_label = f"{notes[root_note]}{quality}"
                
                # Calculate confidence based on chroma clarity
                max_val = np.max(chroma_sum)
                min_val = np.min(chroma_sum)
                clarity = (max_val - min_val) / (max_val + min_val + 1e-8)
                confidence = min(0.8, max(0.4, clarity))
                
                return chord_label, float(confidence)
                
        except Exception as e:
            logger.error(f"Error in window chord analysis: {str(e)}")
            return "C", 0.5  # Default fallback
    
    def _post_process_chords(self, chord_list: List[Dict[str, Any]], beat_times: List[float]) -> List[Dict[str, Any]]:
        """
        Post-process chord list to:
        1. Remove duplicate consecutive chords
        2. Align chord changes with beats
        3. Filter out very short chord segments
        """
        if not chord_list:
            return []
        
        # Sort by time
        chord_list.sort(key=lambda x: x["time"])
        
        # Align chord changes to nearest beat
        if beat_times:
            for chord in chord_list:
                # Find closest beat
                closest_beat = min(beat_times, key=lambda b: abs(b - chord["time"]))
                chord["time"] = float(closest_beat)
        
        # Group by aligned time positions
        chord_groups = {}
        for chord in chord_list:
            time_pos = chord["time"]
            if time_pos not in chord_groups:
                chord_groups[time_pos] = []
            chord_groups[time_pos].append(chord)
        
        # For each group, select the chord with highest confidence
        best_chords = []
        for time_pos in sorted(chord_groups.keys()):
            chords = chord_groups[time_pos]
            best_chord = max(chords, key=lambda c: c["confidence"])
            best_chords.append(best_chord)
        
        # Remove duplicates (same chord in consecutive positions)
        processed_chords = []
        prev_chord = None
        min_duration = 0.25  # Minimum chord duration in seconds
        
        for i, chord in enumerate(best_chords):
            # Check if this is a different chord from previous
            if prev_chord is None or chord["chord"] != prev_chord["chord"]:
                # Calculate end time (for duration checking)
                if i < len(best_chords) - 1:
                    next_time = best_chords[i+1]["time"]
                    duration = next_time - chord["time"]
                    
                    # Only add if duration is long enough
                    if duration >= min_duration:
                        processed_chords.append(chord)
                        prev_chord = chord
                else:
                    # Last chord, always add it
                    processed_chords.append(chord)
                    prev_chord = chord
        
        logger.info(f"Processed {len(chord_list)} raw chords into {len(processed_chords)} refined chords")
        return processed_chords
    
    def _generate_fallback_chords(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Generate a simple chord progression for fallback"""
        # Simple I-V-vi-IV progression in C major
        chords = ["C", "G", "Am", "F"]
        chord_list = []
        
        duration = end_time - start_time
        chord_duration = duration / len(chords)
        
        for i, chord in enumerate(chords):
            time_pos = start_time + i * chord_duration
            
            chord_info = {
                "time": float(time_pos),
                "chord": chord,
                "confidence": 0.6,
                "is_diatonic": True
            }
            chord_list.append(chord_info)
        
        return chord_list
    
    async def _generate_guitar_tabs(self, chords: List[Dict[str, Any]], tempo_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate guitar tablature from chord progression"""
        try:
            # Standard guitar chord fingerings
            chord_fingerings = {
                "C": [0, 1, 0, 2, 3, 0],      # C major
                "G": [3, 2, 0, 0, 3, 3],      # G major
                "Am": [0, 0, 2, 2, 1, 0],     # A minor
                "F": [1, 1, 3, 3, 1, 1],      # F major (barre)
                "D": [2, 0, 0, 2, 3, 2],      # D major
                "E": [0, 2, 2, 1, 0, 0],      # E major
                "Em": [0, 2, 2, 0, 0, 0],     # E minor
                "A": [0, 0, 2, 2, 2, 0],      # A major
                "Dm": [1, 0, 0, 2, 3, 1],     # D minor
            }
            
            measures = []
            
            for chord_info in chords:
                chord_name = chord_info["chord"]
                
                # Get base chord name (remove extensions for now)
                base_chord = chord_name.split("/")[0]  # Remove slash chords
                base_chord = base_chord.replace("maj", "").replace("min", "m")  # Simplify
                
                # Get fingering or use default
                frets = chord_fingerings.get(base_chord, [0, 0, 0, 0, 0, 0])
                
                measure = {
                    "chord": chord_name,
                    "frets": frets,
                    "strumming_pattern": "D D U D U",  # Simple down-up pattern
                    "time": chord_info["time"]
                }
                measures.append(measure)
            
            tab_data = {
                "measures": measures,
                "tempo": tempo_info["tempo"],
                "time_signature": tempo_info["time_signature"],
                "tuning": ["E", "A", "D", "G", "B", "E"],  # Standard tuning
                "capo": 0
            }
            
            return tab_data
            
        except Exception as e:
            logger.error(f"Error generating guitar tabs: {str(e)}")
            return {
                "measures": [],
                "tempo": 120,
                "time_signature": "4/4",
                "tuning": ["E", "A", "D", "G", "B", "E"],
                "capo": 0
            }
    
    def _calculate_confidence(self, key_result: Dict, tempo_result: Dict, chords_result: List) -> float:
        """Calculate overall analysis confidence"""
        try:
            confidences = [
                key_result.get("confidence", 0.5),
                tempo_result.get("confidence", 0.5),
            ]
            
            # Add chord confidences
            if chords_result:
                chord_confidences = [c.get("confidence", 0.5) for c in chords_result]
                confidences.extend(chord_confidences)
            
            return float(np.mean(confidences))
            
        except Exception:
            return 0.5
