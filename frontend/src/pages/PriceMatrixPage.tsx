import React, { useState, useEffect, useMemo } from 'react';
import { UnifiedMatrixToolbar } from '../components/matrix/UnifiedMatrixToolbar';
import { PriceMatrixTable } from '../components/matrix/PriceMatrixTable';
import { Pagination } from '../components/common/Pagination';
import { TableSkeleton } from '../components/common/TableSkeleton';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { PriceComparisonItem } from '../types/pricing';
import { usePriceMatrixQuery } from '../hooks/usePricingQueries';
import { useAiChat } from '../context/AiChatContext';

interface PriceMatrixPageProps {
  categoryFilter?: string;
  onOpenProductDetail?: (product: PriceComparisonItem) => void;
  onOpenAiExplain?: (product: PriceComparisonItem) => void;
}

export const PriceMatrixPage: React.FC<PriceMatrixPageProps> = ({
  categoryFilter: initialCategoryFilter = 'ALL',
  onOpenAiExplain,
}) => {
  const { askExplanationForSku } = useAiChat();
  const [categoryFilter, setCategoryFilter] = useState(initialCategoryFilter);

  // TanStack Query for Server State & Caching
  const { 
    data: items = [], 
    isLoading, 
    isFetching, 
    isError,
    error,
    refetch 
  } = usePriceMatrixQuery(categoryFilter);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [priceGapFilter, setPriceGapFilter] = useState('ALL');
  const [dohRiskFilter, setDohRiskFilter] = useState(false);
  const [inStockOnlyFilter, setInStockOnlyFilter] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Reset to page 1 when any filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [categoryFilter, searchQuery, priceGapFilter, dohRiskFilter, inStockOnlyFilter]);

  const handleResetFilters = () => {
    setCategoryFilter('ALL');
    setSearchQuery('');
    setPriceGapFilter('ALL');
    setDohRiskFilter(false);
    setInStockOnlyFilter(false);
  };

  // Filtered Items logic
  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Category Filter
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

  const totalPages = Math.ceil(filteredItems.length / pageSize) || 1;
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [filteredItems, currentPage, pageSize]);

  return (
    <div>
      {/* Unified Filter Toolbar with Integrated Category Selector & Crawl Trigger */}
      <UnifiedMatrixToolbar
        categoryFilter={categoryFilter}
        setCategoryFilter={setCategoryFilter}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        priceGapFilter={priceGapFilter}
        setPriceGapFilter={setPriceGapFilter}
        dohRiskFilter={dohRiskFilter}
        setDohRiskFilter={setDohRiskFilter}
        inStockOnlyFilter={inStockOnlyFilter}
        setInStockOnlyFilter={setInStockOnlyFilter}
        onCrawlCompleted={() => refetch()}
      />

      {/* Background Revalidation Indicator */}
      {isFetching && !isLoading && (
        <div className="mb-2 text-right">
          <span className="text-2xs font-mono font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded border border-slate-200 dark:border-slate-700">
            Đang đồng bộ dữ liệu...
          </span>
        </div>
      )}

      {/* Error Banner with Retry */}
      {isError && (
        <ErrorBanner
          message={(error as Error)?.message || 'Không thể kết nối đến máy chủ lấy dữ liệu ma trận giá.'}
          onRetry={() => refetch()}
        />
      )}

      {/* Main 3-Way Comparison Table with Skeleton Loading */}
      {isLoading ? (
        <TableSkeleton rows={8} cols={6} />
      ) : (
        <>
          <PriceMatrixTable
            items={paginatedItems}
            onResetFilters={handleResetFilters}
            onExplainProduct={(item) => {
              if (onOpenAiExplain) {
                onOpenAiExplain(item);
              } else {
                askExplanationForSku(item.sku, item.name);
              }
            }}
          />
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={filteredItems.length}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={(newSize) => {
              setPageSize(newSize);
              setCurrentPage(1);
            }}
            itemLabel="sản phẩm"
          />
        </>
      )}
    </div>
  );
};
