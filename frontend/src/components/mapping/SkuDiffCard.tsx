import React from 'react';
import { Check, X, ExternalLink, GitCompare } from 'lucide-react';
import { SkuMappingPair } from '../../types/matching';
import { ConfidenceMeter } from './ConfidenceMeter';
import { formatCurrencyVND } from '../../utils/formatters';

interface SkuDiffCardProps {
  pair: SkuMappingPair;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export const SkuDiffCard: React.FC<SkuDiffCardProps> = ({
  pair,
  onApprove,
  onReject,
}) => {
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 shadow-sm mb-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-3">
        <div className="flex items-center gap-2">
          <span className="p-1.5 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
            <GitCompare className="w-4 h-4" />
          </span>
          <div>
            <span className="text-xs font-bold text-slate-900 dark:text-white">
              Cặp đối soát SKU: {pair.fpt_sku}
            </span>
            <span className="text-[11px] text-slate-500 ml-2">
              Đối thủ: <strong className="font-semibold text-slate-700 dark:text-slate-300">{pair.competitor_source}</strong>
            </span>
          </div>
        </div>

        {/* Confidence Gauge */}
        <div className="flex items-center gap-4">
          <ConfidenceMeter score={pair.confidence_score} />
          
          <div className="flex items-center gap-2 border-l border-slate-200 dark:border-slate-800 pl-4">
            <button
              onClick={() => onReject(pair.id)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-600 dark:text-slate-300 hover:text-rose-600 text-xs font-medium transition"
            >
              <X className="w-3.5 h-3.5" />
              <span>Từ chối</span>
            </button>
            <button
              onClick={() => onApprove(pair.id)}
              className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition shadow-sm"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Xác nhận khớp (100%)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Side-by-Side 2-Column Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        {/* Left Column: FPT Shop (Baseline) */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-800/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-600 text-white uppercase tracking-wider">
              FPT Shop (Chuẩn)
            </span>
            <span className="text-xs font-mono font-bold text-slate-900 dark:text-white">
              {formatCurrencyVND(pair.fpt_price)}
            </span>
          </div>

          <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 min-h-[36px] line-clamp-2">
            {pair.fpt_name}
          </h4>

          {pair.fpt_part_number && (
            <div className="text-[11px] font-mono text-orange-600 dark:text-orange-400 font-semibold mt-1">
              Mã Part: {pair.fpt_part_number}
            </div>
          )}

          {/* Specs List */}
          {pair.fpt_specs && (
            <div className="mt-3 space-y-1 text-xs border-t border-slate-200/60 dark:border-slate-700/60 pt-2.5">
              {Object.entries(pair.fpt_specs).map(([key, val]) => (
                <div key={key} className="flex justify-between text-[11px]">
                  <span className="text-slate-500">{key}:</span>
                  <span className="text-slate-800 dark:text-slate-200 font-medium">{val}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Competitor (Scraped) */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-800/30">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-700 text-white uppercase tracking-wider">
              {pair.competitor_source}
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-mono font-bold text-slate-900 dark:text-white">
                {formatCurrencyVND(pair.competitor_price)}
              </span>
              <a
                href={pair.competitor_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                title="Mở URL gốc kiểm tra chéo"
              >
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 min-h-[36px] line-clamp-2">
            {pair.competitor_name}
          </h4>

          {pair.competitor_part_number && (
            <div className="text-[11px] font-mono text-slate-500 font-semibold mt-1">
              Mã Part: {pair.competitor_part_number}
            </div>
          )}

          {/* Specs List */}
          {pair.competitor_specs && (
            <div className="mt-3 space-y-1 text-xs border-t border-slate-200/60 dark:border-slate-700/60 pt-2.5">
              {Object.entries(pair.competitor_specs).map(([key, val]) => (
                <div key={key} className="flex justify-between text-[11px]">
                  <span className="text-slate-500">{key}:</span>
                  <span className="text-slate-800 dark:text-slate-200 font-medium">{val}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Matching & Differing Highlights */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center gap-3 text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-semibold text-slate-400">Trùng khớp:</span>
          {pair.matched_attributes.map((attr, idx) => (
            <span
              key={idx}
              className="px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 text-[10px] font-medium border border-emerald-200 dark:border-emerald-800"
            >
              {attr}
            </span>
          ))}
        </div>

        {pair.differing_attributes.length > 0 && (
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold text-slate-400">Khác biệt:</span>
            {pair.differing_attributes.map((diff, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 text-[10px] font-medium border border-amber-200 dark:border-amber-800"
              >
                {diff}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
