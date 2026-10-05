import React, { useState, useEffect } from 'react';
import { ApprovalFilterTabs } from '../components/recommendations/ApprovalFilterTabs';
import { BatchActionBar } from '../components/recommendations/BatchActionBar';
import { RecommendationTable } from '../components/recommendations/RecommendationTable';
import { PriceHistoryTable } from '../components/recommendations/PriceHistoryTable';
import { PricingDetailModal } from '../components/recommendations/PricingDetailModal';
import { PricingRecommendation, PriceChangeHistoryItem, ApprovalTabType } from '../types/pricing';
import { 
  getRecommendationsApi, 
  approveRecommendationApi, 
  rejectRecommendationApi,
  getPriceHistoryApi,
  applyCustomPriceApi
} from '../api/pricingApi';

interface PricingApprovalsPageProps {
  categoryFilter: string;
}

export const PricingApprovalsPage: React.FC<PricingApprovalsPageProps> = ({
  categoryFilter,
}) => {
  const [recommendations, setRecommendations] = useState<PricingRecommendation[]>([]);
  const [historyItems, setHistoryItems] = useState<PriceChangeHistoryItem[]>([]);
  const [currentTab, setCurrentTab] = useState<ApprovalTabType>('PENDING');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedDetailItem, setSelectedDetailItem] = useState<PricingRecommendation | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [recData, histData] = await Promise.all([
        getRecommendationsApi(),
        getPriceHistoryApi()
      ]);
      setRecommendations(recData);
      setHistoryItems(histData);
    } catch (error) {
      console.error('Lỗi nạp dữ liệu duyệt giá:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter items according to tab & category
  const filteredRecommendations = recommendations.filter((r) => {
    if (r.status !== currentTab) return false;
    if (categoryFilter !== 'ALL' && r.category !== categoryFilter) return false;
    return true;
  });

  const filteredHistoryItems = historyItems.filter((h) => {
    if (categoryFilter !== 'ALL' && h.category !== categoryFilter) return false;
    return true;
  });

  const counts = {
    pending: recommendations.filter((r) => r.status === 'PENDING').length,
    approved: recommendations.filter((r) => r.status === 'APPROVED').length,
    rejected: recommendations.filter((r) => r.status === 'REJECTED').length,
    history: filteredHistoryItems.length,
  };

  // Selection handlers
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleToggleSelectAll = () => {
    if (selectedIds.length === filteredRecommendations.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredRecommendations.map((i) => i.id));
    }
  };

  const handleClearSelection = () => {
    setSelectedIds([]);
  };

  // Helper to record approval into history
  const recordToHistory = (
    rec: PricingRecommendation,
    finalPrice: number,
    changeType: 'AI_RECOMMENDED' | 'MANUAL_CONFIG'
  ) => {
    const newHistory: PriceChangeHistoryItem = {
      id: 'hist-' + Date.now() + '-' + Math.random().toString(36).substring(2, 6),
      sku: rec.sku,
      product_name: rec.product_name,
      category: rec.category,
      old_price: rec.current_price,
      new_price: finalPrice,
      price_change: finalPrice - rec.current_price,
      price_change_percent: Math.round(((finalPrice - rec.current_price) / rec.current_price) * 1000) / 10,
      cost_price: rec.cost_price,
      floor_price: rec.floor_price,
      margin_percent: Math.round(((finalPrice - rec.cost_price) / finalPrice) * 1000) / 10,
      change_type: changeType,
      scenario: changeType === 'AI_RECOMMENDED' ? rec.scenario : 'Chỉnh tay tại màn hình Detail',
      changed_by: 'Pricing Analyst',
      changed_at: new Date().toISOString(),
      status: 'SYNCED_POS',
    };
    setHistoryItems((prev) => [newHistory, ...prev]);
  };

  // Actions
  const handleApprove = async (id: string) => {
    const rec = recommendations.find((r) => r.id === id);
    await approveRecommendationApi(id);
    if (rec) {
      recordToHistory(rec, rec.suggested_price, 'AI_RECOMMENDED');
    }
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'APPROVED' } : r))
    );
    setSelectedIds((prev) => prev.filter((i) => i !== id));
  };

  const handleReject = async (id: string) => {
    await rejectRecommendationApi(id);
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'REJECTED' } : r))
    );
    setSelectedIds((prev) => prev.filter((i) => i !== id));
  };

  const handleBatchApprove = async () => {
    for (const id of selectedIds) {
      const rec = recommendations.find((r) => r.id === id);
      await approveRecommendationApi(id);
      if (rec) {
        recordToHistory(rec, rec.suggested_price, 'AI_RECOMMENDED');
      }
    }
    setRecommendations((prev) =>
      prev.map((r) => (selectedIds.includes(r.id) ? { ...r, status: 'APPROVED' } : r))
    );
    setSelectedIds([]);
  };

  const handleBatchReject = async () => {
    for (const id of selectedIds) {
      await rejectRecommendationApi(id);
    }
    setRecommendations((prev) =>
      prev.map((r) => (selectedIds.includes(r.id) ? { ...r, status: 'REJECTED' } : r))
    );
    setSelectedIds([]);
  };

  // Apply custom or suggested price from Detail Modal
  const handleApplyFromDetail = async (
    id: string,
    finalPrice: number,
    changeType: 'AI_RECOMMENDED' | 'MANUAL_CONFIG'
  ) => {
    const rec = recommendations.find((r) => r.id === id);
    if (rec) {
      await applyCustomPriceApi(id, finalPrice, changeType);
      recordToHistory(rec, finalPrice, changeType);
      setRecommendations((prev) =>
        prev.map((r) =>
          r.id === id
            ? { ...r, suggested_price: finalPrice, status: 'APPROVED' }
            : r
        )
      );
      setSelectedIds((prev) => prev.filter((i) => i !== id));
    }
    setSelectedDetailItem(null);
  };

  const handleRejectFromDetail = async (id: string) => {
    await handleReject(id);
    setSelectedDetailItem(null);
  };

  return (
    <div>
      {/* Intro Header */}
      <div className="mb-4">
        <h2 className="text-base font-bold text-slate-900 dark:text-white">
          Pricing Approvals
        </h2>
      </div>

      {/* Tabs */}
      <ApprovalFilterTabs
        currentTab={currentTab}
        onTabChange={(tab) => {
          setCurrentTab(tab);
          setSelectedIds([]);
        }}
        counts={counts}
      />

      {/* Conditional Content based on Tab */}
      {currentTab === 'HISTORY' ? (
        <PriceHistoryTable items={filteredHistoryItems} />
      ) : (
        <>
          {/* Batch Action Bar */}
          {currentTab === 'PENDING' && (
            <BatchActionBar
              selectedCount={selectedIds.length}
              onBatchApprove={handleBatchApprove}
              onBatchReject={handleBatchReject}
              onClearSelection={handleClearSelection}
            />
          )}

          {/* Table */}
          {loading ? (
            <div className="p-12 text-center text-slate-400 text-xs">
              Đang nạp danh sách đề xuất giá...
            </div>
          ) : (
            <RecommendationTable
              items={filteredRecommendations}
              selectedIds={selectedIds}
              onToggleSelect={handleToggleSelect}
              onToggleSelectAll={handleToggleSelectAll}
              onApprove={handleApprove}
              onReject={handleReject}
              onOpenDetail={(item) => setSelectedDetailItem(item)}
            />
          )}
        </>
      )}

      {/* Pricing Detail Modal */}
      <PricingDetailModal
        recommendation={selectedDetailItem}
        onClose={() => setSelectedDetailItem(null)}
        onApply={handleApplyFromDetail}
        onReject={handleRejectFromDetail}
      />
    </div>
  );
};

