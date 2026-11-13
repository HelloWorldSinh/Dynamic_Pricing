import { useQuery, QueryClient } from '@tanstack/react-query';
import { 
  getPriceMatrixApi, 
  getRecommendationsApi, 
  getPriceHistoryApi 
} from '../api/pricingApi';
import { PriceComparisonItem, PricingRecommendation, PriceChangeHistoryItem } from '../types/pricing';

export const pricingKeys = {
  all: ['pricing'] as const,
  matrix: (category?: string) => ['pricing', 'matrix', category || 'ALL'] as const,
  recommendations: () => ['pricing', 'recommendations'] as const,
  history: () => ['pricing', 'history'] as const,
};

export function usePriceMatrixQuery(category?: string) {
  return useQuery<PriceComparisonItem[]>({
    queryKey: pricingKeys.matrix(category),
    queryFn: () => getPriceMatrixApi(category),
  });
}

export function useRecommendationsQuery() {
  return useQuery<PricingRecommendation[]>({
    queryKey: pricingKeys.recommendations(),
    queryFn: () => getRecommendationsApi(),
  });
}

export function usePriceHistoryQuery() {
  return useQuery<PriceChangeHistoryItem[]>({
    queryKey: pricingKeys.history(),
    queryFn: () => getPriceHistoryApi(),
  });
}

export function invalidatePricingQueries(qc?: QueryClient) {
  if (qc) {
    qc.invalidateQueries({ queryKey: pricingKeys.all });
  }
}
