import React, { useEffect, useRef, useState } from 'react';
import type { MouseEvent as ReactMouseEvent } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { api } from '../lib/api';
import { JobStatusResponse, WaveformData } from '../types/analysis';

interface WaveformViewerProps {
  jobId: string | null;
  data: WaveformData | null;
  onDataLoaded: (data: WaveformData) => void;
  onTrimSelection: (start: number, end: number) => void;
  isLoading: boolean;
}

interface SelectionRange {
  start: number;
  end: number;
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
  const [selection, setSelection] = useState<SelectionRange | null>(null);
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

  const renderWaveform = (): void => {
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
    if (selection && data) {
      const audioDuration = data.duration;
      const startX = (selection.start / audioDuration) * width;
      const endX = (selection.end / audioDuration) * width;
      
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

  const getTimeFromMouseEvent = (e: MouseEvent | ReactMouseEvent): number => {
    if (!data || !waveformRef.current) return 0;
    
    const audioDuration = data.duration; // Store in local variable for TypeScript
    const rect = waveformRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const time = (x / rect.width) * audioDuration;
    
    // Clamp to valid range
    return Math.max(0, Math.min(audioDuration, time));
  };

  const handleMouseDown = (e: MouseEvent): void => {
    const clickTime = getTimeFromMouseEvent(e);
    
    // Instead of creating a fixed-size window, set both start and end to the click point
    // This will allow the user to drag to define the actual selection size
    setIsDragging(true);
    setDragStart(clickTime);
    
    // Initialize selection to a zero-length selection at click point
    // It will be expanded as the user drags
    setSelection({ start: clickTime, end: clickTime });
  };

  const handleMouseMove = (e: MouseEvent): void => {
    if (!isDragging || dragStart === null || !data) return;
    
    const currentTime = getTimeFromMouseEvent(e);
    const maxDuration = 30; // Maximum 30 seconds selection
    const audioDuration = data.duration; // Store duration in local variable to satisfy TypeScript
    
    // Use the initial click position as the anchor point
    // and the current mouse position as the moving point
    let start = Math.min(dragStart, currentTime);
    let end = Math.max(dragStart, currentTime);
    
    // Ensure selection doesn't exceed maximum duration
    if (end - start > maxDuration) {
      if (currentTime > dragStart) {
        // If dragging to the right (expanding end)
        end = start + maxDuration;
      } else {
        // If dragging to the left (expanding start)
        start = end - maxDuration;
      }
    }
    
    // Ensure we don't go beyond boundaries
    start = Math.max(0, start);
    end = Math.min(audioDuration, end);
    
    setSelection({ start, end });
  };

  const handleMouseUp = (): void => {
    if (isDragging && selection && data) {
      setIsDragging(false);
      setDragStart(null);
      
      // Check if the selection is too small (less than 1 second)
      // This prevents accidental clicks from creating tiny selections
      if (selection.end - selection.start < 1) {
        // If it's basically a click (very small selection), either:
        // 1. Clear the selection if we want clicks to reset, or
        // 2. Create a reasonable default selection around the click point
        const clickPoint = selection.start;
        const minDuration = 5; // Minimum 5 seconds for a good analysis
        const audioDuration = data.duration; // Store duration in local variable
        
        // Create a 5-second selection centered on the click point
        let start = Math.max(0, clickPoint - (minDuration / 2));
        let end = start + minDuration;
        
        // If the end would go beyond the duration, shift the window back
        if (end > audioDuration) {
          end = audioDuration;
          start = Math.max(0, end - minDuration);
        }
        
        setSelection({ start, end });
      }
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

  const resetSelection = (): void => {
    setSelection(null);
    renderWaveform();
  };
  
  const selectFullTrack = (): void => {
    if (data && data.duration) {
      setSelection({ start: 0, end: data.duration });
      renderWaveform();
    }
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
          <button onClick={selectFullTrack} className="btn-outline bg-blue-50">
            <span className="mr-1">🎵</span>
            Full Track
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm text-gray-600">
        <strong>Instructions:</strong> Click and drag on the waveform to select a region 
        for analysis. The selection will be highlighted in blue. For a precise selection, 
        click where you want to start and drag to where you want to end. 
        For best results, select a segment of 5-30 seconds, or use the "Full Track" 
        button to analyze the entire audio.
      </p>
      </div>
    </div>
  );
};

export default WaveformViewer;
