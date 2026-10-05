import React from 'react';
import { ShieldCheck, Check, X, TrendingDown } from 'lucide-react';
import { PricingRecommendation } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface RecommendationTableProps {
  items: PricingRecommendation[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onToggleSelectAll: () => void;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

export const RecommendationTable: React.FC<RecommendationTableProps> = ({
  items,
  selectedIds,
  onToggleSelect,
  onToggleSelectAll,
  onApprove,
  onReject,
}) => {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
        <p className="text-xs text-slate-500">Không có đề xuất giá nào trong danh mục này.</p>
      </div>
    );
  }

  const allSelected = items.length > 0 && selectedIds.length === items.length;

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
              <th className="py-3 px-3 text-right">Giá sàn bảo vệ</th>
              <th className="py-3 px-3 text-center">Biên lợi nhuận</th>
              <th className="py-3 px-4">Kịch bản &amp; Căn cứ</th>
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
                  <td className="py-3 px-4 max-w-[240px]">
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

                  {/* Scenario & Reason */}
                  <td className="py-3 px-4 max-w-[280px]">
                    <div className="text-[11px] text-slate-700 dark:text-slate-300 line-clamp-2">
                      {item.scenario}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Đối thủ: {item.competitor_name} ({formatCurrencyVND(item.min_competitor_price)})
                    </div>
                  </td>

                  {/* Action Buttons */}
                  <td className="py-3 px-4 text-center">
                    {item.status === 'PENDING' ? (
                      <div className="flex items-center justify-center gap-1.5">
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
                      </div>
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
