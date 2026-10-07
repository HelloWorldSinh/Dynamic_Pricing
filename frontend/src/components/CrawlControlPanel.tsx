import React, { useState, useEffect, useRef } from 'react';
import { crawlerApi } from '../api/crawlerApi.js';
import type { CompetitorSource, CrawlProgressResponse } from '../types/index.js';

interface CrawlControlPanelProps {
  onTriggerSuccess?: (source: string, taskId: string) => void;
}

export const CrawlControlPanel: React.FC<CrawlControlPanelProps> = ({ onTriggerSuccess }) => {
  const [selectedSource, setSelectedSource] = useState<CompetitorSource>('cellphones');
  const [selectedCategory, setSelectedCategory] = useState<string>('phone');
  const [selectedLimit, setSelectedLimit] = useState<number>(20);
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
          setErrorMessage(progress.message || 'Tiến trình cào dữ liệu gặp lỗi.');
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

  const handleTrigger = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);
    setTaskProgress(null);

    try {
      const response = await crawlerApi.trigger({
        source: selectedSource,
        category: selectedCategory,
        limit: selectedLimit > 0 ? selectedLimit : undefined,
      });

      setActiveTaskId(response.task_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Không thể kích hoạt tiến trình cào.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isJobRunning = taskProgress?.status === 'RUNNING' || taskProgress?.status === 'PENDING';

  return (
    <div
      style={{
        backgroundColor: 'var(--color-bg-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem',
        marginBottom: '1.5rem',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div style={{ marginBottom: '1rem' }}>
        <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, color: 'var(--color-text-primary)', marginBottom: '0.25rem' }}>
          Bảng Điều Khiển Cào Dữ Liệu Đối Thủ (Crawler Engine)
        </h2>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
          Kích hoạt tiến trình thu thập giá theo thời gian thực và theo dõi tiến độ chi tiết từng trang.
        </p>
      </div>

      {/* Bộ điều khiển đầu vào */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
        <div>
          <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '0.35rem' }}>
            Nguồn Đối Thủ
          </label>
          <select
            value={selectedSource}
            disabled={isJobRunning}
            onChange={(e) => setSelectedSource(e.target.value as CompetitorSource)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '160px',
              backgroundColor: isJobRunning ? 'var(--color-bg-primary)' : 'var(--color-bg-surface)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value="cellphones">CellphoneS</option>
            <option value="hoangha">Hoàng Hà Mobile</option>
            <option value="fptshop">FPT Shop (Nội bộ)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '0.35rem' }}>
            Ngành Hàng
          </label>
          <select
            value={selectedCategory}
            disabled={isJobRunning}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '140px',
              backgroundColor: isJobRunning ? 'var(--color-bg-primary)' : 'var(--color-bg-surface)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value="phone">Điện thoại</option>
            <option value="laptop">Laptop</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '0.35rem' }}>
            Số Lượng Cào
          </label>
          <select
            value={selectedLimit}
            disabled={isJobRunning}
            onChange={(e) => setSelectedLimit(Number(e.target.value))}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '180px',
              backgroundColor: isJobRunning ? 'var(--color-bg-primary)' : 'var(--color-bg-surface)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value={20}>20 sản phẩm (Nhanh - Khuyến nghị)</option>
            <option value={50}>50 sản phẩm (Tiêu chuẩn)</option>
            <option value={100}>100 sản phẩm (Mở rộng)</option>
            <option value={0}>Toàn bộ (Mất vài phút)</option>
          </select>
        </div>

        <button
          type="button"
          onClick={handleTrigger}
          disabled={isSubmitting || isJobRunning}
          style={{
            padding: '0.5rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: (isSubmitting || isJobRunning) ? 'var(--color-text-muted)' : 'var(--color-primary)',
            color: 'var(--color-text-inverse)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
            cursor: (isSubmitting || isJobRunning) ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.15s ease',
          }}
        >
          {isSubmitting ? 'Đang gửi lệnh...' : isJobRunning ? 'Đang tiến hành cào...' : 'Kích hoạt cào ngay'}
        </button>
      </div>

      {/* Thông báo lỗi nếu có */}
      {errorMessage && (
        <div
          style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            backgroundColor: 'var(--color-status-danger-bg)',
            color: 'var(--color-status-danger-text)',
            border: '1px solid var(--color-status-danger-border)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-sm)',
          }}
        >
          {errorMessage}
        </div>
      )}

      {/* Bảng hiển thị tiến độ thời gian thực */}
      {taskProgress && (
        <div
          style={{
            marginTop: '1.25rem',
            padding: '1rem',
            backgroundColor: 'var(--color-bg-primary)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
                Tiến Trình Task:
              </span>
              <span style={{ fontSize: 'var(--font-size-xs)', fontFamily: 'monospace', color: 'var(--color-text-primary)' }}>
                {taskProgress.task_id}
              </span>
            </div>

            {/* Status Badge */}
            <span
              style={{
                fontSize: 'var(--font-size-xs)',
                fontWeight: 700,
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor:
                  taskProgress.status === 'COMPLETED'
                    ? 'var(--color-status-success-bg)'
                    : taskProgress.status === 'FAILED'
                    ? 'var(--color-status-danger-bg)'
                    : 'var(--color-primary-light)',
                color:
                  taskProgress.status === 'COMPLETED'
                    ? 'var(--color-status-success-text)'
                    : taskProgress.status === 'FAILED'
                    ? 'var(--color-status-danger-text)'
                    : 'var(--color-primary)',
                border: `1px solid ${
                  taskProgress.status === 'COMPLETED'
                    ? 'var(--color-status-success-border)'
                    : taskProgress.status === 'FAILED'
                    ? 'var(--color-status-danger-border)'
                    : 'var(--color-primary)'
                }`,
              }}
            >
              {taskProgress.status === 'COMPLETED'
                ? 'ĐÃ HOÀN TẤT'
                : taskProgress.status === 'FAILED'
                ? 'THẤT BẠI'
                : taskProgress.status === 'RUNNING'
                ? 'ĐANG THỰC HIỆN'
                : 'ĐANG CHỜ'}
            </span>
          </div>

          {/* Thanh Tiến Độ (Progress Bar) */}
          <div
            style={{
              width: '100%',
              height: '8px',
              backgroundColor: 'var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              marginBottom: '0.75rem',
            }}
          >
            <div
              style={{
                width: `${taskProgress.progress_percent}%`,
                height: '100%',
                backgroundColor:
                  taskProgress.status === 'COMPLETED'
                    ? 'var(--color-status-success-text)'
                    : 'var(--color-primary)',
                transition: 'width 0.3s ease',
              }}
            />
          </div>

          {/* Chỉ số chi tiết */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <div style={{ backgroundColor: 'var(--color-bg-surface)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Tiến Độ Tỷ Lệ</div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                {taskProgress.progress_percent}%
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--color-bg-surface)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Đã Thu Thập</div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                {taskProgress.scraped_count} {taskProgress.limit ? `/ ${taskProgress.limit}` : ''} sản phẩm
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--color-bg-surface)', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Trang Hiện Tại</div>
              <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                Trang {taskProgress.current_page || 1}
              </div>
            </div>
          </div>

          {/* Dòng trạng thái log trực tiếp */}
          <div
            style={{
              padding: '0.5rem 0.75rem',
              backgroundColor: 'var(--color-bg-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-secondary)',
            }}
          >
            Trạng thái hiện tại: {taskProgress.message}
          </div>
        </div>
      )}
    </div>
  );
};
