import React, { useState, useEffect, useMemo } from 'react';
import { DebounceTriggerBar } from '../components/matrix/DebounceTriggerBar';
import { MatrixFilterToolbar } from '../components/matrix/MatrixFilterToolbar';
import { PriceMatrixTable } from '../components/matrix/PriceMatrixTable';
import { Pagination } from '../components/common/Pagination';
import { PriceComparisonItem } from '../types/pricing';
import { getPriceMatrixApi } from '../api/pricingApi';

interface PriceMatrixPageProps {
  categoryFilter: string;
  onOpenProductDetail: (product: PriceComparisonItem) => void;
  onOpenAiExplain?: (product: PriceComparisonItem) => void;
}

export const PriceMatrixPage: React.FC<PriceMatrixPageProps> = ({
  categoryFilter,
  onOpenProductDetail,
}) => {
  const [items, setItems] = useState<PriceComparisonItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [priceGapFilter, setPriceGapFilter] = useState('ALL');
  const [dohRiskFilter, setDohRiskFilter] = useState(false);
  const [inStockOnlyFilter, setInStockOnlyFilter] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const fetchData = async () => {
    setLoading(true);
    try {
      const matrixData = await getPriceMatrixApi(categoryFilter);
      setItems(matrixData);
    } catch (error) {
      console.error('Lỗi nạp dữ liệu ma trận giá:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [categoryFilter]);

  // Reset to page 1 when any filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [categoryFilter, searchQuery, priceGapFilter, dohRiskFilter, inStockOnlyFilter]);

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

  const totalPages = Math.ceil(filteredItems.length / pageSize) || 1;
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredItems.slice(start, start + pageSize);
  }, [filteredItems, currentPage, pageSize]);

  return (
    <div>
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
        <>
          <PriceMatrixTable
            items={paginatedItems}
            onSelectProduct={onOpenProductDetail}
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
