import { apiClient } from './client';
import { PriceComparisonItem, PricingRecommendation, PriceChangeHistoryItem } from '../types/pricing';
import { SkuMappingPair } from '../types/matching';
import { mockPriceMatrix, mockRecommendations, mockMappingQueue, mockPriceHistory } from './mockData';

// Price Comparison Matrix
export async function getPriceMatrixApi(category?: string): Promise<PriceComparisonItem[]> {
  try {
    const params = category && category !== 'ALL' ? { category } : {};
    const res = await apiClient.get<PriceComparisonItem[]>('/pricing/matrix', { params });
    return res.data;
  } catch (error) {
    // Graceful fallback to mock data
    if (category && category !== 'ALL') {
      return mockPriceMatrix.filter((item) => item.category === category);
    }
    return mockPriceMatrix;
  }
}

// Pricing Recommendations & Approvals
export async function getRecommendationsApi(): Promise<PricingRecommendation[]> {
  try {
    const res = await apiClient.get<PricingRecommendation[]>('/pricing/recommendations');
    return res.data;
  } catch (error) {
    return mockRecommendations;
  }
}

export async function approveRecommendationApi(id: string): Promise<void> {
  try {
    await apiClient.post(`/pricing/recommendations/${id}/approve`);
  } catch (error) {
    console.log('[Pricing API] Local approve simulated for:', id);
  }
}

export async function rejectRecommendationApi(id: string): Promise<void> {
  try {
    await apiClient.post(`/pricing/recommendations/${id}/reject`);
  } catch (error) {
    console.log('[Pricing API] Local reject simulated for:', id);
  }
}

export async function getPriceHistoryApi(): Promise<PriceChangeHistoryItem[]> {
  try {
    const res = await apiClient.get<PriceChangeHistoryItem[]>('/pricing/history');
    return res.data;
  } catch (error) {
    return mockPriceHistory;
  }
}

export async function applyCustomPriceApi(
  id: string,
  customPrice: number,
  changeType: 'AI_RECOMMENDED' | 'MANUAL_CONFIG' = 'MANUAL_CONFIG'
): Promise<void> {
  try {
    await apiClient.post(`/pricing/recommendations/${id}/apply-custom`, {
      custom_price: customPrice,
      change_type: changeType,
    });
  } catch (error) {
    console.log('[Pricing API] Local custom price simulated for:', id, customPrice, changeType);
  }
}

// SKU Mapping Queue (60-79%)
export async function getSkuMappingQueueApi(): Promise<SkuMappingPair[]> {
  try {
    const res = await apiClient.get<SkuMappingPair[]>('/matching/queue');
    return res.data;
  } catch (error) {
    return mockMappingQueue;
  }
}

export async function approveSkuMappingApi(id: string): Promise<void> {
  try {
    await apiClient.post(`/matching/queue/${id}/approve`);
  } catch (error) {
    console.log('[Matching API] Local approve simulated for:', id);
  }
}

export async function rejectSkuMappingApi(id: string): Promise<void> {
  try {
    await apiClient.post(`/matching/queue/${id}/reject`);
  } catch (error) {
    console.log('[Matching API] Local reject simulated for:', id);
  }
}
