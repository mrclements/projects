import React, { useState } from 'react';
import { Youtube, AlertCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:4000';

interface YouTubeUrlInputProps {
  onJobCreated: (jobId: string) => void;
  onShowDisclaimer: () => void;
  disabled?: boolean;
}

const YouTubeUrlInput: React.FC<YouTubeUrlInputProps> = ({
  onJobCreated,
  onShowDisclaimer,
  disabled = false
}) => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValidYouTubeUrl = (url: string): boolean => {
    const patterns = [
      /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
      /^https?:\/\/youtu\.be\/[\w-]+/,
      /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/
    ];
    return patterns.some(pattern => pattern.test(url));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setError('Please enter a YouTube URL');
      return;
    }

    if (!isValidYouTubeUrl(url)) {
      setError('Please enter a valid YouTube URL');
      return;
    }

    setError(null);
    setIsLoading(true);

    try {
      onShowDisclaimer();

      const response = await fetch(
        `${API_URL}/api/analysis/ingest`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ youtubeUrl: url, userConsent: true })
        }
      );

      if (!response.ok) {
        setError('Failed to start analysis');
        setIsLoading(false);
        return;
      }

      const result = await response.json();
      onJobCreated(result.jobId);
      setIsLoading(false);

    } catch (err) {
      setError('Failed to process YouTube URL. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="youtube-url" className="block text-sm font-medium text-gray-700 mb-2">
            YouTube Video URL
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Youtube className="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="youtube-url"
              type="url"
              className="input pl-10"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={disabled || isLoading}
            />
          </div>
          {error && (
            <div className="mt-2 flex items-center text-red-600 text-sm">
              <AlertCircle className="h-4 w-4 mr-1" />
              {error}
            </div>
          )}
        </div>

        <button
          type="submit"
          disabled={disabled || isLoading || !url.trim()}
          className="btn-primary w-full sm:w-auto"
        >
          {isLoading ? (
            <>
              <div className="loading-dots mr-2">
                <div></div>
                <div></div>
                <div></div>
              </div>
              Processing...
            </>
          ) : (
            'Load & Extract Audio'
          )}
        </button>
      </form>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-blue-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">
              Educational Use Only
            </h3>
            <div className="mt-2 text-sm text-blue-700">
              <p>
                This tool is for educational and personal analysis only. By using this service, 
                you confirm that you have the legal right to analyze the provided content.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default YouTubeUrlInput;
