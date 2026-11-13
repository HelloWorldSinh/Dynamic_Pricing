import React from 'react';
import { PricingRecommendation } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';
import { useAiChat } from '../../context/AiChatContext';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';

interface RecommendationTableProps {
  items: PricingRecommendation[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onToggleSelectAll: () => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
  onOpenDetail: (item: PricingRecommendation) => void;
}

export const RecommendationTable: React.FC<RecommendationTableProps> = ({
  items,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onApprove,
  onReject,
  onOpenDetail,
}) => {
  const { askExplanationForSku } = useAiChat();

  if (items.length === 0) {
    return (
      <EmptyState
        title="Không có đề xuất giá"
        description="Không tìm thấy đề xuất giá nào phù hợp với bộ lọc hiện tại."
      />
    );
  }

  const allSelected = items.length > 0 && items.every((item) => selectedIds.includes(item.id));

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/90 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-semibold text-xs sticky top-0 z-10">
              <th className="py-3 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={onToggleSelectAll}
                  aria-label="Chọn toàn bộ sản phẩm trên trang"
                  className="rounded border-slate-300 text-orange-600 focus:ring-orange-500 w-3.5 h-3.5"
                />
              </th>
              <th className="py-3 px-4">Sản phẩm &amp; Tồn kho</th>
              <th className="py-3 px-3 text-right">Giá hiện tại</th>
              <th className="py-3 px-3 text-center">Đề xuất mới</th>
              <th className="py-3 px-3 text-center">Composite (D-I-C)</th>
              <th className="py-3 px-3 text-right">Giá sàn bảo vệ</th>
              <th className="py-3 px-3 text-center">Biên lợi nhuận</th>
              <th className="py-3 px-4 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
            {items.map((item) => {
              const isSelected = selectedIds.includes(item.id);
              const priceDrop = item.suggested_price < item.current_price;
              const priceDiff = item.suggested_price - item.current_price;
              const priceDiffPercent = item.current_price > 0 ? (priceDiff / item.current_price) * 100 : 0;

              return (
                <tr
                  key={item.id}
                  className={`transition-colors ${
                    isSelected
                      ? 'bg-orange-50/60 dark:bg-orange-950/20'
                      : 'even:bg-white dark:even:bg-slate-900 odd:bg-slate-50/50 dark:odd:bg-slate-800/30 hover:bg-orange-50/40 dark:hover:bg-slate-800/60'
                  }`}
                >
                  {/* Select Checkbox */}
                  <td className="py-3 px-3 text-center">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelect(item.id)}
                      aria-label={`Chọn sản phẩm ${item.product_name}`}
                      className="rounded border-slate-300 text-orange-600 focus:ring-orange-500 w-3.5 h-3.5"
                    />
                  </td>

                  {/* Product Info */}
                  <td className="py-3 px-4 max-w-[280px]">
                    <div className="font-semibold text-slate-900 dark:text-slate-100 truncate" title={item.product_name}>
                      {item.product_name}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-2xs font-mono text-slate-500 dark:text-slate-400">
                        {item.sku}
                      </span>
                      <span
                        className={`text-2xs font-medium ${
                          item.doh > 45 ? 'text-rose-600 dark:text-rose-400 font-semibold' : 'text-slate-400'
                        }`}
                      >
                        DOH: {item.doh}d (Tồn: {item.inventory_quantity})
                      </span>
                    </div>
                  </td>

                  {/* Current Price */}
                  <td className="py-3 px-3 text-right font-mono font-medium text-slate-600 dark:text-slate-400">
                    {formatCurrencyVND(item.current_price)}
                  </td>

                  {/* Suggested Price */}
                  <td className="py-3 px-3 text-center">
                    <div className="inline-flex flex-col items-center">
                      <div className="font-mono font-bold text-xs text-orange-600 dark:text-orange-400">
                        {formatCurrencyVND(item.suggested_price)}
                      </div>
                      <div className="flex items-center gap-1 mt-0.5">
                        <span className={`text-2xs font-mono font-bold ${priceDrop ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                          {priceDiff >= 0 ? `+${priceDiffPercent.toFixed(1)}%` : `${priceDiffPercent.toFixed(1)}%`}
                        </span>
                        {item.is_floor_protected && (
                          <Badge size="sm" variant="floor">
                            FLOOR CAP
                          </Badge>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Composite Score & DIC signals */}
                  <td className="py-3 px-3 text-center">
                    <div className="flex flex-col items-center gap-0.5">
                      <Badge
                        size="sm"
                        variant={
                          (item.composite_score ?? 0) >= 0.75
                            ? 'success'
                            : (item.composite_score ?? 0) <= -0.75
                            ? 'danger'
                            : (item.composite_score ?? 0) !== 0
                            ? 'warning'
                            : 'neutral'
                        }
                      >
                        {(item.composite_score ?? 0) > 0 ? `+${(item.composite_score ?? 0).toFixed(2)}` : (item.composite_score ?? 0).toFixed(2)}
                      </Badge>
                      <div className="flex items-center gap-1 text-2xs font-mono text-slate-400 dark:text-slate-500">
                        <span title="Demand Score">D:{(item.demand_score ?? 0) > 0 ? `+${item.demand_score}` : (item.demand_score ?? 0)}</span>
                        <span>|</span>
                        <span title="Inventory Score">I:{(item.inventory_score ?? 0) > 0 ? `+${item.inventory_score}` : (item.inventory_score ?? 0)}</span>
                        <span>|</span>
                        <span title="Competitor Score">C:{(item.competitor_score ?? 0) > 0 ? `+${item.competitor_score}` : (item.competitor_score ?? 0)}</span>
                      </div>
                    </div>
                  </td>

                  {/* Floor Price */}
                  <td className="py-3 px-3 text-right">
                    <div className="font-mono font-bold text-slate-700 dark:text-slate-300 text-xs">
                      {formatCurrencyVND(item.floor_price)}
                    </div>
                    <div className="text-2xs font-mono text-slate-400">
                      Vốn: {formatCurrencyVND(item.cost_price)}
                    </div>
                  </td>

                  {/* Margin Impact */}
                  <td className="py-3 px-3 text-center">
                    <Badge
                      size="sm"
                      variant={item.margin_impact_percent < 0 ? 'danger' : 'success'}
                    >
                      {formatPercent(item.margin_impact_percent)}
                    </Badge>
                  </td>

                  {/* Action Buttons */}
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => onOpenDetail(item)}
                      >
                        Chi tiết
                      </Button>

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => askExplanationForSku(item.sku, item.product_name)}
                      >
                        AI
                      </Button>

                      {item.status === 'PENDING' ? (
                        <>
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => onApprove(item.id)}
                          >
                            Duyệt
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            onClick={() => onReject(item.id)}
                          >
                            Từ chối
                          </Button>
                        </>
                      ) : (
                        <Badge
                          size="sm"
                          variant={item.status === 'APPROVED' ? 'success' : 'neutral'}
                        >
                          {item.status === 'APPROVED' ? 'ĐÃ DUYỆT' : 'ĐÃ TỪ CHỐI'}
                        </Badge>
                      )}
                    </div>
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
