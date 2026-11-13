import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X } from 'lucide-react';
import { triggerDualCrawlApi, getLatestCrawlTimeApi, getCrawlStatsApi, crawlerApi } from '../../api/crawlerApi';
import { getSkuMatchingStatsApi, SkuMatchingStats } from '../../api/pricingApi';
import type { CrawlProgressResponse } from '../../types/index';
import { Button } from '../common/Button';

const STORAGE_ACTIVE_TASK_ID = 'dynamic_pricing_active_task_id';
const STORAGE_TASK_PROGRESS = 'dynamic_pricing_task_progress';

interface UnifiedMatrixToolbarProps {
  categoryFilter: string;
  setCategoryFilter: (category: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  priceGapFilter: string;
  setPriceGapFilter: (val: string) => void;
  dohRiskFilter: boolean;
  setDohRiskFilter: (val: boolean) => void;
  inStockOnlyFilter: boolean;
  setInStockOnlyFilter: (val: boolean) => void;
  onCrawlCompleted: () => void;
}

export const UnifiedMatrixToolbar: React.FC<UnifiedMatrixToolbarProps> = ({
  categoryFilter,
  setCategoryFilter,
  searchQuery,
  setSearchQuery,
  priceGapFilter,
  setPriceGapFilter,
  dohRiskFilter,
  setDohRiskFilter,
  inStockOnlyFilter,
  setInStockOnlyFilter,
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
  const [matchingStats, setMatchingStats] = useState<SkuMatchingStats | null>(null);
  const [dbScrapedTotal, setDbScrapedTotal] = useState<number | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onCrawlCompletedRef = useRef(onCrawlCompleted);

  useEffect(() => {
    onCrawlCompletedRef.current = onCrawlCompleted;
  }, [onCrawlCompleted]);

  const loadAllStats = useCallback(async () => {
    try {
      const [crawlStats, matchStats] = await Promise.all([
        getCrawlStatsApi(categoryFilter),
        getSkuMatchingStatsApi(),
      ]);
      if (crawlStats && typeof crawlStats.total === 'number') {
        setDbScrapedTotal(crawlStats.total);
      }
      if (matchStats && typeof matchStats.total_skus === 'number') {
        setMatchingStats(matchStats);
      }
    } catch (err) {
      console.warn('Lỗi khi nạp số liệu thống kê:', err);
    }
  }, [categoryFilter]);

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

          if (completionTimeoutRef.current) clearTimeout(completionTimeoutRef.current);
          completionTimeoutRef.current = setTimeout(() => {
            if (isMounted) setActiveTaskId(null);
          }, 8000);
        } else if (progress.status === 'FAILED') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
          setIsCrawling(false);

          if (completionTimeoutRef.current) clearTimeout(completionTimeoutRef.current);
          completionTimeoutRef.current = setTimeout(() => {
            if (isMounted) setActiveTaskId(null);
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
  }, [activeTaskId, loadAllStats]);

  const formatTimestamp = (isoString: string): string => {
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      const pad = (n: number) => n.toString().padStart(2, '0');
      return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}`;
    } catch {
      return isoString;
    }
  };

  const handleTrigger = async () => {
    if (countdown > 0 || isCrawling || activeTaskId) return;

    setIsCrawling(true);
    const initialProgress: CrawlProgressResponse = {
      task_id: 'init',
      source: 'FULL_PIPELINE',
      category: categoryFilter,
      status: 'RUNNING',
      current_page: 0,
      total_pages: 1,
      scraped_count: 0,
      progress_percent: 5,
      message: 'Đang khởi tạo crawler...',
      started_at: new Date().toISOString(),
    };
    setTaskProgress(initialProgress);

    try {
      const resList = await triggerDualCrawlApi(categoryFilter);
      const firstRes = Array.isArray(resList) ? resList[0] : resList;
      const taskId = firstRes?.task_id || firstRes?.job_id;

      if (taskId) {
        localStorage.setItem(STORAGE_ACTIVE_TASK_ID, taskId);
        setActiveTaskId(taskId);
        setTaskProgress({ ...initialProgress, task_id: taskId });
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
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-4 shadow-xs p-3">
      {/* Top Row: Category Selection + Crawl State & CTA */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        {/* Left: Category Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={() => setCategoryFilter('ALL')}
            className={`px-3 py-1 rounded text-xs font-semibold transition ${
              categoryFilter === 'ALL'
                ? 'bg-orange-600 text-white shadow-xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Tất cả
          </button>
          <button
            type="button"
            onClick={() => setCategoryFilter('PHONE')}
            className={`px-3 py-1 rounded text-xs font-semibold transition ${
              categoryFilter === 'PHONE'
                ? 'bg-orange-600 text-white shadow-xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Điện thoại
          </button>
          <button
            type="button"
            onClick={() => setCategoryFilter('LAPTOP')}
            className={`px-3 py-1 rounded text-xs font-semibold transition ${
              categoryFilter === 'LAPTOP'
                ? 'bg-orange-600 text-white shadow-xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            Laptop
          </button>
        </div>

        {/* Right: Crawl Pulse, Timestamp & CTA */}
        <div className="flex items-center gap-3 flex-wrap lg:justify-end">
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                isRunning
                  ? 'bg-amber-500 animate-pulse ring-2 ring-amber-500/20'
                  : 'bg-emerald-500'
              }`}
            />
            <span className="text-slate-500 dark:text-slate-400 text-xs">
              Cập nhật:{' '}
              <span className="font-mono font-semibold text-slate-700 dark:text-slate-300">
                {lastUpdated ? formatTimestamp(lastUpdated) : '—'}
              </span>
            </span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span className="text-slate-500 dark:text-slate-400 text-xs">
              Đã thu thập <strong className="font-mono text-slate-700 dark:text-slate-200">{scrapedCount}</strong> SP
              {matchingStats && (
                <span className="hidden sm:inline">
                  {' '}| Ghép cặp <strong className="font-mono text-slate-700 dark:text-slate-200">{matchingStats.matched_skus}/{matchingStats.total_skus}</strong> ({matchingStats.match_rate}%)
                </span>
              )}
            </span>
          </div>

          <Button
            size="sm"
            variant="primary"
            onClick={handleTrigger}
            disabled={countdown > 0 || isRunning}
            isLoading={isRunning}
          >
            {isRunning
              ? `Cào dữ liệu (${taskProgress?.progress_percent || 0}%)`
              : countdown > 0
                ? `Chờ ${countdown}s`
                : 'Cào dữ liệu'}
          </Button>
        </div>
      </div>

      {/* Bottom Row: Search Input + Multi-criteria Filter Selectors */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-2.5 pt-3">
        {/* Search Input */}
        <div className="flex-1 max-w-md relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo SKU, tên sản phẩm, Part-Number..."
            className="w-full px-3 py-1.5 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 transition"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded transition"
              aria-label="Xóa từ khóa tìm kiếm"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Right Filter Selects & Checkboxes */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Price Gap Selector */}
          <select
            value={priceGapFilter}
            onChange={(e) => setPriceGapFilter(e.target.value)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500 font-medium"
          >
            <option value="ALL">Mọi chênh lệch giá</option>
            <option value="GAP_5">FPT đắt hơn ≥ 5% (Báo động)</option>
            <option value="GAP_2">FPT đắt hơn ≥ 2%</option>
            <option value="CHEAPER">FPT rẻ hơn đối thủ</option>
          </select>

          {/* DOH Risk Checkbox */}
          <label className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition shrink-0">
            <input
              type="checkbox"
              checked={dohRiskFilter}
              onChange={(e) => setDohRiskFilter(e.target.checked)}
              className="rounded border-slate-300 text-orange-600 focus:ring-orange-500 w-3.5 h-3.5"
            />
            <span className="text-2xs font-medium">DOH &gt; 30 ngày</span>
          </label>

          {/* In-Stock Only Checkbox */}
          <label className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none bg-slate-50 dark:bg-slate-800 px-2.5 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/60 transition shrink-0">
            <input
              type="checkbox"
              checked={inStockOnlyFilter}
              onChange={(e) => setInStockOnlyFilter(e.target.checked)}
              className="rounded border-slate-300 text-orange-600 focus:ring-orange-500 w-3.5 h-3.5"
            />
            <span className="text-2xs font-medium">Đối thủ còn hàng</span>
          </label>
        </div>
      </div>
    </div>
  );
};
