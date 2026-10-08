import React from 'react';
import { ExternalLink, Sliders, Inbox } from 'lucide-react';
import { CrawlResult } from '../../types/crawl';
import { formatCurrencyVND, formatDate } from '../../utils/formatters';

interface CompetitorDataTableProps {
  items: CrawlResult[];
  onSelectProduct: (item: CrawlResult) => void;
  onResetFilter?: () => void;
}

export const CompetitorDataTable: React.FC<CompetitorDataTableProps> = ({
  items,
  onSelectProduct,
  onResetFilter,
}) => {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
        <Inbox className="w-10 h-10 mx-auto text-slate-400 dark:text-slate-600 mb-3" />
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
          Không tìm thấy dữ liệu cào đối thủ phù hợp
        </h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Không có sản phẩm nào thỏa mãn điều kiện tìm kiếm hoặc bộ lọc hiện tại.
        </p>
        {onResetFilter && (
          <button
            onClick={onResetFilter}
            className="mt-4 px-3 py-1.5 text-xs font-semibold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/40 hover:bg-orange-100 dark:hover:bg-orange-900/40 rounded-lg transition"
          >
            Đặt lại bộ lọc
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-3 px-4 w-36">Nguồn cào</th>
              <th className="py-3 px-4 min-w-[280px]">Tên sản phẩm đối thủ</th>
              <th className="py-3 px-4 text-right w-40">Giá bán đối thủ</th>
              <th className="py-3 px-4 text-center w-36">Tình trạng kho</th>
              <th className="py-3 px-4 text-center w-36">Thời điểm cào</th>
              <th className="py-3 px-4 text-center w-32">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {items.map((item) => {
              const isCellphoneS = item.source === 'CELLPHONES';
              const hasDiscount = item.original_price && item.original_price > item.price;
              const specsCount = Object.keys(item.specifications || {}).length;

              return (
                <tr
                  key={item.id}
                  onClick={() => onSelectProduct(item)}
                  className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition cursor-pointer group"
                >
                  {/* Cột 1: Nguồn đối thủ */}
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold tracking-wider border ${
                        isCellphoneS
                          ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-900'
                          : 'bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-900'
                      }`}
                    >
                      {item.source}
                    </span>
                  </td>

                  {/* Cột 2: Tên sản phẩm */}
                  <td className="py-3.5 px-4">
                    <div className="font-semibold text-slate-900 dark:text-slate-100 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition leading-snug">
                      {item.product_name}
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400 font-mono">
                      <span className="truncate max-w-xs">{item.url}</span>
                    </div>
                  </td>

                  {/* Cột 3: Giá bán */}
                  <td className="py-3.5 px-4 text-right">
                    <div className="font-bold font-mono text-sm text-slate-900 dark:text-slate-100">
                      {formatCurrencyVND(item.price)}
                    </div>
                    {hasDiscount && (
                      <div className="text-[10px] text-slate-400 line-through font-mono mt-0.5">
                        {formatCurrencyVND(item.original_price)}
                      </div>
                    )}
                  </td>

                  {/* Cột 4: Trạng thái kho */}
                  <td className="py-3.5 px-4 text-center">
                    <span
                      className={`inline-flex items-center text-[10px] font-semibold px-2.5 py-0.5 rounded-full ${
                        item.is_in_stock
                          ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900/60'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-200 dark:border-slate-700'
                      }`}
                    >
                      {item.is_in_stock ? 'Còn hàng' : 'Tạm hết'}
                    </span>
                    {item.stock_status_text && (
                      <div className="text-[10px] text-slate-400 mt-0.5 truncate max-w-[130px] mx-auto">
                        {item.stock_status_text}
                      </div>
                    )}
                  </td>

                  {/* Cột 5: Thời điểm cào */}
                  <td className="py-3.5 px-4 text-center font-mono text-[11px] text-slate-500 dark:text-slate-400">
                    {formatDate(item.crawled_at)}
                  </td>

                  {/* Cột 6: Thao tác */}
                  <td className="py-3.5 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-center gap-1.5">
                      <button
                        onClick={() => onSelectProduct(item)}
                        className="px-2.5 py-1 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-orange-600 dark:hover:text-orange-400 bg-slate-100 dark:bg-slate-800 hover:bg-orange-50 dark:hover:bg-orange-950/40 flex items-center gap-1 transition"
                        title="Xem chi tiết thông số kỹ thuật và raw JSON"
                      >
                        <Sliders className="w-3 h-3" />
                        <span>Specs ({specsCount})</span>
                      </button>

                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 rounded-lg text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                        title="Mở bài viết gốc đối thủ"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
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
