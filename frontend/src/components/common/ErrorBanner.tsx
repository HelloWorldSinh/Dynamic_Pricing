import React from 'react';
import { cn } from '../../utils/cn';
import { Button } from './Button';

export interface ErrorBannerProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  title = 'Lỗi kết nối máy chủ',
  message = 'Không thể đồng bộ dữ liệu từ máy chủ. Vui lòng kiểm tra lại đường truyền hoặc dịch vụ backend.',
  onRetry,
  className,
}) => {
  return (
    <div
      className={cn(
        'p-4 rounded-xl border border-rose-200 dark:border-rose-900 bg-rose-50/70 dark:bg-rose-950/30 text-rose-800 dark:text-rose-200 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs',
        className
      )}
      role="alert"
    >
      <div>
        <div className="text-xs font-bold uppercase tracking-wider text-rose-700 dark:text-rose-400">
          [ LỖI KẾT NỐI ] {title}
        </div>
        <p className="text-xs text-rose-600 dark:text-rose-300 mt-0.5 leading-relaxed">
          {message}
        </p>
      </div>

      {onRetry && (
        <div className="shrink-0">
          <Button
            variant="destructive"
            size="sm"
            onClick={onRetry}
            className="bg-rose-600 hover:bg-rose-700 text-white"
          >
            Thử lại kết nối
          </Button>
        </div>
      )}
    </div>
  );
};

