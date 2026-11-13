import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { AiChatMessage, ExplainableFactors, ChatSessionSummary } from '../types/ai';
import {
  sendAiMessageApi,
  getAiExplanationApi,
  getAiSessionsApi,
  getAiSessionMessagesApi,
  deleteAiSessionApi,
} from '../api/aiApi';

export type AiWidgetState = 'minimized' | 'compact' | 'expanded';

const SESSION_STORAGE_KEY = 'ai_chat_session_id';

interface ApiErrorLike {
  response?: {
    data?: {
      detail?: unknown;
    };
  };
}

const getApiErrorMessage = (error: unknown, fallback: string): string => {
  const detail = (error as ApiErrorLike)?.response?.data?.detail;
  return typeof detail === 'string' && detail.trim() ? detail : fallback;
};

interface AiChatContextType {
  state: AiWidgetState;
  setState: (state: AiWidgetState) => void;
  openCompact: () => void;
  openExpanded: () => void;
  minimize: () => void;
  messages: AiChatMessage[];
  sendMessage: (text: string) => Promise<void>;
  askExplanationForSku: (sku: string, productName: string) => Promise<void>;
  isThinking: boolean;
  clearMessages: () => void;
  sessionId: string | null;
  newChat: () => void;
  sessions: ChatSessionSummary[];
  loadSessions: () => Promise<void>;
  switchSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
}

const AiChatContext = createContext<AiChatContextType | undefined>(undefined);

export const AiChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AiWidgetState>('minimized');
  const [isThinking, setIsThinking] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(() => {
    return sessionStorage.getItem(SESSION_STORAGE_KEY);
  });
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);

  const [messages, setMessages] = useState<AiChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content: 'Xin chào! Tôi là FPT Shop Market Copilot. Tôi có thể hỗ trợ bạn tra cứu chênh lệch giá đối thủ, cảnh báo rủi ro tồn kho DOH hoặc giải trình minh bạch lý do điều chỉnh giá.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  // Đồng bộ sessionId vào sessionStorage khi có thay đổi
  useEffect(() => {
    if (sessionId) {
      sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
    } else {
      sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
  }, [sessionId]);

  const loadSessions = useCallback(async () => {
    const list = await getAiSessionsApi(30);
    setSessions(list);
  }, []);

  // Tải danh sách phiên khi mở studio
  useEffect(() => {
    if (state === 'expanded') {
      loadSessions();
    }
  }, [state, loadSessions]);

  // Lắng nghe phím ESC để đóng nhanh studio
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && state === 'expanded') {
        setState('minimized');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state]);

  const openCompact = () => setState('expanded'); // Luôn mở thẳng Studio
  const openExpanded = () => setState('expanded');
  const minimize = () => setState('minimized');

  const switchSession = async (targetSessionId: string) => {
    if (targetSessionId === sessionId) return;
    setIsThinking(true);
    try {
      setSessionId(targetSessionId);
      const history = await getAiSessionMessagesApi(targetSessionId);
      if (Array.isArray(history) && history.length > 0) {
        const mapped: AiChatMessage[] = history.map((m: any) => ({
          id: m.id || String(Date.now() + Math.random()),
          sender: m.role === 'user' ? 'user' : 'assistant',
          content: m.content,
          timestamp: m.created_at
            ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          tableData: m.retrieved_context?.tableData,
          explainFactors: m.retrieved_context?.explainFactors,
          suggestions: m.retrieved_context?.suggestions,
        }));
        setMessages(mapped);
      } else {
        clearMessages();
      }
    } catch (err) {
      console.error('Lỗi nạp lịch sử phiên chat:', err);
    } finally {
      setIsThinking(false);
    }
  };

  const deleteSession = async (targetSessionId: string) => {
    const success = await deleteAiSessionApi(targetSessionId);
    if (success) {
      setSessions((prev) => prev.filter((s) => s.id !== targetSessionId));
      if (sessionId === targetSessionId) {
        newChat();
      }
    }
  };

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: AiChatMessage = {
      id: 'user-' + Date.now(),
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);

    try {
      const response = await sendAiMessageApi(text, sessionId);

      // Cập nhật session_id nếu backend trả về session mới
      if (response.session_id && response.session_id !== sessionId) {
        setSessionId(response.session_id);
      }

      const aiMsg: AiChatMessage = {
        id: 'ai-' + Date.now(),
        sender: 'assistant',
        content: response.message,
        tableData: response.tableData,
        explainFactors: response.explainFactors,
        suggestions: response.suggestions,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
      // Cập nhật lại danh sách sessions để hiển thị tiêu đề mới
      loadSessions();
    } catch (error) {
      const errorMsg: AiChatMessage = {
        id: 'ai-err-' + Date.now(),
        sender: 'assistant',
        content: getApiErrorMessage(
          error,
          'Rất tiếc, đã có sự cố khi kết nối tới mô hình AI. Vui lòng thử lại sau giây lát.'
        ),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const askExplanationForSku = async (sku: string, productName: string) => {
    // Mở ở chế độ Studio Toàn Màn Hình
    setState('expanded');
    
    const userMsg: AiChatMessage = {
      id: 'user-exp-' + Date.now(),
      sender: 'user',
      content: `Tại sao hệ thống đề xuất điều chỉnh giá cho mã "${sku} - ${productName}"?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);

    try {
      const factors: ExplainableFactors = await getAiExplanationApi(sku);
      const aiMsg: AiChatMessage = {
        id: 'ai-exp-' + Date.now(),
        sender: 'assistant',
        content: `Dưới đây là căn cứ giải trình 3 lớp của thuật toán định giá cho sản phẩm ${sku}:`,
        explainFactors: factors,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error('Lỗi khi tải căn cứ giải trình SKU:', error);
      const errorMsg: AiChatMessage = {
        id: 'ai-err-' + Date.now(),
        sender: 'assistant',
        content: getApiErrorMessage(
          error,
          `Không thể tải dữ liệu giải trình cho mã sản phẩm ${sku}. Vui lòng thử lại sau.`
        ),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const clearMessages = () => {
    setMessages([
      {
        id: 'welcome-' + Date.now(),
        sender: 'assistant',
        content: 'Cuộc trò chuyện đã được làm mới. Tôi sẵn sàng hỗ trợ bạn câu hỏi tiếp theo.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  const newChat = () => {
    setSessionId(null);
    clearMessages();
  };

  return (
    <AiChatContext.Provider
      value={{
        state,
        setState,
        openCompact,
        openExpanded,
        minimize,
        messages,
        sendMessage,
        askExplanationForSku,
        isThinking,
        clearMessages,
        sessionId,
        newChat,
        sessions,
        loadSessions,
        switchSession,
        deleteSession,
      }}
    >
      {children}
    </AiChatContext.Provider>
  );
};

export const useAiChat = (): AiChatContextType => {
  const context = useContext(AiChatContext);
  if (!context) {
    throw new Error('useAiChat must be used within an AiChatProvider');
  }
  return context;
};
