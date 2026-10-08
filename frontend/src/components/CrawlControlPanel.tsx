import React, { useState, useEffect, useRef } from 'react';
import { Play, RefreshCw, CheckCircle2, AlertCircle, Zap, Check } from 'lucide-react';
import { crawlerApi } from '../api/crawlerApi.js';
import type { CrawlProgressResponse } from '../types/index.js';

interface CrawlControlPanelProps {
  onTriggerSuccess?: (source: string, taskId: string) => void;
}

export const CrawlControlPanel: React.FC<CrawlControlPanelProps> = ({ onTriggerSuccess }) => {
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
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
          if (onTriggerSuccess) {
            onTriggerSuccess(progress.source, activeTaskId);
          }
        } else if (progress.status === 'FAILED') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
          setErrorMessage(progress.message || 'Tiến trình Full Pipeline gặp lỗi.');
        }
      } catch (err: unknown) {
        console.error('Lỗi khi tra cứu tiến độ:', err);
      }
    };

    // Gọi ngay lần đầu
    fetchStatus();

    // Thiết lập chu kỳ 1.5 giây
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

  const isJobRunning = taskProgress?.status === 'RUNNING' || taskProgress?.status === 'PENDING';
  const isCompleted = taskProgress?.status === 'COMPLETED';

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 mb-6 shadow-sm">
      {/* Header & Tiêu đề */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
              <Zap className="w-4 h-4" />
            </span>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Bảng Điều Khiển Cào & Đối Soát SKU (Full Pipeline)
            </h2>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
              Chạy tự động giống run_full_pipeline.py
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Cào toàn bộ sản phẩm Điện thoại & Laptop từ <strong>CellphoneS</strong> và <strong>Hoàng Hà Mobile</strong>, tự động đối soát với <strong>329 SKU FPT Shop</strong>, cập nhật Cơ sở dữ liệu và xuất file Excel.
          </p>
        </div>

        {/* Nút bấm Kích hoạt Full Pipeline */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleTriggerFullPipeline}
            disabled={isSubmitting || isJobRunning}
            className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold transition shadow-sm ${
              isSubmitting || isJobRunning
                ? 'bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed'
                : 'bg-orange-600 hover:bg-orange-500 text-white shadow-orange-600/20 hover:shadow-md cursor-pointer'
            }`}
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Đang khởi động...</span>
              </>
            ) : isJobRunning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Đang chạy Full Pipeline ({taskProgress?.progress_percent || 0}%)...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Kích hoạt Full Pipeline ngay</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Thông tin phạm vi pipeline */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <Check className="w-3.5 h-3.5 text-emerald-500" />
          <span>Đối thủ: <strong>CellphoneS & Hoàng Hà Mobile</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Check className="w-3.5 h-3.5 text-emerald-500" />
          <span>Danh mục: <strong>Điện thoại & Laptop (Tất cả các trang)</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Check className="w-3.5 h-3.5 text-emerald-500" />
          <span>Thuật toán: <strong>2 Tầng SKU Matcher + Đồng bộ CSDL & Excel</strong></span>
        </div>
      </div>

      {/* Thông báo lỗi nếu có */}
      {errorMessage && (
        <div className="mt-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Bảng hiển thị tiến độ thời gian thực */}
      {taskProgress && (
        <div className="mt-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Tiến trình:</span>
              <span className="text-xs font-mono text-slate-800 dark:text-slate-200">{taskProgress.task_id}</span>
            </div>

            {/* Status Badge */}
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                isCompleted
                  ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800'
                  : taskProgress.status === 'FAILED'
                  ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-800'
                  : 'bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-800 animate-pulse'
              }`}
            >
              {isCompleted
                ? 'ĐÃ HOÀN TẤT 100%'
                : taskProgress.status === 'FAILED'
                ? 'GẶP LỖI'
                : 'ĐANG THỰC HIỆN'}
            </span>
          </div>

          {/* Thanh Tiến Độ (Progress Bar) */}
          <div className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden mb-3">
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
            <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-800 flex items-center gap-2 text-xs text-emerald-700 dark:text-emerald-300 bg-emerald-50/60 dark:bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-200/60 dark:border-emerald-900/60">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>Dữ liệu cào đã được UPSERT vào CSDL và bảng đối soát SKU đã được làm mới đồng bộ!</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
