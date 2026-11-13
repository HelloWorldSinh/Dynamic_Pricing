import { useQuery, QueryClient } from '@tanstack/react-query';
import { getSkuMappingQueueApi } from '../api/pricingApi';
import { SkuMappingPair } from '../types/matching';
import { pricingKeys } from './usePricingQueries';

export const skuKeys = {
  all: ['sku'] as const,
  queue: () => ['sku', 'queue'] as const,
};

export function useSkuMappingQueueQuery() {
  return useQuery<SkuMappingPair[]>({
    queryKey: skuKeys.queue(),
    queryFn: async () => {
      const data = await getSkuMappingQueueApi();
      return data.filter((item) => item.status === 'PENDING');
    },
  });
}

export function invalidateSkuQueries(qc: QueryClient) {
  // Khi duyệt hoặc từ chối SKU:
  // 1. Invalidate hàng đợi SKU
  // 2. Invalidate Ma trận giá (sản phẩm khớp mới sẽ xuất hiện trong ma trận)
  qc.invalidateQueries({ queryKey: skuKeys.all });
  qc.invalidateQueries({ queryKey: pricingKeys.all });
}
