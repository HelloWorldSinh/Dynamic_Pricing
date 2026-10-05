import React, { createContext, useContext, useState } from 'react';
import { AiChatMessage, ExplainableFactors } from '../types/ai';
import { sendAiMessageApi, getAiExplanationApi } from '../api/aiApi';

export type AiWidgetState = 'minimized' | 'compact' | 'expanded';

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
}

const AiChatContext = createContext<AiChatContextType | undefined>(undefined);

export const AiChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AiWidgetState>('minimized');
  const [isThinking, setIsThinking] = useState(false);
  const [messages, setMessages] = useState<AiChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content: 'Xin chào! Tôi là Trợ lý AI Định giá FPT Shop. Tôi có thể giúp bạn tra cứu chênh lệch giá đối thủ, kiểm tra rủi ro tồn kho DOH hoặc phân tích minh bạch lý do đề xuất giá.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const openCompact = () => setState('compact');
  const openExpanded = () => setState('expanded');
  const minimize = () => setState('minimized');

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
      const response = await sendAiMessageApi(text);
      const aiMsg: AiChatMessage = {
        id: 'ai-' + Date.now(),
        sender: 'assistant',
        content: response.message,
        tableData: response.tableData,
        explainFactors: response.explainFactors,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      const errorMsg: AiChatMessage = {
        id: 'ai-err-' + Date.now(),
        sender: 'assistant',
        content: 'Rất tiếc, đã có sự cố khi kết nối tới mô hình AI. Vui lòng thử lại sau giây lát.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const askExplanationForSku = async (sku: string, productName: string) => {
    // When asking for explanation, open in expanded mode to display the 3-tier card properly!
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
        content: `Dưới đây là bản giải trình 3 lớp của thuật toán cho mã ${sku}:`,
        explainFactors: factors,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (error) {
      console.error(error);
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
