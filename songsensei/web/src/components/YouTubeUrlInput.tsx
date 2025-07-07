import React, { useState } from 'react';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { JobResponse } from '../types/analysis';

interface YouTubeUrlInputProps {
  onJobCreated: (jobId: string) => void;
  onShowDisclaimer: () => void;
  disabled?: boolean;
}

/**
 * Strongly validates the server response.
 * Throws if data is invalid.
 */
function mapJobResponse(data: any): JobResponse {
  if (!data || typeof data.job_id !== 'string') {
    throw new Error(
      `Invalid server response: missing job_id. Got: ${JSON.stringify(data)}`
    );
  }

  return {
    jobId: data.job_id,
    status: data.status,
    message: data.message,
  };
}

const YouTubeUrlInput: React.FC<YouTubeUrlInputProps> = ({
  onJobCreated,
  onShowDisclaimer,
  disabled
}) => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!url) {
      setError('Please enter a YouTube URL.');
      return;
    }

    setLoading(true);
    try {
      const resp = await axios.post('/api/analysis/ingest', {
        youtube_url: url,
        user_consent: true
      });

      const normalized = mapJobResponse(resp.data);
      onJobCreated(normalized.jobId);
    } catch (err: any) {
      console.error('Error ingesting YouTube URL:', err);
      if (err instanceof Error) {
        setError(err.message);
      } else if (err?.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to ingest video. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white shadow-sm border rounded-lg p-6">
      <p className="text-gray-600 mb-2">
        Enter a YouTube link to extract its audio and analyze chords and tabs.
        <button
          className="text-blue-600 underline ml-1"
          onClick={onShowDisclaimer}
          type="button"
        >
          View Disclaimer
        </button>
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col space-y-4">
        <input
          type="url"
          className="form-input w-full rounded border-gray-300 focus:border-primary-500 focus:ring-primary-500"
          placeholder="https://www.youtube.com/watch?v=..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading || disabled}
          required
        />
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <button
          type="submit"
          disabled={loading || disabled}
          className="btn-primary flex items-center justify-center"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin h-4 w-4 mr-2" />
              Loading...
            </>
          ) : (
            'Ingest Video'
          )}
        </button>
      </form>
    </div>
  );
};

export default YouTubeUrlInput;
