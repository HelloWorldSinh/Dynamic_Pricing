import React, { useState } from 'react';
import type { SkuMapping, MappingStatus } from '../types/index.js';

interface MatchingReviewTableProps {
  mappings: SkuMapping[];
  onReviewAction?: (id: number, action: 'approve' | 'reject') => void;
}

export const MatchingReviewTable: React.FC<MatchingReviewTableProps> = ({
  mappings,
  onReviewAction,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredMappings = mappings.filter((item) => {
    const matchStatus = filterStatus === 'ALL' || item.status === filterStatus;
    const matchSearch =
      searchQuery === '' ||
      item.fpt_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.fpt_sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.competitor_product_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchStatus && matchSearch;
  });

  const getStatusBadgeStyle = (status: MappingStatus) => {
    switch (status) {
      case 'APPROVED':
        return {
          backgroundColor: 'var(--color-status-success-bg)',
          color: 'var(--color-status-success-text)',
          borderColor: 'var(--color-status-success-border)',
        };
      case 'PENDING':
        return {
          backgroundColor: 'var(--color-status-warning-bg)',
          color: 'var(--color-status-warning-text)',
          borderColor: 'var(--color-status-warning-border)',
        };
      case 'UNMATCHED':
      default:
        return {
          backgroundColor: 'var(--color-status-danger-bg)',
          color: 'var(--color-status-danger-text)',
          borderColor: 'var(--color-status-danger-border)',
        };
    }
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price);
  };

  const formatPercent = (score: number) => {
    return `${Math.round(score * 100)}%`;
  };

  return (
    <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            Danh Sach Doi Soat San Pham (SKU Mappings)
          </h2>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            Tong cong {filteredMappings.length} ban ghi phu hop
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="Tim kiem theo SKU hoac ten san pham..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '240px'
            }}
          />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{
              padding: '0.45rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              backgroundColor: 'var(--color-bg-surface)'
            }}
          >
            <option value="ALL">Tat ca trang thai</option>
            <option value="APPROVED">Da duyet (APPROVED)</option>
            <option value="PENDING">Cho duyet (PENDING)</option>
            <option value="UNMATCHED">Chua khop (UNMATCHED)</option>
          </select>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--font-size-sm)' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--color-border)', color: 'var(--color-text-muted)' }}>
              <th style={{ padding: '0.75rem 0.5rem' }}>Ma SKU</th>
              <th style={{ padding: '0.75rem 0.5rem' }}>San pham FPT Shop</th>
              <th style={{ padding: '0.75rem 0.5rem' }}>Doi thu & Ten san pham</th>
              <th style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>Gia doi thu</th>
              <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>Do tin cay</th>
              <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>Trang thai</th>
              <th style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>Thao tac</th>
            </tr>
          </thead>
          <tbody>
            {filteredMappings.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                  Khong co ban ghi nao phu hop voi bo loc hien tai.
                </td>
              </tr>
            ) : (
              filteredMappings.map((row) => (
                <tr key={row.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'monospace', fontWeight: 600 }}>
                    {row.fpt_sku}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', fontWeight: 500, color: 'var(--color-text-primary)' }}>
                    {row.fpt_name}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    <div style={{ fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', color: 'var(--color-text-muted)', fontWeight: 600 }}>
                      {row.competitor_source}
                    </div>
                    <div>{row.competitor_product_name}</div>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right', fontWeight: 600 }}>
                    {formatPrice(row.competitor_price)}
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 'var(--font-size-xs)',
                        fontWeight: 600,
                        backgroundColor: row.confidence_score >= 0.85 ? 'var(--color-status-success-bg)' : 'var(--color-status-warning-bg)',
                        color: row.confidence_score >= 0.85 ? 'var(--color-status-success-text)' : 'var(--color-status-warning-text)',
                      }}
                    >
                      {formatPercent(row.confidence_score)}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>
                    <span
                      style={{
                        padding: '0.25rem 0.6rem',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 'var(--font-size-xs)',
                        fontWeight: 600,
                        border: '1px solid',
                        ...getStatusBadgeStyle(row.status),
                      }}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'center' }}>
                    {row.status === 'PENDING' && onReviewAction && (
                      <div style={{ display: 'inline-flex', gap: '0.35rem' }}>
                        <button
                          type="button"
                          onClick={() => onReviewAction(row.id, 'approve')}
                          style={{
                            padding: '0.25rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 'var(--font-size-xs)',
                            fontWeight: 600,
                            backgroundColor: 'var(--color-status-success-bg)',
                            color: 'var(--color-status-success-text)',
                            border: '1px solid var(--color-status-success-border)'
                          }}
                        >
                          Duyet
                        </button>
                        <button
                          type="button"
                          onClick={() => onReviewAction(row.id, 'reject')}
                          style={{
                            padding: '0.25rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 'var(--font-size-xs)',
                            fontWeight: 600,
                            backgroundColor: 'var(--color-status-danger-bg)',
                            color: 'var(--color-status-danger-text)',
                            border: '1px solid var(--color-status-danger-border)'
                          }}
                        >
                          Huy
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
