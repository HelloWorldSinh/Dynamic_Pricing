import React from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
  hasClear?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', onClear, hasClear, value, ...props }, ref) => {
    return (
      <div className="relative w-full">
        <input
          ref={ref}
          type={type}
          value={value}
          className={cn(
            'w-full h-8 px-3 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 focus:border-orange-500 transition-colors',
            hasClear && value ? 'pr-7' : '',
            className
          )}
          {...props}
        />
        {hasClear && value && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded transition"
            title="Xóa tìm kiếm"
            aria-label="Xóa nội dung tìm kiếm"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

