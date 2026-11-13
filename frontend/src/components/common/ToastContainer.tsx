import React from 'react';
import { useToast, ToastType } from '../../context/ToastContext';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  const typeStyles: Record<ToastType, { border: string; bg: string; title: string }> = {
    success: {
      border: 'border-emerald-500 dark:border-emerald-600',
      bg: 'bg-white dark:bg-slate-900',
      title: 'text-emerald-700 dark:text-emerald-400',
    },
    warning: {
      border: 'border-amber-500 dark:border-amber-600',
      bg: 'bg-white dark:bg-slate-900',
      title: 'text-amber-700 dark:text-amber-400',
    },
    danger: {
      border: 'border-rose-500 dark:border-rose-600',
      bg: 'bg-white dark:bg-slate-900',
      title: 'text-rose-700 dark:text-rose-400',
    },
    info: {
      border: 'border-blue-500 dark:border-blue-600',
      bg: 'bg-white dark:bg-slate-900',
      title: 'text-blue-700 dark:text-blue-400',
    },
  };

  const typeBadges: Record<ToastType, string> = {
    success: 'THÀNH CÔNG',
    warning: 'CẢNH BÁO',
    danger: 'THẤT BẠI',
    info: 'THÔNG BÁO',
  };

  return (
    <div
      className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast) => {
        const style = typeStyles[toast.type];
        return (
          <div
            key={toast.id}
            role="status"
            className={`pointer-events-auto p-3.5 rounded-xl border-l-4 border shadow-xl ${style.border} ${style.bg} animate-in fade-in slide-in-from-bottom-2 duration-150 flex items-start justify-between gap-3`}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                  [{typeBadges[toast.type]}]
                </span>
                <span className={`text-xs font-bold truncate ${style.title}`}>
                  {toast.title}
                </span>
              </div>
              {toast.message && (
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5 leading-snug">
                  {toast.message}
                </p>
              )}
            </div>

            <button
              type="button"
              onClick={() => removeToast(toast.id)}
              className="text-2xs font-mono font-bold text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 shrink-0 p-1"
              aria-label="Đóng thông báo"
            >
              [X]
            </button>
          </div>
        );
      })}
    </div>
  );
};

