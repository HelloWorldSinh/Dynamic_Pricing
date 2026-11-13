import React, { useState, useMemo } from 'react';
import { PriceChangeHistoryItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';
import { ProductPriceHistoryModal } from './ProductPriceHistoryModal';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { EmptyState } from '../common/EmptyState';

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
      {productGroups.length === 0 ? (
        <EmptyState
          title="Chưa có lịch sử thay đổi giá"
          description="Chưa có sản phẩm nào ghi nhận lịch sử thay đổi giá trong bộ lọc hiện tại."
        />
      ) : (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/90 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-semibold text-xs sticky top-0 z-10">
                  <th className="py-3 px-4">Sản phẩm &amp; SKU</th>
                  <th className="py-3 px-4 text-center">Lần đổi gần nhất</th>
                  <th className="py-3 px-3 text-right">Mức biến động</th>
                  <th className="py-3 px-3 text-center">Biên LN</th>
                  <th className="py-3 px-4">Cập nhật cuối</th>
                  <th className="py-3 px-4 text-center">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
                {productGroups.map((group) => {
                  const isDecrease = group.latestItem.price_change < 0;

                  return (
                    <tr
                      key={group.sku}
                      className="even:bg-white dark:even:bg-slate-900 odd:bg-slate-50/50 dark:odd:bg-slate-800/30 hover:bg-orange-50/40 dark:hover:bg-slate-800/60 transition-colors"
                    >
                      {/* Product & SKU - Clickable */}
                      <td className="py-3 px-4 max-w-[260px]">
                        <button
                          type="button"
                          onClick={() => setSelectedSku(group.sku)}
                          className="text-left group flex flex-col focus:outline-none"
                        >
                          <span className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 group-hover:underline transition-colors truncate">
                            {group.product_name}
                          </span>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <span className="text-2xs font-mono text-slate-500">
                              {group.sku}
                            </span>
                            <Badge size="sm" variant="neutral">
                              {group.category}
                            </Badge>
                          </div>
                        </button>
                      </td>

                      {/* Latest Price Change */}
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        <div className="inline-flex items-center gap-1.5 font-mono text-xs">
                          <span className="text-slate-400 line-through text-2xs">
                            {formatCurrencyVND(group.latestItem.old_price)}
                          </span>
                          <span className="text-slate-400 text-2xs">→</span>
                          <span className="font-bold text-slate-900 dark:text-white">
                            {formatCurrencyVND(group.latestItem.new_price)}
                          </span>
                        </div>
                      </td>

                      {/* Price Change Amount & % */}
                      <td className="py-3 px-3 text-right whitespace-nowrap font-mono font-bold">
                        <Badge
                          size="sm"
                          variant={isDecrease ? 'danger' : 'success'}
                        >
                          {group.latestItem.price_change > 0 ? '+' : ''}{formatCurrencyVND(group.latestItem.price_change)}
                        </Badge>
                        <div className="text-2xs text-slate-400 font-mono mt-0.5">
                          {formatPercent(group.latestItem.price_change_percent)}
                        </div>
                      </td>

                      {/* Margin % */}
                      <td className="py-3 px-3 text-center whitespace-nowrap font-mono font-bold">
                        <Badge size="sm" variant="success">
                          {formatPercent(group.latestItem.margin_percent)}
                        </Badge>
                      </td>

                      {/* Latest Date & Actor */}
                      <td className="py-3 px-4 max-w-[200px] whitespace-nowrap">
                        <div className="font-mono text-slate-600 dark:text-slate-300 text-xs">
                          {formatDateTime(group.latestItem.changed_at)}
                        </div>
                        <div className="text-2xs text-slate-400 mt-0.5">
                          Bởi: <span className="font-medium text-slate-600 dark:text-slate-300">{group.latestItem.changed_by}</span>
                        </div>
                      </td>

                      {/* Action Button */}
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => setSelectedSku(group.sku)}
                        >
                          Lịch sử ({group.revisionsCount})
                        </Button>
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
