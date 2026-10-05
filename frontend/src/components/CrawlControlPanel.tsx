import React, { useState } from 'react';
import { crawlerApi } from '../api/crawlerApi.js';
import type { CompetitorSource } from '../types/index.js';

interface CrawlControlPanelProps {
  onTriggerSuccess?: (source: string, taskId: string) => void;
}

export const CrawlControlPanel: React.FC<CrawlControlPanelProps> = ({ onTriggerSuccess }) => {
  const [selectedSource, setSelectedSource] = useState<CompetitorSource>('cellphones');
  const [selectedCategory, setSelectedCategory] = useState<string>('phone');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleTrigger = async () => {
    setIsLoading(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const response = await crawlerApi.trigger({
        source: selectedSource,
        category: selectedCategory,
      });

      setStatusMessage(`Da tiep nhan yeu cau cao gia (${response.task_id}). He thong dang xu ly ngam.`);
      if (onTriggerSuccess) {
        onTriggerSuccess(selectedSource, response.task_id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Khong the kich hoat cao gia.';
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ backgroundColor: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: '1.25rem', marginBottom: '1.5rem' }}>
      <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: '0.25rem' }}>
        Bang Dieu Khien Cao Du Lieu Doi Thu (Crawler Engine)
      </h2>
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: '1rem' }}>
        Kich hoat tien trinh thu thap gia thoi gian thuc. Co che Debounce 30 giay bao ve he thong.
      </p>

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '0.35rem' }}>
            Nguon Doi Thu
          </label>
          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value as CompetitorSource)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '160px',
              backgroundColor: 'var(--color-bg-surface)'
            }}
          >
            <option value="cellphones">CellphoneS</option>
            <option value="hoangha">Hoang Ha Mobile</option>
            <option value="fptshop">FPT Shop (Internal)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: '0.35rem' }}>
            Nganh Hang
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: '0.5rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              fontSize: 'var(--font-size-sm)',
              minWidth: '140px',
              backgroundColor: 'var(--color-bg-surface)'
            }}
          >
            <option value="phone">Dien thoai</option>
            <option value="laptop">Laptop</option>
          </select>
        </div>

        <button
          type="button"
          onClick={handleTrigger}
          disabled={isLoading}
          style={{
            padding: '0.5rem 1.25rem',
            borderRadius: 'var(--radius-md)',
            backgroundColor: isLoading ? 'var(--color-text-muted)' : 'var(--color-primary)',
            color: 'var(--color-text-inverse)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
            cursor: isLoading ? 'not-allowed' : 'pointer',
            transition: 'background-color 0.15s ease'
          }}
        >
          {isLoading ? 'Dang gui yeu cau...' : 'Kich hoat cao ngay'}
        </button>
      </div>

      {statusMessage && (
        <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: 'var(--color-status-success-bg)', color: 'var(--color-status-success-text)', border: '1px solid var(--color-status-success-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }}>
          {statusMessage}
        </div>
      )}

      {errorMessage && (
        <div style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: 'var(--color-status-danger-bg)', color: 'var(--color-status-danger-text)', border: '1px solid var(--color-status-danger-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }}>
          {errorMessage}
        </div>
      )}
    </div>
  );
};
