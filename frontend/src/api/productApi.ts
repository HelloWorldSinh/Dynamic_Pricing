import { apiClient } from './client';
import { Product } from '../types/product';

export async function getProductsApi(category?: string, limit = 50): Promise<Product[]> {
  try {
    const params: Record<string, any> = { limit };
    if (category && category !== 'ALL') {
      params.category = category;
    }
    const res = await apiClient.get<Product[]>('/products', { params });
    return res.data;
  } catch (error) {
    console.warn('[Product API] Fallback to empty products:', error);
    return [];
  }
}
