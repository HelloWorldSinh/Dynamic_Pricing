import React, { useState, useEffect } from 'react';
import { 
  X, 
  ShieldCheck, 
  AlertTriangle, 
  TrendingDown, 
  TrendingUp, 
  Check, 
  Bot, 
  Sliders, 
  BarChart3, 
  Warehouse 
} from 'lucide-react';
import { PricingRecommendation } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface PricingDetailModalProps {
  recommendation: PricingRecommendation | null;
  onClose: () => void;
  onApply: (id: string, finalPrice: number, changeType: 'AI_RECOMMENDED' | 'MANUAL_CONFIG') => void;
  onReject: (id: string) => void;
}

export const PricingDetailModal: React.FC<PricingDetailModalProps> = ({
  recommendation,
  onClose,
  onApply,
  onReject,
}) => {
  if (!recommendation) return null;

  const [priceMode, setPriceMode] = useState<'SUGGESTED' | 'CUSTOM'>('SUGGESTED');
  const [customPrice, setCustomPrice] = useState<number>(recommendation.suggested_price);
  const [overrideFloor, setOverrideFloor] = useState<boolean>(false);

  // Sync state when recommendation changes
  useEffect(() => {
    if (recommendation) {
      setPriceMode('SUGGESTED');
      setCustomPrice(recommendation.suggested_price);
      setOverrideFloor(false);
    }
  }, [recommendation]);

  // Derived values for 3-shop comparison
  const fptCurrentPrice = recommendation.current_price;
  const cellphonesPrice = recommendation.cellphones_price || recommendation.min_competitor_price;
  const cellphonesInStock = recommendation.cellphones_in_stock !== false;
  const hoanghaPrice = recommendation.hoangha_price || Math.round(recommendation.min_competitor_price * 1.005);
  const hoanghaInStock = recommendation.hoangha_in_stock !== false;

  // Active chosen price
  const activePrice = priceMode === 'SUGGESTED' ? recommendation.suggested_price : customPrice;
  const isBelowFloor = activePrice < recommendation.floor_price;
  const activeMarginPercent = Math.round(
    ((activePrice - recommendation.cost_price) / activePrice) * 1000
  ) / 10;
  const priceDiffVsCurrent = activePrice - recommendation.current_price;

  // Bar Chart calculations
  const allPrices = [fptCurrentPrice, activePrice, cellphonesPrice, hoanghaPrice];
  const maxPrice = Math.max(...allPrices);
  const minPrice = Math.min(...allPrices, recommendation.floor_price);
  const range = maxPrice - minPrice || 1;

  const getBarHeight = (price: number) => {
    const ratio = (price - minPrice) / range;
    return Math.round(ratio * 55 + 40); // 40% to 95% height
  };

  const handleApplyClick = () => {
    if (isBelowFloor && !overrideFloor) return;
    onApply(
      recommendation.id,
      activePrice,
      priceMode === 'SUGGESTED' ? 'AI_RECOMMENDED' : 'MANUAL_CONFIG'
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-3xl max-h-[92vh] flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-orange-600/10 text-orange-600 dark:text-orange-400">
                <BarChart3 className="w-4 h-4" />
              </span>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Căn Cứ &amp; Cấu Hình Định Giá
              </h2>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-semibold">
                {recommendation.sku}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 font-medium line-clamp-1">
              {recommendation.product_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Section 1: Căn Cứ & Tín Hiệu Định Giá */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-1.5">
              <span>1. Thông tin căn cứ &amp; Tín hiệu thị trường</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Kịch bản áp dụng */}
              <div className="p-3.5 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/30 dark:bg-blue-950/20 md:col-span-2">
                <div className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide flex items-center gap-1.5">
                  <Bot className="w-3.5 h-3.5" />
                  <span>Kịch bản phân tích</span>
                </div>
                <div className="text-xs text-slate-800 dark:text-slate-200 font-medium mt-1.5 leading-relaxed">
                  {recommendation.scenario}
                </div>
              </div>

              {/* Tồn kho & DOH */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
                <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                  <Warehouse className="w-3.5 h-3.5" />
                  <span>Tồn kho &amp; DOH</span>
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className={`text-lg font-black font-mono ${recommendation.doh > 45 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-white'}`}>
                    {recommendation.doh}
                  </span>
                  <span className="text-xs text-slate-500">ngày DOH</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Hiện còn: <span className="font-semibold text-slate-700 dark:text-slate-300">{recommendation.inventory_quantity} máy</span>
                </div>
              </div>
            </div>

            {/* Thước đo tài chính */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
              <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[10px] text-slate-400 font-medium">Giá bán hiện tại</div>
                <div className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200 mt-1">
                  {formatCurrencyVND(recommendation.current_price)}
                </div>
              </div>
              <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[10px] text-slate-400 font-medium">Giá vốn (Cost)</div>
                <div className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200 mt-1">
                  {formatCurrencyVND(recommendation.cost_price)}
                </div>
              </div>
              <div className="p-3 rounded-xl border border-pink-200 dark:border-pink-900/50 bg-pink-50/20 dark:bg-pink-950/20">
                <div className="text-[10px] text-pink-600 dark:text-pink-400 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  <span>Giá sàn bảo vệ</span>
                </div>
                <div className="text-xs font-bold font-mono text-pink-600 dark:text-pink-400 mt-1">
                  {formatCurrencyVND(recommendation.floor_price)}
                </div>
              </div>
              <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[10px] text-slate-400 font-medium">Đối thủ thấp nhất</div>
                <div className="text-xs font-bold font-mono text-slate-800 dark:text-slate-200 mt-1">
                  {formatCurrencyVND(recommendation.min_competitor_price)}
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Biểu Đồ Cột So Sánh Mức Giá 3 Shop */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center gap-1.5">
                <span>2. Biểu đồ so sánh mức giá 3 shop hiện tại</span>
              </h3>
              <div className="flex items-center gap-3 text-[10px] text-slate-400">
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-sm bg-orange-600 inline-block" /> FPT Shop
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 inline-block" /> CellphoneS
                </span>
                <span className="flex items-center gap-1">
                  <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 inline-block" /> Hoàng Hà
                </span>
              </div>
            </div>

            {/* Visual Bar Chart Box */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
              <div className="h-48 flex items-end justify-around gap-4 pt-6 pb-2 px-4 relative">
                {/* Floor Price Guide Line */}
                <div 
                  className="absolute left-0 right-0 border-b border-dashed border-pink-400 dark:border-pink-500 z-10 flex items-center justify-end pr-2 pointer-events-none"
                  style={{ bottom: `${getBarHeight(recommendation.floor_price) * 0.45}%` }}
                >
                  <span className="text-[10px] font-mono text-pink-600 dark:text-pink-400 bg-white dark:bg-slate-900 px-1.5 py-0.5 rounded shadow-sm border border-pink-200 dark:border-pink-800">
                    Sàn: {formatCurrencyVND(recommendation.floor_price)}
                  </span>
                </div>

                {/* Bar 1: FPT Shop (Hiện tại) */}
                <div className="flex-1 flex flex-col items-center h-full justify-end max-w-[120px]">
                  <div className="text-[11px] font-mono font-bold text-orange-600 dark:text-orange-400 mb-1">
                    {formatCurrencyVND(fptCurrentPrice)}
                  </div>
                  <div 
                    className="w-full rounded-t-lg bg-orange-500/80 hover:bg-orange-500 transition-all shadow-md flex items-end justify-center pb-2"
                    style={{ height: `${getBarHeight(fptCurrentPrice)}%` }}
                  >
                    <span className="text-[10px] font-bold text-white tracking-tighter">FPT Hiện tại</span>
                  </div>
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-2 text-center">
                    FPT Shop
                  </div>
                  <div className="text-[10px] text-slate-400">Baseline</div>
                </div>

                {/* Bar 2: FPT Shop (Đang chọn áp dụng) */}
                <div className="flex-1 flex flex-col items-center h-full justify-end max-w-[120px]">
                  <div className="text-[11px] font-mono font-black text-amber-500 mb-1 flex items-center gap-0.5">
                    {priceDiffVsCurrent < 0 ? (
                      <TrendingDown className="w-3 h-3 text-rose-500" />
                    ) : (
                      <TrendingUp className="w-3 h-3 text-emerald-500" />
                    )}
                    <span>{formatCurrencyVND(activePrice)}</span>
                  </div>
                  <div 
                    className="w-full rounded-t-lg bg-gradient-to-t from-orange-600 to-amber-500 transition-all shadow-lg ring-2 ring-orange-500/50 flex items-end justify-center pb-2"
                    style={{ height: `${getBarHeight(activePrice)}%` }}
                  >
                    <span className="text-[10px] font-bold text-white tracking-tighter">Áp Dụng Mới</span>
                  </div>
                  <div className="text-xs font-semibold text-orange-600 dark:text-orange-400 mt-2 text-center">
                    FPT Mới
                  </div>
                  <div className="text-[10px] font-medium text-emerald-500">
                    Margin: {formatPercent(activeMarginPercent)}
                  </div>
                </div>

                {/* Bar 3: CellphoneS */}
                <div className="flex-1 flex flex-col items-center h-full justify-end max-w-[120px]">
                  <div className="text-[11px] font-mono font-bold text-rose-600 dark:text-rose-400 mb-1">
                    {formatCurrencyVND(cellphonesPrice)}
                  </div>
                  <div 
                    className="w-full rounded-t-lg bg-rose-500 hover:bg-rose-600 transition-all shadow-md flex items-end justify-center pb-2"
                    style={{ height: `${getBarHeight(cellphonesPrice)}%` }}
                  >
                    <span className="text-[10px] font-bold text-white tracking-tighter">
                      {cellphonesInStock ? 'Còn hàng' : 'Hết'}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-2 text-center">
                    CellphoneS
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {cellphonesInStock ? (
                      <span className="text-emerald-500">Còn hàng</span>
                    ) : (
                      <span className="text-slate-400">Hết hàng</span>
                    )}
                  </div>
                </div>

                {/* Bar 4: Hoàng Hà Mobile */}
                <div className="flex-1 flex flex-col items-center h-full justify-end max-w-[120px]">
                  <div className="text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-400 mb-1">
                    {formatCurrencyVND(hoanghaPrice)}
                  </div>
                  <div 
                    className="w-full rounded-t-lg bg-emerald-500 hover:bg-emerald-600 transition-all shadow-md flex items-end justify-center pb-2"
                    style={{ height: `${getBarHeight(hoanghaPrice)}%` }}
                  >
                    <span className="text-[10px] font-bold text-white tracking-tighter">
                      {hoanghaInStock ? 'Còn hàng' : 'Hết'}
                    </span>
                  </div>
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mt-2 text-center">
                    Hoàng Hà
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {hoanghaInStock ? (
                      <span className="text-emerald-500">Còn hàng</span>
                    ) : (
                      <span className="text-slate-400">Hết hàng</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Lựa Chọn Giá / Tự Config Giá */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-1.5">
              <span>3. Quyết định mức giá áp dụng</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Option A: Dùng giá đề xuất AI */}
              <label 
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  priceMode === 'SUGGESTED'
                    ? 'border-orange-500 bg-orange-50/20 dark:bg-orange-950/20 ring-1 ring-orange-500/50'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50/50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name="priceMode"
                    checked={priceMode === 'SUGGESTED'}
                    onChange={() => setPriceMode('SUGGESTED')}
                    className="mt-1 text-orange-600 focus:ring-orange-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <Bot className="w-3.5 h-3.5 text-blue-500" />
                        <span>Dùng giá đề xuất AI</span>
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                        Khuyến nghị
                      </span>
                    </div>
                    <div className="text-lg font-black font-mono text-orange-600 dark:text-orange-400 mt-2">
                      {formatCurrencyVND(recommendation.suggested_price)}
                    </div>
                    <div className="text-[11px] text-slate-500 mt-1">
                      Biên lợi nhuận dự kiến: <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatPercent(recommendation.margin_impact_percent)}</span>
                    </div>
                  </div>
                </div>
              </label>

              {/* Option B: Tự cấu hình giá mới */}
              <label 
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  priceMode === 'CUSTOM'
                    ? 'border-orange-500 bg-orange-50/20 dark:bg-orange-950/20 ring-1 ring-orange-500/50'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50/50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name="priceMode"
                    checked={priceMode === 'CUSTOM'}
                    onChange={() => setPriceMode('CUSTOM')}
                    className="mt-1 text-orange-600 focus:ring-orange-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <Sliders className="w-3.5 h-3.5 text-purple-500" />
                        <span>Tự cấu hình giá mới</span>
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
                        Chỉnh tay
                      </span>
                    </div>

                    <div className="mt-2">
                      <div className="relative">
                        <input
                          type="number"
                          step={10000}
                          value={customPrice}
                          disabled={priceMode !== 'CUSTOM'}
                          onChange={(e) => setCustomPrice(Number(e.target.value))}
                          className="w-full text-base font-black font-mono px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500 disabled:opacity-50"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 font-bold">
                          VND
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                        <span>Biên lợi nhuận: <span className="font-bold text-emerald-600 dark:text-emerald-400">{formatPercent(activeMarginPercent)}</span></span>
                        <span className="font-mono text-[10px]">
                          {priceDiffVsCurrent > 0 ? '+' : ''}{formatCurrencyVND(priceDiffVsCurrent)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </label>
            </div>

            {/* Floor Price Guard Warning */}
            {isBelowFloor && (
              <div className="mt-3 p-3 rounded-xl border border-pink-300 dark:border-pink-900 bg-pink-50 dark:bg-pink-950/40 text-pink-700 dark:text-pink-300 flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-pink-600 dark:text-pink-400 flex-shrink-0 mt-0.5" />
                <div className="text-xs flex-1">
                  <div className="font-bold">Cảnh báo vi phạm Giá sàn bảo vệ (Floor Price Guard)!</div>
                  <div className="text-[11px] text-pink-600/90 dark:text-pink-400/90 mt-0.5">
                    Mức giá bạn nhập ({formatCurrencyVND(customPrice)}) thấp hơn giá sàn an toàn ({formatCurrencyVND(recommendation.floor_price)} - Vốn + 5%). Việc bán dưới giá sàn sẽ làm thâm hụt lợi nhuận gộp.
                  </div>
                  <label className="mt-2 flex items-center gap-2 cursor-pointer font-semibold text-[11px]">
                    <input
                      type="checkbox"
                      checked={overrideFloor}
                      onChange={(e) => setOverrideFloor(e.target.checked)}
                      className="rounded border-pink-400 text-pink-600 focus:ring-pink-500"
                    />
                    <span>Xác nhận ngoại lệ ghi đè giá sàn bảo vệ (Yêu cầu quyền Quản lý)</span>
                  </label>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
          <button
            onClick={() => onReject(recommendation.id)}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition"
          >
            Từ chối đề xuất
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
            >
              Hủy / Đóng
            </button>
            <button
              onClick={handleApplyClick}
              disabled={isBelowFloor && !overrideFloor}
              className={`flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-bold text-white shadow-sm transition-all active:scale-95 ${
                isBelowFloor && !overrideFloor
                  ? 'bg-slate-300 dark:bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-orange-600 hover:bg-orange-700 shadow-orange-600/30'
              }`}
            >
              <Check className="w-4 h-4" />
              <span>Phê duyệt &amp; Áp dụng giá này</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
