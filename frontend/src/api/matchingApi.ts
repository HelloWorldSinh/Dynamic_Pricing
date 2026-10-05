import { request } from './client.js';
import type { SkuMapping } from '../types/index.js';

export interface MappingFilterParams {
  status?: string;
  source?: string;
  min_confidence?: number;
}

export const matchingApi = {
  async getMappings(params: MappingFilterParams = {}): Promise<SkuMapping[]> {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.source) query.append('source', params.source);
    if (params.min_confidence !== undefined) query.append('min_confidence', params.min_confidence.toString());

    const qs = query.toString();
    const endpoint = `/products/mappings${qs ? `?${qs}` : ''}`;
    try {
      return await request<SkuMapping[]>(endpoint);
    } catch {
      // Fallback cho truong hop mock local / endpoint chua expose
      return [];
    }
  },

  async reviewMapping(id: number, action: 'approve' | 'reject'): Promise<{ success: boolean }> {
    return request<{ success: boolean }>(`/products/mappings/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  }
};
