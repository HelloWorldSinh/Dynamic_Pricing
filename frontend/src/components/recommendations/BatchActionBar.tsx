import React from 'react';
import { Check, X, Layers } from 'lucide-react';

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
    <div className="bg-slate-900 text-white dark:bg-slate-800 p-3 px-4 rounded-xl mb-4 flex items-center justify-between shadow-lg shadow-slate-950/20 border border-slate-700 animate-in fade-in slide-in-from-top-2 duration-200">
      <div className="flex items-center gap-2 text-xs">
        <Layers className="w-4 h-4 text-orange-400" />
        <span>Đã chọn <strong className="font-bold text-orange-400">{selectedCount}</strong> sản phẩm</span>
        <button
          onClick={onClearSelection}
          className="text-slate-400 hover:text-white underline text-[11px] ml-2"
        >
          Bỏ chọn
        </button>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onBatchReject}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 text-xs font-semibold transition"
        >
          <X className="w-3.5 h-3.5" />
          <span>Bác bỏ ({selectedCount})</span>
        </button>
        <button
          onClick={onBatchApprove}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition shadow-sm"
        >
          <Check className="w-3.5 h-3.5" />
          <span>Duyệt toàn bộ ({selectedCount})</span>
        </button>
      </div>
    </div>
  );
};
