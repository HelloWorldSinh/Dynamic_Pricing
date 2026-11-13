import React from 'react';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'warning' | 'danger' | 'floor' | 'info' | 'neutral' | 'brand';
  size?: '2xs' | 'xs' | 'sm';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'neutral',
  size = 'xs',
  children,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-bold font-mono tracking-tight transition-colors select-none rounded-md border';

  const variants = {
    success:
      'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
    warning:
      'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-800',
    danger:
      'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-900',
    floor:
      'bg-pink-50 dark:bg-pink-950/40 text-pink-700 dark:text-pink-400 border-pink-200 dark:border-pink-900',
    info:
      'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-900',
    neutral:
      'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700',
    brand:
      'bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-900/60',
  };

  const sizes = {
    '2xs': 'text-[10px] px-1.5 py-0.2',
    xs: 'text-[11px] px-2 py-0.5',
    sm: 'text-xs px-2.5 py-1',
  };

  return (
    <span className={cn(baseStyles, variants[variant], sizes[size], className)} {...props}>
      {children}
    </span>
  );
};

