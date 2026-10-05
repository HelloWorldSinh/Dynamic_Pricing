import React from 'react';
import { 
  ExternalLink, 
  Info, 
  ArrowUpDown, 
  TrendingUp, 
  TrendingDown, 
  Equal 
} from 'lucide-react';
import { PriceComparisonItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface PriceMatrixTableProps {
  items: PriceComparisonItem[];
  onSelectProduct: (item: PriceComparisonItem) => void;
  onExplainProduct?: (item: PriceComparisonItem) => void;
}

export const PriceMatrixTable: React.FC<PriceMatrixTableProps> = ({
  items,
  onSelectProduct,
}) => {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
        <Info className="w-8 h-8 mx-auto text-slate-400 mb-3" />
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
          Không tìm thấy sản phẩm nào
        </h3>
        <p className="text-xs text-slate-500 mt-1">
          Hãy thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm của bạn.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4">Sản phẩm &amp; Mã Part</th>
              <th className="py-3 px-3 text-right">Giá FPT Shop</th>
              <th className="py-3 px-3 text-right">CellphoneS</th>
              <th className="py-3 px-3 text-right">Hoàng Hà</th>
              <th className="py-3 px-3 text-center">
                <span className="flex items-center justify-center gap-1 cursor-pointer">
                  Chênh lệch <ArrowUpDown className="w-3 h-3 text-slate-400" />
                </span>
              </th>
              <th className="py-3 px-3 text-center">Độ tin cậy</th>
              <th className="py-3 px-3 text-center">Tồn kho / DOH</th>
              <th className="py-3 px-4 text-center">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {items.map((item) => {
              const isExpensive = item.price_diff > 0;
              const isDanger = item.price_diff_percent >= 5;
              const isCheaper = item.price_diff < 0;
              const isEqual = item.price_diff === 0;

              return (
                <tr
                  key={item.id}
                  className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                >
                  {/* Product Info */}
                  <td className="py-3 px-4 max-w-[280px]">
                    <div className="font-semibold text-slate-900 dark:text-slate-100 truncate" title={item.name}>
                      {item.name}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                        {item.sku}
                      </span>
                      {item.part_number && (
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 font-medium">
                          PN: {item.part_number}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* FPT Price */}
                  <td className="py-3 px-3 text-right font-bold text-slate-900 dark:text-white text-sm font-mono">
                    {formatCurrencyVND(item.fpt_price)}
                  </td>

                  {/* CellphoneS Price */}
                  <td className="py-3 px-3 text-right">
                    {item.cellphones ? (
                      <div className="flex flex-col items-end">
                        <span className="font-semibold font-mono text-slate-800 dark:text-slate-200">
                          {formatCurrencyVND(item.cellphones.price)}
                        </span>
                        <div className="flex items-center gap-1 mt-0.5">
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-medium ${
                              item.cellphones.is_in_stock
                                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                                : 'bg-slate-100 dark:bg-slate-800 text-slate-400'
                            }`}
                          >
                            {item.cellphones.is_in_stock ? 'Còn hàng' : 'Hết hàng'}
                          </span>
                          <a
                            href={item.cellphones.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                            title="Mở web CellphoneS"
                          >
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-400 text-[11px]">—</span>
                    )}
                  </td>

                  {/* Hoàng Hà Price */}
                  <td className="py-3 px-3 text-right">
                    {item.hoangha ? (
                      <div className="flex flex-col items-end">
                        <span className="font-semibold font-mono text-slate-800 dark:text-slate-200">
                          {formatCurrencyVND(item.hoangha.price)}
                        </span>
                        <div className="flex items-center gap-1 mt-0.5">
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-medium ${
                              item.hoangha.is_in_stock
                                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                                : 'bg-slate-100 dark:bg-slate-800 text-slate-400'
                            }`}
                          >
                            {item.hoangha.is_in_stock ? 'Còn hàng' : 'Hết hàng'}
                          </span>
                          <a
                            href={item.hoangha.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                            title="Mở web Hoàng Hà"
                          >
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-400 text-[11px]">—</span>
                    )}
                  </td>

                  {/* Price Gap Diff Badge */}
                  <td className="py-3 px-3 text-center">
                    <div className="inline-flex flex-col items-center">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold font-mono ${
                          isDanger
                            ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/80 dark:text-rose-400 border border-rose-300 dark:border-rose-900'
                            : isExpensive
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/80 dark:text-amber-400 border border-amber-300 dark:border-amber-900'
                            : isCheaper
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/80 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-900'
                            : 'bg-blue-100 text-blue-700 dark:bg-blue-950/80 dark:text-blue-400 border border-blue-300 dark:border-blue-900'
                        }`}
                      >
                        {isExpensive ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : isCheaper ? (
                          <TrendingDown className="w-3 h-3" />
                        ) : (
                          <Equal className="w-3 h-3" />
                        )}
                        {formatPercent(item.price_diff_percent)}
                      </span>
                      <span className="text-[10px] text-slate-400 mt-0.5 font-mono">
                        {isEqual ? 'Bằng giá' : formatCurrencyVND(Math.abs(item.price_diff))}
                      </span>
                    </div>
                  </td>

                  {/* Confidence Badge */}
                  <td className="py-3 px-3 text-center">
                    <span
                      className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        item.confidence_score === 100
                          ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
                          : item.confidence_score >= 80
                          ? 'bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800'
                          : 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800'
                      }`}
                    >
                      {item.confidence_score}%
                    </span>
                  </td>

                  {/* Inventory / DOH */}
                  <td className="py-3 px-3 text-center">
                    <div className="font-medium text-slate-800 dark:text-slate-200">
                      {item.inventory_quantity} máy
                    </div>
                    <span
                      className={`text-[10px] font-semibold ${
                        item.doh > 45
                          ? 'text-rose-600 dark:text-rose-400 font-bold'
                          : item.doh > 30
                          ? 'text-amber-600 dark:text-amber-400'
                          : 'text-slate-400'
                      }`}
                    >
                      DOH: {item.doh} ngày
                    </span>
                  </td>

                  {/* Action Buttons */}
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => onSelectProduct(item)}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium transition shadow-sm"
                      title="Xem thông số kỹ thuật chi tiết"
                    >
                      Chi tiết
                    </button>
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
