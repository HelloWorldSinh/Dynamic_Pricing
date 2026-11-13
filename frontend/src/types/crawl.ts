export type CrawlSource = 'FPT' | 'FPTSHOP' | 'CELLPHONES' | 'HOANGHA' | 'FULL_PIPELINE' | 'ALL';

export interface CrawlResult {
  id: string | number;
  source: CrawlSource;
  product_name: string;
  url: string;
  price: number;
  original_price?: number;
  is_in_stock: boolean;
  category?: string;
  specifications?: Record<string, any>;
  crawled_at: string;
}

export interface CrawlJobResponse {
  message: string;
  job_id?: string;
  source: CrawlSource;
  category: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  started_at: string;
}

export interface DebounceStatus {
  isDebounced: boolean;
  remainingSeconds: number;
}
