import React from 'react';
import { PriceChangeHistoryItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';
import { Modal } from '../common/Modal';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

interface ProductPriceHistoryModalProps {
  sku: string | null;
  items: PriceChangeHistoryItem[];
  onClose: () => void;
}

export const ProductPriceHistoryModal: React.FC<ProductPriceHistoryModalProps> = ({
  sku,
  items,
  onClose,
}) => {
  if (!sku) return null;

  const productHistory = items
    .filter((i) => i.sku === sku)
    .sort((a, b) => new Date(b.changed_at).getTime() - new Date(a.changed_at).getTime());

  if (productHistory.length === 0) return null;

  const latest = productHistory[0];
  const oldest = productHistory[productHistory.length - 1];
  const totalChange = latest.new_price - oldest.old_price;
  const totalChangePercent = Math.round((totalChange / oldest.old_price) * 1000) / 10;

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

  // Sparkline coordinates calculation
  const chronologicalHistory = [...productHistory].reverse();
  const prices = chronologicalHistory.map((h) => h.new_price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;
  const sparkWidth = 260;
  const sparkHeight = 44;
  const points = prices.map((p, idx) => {
    const x = idx === 0 ? 4 : (idx / (prices.length - 1 || 1)) * (sparkWidth - 8) + 4;
    const y = sparkHeight - ((p - minPrice) / priceRange) * (sparkHeight - 12) - 6;
    return `${x},${y}`;
  }).join(' ');

  return (
    <Modal
      isOpen={!!sku}
      onClose={onClose}
      title={latest.product_name}
      subtitle={`SKU: ${latest.sku} | DANH MỤC: ${latest.category} | ${productHistory.length} LẦN ĐIỀU CHỈNH GIÁ`}
      maxWidth="2xl"
    >
      <div className="space-y-4">
        {/* Sparkline & Overview Stats Strip */}
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs w-full sm:w-auto">
            <div>
              <div className="text-2xs font-mono uppercase text-slate-400">Giá ban đầu</div>
              <div className="font-mono font-bold text-slate-600 dark:text-slate-400 line-through">
                {formatCurrencyVND(oldest.old_price)}
              </div>
            </div>

            <div>
              <div className="text-2xs font-mono uppercase text-slate-400">Giá hiện tại</div>
              <div className="font-mono font-bold text-orange-600 dark:text-orange-400 text-sm">
                {formatCurrencyVND(latest.new_price)}
              </div>
            </div>

            <div>
              <div className="text-2xs font-mono uppercase text-slate-400">Tổng biến động</div>
              <div className={`font-mono font-bold text-xs ${totalChange < 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                {totalChange > 0 ? '+' : ''}{formatCurrencyVND(totalChange)} ({formatPercent(totalChangePercent)})
              </div>
            </div>
          </div>

          {/* SVG Sparkline */}
          {prices.length > 1 && (
            <div className="flex flex-col items-center sm:items-end shrink-0">
              <span className="text-2xs font-mono text-slate-400 mb-1">XU HƯỚNG BIẾN ĐỘNG</span>
              <svg width={sparkWidth} height={sparkHeight} className="overflow-visible">
                <polyline
                  fill="none"
                  stroke={totalChange < 0 ? '#e11d48' : '#059669'}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={points}
                />
                {chronologicalHistory.map((_, idx) => {
                  const [px, py] = points.split(' ')[idx].split(',');
                  return (
                    <circle
                      key={idx}
                      cx={px}
                      cy={py}
                      r="3"
                      className="fill-white stroke-orange-600 stroke-2"
                    />
                  );
                })}
              </svg>
            </div>
          )}
        </div>

        {/* Timeline Header */}
        <div className="text-2xs font-mono font-bold uppercase tracking-wider text-slate-400">
          [ DÒNG THỜI GIAN ĐIỀU CHỈNH GIÁ ]
        </div>

        {/* Timeline Items */}
        <div className="relative border-l border-slate-200 dark:border-slate-800 ml-3 space-y-4 py-1 max-h-[50vh] overflow-y-auto pr-2">
          {productHistory.map((rev, idx) => {
            const isLatest = idx === 0;
            const isDecrease = rev.price_change < 0;

            return (
              <div key={rev.id} className="relative pl-5 group">
                {/* Timeline Node Dot */}
                <div
                  className={`absolute -left-[5px] top-2 w-2.5 h-2.5 rounded-full border border-white dark:border-slate-900 ${
                    isLatest ? 'bg-orange-600' : 'bg-slate-400 dark:bg-slate-600'
                  }`}
                />

                <div
                  className={`p-3.5 rounded-xl border transition-all ${
                    isLatest
                      ? 'border-orange-300 dark:border-orange-800/80 bg-orange-50/20 dark:bg-orange-950/20'
                      : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2 border-b border-slate-100 dark:border-slate-800">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900 dark:text-white">
                        Lần #{productHistory.length - idx}
                      </span>
                      {isLatest && (
                        <Badge size="sm" variant="warning">
                          MỚI NHẤT
                        </Badge>
                      )}
                      <span className="text-2xs text-slate-400 font-mono">
                        {formatDateTime(rev.changed_at)}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Badge
                        size="sm"
                        variant={rev.change_type === 'AI_RECOMMENDED' ? 'info' : 'neutral'}
                      >
                        {rev.change_type === 'AI_RECOMMENDED' ? 'ĐỀ XUẤT AI' : 'CHỈNH TAY'}
                      </Badge>
                      <Badge size="sm" variant="success">
                        ĐỒNG BỘ POS
                      </Badge>
                    </div>
                  </div>

                  {/* Price Comparison */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 items-center text-xs">
                    <div>
                      <span className="text-2xs font-mono text-slate-400">GIÁ: </span>
                      <span className="font-mono text-slate-400 line-through">
                        {formatCurrencyVND(rev.old_price)}
                      </span>
                      <span className="mx-1 text-slate-400">→</span>
                      <span className="font-mono font-bold text-slate-900 dark:text-white">
                        {formatCurrencyVND(rev.new_price)}
                      </span>
                    </div>

                    <div className="flex sm:justify-end items-center gap-2">
                      <Badge size="sm" variant={isDecrease ? 'danger' : 'success'}>
                        {rev.price_change > 0 ? '+' : ''}{formatCurrencyVND(rev.price_change)} ({formatPercent(rev.price_change_percent)})
                      </Badge>
                      <Badge size="sm" variant="neutral">
                        BIÊN LN: {formatPercent(rev.margin_percent)}
                      </Badge>
                    </div>
                  </div>

                  <div className="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-2xs text-slate-500">
                    <div>
                      <strong className="font-semibold text-slate-700 dark:text-slate-300">Căn cứ: </strong>
                      {rev.scenario}
                    </div>
                    <div>
                      Bởi: <span className="font-mono font-medium text-slate-700 dark:text-slate-300">{rev.changed_by}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Audit Note & Close */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100 dark:border-slate-800">
          <span className="text-2xs font-mono text-slate-400">
            [ NHẬT KÝ KIỂM TOÁN - DỮ LIỆU ĐÃ ĐƯỢC KÝ SỐ POS ]
          </span>
          <Button size="sm" variant="secondary" onClick={onClose}>
            Đóng
          </Button>
        </div>
      </div>
    </Modal>
  );
};
