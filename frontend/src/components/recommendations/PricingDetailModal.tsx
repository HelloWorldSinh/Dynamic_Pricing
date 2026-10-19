import React, { useState, useEffect } from 'react';
import { 
  X, 
  ShieldCheck, 
  AlertTriangle, 
  Check, 
  Bot, 
  Sliders, 
  BarChart3, 
  TrendingDown,
  TrendingUp,
  Info
} from 'lucide-react';
import { PricingRecommendation } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface PricingDetailModalProps {
  recommendation: PricingRecommendation | null;
  onClose: () => void;
  onApply: (id: string, finalPrice: number, changeType: 'AI_RECOMMENDED' | 'MANUAL_CONFIG') => void;
  onReject: (id: string) => void;
}

// Chuyển đổi văn bản không dấu hoặc thông báo kỹ thuật tiếng Anh sang tiếng Việt có dấu chuẩn xác
function formatVietnameseText(text?: string): string {
  if (!text) return '';
  let res = text;
  // Specific mappings for reasoning_3layers
  res = res.replace(/Nhu cau thi truong o muc tieu chuan \(Neutral\)\./gi, 'Nhu cầu thị trường ở mức tiêu chuẩn (Neutral).');
  res = res.replace(/Nhu cau thi truong/gi, 'Nhu cầu thị trường');
  res = res.replace(/o muc tieu chuan/gi, 'ở mức tiêu chuẩn');
  res = res.replace(/Luu luong quan tam:/gi, 'Lưu lượng quan tâm:');
  res = res.replace(/\bviews\b/gi, 'lượt xem');
  res = res.replace(/\bgio hang\b/gi, 'giỏ hàng');
  res = res.replace(/Doi thu\s+/gi, 'Đối thủ ');
  res = res.replace(/\s+dang ban re hon\s+/gi, ' đang bán rẻ hơn ');
  res = res.replace(/\s+dang ban cao hon\s+/gi, ' đang bán cao hơn ');
  res = res.replace(/Tat ca doi thu chinh\s+/gi, 'Tất cả đối thủ chính ');
  res = res.replace(/\s+deu dang het hang\s+/gi, ' đều đang hết hàng ');
  res = res.replace(/Chua co du lieu gia doi thu doi soat\./gi, 'Chưa có dữ liệu giá đối thủ đối soát.');
  res = res.replace(/Muc gia de xuat da duoc dieu chinh ve muc gia san de bao toan bien loi nhuan an toan\./gi, 'Mức giá đề xuất đã được điều chỉnh về mức giá sàn để bảo toàn biên lợi nhuận an toàn.');
  res = res.replace(/Muc gia de xuat nam trong nguong an toan tren muc gia san\./gi, 'Mức giá đề xuất nằm trong ngưỡng an toàn trên mức giá sàn.');
  res = res.replace(/Canh bao hang ton kho loi thoi/gi, 'Cảnh báo hàng tồn kho lỗi thời');
  res = res.replace(/Hang ton kho u dong cao/gi, 'Hàng tồn kho ứ đọng cao');
  res = res.replace(/Hang khan hiem sap het/gi, 'Hàng khan hiếm sắp hết');
  res = res.replace(/Ton kho on dinh/gi, 'Tồn kho ổn định');
  res = res.replace(/\bngay\b/gi, 'ngày');
  res = res.replace(/\bso luong=/gi, 'số lượng=');
  res = res.replace(/\bluong ton=/gi, 'lượng tồn=');
  res = res.replace(/\bluong ton kha dung=/gi, 'lượng tồn khả dụng=');
  // Guardrail english warnings
  res = res.replace(/Margin floor protection activated: Price capped at floor_price/gi, 'Kích hoạt cơ chế bảo vệ giá sàn: Mức giá được chặn ở mức giá sàn an toàn');
  res = res.replace(/Predatory pricing warning: Competitor price is below 80% of cost price/gi, 'Cảnh báo bán phá giá (Predatory Pricing): Giá đối thủ thấp hơn 80% giá vốn');
  return res;
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

  // Derived competitor prices
  const fptCurrentPrice = recommendation.current_price;
  const cellphonesPrice = recommendation.cellphones_price || recommendation.min_competitor_price;
  const cellphonesInStock = recommendation.cellphones_in_stock !== false;
  const hoanghaPrice = recommendation.hoangha_price || Math.round(recommendation.min_competitor_price * 1.005);
  const hoanghaInStock = recommendation.hoangha_in_stock !== false;

  // Active chosen price
  const activePrice = priceMode === 'SUGGESTED' ? recommendation.suggested_price : customPrice;
  const isBelowFloor = activePrice < recommendation.floor_price;

  // Accurate Financial Calculations
  const priceDiffVsCurrent = activePrice - fptCurrentPrice;
  const priceDiffPercent = fptCurrentPrice > 0 ? (priceDiffVsCurrent / fptCurrentPrice) * 100 : 0;
  const profitPerUnit = activePrice - recommendation.cost_price;
  const activeMarginPercent = activePrice > 0 ? (profitPerUnit / activePrice) * 100 : 0;

  // Horizontal Price Positioning Bar calculations
  // Dùng thang đo chuẩn từ 0 đến maxVal (Zero-based scale) để bảo toàn tỉ lệ thực tế giữa các mức giá
  const allPrices = [
    recommendation.cost_price,
    recommendation.floor_price,
    hoanghaPrice,
    cellphonesPrice,
    activePrice,
    fptCurrentPrice,
  ].filter((p): p is number => typeof p === 'number' && p > 0);

  const maxVal = allPrices.length > 0 ? Math.max(...allPrices) : 1;
  // Khoảng đệm an toàn 6% bên phải để thanh dài nhất không chạm mép khung
  const scaleMax = maxVal * 1.06;

  const getPositionPercent = (val: number) => {
    if (!val || val <= 0) return 0;
    return Math.max(1, Math.min(100, (val / scaleMax) * 100));
  };

  const floorPositionPercent = getPositionPercent(recommendation.floor_price);

  const priceRows = [
    {
      label: 'Giá vốn (Cost)',
      value: recommendation.cost_price,
      barColor: 'bg-slate-400 dark:bg-slate-500',
      textColor: 'text-slate-600 dark:text-slate-400',
      badge: null,
    },
    {
      label: 'Giá sàn bảo vệ',
      value: recommendation.floor_price,
      barColor: 'bg-pink-500',
      textColor: 'text-pink-600 dark:text-pink-400 font-bold',
      badge: 'Vốn + 5%',
      isFloor: true,
    },
    {
      label: 'Hoàng Hà',
      value: hoanghaPrice,
      barColor: 'bg-emerald-500',
      textColor: 'text-emerald-600 dark:text-emerald-400 font-semibold',
      badge: hoanghaInStock ? 'Còn hàng' : 'Hết',
    },
    {
      label: 'CellphoneS',
      value: cellphonesPrice,
      barColor: 'bg-rose-500',
      textColor: 'text-rose-600 dark:text-rose-400 font-semibold',
      badge: cellphonesInStock ? 'Còn hàng' : 'Hết',
    },
    {
      label: 'Giá FPT Mới (Đề xuất)',
      value: activePrice,
      barColor: 'bg-orange-500 ring-2 ring-orange-500/30',
      textColor: 'text-orange-600 dark:text-orange-400 font-black',
      badge: priceMode === 'SUGGESTED' ? 'AI' : 'Chỉnh tay',
      isProposed: true,
    },
    {
      label: 'Giá FPT Hiện tại',
      value: fptCurrentPrice,
      barColor: 'bg-slate-500 dark:bg-slate-400',
      textColor: 'text-slate-700 dark:text-slate-300 font-medium',
      badge: 'Baseline',
    },
  ];

  const handleApplyClick = () => {
    if (isBelowFloor && !overrideFloor) return;
    onApply(
      recommendation.id,
      activePrice,
      priceMode === 'SUGGESTED' ? 'AI_RECOMMENDED' : 'MANUAL_CONFIG'
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/70 backdrop-blur-xs animate-in fade-in duration-200">
      <div 
        className="w-full max-w-6xl xl:max-w-7xl max-h-[92vh] flex flex-col rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 1. Modal Header: Inline SKU, Title, and Scenario Badge */}
        <div className="flex items-center justify-between px-6 py-3.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <span className="p-1.5 rounded-lg bg-orange-600/10 text-orange-600 dark:text-orange-400 shrink-0">
              <BarChart3 className="w-4 h-4" />
            </span>
            <div className="flex items-center gap-2.5 flex-wrap min-w-0">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white shrink-0">
                Căn Cứ &amp; Cấu Hình Định Giá
              </h2>
              <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 shrink-0">
                {recommendation.sku}
              </span>
              <span className="text-xs text-slate-500 font-medium truncate max-w-sm">
                {recommendation.product_name}
              </span>
              <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900/60 shrink-0">
                {recommendation.scenario}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800 transition shrink-0"
            title="Đóng modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 2-Column Body Layout */}
        <div className="flex-1 overflow-y-auto p-5 grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* ================= LEFT COLUMN (56% / 7 cols) ================= */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            {/* Guardrail & Scenario Alert Box */}
            <div className="p-3.5 rounded-xl border border-blue-100 dark:border-blue-900/40 bg-blue-50/25 dark:bg-blue-950/15">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                  <Bot className="w-3.5 h-3.5" />
                  <span>Phân tích căn cứ &amp; Tín hiệu thị trường</span>
                </span>
                <span className="text-[10px] font-medium text-slate-400">
                  3 lớp Guardrails
                </span>
              </div>

              <div className="space-y-2 text-xs">
                {/* Demand Signal */}
                <div className="flex items-start gap-2 p-2 rounded-lg bg-white/80 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 shrink-0">
                    Nhu cầu
                  </span>
                  <span className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
                    {formatVietnameseText(recommendation.reasoning_3layers?.market_demand_factor) || 'Lực cầu thị trường ổn định, cần duy trì sức cạnh tranh so với đối thủ.'}
                  </span>
                </div>

                {/* Competitor Signal */}
                <div className="flex items-start gap-2 p-2 rounded-lg bg-white/80 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-100 dark:bg-rose-900/60 text-rose-700 dark:text-rose-300 shrink-0">
                    Đối thủ
                  </span>
                  <span className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
                    {formatVietnameseText(recommendation.reasoning_3layers?.competitor_factor) || `Đối thủ thấp nhất hiện tại: ${formatCurrencyVND(recommendation.min_competitor_price)}.`}
                  </span>
                </div>

                {/* Floor Guardrail Signal */}
                <div className="flex items-start gap-2 p-2 rounded-lg bg-white/80 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-pink-100 dark:bg-pink-900/60 text-pink-700 dark:text-pink-300 shrink-0">
                    Giá sàn
                  </span>
                  <span className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed">
                    {formatVietnameseText(recommendation.reasoning_3layers?.floor_protection_factor) || `Giá sàn bảo vệ tối thiểu ${formatCurrencyVND(recommendation.floor_price)} (Giá vốn + 5% markup).`}
                  </span>
                </div>
              </div>
            </div>

            {/* Horizontal Price Positioning Bar (Replaces bulky 4-bar vertical chart) */}
            <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex-1 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Định Vị Tương Quan Giá Bán 6 Điểm Cốt Lõi
                </span>
                <span className="text-[10px] font-mono text-pink-600 dark:text-pink-400 bg-pink-50 dark:bg-pink-950/50 px-2.5 py-0.5 rounded border border-pink-200 dark:border-pink-900/60 font-semibold">
                  Ngưỡng sàn: {formatCurrencyVND(recommendation.floor_price)}
                </span>
              </div>

              {/* Bullet rows with horizontal positioning tracks */}
              <div className="space-y-2.5 pt-1">
                {priceRows.map((row, idx) => {
                  const pos = getPositionPercent(row.value);
                  return (
                    <div key={idx} className="flex items-center text-xs group">
                      {/* Row Label (No truncation, comfortable width) */}
                      <div className="w-[205px] shrink-0 text-[11px] font-medium text-slate-700 dark:text-slate-300 flex items-center justify-between pr-3">
                        <span className="whitespace-nowrap font-medium">{row.label}</span>
                        {row.badge && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-mono font-semibold shrink-0 ml-1.5">
                            {row.badge}
                          </span>
                        )}
                      </div>

                      {/* Bar Track Container with responsive guideline */}
                      <div className="flex-1 relative h-3.5 flex items-center">
                        {/* Guideline line cutting vertically through this track */}
                        <div 
                          className="absolute -top-1 -bottom-1 w-0 border-l border-dashed border-pink-400 dark:border-pink-500 z-10 pointer-events-none"
                          style={{ left: `${floorPositionPercent}%` }}
                        />
                        {/* Track background */}
                        <div className="w-full h-full bg-slate-100 dark:bg-slate-800 rounded-md overflow-hidden flex items-center">
                          <div
                            className={`h-full rounded-md transition-all duration-300 ${row.barColor}`}
                            style={{ width: `${pos}%` }}
                          />
                        </div>
                      </div>

                      {/* Formatted Price */}
                      <div className="w-[115px] shrink-0 text-right pl-3">
                        <span className={`text-[11px] font-mono ${row.textColor}`}>
                          {row.value > 0 ? formatCurrencyVND(row.value) : '—'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Compact Signal Cards (4-Grid Row) */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {/* Card 1: Composite Score */}
              <div className="p-2.5 rounded-xl border border-orange-200 dark:border-orange-800/60 bg-orange-50/20 dark:bg-orange-950/15">
                <div className="text-[9px] text-orange-600 dark:text-orange-400 font-bold uppercase tracking-wider">
                  Composite Score
                </div>
                <div className="text-sm font-black font-mono text-orange-600 dark:text-orange-400 mt-0.5">
                  {(recommendation.composite_score ?? 0) > 0 ? `+${(recommendation.composite_score ?? 0).toFixed(2)}` : (recommendation.composite_score ?? 0).toFixed(2)}
                </div>
                <div className="text-[9px] text-slate-400 leading-tight">0.4D + 0.35I + 0.25C</div>
              </div>

              {/* Card 2: Demand (D) */}
              <div className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[9px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
                  Demand (Cầu: D)
                </div>
                <div className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {(recommendation.demand_score ?? 0) > 0 ? `+${recommendation.demand_score}` : (recommendation.demand_score ?? 0)}
                </div>
                <div className="text-[9px] text-slate-400 leading-tight">Thang -2 đến +2</div>
              </div>

              {/* Card 3: Inventory (I) */}
              <div className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[9px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
                  Inventory (Kho: I)
                </div>
                <div className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {recommendation.inventory_quantity} máy
                </div>
                <div className="text-[9px] text-slate-400 leading-tight">
                  <span className={recommendation.doh > 45 ? 'text-rose-500 font-bold' : ''}>
                    {recommendation.doh} ngày DOH
                  </span>
                </div>
              </div>

              {/* Card 4: Competitor (C) */}
              <div className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-[9px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">
                  Competitor (C)
                </div>
                <div className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {(recommendation.competitor_score ?? 0) > 0 ? `+${recommendation.competitor_score}` : (recommendation.competitor_score ?? 0)}
                </div>
                <div className="text-[9px] text-slate-400 leading-tight">Thang -2 đến +2</div>
              </div>
            </div>
          </div>

          {/* ================= RIGHT COLUMN (45% / 5 cols) ================= */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-4">
            {/* Pricing Decision Options (Stacked Vertically) */}
            <div className="space-y-3">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 block">
                Quyết Định Mức Giá Áp Dụng
              </span>

              {/* Option 1: Dùng giá đề xuất AI */}
              <label 
                className={`p-3.5 rounded-xl border cursor-pointer transition-all block ${
                  priceMode === 'SUGGESTED'
                    ? 'border-orange-500 bg-orange-50/20 dark:bg-orange-950/20 ring-1 ring-orange-500/50 shadow-xs'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50/50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name="modalPriceMode"
                    checked={priceMode === 'SUGGESTED'}
                    onChange={() => setPriceMode('SUGGESTED')}
                    className="mt-1 text-orange-600 focus:ring-orange-500 cursor-pointer"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <Bot className="w-3.5 h-3.5 text-blue-500" />
                        <span>Dùng giá đề xuất AI</span>
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300">
                        Khuyến nghị
                      </span>
                    </div>

                    <div className="text-lg font-black font-mono text-orange-600 dark:text-orange-400 mt-1">
                      {formatCurrencyVND(recommendation.suggested_price)}
                    </div>
                  </div>
                </div>
              </label>

              {/* Option 2: Tự cấu hình giá mới */}
              <label 
                className={`p-3.5 rounded-xl border cursor-pointer transition-all block ${
                  priceMode === 'CUSTOM'
                    ? 'border-orange-500 bg-orange-50/20 dark:bg-orange-950/20 ring-1 ring-orange-500/50 shadow-xs'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50/50 dark:hover:bg-slate-800/40'
                }`}
              >
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    name="modalPriceMode"
                    checked={priceMode === 'CUSTOM'}
                    onChange={() => setPriceMode('CUSTOM')}
                    className="mt-1 text-orange-600 focus:ring-orange-500 cursor-pointer"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                        <Sliders className="w-3.5 h-3.5 text-purple-500" />
                        <span>Tự cấu hình giá mới</span>
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300">
                        Chỉnh tay
                      </span>
                    </div>

                    {/* Currency Input */}
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

                    {/* Quick-fill chips */}
                    <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          setPriceMode('CUSTOM');
                          setCustomPrice(recommendation.floor_price);
                        }}
                        className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition font-medium border border-slate-200 dark:border-slate-700"
                      >
                        = Bằng giá sàn ({formatCurrencyVND(recommendation.floor_price)})
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          setPriceMode('CUSTOM');
                          setCustomPrice(recommendation.min_competitor_price);
                        }}
                        className="text-[10px] px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition font-medium border border-slate-200 dark:border-slate-700"
                      >
                        = Đối thủ thấp nhất ({formatCurrencyVND(recommendation.min_competitor_price)})
                      </button>
                    </div>
                  </div>
                </div>
              </label>
            </div>

            {/* Live Financial Impact Simulator Box */}
            <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/30 space-y-2.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-orange-500" />
                <span>Mô Phỏng Tác Động Tài Chính (Live Simulator)</span>
              </span>

              {/* 3 Metric Cards */}
              <div className="space-y-2">
                {/* Metric 1: Mức điều chỉnh giá so với hiện tại */}
                <div className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs">
                  <span className="text-slate-500 font-medium">Mức điều chỉnh giá:</span>
                  <div className="flex items-center gap-1 font-mono font-bold">
                    {priceDiffVsCurrent < 0 ? (
                      <span className="text-rose-600 dark:text-rose-400 flex items-center gap-0.5">
                        <TrendingDown className="w-3.5 h-3.5" />
                        {formatCurrencyVND(priceDiffVsCurrent)} ({priceDiffPercent.toFixed(1)}%)
                      </span>
                    ) : priceDiffVsCurrent > 0 ? (
                      <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
                        <TrendingUp className="w-3.5 h-3.5" />
                        +{formatCurrencyVND(priceDiffVsCurrent)} (+{priceDiffPercent.toFixed(1)}%)
                      </span>
                    ) : (
                      <span className="text-slate-500">Giữ nguyên (0.0%)</span>
                    )}
                  </div>
                </div>

                {/* Metric 2: Biên lợi nhuận gộp dự kiến */}
                <div className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs">
                  <span className="text-slate-500 font-medium">Biên lợi nhuận dự kiến:</span>
                  <div className="flex items-center gap-1.5 font-mono">
                    <span className={`font-bold ${activeMarginPercent >= 15 ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'}`}>
                      {formatPercent(activeMarginPercent)}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      ({formatCurrencyVND(profitPerUnit)}/SP)
                    </span>
                  </div>
                </div>

                {/* Metric 3: Trạng thái giá sàn */}
                <div className="flex items-center justify-between p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs">
                  <span className="text-slate-500 font-medium">Trạng thái Giá sàn:</span>
                  {!isBelowFloor ? (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" />
                      <span>Đạt chuẩn bảo vệ sàn</span>
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-pink-50 dark:bg-pink-950/40 text-pink-600 dark:text-pink-400 border border-pink-200 dark:border-pink-800 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      <span>Thấp hơn giá sàn</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Warning if below floor */}
              {isBelowFloor && (
                <div className="p-2.5 rounded-lg border border-pink-300 dark:border-pink-900 bg-pink-50 dark:bg-pink-950/40 text-pink-700 dark:text-pink-300 text-xs">
                  <div className="font-bold flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-pink-600" />
                    <span>Cảnh báo vi phạm Giá sàn bảo vệ!</span>
                  </div>
                  <div className="text-[10px] text-pink-600/90 dark:text-pink-400/90 mt-0.5">
                    Giá thiết lập thấp hơn giá sàn ({formatCurrencyVND(recommendation.floor_price)}). Bán dưới giá sàn sẽ thâm hụt margin.
                  </div>
                  <label className="mt-2 flex items-center gap-2 cursor-pointer font-semibold text-[11px]">
                    <input
                      type="checkbox"
                      checked={overrideFloor}
                      onChange={(e) => setOverrideFloor(e.target.checked)}
                      className="rounded border-pink-400 text-pink-600 focus:ring-pink-500 w-3.5 h-3.5 cursor-pointer"
                    />
                    <span>Xác nhận ngoại lệ ghi đè giá sàn bảo vệ</span>
                  </label>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 3. Modal Footer Actions */}
        <div className="flex items-center justify-between px-6 py-3.5 border-t border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 shrink-0">
          <button
            type="button"
            onClick={() => onReject(recommendation.id)}
            className="px-3.5 py-2 rounded-lg text-xs font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition"
          >
            Từ chối đề xuất
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
            >
              Hủy / Đóng
            </button>
            <button
              type="button"
              onClick={handleApplyClick}
              disabled={isBelowFloor && !overrideFloor}
              className={`flex items-center gap-1.5 px-5 py-2 rounded-lg text-xs font-bold text-white shadow-xs transition-all active:scale-95 ${
                isBelowFloor && !overrideFloor
                  ? 'bg-slate-300 dark:bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-orange-600 hover:bg-orange-700 shadow-orange-600/30 cursor-pointer'
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
