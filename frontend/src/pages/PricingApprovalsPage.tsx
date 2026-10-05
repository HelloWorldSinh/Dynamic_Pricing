import React, { useState, useEffect, useMemo } from 'react';
import { Search, X } from 'lucide-react';
import { ApprovalFilterTabs } from '../components/recommendations/ApprovalFilterTabs';
import { BatchActionBar } from '../components/recommendations/BatchActionBar';
import { RecommendationTable } from '../components/recommendations/RecommendationTable';
import { PriceHistoryTable } from '../components/recommendations/PriceHistoryTable';
import { PricingDetailModal } from '../components/recommendations/PricingDetailModal';
import { Pagination } from '../components/common/Pagination';
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

  // Search
  const [searchQuery, setSearchQuery] = useState('');

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

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

  // Reset to page 1 and clear selections when tab, category, or search query changes
  useEffect(() => {
    setCurrentPage(1);
    setSelectedIds([]);
  }, [currentTab, categoryFilter, searchQuery]);

  // Filter items according to tab, category & search query
  const filteredRecommendations = useMemo(() => {
    return recommendations.filter((r) => {
      if (r.status !== currentTab) return false;
      if (categoryFilter !== 'ALL' && r.category !== categoryFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = r.product_name.toLowerCase().includes(q);
        const matchSku = r.sku.toLowerCase().includes(q);
        const matchScenario = r.scenario?.toLowerCase().includes(q) || false;
        if (!matchName && !matchSku && !matchScenario) return false;
      }
      return true;
    });
  }, [recommendations, currentTab, categoryFilter, searchQuery]);

  const filteredHistoryItems = useMemo(() => {
    return historyItems.filter((h) => {
      if (categoryFilter !== 'ALL' && h.category !== categoryFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = h.product_name.toLowerCase().includes(q);
        const matchSku = h.sku.toLowerCase().includes(q);
        const matchUser = h.changed_by.toLowerCase().includes(q);
        const matchScenario = h.scenario?.toLowerCase().includes(q) || false;
        if (!matchName && !matchSku && !matchUser && !matchScenario) return false;
      }
      return true;
    });
  }, [historyItems, categoryFilter, searchQuery]);

  // Group history items by product (SKU)
  const historyProductGroups = useMemo(() => {
    const map = new Map<string, {
      sku: string;
      product_name: string;
      category: string;
      latestItem: PriceChangeHistoryItem;
      revisionsCount: number;
    }>();

    const countMap = new Map<string, number>();
    historyItems.forEach((item) => {
      countMap.set(item.sku, (countMap.get(item.sku) || 0) + 1);
    });

    filteredHistoryItems.forEach((item) => {
      if (!map.has(item.sku)) {
        map.set(item.sku, {
          sku: item.sku,
          product_name: item.product_name,
          category: item.category,
          latestItem: item,
          revisionsCount: countMap.get(item.sku) || 1,
        });
      }
    });

    return Array.from(map.values());
  }, [filteredHistoryItems, historyItems]);

  const counts = {
    pending: recommendations.filter((r) => r.status === 'PENDING' && (categoryFilter === 'ALL' || r.category === categoryFilter)).length,
    approved: recommendations.filter((r) => r.status === 'APPROVED' && (categoryFilter === 'ALL' || r.category === categoryFilter)).length,
    rejected: recommendations.filter((r) => r.status === 'REJECTED' && (categoryFilter === 'ALL' || r.category === categoryFilter)).length,
    history: historyProductGroups.length,
  };

  // Paginated data
  const totalRecPages = Math.ceil(filteredRecommendations.length / pageSize) || 1;
  const paginatedRecommendations = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecommendations.slice(start, start + pageSize);
  }, [filteredRecommendations, currentPage, pageSize]);

  const totalHistPages = Math.ceil(historyProductGroups.length / pageSize) || 1;
  const paginatedHistoryProducts = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return historyProductGroups.slice(start, start + pageSize);
  }, [historyProductGroups, currentPage, pageSize]);

  // Selection handlers
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleToggleSelectAll = () => {
    const pageItemIds = paginatedRecommendations.map((i) => i.id);
    const allPageSelected = pageItemIds.length > 0 && pageItemIds.every((id) => selectedIds.includes(id));
    if (allPageSelected) {
      setSelectedIds((prev) => prev.filter((id) => !pageItemIds.includes(id)));
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...pageItemIds])));
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

      {/* Search Toolbar */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo tên sản phẩm, mã SKU hoặc kịch bản..."
            className="w-full pl-9 pr-8 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded transition"
              title="Xóa tìm kiếm"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="text-xs text-slate-500 flex items-center gap-2">
          <span>
            Tìm thấy: <strong className="font-semibold text-slate-900 dark:text-white">
              {currentTab === 'HISTORY' ? historyProductGroups.length : filteredRecommendations.length}
            </strong> {currentTab === 'HISTORY' ? 'sản phẩm' : 'đề xuất'}
          </span>
        </div>
      </div>

      {/* Conditional Content based on Tab */}
      {currentTab === 'HISTORY' ? (
        <>
          <PriceHistoryTable products={paginatedHistoryProducts} allItems={historyItems} />
          <Pagination
            currentPage={currentPage}
            totalPages={totalHistPages}
            totalItems={historyProductGroups.length}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={(newSize) => {
              setPageSize(newSize);
              setCurrentPage(1);
            }}
            itemLabel="sản phẩm"
          />
        </>
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
            <>
              <RecommendationTable
                items={paginatedRecommendations}
                selectedIds={selectedIds}
                onToggleSelect={handleToggleSelect}
                onToggleSelectAll={handleToggleSelectAll}
                onApprove={handleApprove}
                onReject={handleReject}
                onOpenDetail={(item) => setSelectedDetailItem(item)}
              />
              <Pagination
                currentPage={currentPage}
                totalPages={totalRecPages}
                totalItems={filteredRecommendations.length}
                pageSize={pageSize}
                onPageChange={setCurrentPage}
                onPageSizeChange={(newSize) => {
                  setPageSize(newSize);
                  setCurrentPage(1);
                }}
                itemLabel="đề xuất"
              />
            </>
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

