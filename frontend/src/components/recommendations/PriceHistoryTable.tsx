import React, { useState, useMemo } from 'react';
import { 
  History, 
  ArrowRight, 
  TrendingDown, 
  TrendingUp, 
  Eye 
} from 'lucide-react';
import { PriceChangeHistoryItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';
import { ProductPriceHistoryModal } from './ProductPriceHistoryModal';

export interface ProductPriceHistoryGroup {
  sku: string;
  product_name: string;
  category: string;
  latestItem: PriceChangeHistoryItem;
  revisionsCount: number;
}

interface PriceHistoryTableProps {
  products?: ProductPriceHistoryGroup[];
  items?: PriceChangeHistoryItem[];
  allItems?: PriceChangeHistoryItem[];
}

export const PriceHistoryTable: React.FC<PriceHistoryTableProps> = ({ 
  products,
  items,
  allItems
}) => {
  const [selectedSku, setSelectedSku] = useState<string | null>(null);

  // Group items by product (SKU) if products array is not passed directly
  const productGroups = useMemo(() => {
    if (products && products.length > 0) {
      return products;
    }
    if (!items || items.length === 0) {
      return [];
    }

    const map = new Map<string, ProductPriceHistoryGroup>();
    const sourceForCount = allItems || items;
    const countMap = new Map<string, number>();
    sourceForCount.forEach((item) => {
      countMap.set(item.sku, (countMap.get(item.sku) || 0) + 1);
    });

    items.forEach((item) => {
      if (!map.has(item.sku)) {
        map.set(item.sku, {
          sku: item.sku,
          product_name: item.product_name,
          category: item.category,
          latestItem: item,
          revisionsCount: countMap.get(item.sku) || 1,
        });
      }
    });

    return Array.from(map.values());
  }, [products, items, allItems]);

  const formatDateTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      const pad = (n: number) => n.toString().padStart(2, '0');
      return `${pad(d.getHours())}:${pad(d.getMinutes())} - ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-4">
      {/* Main Content Table: Direct Product Listing */}
      {productGroups.length === 0 ? (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
          <History className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-50" />
          <p className="text-xs text-slate-500">Chưa có sản phẩm nào có lịch sử thay đổi giá phù hợp.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Sản phẩm &amp; SKU</th>
                  <th className="py-3 px-4 text-center">Lần đổi gần nhất</th>
                  <th className="py-3 px-3 text-right">Mức biến động</th>
                  <th className="py-3 px-3 text-center">Biên LN</th>
                  <th className="py-3 px-3 text-center">Số lần đổi giá</th>
                  <th className="py-3 px-4">Cập nhật cuối</th>
                  <th className="py-3 px-4 text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {productGroups.map((group) => {
                  const isDecrease = group.latestItem.price_change < 0;

                  return (
                    <tr
                      key={group.sku}
                      className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {/* Product & SKU - Clickable */}
                      <td className="py-3 px-4 max-w-[260px]">
                        <button
                          onClick={() => setSelectedSku(group.sku)}
                          className="text-left group flex flex-col focus:outline-none"
                          title="Nhấn để xem toàn bộ lịch sử các lần chỉnh sửa giá của sản phẩm này"
                        >
                          <span className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 group-hover:underline transition-colors truncate">
                            {group.product_name}
                          </span>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="text-[10px] font-mono text-slate-500">
                              {group.sku}
                            </span>
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold uppercase">
                              {group.category}
                            </span>
                          </div>
                        </button>
                      </td>

                      {/* Latest Price Change */}
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        <div className="inline-flex items-center gap-1.5 font-mono">
                          <span className="text-slate-400 line-through text-[11px]">
                            {formatCurrencyVND(group.latestItem.old_price)}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                          <span className="font-bold text-slate-900 dark:text-white">
                            {formatCurrencyVND(group.latestItem.new_price)}
                          </span>
                        </div>
                      </td>

                      {/* Price Change Amount & % */}
                      <td className="py-3 px-3 text-right whitespace-nowrap font-mono font-bold">
                        <span
                          className={`inline-flex items-center gap-1 ${
                            isDecrease
                              ? 'text-rose-600 dark:text-rose-400'
                              : 'text-emerald-600 dark:text-emerald-400'
                          }`}
                        >
                          {isDecrease ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                          <span>{group.latestItem.price_change > 0 ? '+' : ''}{formatCurrencyVND(group.latestItem.price_change)}</span>
                        </span>
                        <div className="text-[10px] text-slate-400 font-normal">
                          {formatPercent(group.latestItem.price_change_percent)}
                        </div>
                      </td>

                      {/* Margin % */}
                      <td className="py-3 px-3 text-center whitespace-nowrap font-mono font-bold">
                        <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900">
                          {formatPercent(group.latestItem.margin_percent)}
                        </span>
                      </td>

                      {/* Total Revisions Badge */}
                      <td className="py-3 px-3 text-center whitespace-nowrap">
                        <button
                          onClick={() => setSelectedSku(group.sku)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800/80 hover:bg-orange-100 dark:hover:bg-orange-900/60 transition shadow-sm"
                          title="Bấm để xem danh sách các lần sửa giá"
                        >
                          <History className="w-3 h-3" />
                          <span>{group.revisionsCount} lần điều chỉnh</span>
                        </button>
                      </td>

                      {/* Latest Date & Actor */}
                      <td className="py-3 px-4 max-w-[200px] whitespace-nowrap">
                        <div className="font-mono text-slate-600 dark:text-slate-300">
                          {formatDateTime(group.latestItem.changed_at)}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          Bởi: <span className="font-medium text-slate-600 dark:text-slate-300">{group.latestItem.changed_by}</span>
                        </div>
                      </td>

                      {/* Action Button */}
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        <button
                          onClick={() => setSelectedSku(group.sku)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-medium text-xs transition shadow-sm"
                          title="Xem lịch sử các lần sửa đổi giá của sản phẩm này"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>Xem lịch sử ({group.revisionsCount})</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Product Price History Modal Popup */}
      <ProductPriceHistoryModal
        sku={selectedSku}
        items={allItems || items || []}
        onClose={() => setSelectedSku(null)}
      />
    </div>
  );
};
