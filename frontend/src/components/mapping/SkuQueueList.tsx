import React from 'react';
import { Search, X, CheckCheck, Trash2, Filter } from 'lucide-react';
import { SkuMappingPair } from '../../types/matching';
import { SkuQueueCard } from './SkuQueueCard';

interface SkuQueueListProps {
  queue: SkuMappingPair[];
  totalCount: number;
  selectedId: string | null;
  onSelect: (id: string) => void;
  selectedBatchIds: Set<string>;
  onToggleBatch: (id: string) => void;
  onSelectAllBatch: (selectAll: boolean) => void;
  onBatchApprove: () => void;
  onBatchReject: () => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  sourceFilter: 'ALL' | 'CELLPHONES' | 'HOANGHA';
  onSourceFilterChange: (src: 'ALL' | 'CELLPHONES' | 'HOANGHA') => void;
  confidenceFilter: 'ALL' | 'HIGH' | 'MID';
  onConfidenceFilterChange: (conf: 'ALL' | 'HIGH' | 'MID') => void;
}

export const SkuQueueList: React.FC<SkuQueueListProps> = ({
  queue,
  totalCount,
  selectedId,
  onSelect,
  selectedBatchIds,
  onToggleBatch,
  onSelectAllBatch,
  onBatchApprove,
  onBatchReject,
  searchQuery,
  onSearchChange,
  sourceFilter,
  onSourceFilterChange,
  confidenceFilter,
  onConfidenceFilterChange,
}) => {
  const isAllSelected = queue.length > 0 && queue.every((item) => selectedBatchIds.has(item.id));
  const someSelected = selectedBatchIds.size > 0;

  return (
    <div className="flex flex-col h-full bg-slate-50/50 dark:bg-slate-900/50">
      {/* Top Controls Header */}
      <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 space-y-2.5 bg-white dark:bg-slate-900">
        {/* Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Tìm theo SKU, tên sản phẩm..."
            className="w-full pl-9 pr-8 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
          <span className="text-slate-400 flex items-center gap-1 mr-1">
            <Filter className="w-3 h-3" />
          </span>

          {/* Source filters */}
          <button
            onClick={() => onSourceFilterChange('ALL')}
            className={`px-2 py-0.5 rounded-md font-medium transition ${
              sourceFilter === 'ALL'
                ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-semibold'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
            }`}
          >
            Tất cả
          </button>
          <button
            onClick={() => onSourceFilterChange('CELLPHONES')}
            className={`px-2 py-0.5 rounded-md font-medium transition ${
              sourceFilter === 'CELLPHONES'
                ? 'bg-red-600 text-white font-semibold'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
            }`}
          >
            CellphoneS
          </button>
          <button
            onClick={() => onSourceFilterChange('HOANGHA')}
            className={`px-2 py-0.5 rounded-md font-medium transition ${
              sourceFilter === 'HOANGHA'
                ? 'bg-emerald-600 text-white font-semibold'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
            }`}
          >
            Hoàng Hà
          </button>

          <span className="text-slate-300 dark:text-slate-700">|</span>

          {/* Confidence filters */}
          <button
            onClick={() => onConfidenceFilterChange(confidenceFilter === 'HIGH' ? 'ALL' : 'HIGH')}
            className={`px-2 py-0.5 rounded-md font-medium transition ${
              confidenceFilter === 'HIGH'
                ? 'bg-blue-600 text-white font-semibold'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
            }`}
            title="Độ tin cậy ≥ 75%"
          >
            ≥75%
          </button>
          <button
            onClick={() => onConfidenceFilterChange(confidenceFilter === 'MID' ? 'ALL' : 'MID')}
            className={`px-2 py-0.5 rounded-md font-medium transition ${
              confidenceFilter === 'MID'
                ? 'bg-amber-600 text-white font-semibold'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200'
            }`}
            title="Độ tin cậy < 75%"
          >
            &lt;75%
          </button>
        </div>

        {/* Batch Selection Row */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-500">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={isAllSelected}
              onChange={(e) => onSelectAllBatch(e.target.checked)}
              className="w-3.5 h-3.5 rounded border-slate-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
            />
            <span className="font-medium text-slate-700 dark:text-slate-300">
              Chọn tất cả ({queue.length})
            </span>
          </label>

          <span className="text-[10px] font-mono text-slate-400">
            Hiện {queue.length}/{totalCount} mục
          </span>
        </div>
      </div>

      {/* Scrollable Queue Cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {queue.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">
            Không tìm thấy cặp SKU nào phù hợp với bộ lọc.
          </div>
        ) : (
          queue.map((pair) => (
            <SkuQueueCard
              key={pair.id}
              pair={pair}
              isSelected={selectedId === pair.id}
              isChecked={selectedBatchIds.has(pair.id)}
              onSelect={onSelect}
              onToggleCheck={(id, e) => {
                e.stopPropagation();
                onToggleBatch(id);
              }}
            />
          ))
        )}
      </div>

      {/* Floating/Sticky Batch Action Bar */}
      {someSelected && (
        <div className="p-3 border-t border-orange-200 dark:border-orange-900/60 bg-orange-50/90 dark:bg-orange-950/80 backdrop-blur-sm flex items-center justify-between gap-2 shadow-lg animate-in fade-in slide-in-from-bottom-2">
          <span className="text-xs font-semibold text-orange-900 dark:text-orange-200">
            Đã chọn {selectedBatchIds.size} SKU
          </span>

          <div className="flex items-center gap-1.5">
            <button
              onClick={onBatchReject}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition shadow-sm"
              title="Từ chối tất cả các mục đã chọn"
            >
              <Trash2 className="w-3 h-3" />
              <span>Từ chối</span>
            </button>
            <button
              onClick={onBatchApprove}
              className="flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition shadow-sm"
              title="Xác nhận khớp 100% tất cả các mục đã chọn"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>Duyệt ({selectedBatchIds.size})</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
