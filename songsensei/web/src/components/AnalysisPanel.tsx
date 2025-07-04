import React, { useState } from 'react';
import { Music, Play, Download, Info } from 'lucide-react';
import { AnalysisResult } from '../types/analysis';

interface AnalysisPanelProps {
  result: AnalysisResult;
  jobId: string | null;
  trimSelection: { start: number; end: number } | null;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  result,
  jobId,
  trimSelection
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'chords' | 'tabs'>('overview');

  const renderChordDiagram = (chord: string, frets: number[]) => {
    return (
      <div className="chord-diagram text-center">
        <h4 className="font-semibold text-sm mb-2">{chord}</h4>
        <div className="relative">
          {/* Guitar neck visualization */}
          <div className="grid grid-cols-6 gap-1 mb-2">
            {frets.map((fret, stringIndex) => (
              <div key={stringIndex} className="text-center">
                <div className="w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center text-xs font-mono">
                  {fret === 0 ? 'O' : fret}
                </div>
              </div>
            ))}
          </div>
          <div className="text-xs text-gray-500 grid grid-cols-6 gap-1">
            {['E', 'A', 'D', 'G', 'B', 'E'].map((string, i) => (
              <div key={i} className="text-center">{string}</div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderTabNotation = () => {
    return (
      <div className="tab-notation">
        <div className="mb-4">
          <div className="text-sm font-semibold mb-2">Guitar Tablature</div>
          <div className="text-xs text-gray-600 mb-2">
            Tempo: {result.tempo} BPM | Key: {result.key} | Time Signature: {result.time_signature}
          </div>
        </div>
        
        {/* TAB Lines */}
        <div className="space-y-1 text-xs">
          {result.tab.tuning.map((tuning, stringIndex) => (
            <div key={stringIndex} className="flex items-center">
              <span className="w-4 text-right mr-2">{tuning}|</span>
              <div className="flex">
                {result.tab.measures.map((measure, measureIndex) => (
                  <span key={measureIndex} className="mr-4">
                    {measure.frets[stringIndex]}
                    {measureIndex < result.tab.measures.length - 1 ? '-' : ''}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Chord names below */}
        <div className="mt-4 pt-2 border-t border-gray-200">
          <div className="flex">
            <span className="w-6 mr-2"></span>
            {result.tab.measures.map((measure, index) => (
              <span key={index} className="mr-4 text-sm font-medium">
                {measure.chord}
              </span>
            ))}
          </div>
        </div>

        {/* Strumming pattern */}
        <div className="mt-2">
          <div className="flex">
            <span className="w-6 mr-2 text-xs">Strum:</span>
            {result.tab.measures.map((measure, index) => (
              <span key={index} className="mr-4 text-xs text-gray-600">
                {measure.strumming_pattern || 'D D U D U'}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header with confidence score */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Analysis Results</h2>
        <div className="flex items-center space-x-2">
          <Info className="h-4 w-4 text-blue-500" />
          <span className="text-sm text-gray-600">
            Confidence: {(result.confidence * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'chords', label: 'Chord Progression' },
            { id: 'tabs', label: 'Guitar Tab' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="py-4">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-2">Musical Key</h3>
              <p className="text-2xl font-bold text-primary-600">{result.key}</p>
            </div>
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-2">Tempo</h3>
              <p className="text-2xl font-bold text-green-600">{result.tempo} BPM</p>
            </div>
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-2">Time Signature</h3>
              <p className="text-2xl font-bold text-purple-600">{result.time_signature}</p>
            </div>
          </div>
        )}

        {activeTab === 'chords' && (
          <div className="space-y-6">
            {/* Chord progression timeline */}
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Chord Progression</h3>
              <div className="space-y-2">
                {result.chords.map((chord, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-500 w-16">
                        {Math.floor(chord.time / 60)}:{(chord.time % 60).toFixed(0).padStart(2, '0')}
                      </span>
                      <span className="font-semibold text-lg">{chord.chord}</span>
                      {!chord.is_diatonic && (
                        <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded">
                          Non-diatonic
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {(chord.confidence * 100).toFixed(0)}% confidence
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Chord diagrams */}
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4">Chord Diagrams</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {result.tab.measures.map((measure, index) => 
                  renderChordDiagram(measure.chord, measure.frets)
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tabs' && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Guitar Tablature</h3>
              <button className="btn-outline">
                <Download className="h-4 w-4 mr-2" />
                Export Tab
              </button>
            </div>
            {renderTabNotation()}
          </div>
        )}
      </div>

      {/* Playback Controls */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Playback & Practice</h3>
        <div className="flex items-center space-x-4">
          <button className="btn-primary">
            <Play className="h-4 w-4 mr-2" />
            Play with Chords
          </button>
          <button className="btn-outline">
            <Music className="h-4 w-4 mr-2" />
            Loop Section
          </button>
          <div className="text-sm text-gray-600">
            {trimSelection && (
              <>Segment: {trimSelection.start.toFixed(1)}s - {trimSelection.end.toFixed(1)}s</>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPanel;
