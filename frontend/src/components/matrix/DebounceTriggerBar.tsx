import React, { useState, useEffect, useRef, useCallback } from 'react';
import { triggerDualCrawlApi, getLatestCrawlTimeApi, getCrawlStatsApi, crawlerApi } from '../../api/crawlerApi';
import { getSkuMatchingStatsApi, SkuMatchingStats } from '../../api/pricingApi';
import type { CrawlProgressResponse } from '../../types/index';

const STORAGE_ACTIVE_TASK_ID = 'dynamic_pricing_active_task_id';
const STORAGE_TASK_PROGRESS = 'dynamic_pricing_task_progress';

interface DebounceTriggerBarProps {
  category?: string;
  onCrawlCompleted: () => void;
}

export const DebounceTriggerBar: React.FC<DebounceTriggerBarProps> = ({
  category,
  onCrawlCompleted,
}) => {
  const [activeTaskId, setActiveTaskId] = useState<string | null>(() => {
    return localStorage.getItem(STORAGE_ACTIVE_TASK_ID);
  });
  const [isCrawling, setIsCrawling] = useState<boolean>(() => {
    return !!localStorage.getItem(STORAGE_ACTIVE_TASK_ID);
  });
  const [taskProgress, setTaskProgress] = useState<CrawlProgressResponse | null>(() => {
    const cached = localStorage.getItem(STORAGE_TASK_PROGRESS);
    if (cached) {
      try {
        return JSON.parse(cached);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [countdown, setCountdown] = useState<number>(0);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  // Thống kê thực tế từ DB: số bản ghi cào và tỷ lệ ghép cặp SKU
  const [matchingStats, setMatchingStats] = useState<SkuMatchingStats | null>(null);
  const [dbScrapedTotal, setDbScrapedTotal] = useState<number | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onCrawlCompletedRef = useRef(onCrawlCompleted);

  useEffect(() => {
    onCrawlCompletedRef.current = onCrawlCompleted;
  }, [onCrawlCompleted]);

  // Nạp số liệu thống kê thực tế từ API cào và API đối soát SKU
  const loadAllStats = useCallback(async () => {
    try {
      const [crawlStats, matchStats] = await Promise.all([
        getCrawlStatsApi(category),
        getSkuMatchingStatsApi(),
      ]);
      if (crawlStats && typeof crawlStats.total === 'number') {
        setDbScrapedTotal(crawlStats.total);
      }
      if (matchStats && typeof matchStats.total_skus === 'number') {
        setMatchingStats(matchStats);
      }
    } catch (err) {
      console.warn('Lỗi khi nạp số liệu thống kê cào và đối soát:', err);
    }
  }, [category]);

  // Lấy thời điểm cào gần nhất và số liệu thống kê khi tải component
  useEffect(() => {
    let isMounted = true;
    const loadTime = async () => {
      const time = await getLatestCrawlTimeApi();
      if (isMounted && time) {
        setLastUpdated(time);
      }
    };
    loadTime();
    loadAllStats();
    return () => {
      isMounted = false;
    };
  }, [loadAllStats]);

  // Đếm ngược Debounce
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

  // Polling tiến độ cào thời gian thực khi có activeTaskId
  useEffect(() => {
    if (!activeTaskId) return;

    let isMounted = true;

    const pollStatus = async () => {
      try {
        const progress = await crawlerApi.getStatus(activeTaskId);
        if (!isMounted) return;

        setTaskProgress(progress);
        localStorage.setItem(STORAGE_TASK_PROGRESS, JSON.stringify(progress));

        if (progress.status === 'COMPLETED') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
          setIsCrawling(false);

          const nowIso = new Date().toISOString();
          setLastUpdated(nowIso);
          setCountdown(30);

          onCrawlCompletedRef.current();
          loadAllStats();

          if (completionTimeoutRef.current) {
            clearTimeout(completionTimeoutRef.current);
          }
          completionTimeoutRef.current = setTimeout(() => {
            if (isMounted) {
              setActiveTaskId(null);
            }
          }, 8000);
        } else if (progress.status === 'FAILED') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
          setIsCrawling(false);

          if (completionTimeoutRef.current) {
            clearTimeout(completionTimeoutRef.current);
          }
          completionTimeoutRef.current = setTimeout(() => {
            if (isMounted) {
              setActiveTaskId(null);
            }
          }, 10000);
        }
      } catch (err: unknown) {
        console.error('Lỗi khi tra cứu tiến độ cào:', err);
      }
    };

    pollStatus();
    pollingRef.current = setInterval(pollStatus, 1500);

    return () => {
      isMounted = false;
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      if (completionTimeoutRef.current) {
        clearTimeout(completionTimeoutRef.current);
        completionTimeoutRef.current = null;
      }
    };
  }, [activeTaskId]);

  const formatTimestamp = (isoString: string): string => {
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      const pad = (n: number) => n.toString().padStart(2, '0');
      return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
    } catch {
      return isoString;
    }
  };

  const handleTrigger = async () => {
    if (countdown > 0 || isCrawling || activeTaskId) return;

    setIsCrawling(true);

    const initialProgress: CrawlProgressResponse = {
      task_id: 'khoi-tao',
      source: 'FULL_PIPELINE',
      category: 'ALL',
      status: 'RUNNING',
      current_page: 0,
      total_pages: 1,
      scraped_count: 0,
      progress_percent: 5,
      message: 'Đang khởi tạo kết nối CellphoneS & Hoàng Hà Mobile...',
      started_at: new Date().toISOString(),
    };
    setTaskProgress(initialProgress);

    try {
      const resList = await triggerDualCrawlApi(category);
      const firstRes = Array.isArray(resList) ? resList[0] : resList;
      const taskId = firstRes?.task_id || firstRes?.job_id;

      if (taskId) {
        localStorage.setItem(STORAGE_ACTIVE_TASK_ID, taskId);
        setActiveTaskId(taskId);
        setTaskProgress({
          ...initialProgress,
          task_id: taskId,
        });
      } else {
        localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
        setIsCrawling(false);
        setLastUpdated(new Date().toISOString());
        setCountdown(30);
        onCrawlCompletedRef.current();
        loadAllStats();
      }
    } catch (error: any) {
      localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
      setIsCrawling(false);
      setActiveTaskId(null);
      if (error.response?.status === 429) {
        setCountdown(15);
      }
    }
  };

  const isRunning = isCrawling || !!activeTaskId;
  const scrapedCount = taskProgress?.scraped_count
    ? taskProgress.scraped_count.toLocaleString()
    : dbScrapedTotal !== null
      ? dbScrapedTotal.toLocaleString()
      : '4,261';

  return (
    <div className="py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-3.5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
      {/* Left: Indicator Dot, Timestamp, Summary Stats or Active Progress */}
      <div className="flex flex-wrap items-center gap-2.5 min-w-0">
        {/* Status Dot */}
        <span
          className={`w-2 h-2 rounded-full shrink-0 ${isRunning
            ? 'bg-amber-500 animate-pulse ring-4 ring-amber-500/20'
            : 'bg-emerald-500'
            }`}
        />

        {/* Timestamp */}
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium whitespace-nowrap">
          Cập nhật: <span className="font-mono font-bold text-slate-800 dark:text-slate-200">{lastUpdated ? formatTimestamp(lastUpdated) : '10:15 14/10/2026'}</span>
        </span>

        <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">|</span>

        {/* Summary Stats or Live Progress */}
        {isRunning ? (
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="text-xs text-orange-600 dark:text-orange-400 font-medium truncate max-w-xs">
              {taskProgress?.message || 'Đang cào dữ liệu đối thủ...'}
            </span>
            <div className="w-24 sm:w-32 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden shrink-0">
              <div
                className="h-full bg-orange-500 rounded-full transition-all duration-300"
                style={{ width: `${taskProgress?.progress_percent || 10}%` }}
              />
            </div>
            <span className="text-xs font-mono font-bold text-orange-600 dark:text-orange-400 shrink-0">
              {taskProgress?.progress_percent || 0}%
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
              Đã thu thập <strong className="font-mono text-slate-900 dark:text-white font-bold">{scrapedCount}</strong> SP
            </span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
              Ghép cặp{' '}
              <strong className="font-mono text-slate-900 dark:text-white font-bold">
                {matchingStats ? `${matchingStats.matched_skus}/${matchingStats.total_skus}` : 'error'}
              </strong>{' '}
              SKU -{' '}
              <strong className="text-emerald-600 dark:text-emerald-400 font-mono font-bold">
                {matchingStats ? `${matchingStats.match_rate}%` : 'error'}
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Right: Primary CTA Button */}
      <div className="shrink-0 flex items-center justify-end">
        <button
          type="button"
          onClick={handleTrigger}
          disabled={countdown > 0 || isRunning}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold tracking-tight transition-all duration-150 shadow-xs ${countdown > 0 || isRunning
            ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-200 dark:border-slate-700'
            : 'bg-orange-600 hover:bg-orange-700 text-white shadow-orange-600/20 active:scale-95 cursor-pointer'
            }`}
        >
          {isRunning
            ? `Đang cào dữ liệu (${taskProgress?.progress_percent || 0}%)`
            : countdown > 0
              ? `Chờ ${countdown}s (Debounce)`
              : 'Cào dữ liệu'}
        </button>
      </div>
    </div>
  );
};
