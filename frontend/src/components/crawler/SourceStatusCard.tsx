import React from 'react';
import { CrawlSource } from '../../types/crawl';
import { formatDate } from '../../utils/formatters';
import { Badge } from '../common/Badge';

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
    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-slate-900 dark:text-white tracking-wide">
            {source}
          </span>
          <Badge
            size="sm"
            variant={status === 'HEALTHY' ? 'success' : 'warning'}
          >
            {status}
          </Badge>
        </div>

        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
          {title}
        </h3>
        <p className="text-2xs font-mono text-slate-400 mt-0.5 truncate">{url}</p>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <span className="text-2xs text-slate-400 block font-medium">Thu thập</span>
          <span className="font-bold font-mono text-slate-800 dark:text-slate-200 text-xs">
            {itemsCount.toLocaleString()}
          </span>
        </div>
        <div>
          <span className="text-2xs text-slate-400 block font-medium">Thành công</span>
          <span className="font-bold font-mono text-emerald-600 dark:text-emerald-400 text-xs">
            {successRate}%
          </span>
        </div>
        <div>
          <span className="text-2xs text-slate-400 block font-medium">Lần cuối</span>
          <span className="font-mono text-2xs text-slate-600 dark:text-slate-300 block truncate">
            {formatDate(lastCrawledAt)}
          </span>
        </div>
      </div>
    </div>
  );
};
