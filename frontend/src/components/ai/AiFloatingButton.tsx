import React from 'react';
import { Bot, Sparkles } from 'lucide-react';
import { useAiChat } from '../../context/AiChatContext';

export const AiFloatingButton: React.FC = () => {
  const { state, openCompact } = useAiChat();

  if (state !== 'minimized') return null;

  return (
    <button
      onClick={openCompact}
      className="fixed bottom-6 right-6 z-40 group flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white font-bold text-xs shadow-xl shadow-orange-600/30 hover:shadow-orange-600/50 hover:scale-105 active:scale-95 transition-all duration-200"
      title="Mở Trợ lý AI Định giá FPT"
    >
      <div className="relative">
        <Bot className="w-5 h-5 text-white" />
        <span className="absolute -top-1 -right-1 flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-200 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-300"></span>
        </span>
      </div>
      <span>Trợ lý AI Định giá</span>
      <Sparkles className="w-3.5 h-3.5 text-amber-200 animate-pulse" />
    </button>
  );
};
