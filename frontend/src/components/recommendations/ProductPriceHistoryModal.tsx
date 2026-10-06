import React from 'react';
import { 
  X, 
  History, 
  ArrowRight, 
  TrendingDown, 
  TrendingUp, 
  Bot, 
  UserCheck, 
  CheckCircle2, 
  Calendar,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { PriceChangeHistoryItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

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

  // Filter history for this SKU and sort newest first
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between bg-slate-50/50 dark:bg-slate-950/50">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-xl bg-orange-500/10 text-orange-600 dark:text-orange-400 mt-0.5">
              <History className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-600 text-white uppercase tracking-wider">
                  {latest.category}
                </span>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-semibold">
                  {latest.sku}
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                  {productHistory.length} lần điều chỉnh giá
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white leading-snug">
                {latest.product_name}
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Overview Stats Strip */}
        <div className="p-4 px-6 bg-slate-50/80 dark:bg-slate-800/40 border-b border-slate-200 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <div className="text-[11px] text-slate-500">Giá ban đầu:</div>
            <div className="font-mono font-semibold text-slate-800 dark:text-slate-200 line-through">
              {formatCurrencyVND(oldest.old_price)}
            </div>
          </div>

          <div>
            <div className="text-[11px] text-slate-500">Giá hiện tại:</div>
            <div className="font-mono font-bold text-slate-900 dark:text-white">
              {formatCurrencyVND(latest.new_price)}
            </div>
          </div>

          <div>
            <div className="text-[11px] text-slate-500">Tổng biến động:</div>
            <div
              className={`font-mono font-bold flex items-center gap-1 ${
                totalChange < 0
                  ? 'text-rose-600 dark:text-rose-400'
                  : totalChange > 0
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : 'text-slate-600 dark:text-slate-400'
              }`}
            >
              <span>{totalChange > 0 ? '+' : ''}{formatCurrencyVND(totalChange)}</span>
              <span className="text-[10px]">({formatPercent(totalChangePercent)})</span>
            </div>
          </div>

          <div>
            <div className="text-[11px] text-slate-500">Biên LN hiện tại:</div>
            <div className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
              {formatPercent(latest.margin_percent)}
            </div>
          </div>
        </div>

        {/* Timeline Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs flex-1">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Layers className="w-3.5 h-3.5 text-orange-500" />
            <span>Dòng thời gian các lần điều chỉnh giá ({productHistory.length})</span>
          </div>

          <div className="relative border-l-2 border-slate-200 dark:border-slate-800 ml-3.5 space-y-5 py-1">
            {productHistory.map((rev, idx) => {
              const isLatest = idx === 0;
              const isDecrease = rev.price_change < 0;

              return (
                <div key={rev.id} className="relative pl-6 group">
                  {/* Timeline Node Dot */}
                  <div
                    className={`absolute -left-[9px] top-1.5 w-4 h-4 rounded-full border-2 border-white dark:border-slate-900 flex items-center justify-center ${
                      isLatest
                        ? 'bg-orange-600 shadow-md shadow-orange-500/50'
                        : 'bg-slate-400 dark:bg-slate-600'
                    }`}
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-white"></div>
                  </div>

                  {/* Revision Card */}
                  <div className={`p-4 rounded-xl border transition-all ${
                    isLatest 
                      ? 'border-orange-200 dark:border-orange-900/60 bg-orange-50/20 dark:bg-orange-950/20 shadow-sm'
                      : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60'
                  }`}>
                    {/* Header */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2.5 border-b border-slate-100 dark:border-slate-800">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                          Lần #{productHistory.length - idx}
                          {isLatest && (
                            <span className="text-[9px] px-1.5 py-0.2 rounded bg-orange-500 text-white uppercase font-bold">
                              Mới nhất
                            </span>
                          )}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          {formatDateTime(rev.changed_at)}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5">
                        {rev.change_type === 'AI_RECOMMENDED' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                            <Bot className="w-3 h-3" />
                            <span>Đề xuất AI</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
                            <UserCheck className="w-3 h-3" />
                            <span>Tự chỉnh tay</span>
                          </span>
                        )}

                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>POS</span>
                        </span>
                      </div>
                    </div>

                    {/* Price Diff Grid */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center">
                      <div>
                        <div className="text-[11px] text-slate-500 mb-1">Mức giá thay đổi:</div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-slate-400 line-through">
                            {formatCurrencyVND(rev.old_price)}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                          <span className="font-mono font-bold text-slate-900 dark:text-white text-sm">
                            {formatCurrencyVND(rev.new_price)}
                          </span>
                        </div>
                      </div>

                      <div className="flex sm:justify-end items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg font-mono font-bold text-xs ${
                            isDecrease
                              ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900'
                              : 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900'
                          }`}
                        >
                          {isDecrease ? <TrendingDown className="w-3.5 h-3.5" /> : <TrendingUp className="w-3.5 h-3.5" />}
                          <span>{rev.price_change > 0 ? '+' : ''}{formatCurrencyVND(rev.price_change)}</span>
                          <span className="text-[10px] opacity-75">({formatPercent(rev.price_change_percent)})</span>
                        </span>

                        <span className="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 font-mono text-[11px] text-slate-700 dark:text-slate-300 font-semibold" title="Biên lợi nhuận">
                          LN: {formatPercent(rev.margin_percent)}
                        </span>
                      </div>
                    </div>

                    {/* Scenario & Changed By */}
                    <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px]">
                      <div className="text-slate-600 dark:text-slate-400">
                        <strong className="text-slate-700 dark:text-slate-300 font-semibold">Căn cứ: </strong>
                        {rev.scenario}
                      </div>
                      <div className="text-slate-400 shrink-0">
                        Người thực hiện: <span className="font-medium text-slate-700 dark:text-slate-300">{rev.changed_by}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="p-3.5 px-6 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 flex items-center justify-between">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Tất cả dữ liệu thay đổi giá đều được mã hoá và lưu vết kiểm toán (Audit Trail).</span>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 font-semibold text-xs transition"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
