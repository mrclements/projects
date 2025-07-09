import React, { useState, useEffect } from 'react';
import { api, getCloudStatus, analyzeSegment, CloudServiceStatus, CloudOptions } from './lib/api';
import { Music, Play, Cloud, CloudOff, Info } from 'lucide-react';
import YouTubeUrlInput from './components/YouTubeUrlInput';
import WaveformViewer from './components/WaveformViewer';
import SpleeterTracks from './components/SpleeterTracks';
import AnalysisPanel from './components/AnalysisPanel';
import LegalDisclaimer from './components/LegalDisclaimer';
import { AnalysisResult, JobStatus, AnalysisResponse } from './types/analysis';

function App() {
  const [currentJob, setCurrentJob] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus>('idle');
  const [waveformData, setWaveformData] = useState<any>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [trimSelection, setTrimSelection] = useState<{ start: number; end: number } | null>(null);
  const [enableCloudServices, setEnableCloudServices] = useState(false);
  const [cloudStatus, setCloudStatus] = useState<CloudServiceStatus | null>(null);
  const [selectedTrack, setSelectedTrack] = useState<string | null>(null);
  const [selectedTrackType, setSelectedTrackType] = useState<string | null>(null);
  const [showSpleeterTracks, setShowSpleeterTracks] = useState(false);
  const [cloudOptions, setCloudOptions] = useState<CloudOptions>({
    sourceSeparation: true,
    advancedStructure: true,
    enhancedKeyDetection: true
  });

  const handleJobCreated = (jobId: string) => {
    setCurrentJob(jobId);
    setJobStatus('processing');
  };

  const handleWaveformLoaded = (data: any) => {
    setWaveformData(data);
    setJobStatus('ready');
  };

  const handleTrimSelection = (start: number, end: number) => {
    setTrimSelection({ start, end });
  };

  // Fetch cloud service status on load
  useEffect(() => {
    const fetchCloudStatus = async () => {
      try {
        const status = await getCloudStatus();
        setCloudStatus(status);
      } catch (error) {
        console.error('Failed to fetch cloud service status:', error);
      }
    };
    
    fetchCloudStatus();
    // Refresh status every 30 seconds
    const intervalId = setInterval(fetchCloudStatus, 30000);
    
    return () => clearInterval(intervalId);
  }, []);

  const triggerAnalysis = async () => {
    if (!currentJob || !trimSelection) return;
    setJobStatus('analyzing');
    try {
      await analyzeSegment(
        currentJob,
        trimSelection.start,
        trimSelection.end,
        enableCloudServices,
        cloudOptions
      );
      const interval = setInterval(async () => {
        try {
          const resp = await api.get<AnalysisResponse>(`/api/analysis/analysis/${currentJob}`);
          if (resp.data.status === 'completed' && resp.data.analysis) {
            setAnalysisResult(resp.data.analysis as AnalysisResult);
            setJobStatus('analyzed');
            clearInterval(interval);
          }
        } catch (err) {
          console.error('Analysis polling error:', err);
          clearInterval(interval);
          setJobStatus('failed');
        }
      }, 2000);
    } catch (err) {
      console.error('Analysis start error:', err);
      setJobStatus('failed');
    }
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
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setEnableCloudServices(!enableCloudServices)}
                  className={`flex items-center px-3 py-1 rounded text-sm border ${
                    enableCloudServices 
                      ? 'bg-blue-50 text-blue-700 border-blue-300' 
                      : 'bg-gray-50 text-gray-700 border-gray-300'
                  }`}
                  title={enableCloudServices ? "Cloud services enabled" : "Cloud services disabled"}
                >
                  {enableCloudServices ? (
                    <><Cloud className="h-4 w-4 mr-1" /> Cloud ON</>
                  ) : (
                    <><CloudOff className="h-4 w-4 mr-1" /> Cloud OFF</>
                  )}
                </button>
                {cloudStatus && (
                  <div className="relative group">
                    <Info className="h-4 w-4 text-gray-400 cursor-help" />
                    <div className="absolute right-0 mt-2 w-64 p-2 bg-white shadow-lg rounded-md border text-xs hidden group-hover:block z-10">
                      <p className="font-semibold mb-1">Cloud Services Status:</p>
                      <ul className="space-y-1">
                        {Object.entries(cloudStatus.services).map(([service, status]) => (
                          <li key={service} className="flex items-center justify-between">
                            <span>{service}</span>
                            <span className={`px-1.5 py-0.5 rounded-full ${
                              status.enabled && status.healthy 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {status.enabled && status.healthy ? 'Available' : 'Unavailable'}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
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
              
              {jobStatus === 'ready' && enableCloudServices && (
                <div className="mt-4 flex justify-end">
                  <button
                    onClick={() => setShowSpleeterTracks(true)}
                    className="btn-outline flex items-center space-x-2"
                  >
                    <Cloud className="h-4 w-4" />
                    <span>Separate Instrument Tracks (Spleeter)</span>
                  </button>
                </div>
              )}
            </div>
          )}
          
          {/* Spleeter Tracks */}
          {showSpleeterTracks && currentJob && (
            <div className="card">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                2.5. Separate Instrument Tracks
              </h2>
              <SpleeterTracks 
                audioUrl={currentJob ? `/api/analysis/audio/${currentJob}` : null}
                jobId={currentJob}
                onTrackSelected={(trackUrl, trackType) => {
                  setSelectedTrack(trackUrl);
                  setSelectedTrackType(trackType);
                }}
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
                <div className="flex items-center space-x-3">
                  {enableCloudServices && (
                    <div className="flex items-center space-x-2 bg-blue-50 p-2 rounded">
                      <Cloud className="h-4 w-4 text-blue-700" />
                      <span className="text-xs text-blue-700">
                        {selectedTrackType 
                          ? `Analyzing ${selectedTrackType} track` 
                          : "Using cloud processing"}
                      </span>
                    </div>
                  )}
                  <button
                    className="btn-primary"
                    onClick={triggerAnalysis}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Analyze Chords & Tabs
                  </button>
                </div>
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
              <span>Powered by yt-dlp, Essentia, madmom & music21{enableCloudServices ? ' + Cloud Services' : ''}</span>
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
