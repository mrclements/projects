import React, { useState, useEffect } from 'react';
import { separateTracks, SeparationModel } from '../lib/api';
import WaveformViewer from './WaveformViewer';

// Define the API response structure for dynamic stems
interface SeparatedTracksResponse {
  success: boolean;
  tracks?: Record<string, string>; // Dynamic mapping of track type to URL
  cloud_service?: string;
  error?: string;
}

interface SeparatedTracksProps {
  audioUrl: string | null;
  jobId: string | null;
  onTrackSelected: (trackUrl: string, trackType: string) => void;
  model?: SeparationModel;
}

interface TrackData {
  url: string;
  type: string;
  label: string;
  waveformData?: any;
}

const SeparatedTracks: React.FC<SeparatedTracksProps> = ({ 
  audioUrl, 
  jobId, 
  onTrackSelected,
  model = SeparationModel.DEMUCS 
}) => {
  const [tracks, setTracks] = useState<TrackData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [modelInfo, setModelInfo] = useState<string | null>(null);
  const [currentModel, setCurrentModel] = useState<SeparationModel>(model);

  // Process audio through source separation when audioUrl changes
  useEffect(() => {
    if (!audioUrl || !jobId) return;
    
    const processTracks = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Call API endpoint to process with source separation
        const response = await separateTracks(jobId, audioUrl, currentModel);
        
        if (response.success && response.tracks) {
          // Convert API response to track data
          const tracksData: TrackData[] = Object.entries(response.tracks)
            .map(([key, url]) => {
              // Convert key like "vocals_path" to "vocals"
              const type = key.replace('_path', '');
              return {
                url,
                type,
                label: formatTrackName(type)
              };
            })
            .filter((track): track is TrackData => Boolean(track.url));
          
          setTracks(tracksData);
          
          // Set model info for display
          if (response.cloud_service) {
            setModelInfo(response.cloud_service === 'demucs' 
              ? 'Hybrid-Transformer Demucs v4' 
              : 'Spleeter 4-stem');
          } else {
            // Default based on selected model
            setModelInfo(currentModel === SeparationModel.DEMUCS 
              ? 'Hybrid-Transformer Demucs v4' 
              : 'Spleeter 4-stem');
          }
        } else {
          setError(response.error !== undefined ? response.error : 'Failed to process tracks');
        }
      } catch (err) {
        console.error('Error processing tracks:', err);
        setError('Error connecting to source separation service');
      } finally {
        setIsLoading(false);
      }
    };
    
    processTracks();
  }, [audioUrl, jobId, currentModel]);

  // Format track name for display
  const formatTrackName = (type: string): string => {
    const name = type.replace(/_/g, ' ');
    return name.charAt(0).toUpperCase() + name.slice(1);
  };

  // Handle track selection
  const handleTrackSelect = (track: TrackData) => {
    setSelectedTrack(track.type);
    onTrackSelected(track.url, track.type);
  };

  // Handle track waveform data loaded
  const handleTrackDataLoaded = (trackType: string, waveformData: any) => {
    setTracks((prevTracks: TrackData[]) => 
      prevTracks.map((track: TrackData) => 
        track.type === trackType 
          ? { ...track, waveformData } 
          : track
      )
    );
  };

  if (isLoading) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-medium mb-4">Separating Tracks</h3>
        <div className="flex justify-center">
          <div className="loading-spinner"></div>
        </div>
        <p className="text-center mt-2 text-gray-600">
          Processing your audio into separate instrument tracks...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 rounded-lg border border-red-200">
        <h3 className="text-lg font-medium mb-2 text-red-700">Track Separation Failed</h3>
        <p className="text-red-600">{error}</p>
        <p className="mt-2 text-gray-600">
          Check your Hugging Face API token and connection, or try again later.
        </p>
      </div>
    );
  }

  if (tracks.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6 mt-8">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold">Separated Instrument Tracks</h3>
        
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Model:</span>
          <select 
            className="border rounded-md px-2 py-1 text-sm"
            value={currentModel}
            onChange={(e) => {
              const newModel = e.target.value as SeparationModel;
              setCurrentModel(newModel);
              // This will trigger the useEffect to re-run separation
              if (audioUrl && jobId) {
                setTracks([]);
              }
            }}
          >
            <option value={SeparationModel.DEMUCS}>Demucs v4</option>
            <option value={SeparationModel.SPLEETER}>Spleeter</option>
          </select>
        </div>
      </div>
      
      <p className="text-gray-600">
        Select a track to analyze or listen to the isolated instruments:
      </p>
      
      {modelInfo && (
        <div className="p-2 bg-blue-50 border border-blue-200 rounded-lg text-blue-800 text-sm">
          Using {modelInfo} for source separation
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tracks.map((track: TrackData) => (
          <div 
            key={track.type}
            className={`border rounded-lg p-4 ${
              selectedTrack === track.type ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            }`}
          >
            <div className="flex justify-between items-center mb-2">
              <h4 className="text-lg font-medium">{track.label}</h4>
              <button
                onClick={() => handleTrackSelect(track)}
                className={`px-3 py-1 rounded-full text-sm ${
                  selectedTrack === track.type
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                }`}
              >
                {selectedTrack === track.type ? 'Selected' : 'Select for Analysis'}
              </button>
            </div>
            
            <div className="audio-player mb-3">
              <audio 
                src={track.url} 
                controls 
                className="w-full"
                controlsList="nodownload"
              />
            </div>
            
            {/* Mini waveform visualization */}
            <div className="bg-gray-800 rounded h-16">
              {/* Placeholder for waveform visualization */}
              {/* We could implement a simplified version of WaveformViewer here */}
            </div>
          </div>
        ))}
      </div>
      
      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h4 className="font-medium text-yellow-800">About Source Separation</h4>
        <p className="mt-1 text-gray-700">
          This feature uses AI-powered source separation to isolate different instruments from mixed audio.
          Hybrid-Transformer Demucs v4 provides high-quality separation that makes it easier to analyze 
          specific parts of a song, like guitar, bass, or vocals.
        </p>
      </div>
    </div>
  );
};

export default SeparatedTracks;
