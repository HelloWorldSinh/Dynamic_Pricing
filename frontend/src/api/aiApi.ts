import { apiClient } from './client';
import { AiMessageResponse, ExplainableFactors, ChatSessionSummary } from '../types/ai';

export async function sendAiMessageApi(
  message: string,
  sessionId?: string | null
): Promise<AiMessageResponse> {
  const res = await apiClient.post<AiMessageResponse>('/ai/chat', {
    message,
    session_id: sessionId || null,
  });
  return res.data;
}

export async function getAiExplanationApi(sku: string): Promise<ExplainableFactors> {
  const res = await apiClient.get<ExplainableFactors>(`/ai/explain/${sku}`);
  return res.data;
}

export async function getAiSessionsApi(limit: number = 20): Promise<ChatSessionSummary[]> {
  try {
    const res = await apiClient.get<ChatSessionSummary[]>('/ai/sessions', { params: { limit } });
    return res.data;
  } catch (error) {
    console.warn('[AI Api] Lỗi tải danh sách phiên:', error);
    return [];
  }
}

export async function getAiSessionMessagesApi(sessionId: string): Promise<any[]> {
  try {
    const res = await apiClient.get<any[]>(`/ai/sessions/${sessionId}`);
    return res.data;
  } catch (error) {
    console.warn(`[AI Api] Lỗi tải tin nhắn phiên ${sessionId}:`, error);
    return [];
  }
}

export async function deleteAiSessionApi(sessionId: string): Promise<boolean> {
  try {
    const res = await apiClient.delete<{ success: boolean }>(`/ai/sessions/${sessionId}`);
    return res.data?.success ?? true;
  } catch (error) {
    console.warn(`[AI Api] Lỗi xóa phiên ${sessionId}:`, error);
    return false;
  }
}
