import axios from 'axios';
import { AnalysisResult } from '../types/analysis';

// Define response types
export interface CloudServiceStatus {
  status: string;
  services: {
    demucs: { enabled: boolean; healthy: boolean; error?: string };
    spleeter: { enabled: boolean; healthy: boolean; error?: string };
    colab: { enabled: boolean; healthy: boolean; error?: string };
    render: { enabled: boolean; healthy: boolean; error?: string };
    github_actions: { enabled: boolean; healthy: boolean; error?: string };
  };
}

export interface WakeSpacesResult {
  success: boolean;
  enabled: boolean;
  spleeter: boolean;
  demucs: boolean;
  timestamp: string;
  message?: string;
  error?: string;
}

export enum SeparationModel {
  DEMUCS = 'demucs',
  SPLEETER = 'spleeter'
}

export interface SeparatedTracks {
  success: boolean;
  tracks: Record<string, string>; // Map of track name to URL
  cloud_service?: string;
  fallback?: boolean;
  error?: string; // Error message if separation failed
}

export interface CloudOptions {
  sourceSeparation?: boolean;
  advancedStructure?: boolean;
  enhancedKeyDetection?: boolean;
}

export const api = axios.create({
  // eslint-disable-next-line @typescript-eslint/strict-boolean-expressions
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:4000',
  headers: { 'Content-Type': 'application/json' }
});

// Song analysis functions
export const ingestYouTubeUrl = async (youtubeUrl: string, userConsent: boolean = true) => {
  const response = await api.post('/api/analysis/ingest', { youtubeUrl, userConsent });
  return response.data;
};

export const checkStatus = async (jobId: string) => {
  const response = await api.get(`/api/analysis/status/${jobId}`);
  return response.data;
};

export const analyzeSegment = async (
  jobId: string, 
  startTime: number, 
  endTime: number,
  enableCloudServices: boolean = false,
  cloudOptions?: CloudOptions
) => {
  const response = await api.post('/api/analysis/analyze', {
    jobId,
    startTime,
    endTime,
    analysisVersion: '2.0',
    enableCloudServices,
    cloudOptions
  });
  return response.data;
};

export const getAnalysisResult = async (jobId: string) => {
  const response = await api.get<{ job_id: string; status: string; analysis: AnalysisResult }>(
    `/api/analysis/analysis/${jobId}`
  );
  return response.data;
};

export const getCloudStatus = async (): Promise<CloudServiceStatus> => {
  const response = await api.get<CloudServiceStatus>('/api/analysis/cloud-status');
  return response.data;
};

export const wakeHuggingFaceSpaces = async (): Promise<WakeSpacesResult> => {
  const response = await api.post<WakeSpacesResult>('/api/analysis/wake-spaces');
  return response.data;
};

// Track separation function
export const separateTracks = async (
  jobId: string,
  audioUrl: string,
  model: SeparationModel = SeparationModel.DEMUCS
): Promise<SeparatedTracks> => {
  const response = await api.post<SeparatedTracks>('/api/analysis/separate-tracks', {
    jobId,
    audioUrl,
    model
  });
  return response.data;
};
