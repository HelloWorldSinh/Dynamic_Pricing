import React, { useState, useEffect } from 'react';
import { RefreshCw, Database } from 'lucide-react';
import { CompetitorSummaryCards } from '../components/competitor/CompetitorSummaryCards';
import { CompetitorFilterBar } from '../components/competitor/CompetitorFilterBar';
import { CompetitorDataTable } from '../components/competitor/CompetitorDataTable';
import { CompetitorSpecsDrawer } from '../components/competitor/CompetitorSpecsDrawer';
import { Pagination } from '../components/common/Pagination';
import { CrawlResult } from '../types/crawl';
import { getCrawlResultsApi, getCrawlStatsApi, CrawlStats } from '../api/crawlerApi';

interface CompetitorFeedsPageProps {
  categoryFilter?: string;
}

export const CompetitorFeedsPage: React.FC<CompetitorFeedsPageProps> = ({
  categoryFilter: propCategoryFilter = 'ALL',
}) => {
  const [items, setItems] = useState<CrawlResult[]>([]);
  const [stats, setStats] = useState<CrawlStats | null>(null);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(true);

  // Bộ lọc
  const [categoryFilter, setCategoryFilter] = useState(propCategoryFilter);
  const [searchQuery, setSearchQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [stockFilter, setStockFilter] = useState('ALL');
  const [sortOrder, setSortOrder] = useState('LATEST');

  // Đồng bộ khi prop thay đổi từ Navbar
  useEffect(() => {
    setCategoryFilter(propCategoryFilter);
  }, [propCategoryFilter]);

  // Phân trang
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Drawer xem chi tiết
  const [selectedProduct, setSelectedProduct] = useState<CrawlResult | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const skip = (currentPage - 1) * pageSize;
      const [res, statsRes] = await Promise.all([
        getCrawlResultsApi(
          sourceFilter,
          categoryFilter,
          searchQuery,
          stockFilter,
          sortOrder,
          skip,
          pageSize
        ),
        getCrawlStatsApi(categoryFilter)
      ]);
      setItems(res.items);
      setTotalItems(res.total);
      setStats(statsRes);
    } catch (error) {
      console.error('Lỗi tải dữ liệu cào đối thủ:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [categoryFilter, searchQuery, sourceFilter, stockFilter, sortOrder, currentPage, pageSize]);

  // Reset về trang 1 khi thay đổi bất kỳ bộ lọc nào
  useEffect(() => {
    setCurrentPage(1);
  }, [categoryFilter, searchQuery, sourceFilter, stockFilter, sortOrder]);

  const totalPages = Math.ceil(totalItems / pageSize) || 1;
  const paginatedItems = items;

  return (
    <div>
      {/* Tiêu đề trang & Nút hành động */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h1 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            <span>Dữ liệu Cào từ Đối thủ (Competitor Feeds)</span>
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Theo dõi, tra cứu giá bán thực tế và thông số kỹ thuật bóc tách từ CellphoneS và Hoàng Hà Mobile.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 shadow-sm transition disabled:opacity-50"
            title="Tải lại dữ liệu mới nhất"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-orange-600' : 'text-slate-400'}`} />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* 4 Thẻ KPI Tổng quan */}
      <CompetitorSummaryCards stats={stats} />

      {/* Thanh Công cụ Lọc & Tìm kiếm */}
      <CompetitorFilterBar
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        sourceFilter={sourceFilter}
        setSourceFilter={setSourceFilter}
        categoryFilter={categoryFilter}
        setCategoryFilter={setCategoryFilter}
        stockFilter={stockFilter}
        setStockFilter={setStockFilter}
        sortOrder={sortOrder}
        setSortOrder={setSortOrder}
        totalFiltered={totalItems}
        totalOriginal={stats?.total || 0}
      />

      {/* Bảng Dữ liệu Đối thủ */}
      {loading ? (
        <div className="p-16 text-center text-slate-400 dark:text-slate-500 text-xs rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <RefreshCw className="w-6 h-6 animate-spin text-orange-500 mx-auto mb-2" />
          <span>Đang nạp nguồn cấp dữ liệu cào từ đối thủ...</span>
        </div>
      ) : (
        <>
          <CompetitorDataTable
            items={paginatedItems}
            onSelectProduct={(item) => setSelectedProduct(item)}
            onResetFilter={() => {
              setSearchQuery('');
              setSourceFilter('ALL');
              setStockFilter('ALL');
              setSortOrder('LATEST');
            }}
          />

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={totalItems}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={(newSize) => {
              setPageSize(newSize);
              setCurrentPage(1);
            }}
            itemLabel="sản phẩm đối thủ"
          />
        </>
      )}

      {/* Drawer Chi tiết Cấu hình & Raw JSON */}
      <CompetitorSpecsDrawer
        item={selectedProduct}
        onClose={() => setSelectedProduct(null)}
      />
    </div>
  );
};
export default CompetitorFeedsPage;
