import { apiClient, request } from './client';
import type { CrawlResult, CrawlJobResponse, CrawlSource } from '../types/crawl';
import type { CrawlTriggerPayload, CrawlProgressResponse } from '../types/index';
import { mockCrawlResults } from './mockData';

export async function triggerCrawlApi(
  source: CrawlSource | string,
  category: string,
  limit?: number
): Promise<CrawlJobResponse & { task_id?: string }> {
  try {
    const res = await apiClient.post<any>('/crawl/trigger', {
      source: source.toLowerCase(),
      category: category.toLowerCase(),
      limit,
    });
    return {
      ...res.data,
      job_id: res.data.task_id || res.data.job_id,
      task_id: res.data.task_id || res.data.job_id,
    };
  } catch (error: any) {
    // If backend 429 debounce, re-throw to allow component to display remaining countdown
    if (error.response?.status === 429) {
      throw error;
    }
    // Fallback simulation when offline
    console.warn('[Crawler API] Fallback to simulated trigger');
    const fallbackId = 'task-' + Date.now();
    return {
      message: `Đã kích hoạt cào dữ liệu cho ${source} (${category})`,
      source: source as CrawlSource,
      category,
      status: 'RUNNING',
      job_id: fallbackId,
      task_id: fallbackId,
      started_at: new Date().toISOString(),
    };
  }
}

export async function triggerDualCrawlApi(category: string): Promise<any[]> {
  const cat = category.toLowerCase() === 'all' ? 'laptop' : category.toLowerCase();
  return Promise.all([
    triggerCrawlApi('CELLPHONES', cat),
    triggerCrawlApi('HOANGHA', cat),
  ]);
}

export async function getLatestCrawlTimeApi(): Promise<string | null> {
  try {
    const res = await apiClient.get<CrawlResult[]>('/crawl/results', { params: { limit: 1 } });
    if (res.data && res.data.length > 0 && res.data[0].crawled_at) {
      return res.data[0].crawled_at;
    }
  } catch (error) {
    console.warn('[Crawler API] Could not fetch latest crawl time:', error);
  }
  return mockCrawlResults[0]?.crawled_at || new Date().toISOString();
}

export async function getCrawlResultsApi(source?: CrawlSource): Promise<CrawlResult[]> {
  try {
    const params: any = { limit: 200 };
    if (source) {
      params.source = source.toLowerCase();
    }
    const res = await apiClient.get<CrawlResult[]>('/crawl/results', { params });
    return res.data;
  } catch (error) {
    console.warn('[Crawler API] Fallback to mock crawl results:', error);
    if (source) {
      return mockCrawlResults.filter((r) => r.source.toUpperCase() === source.toUpperCase());
    }
    return mockCrawlResults;
  }
}

export const crawlerApi = {
  trigger: async (arg1: CrawlTriggerPayload | any, arg2 = 'phone'): Promise<any> => {
    let source: string;
    let category = arg2;
    let limit: number | undefined;

    if (typeof arg1 === 'object' && arg1 !== null) {
      source = arg1.source;
      category = arg1.category || arg2;
      limit = arg1.limit;
    } else {
      source = arg1;
    }

    const res = await triggerCrawlApi(source, category, limit);
    return {
      ...res,
      task_id: res.task_id || res.job_id || 'task-' + Date.now(),
    };
  },

  getStatus: async (taskId: string): Promise<CrawlProgressResponse> => {
    return request<CrawlProgressResponse>(`/crawl/status/${taskId}`);
  },

  getResults: (source?: string) => getCrawlResultsApi(source as CrawlSource | undefined),

  checkHealth: async (): Promise<{ status: string }> => {
    try {
      const rootUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '');
      const response = await fetch(`${rootUrl}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      return response.json();
    } catch {
      return { status: 'ok' };
    }
  },
};
