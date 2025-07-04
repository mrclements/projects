import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface LegalDisclaimerProps {
  onAccept: () => void;
  onCancel: () => void;
}

const LegalDisclaimer: React.FC<LegalDisclaimerProps> = ({
  onAccept,
  onCancel
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-6 w-6 text-orange-500" />
            <h2 className="text-xl font-semibold text-gray-900">Legal Notice & Terms of Use</h2>
          </div>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-4 text-sm text-gray-700">
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h3 className="font-semibold text-orange-800 mb-2">Educational Use Only</h3>
            <p className="text-orange-700">
              This tool is intended for educational and personal analysis purposes only. 
              Commercial use is not permitted without proper licensing.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Your Responsibilities</h3>
            <ul className="space-y-2 list-disc list-inside">
              <li>You must own or have legal rights to analyze the YouTube content you submit</li>
              <li>You are responsible for ensuring compliance with YouTube's Terms of Service</li>
              <li>You understand this tool downloads audio temporarily for analysis only</li>
              <li>Audio files are automatically deleted within 24 hours</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Data Handling</h3>
            <ul className="space-y-2 list-disc list-inside">
              <li>Audio is extracted for analysis purposes only and not redistributed</li>
              <li>Generated chord progressions and tabs are transformative works</li>
              <li>No copyrighted audio content is stored permanently</li>
              <li>All temporary files are deleted automatically</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">YouTube Terms Compliance</h3>
            <p>
              By using this service, you acknowledge that you are using yt-dlp for personal, 
              educational purposes in accordance with YouTube's Terms of Service. You must not 
              use this service to infringe upon copyright or violate any applicable laws.
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Future Commercial Use</h3>
            <p>
              Any commercial deployment of this technology will require consultation with 
              legal counsel and may require Music Publishing licenses and additional 
              copyright clearances.
            </p>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Disclaimer</h3>
            <p className="text-gray-600">
              This software is provided "as is" without warranty. Users assume all 
              responsibility for legal compliance. The developers are not responsible 
              for any misuse of this tool.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-800 mb-2">Open Source Notice</h3>
            <p className="text-blue-700">
              This project uses open-source libraries including yt-dlp (GPL-3), 
              Essentia, madmom, librosa, and music21. See the project documentation 
              for full licensing information.
            </p>
          </div>
        </div>

        <div className="border-t p-6">
          <div className="flex flex-col sm:flex-row sm:justify-end space-y-2 sm:space-y-0 sm:space-x-3">
            <button onClick={onCancel} className="btn-outline">
              Cancel
            </button>
            <button onClick={onAccept} className="btn-primary">
              I Understand & Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LegalDisclaimer;
