import React from 'react';
import { useAiChat } from '../../context/AiChatContext';

export const AiFloatingButton: React.FC = () => {
  const { state, openExpanded } = useAiChat();

  if (state !== 'minimized') return null;

  return (
    <button
      onClick={openExpanded}
      className="fixed bottom-6 right-6 z-40 group flex items-center justify-center w-14 h-14 rounded-full bg-orange-600 hover:bg-orange-500 text-white shadow-xl shadow-orange-600/35 hover:shadow-orange-600/55 hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer border border-orange-400/40"
      title="Mở AI Pricing Studio"
      aria-label="Mở AI Pricing Studio"
    >
      <div className="relative flex items-center justify-center">
        <span className="font-mono font-black text-sm tracking-tighter text-white">
          AI
        </span>
        <span className="absolute -top-2 -right-2 flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-300 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-400 border border-orange-600"></span>
        </span>
      </div>

      {/* Floating tooltip badge on hover */}
      <span className="absolute right-16 px-3 py-1.5 rounded-xl bg-slate-900/95 dark:bg-slate-800/95 backdrop-blur-sm text-white text-xs font-semibold whitespace-nowrap shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:-translate-x-1 transition-all duration-200 border border-slate-700/60">
        AI Pricing Studio
      </span>
    </button>
  );
};
