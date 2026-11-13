import React, { useState, useRef, useEffect } from 'react';
import { useAiChat } from '../../context/AiChatContext';
import { ExplainableCard } from './ExplainableCard';
import { MarkdownRenderer } from './MarkdownRenderer';
import { AiDataTable } from './AiDataTable';
import { InteractivePromptChips } from './InteractivePromptChips';

export const ExpandedAiDrawer: React.FC = () => {
  const {
    state,
    minimize,
    messages,
    sendMessage,
    isThinking,
    newChat,
    sessions,
    sessionId,
    switchSession,
    deleteSession,
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
    'Top laptop ASUS FPT đắt hơn CellphoneS',
    'Mã nào đang có nguy cơ tồn kho DOH > 45 ngày?',
    'So sánh giá Samsung Galaxy S25 giữa 3 bên',
    'Phân tích mã FPT-ASUS-VIVO15',
  ];

  return (
    <div className="fixed inset-0 z-50 flex bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full h-full bg-white dark:bg-slate-900 flex flex-col overflow-hidden">
        {/* Top Header Bar */}
        <div className="p-3.5 px-6 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-orange-600 flex items-center justify-center text-white font-mono font-bold text-xs tracking-wider shadow-sm">
              AI
            </div>
            <div>
              <div className="text-sm font-bold flex items-center gap-2">
                <span>AI Pricing Studio</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-orange-500/20 text-orange-400 font-mono font-semibold">
                  PBI-017 &amp; PBI-018
                </span>
              </div>
              <div className="text-xs text-slate-400">
                FPT Shop Market Copilot - Không gian phân tích định giá chuyên sâu
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={newChat}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition cursor-pointer border border-slate-700"
              title="Khởi tạo phiên hội thoại mới"
            >
              + Hội thoại mới
            </button>
            <button
              type="button"
              onClick={minimize}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-900/60 text-slate-300 hover:text-white text-xs font-semibold transition cursor-pointer border border-slate-700 hover:border-rose-700"
              title="Đóng studio (hoặc nhấn ESC)"
            >
              Đóng (ESC)
            </button>
          </div>
        </div>

        {/* 2-Column Studio Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* CỘT TRÁI: Sidebar danh sách phiên hội thoại (280px) */}
          <div className="w-72 shrink-0 bg-slate-50 dark:bg-slate-950/70 border-r border-slate-200 dark:border-slate-800 flex flex-col h-full">
            <div className="p-3 px-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between shrink-0">
              <span className="text-[11px] font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                Lịch sử phiên hội thoại
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono">
                {sessions.length}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
              {sessions.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">
                  Chưa có phiên hội thoại nào được lưu.
                </div>
              ) : (
                sessions.map((s) => {
                  const isActive = s.id === sessionId;
                  return (
                    <div
                      key={s.id}
                      onClick={() => switchSession(s.id)}
                      className={`group p-2.5 rounded-xl border text-xs cursor-pointer transition flex flex-col gap-1 ${
                        isActive
                          ? 'bg-orange-50 dark:bg-orange-950/40 border-orange-300 dark:border-orange-800 text-orange-950 dark:text-orange-200 font-medium shadow-xs'
                          : 'bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-1">
                        <span className="truncate flex-1 font-semibold text-xs" title={s.title}>
                          {s.title || 'Cuộc hội thoại'}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSession(s.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-[10px] text-rose-500 hover:text-rose-700 dark:hover:text-rose-400 font-semibold px-1 rounded transition"
                          title="Xóa phiên này"
                        >
                          Xóa
                        </button>
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span>
                          {s.created_at ? new Date(s.created_at).toLocaleDateString('vi-VN') : ''}
                        </span>
                        <span className="font-mono">{s.message_count} tin nhắn</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* CỘT PHẢI: Không gian trò chuyện & phân tích dữ liệu lớn */}
          <div className="flex-1 flex flex-col h-full overflow-hidden bg-white dark:bg-slate-900">
            {/* Quick Suggestion Chips Header */}
            <div className="p-3 px-6 bg-slate-50 dark:bg-slate-950/40 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2 overflow-x-auto shrink-0">
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 shrink-0">
                Chủ đề gợi ý:
              </span>
              {promptChips.map((chip, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => sendMessage(chip)}
                  className="text-xs whitespace-nowrap px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-orange-500 dark:hover:border-orange-500 text-slate-700 dark:text-slate-300 transition cursor-pointer font-medium"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Message History */}
            <div className="flex-1 p-6 overflow-y-auto space-y-4 text-xs">
              <div className="max-w-5xl mx-auto w-full space-y-4">
                {messages.map((msg) => {
                  const isUser = msg.sender === 'user';
                  return (
                    <div
                      key={msg.id}
                      className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl p-4 leading-relaxed shadow-sm ${
                          isUser
                            ? 'bg-orange-600 text-white rounded-br-none'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-none border border-slate-200/60 dark:border-slate-700/60'
                        }`}
                      >
                        {isUser ? (
                          <div className="text-sm font-normal">{msg.content}</div>
                        ) : (
                          <MarkdownRenderer content={msg.content} />
                        )}

                        {/* Render Table Data with intelligent formatting and 1-click action */}
                        {msg.tableData && msg.tableData.length > 0 && (
                          <AiDataTable
                            data={msg.tableData}
                            onAnalyze={(sku) => sendMessage(`Phân tích mã ${sku}`)}
                          />
                        )}

                        {/* Render Explainable AI Card if available */}
                        {msg.explainFactors && (
                          <ExplainableCard factors={msg.explainFactors} />
                        )}

                        {/* Interactive Clarification & Quick Prompt Chips */}
                        {!isUser && (
                          <InteractivePromptChips
                            suggestions={msg.suggestions}
                            tableData={msg.tableData}
                            onSelectPrompt={(prompt) => sendMessage(prompt)}
                          />
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 mt-1 px-1">{msg.timestamp}</span>
                    </div>
                  );
                })}

                {isThinking && (
                  <div className="flex items-center gap-3 p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 text-xs w-fit">
                    <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-ping"></span>
                    <span>AI đang phân tích ma trận giá, kho hàng và quy tắc giá sàn...</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Footer Input Bar */}
            <div className="p-4 px-6 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shrink-0">
              <div className="max-w-5xl mx-auto w-full flex flex-col gap-1.5">
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Hỏi bất kỳ câu hỏi nào về thị trường giá, đối thủ, hoặc lý do đề xuất..."
                    className="flex-1 text-xs px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 font-normal"
                  />
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={!input.trim() || isThinking}
                    className="px-6 py-3 rounded-xl bg-orange-600 hover:bg-orange-500 disabled:opacity-40 text-white font-semibold text-xs transition shadow-sm cursor-pointer shrink-0"
                  >
                    Gửi câu hỏi
                  </button>
                </div>
                <div className="text-[10px] text-slate-400 px-1 flex items-center justify-between">
                  <span>Nhấn Enter để gửi câu hỏi</span>
                  <span>Nhấn ESC để thu nhỏ về nút nổi</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
