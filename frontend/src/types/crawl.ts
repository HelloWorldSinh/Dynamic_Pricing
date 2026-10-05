export type CrawlSource = 'FPT' | 'CELLPHONES' | 'HOANGHA';

export interface CrawlResult {
  id: number;
  source: CrawlSource;
  product_name: string;
  url: string;
  price: number;
  is_in_stock: boolean;
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
