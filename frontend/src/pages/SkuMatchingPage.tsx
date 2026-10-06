import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { GitCompare, CheckCircle2, Sparkles, Check, Info } from 'lucide-react';
import { SkuMappingPair } from '../types/matching';
import { 
  getSkuMappingQueueApi, 
  approveSkuMappingApi, 
  rejectSkuMappingApi 
} from '../api/pricingApi';
import { SkuQueueList } from '../components/mapping/SkuQueueList';
import { SkuDetailInspector } from '../components/mapping/SkuDetailInspector';

export const SkuMatchingPage: React.FC = () => {
  const [queue, setQueue] = useState<SkuMappingPair[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedBatchIds, setSelectedBatchIds] = useState<Set<string>>(new Set());

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState<'ALL' | 'CELLPHONES' | 'HOANGHA'>('ALL');
  const [confidenceFilter, setConfidenceFilter] = useState<'ALL' | 'HIGH' | 'MID'>('ALL');

  // Toast notification
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'info' = 'success') => {
    setToast({ message, type });
    const timer = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(timer);
  }, []);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const data = await getSkuMappingQueueApi();
      const pendingItems = data.filter((item) => item.status === 'PENDING');
      setQueue(pendingItems);
      if (pendingItems.length > 0) {
        setSelectedId(pendingItems[0].id);
      }
    } catch (error) {
      console.error('Lỗi nạp hàng đợi đối soát SKU:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  // Filtered queue calculation
  const filteredQueue = useMemo(() => {
    return queue.filter((item) => {
      // 1. Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesFpt = item.fpt_name.toLowerCase().includes(q) || item.fpt_sku.toLowerCase().includes(q) || (item.fpt_part_number && item.fpt_part_number.toLowerCase().includes(q));
        const matchesComp = item.competitor_name.toLowerCase().includes(q) || (item.competitor_part_number && item.competitor_part_number.toLowerCase().includes(q));
        if (!matchesFpt && !matchesComp) return false;
      }

      // 2. Source filter
      if (sourceFilter !== 'ALL' && item.competitor_source !== sourceFilter) {
        return false;
      }

      // 3. Confidence filter
      if (confidenceFilter === 'HIGH' && item.confidence_score < 75) {
        return false;
      }
      if (confidenceFilter === 'MID' && item.confidence_score >= 75) {
        return false;
      }

      return true;
    });
  }, [queue, searchQuery, sourceFilter, confidenceFilter]);

  // Keep selectedId valid
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

  // Action: Approve
  const handleApprove = useCallback(async (id: string) => {
    const itemToApprove = queue.find((i) => i.id === id);
    const currIdx = filteredQueue.findIndex((i) => i.id === id);
    const nextItem = filteredQueue[currIdx + 1] || filteredQueue[currIdx - 1] || null;

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

    if (itemToApprove) {
      showToast(`Đã duyệt khớp 100%: ${itemToApprove.fpt_sku}`, 'success');
    }
  }, [queue, filteredQueue, showToast]);

  // Action: Reject
  const handleReject = useCallback(async (id: string) => {
    const itemToReject = queue.find((i) => i.id === id);
    const currIdx = filteredQueue.findIndex((i) => i.id === id);
    const nextItem = filteredQueue[currIdx + 1] || filteredQueue[currIdx - 1] || null;

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

    if (itemToReject) {
      showToast(`Đã từ chối khớp SKU: ${itemToReject.fpt_sku}`, 'info');
    }
  }, [queue, filteredQueue, showToast]);

  // Batch actions
  const handleToggleBatch = (id: string) => {
    setSelectedBatchIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAllBatch = (selectAll: boolean) => {
    if (selectAll) {
      setSelectedBatchIds(new Set(filteredQueue.map((i) => i.id)));
    } else {
      setSelectedBatchIds(new Set());
    }
  };

  const handleBatchApprove = async () => {
    const ids = Array.from(selectedBatchIds);
    if (ids.length === 0) return;

    for (const id of ids) {
      await approveSkuMappingApi(id);
    }

    setQueue((prev) => prev.filter((item) => !selectedBatchIds.has(item.id)));
    setSelectedBatchIds(new Set());
    showToast(`Đã duyệt hàng loạt ${ids.length} cặp SKU`, 'success');
  };

  const handleBatchReject = async () => {
    const ids = Array.from(selectedBatchIds);
    if (ids.length === 0) return;

    for (const id of ids) {
      await rejectSkuMappingApi(id);
    }

    setQueue((prev) => prev.filter((item) => !selectedBatchIds.has(item.id)));
    setSelectedBatchIds(new Set());
    showToast(`Đã từ chối hàng loạt ${ids.length} cặp SKU`, 'info');
  };

  return (
    <div className="space-y-3">
      {/* Page Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Đối Soát Sản Phẩm Đối Thủ (SKU Mapping Workspace)
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 font-semibold font-mono">
                Ngưỡng nghi vấn: 60% – 79%
              </span>
            </h1>
            <p className="text-[11px] text-slate-500">
              Chế độ Master-Detail Split View: Soi sâu và đối chiếu thông số kỹ thuật sản phẩm
            </p>
          </div>
        </div>

        {/* Counter */}
        <div className="flex items-center gap-3">
          <div className="text-xs text-slate-600 dark:text-slate-300 font-medium bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-900 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
            <span>Còn <strong>{queue.length}</strong> cặp SKU</span>
          </div>
        </div>
      </div>

      {/* Main Split View Container */}
      {loading ? (
        <div className="h-[600px] flex items-center justify-center rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-400">
          Đang nạp dữ liệu hàng đợi đối soát...
        </div>
      ) : queue.length === 0 ? (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-16 text-center shadow-sm">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            Hàng đợi trống!
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            Toàn bộ sản phẩm đối thủ đều đã được khớp tự động hoặc đã hoàn thành quy trình đối soát thủ công.
          </p>
        </div>
      ) : (
        <div className="h-[calc(100vh-140px)] min-h-[620px] flex flex-col lg:flex-row gap-3.5 overflow-hidden">
          {/* Left Pane (35% - 40%): Queue Navigation List */}
          <div className="w-full lg:w-[380px] xl:w-[410px] shrink-0 h-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-col">
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
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              sourceFilter={sourceFilter}
              onSourceFilterChange={setSourceFilter}
              confidenceFilter={confidenceFilter}
              onConfidenceFilterChange={setConfidenceFilter}
            />
          </div>

          {/* Right Pane (60% - 65%): Deep Diff Inspector */}
          <div className="flex-1 min-w-0 h-full overflow-hidden">
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

      {/* Floating Notification Toast */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 text-white dark:bg-white dark:text-slate-900 text-xs font-medium shadow-2xl animate-in fade-in slide-in-from-bottom-4">
          {toast.type === 'success' ? (
            <Check className="w-4 h-4 text-emerald-400 dark:text-emerald-600" />
          ) : (
            <Info className="w-4 h-4 text-amber-400 dark:text-amber-600" />
          )}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
};
