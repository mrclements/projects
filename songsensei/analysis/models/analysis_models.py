from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class JobStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ANALYZING = "analyzing"

class WaveformData(BaseModel):
    peaks: List[float]
    duration: float
    sample_rate: int
    metadata: Optional[Dict[str, Any]] = None

class ChordInfo(BaseModel):
    time: float
    chord: str
    confidence: float
    is_diatonic: bool
    root: Optional[str] = None
    quality: Optional[str] = None

class TabMeasure(BaseModel):
    chord: str
    frets: List[int]  # 6 strings, fret numbers
    fingering: Optional[List[int]] = None  # finger positions
    strumming_pattern: Optional[str] = None

class AnalysisResult(BaseModel):
    key: str
    tempo: float
    time_signature: str
    confidence: float
    chords: List[ChordInfo]
    tab: Dict[str, Any]
    key_changes: Optional[List[Dict[str, Any]]] = None
    modulations: Optional[List[Dict[str, Any]]] = None

class Job(BaseModel):
    job_id: str
    status: JobStatus
    youtube_url: str
    created_at: Optional[str] = None
    audio_path: Optional[str] = None
    waveform_data: Optional[WaveformData] = None
    analysis_result: Optional[AnalysisResult] = None
    error: Optional[str] = None
