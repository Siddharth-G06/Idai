import React from 'react';
import { SearchX } from 'lucide-react';

const EmptyState = ({ message = "No data found matching your criteria." }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 m-4 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md animate-in fade-in zoom-in duration-500">
      <div className="p-4 bg-white/10 rounded-full mb-6 text-gray-400">
        <SearchX className="w-10 h-10" />
      </div>
      <p className="text-lg text-gray-300 text-center max-w-sm font-medium">
        {message}
      </p>
    </div>
  );
};

export default EmptyState;
