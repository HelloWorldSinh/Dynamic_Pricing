import React from 'react';
import { ExternalLink } from 'lucide-react';
import { PriceComparisonItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';

interface PriceMatrixTableProps {
  items: PriceComparisonItem[];
  onExplainProduct?: (item: PriceComparisonItem) => void;
  onResetFilters?: () => void;
}

export const PriceMatrixTable: React.FC<PriceMatrixTableProps> = ({
  items,
  onResetFilters,
}) => {
  if (items.length === 0) {
    return (
      <EmptyState
        title="Không tìm thấy sản phẩm nào"
        description="Không có sản phẩm nào phù hợp với bộ lọc hoặc từ khóa tìm kiếm hiện tại."
        resetLabel={onResetFilters ? 'Đặt lại bộ lọc' : undefined}
        onReset={onResetFilters}
      />
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/90 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-semibold text-xs sticky top-0 z-10">
              <th className="py-3 px-4">Sản phẩm FPT</th>
              <th className="py-3 px-3 text-right">Giá FPT Shop</th>
              <th className="py-3 px-3 text-right">CellphoneS</th>
              <th className="py-3 px-3 text-right">Hoàng Hà</th>
              <th className="py-3 px-3 text-center">Chênh lệch giá</th>
              <th className="py-3 px-3 text-center">Độ tin cậy</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
            {items.map((item) => {
              const isExpensive = item.price_diff > 0;
              const isDanger = item.price_diff_percent >= 5;
              const isCheaper = item.price_diff < 0;
              const isEqual = item.price_diff === 0;

              return (
                <tr
                  key={item.id}
                  className="even:bg-white dark:even:bg-slate-900 odd:bg-slate-50/50 dark:odd:bg-slate-800/30 hover:bg-orange-50/60 dark:hover:bg-slate-800/70 transition-colors duration-100"
                >
                  {/* Product Info */}
                  <td className="py-3 px-4 max-w-[340px]">
                    <div className="font-semibold text-slate-900 dark:text-slate-100 truncate" title={item.name}>
                      {item.name}
                    </div>
                    <div className="mt-1 flex items-center gap-2">
                      <span className="text-2xs font-mono text-slate-500 dark:text-slate-400">
                        {item.sku}
                      </span>
                      {item.part_number && (
                        <span className="text-2xs font-mono text-slate-400 dark:text-slate-500">
                          PN: {item.part_number}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* FPT Price */}
                  <td className="py-3 px-3 text-right font-bold text-slate-900 dark:text-white text-xs font-mono">
                    {formatCurrencyVND(item.fpt_price)}
                  </td>

                  {/* CellphoneS Price */}
                  <td className="py-3 px-3 text-right">
                    {item.cellphones ? (
                      <div className="flex flex-col items-end">
                        <span className="font-semibold font-mono text-slate-800 dark:text-slate-200">
                          {formatCurrencyVND(item.cellphones.price)}
                        </span>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <Badge
                            size="sm"
                            variant={item.cellphones.is_in_stock ? 'success' : 'neutral'}
                          >
                            {item.cellphones.is_in_stock ? 'Còn hàng' : 'Hết hàng'}
                          </Badge>
                          <a
                            href={item.cellphones.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors p-0.5 rounded"
                            title="Mở liên kết CellphoneS"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-400 text-xs font-mono">—</span>
                    )}
                  </td>

                  {/* Hoàng Hà Price */}
                  <td className="py-3 px-3 text-right">
                    {item.hoangha ? (
                      <div className="flex flex-col items-end">
                        <span className="font-semibold font-mono text-slate-800 dark:text-slate-200">
                          {formatCurrencyVND(item.hoangha.price)}
                        </span>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <Badge
                            size="sm"
                            variant={item.hoangha.is_in_stock ? 'success' : 'neutral'}
                          >
                            {item.hoangha.is_in_stock ? 'Còn hàng' : 'Hết hàng'}
                          </Badge>
                          <a
                            href={item.hoangha.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 transition-colors p-0.5 rounded"
                            title="Mở liên kết Hoàng Hà"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-400 text-xs font-mono">—</span>
                    )}
                  </td>

                  {/* Price Gap Diff */}
                  <td className="py-3 px-3 text-center">
                    <div className="inline-flex flex-col items-center">
                      <Badge
                        size="sm"
                        variant={
                          isDanger ? 'danger' : isExpensive ? 'warning' : isCheaper ? 'success' : 'info'
                        }
                      >
                        {isEqual ? '0%' : formatPercent(item.price_diff_percent)}
                      </Badge>
                      <span className="text-2xs text-slate-400 dark:text-slate-500 mt-0.5 font-medium">
                        {isEqual ? 'Bằng giá' : formatCurrencyVND(Math.abs(item.price_diff))}
                      </span>
                    </div>
                  </td>

                  {/* Confidence Badge */}
                  <td className="py-3 px-3 text-center">
                    <Badge
                      size="sm"
                      variant={
                        item.confidence_score === 100
                          ? 'success'
                          : item.confidence_score >= 80
                          ? 'info'
                          : 'warning'
                      }
                    >
                      {item.confidence_score}%
                    </Badge>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
