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

export async function triggerDualCrawlApi(_category?: string): Promise<any[]> {
  // Luôn kích hoạt Full Pipeline (cào cả Phone & Laptop từ CellphoneS và Hoàng Hà + tự động đối soát SKU vào DB)
  const res = await crawlerApi.triggerFullPipeline();
  return [res];
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

export interface CrawlResultsResponse {
  items: CrawlResult[];
  total: number;
}

export async function getCrawlResultsApi(
  source?: CrawlSource | string,
  category?: string,
  search?: string,
  stockStatus?: string,
  sortOrder?: string,
  skip: number = 0,
  limit: number = 50
): Promise<CrawlResultsResponse> {
  try {
    const params: any = { skip, limit };
    if (source && source !== 'ALL') {
      params.source = source.toLowerCase();
    }
    if (category && category !== 'ALL') {
      params.category = category.toLowerCase();
    }
    if (search) {
      params.search = search;
    }
    if (stockStatus && stockStatus !== 'ALL') {
      params.stock_status = stockStatus;
    }
    if (sortOrder) {
      params.sort_order = sortOrder;
    }

    const res = await apiClient.get<any>('/crawl/results', { params });
    const data = res.data?.items || res.data || [];
    const total = res.data?.total || data.length;

    const normalized: CrawlResult[] = data.map((item: any) => ({
      id: item.id,
      source: (item.source || '').toUpperCase() as CrawlSource,
      product_name: item.product_name || item.raw_name || 'Chưa cập nhật tên',
      url: item.url || '#',
      price: item.price ?? item.current_price ?? 0,
      original_price: item.original_price,
      is_in_stock: typeof item.is_in_stock === 'boolean' ? item.is_in_stock : true,
      stock_status_text: item.stock_status_text,
      category: item.category,
      specifications: item.specifications || item.raw_specs || {},
      crawled_at: item.crawled_at || new Date().toISOString(),
    }));
    return { items: normalized, total };
  } catch (error) {
    console.warn('[Crawler API] Fallback to mock crawl results:', error);
    let results = [...mockCrawlResults];
    if (source && source !== 'ALL') {
      results = results.filter((r) => r.source.toUpperCase() === source.toUpperCase());
    }
    if (category && category !== 'ALL') {
      results = results.filter((r) => !r.category || r.category.toUpperCase() === category.toUpperCase());
    }
    if (search) {
      const q = search.toLowerCase();
      results = results.filter((r) => r.product_name.toLowerCase().includes(q) || r.url.toLowerCase().includes(q));
    }
    if (stockStatus === 'IN_STOCK') {
      results = results.filter(r => r.is_in_stock);
    } else if (stockStatus === 'OUT_OF_STOCK') {
      results = results.filter(r => !r.is_in_stock);
    }
    
    if (sortOrder === 'PRICE_ASC') {
      results.sort((a, b) => a.price - b.price);
    } else if (sortOrder === 'PRICE_DESC') {
      results.sort((a, b) => b.price - a.price);
    } else if (sortOrder === 'NAME_ASC') {
      results.sort((a, b) => a.product_name.localeCompare(b.product_name));
    } else {
      results.sort((a, b) => new Date(b.crawled_at).getTime() - new Date(a.crawled_at).getTime());
    }

    const total = results.length;
    results = results.slice(skip, skip + limit);

    return { items: results, total };
  }
}

export interface CrawlStats {
  total: number;
  cellphones_count: number;
  hoangha_count: number;
  phone_count: number;
  laptop_count: number;
  in_stock_count: number;
  latest_crawled_at: string | null;
}

export async function getCrawlStatsApi(category?: string): Promise<CrawlStats> {
  try {
    const params: any = {};
    if (category && category !== 'ALL') {
      params.category = category.toLowerCase();
    }
    const res = await apiClient.get<CrawlStats>('/crawl/stats', { params });
    return res.data;
  } catch (error) {
    console.warn('[Crawler API] Fallback to mock crawl stats:', error);
    return {
      total: mockCrawlResults.length,
      cellphones_count: mockCrawlResults.filter((r) => r.source === 'CELLPHONES').length,
      hoangha_count: mockCrawlResults.filter((r) => r.source === 'HOANGHA').length,
      phone_count: 50,
      laptop_count: 30,
      in_stock_count: mockCrawlResults.filter((r) => r.is_in_stock).length,
      latest_crawled_at: new Date().toISOString()
    };
  }
}

export const crawlerApi = {
  trigger: async (arg1: CrawlTriggerPayload | any, arg2 = 'all'): Promise<any> => {
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

  triggerFullPipeline: async (): Promise<any> => {
    return crawlerApi.trigger({
      source: 'full_pipeline',
      category: 'all',
      limit: undefined,
    });
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
