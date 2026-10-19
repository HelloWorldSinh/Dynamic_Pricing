import React from 'react';
import { SkuMappingPair } from '../../types/matching';

interface SkuQueueCardProps {
  pair: SkuMappingPair;
  isSelected: boolean;
  isChecked: boolean;
  onSelect: (id: string) => void;
  onToggleCheck: (id: string, e: React.MouseEvent) => void;
}

export const SkuQueueCard: React.FC<SkuQueueCardProps> = ({
  pair,
  isSelected,
  isChecked,
  onSelect,
  onToggleCheck,
}) => {
  const getConfidenceBadgeColor = (score: number) => {
    if (score >= 75) {
      return 'bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800';
    }
    if (score >= 68) {
      return 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800';
    }
    return 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800';
  };

  const getSourceBadgeColor = (source: string) => {
    if (source === 'CELLPHONES') {
      return 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border-red-200 dark:border-red-900/60';
    }
    return 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900/60';
  };

  const mismatchText = pair.differing_attributes && pair.differing_attributes.length > 0
    ? `Lệch: ${pair.differing_attributes.join(', ')}`
    : 'Chờ duyệt đối soát';

  return (
    <div
      onClick={() => onSelect(pair.id)}
      className={`group relative rounded-xl p-3 transition-all cursor-pointer border ${
        isSelected
          ? 'bg-orange-50/70 dark:bg-orange-950/20 border-orange-500 dark:border-orange-500 shadow-xs ring-1 ring-orange-500/30'
          : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-xs'
      }`}
    >
      {/* Active Indicator Bar */}
      {isSelected && (
        <div className="absolute left-0 top-3 bottom-3 w-1 bg-orange-500 rounded-r-full" />
      )}

      {/* Header: Checkbox, SKU & Source Badge */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={() => {}}
            onClick={(e) => onToggleCheck(pair.id, e)}
            className="w-3.5 h-3.5 rounded border-slate-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
          />
          <span className="text-[11px] font-mono font-bold text-slate-700 dark:text-slate-300 truncate">
            {pair.fpt_sku}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <span
            className={`text-[9px] font-bold px-1.5 py-0.2 rounded border uppercase tracking-wider ${getSourceBadgeColor(
              pair.competitor_source
            )}`}
          >
            {pair.competitor_source}
          </span>
          <span
            className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded border ${getConfidenceBadgeColor(
              pair.confidence_score
            )}`}
          >
            {pair.confidence_score}%
          </span>
        </div>
      </div>

      {/* Product Name */}
      <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 line-clamp-2 mb-1.5 leading-snug">
        {pair.fpt_name}
      </h4>

      {/* Part Number / Model info if available */}
      {pair.fpt_part_number && (
        <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 mb-1.5 truncate">
          Part: <span className="font-semibold text-slate-700 dark:text-slate-300">{pair.fpt_part_number}</span>
        </div>
      )}

      {/* Readable Mismatch Tag Badge */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center">
        <span
          className={`text-[10px] px-2 py-0.5 rounded-md font-medium truncate max-w-full ${
            pair.differing_attributes && pair.differing_attributes.length > 0
              ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200/80 dark:border-amber-800/80 font-bold'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
          }`}
          title={mismatchText}
        >
          {mismatchText}
        </span>
      </div>
    </div>
  );
};
