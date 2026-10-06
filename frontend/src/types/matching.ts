import { ProductSpecs } from './product';

export interface SkuMappingPair {
  id: string;
  fpt_sku: string;
  fpt_name: string;
  fpt_part_number?: string;
  fpt_specs?: ProductSpecs;
  fpt_price: number;
  competitor_source: 'CELLPHONES' | 'HOANGHA';
  competitor_name: string;
  competitor_url: string;
  competitor_price: number;
  competitor_part_number?: string;
  competitor_specs?: ProductSpecs;
  confidence_score: number; // 60 - 79
  matched_attributes: string[];
  differing_attributes: string[];
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
}
