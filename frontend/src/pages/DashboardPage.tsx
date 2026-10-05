import React, { useEffect, useState } from 'react';
import { CrawlControlPanel } from '../components/CrawlControlPanel.js';
import { MatchingReviewTable } from '../components/MatchingReviewTable.js';
import { crawlerApi } from '../api/crawlerApi.js';
import type { SkuMapping } from '../types/index.js';

// Mau du lieu khoi tao mo phong 329 SKU FPT Shop
const INITIAL_SAMPLE_MAPPINGS: SkuMapping[] = [
  {
    id: 1,
    fpt_sku: '00891234',
    fpt_name: 'iPhone 15 Pro Max 256GB',
    competitor_source: 'cellphones',
    competitor_product_name: 'iPhone 15 Pro Max 256GB | Chinh hang VN/A',
    competitor_price: 24990000,
    confidence_score: 0.96,
    match_tier: 'TIER_1_EXACT',
    status: 'APPROVED',
  },
  {
    id: 2,
    fpt_sku: '00891235',
    fpt_name: 'Samsung Galaxy S24 Ultra 12GB 256GB',
    competitor_source: 'hoangha',
    competitor_product_name: 'Samsung Galaxy S24 Ultra (12GB/256GB) - Chinh hang',
    competitor_price: 26490000,
    confidence_score: 0.94,
    match_tier: 'TIER_1_EXACT',
    status: 'APPROVED',
  },
  {
    id: 3,
    fpt_sku: '00891236',
    fpt_name: 'MacBook Air 13 M3 8GB 256GB',
    competitor_source: 'cellphones',
    competitor_product_name: 'Apple MacBook Air M3 13 inch 8GB 256GB 2024',
    competitor_price: 24890000,
    confidence_score: 0.78,
    match_tier: 'TIER_2_FUZZY',
    status: 'PENDING',
  },
  {
    id: 4,
    fpt_sku: '00891237',
    fpt_name: 'Xiaomi Redmi Note 13 6GB 128GB',
    competitor_source: 'hoangha',
    competitor_product_name: 'Xiaomi Redmi Note 13 (6GB/128GB)',
    competitor_price: 4190000,
    confidence_score: 0.91,
    match_tier: 'TIER_1_EXACT',
    status: 'APPROVED',
  },
  {
    id: 5,
    fpt_sku: '00891238',
    fpt_name: 'OPPO Reno11 F 5G 8GB 256GB',
    competitor_source: 'cellphones',
    competitor_product_name: 'OPPO Reno 11F 5G 8GB 256GB',
    competitor_price: 7990000,
    confidence_score: 0.72,
    match_tier: 'TIER_2_FUZZY',
    status: 'PENDING',
  },
];

export const DashboardPage: React.FC = () => {
  const [mappings, setMappings] = useState<SkuMapping[]>(INITIAL_SAMPLE_MAPPINGS);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    crawlerApi
      .checkHealth()
      .then(() => setBackendStatus('online'))
      .catch(() => setBackendStatus('offline'));
  }, []);

  const handleReviewAction = (id: number, action: 'approve' | 'reject') => {
    setMappings((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          return {
            ...item,
            status: action === 'approve' ? 'APPROVED' : 'UNMATCHED',
          };
        }
        return item;
      })
    );
  };

  const totalCount = mappings.length;
  const approvedCount = mappings.filter((m) => m.status === 'APPROVED').length;
  const pendingCount = mappings.filter((m) => m.status === 'PENDING').length;

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>
        <div>
          <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-primary)' }}>
            Dynamic Pricing System
          </h1>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            He thong Ho tro Dinh gia Ban le Tu dong & Giam sat Doi thu Da nguon
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 500 }}>
            Ket noi Backend API:
          </span>
          <span
            style={{
              padding: '0.25rem 0.6rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)',
              fontWeight: 600,
              backgroundColor:
                backendStatus === 'online'
                  ? 'var(--color-status-success-bg)'
                  : backendStatus === 'offline'
                  ? 'var(--color-status-danger-bg)'
                  : 'var(--color-status-neutral-bg)',
              color:
                backendStatus === 'online'
                  ? 'var(--color-status-success-text)'
                  : backendStatus === 'offline'
                  ? 'var(--color-status-danger-text)'
                  : 'var(--color-status-neutral-text)',
              border: '1px solid',
              borderColor:
                backendStatus === 'online'
                  ? 'var(--color-status-success-border)'
                  : backendStatus === 'offline'
                  ? 'var(--color-status-danger-border)'
                  : 'var(--color-status-neutral-border)',
            }}
          >
            {backendStatus === 'online' ? 'CONNECTED (Port 8000)' : backendStatus === 'offline' ? 'DISCONNECTED' : 'CHECKING...'}
          </span>
        </div>
      </header>

      {/* KPI Cards */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1rem' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Tong So SKU Theo Doi
          </div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, marginTop: '0.25rem' }}>
            {totalCount}
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1rem' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Khop Chinh Xac (Approved)
          </div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-status-success-text)', marginTop: '0.25rem' }}>
            {approvedCount}
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1rem' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Cho Phe Duyet (Pending)
          </div>
          <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-status-warning-text)', marginTop: '0.25rem' }}>
            {pendingCount}
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1rem' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>
            Nguon Cào Hien Tai
          </div>
          <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 600, marginTop: '0.5rem', color: 'var(--color-text-secondary)' }}>
            CellphoneS & Hoang Ha
          </div>
        </div>
      </section>

      {/* Crawl Control */}
      <CrawlControlPanel />

      {/* SKU Matching Table */}
      <MatchingReviewTable mappings={mappings} onReviewAction={handleReviewAction} />
    </div>
  );
};
