import React from 'react';
import { cn } from '../../utils/cn';

export interface TableSkeletonProps {
  rows?: number;
  cols?: number;
  className?: string;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({
  rows = 8,
  cols = 6,
  className,
}) => {
  return (
    <div
      className={cn(
        'rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden',
        className
      )}
      aria-label="Đang nạp dữ liệu..."
      role="status"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800">
              {Array.from({ length: cols }).map((_, i) => (
                <th key={i} className="py-3 px-3">
                  <div className="h-3.5 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-3/4" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {Array.from({ length: rows }).map((_, r) => (
              <tr key={r} className="animate-pulse">
                {Array.from({ length: cols }).map((_, c) => (
                  <td key={c} className="py-3 px-3">
                    <div
                      className={cn(
                        'h-3.5 bg-slate-100 dark:bg-slate-800/60 rounded',
                        c === 0 ? 'w-5/6' : c === cols - 1 ? 'w-1/2 mx-auto' : 'w-2/3 ml-auto'
                      )}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <span className="sr-only">Đang nạp dữ liệu bảng...</span>
    </div>
  );
};

