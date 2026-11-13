import React from 'react';
import { Button } from '../common/Button';

interface BatchActionBarProps {
  selectedCount: number;
  onBatchApprove: () => void;
  onBatchReject: () => void;
  onClearSelection: () => void;
}

export const BatchActionBar: React.FC<BatchActionBarProps> = ({
  selectedCount,
  onBatchApprove,
  onBatchReject,
  onClearSelection,
}) => {
  if (selectedCount === 0) return null;

  return (
    <div className="bg-slate-900 text-white dark:bg-slate-800 p-3 px-4 rounded-xl mb-4 flex flex-wrap items-center justify-between gap-3 shadow-md border border-slate-700 animate-in fade-in slide-in-from-top-2 duration-150">
      <div className="flex items-center gap-2.5 text-xs">
        <span className="text-xs font-bold text-orange-400">
          Thao tác hàng loạt:
        </span>
        <span>
          Đã chọn <strong className="font-mono font-bold text-orange-300">{selectedCount}</strong> sản phẩm
        </span>
        <button
          type="button"
          onClick={onClearSelection}
          className="text-slate-400 hover:text-white underline text-xs ml-2 transition"
        >
          Bỏ chọn
        </button>
      </div>

      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="destructive"
          onClick={onBatchReject}
        >
          Từ chối ({selectedCount})
        </Button>
        <Button
          size="sm"
          variant="primary"
          onClick={onBatchApprove}
        >
          Phê duyệt ({selectedCount})
        </Button>
      </div>
    </div>
  );
};
