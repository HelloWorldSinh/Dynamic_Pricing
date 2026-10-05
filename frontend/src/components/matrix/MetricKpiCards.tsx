import React from 'react';
import { TrendingUp, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';
import { PriceComparisonItem } from '../../types/pricing';

interface MetricKpiCardsProps {
  items: PriceComparisonItem[];
  pendingApprovalsCount: number;
}

export const MetricKpiCards: React.FC<MetricKpiCardsProps> = ({
  items,
  pendingApprovalsCount,
}) => {
  const totalSkus = items.length;
  const expensiveCount = items.filter((item) => item.price_diff > 0).length;
  const winRate = totalSkus > 0 ? Math.round(((totalSkus - expensiveCount) / totalSkus) * 100) : 0;
  const highRiskDohCount = items.filter((item) => item.doh > 45).length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* Total SKUs */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Tổng mã theo dõi
          </span>
          <span className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
            <TrendingUp className="w-4 h-4" />
          </span>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-slate-900 dark:text-white">
            {totalSkus}
          </span>
          <span className="text-xs text-slate-500">SKU chuẩn</span>
        </div>
        <div className="mt-1 text-[11px] text-slate-400">
          CellphoneS & Hoàng Hà Mobile
        </div>
      </div>

      {/* FPT Đắt Hơn */}
      <div className="p-4 rounded-xl border border-rose-200 dark:border-rose-950/60 bg-rose-50/30 dark:bg-rose-950/20 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-wider">
            FPT đang đắt hơn
          </span>
          <span className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-300">
            <AlertTriangle className="w-4 h-4" />
          </span>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-rose-600 dark:text-rose-400">
            {expensiveCount}
          </span>
          <span className="text-xs text-rose-600/80 dark:text-rose-400/80 font-medium">
            mã hàng cần xử lý
          </span>
        </div>
        <div className="mt-1 text-[11px] text-rose-500/80 dark:text-rose-400/60">
          {highRiskDohCount} mã có DOH &gt; 45 ngày
        </div>
      </div>

      {/* Win Rate */}
      <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-950/60 bg-emerald-50/30 dark:bg-emerald-950/20 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">
            Tỉ lệ cạnh tranh giá
          </span>
          <span className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-300">
            <CheckCircle2 className="w-4 h-4" />
          </span>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
            {winRate}%
          </span>
          <span className="text-xs text-emerald-600/80 dark:text-emerald-400/80 font-medium">
            bằng hoặc rẻ hơn
          </span>
        </div>
        <div className="mt-1 text-[11px] text-emerald-500/80 dark:text-emerald-400/60">
          Bảo vệ thị phần bán lẻ
        </div>
      </div>

      {/* Pending Approvals */}
      <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-950/60 bg-amber-50/30 dark:bg-amber-950/20 shadow-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wider">
            Đề xuất chờ duyệt
          </span>
          <span className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/40 text-amber-600 dark:text-amber-300">
            <Clock className="w-4 h-4" />
          </span>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-amber-600 dark:text-amber-400">
            {pendingApprovalsCount}
          </span>
          <span className="text-xs text-amber-600/80 dark:text-amber-400/80 font-medium">
            gợi ý giá mới
          </span>
        </div>
        <div className="mt-1 text-[11px] text-amber-500/80 dark:text-amber-400/60">
          Có kiểm tra an toàn giá sàn
        </div>
      </div>
    </div>
  );
};
