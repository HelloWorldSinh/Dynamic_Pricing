import React from 'react';
import { ExplainableFactors } from '../../types/ai';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface ExplainableCardProps {
  factors: ExplainableFactors;
}

export const ExplainableCard: React.FC<ExplainableCardProps> = ({ factors }) => {
  const { competitor_shift, inventory_status, floor_protection } = factors;

  // Tính toán độ rộng thanh tiến trình biên an toàn (Scale từ 0% đến 25% an toàn = 100% thanh bar)
  const marginVal = floor_protection.safety_margin_percent || 0;
  const barFillPercent = floor_protection.is_capped
    ? 5
    : Math.min(100, Math.max(8, (marginVal / 20) * 100));

  const isMarginHealthy = marginVal >= 5 && !floor_protection.is_capped;
  const isMarginWarning = marginVal > 0 && marginVal < 5 && !floor_protection.is_capped;

  return (
    <div className="mt-3 p-4 rounded-xl border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-900 shadow-xs text-xs space-y-3.5">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-900 dark:text-white uppercase tracking-wider text-[11px]">
            Căn Cứ Giải Trình 3 Lớp (Explainable AI)
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-orange-50 dark:bg-orange-950/60 text-orange-600 dark:text-orange-400 font-mono font-semibold">
            PBI-018
          </span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">
          TRIPLE-GUARD
        </span>
      </div>

      {/* Lớp 1: Biến động giá đối thủ */}
      <div className="p-3 rounded-lg bg-rose-50/40 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wide">
            [LỚP 1] Thị Trường Đối Thủ
          </span>
          <span
            className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
              competitor_shift.is_in_stock
                ? 'bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
            }`}
          >
            {competitor_shift.is_in_stock ? 'CÒN HÀNG THỰC TẾ' : 'HẾT HÀNG'}
          </span>
        </div>
        <div className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
          Đối thủ <strong>{competitor_shift.competitor}</strong> vừa điều chỉnh giảm{' '}
          <strong className="text-rose-600 dark:text-rose-400">
            {formatCurrencyVND(competitor_shift.price_cut)}
          </strong>
          , đưa mức giá về <strong>{formatCurrencyVND(competitor_shift.new_price)}</strong>.
          {competitor_shift.is_in_stock
            ? ' Hệ thống kích hoạt luật bám giá cạnh tranh để bảo vệ thị phần.'
            : ' Đối thủ hết hàng trên website, hệ thống bỏ qua không hạ giá theo.'}
        </div>
      </div>

      {/* Lớp 2: Hiện trạng tồn kho FPT */}
      <div className="p-3 rounded-lg bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[11px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wide">
            [LỚP 2] Hiện Trạng Tồn Kho FPT Shop
          </span>
          <span
            className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
              inventory_status.doh > 45
                ? 'bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}
          >
            DOH = {inventory_status.doh} NGÀY
          </span>
        </div>
        <div className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
          Tồn kho khả dụng: <strong>{inventory_status.quantity} máy</strong>. Số ngày lưu kho:{' '}
          <strong className="text-amber-700 dark:text-amber-400">
            {inventory_status.doh} ngày
          </strong>{' '}
          ({inventory_status.doh > 45
            ? 'Thuộc diện rủi ro cao DOH > 45 ngày, cần ưu tiên kích cầu giải phóng vốn'
            : 'Tốc độ quay vòng bình thường, không chịu áp lực tồn đọng'}).
        </div>
      </div>

      {/* Lớp 3: Kiểm tra an toàn giá sàn & Thanh tiến trình trực quan */}
      <div className="p-3 rounded-lg bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40 space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wide">
            [LỚP 3] Bảo Vệ Giá Sàn (Floor Price Guard)
          </span>
          <span
            className={`text-[10px] px-2 py-0.5 rounded font-mono font-semibold ${
              floor_protection.is_capped
                ? 'bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300'
                : isMarginHealthy
                ? 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300'
                : 'bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300'
            }`}
          >
            {floor_protection.is_capped
              ? 'GHIM CHẶN TẠI GIÁ SÀN'
              : `BIÊN AN TOÀN ${formatPercent(floor_protection.safety_margin_percent)}`}
          </span>
        </div>

        {/* Visual Safety Margin Progress Bar */}
        <div className="bg-slate-100 dark:bg-slate-800/80 p-2.5 rounded-md border border-slate-200/60 dark:border-slate-700/60 space-y-1.5">
          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 dark:text-slate-400">
            <span>Giá sàn: {formatCurrencyVND(floor_protection.floor_price)}</span>
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              Đề xuất: {formatCurrencyVND(floor_protection.suggested_price)}
            </span>
          </div>

          <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${
                floor_protection.is_capped
                  ? 'bg-rose-500'
                  : isMarginHealthy
                  ? 'bg-emerald-500'
                  : isMarginWarning
                  ? 'bg-amber-500'
                  : 'bg-slate-400'
              }`}
              style={{ width: `${barFillPercent}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-[10px]">
            <span className="text-slate-400">Ngưỡng vốn tối thiểu</span>
            <span
              className={`font-mono font-semibold ${
                floor_protection.is_capped
                  ? 'text-rose-600 dark:text-rose-400'
                  : 'text-emerald-600 dark:text-emerald-400'
              }`}
            >
              {floor_protection.is_capped
                ? '0.0% (Chạm giá sàn)'
                : `${formatPercent(floor_protection.safety_margin_percent)} an toàn`}
            </span>
          </div>
        </div>

        <div className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
          {floor_protection.is_capped ? (
            <span className="font-semibold text-rose-700 dark:text-rose-400">
              Chú ý: Mức giá bám theo đối thủ thấp hơn giá sàn, thuật toán tự động ghim chặn tại đúng giá sàn để đảm bảo không bán lỗ.
            </span>
          ) : (
            <span className="text-slate-700 dark:text-slate-300">
              Mức giá đề xuất mới đảm bảo an toàn tuyệt đối cho biên lợi nhuận gộp, cao hơn giá sàn{' '}
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono">
                {formatPercent(floor_protection.safety_margin_percent)}
              </strong>.
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
