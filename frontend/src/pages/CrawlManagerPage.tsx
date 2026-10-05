import React, { useState, useEffect } from 'react';
import { SourceStatusCard } from '../components/crawler/SourceStatusCard';
import { CronSchedulePanel } from '../components/crawler/CronSchedulePanel';
import { RawDataInspector } from '../components/crawler/RawDataInspector';
import { CrawlResult } from '../types/crawl';
import { getCrawlResultsApi } from '../api/crawlerApi';

export const CrawlManagerPage: React.FC = () => {
  const [crawlResults, setCrawlResults] = useState<CrawlResult[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchResults = async () => {
    setLoading(true);
    try {
      const data = await getCrawlResultsApi();
      setCrawlResults(data);
    } catch (error) {
      console.error('Lỗi nạp dữ liệu crawler:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  const cellphonesCount = crawlResults.filter((r) => r.source === 'CELLPHONES').length;
  const hoanghaCount = crawlResults.filter((r) => r.source === 'HOANGHA').length;
  const fptCount = crawlResults.filter((r) => r.source === 'FPT').length;

  return (
    <div>
      {/* Intro Header */}
      <div className="mb-6">
        <h2 className="text-sm font-bold text-slate-900 dark:text-white">
          Trung Tâm Vận Hành Thu Thập Dữ Liệu (Crawl Operations)
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Giám sát trạng thái 3 nguồn dữ liệu thị trường, kiểm soát lịch cào tự động và đối soát dữ liệu thô.
        </p>
      </div>

      {/* 3 Source Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
          source="FPT"
          title="FPT Shop Baseline"
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
        <div className="p-12 text-center text-slate-400 text-xs">
          Đang nạp dữ liệu cào thô...
        </div>
      ) : (
        <RawDataInspector items={crawlResults} />
      )}
    </div>
  );
};
