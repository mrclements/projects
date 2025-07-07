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

class SongSegment(BaseModel):
    id: str
    label: str  # "Intro", "Verse", "Chorus", "Bridge", "Solo", "Outro"
    start_time: float
    end_time: float
    confidence: float
    characteristics: Optional[Dict[str, float]] = None  # energy, complexity, repetition_score

class KeyChange(BaseModel):
    time: float
    from_key: str
    to_key: str
    confidence: float

class TimeSignatureChange(BaseModel):
    time: float
    from_signature: str
    to_signature: str
    confidence: float

class Modulation(BaseModel):
    time: float
    type: str  # "relative", "parallel", "chromatic", "enharmonic"
    confidence: float

class TabExports(BaseModel):
    gpFileUrl: Optional[str] = None     # Guitar Pro file
    pdfUrl: Optional[str] = None        # PDF sheet music
    musicXmlUrl: Optional[str] = None   # MusicXML format
    midiUrl: Optional[str] = None       # MIDI file

class ProcessingMetadata(BaseModel):
    cloudServices: Optional[List[str]] = None  # Services used: ["spleeter", "colab", "render"]
    sourceSeparation: Optional[bool] = None
    processingTime: Optional[float] = None
    queuePosition: Optional[int] = None

class QualityMetrics(BaseModel):
    chordAccuracy: Optional[float] = None
    structureConfidence: Optional[float] = None
    keyStability: Optional[float] = None
    rhythmConsistency: Optional[float] = None

class AnalysisResult(BaseModel):
    # Core V1 fields
    key: str
    tempo: float
    time_signature: str
    confidence: float
    chords: List[ChordInfo]
    
    # V2 Extensions
    analysisVersion: str = "2.0"
    
    # Song structure analysis
    segments: List[SongSegment] = []
    
    # Enhanced key and time signature tracking
    key_changes: List[KeyChange] = []
    time_signature_changes: List[TimeSignatureChange] = []
    modulations: List[Modulation] = []
    
    # Enhanced tab generation with export options
    tab: Dict[str, Any]  # Keep flexible for now, will enhance later
    
    # Cloud processing metadata
    processing: Optional[ProcessingMetadata] = None
    
    # Quality metrics
    quality: Optional[QualityMetrics] = None

class Job(BaseModel):
    job_id: str
    status: JobStatus
    youtube_url: str
    created_at: Optional[str] = None
    audio_path: Optional[str] = None
    waveform_data: Optional[WaveformData] = None
    analysis_result: Optional[AnalysisResult] = None
    error: Optional[str] = None
