import React from 'react';
import { Check, X, ExternalLink, CheckCircle2 } from 'lucide-react';
import { SkuMappingPair } from '../../types/matching';
import { SkuSpecMatrix } from './SkuSpecMatrix';
import { ConfidenceMeter } from './ConfidenceMeter';

interface SkuDetailInspectorProps {
  pair: SkuMappingPair | null;
  currentIndex: number;
  totalInQueue: number;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export const SkuDetailInspector: React.FC<SkuDetailInspectorProps> = ({
  pair,
  currentIndex,
  totalInQueue,
  onApprove,
  onReject,
}) => {
  if (!pair) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
        <CheckCircle2 className="w-12 h-12 text-emerald-500 mb-3" />
        <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
          Hàng đợi đối soát trống!
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Toàn bộ SKU trong danh sách đều đã được xử lý xong hoặc tự động đối soát chính xác 100%.
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-5 space-y-5 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
      {/* Sticky Action Header */}
      <div className="sticky -top-5 z-10 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md pb-4 pt-1 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/40 px-2 py-0.5 rounded border border-orange-200 dark:border-orange-800">
              SKU: {pair.fpt_sku}
            </span>
            <span className="text-[11px] text-slate-400 font-medium">
              #{currentIndex + 1} / {totalInQueue} trong hàng đợi
            </span>
          </div>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white mt-1 line-clamp-1">
            {pair.fpt_name}
          </h2>
        </div>

        {/* Action Buttons & Confidence */}
        <div className="flex items-center gap-4 shrink-0">
          <ConfidenceMeter score={pair.confidence_score} />

          <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-4">
            <button
              onClick={() => onReject(pair.id)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 hover:border-rose-200 dark:border-rose-800 text-xs font-semibold transition group shadow-sm"
            >
              <X className="w-4 h-4 text-slate-400 group-hover:text-rose-600" />
              <span>Từ chối</span>
            </button>

            <button
              onClick={() => onApprove(pair.id)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-sm hover:shadow"
            >
              <Check className="w-4 h-4 stroke-[2.5]" />
              <span>Khớp 100%</span>
            </button>
          </div>
        </div>
      </div>

      {/* Hero Comparison Side-by-Side Cards (Focused on Product Identity & Specs) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left Card: FPT Shop (Chuẩn) */}
        <div className="p-4 rounded-xl border border-orange-200 dark:border-orange-900/60 bg-orange-50/30 dark:bg-orange-950/10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-600 text-white uppercase tracking-wider">
              FPT Shop (Chuẩn)
            </span>
            <span className="text-xs font-mono text-slate-500 dark:text-slate-400">
              Mã: {pair.fpt_sku}
            </span>
          </div>

          <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100 min-h-[36px] line-clamp-2">
            {pair.fpt_name}
          </h3>

          <div className="mt-2 pt-2 border-t border-orange-100 dark:border-orange-900/40 flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">Mã Part / Model:</span>
            <span className="font-mono font-bold text-orange-600 dark:text-orange-400 text-[11px]">
              {pair.fpt_part_number || 'Chưa cập nhật'}
            </span>
          </div>
        </div>

        {/* Right Card: Competitor (Crawled) */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20">
          <div className="flex items-center justify-between mb-2">
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded text-white uppercase tracking-wider ${
                pair.competitor_source === 'CELLPHONES' ? 'bg-red-600' : 'bg-emerald-600'
              }`}
            >
              {pair.competitor_source}
            </span>

            {pair.competitor_url && (
              <a
                href={pair.competitor_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-[11px] text-blue-600 dark:text-blue-400 hover:underline transition"
                title="Mở website đối thủ để kiểm tra chéo"
              >
                <span>Xem web gốc</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          <h3 className="text-xs font-semibold text-slate-900 dark:text-slate-100 min-h-[36px] line-clamp-2">
            {pair.competitor_name}
          </h3>

          <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-500 text-[11px]">Mã Part / Model:</span>
            <span className="font-mono font-bold text-slate-700 dark:text-slate-300 text-[11px]">
              {pair.competitor_part_number || 'Chưa cập nhật'}
            </span>
          </div>
        </div>
      </div>

      {/* Aligned Spec Matrix */}
      <SkuSpecMatrix pair={pair} />
    </div>
  );
};
