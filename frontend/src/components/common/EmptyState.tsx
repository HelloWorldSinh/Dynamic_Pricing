import React from 'react';
import { cn } from '../../utils/cn';
import { Button } from './Button';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  onReset?: () => void;
  resetLabel?: string;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'Không tìm thấy dữ liệu',
  description = 'Không có bản ghi nào phù hợp với điều kiện tìm kiếm hoặc bộ lọc hiện tại.',
  onReset,
  resetLabel = 'Đặt lại bộ lọc',
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-dashed border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-12 text-center shadow-xs flex flex-col items-center justify-center',
        className
      )}
    >
      <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 font-mono font-bold text-xs flex items-center justify-center mb-3">
        0
      </div>
      <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
        {title}
      </h3>
      <p className="text-xs text-slate-500 max-w-sm mt-1 leading-relaxed">
        {description}
      </p>
      {onReset && (
        <div className="mt-4">
          <Button variant="secondary" size="sm" onClick={onReset}>
            {resetLabel}
          </Button>
        </div>
      )}
    </div>
  );
};

