import React from 'react';
import { Search, Filter, X } from 'lucide-react';

interface MatrixFilterToolbarProps {
  categoryFilter: string;
  setCategoryFilter: (category: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  priceGapFilter: string;
  setPriceGapFilter: (val: string) => void;
  dohRiskFilter: boolean;
  setDohRiskFilter: (val: boolean) => void;
  inStockOnlyFilter: boolean;
  setInStockOnlyFilter: (val: boolean) => void;
}

export const MatrixFilterToolbar: React.FC<MatrixFilterToolbarProps> = ({
  categoryFilter,
  setCategoryFilter,
  searchQuery,
  setSearchQuery,
  priceGapFilter,
  setPriceGapFilter,
  dohRiskFilter,
  setDohRiskFilter,
  inStockOnlyFilter,
  setInStockOnlyFilter,
}) => {
  return (
    <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-3.5 shadow-xs flex flex-wrap items-center gap-3">
      {/* 1. Category Segmented Control */}
      <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium shrink-0">
        <button
          type="button"
          onClick={() => setCategoryFilter('ALL')}
          className={`px-3 py-1.5 rounded-md transition ${
            categoryFilter === 'ALL'
              ? 'bg-white dark:bg-slate-900 text-orange-600 dark:text-orange-400 font-bold shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          Tất cả
        </button>
        <button
          type="button"
          onClick={() => setCategoryFilter('PHONE')}
          className={`px-3 py-1.5 rounded-md transition ${
            categoryFilter === 'PHONE'
              ? 'bg-white dark:bg-slate-900 text-orange-600 dark:text-orange-400 font-bold shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          Điện thoại
        </button>
        <button
          type="button"
          onClick={() => setCategoryFilter('LAPTOP')}
          className={`px-3 py-1.5 rounded-md transition ${
            categoryFilter === 'LAPTOP'
              ? 'bg-white dark:bg-slate-900 text-orange-600 dark:text-orange-400 font-bold shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
          }`}
        >
          Laptop
        </button>
      </div>

      <div className="h-5 w-px bg-slate-200 dark:border-slate-800 hidden sm:block" />

      {/* 2. Search Input */}
      <div className="relative flex-1 min-w-[220px] max-w-sm">
        <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Tìm theo tên sản phẩm, Part-Number hoặc SKU..."
          className="w-full pl-8 pr-7 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 transition"
        />
        {searchQuery && (
          <button
            type="button"
            onClick={() => setSearchQuery('')}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            <X className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Right Filters Group */}
      <div className="flex flex-wrap items-center gap-2.5 ml-auto">
        {/* 3. Price Gap Selector */}
        <div className="flex items-center gap-1.5 shrink-0">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={priceGapFilter}
            onChange={(e) => setPriceGapFilter(e.target.value)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500 font-medium"
          >
            <option value="ALL">Mọi chênh lệch giá</option>
            <option value="GAP_5">FPT đắt hơn ≥ 5% (Báo động)</option>
            <option value="GAP_2">FPT đắt hơn ≥ 2%</option>
            <option value="CHEAPER">FPT rẻ hơn đối thủ</option>
          </select>
        </div>

        {/* 4. DOH Risk Checkbox */}
        <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition shrink-0">
          <input
            type="checkbox"
            checked={dohRiskFilter}
            onChange={(e) => setDohRiskFilter(e.target.checked)}
            className="rounded border-slate-300 text-orange-600 focus:ring-orange-500 w-3.5 h-3.5"
          />
          <span>DOH &gt; 30 ngày</span>
        </label>

        {/* 5. In-Stock Only Checkbox */}
        <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition shrink-0">
          <input
            type="checkbox"
            checked={inStockOnlyFilter}
            onChange={(e) => setInStockOnlyFilter(e.target.checked)}
            className="rounded border-slate-300 text-orange-600 focus:ring-orange-500 w-3.5 h-3.5"
          />
          <span>Đối thủ còn hàng</span>
        </label>
      </div>
    </div>
  );
};
