export interface ExplainableFactors {
  competitor_shift: {
    competitor: string;
    old_price?: number;
    new_price: number;
    price_cut: number;
    is_in_stock: boolean;
  };
  inventory_status: {
    sku: string;
    doh: number;
    quantity: number;
    doh_risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  floor_protection: {
    floor_price: number;
    suggested_price: number;
    safety_margin_percent: number;
    is_capped: boolean;
  };
}

export interface AiChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  tableData?: Array<Record<string, any>>;
  explainFactors?: ExplainableFactors;
  suggestions?: string[];
}

export interface AiMessageResponse {
  message: string;
  session_id?: string;
  tableData?: Array<Record<string, any>>;
  explainFactors?: ExplainableFactors;
  suggestions?: string[];
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
}
