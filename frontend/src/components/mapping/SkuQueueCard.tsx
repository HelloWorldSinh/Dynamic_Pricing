import React from 'react';
import { SkuMappingPair } from '../../types/matching';
import { Badge } from '../common/Badge';

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
  const getConfidenceVariant = (score: number) => {
    if (score >= 75) return 'info' as const;
    if (score >= 68) return 'warning' as const;
    return 'danger' as const;
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
        <div className="absolute left-0 top-3 bottom-3 w-1 bg-orange-600 rounded-r-full" />
      )}

      {/* Header: Checkbox, SKU & Source Badge */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <input
            type="checkbox"
            checked={isChecked}
            onChange={() => {}}
            onClick={(e) => onToggleCheck(pair.id, e)}
            aria-label={`Chọn cặp SKU ${pair.fpt_sku}`}
            className="w-3.5 h-3.5 rounded border-slate-300 text-orange-600 focus:ring-orange-500 cursor-pointer"
          />
          <span className="text-2xs font-mono font-bold text-slate-700 dark:text-slate-300 truncate">
            {pair.fpt_sku}
          </span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <Badge
            size="sm"
            variant={pair.competitor_source === 'CELLPHONES' ? 'danger' : 'success'}
          >
            {pair.competitor_source}
          </Badge>
          <Badge
            size="sm"
            variant={getConfidenceVariant(pair.confidence_score)}
          >
            {pair.confidence_score}%
          </Badge>
        </div>
      </div>

      {/* Product Name */}
      <h4 className="text-xs font-semibold text-slate-900 dark:text-slate-100 line-clamp-2 mb-1.5 leading-snug">
        {pair.fpt_name}
      </h4>

      {/* Part Number */}
      {pair.fpt_part_number && (
        <div className="text-2xs font-mono text-slate-500 dark:text-slate-400 mb-1.5 truncate">
          PN: <span className="font-semibold text-slate-700 dark:text-slate-300">{pair.fpt_part_number}</span>
        </div>
      )}

      {/* Mismatch Attribute Badge */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center">
        <span
          className={`text-2xs font-mono truncate ${
            pair.differing_attributes && pair.differing_attributes.length > 0
              ? 'text-rose-600 dark:text-rose-400 font-semibold'
              : 'text-slate-400'
          }`}
        >
          {mismatchText}
        </span>
      </div>
    </div>
  );
};
