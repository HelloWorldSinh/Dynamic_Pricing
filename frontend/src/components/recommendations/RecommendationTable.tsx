import React from 'react';
import { ShieldCheck, Check, X, TrendingDown, Eye } from 'lucide-react';
import { PricingRecommendation } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

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
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
        <p className="text-xs text-slate-500">Không có đề xuất giá nào trong danh mục này.</p>
      </div>
    );
  }

  const allSelected = items.length > 0 && items.every((item) => selectedIds.includes(item.id));

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-3 w-10 text-center">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={onToggleSelectAll}
                  className="rounded border-slate-300 text-orange-600 focus:ring-orange-500"
                />
              </th>
              <th className="py-3 px-4">Sản phẩm &amp; Tồn kho</th>
              <th className="py-3 px-3 text-right">Giá hiện tại</th>
              <th className="py-3 px-3 text-center">Đề xuất mới</th>
              <th className="py-3 px-3 text-center">Composite &amp; D-I-C</th>
              <th className="py-3 px-3 text-right">Giá sàn bảo vệ</th>
              <th className="py-3 px-3 text-center">Biên lợi nhuận</th>
              <th className="py-3 px-4 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {items.map((item) => {
              const isSelected = selectedIds.includes(item.id);
              const priceDrop = item.suggested_price < item.current_price;

              return (
                <tr
                  key={item.id}
                  className={`transition-colors ${
                    isSelected
                      ? 'bg-orange-50/40 dark:bg-orange-950/20'
                      : 'hover:bg-slate-50/60 dark:hover:bg-slate-800/40'
                  }`}
                >
                  {/* Select Checkbox */}
                  <td className="py-3 px-3 text-center">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelect(item.id)}
                      className="rounded border-slate-300 text-orange-600 focus:ring-orange-500"
                    />
                  </td>

                  {/* Product Info */}
                  <td className="py-3 px-4 max-w-[280px]">
                    <div className="font-semibold text-slate-900 dark:text-slate-100 truncate" title={item.product_name}>
                      {item.product_name}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                        {item.sku}
                      </span>
                      <span
                        className={`text-[10px] font-semibold ${
                          item.doh > 45 ? 'text-rose-500' : 'text-slate-400'
                        }`}
                      >
                        DOH: {item.doh} ngày (Tồn: {item.inventory_quantity})
                      </span>
                    </div>
                  </td>

                  {/* Current Price */}
                  <td className="py-3 px-3 text-right font-mono font-medium text-slate-600 dark:text-slate-400">
                    {formatCurrencyVND(item.current_price)}
                  </td>

                  {/* Suggested Price */}
                  <td className="py-3 px-3 text-center">
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-800 text-orange-700 dark:text-orange-300 font-bold font-mono">
                      {priceDrop && <TrendingDown className="w-3 h-3 text-rose-500" />}
                      <span>{formatCurrencyVND(item.suggested_price)}</span>
                    </div>
                    {item.is_floor_protected && (
                      <div className="mt-1 flex items-center justify-center gap-1 text-[10px] text-pink-600 dark:text-pink-400 font-semibold">
                        <ShieldCheck className="w-3 h-3" />
                        <span>Floor Cap</span>
                      </div>
                    )}
                  </td>

                  {/* Composite Score & DIC signals */}
                  <td className="py-3 px-3 text-center">
                    <div className="flex flex-col items-center gap-1">
                      <span
                        className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border ${
                          (item.composite_score ?? 0) >= 0.75
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                            : (item.composite_score ?? 0) <= -0.75
                            ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-800'
                            : (item.composite_score ?? 0) !== 0
                            ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700'
                        }`}
                      >
                        Score: {(item.composite_score ?? 0) > 0 ? `+${(item.composite_score ?? 0).toFixed(2)}` : (item.composite_score ?? 0).toFixed(2)}
                      </span>
                      <div className="flex items-center gap-1 text-[10px] font-mono text-slate-500 dark:text-slate-400">
                        <span title="Demand Score (Nhu cầu)">D:{(item.demand_score ?? 0) > 0 ? `+${item.demand_score}` : (item.demand_score ?? 0)}</span>
                        <span>•</span>
                        <span title="Inventory Score (Tồn kho)">I:{(item.inventory_score ?? 0) > 0 ? `+${item.inventory_score}` : (item.inventory_score ?? 0)}</span>
                        <span>•</span>
                        <span title="Competitor Score (Đối thủ)">C:{(item.competitor_score ?? 0) > 0 ? `+${item.competitor_score}` : (item.competitor_score ?? 0)}</span>
                      </div>
                    </div>
                  </td>

                  {/* Floor Price */}
                  <td className="py-3 px-3 text-right">
                    <div className="font-mono text-slate-700 dark:text-slate-300">
                      {formatCurrencyVND(item.floor_price)}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      Vốn: {formatCurrencyVND(item.cost_price)}
                    </div>
                  </td>

                  {/* Margin Impact */}
                  <td className="py-3 px-3 text-center">
                    <span
                      className={`inline-block text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                        item.margin_impact_percent < 0
                          ? 'bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400'
                          : 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400'
                      }`}
                    >
                      {formatPercent(item.margin_impact_percent)}
                    </span>
                  </td>

                  {/* Action Buttons */}
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      <button
                        onClick={() => onOpenDetail(item)}
                        className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition font-medium flex items-center gap-1 shadow-sm text-[11px]"
                        title="Xem chi tiết căn cứ và biểu đồ giá 3 shop"
                      >
                        <Eye className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
                        <span>Detail</span>
                      </button>

                      {item.status === 'PENDING' ? (
                        <>
                          <button
                            onClick={() => onApprove(item.id)}
                            className="p-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm"
                            title="Phê duyệt giá này"
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => onReject(item.id)}
                            className="p-1.5 rounded-lg bg-slate-100 hover:bg-rose-50 dark:bg-slate-800 dark:hover:bg-rose-950/40 text-slate-600 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400 transition"
                            title="Từ chối đề xuất"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </>
                      ) : (
                        <span
                          className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                            item.status === 'APPROVED'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300'
                              : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                          }`}
                        >
                          {item.status === 'APPROVED' ? 'Đã duyệt' : 'Đã từ chối'}
                        </span>
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
