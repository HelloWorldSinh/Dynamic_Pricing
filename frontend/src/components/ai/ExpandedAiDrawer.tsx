import React, { useState, useRef, useEffect } from 'react';
import { 
  Bot, 
  Minimize2, 
  X, 
  Send, 
  Sparkles, 
  RotateCcw,
  Loader2, 
  Table 
} from 'lucide-react';
import { useAiChat } from '../../context/AiChatContext';
import { ExplainableCard } from './ExplainableCard';

export const ExpandedAiDrawer: React.FC = () => {
  const { 
    state, 
    openCompact, 
    minimize, 
    messages, 
    sendMessage, 
    isThinking, 
    clearMessages 
  } = useAiChat();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (state === 'expanded') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isThinking, state]);

  if (state !== 'expanded') return null;

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
    'Liệt kê 5 laptop ASUS FPT đắt hơn CellphoneS',
    'Mã iPhone nào đang có nguy cơ tồn kho DOH > 45 ngày?',
    'So sánh giá Samsung Galaxy S25 giữa 3 bên',
    'Phân tích mã FPT-ASUS-VIVO15',
  ];

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-3xl h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="p-4 px-6 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-orange-600 flex items-center justify-center text-white shadow-md shadow-orange-600/30">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-bold flex items-center gap-2">
                <span>AI Pricing Studio &amp; Explainable Engine</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-orange-500/20 text-orange-400 font-mono font-semibold">
                  PBI-017 &amp; PBI-018
                </span>
              </div>
              <div className="text-xs text-slate-400">
                Không gian phân tích định giá chuyên sâu cho Pricing Analyst
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={clearMessages}
              className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Làm mới lịch sử chat"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={openCompact}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
              title="Thu nhỏ về khung chat góc phải"
            >
              <Minimize2 className="w-3.5 h-3.5 text-orange-400" />
              <span>Thu nhỏ (Popup)</span>
            </button>
            <button
              onClick={minimize}
              className="p-2 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
              title="Đóng"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="p-3 px-6 bg-slate-50 dark:bg-slate-950/60 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2 overflow-x-auto">
          <Sparkles className="w-4 h-4 text-orange-500 flex-shrink-0" />
          {promptChips.map((chip, idx) => (
            <button
              key={idx}
              onClick={() => sendMessage(chip)}
              className="text-xs whitespace-nowrap px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-orange-500 text-slate-700 dark:text-slate-300 transition"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Message History */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4 text-xs">
          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[90%] rounded-2xl p-4 leading-relaxed shadow-sm ${
                    isUser
                      ? 'bg-orange-600 text-white rounded-br-none'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-none border border-slate-200/60 dark:border-slate-700/60'
                  }`}
                >
                  <div className="text-sm font-normal">{msg.content}</div>

                  {/* Render Table Data if available */}
                  {msg.tableData && msg.tableData.length > 0 && (
                    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm">
                      <div className="p-2 px-3 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700 text-[11px] font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                        <Table className="w-3.5 h-3.5 text-orange-500" />
                        <span>Bảng Dữ Liệu Chi Tiết</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="bg-slate-50/50 dark:bg-slate-800/40 text-[11px] font-semibold text-slate-500 border-b border-slate-200 dark:border-slate-700">
                              {Object.keys(msg.tableData[0]).map((header) => (
                                <th key={header} className="p-2.5 px-3">
                                  {header}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                            {msg.tableData.map((row, rIdx) => (
                              <tr key={rIdx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                                {Object.values(row).map((val: any, cIdx) => (
                                  <td key={cIdx} className="p-2.5 px-3 font-medium">
                                    {val}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Render Explainable AI Card if available */}
                  {msg.explainFactors && (
                    <ExplainableCard factors={msg.explainFactors} />
                  )}
                </div>
                <span className="text-[10px] text-slate-400 mt-1 px-1">{msg.timestamp}</span>
              </div>
            );
          })}

          {isThinking && (
            <div className="flex items-center gap-2.5 p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/60 text-slate-500 text-xs w-fit">
              <Loader2 className="w-4 h-4 animate-spin text-orange-500" />
              <span>AI đang phân tích ma trận giá, kho hàng và quy tắc giá sàn...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Footer Input Bar */}
        <div className="p-4 px-6 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi bất kỳ câu hỏi nào về thị trường giá, đối thủ, hoặc lý do đề xuất..."
            className="flex-1 text-xs px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isThinking}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white font-semibold text-xs transition shadow-sm"
          >
            <span>Gửi câu hỏi</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
