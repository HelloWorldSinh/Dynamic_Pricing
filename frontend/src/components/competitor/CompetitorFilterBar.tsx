import React from 'react';
import { Search, Filter, ArrowUpDown, X, RotateCcw } from 'lucide-react';

interface CompetitorFilterBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  sourceFilter: string;
  setSourceFilter: (source: string) => void;
  categoryFilter?: string;
  setCategoryFilter?: (category: string) => void;
  stockFilter: string;
  setStockFilter: (status: string) => void;
  sortOrder: string;
  setSortOrder: (order: string) => void;
  totalFiltered: number;
  totalOriginal: number;
}

export const CompetitorFilterBar: React.FC<CompetitorFilterBarProps> = ({
  searchQuery,
  setSearchQuery,
  sourceFilter,
  setSourceFilter,
  categoryFilter = 'ALL',
  setCategoryFilter,
  stockFilter,
  setStockFilter,
  sortOrder,
  setSortOrder,
  totalFiltered,
  totalOriginal,
}) => {
  const isFilteringActive =
    searchQuery.trim() !== '' ||
    sourceFilter !== 'ALL' ||
    (categoryFilter && categoryFilter !== 'ALL') ||
    stockFilter !== 'ALL' ||
    sortOrder !== 'LATEST';

  const handleReset = () => {
    setSearchQuery('');
    setSourceFilter('ALL');
    if (setCategoryFilter) setCategoryFilter('ALL');
    setStockFilter('ALL');
    setSortOrder('LATEST');
  };

  return (
    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-4 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Search Box */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo tên sản phẩm, URL, từ khóa cấu hình..."
            className="w-full pl-9 pr-8 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              title="Xóa tìm kiếm"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Ngành hàng */}
          {setCategoryFilter && (
            <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] text-slate-400 ml-1">Ngành:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="text-xs bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none pr-1 py-1 font-medium cursor-pointer"
              >
                <option value="ALL">Mọi danh mục</option>
                <option value="PHONE">Điện thoại</option>
                <option value="LAPTOP">Laptop</option>
              </select>
            </div>
          )}

          {/* Nguồn đối thủ */}
          <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
            <Filter className="w-3.5 h-3.5 text-slate-400 ml-1" />
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="text-xs bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none pr-1 py-1 font-medium cursor-pointer"
            >
              <option value="ALL">Mọi nguồn đối thủ</option>
              <option value="CELLPHONES">CellphoneS</option>
              <option value="HOANGHA">Hoàng Hà Mobile</option>
            </select>
          </div>

          {/* Tình trạng kho */}
          <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
            <span className="text-[11px] text-slate-400 ml-1">Kho:</span>
            <select
              value={stockFilter}
              onChange={(e) => setStockFilter(e.target.value)}
              className="text-xs bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none pr-1 py-1 font-medium cursor-pointer"
            >
              <option value="ALL">Mọi trạng thái</option>
              <option value="IN_STOCK">Chỉ còn hàng</option>
              <option value="OUT_OF_STOCK">Tạm hết hàng</option>
            </select>
          </div>

          {/* Sắp xếp */}
          <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="text-xs bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none pr-1 py-1 font-medium cursor-pointer"
            >
              <option value="LATEST">Mới cào nhất</option>
              <option value="PRICE_ASC">Giá tăng dần</option>
              <option value="PRICE_DESC">Giá giảm dần</option>
              <option value="NAME_ASC">Tên sản phẩm (A-Z)</option>
            </select>
          </div>

          {/* Nút reset nếu có filter */}
          {isFilteringActive && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1 px-2.5 py-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 hover:bg-orange-50 dark:hover:bg-orange-950/30 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 transition"
              title="Đặt lại bộ lọc"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Xóa lọc</span>
            </button>
          )}

          {/* Counter Badge */}
          <div className="ml-auto pl-2 flex items-center text-xs text-slate-500 dark:text-slate-400">
            <span>Hiển thị </span>
            <span className="font-bold font-mono text-slate-900 dark:text-white px-1">
              {totalFiltered}
            </span>
            <span>/ {totalOriginal} bản ghi</span>
          </div>
        </div>
      </div>
    </div>
  );
};
