export interface CompetitorPriceInfo {
  source: 'CELLPHONES' | 'HOANGHA';
  price: number;
  url: string;
  is_in_stock: boolean;
  product_name: string;
  matched_at?: string;
}

export interface PriceComparisonItem {
  id: string;
  sku: string;
  name: string;
  category: 'PHONE' | 'LAPTOP';
  brand: string;
  part_number?: string;
  fpt_price: number;
  cellphones?: CompetitorPriceInfo;
  hoangha?: CompetitorPriceInfo;
  min_competitor_price: number;
  price_diff: number; // fpt_price - min_competitor_price
  price_diff_percent: number; // ((fpt - comp) / comp) * 100
  confidence_score: number; // 0 - 100
  match_tier: 'EXACT_PART_NUMBER' | 'NORMALIZED_ATTRIBUTE' | 'MANUAL_REVIEW';
  doh: number; // Days on hand
  inventory_quantity: number;
  cost_price: number;
  floor_price: number;
  status: 'SAFE' | 'WARNING' | 'DANGER' | 'EQUAL';
}

export interface PricingRecommendation {
  id: string;
  sku: string;
  product_name: string;
  category: 'PHONE' | 'LAPTOP';
  brand: string;
  current_price: number;
  suggested_price: number;
  floor_price: number;
  cost_price: number;
  is_floor_protected: boolean;
  doh: number;
  inventory_quantity: number;
  min_competitor_price: number;
  competitor_name: string;
  competitor_in_stock: boolean;
  scenario: string; // e.g., "Kịch bản 4: DOH > 45 ngày & CellphoneS còn hàng"
  margin_impact_percent: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  reviewed_at?: string;
  reviewed_by?: string;
}
