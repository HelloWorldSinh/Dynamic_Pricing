import React, { useState, useEffect } from 'react';
import { RefreshCw, Play, CheckCircle, AlertCircle } from 'lucide-react';
import { triggerCrawlApi } from '../../api/crawlerApi';
import { CrawlSource } from '../../types/crawl';

interface DebounceTriggerBarProps {
  category: string;
  onCrawlCompleted: () => void;
}

export const DebounceTriggerBar: React.FC<DebounceTriggerBarProps> = ({
  category,
  onCrawlCompleted,
}) => {
  const [selectedSource, setSelectedSource] = useState<CrawlSource>('CELLPHONES');
  const [isCrawling, setIsCrawling] = useState(false);
  const [countdown, setCountdown] = useState<number>(0);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Handle Debounce countdown timer
  useEffect(() => {
    if (countdown <= 0) return;
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [countdown]);

  const handleTrigger = async () => {
    if (countdown > 0 || isCrawling) return;

    setIsCrawling(true);
    setFeedback(null);

    try {
      const res = await triggerCrawlApi(selectedSource, category === 'ALL' ? 'laptop' : category);
      setFeedback({
        type: 'success',
        message: `${res.message || 'Đã kích hoạt cào dữ liệu thành công'}. Debounce 30s đang kích hoạt.`,
      });
      setCountdown(30); // 30s debounce protection
      onCrawlCompleted();
    } catch (error: any) {
      if (error.response?.status === 429) {
        setFeedback({
          type: 'error',
          message: error.response?.data?.detail || 'Hệ thống đang debounce, vui lòng đợi thêm giây lát.',
        });
        setCountdown(15);
      } else {
        setFeedback({
          type: 'error',
          message: 'Lỗi kích hoạt cào dữ liệu. Vui lòng kiểm tra lại kết nối backend.',
        });
      }
    } finally {
      setIsCrawling(false);
    }
  };

  return (
    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-6 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Source selector & Title */}
        <div className="flex items-center gap-3">
          <span className="p-2 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
            <RefreshCw className={`w-4 h-4 ${isCrawling ? 'animate-spin' : ''}`} />
          </span>
          <div>
            <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>On-Demand Crawl</span>
              <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono">
                Debounce 30s
              </span>
            </div>
          </div>
        </div>

        {/* Trigger Controls */}
        <div className="flex items-center gap-3">
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value as CrawlSource)}
            disabled={countdown > 0 || isCrawling}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500 disabled:opacity-50"
          >
            <option value="CELLPHONES">Nguồn: CellphoneS</option>
            <option value="HOANGHA">Nguồn: Hoàng Hà Mobile</option>
            <option value="FPT">Nguồn: FPT Shop (Baseline)</option>
          </select>

          <button
            onClick={handleTrigger}
            disabled={countdown > 0 || isCrawling}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 shadow-sm
              ${
                countdown > 0 || isCrawling
                  ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                  : 'bg-orange-600 hover:bg-orange-700 text-white shadow-orange-600/20 active:scale-95'
              }`}
          >
            {isCrawling ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Đang cào dữ liệu...</span>
              </>
            ) : countdown > 0 ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Đợi {countdown}s (Debounce)</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Trigger Crawl</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`mt-3 p-2.5 rounded-lg text-xs flex items-center gap-2 transition-all ${
            feedback.type === 'success'
              ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900'
              : 'bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-900'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}
    </div>
  );
};
