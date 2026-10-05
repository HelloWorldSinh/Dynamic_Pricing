import React, { useState, useEffect, useMemo } from 'react';
import { MetricKpiCards } from '../components/matrix/MetricKpiCards';
import { DebounceTriggerBar } from '../components/matrix/DebounceTriggerBar';
import { MatrixFilterToolbar } from '../components/matrix/MatrixFilterToolbar';
import { PriceMatrixTable } from '../components/matrix/PriceMatrixTable';
import { PriceComparisonItem } from '../types/pricing';
import { getPriceMatrixApi, getRecommendationsApi } from '../api/pricingApi';

interface PriceMatrixPageProps {
  categoryFilter: string;
  onOpenProductDetail: (product: PriceComparisonItem) => void;
  onOpenAiExplain: (product: PriceComparisonItem) => void;
}

export const PriceMatrixPage: React.FC<PriceMatrixPageProps> = ({
  categoryFilter,
  onOpenProductDetail,
  onOpenAiExplain,
}) => {
  const [items, setItems] = useState<PriceComparisonItem[]>([]);
  const [pendingCount, setPendingCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [priceGapFilter, setPriceGapFilter] = useState('ALL');
  const [dohRiskFilter, setDohRiskFilter] = useState(false);
  const [inStockOnlyFilter, setInStockOnlyFilter] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [matrixData, recData] = await Promise.all([
        getPriceMatrixApi(categoryFilter),
        getRecommendationsApi(),
      ]);
      setItems(matrixData);
      setPendingCount(recData.filter((r) => r.status === 'PENDING').length);
    } catch (error) {
      console.error('Lỗi nạp dữ liệu ma trận giá:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [categoryFilter]);

  // Filtered Items logic
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Category Filter (from Navbar)
      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) {
        return false;
      }

      // Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = item.name.toLowerCase().includes(q);
        const matchSku = item.sku.toLowerCase().includes(q);
        const matchPart = item.part_number?.toLowerCase().includes(q) || false;
        if (!matchName && !matchSku && !matchPart) {
          return false;
        }
      }

      // Price Gap Filter
      if (priceGapFilter === 'GAP_5' && item.price_diff_percent < 5) {
        return false;
      }
      if (priceGapFilter === 'GAP_2' && item.price_diff_percent < 2) {
        return false;
      }
      if (priceGapFilter === 'CHEAPER' && item.price_diff >= 0) {
        return false;
      }

      // DOH Risk Filter (> 30 days)
      if (dohRiskFilter && item.doh <= 30) {
        return false;
      }

      // In Stock Only Filter
      if (inStockOnlyFilter) {
        const compInStock =
          (item.cellphones && item.cellphones.is_in_stock) ||
          (item.hoangha && item.hoangha.is_in_stock);
        if (!compInStock) return false;
      }

      return true;
    });
  }, [items, categoryFilter, searchQuery, priceGapFilter, dohRiskFilter, inStockOnlyFilter]);

  return (
    <div>
      {/* 4 KPI Summary Cards */}
      <MetricKpiCards items={items} pendingApprovalsCount={pendingCount} />

      {/* On-Demand Crawl with 30s Debounce */}
      <DebounceTriggerBar category={categoryFilter} onCrawlCompleted={fetchData} />

      {/* Multi-criteria Filter Toolbar */}
      <MatrixFilterToolbar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        priceGapFilter={priceGapFilter}
        setPriceGapFilter={setPriceGapFilter}
        dohRiskFilter={dohRiskFilter}
        setDohRiskFilter={setDohRiskFilter}
        inStockOnlyFilter={inStockOnlyFilter}
        setInStockOnlyFilter={setInStockOnlyFilter}
        totalFiltered={filteredItems.length}
      />

      {/* Main 3-Way Comparison Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Đang nạp dữ liệu đối soát giá 3 bên...
        </div>
      ) : (
        <PriceMatrixTable
          items={filteredItems}
          onSelectProduct={onOpenProductDetail}
          onExplainProduct={onOpenAiExplain}
        />
      )}
    </div>
  );
};
