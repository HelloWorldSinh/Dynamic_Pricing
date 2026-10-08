import React from 'react';
import { Database, Smartphone, ShoppingBag, CheckCircle2, Clock } from 'lucide-react';
import { CrawlStats } from '../../api/crawlerApi';
import { formatDate } from '../../utils/formatters';

interface CompetitorSummaryCardsProps {
  stats: CrawlStats | null;
}

export const CompetitorSummaryCards: React.FC<CompetitorSummaryCardsProps> = ({ stats }) => {
  if (!stats) return null;

  const {
    total,
    cellphones_count,
    hoangha_count,
    phone_count,
    laptop_count,
    in_stock_count,
    latest_crawled_at
  } = stats;

  const outOfStockCount = total - in_stock_count;
  const inStockRate = total > 0 ? Math.round((in_stock_count / total) * 100) : 0;
  
  const cellphonesRate = total > 0 ? Math.round((cellphones_count / total) * 100) : 0;
  const hoanghaRate = total > 0 ? Math.round((hoangha_count / total) * 100) : 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
      {/* Card 1: Tổng số sản phẩm */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between transition-all hover:border-slate-300 dark:hover:border-slate-700">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Tổng bản ghi cào
          </span>
          <div className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <Database className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="mt-2">
          <div className="text-xl font-black font-mono text-slate-900 dark:text-white">
            {total}
          </div>
          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
            <span className="inline-block w-1 h-1 rounded-full bg-blue-500" />
            <span>{phone_count} Điện thoại • {laptop_count} Laptop</span>
          </div>
        </div>
      </div>

      {/* Card 2: Dữ liệu CellphoneS */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between transition-all hover:border-rose-300 dark:hover:border-rose-900/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              CELLPHONES
            </span>
          </div>
          <div className="w-7 h-7 rounded-lg bg-rose-50 dark:bg-rose-950/50 text-rose-600 dark:text-rose-400 flex items-center justify-center">
            <Smartphone className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="mt-2">
          <div className="text-xl font-black font-mono text-slate-900 dark:text-white">
            {cellphones_count}
          </div>
          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 flex items-center justify-between">
            <span>Chiếm tỷ trọng</span>
            <span className="font-semibold font-mono text-rose-600 dark:text-rose-400">
              {cellphonesRate}%
            </span>
          </div>
        </div>
      </div>

      {/* Card 3: Dữ liệu Hoàng Hà Mobile */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between transition-all hover:border-amber-300 dark:hover:border-amber-900/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              HOÀNG HÀ
            </span>
          </div>
          <div className="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 flex items-center justify-center">
            <ShoppingBag className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="mt-2">
          <div className="text-xl font-black font-mono text-slate-900 dark:text-white">
            {hoangha_count}
          </div>
          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 flex items-center justify-between">
            <span>Chiếm tỷ trọng</span>
            <span className="font-semibold font-mono text-amber-600 dark:text-amber-400">
              {hoanghaRate}%
            </span>
          </div>
        </div>
      </div>

      {/* Card 4: Tình trạng Kho & Freshness */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between transition-all hover:border-emerald-300 dark:hover:border-emerald-900/60">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Tỷ lệ Còn hàng
          </span>
          <div className="w-7 h-7 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-3.5 h-3.5" />
          </div>
        </div>
        <div className="mt-2">
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-black font-mono text-emerald-600 dark:text-emerald-400">
              {inStockRate}%
            </span>
            <span className="text-[10px] text-slate-400">
              ({outOfStockCount} hết hàng)
            </span>
          </div>
          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1 truncate">
            <Clock className="w-2.5 h-2.5 text-slate-400 flex-shrink-0" />
            <span className="truncate">
              Mới nhất: {latest_crawled_at ? formatDate(latest_crawled_at) : 'Chưa có dữ liệu'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
