import React, { useEffect, useState } from 'react';
import { getCloudStatus, wakeHuggingFaceSpaces, CloudServiceStatus, WakeSpacesResult } from '../lib/api';

interface CloudServicesStatusProps {
  showDetailedStatus?: boolean;
  onStatusChange?: (status: CloudServiceStatus) => void;
}

const CloudServicesStatus: React.FC<CloudServicesStatusProps> = ({ 
  showDetailedStatus = false,
  onStatusChange
}) => {
  const [status, setStatus] = useState<CloudServiceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [wakingUp, setWakingUp] = useState<boolean>(false);
  const [wakeResult, setWakeResult] = useState<WakeSpacesResult | null>(null);
  const [wakeAttemptCount, setWakeAttemptCount] = useState<number>(0);
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const result = await getCloudStatus();
        setStatus(result);
        setError(null); // Clear any previous errors
        if (onStatusChange) {
          onStatusChange(result);
        }
      } catch (err) {
        console.error('Error fetching cloud status:', err);
        
        // Create a fallback status object instead of setting error state
        // This allows us to show partial availability even when API fails
        const fallbackStatus: CloudServiceStatus = {
          status: "degraded",
          services: {
            demucs: { enabled: true, healthy: false, error: "Connection error" },
            spleeter: { enabled: true, healthy: false, error: "Connection error" },
            colab: { enabled: false, healthy: false },
            render: { enabled: false, healthy: false },
            github_actions: { enabled: false, healthy: false }
          }
        };
        
        setStatus(fallbackStatus);
        setError('Cloud services status check failed, showing estimated availability');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    
    // Refresh status every 60 seconds
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, [onStatusChange]);

  // Get summary status (healthy if at least one service is enabled and healthy)
  const getSummaryStatus = (): string => {
    if (!status) return 'unknown';
    
    const services = status.services;
    const hasHealthyService = Object.values(services).some(service => 
      service.enabled && service.healthy
    );
    
    return hasHealthyService ? 'available' : 'unavailable';
  };

  // Check specifically if source separation is available
  const isSeparationAvailable = (): boolean => {
    if (!status) return false;
    
    const services = status.services;
    return (
      (services.demucs.enabled && services.demucs.healthy) || 
      (services.spleeter.enabled && services.spleeter.healthy)
    );
  };

  if (loading) {
    return (
      <div className="text-sm text-gray-500 animate-pulse">
        Checking cloud services...
      </div>
    );
  }

  // Remove the complete error handling block so we still show partial status
  // even when there's an error

  // Simple status display
  if (!showDetailedStatus) {
    const summaryStatus = getSummaryStatus();
    return (
      <div className="flex items-center gap-2">
        <div 
          className={`w-2 h-2 rounded-full ${
            summaryStatus === 'available' ? 'bg-green-500' : 
            summaryStatus === 'unavailable' ? 'bg-red-500' : 'bg-gray-500'
          }`}
        />
        <div className="text-sm">
          Cloud services: <span className="font-medium">{summaryStatus}</span>
          {isSeparationAvailable() && 
            <span className="ml-1 text-xs text-green-600">(source separation available)</span>
          }
          {error && <span className="ml-1 text-xs text-orange-500">({error})</span>}
        </div>
      </div>
    );
  }

  // Function to wake up Hugging Face spaces with retry logic
  const handleWakeSpaces = async () => {
    try {
      setWakingUp(true);
      setError(null);
      setWakeAttemptCount(prev => prev + 1);
      
      // First wake-up attempt
      const result = await wakeHuggingFaceSpaces();
      setWakeResult(result);
      
      // If wake-up was successful or partially successful
      if (result.success || (result.spleeter || result.demucs)) {
        // Set up polling to check status periodically
        let attempts = 0;
        const maxAttempts = 5; // Maximum status check attempts
        const checkStatus = async () => {
          if (attempts >= maxAttempts) {
            // Stop checking after max attempts
            return;
          }
          
          attempts++;
          try {
            // Get the latest status
            const newStatus = await getCloudStatus();
            setStatus(newStatus);
            if (onStatusChange) onStatusChange(newStatus);
            
            // Check if services are healthy now
            const demucsHealthy = newStatus.services.demucs.healthy;
            const spleeterHealthy = newStatus.services.spleeter.healthy;
            
            if ((demucsHealthy || spleeterHealthy) && attempts < maxAttempts) {
              // At least one service is healthy, stop polling
              console.log('Services are now awake!');
            } else if (attempts < maxAttempts) {
              // Services still not healthy, continue polling
              setTimeout(checkStatus, 3000); // Check again in 3 seconds
            }
          } catch (error) {
            console.error('Error checking service status:', error);
            if (attempts < maxAttempts) {
              setTimeout(checkStatus, 3000);
            }
          }
        };
        
        // Start the status polling after a short delay
        setTimeout(checkStatus, 2000);
      }
    } catch (err) {
      setError('Failed to wake up cloud services');
      console.error('Error waking up spaces:', err);
    } finally {
      setWakingUp(false);
    }
  };

  // Detailed status display
  return (
    <div className="bg-gray-100 rounded-md p-4 shadow-sm">
      <h3 className="font-semibold text-lg mb-3">Cloud Services Status</h3>
      
      {error && (
        <div className="mb-2 text-sm text-orange-500">
          {error}
        </div>
      )}

      {status && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="col-span-2 mb-1 font-medium">Source Separation</div>
            
            <div className="flex items-center gap-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  status.services.demucs.enabled && status.services.demucs.healthy 
                    ? 'bg-green-500' : 
                    (status.services.demucs.enabled ? 'bg-yellow-500' : 'bg-red-500')
                }`}
              />
              <span>Demucs v4</span>
            </div>
            
            <div className="text-sm text-gray-600">
              {status.services.demucs.enabled 
                ? (status.services.demucs.healthy 
                  ? 'Available' 
                  : 'Service hibernating')
                : 'Not configured'
              }
            </div>
            
            <div className="flex items-center gap-2">
              <div 
                className={`w-2 h-2 rounded-full ${
                  status.services.spleeter.enabled && status.services.spleeter.healthy 
                    ? 'bg-green-500' : 
                    (status.services.spleeter.enabled ? 'bg-yellow-500' : 'bg-red-500')
                }`}
              />
              <span>Spleeter</span>
            </div>
            
            <div className="text-sm text-gray-600">
              {status.services.spleeter.enabled 
                ? (status.services.spleeter.healthy 
                  ? 'Available' 
                  : 'Service hibernating')
                : 'Not configured'
              }
            </div>
          </div>
          
          {/* Wake up button */}
          {(status.services.demucs.enabled || status.services.spleeter.enabled) && 
           (!status.services.demucs.healthy || !status.services.spleeter.healthy) && (
            <div className="mt-2">
              <button
                onClick={handleWakeSpaces}
                disabled={wakingUp}
                className={`px-3 py-1 text-sm rounded-md ${
                  wakingUp 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {wakingUp ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Waking up services...
                  </span>
                ) : 'Wake up services'}
              </button>
              
              {wakeResult && (
                <div className="mt-1 text-xs">
                  {wakeResult.success ? (
                    <span className="text-green-600">
                      Services are waking up. Status will update automatically.
                    </span>
                  ) : wakeResult.spleeter || wakeResult.demucs ? (
                    <span className="text-green-600">
                      Partial success! Some services are waking up. This can take up to 30 seconds.
                    </span>
                  ) : (
                    <span className="text-red-500">
                      {wakeResult.message || 'Failed to wake up services. Please try again.'}
                    </span>
                  )}
                  {wakeAttemptCount > 1 && (
                    <div className="mt-1 text-gray-600">
                      Wake-up attempted {wakeAttemptCount} times. Hugging Face Spaces can take up to a minute to fully wake up.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* Other cloud services would go here in the future */}
          
          <div className="mt-4 text-sm">
            <div className="text-gray-600 mb-1">
              Cloud services are managed by Hugging Face Spaces and may hibernate after periods of inactivity.
            </div>
            <div className="text-gray-600">
              If services are hibernating, click "Wake up services" and wait 15-30 seconds for them to become available.
              You may need to click the button again if services don't wake up after the first attempt.
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CloudServicesStatus;
