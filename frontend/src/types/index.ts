export type CompetitorSource = 'cellphones' | 'hoangha' | 'fptshop';

export type MappingStatus = 'APPROVED' | 'PENDING' | 'UNMATCHED';

export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  brand?: string;
  base_price: number;
  cost_price: number;
  floor_price: number;
  doh: number;
}

export interface CrawlResultItem {
  id: string;
  source: CompetitorSource;
  url: string;
  product_name: string;
  current_price: number;
  original_price?: number;
  is_in_stock: boolean;
  specifications?: Record<string, string>;
  crawled_at: string;
}

export interface SkuMapping {
  id: number;
  fpt_sku: string;
  fpt_name: string;
  competitor_source: CompetitorSource;
  competitor_product_name: string;
  competitor_price: number;
  confidence_score: number;
  match_tier: 'TIER_1_EXACT' | 'TIER_2_FUZZY';
  status: MappingStatus;
  reviewed_at?: string;
}

export interface CrawlTriggerPayload {
  source: CompetitorSource;
  category?: string;
  target_url?: string;
}

export interface CrawlTriggerResponse {
  task_id: string;
  status: string;
  message: string;
  started_at: string;
}

export interface CrawlDebounceStatus {
  source: string;
  is_locked: boolean;
  remaining_seconds: number;
}

export interface SystemHealth {
  status: string;
  project: string;
  environment: string;
}
