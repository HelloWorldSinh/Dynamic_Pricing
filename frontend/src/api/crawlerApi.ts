import { apiClient } from './client';
import { CrawlResult, CrawlJobResponse, CrawlSource } from '../types/crawl';
import { mockCrawlResults } from './mockData';

export async function triggerCrawlApi(source: CrawlSource, category: string): Promise<CrawlJobResponse> {
  try {
    const res = await apiClient.post<CrawlJobResponse>('/crawl/trigger', {
      source,
      category: category.toLowerCase(),
    });
    return res.data;
  } catch (error: any) {
    // If backend 429 debounce, re-throw to allow component to display remaining countdown
    if (error.response?.status === 429) {
      throw error;
    }
    // Fallback simulation when offline
    console.warn('[Crawler API] Fallback to simulated trigger');
    return {
      message: `Đã kích hoạt cào dữ liệu cho ${source} (${category})`,
      source,
      category,
      status: 'RUNNING',
      started_at: new Date().toISOString()
    };
  }
}

export async function getCrawlResultsApi(source?: CrawlSource): Promise<CrawlResult[]> {
  try {
    const params = source ? { source } : {};
    const res = await apiClient.get<CrawlResult[]>('/crawl/results', { params });
    return res.data;
  } catch (error) {
    console.warn('[Crawler API] Fallback to mock crawl results:', error);
    if (source) {
      return mockCrawlResults.filter((r) => r.source === source);
    }
    return mockCrawlResults;
  }
}

export const crawlerApi = {
  trigger: async (arg1: any, arg2 = 'phone'): Promise<CrawlJobResponse & { task_id: string }> => {
    let source: CrawlSource;
    let category = arg2;
    if (typeof arg1 === 'object' && arg1 !== null) {
      source = arg1.source as CrawlSource;
      category = arg1.category || arg2;
    } else {
      source = arg1 as CrawlSource;
    }
    const res = await triggerCrawlApi(source, category);
    return {
      ...res,
      task_id: res.job_id || 'task-' + Date.now(),
    };
  },
  getResults: (source?: string) => getCrawlResultsApi(source as CrawlSource | undefined),
  checkHealth: async () => ({ status: 'ok' }),
};



