import React from 'react';
import { Search, Filter, SlidersHorizontal } from 'lucide-react';

interface MatrixFilterToolbarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  priceGapFilter: string; // 'ALL' | 'GAP_5' | 'GAP_2' | 'CHEAPER'
  setPriceGapFilter: (val: string) => void;
  dohRiskFilter: boolean;
  setDohRiskFilter: (val: boolean) => void;
  inStockOnlyFilter: boolean;
  setInStockOnlyFilter: (val: boolean) => void;
  totalFiltered: number;
}

export const MatrixFilterToolbar: React.FC<MatrixFilterToolbarProps> = ({
  searchQuery,
  setSearchQuery,
  priceGapFilter,
  setPriceGapFilter,
  dohRiskFilter,
  setDohRiskFilter,
  inStockOnlyFilter,
  setInStockOnlyFilter,
  totalFiltered,
}) => {
  return (
    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
      {/* Search Input */}
      <div className="relative flex-1 max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Tìm theo tên sản phẩm, Part-Number hoặc SKU..."
          className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 transition"
        />
      </div>

      {/* Filter Options */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Price Gap Selector */}
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={priceGapFilter}
            onChange={(e) => setPriceGapFilter(e.target.value)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500"
          >
            <option value="ALL">Mọi mức chênh lệch giá</option>
            <option value="GAP_5">FPT đắt hơn ≥ 5% (Báo động đỏ)</option>
            <option value="GAP_2">FPT đắt hơn ≥ 2%</option>
            <option value="CHEAPER">FPT rẻ hơn đối thủ (Win state)</option>
          </select>
        </div>

        {/* DOH Risk Checkbox */}
        <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none bg-slate-50 dark:bg-slate-800 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition">
          <input
            type="checkbox"
            checked={dohRiskFilter}
            onChange={(e) => setDohRiskFilter(e.target.checked)}
            className="rounded border-slate-300 text-orange-600 focus:ring-orange-500"
          />
          <span>Tồn kho DOH &gt; 30 ngày</span>
        </label>

        {/* In-Stock Only Checkbox */}
        <label className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none bg-slate-50 dark:bg-slate-800 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition">
          <input
            type="checkbox"
            checked={inStockOnlyFilter}
            onChange={(e) => setInStockOnlyFilter(e.target.checked)}
            className="rounded border-slate-300 text-orange-600 focus:ring-orange-500"
          />
          <span>Đối thủ còn hàng</span>
        </label>

        {/* Filter count summary */}
        <div className="text-xs text-slate-500 flex items-center gap-1.5 pl-2 border-l border-slate-200 dark:border-slate-800">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400" />
          <span>{totalFiltered} kết quả</span>
        </div>
      </div>
    </div>
  );
};
