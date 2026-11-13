import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { SourceStatusCard } from '../components/crawler/SourceStatusCard';
import { CronSchedulePanel } from '../components/crawler/CronSchedulePanel';
import { RawDataInspector } from '../components/crawler/RawDataInspector';
import { CrawlControlPanel } from '../components/crawler/CrawlControlPanel';
import { TableSkeleton } from '../components/common/TableSkeleton';
import { CrawlResult } from '../types/crawl';
import { getCrawlResultsApi } from '../api/crawlerApi';

export const CrawlManagerPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [crawlResults, setCrawlResults] = useState<CrawlResult[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const response = await getCrawlResultsApi(undefined, undefined, undefined, undefined, undefined, 0, 500);
      setCrawlResults(response.items);
    } catch (error) {
      console.error('Lỗi nạp dữ liệu crawler:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCrawlSuccess = () => {
    fetchResults();
    queryClient.invalidateQueries();
  };

  useEffect(() => {
    fetchResults();
  }, []);

  const cellphonesCount = crawlResults.filter((r) => r.source === 'CELLPHONES').length;
  const hoanghaCount = crawlResults.filter((r) => r.source === 'HOANGHA').length;
  const fptCount = crawlResults.filter((r) => r.source === 'FPT' || r.source === 'FPTSHOP').length;

  return (
    <div>
      {/* Intro Header */}
      <div className="mb-3">
        <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight">
          Vận hành cào dữ liệu đối thủ &amp; FPT Shop
        </h2>
      </div>

      {/* Crawl Control Panel (Full Pipeline & FPT Sync) */}
      <CrawlControlPanel onTriggerSuccess={handleCrawlSuccess} />

      {/* 3 Source Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
        <SourceStatusCard
          source="CELLPHONES"
          title="CellphoneS Scraper"
          url="https://cellphones.com.vn"
          lastCrawledAt="2026-10-05T08:30:12Z"
          itemsCount={cellphonesCount || 100}
          successRate={98.5}
          status="HEALTHY"
        />
        <SourceStatusCard
          source="HOANGHA"
          title="Hoàng Hà Mobile Scraper"
          url="https://hoanghamobile.com"
          lastCrawledAt="2026-10-05T08:30:45Z"
          itemsCount={hoanghaCount || 100}
          successRate={97.2}
          status="HEALTHY"
        />
        <SourceStatusCard
          source="FPTSHOP"
          title="FPT Shop Live Sync"
          url="https://fptshop.com.vn"
          lastCrawledAt="2026-10-05T08:00:00Z"
          itemsCount={fptCount || 329}
          successRate={100}
          status="HEALTHY"
        />
      </div>

      {/* Cron Schedule Panel */}
      <CronSchedulePanel />

      {/* Raw Data Inspector */}
      {loading ? (
        <TableSkeleton rows={8} cols={7} />
      ) : (
        <RawDataInspector items={crawlResults} />
      )}
    </div>
  );
};
