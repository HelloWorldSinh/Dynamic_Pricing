import React from 'react';
import { CrawlSource } from '../../types/crawl';
import { formatDate } from '../../utils/formatters';

interface SourceStatusCardProps {
  source: CrawlSource;
  title: string;
  url: string;
  lastCrawledAt: string;
  itemsCount: number;
  successRate: number;
  status: 'HEALTHY' | 'DEGRADED';
}

export const SourceStatusCard: React.FC<SourceStatusCardProps> = ({
  source,
  title,
  url,
  lastCrawledAt,
  itemsCount,
  successRate,
  status,
}) => {
  return (
    <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                status === 'HEALTHY' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
              }`}
            />
            <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              {source}
            </span>
          </div>
          <span
            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
              status === 'HEALTHY'
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                : 'bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400'
            }`}
          >
            {status}
          </span>
        </div>

        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          {title}
        </h3>
        <p className="text-[11px] font-mono text-slate-400 mt-0.5 truncate">{url}</p>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <span className="text-[10px] text-slate-400 block">Đã thu thập</span>
          <span className="font-bold font-mono text-slate-800 dark:text-slate-200">
            {itemsCount}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Tỉ lệ thành công</span>
          <span className="font-bold font-mono text-emerald-600 dark:text-emerald-400">
            {successRate}%
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">Lần cào cuối</span>
          <span className="font-mono text-[10px] text-slate-600 dark:text-slate-300 block truncate">
            {formatDate(lastCrawledAt)}
          </span>
        </div>
      </div>
    </div>
  );
};
