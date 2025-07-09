import React, { useState, useEffect } from 'react';
import { api } from '../lib/api';
import WaveformViewer from './WaveformViewer';

// Define the API response structure
interface SpleeterResponse {
  success: boolean;
  tracks?: {
    vocals: string;
    drums: string;
    bass: string;
    other: string;
  };
  error?: string;
}

interface SpleeterTracksProps {
  audioUrl: string | null;
  jobId: string | null;
  onTrackSelected: (trackUrl: string, trackType: string) => void;
}

type TrackType = 'vocals' | 'drums' | 'bass' | 'other';

interface TrackData {
  url: string;
  type: TrackType;
  label: string;
  waveformData?: any;
}

const SpleeterTracks: React.FC<SpleeterTracksProps> = ({ audioUrl, jobId, onTrackSelected }) => {
  const [tracks, setTracks] = useState<TrackData[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTrack, setSelectedTrack] = useState<TrackType | null>(null);

  // Process audio through Spleeter when audioUrl changes
  useEffect(() => {
    if (!audioUrl || !jobId) return;
    
    const processTracks = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Call API endpoint to process with Spleeter
        const response = await api.post<SpleeterResponse>('/api/analysis/separate-tracks', {
          jobId,
          audioUrl
        });
        
        if (response.data.success && response.data.tracks) {
          // Convert API response to track data
          const trackData: TrackData[] = [
            {
              url: response.data.tracks.vocals,
              type: 'vocals' as TrackType,
              label: 'Vocals'
            },
            {
              url: response.data.tracks.drums,
              type: 'drums' as TrackType,
              label: 'Drums'
            },
            {
              url: response.data.tracks.bass,
              type: 'bass' as TrackType,
              label: 'Bass'
            },
            {
              url: response.data.tracks.other,
              type: 'other' as TrackType,
              label: 'Other Instruments'
            }
          ].filter((track): track is TrackData => Boolean(track.url)); // Filter out any missing tracks
          
          setTracks(trackData);
        } else {
          setError(response.data.error || 'Failed to process tracks');
        }
      } catch (err) {
        console.error('Error processing tracks:', err);
        setError('Error connecting to Spleeter service');
      } finally {
        setIsLoading(false);
      }
    };
    
    processTracks();
  }, [audioUrl, jobId]);

  // Handle track selection
  const handleTrackSelect = (track: TrackData) => {
    setSelectedTrack(track.type);
    onTrackSelected(track.url, track.type);
  };

  // Handle track waveform data loaded
  const handleTrackDataLoaded = (trackType: TrackType, waveformData: any) => {
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
          Spleeter is processing your audio into separate instrument tracks...
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
      <h3 className="text-xl font-semibold">Separated Instrument Tracks</h3>
      <p className="text-gray-600">
        Select a track to analyze or listen to the isolated instruments:
      </p>
      
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
        <h4 className="font-medium text-yellow-800">About Spleeter</h4>
        <p className="mt-1 text-gray-700">
          Spleeter is an AI-powered source separation tool that can isolate different 
          instruments from mixed audio. This makes it easier to analyze specific parts 
          of a song, like guitar, bass, or vocals.
        </p>
      </div>
    </div>
  );
};

export default SpleeterTracks;
