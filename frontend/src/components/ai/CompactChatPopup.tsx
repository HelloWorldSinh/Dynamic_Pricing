import React, { useState, useRef, useEffect } from 'react';
import { 
  Bot, 
  Maximize2, 
  X, 
  Send, 
  Sparkles, 
  RotateCcw,
  Loader2 
} from 'lucide-react';
import { useAiChat } from '../../context/AiChatContext';

export const CompactChatPopup: React.FC = () => {
  const { 
    state, 
    openExpanded, 
    minimize, 
    messages, 
    sendMessage, 
    isThinking, 
    clearMessages 
  } = useAiChat();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (state === 'compact') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking, state]);

  if (state !== 'compact') return null;

  const handleSend = () => {
    if (!input.trim() || isThinking) return;
    sendMessage(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const promptChips = [
    'Top laptop FPT đắt hơn CellphoneS',
    'Mã nào có DOH > 45 ngày?',
    'So sánh giá Galaxy S25',
  ];

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[380px] h-[520px] rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-200">
      {/* Header */}
      <div className="p-3.5 px-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-orange-600 flex items-center justify-center text-white">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold leading-none flex items-center gap-1.5">
              <span>AI Pricing Assistant</span>
              <span className="text-[9px] px-1.5 py-0.2 rounded bg-orange-500/20 text-orange-400 font-mono">
                RAG
              </span>
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">FPT Shop Market Copilot</div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={clearMessages}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
            title="Làm mới đoạn chat"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={openExpanded}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
            title="Phóng rộng khung chat (Mở Drawer lớn)"
          >
            <Maximize2 className="w-3.5 h-3.5 text-orange-400" />
          </button>
          <button
            onClick={minimize}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
            title="Thu nhỏ về nút nổi"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Quick Prompt Chips */}
      <div className="p-2 px-3 bg-slate-50 dark:bg-slate-950/60 border-b border-slate-100 dark:border-slate-800/80 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
        <Sparkles className="w-3 h-3 text-orange-500 flex-shrink-0" />
        {promptChips.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(chip)}
            className="text-[10px] whitespace-nowrap px-2 py-1 rounded-md bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-orange-500 text-slate-700 dark:text-slate-300 transition"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-3.5 overflow-y-auto space-y-3 text-xs">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-xl p-3 leading-relaxed shadow-sm ${
                  isUser
                    ? 'bg-orange-600 text-white rounded-br-none'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-none border border-slate-200/60 dark:border-slate-700/60'
                }`}
              >
                <div>{msg.content}</div>

                {/* Table Data Preview if any */}
                {msg.tableData && (
                  <div className="mt-2 text-[10px] text-orange-400 font-semibold cursor-pointer underline" onClick={openExpanded}>
                    + Chứa bảng dữ liệu so sánh ({msg.tableData.length} dòng). Bấm phóng to để xem chi tiết.
                  </div>
                )}
              </div>
              <span className="text-[9px] text-slate-400 mt-1 px-1">{msg.timestamp}</span>
            </div>
          );
        })}

        {isThinking && (
          <div className="flex items-center gap-2 p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60 text-slate-500 text-xs w-fit">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-orange-500" />
            <span>AI đang truy vấn dữ liệu cào &amp; tính toán...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-2.5 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hỏi về giá, tồn kho hoặc đối thủ..."
          className="flex-1 text-xs px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isThinking}
          className="p-2 rounded-xl bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white transition shadow-sm flex-shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
