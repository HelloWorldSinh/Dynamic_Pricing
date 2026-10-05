import React from 'react';

interface ConfidenceMeterProps {
  score: number; // 0 - 100
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({ score }) => {
  const getColor = () => {
    if (score >= 80) return 'text-blue-600 dark:text-blue-400 bg-blue-500';
    if (score >= 60) return 'text-amber-600 dark:text-amber-400 bg-amber-500';
    return 'text-rose-600 dark:text-rose-400 bg-rose-500';
  };

  return (
    <div className="flex flex-col items-center">
      <div className="flex items-baseline gap-1">
        <span className={`text-lg font-black font-mono ${getColor().split(' ')[0]}`}>
          {score}%
        </span>
        <span className="text-[10px] text-slate-400">tương đồng</span>
      </div>
      <div className="w-24 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden mt-1">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getColor().split(' ')[2]}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};
