import { request } from './client.js';
import type { CrawlTriggerPayload, CrawlTriggerResponse } from '../types/index.js';

export const crawlerApi = {
  async trigger(payload: CrawlTriggerPayload): Promise<CrawlTriggerResponse> {
    return request<CrawlTriggerResponse>('/crawl/trigger', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async checkHealth(): Promise<{ status: string }> {
    const rootUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '');
    const response = await fetch(`${rootUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    return response.json();
  }
};
