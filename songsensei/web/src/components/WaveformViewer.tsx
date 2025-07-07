import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { api } from '../lib/api';
import { JobStatusResponse } from '../types/analysis';

interface WaveformViewerProps {
  jobId: string | null;
  data: any;
  onDataLoaded: (data: any) => void;
  onTrimSelection: (start: number, end: number) => void;
  isLoading: boolean;
}

const WaveformViewer: React.FC<WaveformViewerProps> = ({
  jobId,
  data,
  onDataLoaded,
  onTrimSelection,
  isLoading
}) => {
  const waveformRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [selection, setSelection] = useState<{ start: number; end: number } | null>(null);
  const [duration, setDuration] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<number | null>(null);


  useEffect(() => {
    if (data && waveformRef.current) {
      renderWaveform();
    }
  }, [data]);

  useEffect(() => {
    if (!jobId) return;
    let intervalId: NodeJS.Timeout;
    intervalId = setInterval(async () => {
      try {
const resp = await api.get<JobStatusResponse>(`/api/analysis/status/${jobId}`);
        const { status, waveform_data } = resp.data;
        if (status === 'completed' && waveform_data) {
          onDataLoaded(waveform_data);
          setDuration(waveform_data.duration);
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Status polling error:', err);
        clearInterval(intervalId);
      }
    }, 2000);
    return () => clearInterval(intervalId);
  }, [jobId, data, isLoading, onDataLoaded]);

  const renderWaveform = () => {
    if (!waveformRef.current || !data) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const container = waveformRef.current;
    const width = container.clientWidth;
    const height = 120;

    canvas.width = width;
    canvas.height = height;
    canvas.className = `w-full h-full ${isDragging ? 'cursor-crosshair' : 'cursor-pointer'}`;

    // Clear canvas
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, 0, width, height);

    // Draw waveform
    const peaks = data.peaks;
    const barWidth = width / peaks.length;

    peaks.forEach((peak: number, i: number) => {
      const barHeight = peak * height * 0.8;
      const x = i * barWidth;
      const y = (height - barHeight) / 2;

      ctx.fillStyle = '#3b82f6';
      ctx.fillRect(x, y, Math.max(1, barWidth - 1), barHeight);
    });

    // Draw selection overlay
    if (selection) {
      const startX = (selection.start / data.duration) * width;
      const endX = (selection.end / data.duration) * width;
      
      ctx.fillStyle = 'rgba(59, 130, 246, 0.3)';
      ctx.fillRect(startX, 0, endX - startX, height);
    }

    // Replace existing canvas
    container.innerHTML = '';
    container.appendChild(canvas);

    // Add mouse event handlers for drag selection
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseUp);
  };

  const getTimeFromMouseEvent = (e: MouseEvent): number => {
    if (!data || !waveformRef.current) return 0;
    
    const rect = waveformRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const time = (x / rect.width) * data.duration;
    
    // Clamp to valid range
    return Math.max(0, Math.min(data.duration, time));
  };

  const handleMouseDown = (e: MouseEvent) => {
    const clickTime = getTimeFromMouseEvent(e);
    setIsDragging(true);
    setDragStart(clickTime);
    setSelection({ start: clickTime, end: clickTime });
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || dragStart === null) return;
    
    const currentTime = getTimeFromMouseEvent(e);
    const start = Math.min(dragStart, currentTime);
    const end = Math.max(dragStart, currentTime);
    
    setSelection({ start, end });
  };

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false);
      setDragStart(null);
    }
  };

  useEffect(() => {
    if (selection) {
      onTrimSelection(selection.start, selection.end);
      renderWaveform(); // Re-render to show selection
    }
  }, [selection, onTrimSelection]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const resetSelection = () => {
    setSelection(null);
    renderWaveform();
  };

  if (isLoading) {
    return (
      <div className="waveform-container h-32 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="loading-dots mb-2">
            <div className="bg-white"></div>
            <div className="bg-white"></div>
            <div className="bg-white"></div>
          </div>
          <p className="text-sm">Extracting audio...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="waveform-container h-32 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <p>Waveform will appear here after audio extraction</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Waveform Display */}
      <div className="waveform-container h-32">
        <div ref={waveformRef} className="w-full h-full" />
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button className="btn-outline">
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>
          <span className="text-sm text-gray-600">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>

        <div className="flex items-center space-x-4">
          {selection && (
            <>
              <span className="text-sm text-gray-600">
                Selection: {formatTime(selection.start)} - {formatTime(selection.end)}
                ({formatTime(selection.end - selection.start)})
              </span>
              <button onClick={resetSelection} className="btn-outline">
                <RotateCcw className="h-4 w-4 mr-1" />
                Reset
              </button>
            </>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-sm text-gray-600">
          <strong>Instructions:</strong> Click and drag on the waveform to select a region 
          for analysis. Select a segment of 10-30 seconds for best results.
        </p>
      </div>
    </div>
  );
};

export default WaveformViewer;
