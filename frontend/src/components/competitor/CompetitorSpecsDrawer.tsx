import React, { useState, useEffect } from 'react';
import { X, ExternalLink, Copy, Check, Sliders, Code2, AlertCircle } from 'lucide-react';
import { CrawlResult } from '../../types/crawl';
import { formatCurrencyVND, formatDate } from '../../utils/formatters';

interface CompetitorSpecsDrawerProps {
  item: CrawlResult | null;
  onClose: () => void;
}

export const CompetitorSpecsDrawer: React.FC<CompetitorSpecsDrawerProps> = ({ item, onClose }) => {
  const [activeTab, setActiveTab] = useState<'specs' | 'json'>('specs');
  const [copied, setCopied] = useState(false);

  // Lắng nghe phím ESC để đóng drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!item) return null;

  const isCellphoneS = item.source === 'CELLPHONES';
  const specs = item.specifications || {};
  const specKeys = Object.keys(specs).filter((key) => key.toLowerCase() !== 'summary');

  const handleCopyJson = async () => {
    try {
      const jsonStr = JSON.stringify(item, null, 2);
      await navigator.clipboard.writeText(jsonStr);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback nếu clipboard API bị chặn
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="fixed inset-y-0 right-0 pl-10 max-w-full flex">
        <div className="w-screen max-w-xl bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col justify-between">
          
          {/* Header */}
          <div className="p-6 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${
                    isCellphoneS
                      ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-900'
                      : 'bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-900'
                  }`}
                >
                  {item.source}
                </span>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    item.is_in_stock
                      ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-400'
                  }`}
                >
                  {item.is_in_stock ? 'Còn hàng' : 'Tạm hết hàng'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                  title="Mở link bài viết trên website đối thủ"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                  title="Đóng drawer (ESC)"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <h2 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
              {item.product_name}
            </h2>

            <div className="mt-3 flex items-baseline gap-3">
              <span className="text-xl font-black font-mono text-orange-600 dark:text-orange-400">
                {formatCurrencyVND(item.price)}
              </span>
              {item.original_price && item.original_price > item.price && (
                <span className="text-xs line-through text-slate-400 font-mono">
                  {formatCurrencyVND(item.original_price)}
                </span>
              )}
              <span className="text-[11px] text-slate-400 ml-auto">
                Cập nhật: {formatDate(item.crawled_at)}
              </span>
            </div>

            {/* Sub-tabs switch */}
            <div className="flex border-b border-slate-200 dark:border-slate-800 mt-5 -mb-6">
              <button
                onClick={() => setActiveTab('specs')}
                className={`flex items-center gap-2 py-2.5 px-4 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'specs'
                    ? 'border-orange-500 text-orange-600 dark:text-orange-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>Thông số bóc tách ({specKeys.length})</span>
              </button>
              <button
                onClick={() => setActiveTab('json')}
                className={`flex items-center gap-2 py-2.5 px-4 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === 'json'
                    ? 'border-orange-500 text-orange-600 dark:text-orange-400'
                    : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>Raw JSON</span>
              </button>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === 'specs' ? (
              specKeys.length > 0 ? (
                <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
                  {specKeys.map((key) => {
                    const val = specs[key];
                    const valStr = typeof val === 'object' ? JSON.stringify(val) : String(val);
                    return (
                      <div
                        key={key}
                        className="grid grid-cols-3 p-3 text-xs hover:bg-slate-50 dark:hover:bg-slate-800/40 transition"
                      >
                        <div className="font-semibold text-slate-600 dark:text-slate-400 pr-2">
                          {key}
                        </div>
                        <div className="col-span-2 font-mono text-slate-900 dark:text-slate-100 break-words">
                          {valStr}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-10 text-center flex flex-col items-center justify-center text-slate-400">
                  <AlertCircle className="w-8 h-8 text-slate-300 dark:text-slate-600 mb-2" />
                  <p className="text-xs">Chưa có thông số kỹ thuật được trích xuất cho sản phẩm này.</p>
                </div>
              )
            ) : (
              <div className="relative">
                <div className="flex items-center justify-between pb-2">
                  <span className="text-[11px] text-slate-400">Dữ liệu thô bóc tách từ HTML:</span>
                  <button
                    onClick={handleCopyJson}
                    className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-500" />
                        <span className="text-emerald-500">Đã sao chép</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Sao chép JSON</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="p-4 rounded-xl bg-slate-950 text-slate-200 font-mono text-xs overflow-x-auto max-h-[500px] border border-slate-800">
                  {JSON.stringify(item, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 flex items-center justify-between">
            <span className="text-[11px] text-slate-400 truncate max-w-[280px]">
              ID: {item.id}
            </span>
            <div className="flex items-center gap-2">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-orange-600 hover:bg-orange-700 rounded-lg shadow-sm transition"
              >
                <span>Xem trên web đối thủ</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
