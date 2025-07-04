import React, { useState } from 'react';
import { Music, Play, Square, Download } from 'lucide-react';
import YouTubeUrlInput from './components/YouTubeUrlInput';
import WaveformViewer from './components/WaveformViewer';
import AnalysisPanel from './components/AnalysisPanel';
import LegalDisclaimer from './components/LegalDisclaimer';
import { AnalysisResult, JobStatus } from './types/analysis';

function App() {
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus>('idle');
  const [waveformData, setWaveformData] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [trimSelection, setTrimSelection] = useState<{ start: number; end: number } | null>(null);

  const handleJobCreated = (jobId: string) => {
    setCurrentJob(jobId);
    setJobStatus('processing');
  };

  const handleWaveformLoaded = (data: any) => {
    setWaveformData(data);
    setJobStatus('ready');
  };

  const handleAnalysisComplete = (result: AnalysisResult) => {
    setAnalysisResult(result);
    setJobStatus('analyzed');
  };

  const handleTrimSelection = (start: number, end: number) => {
    setTrimSelection({ start, end });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Music className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">SongSensei</h1>
              <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">MVP</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Status: <span className="capitalize font-medium">{jobStatus}</span>
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* YouTube URL Input */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              1. Load YouTube Video
            </h2>
            <YouTubeUrlInput 
              onJobCreated={handleJobCreated}
              onShowDisclaimer={() => setShowDisclaimer(true)}
              disabled={jobStatus === 'processing'}
            />
          </div>

          {/* Waveform Viewer */}
          {(jobStatus === 'processing' || waveformData) && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                2. Trim Audio Segment
              </h2>
              <WaveformViewer
                jobId={currentJob}
                data={waveformData}
                onDataLoaded={handleWaveformLoaded}
                onTrimSelection={handleTrimSelection}
                isLoading={jobStatus === 'processing'}
              />
            </div>
          )}

          {/* Analysis Controls */}
          {trimSelection && jobStatus === 'ready' && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                3. Analyze Musical Content
              </h2>
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  Selected: {trimSelection.start.toFixed(1)}s - {trimSelection.end.toFixed(1)}s
                  ({(trimSelection.end - trimSelection.start).toFixed(1)}s duration)
                </div>
                <button 
                  className="btn-primary"
                  onClick={() => {
                    setJobStatus('analyzing');
                    // TODO: Trigger analysis
                  }}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Analyze Chords & Tabs
                </button>
              </div>
            </div>
          )}

          {/* Analysis Results */}
          {analysisResult && (
            <AnalysisPanel 
              result={analysisResult}
              jobId={currentJob}
              trimSelection={trimSelection}
            />
          )}

          {/* Loading State */}
          {jobStatus === 'analyzing' && (
            <div className="card">
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="loading-dots mb-4">
                    <div></div>
                    <div></div>
                    <div></div>
                  </div>
                  <p className="text-gray-600">Analyzing musical content...</p>
                  <p className="text-sm text-gray-500 mt-2">
                    This may take 20-40 seconds for high-accuracy results
                  </p>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              SongSensei MVP - Educational use only
            </div>
            <div className="flex items-center space-x-4">
              <span>Powered by yt-dlp, Essentia, madmom & music21</span>
            </div>
          </div>
        </div>
      </footer>

      {/* Legal Disclaimer Modal */}
      {showDisclaimer && (
        <LegalDisclaimer 
          onAccept={() => setShowDisclaimer(false)}
          onCancel={() => setShowDisclaimer(false)}
        />
      )}
    </div>
  );
}

export default App;
