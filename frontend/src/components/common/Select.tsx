import React from 'react';
import { cn } from '../../utils/cn';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div className="relative inline-flex items-center">
        <select
          ref={ref}
          className={cn(
            'h-8 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500 font-medium cursor-pointer transition-colors pr-6 appearance-none',
            className
          )}
          {...props}
        >
          {children}
        </select>
        <span className="pointer-events-none absolute right-2 text-2xs text-slate-400 font-mono">
          ▼
        </span>
      </div>
    );
  }
);

Select.displayName = 'Select';

