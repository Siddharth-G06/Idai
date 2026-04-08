import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

const ErrorState = ({ message = "Something went wrong while fetching data.", onRetry }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 m-4 rounded-2xl border border-red-500/20 bg-red-500/5 backdrop-blur-xl animate-in fade-in zoom-in duration-300">
      <div className="p-4 bg-red-500/20 rounded-full mb-4">
        <AlertTriangle className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">Couldn't load data</h3>
      <p className="text-gray-400 text-center max-w-md mb-6">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 px-6 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-full transition-all active:scale-95 font-medium shadow-lg shadow-red-500/25"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorState;
