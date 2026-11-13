import React from 'react';
import { SkuMappingPair } from '../../types/matching';
import { SkuQueueCard } from './SkuQueueCard';
import { Button } from '../common/Button';

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
            aria-label="Chọn toàn bộ SKU trong hàng đợi"
            className="w-3.5 h-3.5 rounded border-slate-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
          />
          <span className="font-semibold text-slate-700 dark:text-slate-300 text-2xs uppercase tracking-wider font-mono">
            CHỌN TẤT CẢ ({queue.length})
          </span>
        </label>

        <span className="text-2xs font-mono text-slate-400">
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
        <div className="p-3 border-t border-orange-200 dark:border-orange-900/60 bg-orange-50/95 dark:bg-orange-950/90 flex flex-wrap items-center justify-between gap-2 shadow-md">
          <span className="text-xs font-semibold text-orange-900 dark:text-orange-200">
            Đã chọn {selectedBatchIds.size} SKU
          </span>

          <div className="flex items-center gap-1.5">
            <Button
              size="sm"
              variant="destructive"
              onClick={onBatchReject}
            >
              Từ chối
            </Button>
            <Button
              size="sm"
              variant="primary"
              onClick={onBatchApprove}
            >
              Duyệt ({selectedBatchIds.size})
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
