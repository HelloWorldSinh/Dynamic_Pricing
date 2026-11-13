import React from 'react';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
  className?: string;
  itemLabel?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  pageSize,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = [5, 10, 20, 50],
  className = '',
  itemLabel = 'bản ghi',
}) => {
  if (totalItems === 0) return null;

  const validTotalPages = Math.max(1, totalPages);
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const getPageNumbers = (): (number | string)[] => {
    if (validTotalPages <= 7) {
      return Array.from({ length: validTotalPages }, (_, i) => i + 1);
    }

    if (currentPage <= 4) {
      return [1, 2, 3, 4, 5, '...', validTotalPages];
    }

    if (currentPage >= validTotalPages - 3) {
      return [
        1,
        '...',
        validTotalPages - 4,
        validTotalPages - 3,
        validTotalPages - 2,
        validTotalPages - 1,
        validTotalPages,
      ];
    }

    return [
      1,
      '...',
      currentPage - 1,
      currentPage,
      currentPage + 1,
      '...',
      validTotalPages,
    ];
  };

  const pages = getPageNumbers();

  return (
    <div
      className={`mt-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3 text-xs select-none ${className}`}
    >
      {/* Left: Summary and Page Size */}
      <div className="flex flex-wrap items-center gap-3 text-slate-500 dark:text-slate-400">
        <span>
          Hiển thị <strong className="font-semibold text-slate-800 dark:text-slate-200 font-mono">{startItem}</strong> -{' '}
          <strong className="font-semibold text-slate-800 dark:text-slate-200 font-mono">{endItem}</strong> trong tổng số{' '}
          <strong className="font-semibold text-slate-900 dark:text-white font-mono">{totalItems}</strong> {itemLabel}
        </span>

        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 pl-3 border-l border-slate-200 dark:border-slate-800">
            <span className="text-2xs font-mono">MỖI TRANG:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              aria-label="Số bản ghi mỗi trang"
              className="bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded px-2 py-0.5 text-xs text-slate-800 dark:text-slate-200 font-medium focus:outline-none focus:ring-1 focus:ring-orange-500 cursor-pointer"
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Right: Page Navigation Controls */}
      <div className="flex items-center gap-1">
        {/* First Page */}
        <button
          type="button"
          onClick={() => onPageChange(1)}
          disabled={currentPage <= 1}
          className="px-2 py-1 rounded text-2xs font-mono font-bold border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          aria-label="Trang đầu tiên"
        >
          «
        </button>

        {/* Prev Page */}
        <button
          type="button"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          className="px-2 py-1 rounded text-2xs font-mono font-bold border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          aria-label="Trang trước"
        >
          ‹
        </button>

        {/* Page Number Buttons */}
        <div className="flex items-center gap-1 mx-1">
          {pages.map((p, idx) => {
            if (typeof p === 'string') {
              return (
                <span
                  key={`ellipsis-${idx}`}
                  className="px-1.5 py-0.5 text-slate-400 text-xs font-mono select-none"
                >
                  ...
                </span>
              );
            }

            const isActive = p === currentPage;
            return (
              <button
                key={p}
                type="button"
                onClick={() => onPageChange(p)}
                className={`min-w-[26px] h-6 px-1.5 rounded text-xs font-mono font-bold transition-all ${
                  isActive
                    ? 'bg-orange-600 text-white shadow-xs'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 border border-transparent'
                }`}
              >
                {p}
              </button>
            );
          })}
        </div>

        {/* Next Page */}
        <button
          type="button"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= validTotalPages}
          className="px-2 py-1 rounded text-2xs font-mono font-bold border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          aria-label="Trang kế tiếp"
        >
          ›
        </button>

        {/* Last Page */}
        <button
          type="button"
          onClick={() => onPageChange(validTotalPages)}
          disabled={currentPage >= validTotalPages}
          className="px-2 py-1 rounded text-2xs font-mono font-bold border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          aria-label="Trang cuối cùng"
        >
          »
        </button>
      </div>
    </div>
  );
};
