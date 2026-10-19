import React from 'react';
import { CheckCheck, Trash2 } from 'lucide-react';
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
}) => {
  const isAllSelected = queue.length > 0 && queue.every((item) => selectedBatchIds.has(item.id));
  const someSelected = selectedBatchIds.size > 0;

  return (
    <div className="flex flex-col h-full bg-slate-50/40 dark:bg-slate-900/40">
      {/* Top Header: Batch Select Bar */}
      <div className="p-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between text-xs">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={isAllSelected}
            onChange={(e) => onSelectAllBatch(e.target.checked)}
            className="w-3.5 h-3.5 rounded border-slate-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
          />
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            Chọn tất cả ({queue.length})
          </span>
        </label>

        <span className="text-[11px] font-mono text-slate-400">
          {queue.length}/{totalCount} SKU
        </span>
      </div>

      {/* Scrollable Queue Cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
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

      {/* Pinned Batch Action Bar if any items selected */}
      {someSelected && (
        <div className="p-3 border-t border-orange-200 dark:border-orange-900/60 bg-orange-50/95 dark:bg-orange-950/90 backdrop-blur-xs flex items-center justify-between gap-2 shadow-lg animate-in fade-in">
          <span className="text-xs font-semibold text-orange-900 dark:text-orange-200">
            Đã chọn {selectedBatchIds.size} SKU
          </span>

          <div className="flex items-center gap-1.5">
            <button
              onClick={onBatchReject}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition shadow-xs"
              title="Từ chối tất cả các mục đã chọn"
            >
              <Trash2 className="w-3 h-3" />
              <span>Từ chối</span>
            </button>
            <button
              onClick={onBatchApprove}
              className="flex items-center gap-1 px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-xs"
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
