import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { X } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { SkuMappingPair } from '../types/matching';
import { 
  approveSkuMappingApi, 
  rejectSkuMappingApi 
} from '../api/pricingApi';
import { useSkuMappingQueueQuery, invalidateSkuQueries } from '../hooks/useSkuQueries';
import { SkuQueueList } from '../components/mapping/SkuQueueList';
import { SkuDetailInspector } from '../components/mapping/SkuDetailInspector';
import { useToast } from '../context/ToastContext';
import { Badge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';
import { TableSkeleton } from '../components/common/TableSkeleton';

export const SkuMatchingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { data: queueData = [], isLoading, isFetching } = useSkuMappingQueueQuery();

  const [queue, setQueue] = useState<SkuMappingPair[]>([]);
  const loading = isLoading && queue.length === 0;
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedBatchIds, setSelectedBatchIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (queueData.length > 0) {
      setQueue(queueData);
      setSelectedId((prev) => prev || queueData[0]?.id || null);
    }
  }, [queueData]);

  const [searchQuery, setSearchQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState<'ALL' | 'CELLPHONES' | 'HOANGHA'>('ALL');
  const [confidenceFilter, setConfidenceFilter] = useState<'ALL' | 'HIGH' | 'MID'>('ALL');

  const filteredQueue = useMemo(() => {
    return queue.filter((item) => {
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesFpt = item.fpt_name.toLowerCase().includes(q) || item.fpt_sku.toLowerCase().includes(q) || (item.fpt_part_number && item.fpt_part_number.toLowerCase().includes(q));
        const matchesComp = item.competitor_name.toLowerCase().includes(q) || (item.competitor_part_number && item.competitor_part_number.toLowerCase().includes(q));
        if (!matchesFpt && !matchesComp) return false;
      }

      if (sourceFilter !== 'ALL' && item.competitor_source !== sourceFilter) {
        return false;
      }

      if (confidenceFilter === 'HIGH' && item.confidence_score < 75) {
        return false;
      }
      if (confidenceFilter === 'MID' && item.confidence_score >= 75) {
        return false;
      }

      return true;
    });
  }, [queue, searchQuery, sourceFilter, confidenceFilter]);

  useEffect(() => {
    if (filteredQueue.length === 0) {
      setSelectedId(null);
    } else if (!selectedId || !filteredQueue.some((i) => i.id === selectedId)) {
      setSelectedId(filteredQueue[0].id);
    }
  }, [filteredQueue, selectedId]);

  const selectedItem = useMemo(() => {
    return filteredQueue.find((i) => i.id === selectedId) || null;
  }, [filteredQueue, selectedId]);

  const currentIndex = useMemo(() => {
    if (!selectedId) return 0;
    return filteredQueue.findIndex((i) => i.id === selectedId);
  }, [filteredQueue, selectedId]);

  const handleApprove = useCallback(async (id: string) => {
    const itemToApprove = queue.find((i) => i.id === id);
    const currIdx = filteredQueue.findIndex((i) => i.id === id);
    const nextItem = filteredQueue[currIdx + 1] || filteredQueue[currIdx - 1] || null;

    try {
      await approveSkuMappingApi(id);
      setQueue((prev) => prev.filter((item) => item.id !== id));
      setSelectedBatchIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });

      if (nextItem) {
        setSelectedId(nextItem.id);
      }

      invalidateSkuQueries(queryClient);
      showToast({
        title: 'Khớp thành công',
        message: `Đã xác nhận SKU ${itemToApprove?.fpt_sku || id}`,
        type: 'success',
      });
    } catch (error) {
      console.error('Lỗi duyệt SKU:', error);
      showToast({
        title: 'Lỗi',
        message: 'Không thể duyệt cặp SKU này',
        type: 'danger',
      });
    }
  }, [queue, filteredQueue, queryClient, showToast]);

  const handleReject = useCallback(async (id: string) => {
    const itemToReject = queue.find((i) => i.id === id);
    const currIdx = filteredQueue.findIndex((i) => i.id === id);
    const nextItem = filteredQueue[currIdx + 1] || filteredQueue[currIdx - 1] || null;

    try {
      await rejectSkuMappingApi(id);
      setQueue((prev) => prev.filter((item) => item.id !== id));
      setSelectedBatchIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });

      if (nextItem) {
        setSelectedId(nextItem.id);
      }

      invalidateSkuQueries(queryClient);
      showToast({
        title: 'Đã từ chối',
        message: `Đã loại bỏ cặp SKU ${itemToReject?.fpt_sku || id}`,
        type: 'info',
      });
    } catch (error) {
      console.error('Lỗi từ chối SKU:', error);
      showToast({
        title: 'Lỗi',
        message: 'Không thể từ chối cặp SKU này',
        type: 'danger',
      });
    }
  }, [queue, filteredQueue, queryClient, showToast]);

  const handleToggleBatch = useCallback((id: string) => {
    setSelectedBatchIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const handleSelectAllBatch = useCallback((selectAll: boolean) => {
    if (selectAll) {
      const allIds = new Set(filteredQueue.map((item) => item.id));
      setSelectedBatchIds(allIds);
    } else {
      setSelectedBatchIds(new Set());
    }
  }, [filteredQueue]);

  const handleBatchApprove = useCallback(async () => {
    const ids = Array.from(selectedBatchIds);
    if (ids.length === 0) return;

    try {
      await Promise.all(ids.map((id) => approveSkuMappingApi(id)));
      setQueue((prev) => prev.filter((item) => !selectedBatchIds.has(item.id)));
      setSelectedBatchIds(new Set());
      invalidateSkuQueries(queryClient);
      showToast({
        title: 'Thành công',
        message: `Đã xác nhận khớp ${ids.length} SKU hàng loạt`,
        type: 'success',
      });
    } catch (error) {
      console.error('Lỗi duyệt hàng loạt:', error);
      showToast({
        title: 'Lỗi',
        message: 'Có lỗi xảy ra khi phê duyệt hàng loạt',
        type: 'danger',
      });
    }
  }, [selectedBatchIds, queryClient, showToast]);

  const handleBatchReject = useCallback(async () => {
    const ids = Array.from(selectedBatchIds);
    if (ids.length === 0) return;

    try {
      await Promise.all(ids.map((id) => rejectSkuMappingApi(id)));
      setQueue((prev) => prev.filter((item) => !selectedBatchIds.has(item.id)));
      setSelectedBatchIds(new Set());
      invalidateSkuQueries(queryClient);
      showToast({
        title: 'Đã từ chối',
        message: `Đã từ chối ${ids.length} SKU hàng loạt`,
        type: 'info',
      });
    } catch (error) {
      console.error('Lỗi từ chối hàng loạt:', error);
      showToast({
        title: 'Lỗi',
        message: 'Có lỗi xảy ra khi từ chối hàng loạt',
        type: 'danger',
      });
    }
  }, [selectedBatchIds, queryClient, showToast]);

  return (
    <div>
      {/* Intro Header */}
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight">
          Hàng đợi đối soát SKU
        </h2>
        {isFetching && !loading && (
          <span className="text-2xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2.5 py-0.5 rounded-full border border-slate-200 dark:border-slate-700">
            Đang đồng bộ dữ liệu...
          </span>
        )}
      </div>

      {/* Control Filter Bar */}
      <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 mb-3.5 shadow-xs flex flex-wrap items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo SKU, tên sản phẩm hoặc Part-Number..."
            className="w-full px-3 py-1.5 text-xs rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 transition"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-0.5 rounded transition"
              aria-label="Xóa tìm kiếm"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Source and Confidence Filter Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Source Filter Pills */}
          <div className="flex items-center gap-1">
            <span className="text-2xs font-semibold text-slate-400 mr-0.5">Nguồn:</span>
            <button
              type="button"
              onClick={() => setSourceFilter('ALL')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                sourceFilter === 'ALL'
                  ? 'bg-orange-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Tất cả
            </button>
            <button
              type="button"
              onClick={() => setSourceFilter('CELLPHONES')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                sourceFilter === 'CELLPHONES'
                  ? 'bg-rose-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              CellphoneS
            </button>
            <button
              type="button"
              onClick={() => setSourceFilter('HOANGHA')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                sourceFilter === 'HOANGHA'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Hoàng Hà
            </button>
          </div>

          {/* Confidence Filter Pills */}
          <div className="flex items-center gap-1 ml-2">
            <span className="text-2xs font-semibold text-slate-400 mr-0.5">Độ tin cậy:</span>
            <button
              type="button"
              onClick={() => setConfidenceFilter(confidenceFilter === 'HIGH' ? 'ALL' : 'HIGH')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                confidenceFilter === 'HIGH'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
              }`}
            >
              ≥ 75%
            </button>
            <button
              type="button"
              onClick={() => setConfidenceFilter(confidenceFilter === 'MID' ? 'ALL' : 'MID')}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                confidenceFilter === 'MID'
                  ? 'bg-amber-600 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
              }`}
            >
              &lt; 75%
            </button>
          </div>
        </div>

        {/* Counter Badge */}
        <div className="shrink-0 ml-auto">
          <Badge size="sm" variant="warning">
            Còn {queue.length} cặp SKU
          </Badge>
        </div>
      </div>

      {/* Main Split View Container */}
      {loading ? (
        <TableSkeleton rows={8} cols={4} />
      ) : queue.length === 0 ? (
        <EmptyState
          title="Hàng đợi đối soát trống"
          description="Toàn bộ sản phẩm đối thủ đều đã được khớp tự động hoặc đã hoàn thành quy trình đối soát thủ công."
        />
      ) : (
        <div className="min-h-[580px] lg:h-[calc(100vh-210px)] flex flex-col lg:flex-row gap-3.5">
          {/* Left Pane (32% width): Queue Navigation List */}
          <div className="w-full lg:w-[32%] shrink-0 h-[450px] lg:h-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col">
            <SkuQueueList
              queue={filteredQueue}
              totalCount={queue.length}
              selectedId={selectedId}
              onSelect={setSelectedId}
              selectedBatchIds={selectedBatchIds}
              onToggleBatch={handleToggleBatch}
              onSelectAllBatch={handleSelectAllBatch}
              onBatchApprove={handleBatchApprove}
              onBatchReject={handleBatchReject}
            />
          </div>

          {/* Right Pane (68% width): Unified Diff Workbench */}
          <div className="flex-1 lg:w-[68%] min-w-0 h-[500px] lg:h-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col">
            <SkuDetailInspector
              pair={selectedItem}
              currentIndex={currentIndex}
              totalInQueue={filteredQueue.length}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          </div>
        </div>
      )}
    </div>
  );
};
