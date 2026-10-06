import React from 'react';
import { TrendingDown, Package, ShieldCheck } from 'lucide-react';
import { ExplainableFactors } from '../../types/ai';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface ExplainableCardProps {
  factors: ExplainableFactors;
}

export const ExplainableCard: React.FC<ExplainableCardProps> = ({ factors }) => {
  const { competitor_shift, inventory_status, floor_protection } = factors;

  return (
    <div className="mt-3 p-4 rounded-xl border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-900 shadow-md text-xs space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
        <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px] flex items-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-orange-500" />
          Giải Trình Minh Bạch 3 Lớp (Explainable AI)
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-orange-50 dark:bg-orange-950/60 text-orange-600 dark:text-orange-400 font-semibold font-mono">
          PBI-018
        </span>
      </div>

      {/* Tier 1: Biến động giá đối thủ */}
      <div className="p-3 rounded-lg bg-rose-50/50 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40">
        <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400 font-bold mb-1">
          <TrendingDown className="w-3.5 h-3.5" />
          <span>Lớp 1: Biến Động Thị Trường Đối Thủ</span>
        </div>
        <div className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
          Đối thủ <strong>{competitor_shift.competitor}</strong> vừa điều chỉnh giảm{' '}
          <strong className="text-rose-600 dark:text-rose-400">
            {formatCurrencyVND(competitor_shift.price_cut)}
          </strong>
          , đưa mức giá về <strong>{formatCurrencyVND(competitor_shift.new_price)}</strong>. Trạng thái hàng: 
          <span className="font-semibold ml-1">
            {competitor_shift.is_in_stock ? 'Thực sự còn hàng online (Kích hoạt luật bám giá)' : 'Hết hàng (Bỏ qua)'}
          </span>.
        </div>
      </div>

      {/* Tier 2: Hiện trạng tồn kho FPT */}
      <div className="p-3 rounded-lg bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400 font-bold mb-1">
          <Package className="w-3.5 h-3.5" />
          <span>Lớp 2: Hiện Trạng Tồn Kho FPT Shop</span>
        </div>
        <div className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
          Tồn kho khả dụng: <strong>{inventory_status.quantity} máy</strong>. Số ngày lưu kho: 
          <strong className="text-amber-600 dark:text-amber-400 ml-1">
            DOH = {inventory_status.doh} ngày
          </strong>{' '}
          ({inventory_status.doh > 45 ? 'Thuộc diện rủi ro cao DOH > 45 ngày, cần ưu tiên giải phóng vốn' : 'Tốc độ quay vòng ổn định'}).
        </div>
      </div>

      {/* Tier 3: Kiểm tra an toàn giá sàn */}
      <div className="p-3 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40">
        <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400 font-bold mb-1">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Lớp 3: Kiểm Tra An Toàn Giá Sàn (Floor Price Guard)</span>
        </div>
        <div className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
          Giá sàn tối thiểu: <strong>{formatCurrencyVND(floor_protection.floor_price)}</strong> (Giá vốn + Biên tối thiểu).
          Giá đề xuất mới <strong>{formatCurrencyVND(floor_protection.suggested_price)}</strong> vẫn cao hơn giá sàn{' '}
          <strong className="text-emerald-600 dark:text-emerald-400">
            {formatPercent(floor_protection.safety_margin_percent)}
          </strong>
          {floor_protection.is_capped ? (
            <span className="block mt-1 font-semibold text-pink-600 dark:text-pink-400">
              * Chú ý: Đề xuất ban đầu dưới giá sàn và đã được hệ thống tự động chốt bằng giá sàn để bảo vệ biên lợi nhuận.
            </span>
          ) : (
            <span className="block mt-1 font-semibold text-emerald-600 dark:text-emerald-400">
              ✓ Đảm bảo an toàn 100% biên lợi nhuận kinh doanh.
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
