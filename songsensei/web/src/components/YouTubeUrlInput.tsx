import React, { useState } from 'react';
import axios from 'axios';
import { JobResponse } from '../types/analysis';

interface YouTubeUrlInputProps {
  onJobCreated: (jobId: string) => void;
  onShowDisclaimer: () => void;
  disabled?: boolean;
}

const YouTubeUrlInput: React.FC<YouTubeUrlInputProps> = ({ onJobCreated, onShowDisclaimer, disabled }) => {
  const [youtubeUrl, setYoutubeUrl] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async () => {
    if (!youtubeUrl) return;
    setLoading(true);
    try {
      const resp = await axios.post<JobResponse>('/api/analysis/ingest', {
        youtubeUrl,
        userConsent: true,
      });
      const jobId = resp.data.job_id;
      onJobCreated(jobId);
    } catch (err) {
      console.error('Ingest error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <input
        type="url"
        placeholder="https://www.youtube.com/watch?v=..."
        value={youtubeUrl}
        onChange={(e) => setYoutubeUrl(e.target.value)}
        disabled={disabled || loading}
        className="w-full input"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || loading || !youtubeUrl}
        className="btn-primary"
      >
        {loading ? 'Loading...' : 'Load & Extract Audio'}
      </button>
    </div>
  );
};

export default YouTubeUrlInput;
