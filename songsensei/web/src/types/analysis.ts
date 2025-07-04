export type JobStatus = 'idle' | 'processing' | 'ready' | 'analyzing' | 'analyzed' | 'failed';

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

export interface AnalysisResult {
  key: string;
  tempo: number;
  time_signature: string;
  confidence: number;
  chords: ChordInfo[];
  tab: {
    measures: TabMeasure[];
    tempo: number;
    time_signature: string;
    tuning: string[];
    capo: number;
  };
  key_changes?: Array<{
    time: number;
    from_key: string;
    to_key: string;
    confidence: number;
  }>;
  modulations?: Array<{
    time: number;
    type: string;
    confidence: number;
  }>;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message?: string;
  estimatedTime?: string;
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
