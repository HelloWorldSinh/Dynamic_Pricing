import React, { useState, useEffect } from 'react';
import { PricingRecommendation } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';
import { useAiChat } from '../../context/AiChatContext';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface PricingDetailModalProps {
  recommendation: PricingRecommendation | null;
  onClose: () => void;
  onApply: (id: string, finalPrice: number, changeType: 'AI_RECOMMENDED' | 'MANUAL_CONFIG') => void;
  onReject: (id: string) => void;
}

function formatVietnameseText(text?: string): string {
  if (!text) return '';
  let res = text;
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

  const { askExplanationForSku } = useAiChat();
  const [priceMode, setPriceMode] = useState<'SUGGESTED' | 'CUSTOM'>('SUGGESTED');
  const [customPrice, setCustomPrice] = useState<number>(recommendation.suggested_price);
  const [overrideFloor, setOverrideFloor] = useState<boolean>(false);

  useEffect(() => {
    if (recommendation) {
      setPriceMode('SUGGESTED');
      setCustomPrice(recommendation.suggested_price);
      setOverrideFloor(false);
    }
  }, [recommendation]);

  const fptCurrentPrice = recommendation.current_price;
  const cellphonesPrice = recommendation.cellphones_price || recommendation.min_competitor_price;
  const cellphonesInStock = recommendation.cellphones_in_stock !== false;
  const hoanghaPrice = recommendation.hoangha_price || Math.round(recommendation.min_competitor_price * 1.005);
  const hoanghaInStock = recommendation.hoangha_in_stock !== false;

  const activePrice = priceMode === 'SUGGESTED' ? recommendation.suggested_price : customPrice;
  const isBelowFloor = activePrice < recommendation.floor_price;

  const priceDiffVsCurrent = activePrice - fptCurrentPrice;
  const priceDiffPercent = fptCurrentPrice > 0 ? (priceDiffVsCurrent / fptCurrentPrice) * 100 : 0;
  const profitPerUnit = activePrice - recommendation.cost_price;
  const activeMarginPercent = activePrice > 0 ? (profitPerUnit / activePrice) * 100 : 0;

  const allPrices = [
    recommendation.cost_price,
    recommendation.floor_price,
    cellphonesPrice,
    hoanghaPrice,
    fptCurrentPrice,
    activePrice,
  ].filter((p) => typeof p === 'number' && p > 0);

  const maxVal = Math.max(...allPrices) * 1.05 || 1;

  const getPositionPercent = (val: number): number => {
    if (val <= 0) return 0;
    const pct = (val / maxVal) * 100;
    return Math.min(Math.max(pct, 4), 98);
  };

  const floorPositionPercent = getPositionPercent(recommendation.floor_price);

  const priceRows = [
    {
      label: 'Giá vốn (Cost Price)',
      badge: 'VỐN GỐC',
      value: recommendation.cost_price,
      barColor: 'bg-slate-400 dark:bg-slate-600',
      textColor: 'text-slate-600 dark:text-slate-400',
    },
    {
      label: 'Giá sàn bảo vệ (Floor Price)',
      badge: 'VỐN + 5%',
      value: recommendation.floor_price,
      barColor: 'bg-rose-500 dark:bg-rose-600',
      textColor: 'text-rose-600 dark:text-rose-400 font-bold',
    },
    {
      label: 'CellphoneS',
      badge: cellphonesInStock ? 'CÒN HÀNG' : 'HẾT HÀNG',
      value: cellphonesPrice,
      barColor: 'bg-amber-400 dark:bg-amber-500',
      textColor: 'text-amber-700 dark:text-amber-400 font-semibold',
    },
    {
      label: 'Hoàng Hà Mobile',
      badge: hoanghaInStock ? 'CÒN HÀNG' : 'HẾT HÀNG',
      value: hoanghaPrice,
      barColor: 'bg-amber-500 dark:bg-amber-600',
      textColor: 'text-amber-700 dark:text-amber-400 font-semibold',
    },
    {
      label: 'Giá FPT Shop hiện tại',
      badge: 'HIỆN TẠI',
      value: fptCurrentPrice,
      barColor: 'bg-blue-500 dark:bg-blue-600',
      textColor: 'text-blue-600 dark:text-blue-400 font-semibold',
    },
    {
      label: priceMode === 'SUGGESTED' ? 'Giá đề xuất AI' : 'Giá chỉnh tay',
      badge: priceMode === 'SUGGESTED' ? 'ĐỀ XUẤT' : 'CHỈNH TAY',
      value: activePrice,
      barColor: 'bg-orange-600 dark:bg-orange-500',
      textColor: 'text-orange-600 dark:text-orange-400 font-bold',
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
    <Modal
      isOpen={!!recommendation}
      onClose={onClose}
      title={recommendation.product_name}
      subtitle={`SKU: ${recommendation.sku} | DANH MỤC: ${recommendation.category} | KỊCH BẢN: ${recommendation.scenario || 'Tiêu chuẩn'}`}
      maxWidth="4xl"
    >
      <div className="space-y-4">
        {/* Guardrail & Scenario Alert Box */}
        <div className="p-3.5 rounded-xl border border-blue-200 dark:border-blue-900/40 bg-blue-50/20 dark:bg-blue-950/20">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xs font-mono font-bold uppercase tracking-wider text-blue-700 dark:text-blue-400">
              [ PHÂN TÍCH CĂN CỨ VÀ TÍN HIỆU THỊ TRƯỜNG - 3 LỚP GUARDRAILS ]
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => askExplanationForSku(recommendation.sku, recommendation.product_name)}
            >
              Hỏi AI Copilot
            </Button>
          </div>

          <div className="space-y-1.5 text-xs">
            <div className="flex items-start gap-2 p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
              <Badge size="sm" variant="info">NHU CẦU</Badge>
              <span className="text-slate-700 dark:text-slate-300 text-2xs leading-relaxed">
                {formatVietnameseText(recommendation.reasoning_3layers?.market_demand_factor) || 'Lực cầu thị trường ổn định, cần duy trì sức cạnh tranh so với đối thủ.'}
              </span>
            </div>

            <div className="flex items-start gap-2 p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
              <Badge size="sm" variant="warning">ĐỐI THỦ</Badge>
              <span className="text-slate-700 dark:text-slate-300 text-2xs leading-relaxed">
                {formatVietnameseText(recommendation.reasoning_3layers?.competitor_factor) || `Đối thủ thấp nhất hiện tại: ${formatCurrencyVND(recommendation.min_competitor_price)}.`}
              </span>
            </div>

            <div className="flex items-start gap-2 p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
              <Badge size="sm" variant="floor">GIÁ SÀN</Badge>
              <span className="text-slate-700 dark:text-slate-300 text-2xs leading-relaxed">
                {formatVietnameseText(recommendation.reasoning_3layers?.floor_protection_factor) || `Giá sàn bảo vệ tối thiểu ${formatCurrencyVND(recommendation.floor_price)} (Giá vốn + 5% markup).`}
              </span>
            </div>
          </div>
        </div>

        {/* 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column: Horizontal Positioning & Signals */}
          <div className="lg:col-span-7 flex flex-col space-y-4">
            {/* Horizontal Positioning Bar */}
            <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xs font-mono font-bold uppercase text-slate-500">
                  ĐỊNH VỊ TƯƠNG QUAN GIÁ 6 ĐIỂM
                </span>
                <span className="text-2xs font-mono text-rose-600 dark:text-rose-400 font-bold">
                  SÀN BẢO VỆ: {formatCurrencyVND(recommendation.floor_price)}
                </span>
              </div>

              <div className="space-y-2 pt-1">
                {priceRows.map((row, idx) => {
                  const pos = getPositionPercent(row.value);
                  return (
                    <div key={idx} className="flex items-center text-xs">
                      <div className="w-[185px] shrink-0 text-2xs font-medium text-slate-700 dark:text-slate-300 flex items-center justify-between pr-2">
                        <span className="truncate">{row.label}</span>
                        {row.badge && (
                          <span className="text-[10px] font-mono text-slate-400 shrink-0 ml-1">
                            {row.badge}
                          </span>
                        )}
                      </div>

                      <div className="flex-1 relative h-3 flex items-center">
                        <div 
                          className="absolute -top-1 -bottom-1 w-0 border-l border-dashed border-rose-400 dark:border-rose-500 z-10 pointer-events-none"
                          style={{ left: `${floorPositionPercent}%` }}
                        />
                        <div className="w-full h-full bg-slate-100 dark:bg-slate-800 rounded overflow-hidden flex items-center">
                          <div
                            className={`h-full rounded transition-all duration-200 ${row.barColor}`}
                            style={{ width: `${pos}%` }}
                          />
                        </div>
                      </div>

                      <div className="w-[105px] shrink-0 text-right pl-2">
                        <span className={`text-2xs font-mono ${row.textColor}`}>
                          {row.value > 0 ? formatCurrencyVND(row.value) : '—'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Compact Metric Signal Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-2.5 rounded-lg border border-orange-200 dark:border-orange-800/60 bg-orange-50/20 dark:bg-orange-950/20">
                <div className="text-2xs font-mono font-bold text-orange-600 uppercase">Score</div>
                <div className="text-sm font-bold font-mono text-orange-600 mt-0.5">
                  {(recommendation.composite_score ?? 0) > 0 ? `+${(recommendation.composite_score ?? 0).toFixed(2)}` : (recommendation.composite_score ?? 0).toFixed(2)}
                </div>
                <div className="text-[10px] text-slate-400">0.4D+0.35I+0.25C</div>
              </div>

              <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-2xs font-mono font-bold text-slate-500 uppercase">Demand (D)</div>
                <div className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {(recommendation.demand_score ?? 0) > 0 ? `+${recommendation.demand_score}` : (recommendation.demand_score ?? 0)}
                </div>
                <div className="text-[10px] text-slate-400">Thang -2 đến +2</div>
              </div>

              <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-2xs font-mono font-bold text-slate-500 uppercase">Inventory (I)</div>
                <div className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {recommendation.inventory_quantity} SP
                </div>
                <div className="text-[10px] text-slate-400">{recommendation.doh}d DOH</div>
              </div>

              <div className="p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <div className="text-2xs font-mono font-bold text-slate-500 uppercase">Competitor (C)</div>
                <div className="text-sm font-bold font-mono text-slate-800 dark:text-slate-200 mt-0.5">
                  {(recommendation.competitor_score ?? 0) > 0 ? `+${recommendation.competitor_score}` : (recommendation.competitor_score ?? 0)}
                </div>
                <div className="text-[10px] text-slate-400">Thang -2 đến +2</div>
              </div>
            </div>
          </div>

          {/* Right Column: Pricing Decision Options & Simulator */}
          <div className="lg:col-span-5 flex flex-col justify-between space-y-3">
            <div className="space-y-2">
              <span className="text-2xs font-mono font-bold uppercase text-slate-400">
                QUYẾT ĐỊNH MỨC GIÁ ÁP DỤNG
              </span>

              {/* Option 1: AI Suggested */}
              <label 
                className={`p-3 rounded-xl border cursor-pointer transition-all block ${
                  priceMode === 'SUGGESTED'
                    ? 'border-orange-500 bg-orange-50/20 dark:bg-orange-950/20 ring-1 ring-orange-500/50'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <input
                    type="radio"
                    name="modalPriceMode"
                    checked={priceMode === 'SUGGESTED'}
                    onChange={() => setPriceMode('SUGGESTED')}
                    className="mt-1 text-orange-600 focus:ring-orange-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">
                        DÙNG GIÁ ĐỀ XUẤT AI
                      </span>
                      <Badge size="sm" variant="info">KHUYẾN NGHỊ</Badge>
                    </div>
                    <div className="text-base font-bold font-mono text-orange-600 dark:text-orange-400 mt-1">
                      {formatCurrencyVND(recommendation.suggested_price)}
                    </div>
                  </div>
                </div>
              </label>

              {/* Option 2: Custom Price */}
              <label 
                className={`p-3 rounded-xl border cursor-pointer transition-all block ${
                  priceMode === 'CUSTOM'
                    ? 'border-orange-500 bg-orange-50/20 dark:bg-orange-950/20 ring-1 ring-orange-500/50'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <input
                    type="radio"
                    name="modalPriceMode"
                    checked={priceMode === 'CUSTOM'}
                    onChange={() => setPriceMode('CUSTOM')}
                    className="mt-1 text-orange-600 focus:ring-orange-500"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">
                        TỰ CẤU HÌNH GIÁ MỚI
                      </span>
                      <Badge size="sm" variant="neutral">CHỈNH TAY</Badge>
                    </div>

                    <div className="relative">
                      <input
                        type="number"
                        step={10000}
                        value={customPrice}
                        disabled={priceMode !== 'CUSTOM'}
                        onChange={(e) => setCustomPrice(Number(e.target.value))}
                        className="w-full text-sm font-bold font-mono px-3 py-1.5 rounded-md border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-orange-500 disabled:opacity-50"
                      />
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 text-2xs text-slate-400 font-bold font-mono">
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
                        className="text-2xs font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-orange-500"
                      >
                        [= GIÁ SÀN ({formatCurrencyVND(recommendation.floor_price)})]
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          setPriceMode('CUSTOM');
                          setCustomPrice(recommendation.min_competitor_price);
                        }}
                        className="text-2xs font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-orange-500"
                      >
                        [= ĐỐI THỦ THẤP NHẤT ({formatCurrencyVND(recommendation.min_competitor_price)})]
                      </button>
                    </div>
                  </div>
                </div>
              </label>
            </div>

            {/* Financial Simulator */}
            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 space-y-2">
              <span className="text-2xs font-mono font-bold uppercase text-slate-600 dark:text-slate-400">
                MÔ PHỎNG TÁC ĐỘNG TÀI CHÍNH
              </span>

              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-500 text-2xs">Điều chỉnh so với giá hiện tại:</span>
                  <span className={`font-mono font-bold text-2xs ${priceDiffVsCurrent < 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {priceDiffVsCurrent > 0 ? '+' : ''}{formatCurrencyVND(priceDiffVsCurrent)} ({priceDiffPercent.toFixed(1)}%)
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-500 text-2xs">Biên lợi nhuận dự kiến:</span>
                  <span className="font-mono font-bold text-2xs text-emerald-600">
                    {formatPercent(activeMarginPercent)} ({formatCurrencyVND(profitPerUnit)}/SP)
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-slate-500 text-2xs">Trạng thái Giá sàn:</span>
                  <Badge size="sm" variant={!isBelowFloor ? 'success' : 'danger'}>
                    {!isBelowFloor ? 'ĐẠT CHUẨN BẢO VỆ' : 'THẤP HƠN GIÁ SÀN'}
                  </Badge>
                </div>
              </div>

              {isBelowFloor && (
                <div className="p-2 rounded border border-rose-300 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 text-2xs">
                  <div className="font-bold">CẢNH BÁO VI PHẠM GIÁ SÀN BẢO VỆ</div>
                  <div className="mt-0.5">
                    Mức giá &lt; {formatCurrencyVND(recommendation.floor_price)} sẽ gây thâm hụt biên lợi nhuận cam kết.
                  </div>
                  <label className="mt-1.5 flex items-center gap-1.5 cursor-pointer font-bold">
                    <input
                      type="checkbox"
                      checked={overrideFloor}
                      onChange={(e) => setOverrideFloor(e.target.checked)}
                      className="rounded border-rose-400 text-rose-600 focus:ring-rose-500 w-3.5 h-3.5"
                    />
                    <span>Xác nhận ngoại lệ ghi đè giá sàn bảo vệ</span>
                  </label>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-800">
          <Button
            size="sm"
            variant="destructive"
            onClick={() => onReject(recommendation.id)}
          >
            Từ chối đề xuất
          </Button>

          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" onClick={onClose}>
              Đóng
            </Button>
            <Button
              size="sm"
              variant="primary"
              onClick={handleApplyClick}
              disabled={isBelowFloor && !overrideFloor}
            >
              Phê duyệt &amp; Áp dụng giá
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
