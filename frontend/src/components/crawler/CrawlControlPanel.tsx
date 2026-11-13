import React, { useState, useEffect, useRef } from 'react';
import { crawlerApi } from '../../api/crawlerApi';
import type { CrawlProgressResponse } from '../../types/index';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';

interface CrawlControlPanelProps {
  onTriggerSuccess?: (source: string, taskId: string) => void;
}

const STORAGE_ACTIVE_TASK_ID = 'dynamic_pricing_active_task_id';

export const CrawlControlPanel: React.FC<CrawlControlPanelProps> = ({ onTriggerSuccess }) => {
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isFptSubmitting, setIsFptSubmitting] = useState<boolean>(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(() => {
    return typeof window !== 'undefined' ? localStorage.getItem(STORAGE_ACTIVE_TASK_ID) : null;
  });
  const [taskProgress, setTaskProgress] = useState<CrawlProgressResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll tiến độ cào khi có activeTaskId
  useEffect(() => {
    if (!activeTaskId) return;

    const fetchStatus = async () => {
      try {
        const progress = await crawlerApi.getStatus(activeTaskId);
        setTaskProgress(progress);

        if (progress.status === 'COMPLETED') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
          if (onTriggerSuccess) {
            onTriggerSuccess(progress.source, activeTaskId);
          }
        } else if (progress.status === 'FAILED') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          localStorage.removeItem(STORAGE_ACTIVE_TASK_ID);
          setErrorMessage(progress.message || 'Tiến trình tác vụ gặp lỗi.');
        }
      } catch (err: unknown) {
        console.error('Lỗi khi tra cứu tiến độ:', err);
      }
    };

    fetchStatus();
    pollingRef.current = setInterval(fetchStatus, 1500);

    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [activeTaskId, onTriggerSuccess]);

  const handleTriggerFullPipeline = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    setTaskProgress(null);

    try {
      const response = await crawlerApi.triggerFullPipeline();
      localStorage.setItem(STORAGE_ACTIVE_TASK_ID, response.task_id);
      setActiveTaskId(response.task_id);
    } catch (err: any) {
      if (err.response?.status === 429) {
        setErrorMessage(err.response?.data?.detail || 'Hệ thống đang trong thời gian chờ (debounce). Vui lòng thử lại sau giây lát.');
      } else {
        const msg = err instanceof Error ? err.message : 'Không thể kích hoạt Full Pipeline.';
        setErrorMessage(msg);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSyncFptLive = async () => {
    setIsFptSubmitting(true);
    setErrorMessage(null);
    setTaskProgress(null);

    try {
      const response = await crawlerApi.syncFptPrices();
      localStorage.setItem(STORAGE_ACTIVE_TASK_ID, response.task_id);
      setActiveTaskId(response.task_id);
    } catch (err: any) {
      if (err.response?.status === 429) {
        setErrorMessage(
          err.response?.data?.detail ||
            'Hệ thống đang trong thời gian chờ (debounce). Vui lòng thử lại sau giây lát.'
        );
      } else {
        const msg = err instanceof Error ? err.message : 'Không thể kích hoạt đồng bộ giá FPT Live.';
        setErrorMessage(msg);
      }
    } finally {
      setIsFptSubmitting(false);
    }
  };

  const isJobRunning = taskProgress?.status === 'RUNNING' || taskProgress?.status === 'PENDING';
  const isCompleted = taskProgress?.status === 'COMPLETED';

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 mb-6 shadow-xs">
      {/* Header & Tiêu đề */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <h2 className="text-md font-bold text-slate-900 dark:text-white">
              Bảng Điều Khiển Cào &amp; Đối Soát SKU
            </h2>
            <Badge variant="success" size="xs">
              TỰ ĐỘNG PIPELINE &amp; FPT SYNC
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Thu thập dữ liệu từ CellphoneS, Hoàng Hà Mobile và đồng bộ giá thời gian thực từ FPT Shop vào bảng giá cơ sở.
          </p>
        </div>

        {/* Nhóm Nút bấm Hành động */}
        <div className="flex flex-wrap items-center gap-3">
          <Button
            type="button"
            variant="secondary"
            size="md"
            onClick={handleSyncFptLive}
            disabled={isSubmitting || isFptSubmitting || isJobRunning}
            isLoading={isFptSubmitting}
          >
            {isFptSubmitting ? 'Đang kích hoạt...' : 'Đồng bộ giá FPT Live'}
          </Button>

          <Button
            type="button"
            variant="primary"
            size="md"
            onClick={handleTriggerFullPipeline}
            disabled={isSubmitting || isFptSubmitting || isJobRunning}
            isLoading={isSubmitting || (isJobRunning && !isFptSubmitting)}
          >
            {isSubmitting
              ? 'Đang khởi động...'
              : isJobRunning
              ? `Đang chạy (${taskProgress?.progress_percent || 0}%)...`
              : 'Kích hoạt Full Pipeline ngay'}
          </Button>
        </div>
      </div>

      {/* Thông tin phạm vi pipeline */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
          <span>FPT Shop: <strong className="font-semibold text-slate-800 dark:text-slate-200">API Gateway Live Price Sync</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
          <span>Đối thủ: <strong className="font-semibold text-slate-800 dark:text-slate-200">CellphoneS &amp; Hoàng Hà Mobile</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
          <span>Thuật toán: <strong className="font-semibold text-slate-800 dark:text-slate-200">Part-Number + RapidFuzz</strong></span>
        </div>
      </div>

      {/* Thông báo lỗi nếu có */}
      {errorMessage && (
        <div className="mt-4 p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 text-xs flex items-center justify-between">
          <span>{errorMessage}</span>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-2xs font-bold uppercase hover:underline ml-2"
          >
            Đóng
          </button>
        </div>
      )}

      {/* Bảng hiển thị tiến độ thời gian thực */}
      {taskProgress && (
        <div className="mt-4 p-4 rounded-lg bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Tiến trình:</span>
              <span className="text-xs font-mono font-bold text-slate-800 dark:text-slate-200">{taskProgress.task_id}</span>
            </div>

            {/* Status Badge */}
            <Badge
              variant={isCompleted ? 'success' : taskProgress.status === 'FAILED' ? 'danger' : 'warning'}
              size="xs"
            >
              {isCompleted ? 'ĐÃ HOÀN TẤT 100%' : taskProgress.status === 'FAILED' ? 'GẶP LỖI' : 'ĐANG XỬ LÝ'}
            </Badge>
          </div>

          {/* Thanh Tiến Độ */}
          <div className="w-full h-1.5 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden mb-2.5">
            <div
              className={`h-full transition-all duration-300 ${
                isCompleted
                  ? 'bg-emerald-500'
                  : taskProgress.status === 'FAILED'
                  ? 'bg-rose-500'
                  : 'bg-orange-500'
              }`}
              style={{ width: `${taskProgress.progress_percent}%` }}
            />
          </div>

          {/* Thông điệp trạng thái chi tiết */}
          <div className="text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center justify-between">
            <span>{taskProgress.message || 'Đang xử lý dữ liệu...'}</span>
            <span className="font-mono font-bold text-slate-900 dark:text-white">{taskProgress.progress_percent}%</span>
          </div>

          {/* Khi hoàn tất: Thẻ thông báo kết quả tổng kết */}
          {isCompleted && (
            <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800 text-xs text-emerald-700 dark:text-emerald-300 bg-emerald-50/60 dark:bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-200/60 dark:border-emerald-900/60">
              Dữ liệu đã được xử lý thành công và bảng cơ sở dữ liệu đã được làm mới đồng bộ.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
