import { apiClient } from './client';
import { 
  PriceComparisonItem, 
  PricingRecommendation, 
  PriceChangeHistoryItem,
  MatrixSimulationRequest,
  MatrixSimulationResponse 
} from '../types/pricing';
import { SkuMappingPair } from '../types/matching';
import { mockPriceMatrix, mockRecommendations, mockMappingQueue, mockPriceHistory } from './mockData';

// Price Comparison Matrix
export async function getPriceMatrixApi(category?: string): Promise<PriceComparisonItem[]> {
  try {
    const params = category && category !== 'ALL' ? { category, limit: 100 } : { limit: 100 };
    const res = await apiClient.get<PriceComparisonItem[]>('/pricing/matrix', { params });
    const rawItems = Array.isArray(res.data) ? res.data : (res.data as any)?.items || [];
    if (rawItems && rawItems.length > 0) {
      return rawItems;
    }
    if (category && category !== 'ALL') {
      return mockPriceMatrix.filter((item) => item.category === category);
    }
    return mockPriceMatrix;
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
    const res = await apiClient.get<any>('/pricing/recommendations', { params: { limit: 200 } });
    const rawItems: any[] = Array.isArray(res.data) ? res.data : (res.data?.items || []);
    if (!rawItems || rawItems.length === 0) {
      return mockRecommendations;
    }
    return rawItems.map((item: any) => ({
      id: String(item.id),
      sku: item.sku || `SKU-${item.product_id || item.id}`,
      product_name: item.product_name || `Product ${item.sku || item.id}`,
      category: (item.category?.toUpperCase() === 'LAPTOP' ? 'LAPTOP' : 'PHONE') as 'PHONE' | 'LAPTOP',
      brand: item.brand || 'Apple',
      current_price: Number(item.current_price) || 0,
      suggested_price: Number(item.suggested_price) || 0,
      floor_price: Number(item.floor_price) || 0,
      cost_price: Number(item.cost_price) || 0,
      is_floor_protected: Boolean(item.is_floor_protected ?? (item.suggested_price <= item.floor_price)),
      doh: Number(item.doh) || 30,
      inventory_quantity: Number(item.inventory_quantity) || 10,
      min_competitor_price: Number(item.min_competitor_price) || Number(item.current_price) || 0,
      competitor_name: item.competitor_name || 'CellphoneS',
      competitor_in_stock: Boolean(item.competitor_in_stock ?? true),
      cellphones_price: item.cellphones_price ? Number(item.cellphones_price) : undefined,
      cellphones_in_stock: item.cellphones_in_stock !== undefined ? Boolean(item.cellphones_in_stock) : undefined,
      hoangha_price: item.hoangha_price ? Number(item.hoangha_price) : undefined,
      hoangha_in_stock: item.hoangha_in_stock !== undefined ? Boolean(item.hoangha_in_stock) : undefined,
      scenario: item.scenario || item.scenario_applied || item.scenario_name || 'Kịch bản đề xuất tự động',
      margin_impact_percent: Number(item.margin_impact_percent) || 0,
      status: (item.status?.toUpperCase() || 'PENDING') as 'PENDING' | 'APPROVED' | 'REJECTED',
      composite_score: item.composite_score !== undefined ? Number(item.composite_score) : 0,
      demand_score: item.demand_score !== undefined ? Number(item.demand_score) : 0,
      inventory_score: item.inventory_score !== undefined ? Number(item.inventory_score) : 0,
      competitor_score: item.competitor_score !== undefined ? Number(item.competitor_score) : 0,
      reasoning_3layers: item.reasoning_3layers || {},
      reviewed_at: item.reviewed_at ? String(item.reviewed_at) : undefined,
      reviewed_by: item.reviewed_by ? String(item.reviewed_by) : undefined,
    }));
  } catch (error) {
    return mockRecommendations;
  }
}

export async function approveRecommendationApi(id: string): Promise<void> {
  try {
    await apiClient.post(`/pricing/recommendations/${id}/approve`);
  } catch (error) {
    console.warn('[Pricing API] Local approve simulated for:', id, error);
  }
}

export async function rejectRecommendationApi(id: string): Promise<void> {
  try {
    await apiClient.post(`/pricing/recommendations/${id}/reject`);
  } catch (error) {
    console.warn('[Pricing API] Local reject simulated for:', id, error);
  }
}

export async function getPriceHistoryApi(): Promise<PriceChangeHistoryItem[]> {
  try {
    const res = await apiClient.get<any>('/pricing/history', { params: { limit: 100 } });
    const rawItems: any[] = Array.isArray(res.data) ? res.data : (res.data?.items || []);
    if (!rawItems || rawItems.length === 0) {
      return mockPriceHistory;
    }
    return rawItems.map((item: any) => ({
      id: String(item.id),
      sku: item.sku || `SKU-${item.product_id || item.id}`,
      product_name: item.product_name || `Product ${item.sku || item.id}`,
      category: (item.category?.toUpperCase() === 'LAPTOP' ? 'LAPTOP' : 'PHONE') as 'PHONE' | 'LAPTOP',
      old_price: Number(item.old_price) || 0,
      new_price: Number(item.new_price) || 0,
      price_change: Number(item.price_change ?? (item.new_price - item.old_price)) || 0,
      price_change_percent: Number(item.price_change_percent) || 0,
      cost_price: Number(item.cost_price) || 0,
      floor_price: Number(item.floor_price) || 0,
      margin_percent: Number(item.margin_percent) || 0,
      change_type: (item.change_type === 'AI_RECOMMENDED' ? 'AI_RECOMMENDED' : 'MANUAL_CONFIG') as 'AI_RECOMMENDED' | 'MANUAL_CONFIG',
      scenario: item.scenario || 'Cập nhật giá',
      changed_by: item.changed_by || 'Pricing Manager',
      changed_at: item.changed_at || new Date().toISOString(),
      status: (item.status === 'APPLIED' ? 'APPLIED' : 'SYNCED_POS') as 'APPLIED' | 'SYNCED_POS',
    }));
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
    console.warn('[Pricing API] Local custom price simulated for:', id, customPrice, changeType, error);
  }
}

// SKU Mapping Queue (60-79%)
export async function getSkuMappingQueueApi(): Promise<SkuMappingPair[]> {
  try {
    const res = await apiClient.get<SkuMappingPair[]>('/matching/queue');
    if (Array.isArray(res.data)) {
      return res.data;
    }
    return mockMappingQueue;
  } catch (error) {
    console.warn('[Matching API] Backend offline, fallback to mock queue:', error);
    return mockMappingQueue;
  }
}

export async function approveSkuMappingApi(id: string): Promise<void> {
  await apiClient.post(`/matching/queue/${id}/approve`);
}

export async function rejectSkuMappingApi(id: string): Promise<void> {
  await apiClient.post(`/matching/queue/${id}/reject`);
}

export interface SkuMatchingStats {
  total_skus: number;
  matched_skus: number;
  match_rate: number;
  pending_queue_count: number;
  approved_count: number;
  rejected_count: number;
}

export async function getSkuMatchingStatsApi(): Promise<SkuMatchingStats> {
  try {
    const res = await apiClient.get<SkuMatchingStats>('/matching/stats');
    if (res.data && typeof res.data.total_skus === 'number') {
      return res.data;
    }
  } catch (error) {
    console.warn('[Matching API] Could not fetch matching stats, falling back to mock:', error);
  }
  return {
    total_skus: 224,
    matched_skus: 195,
    match_rate: 87.1,
    pending_queue_count: mockMappingQueue.length,
    approved_count: 195,
    rejected_count: 0,
  };
}

// Matrix Pricing Simulation API
export async function simulateMatrixPricingApi(
  req: MatrixSimulationRequest
): Promise<MatrixSimulationResponse> {
  try {
    const res = await apiClient.post<MatrixSimulationResponse>('/pricing/matrix/simulate', req);
    return res.data;
  } catch (error) {
    // Client-side fallback calculation if API is offline
    const d = req.demand_score;
    const i = req.inventory_score;
    const c = req.competitor_score;
    const wD = req.weights?.demand ?? req.weights?.D ?? 0.40;
    const wI = req.weights?.inventory ?? req.weights?.I ?? 0.35;
    const wC = req.weights?.competitor ?? req.weights?.C ?? 0.25;
    const comp = Math.round((d * wD + i * wI + c * wC) * 100) / 100;

    const key = `${d.toFixed(1)},${i.toFixed(1)},${c.toFixed(1)}`;
    let scenarioName = 'Dải Composite';
    let actionType = 'Hold';
    let targetDelta = 0.0;
    let rationale = 'Phân bổ theo điểm tổng hợp composite.';

    if (key === '2.0,2.0,2.0') {
      scenarioName = 'Kịch bản 1: Festival / Sự kiện lớn';
      targetDelta = 0.12;
      actionType = 'Strong raise';
      rationale = 'Cả 3 yếu tố cùng tăng mạnh: Nhu cầu bùng nổ, hàng khan hiếm trong kho, đối thủ đang bán giá cao hơn.';
    } else if (key === '2.0,0.0,0.0') {
      scenarioName = 'Kịch bản 2: Sản phẩm Viral';
      targetDelta = 0.06;
      actionType = 'Moderate raise';
      rationale = 'Lượt tìm kiếm và quan tâm tăng vọt, trong khi lượng tồn kho vẫn đảm bảo và đối thủ chưa kịp điều chỉnh giá.';
    } else if (key === '0.0,0.0,0.0') {
      scenarioName = 'Kịch bản 3: Bình thường (Baseline)';
      targetDelta = 0.0;
      actionType = 'Hold';
      rationale = 'Thị trường ổn định, cung cầu cân bằng, giá đối thủ ngang bằng trong biên độ an toàn.';
    } else if (key === '2.0,-2.0,0.0') {
      scenarioName = 'Kịch bản 4: Cầu cao nhưng Hàng ứ';
      targetDelta = 0.0;
      actionType = 'Hold + Review';
      rationale = 'Nhu cầu mua lớn nhưng lượng tồn kho thực tế quá cao làm triệt tiêu áp lực tăng giá.';
    } else if (key === '-1.0,2.0,2.0') {
      scenarioName = 'Kịch bản 5: Hàng khan, Đối thủ hết nhưng Cầu yếu';
      targetDelta = 0.02;
      actionType = 'Mild raise';
      rationale = 'Kho sắp hết hàng và đối thủ đã Out-Of-Stock, nhưng nhu cầu khách chưa cao.';
    } else if (key === '-2.0,-2.0,-2.0') {
      scenarioName = 'Kịch bản 6: Khủng hoảng Nhu cầu';
      targetDelta = -0.15;
      actionType = 'Strong lower';
      rationale = 'Cả 3 yếu tố đều chạm đáy: Cầu sụt giảm, kho ứ đọng, đối thủ xả hàng.';
    } else if (key === '-2.0,0.0,-2.0') {
      scenarioName = 'Kịch bản 7: Khách quay lưng, Đối thủ rẻ';
      targetDelta = -0.10;
      actionType = 'Moderate lower';
      rationale = 'Lượt xem và giỏ hàng giảm mạnh do đối thủ đang bán rẻ hơn.';
    } else if (key === '2.0,2.0,-2.0') {
      scenarioName = 'Kịch bản 8: Cầu cao, Hàng khan nhưng Đối thủ rẻ';
      targetDelta = 0.06;
      actionType = 'Moderate raise';
      rationale = 'Nhu cầu lớn và kho khan hàng tạo động lực tăng giá mạnh, lấn át yếu tố đối thủ rẻ.';
    } else if (key === '1.0,-1.0,1.0') {
      scenarioName = 'Kịch bản 9: Tín hiệu Hỗn độn';
      targetDelta = 0.0;
      actionType = 'Hold + A/B Test';
      rationale = 'Các tín hiệu kéo giằng co theo các hướng ngược nhau.';
    } else if (key === '-2.0,-2.0,0.0') {
      scenarioName = 'Đặc biệt: Cuối vòng đời (Clearance)';
      targetDelta = -0.16;
      actionType = 'Clearance';
      rationale = 'Sản phẩm bước vào giai đoạn cuối vòng đời (EOL), cần xả kho thu hồi vốn.';
    } else {
      if (comp >= 1.50) {
        scenarioName = 'Dải Composite: Strong raise';
        targetDelta = 0.12;
        actionType = 'Strong raise';
      } else if (comp >= 0.75) {
        scenarioName = 'Dải Composite: Moderate raise';
        targetDelta = 0.06;
        actionType = 'Moderate raise';
      } else if (comp >= 0.25) {
        scenarioName = 'Dải Composite: Mild raise';
        targetDelta = 0.02;
        actionType = 'Mild raise';
      } else if (comp >= -0.24) {
        scenarioName = 'Dải Composite: Hold';
        targetDelta = 0.0;
        actionType = 'Hold';
      } else if (comp >= -0.74) {
        scenarioName = 'Dải Composite: Mild lower';
        targetDelta = -0.02;
        actionType = 'Mild lower';
      } else if (comp >= -1.49) {
        scenarioName = 'Dải Composite: Moderate lower';
        targetDelta = -0.06;
        actionType = 'Moderate lower';
      } else {
        scenarioName = 'Dải Composite: Strong lower';
        targetDelta = -0.15;
        actionType = 'Strong lower';
      }
      rationale = `Composite score = ${comp.toFixed(2)}`;
    }

    const maxRate = req.max_rate_cap ?? 0.10;
    const notes: string[] = [];
    let clampedPct = targetDelta;
    if (targetDelta > maxRate) {
      clampedPct = maxRate;
      notes.push(`Giới hạn bước nhảy (Rate Cap): Hãm từ ${(targetDelta * 100).toFixed(1)}% về ${(clampedPct * 100).toFixed(1)}%`);
    } else if (targetDelta < -maxRate) {
      clampedPct = -maxRate;
      notes.push(`Giới hạn bước nhảy (Rate Cap): Hãm từ ${(targetDelta * 100).toFixed(1)}% về ${(clampedPct * 100).toFixed(1)}%`);
    }

    const rawCandidate = Math.round(req.current_price * (1 + clampedPct));
    let finalPrice = rawCandidate;
    let isFloorCapped = false;

    if (rawCandidate < req.floor_price) {
      finalPrice = req.floor_price;
      isFloorCapped = true;
      notes.push('Kích hoạt bảo vệ giá sàn: Giá bán được chặn tại mức Floor Price.');
    }

    if (req.competitor_price && req.cost_price && req.competitor_price < Math.round(req.cost_price * 0.8)) {
      notes.push('Cảnh báo bán phá giá: Đối thủ đang bán dưới 80% giá vốn.');
    }

    return {
      demand_score: d,
      inventory_score: i,
      competitor_score: c,
      composite_score: comp,
      scenario_name: scenarioName,
      action_type: actionType,
      target_delta_pct: targetDelta,
      current_price: req.current_price,
      recommended_price: finalPrice,
      price_delta_amount: finalPrice - req.current_price,
      price_delta_pct: Math.round(((finalPrice - req.current_price) / req.current_price) * 10000) / 10000,
      is_floor_capped: isFloorCapped,
      guardrail_notes: notes,
      rationale,
    };
  }
}

