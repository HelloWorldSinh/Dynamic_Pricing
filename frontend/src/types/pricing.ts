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

export type ApprovalTabType = 'PENDING' | 'APPROVED' | 'REJECTED' | 'HISTORY';

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
  cellphones_price?: number;
  cellphones_in_stock?: boolean;
  hoangha_price?: number;
  hoangha_in_stock?: boolean;
  scenario: string; // e.g., "Kịch bản 4: DOH > 45 ngày & CellphoneS còn hàng"
  margin_impact_percent: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  composite_score?: number;
  demand_score?: number;
  inventory_score?: number;
  competitor_score?: number;
  reasoning_3layers?: {
    competitor_factor?: string;
    inventory_factor?: string;
    market_demand_factor?: string;
    floor_protection_factor?: string;
    guardrail_notes?: string[];
  };
  reviewed_at?: string;
  reviewed_by?: string;
}

export interface PriceChangeHistoryItem {
  id: string;
  sku: string;
  product_name: string;
  category: 'PHONE' | 'LAPTOP';
  old_price: number;
  new_price: number;
  price_change: number; // new_price - old_price
  price_change_percent: number;
  cost_price: number;
  floor_price: number;
  margin_percent: number;
  change_type: 'AI_RECOMMENDED' | 'MANUAL_CONFIG';
  scenario: string;
  changed_by: string;
  changed_at: string;
  status: 'APPLIED' | 'SYNCED_POS';
}

export interface MatrixSimulationRequest {
  demand_score: number;
  inventory_score: number;
  competitor_score: number;
  weights?: {
    demand?: number;
    inventory?: number;
    competitor?: number;
    D?: number;
    I?: number;
    C?: number;
  };
  current_price: number;
  cost_price: number;
  floor_price: number;
  competitor_price?: number;
  max_rate_cap?: number;
}

export interface MatrixSimulationResponse {
  demand_score: number;
  inventory_score: number;
  competitor_score: number;
  composite_score: number;
  scenario_name: string;
  action_type: string;
  target_delta_pct: number;
  current_price: number;
  recommended_price: number;
  price_delta_amount: number;
  price_delta_pct: number;
  is_floor_capped: boolean;
  guardrail_notes: string[];
  rationale: string;
}

