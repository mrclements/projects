export type JobStatus = 'idle' | 'processing' | 'ready' | 'completed' | 'analyzing' | 'analyzed' | 'failed';

export interface WaveformData {
  peaks: number[];
  duration: number;
  sample_rate: number;
  metadata?: {
    title?: string;
    artist?: string;
    duration?: string;
    [key: string]: any;
  };
}

export interface ChordInfo {
  time: number;
  chord: string;
  confidence: number;
  is_diatonic: boolean;
  root?: string;
  quality?: string;
}

export interface TabMeasure {
  chord: string;
  frets: number[]; // 6 strings, fret numbers
  fingering?: number[]; // finger positions
  strumming_pattern?: string;
  time: number;
}

export interface SongSegment {
  id: string;
  label: string; // "Intro", "Verse", "Chorus", "Bridge", "Solo", "Outro"
  start_time: number;
  end_time: number;
  confidence: number;
  characteristics?: {
    energy?: number;
    complexity?: number;
    repetition_score?: number;
  };
}

export interface TimeSignatureChange {
  time: number;
  from_signature: string;
  to_signature: string;
  confidence: number;
}

export interface AnalysisResult {
  // Core V1 fields
  key: string;
  tempo: number;
  time_signature: string;
  confidence: number;
  chords: ChordInfo[];
  
  // V2 Extensions
  analysisVersion: "1.0" | "2.0";
  
  // Song structure analysis
  segments: SongSegment[];
  
  // Enhanced key and time signature tracking
  key_changes: Array<{
    time: number;
    from_key: string;
    to_key: string;
    confidence: number;
  }>;
  
  time_signature_changes: TimeSignatureChange[];
  
  modulations: Array<{
    time: number;
    type: string; // "relative", "parallel", "chromatic", "enharmonic"
    confidence: number;
  }>;
  
  // Enhanced tab generation with export options
  tab: {
    measures: TabMeasure[];
    tempo: number;
    time_signature: string;
    tuning: string[];
    capo: number;
    // V2 export formats
    exports?: {
      gpFileUrl?: string;     // Guitar Pro file
      pdfUrl?: string;        // PDF sheet music
      musicXmlUrl?: string;   // MusicXML format
      midiUrl?: string;       // MIDI file
    };
  };
  
  // Cloud processing metadata
  processing?: {
    cloudServices?: string[];  // Services used: ["spleeter", "colab", "render"]
    sourceSeparation?: boolean;
    processingTime?: number;
    queuePosition?: number;
  };
  
  // Quality metrics
  quality?: {
    chordAccuracy?: number;
    structureConfidence?: number;
    keyStability?: number;
    rhythmConsistency?: number;
  };
}

export interface JobResponse {
  jobId: string;        // ✅ camel-case
  status?: string;
  message?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  waveform_data?: WaveformData;
  error?: string;
}

export interface AnalysisResponse {
  job_id: string;
  status: string;
  analysis?: AnalysisResult;
  message?: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: any;
}
