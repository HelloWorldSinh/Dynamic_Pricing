import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { GitCompare, CheckCircle2, Check, Info, Search, X } from 'lucide-react';
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
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'info' | 'error' } | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'info' | 'error' = 'success') => {
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

      if (itemToApprove) {
        showToast(`Đã duyệt khớp 100%: ${itemToApprove.fpt_sku}`, 'success');
      }
    } catch (error) {
      console.error('Lỗi khi duyệt SKU mapping:', error);
      showToast('Lỗi máy chủ khi duyệt SKU, vui lòng thử lại', 'error');
    }
  }, [queue, filteredQueue, showToast]);

  // Action: Reject
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

      if (itemToReject) {
        showToast(`Đã từ chối khớp SKU: ${itemToReject.fpt_sku}`, 'info');
      }
    } catch (error) {
      console.error('Lỗi khi từ chối SKU mapping:', error);
      showToast('Lỗi máy chủ khi từ chối SKU, vui lòng thử lại', 'error');
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

    const successfulIds: string[] = [];
    for (const id of ids) {
      try {
        await approveSkuMappingApi(id);
        successfulIds.push(id);
      } catch (error) {
        console.error(`Lỗi duyệt SKU ${id}:`, error);
      }
    }

    if (successfulIds.length > 0) {
      const successSet = new Set(successfulIds);
      setQueue((prev) => prev.filter((item) => !successSet.has(item.id)));
      setSelectedBatchIds((prev) => {
        const next = new Set(prev);
        successfulIds.forEach((id) => next.delete(id));
        return next;
      });
      showToast(`Đã duyệt hàng loạt ${successfulIds.length} cặp SKU`, 'success');
    }

    if (successfulIds.length < ids.length) {
      showToast(`Có ${ids.length - successfulIds.length} cặp SKU duyệt thất bại`, 'error');
    }
  };

  const handleBatchReject = async () => {
    const ids = Array.from(selectedBatchIds);
    if (ids.length === 0) return;

    const successfulIds: string[] = [];
    for (const id of ids) {
      try {
        await rejectSkuMappingApi(id);
        successfulIds.push(id);
      } catch (error) {
        console.error(`Lỗi từ chối SKU ${id}:`, error);
      }
    }

    if (successfulIds.length > 0) {
      const successSet = new Set(successfulIds);
      setQueue((prev) => prev.filter((item) => !successSet.has(item.id)));
      setSelectedBatchIds((prev) => {
        const next = new Set(prev);
        successfulIds.forEach((id) => next.delete(id));
        return next;
      });
      showToast(`Đã từ chối hàng loạt ${successfulIds.length} cặp SKU`, 'info');
    }

    if (successfulIds.length < ids.length) {
      showToast(`Có ${ids.length - successfulIds.length} cặp SKU từ chối thất bại`, 'error');
    }
  };

  return (
    <div className="space-y-3">
      {/* 1. Compact Workspace Header (Unified Header, Threshold, Search, Filters, Counter) */}
      <div className="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-wrap items-center justify-between gap-3 shrink-0">
        {/* Left: Title & Threshold Badge */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="p-1.5 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
            <GitCompare className="w-4 h-4" />
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-xs font-bold text-slate-900 dark:text-white whitespace-nowrap">
              SKU Mapping Queue
            </h1>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 font-semibold font-mono">
              Ngưỡng nghi vấn: 60% – 79%
            </span>
          </div>
        </div>

        {/* Center: Search & Filter Pills */}
        <div className="flex items-center gap-2 flex-wrap flex-1 max-w-2xl justify-center sm:justify-start">
          {/* Search Input */}
          <div className="relative min-w-[180px] max-w-xs flex-1">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm theo SKU, tên SP..."
              className="w-full pl-8 pr-7 py-1 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Source Filter Pills */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-medium shrink-0">
            <button
              type="button"
              onClick={() => setSourceFilter('ALL')}
              className={`px-2.5 py-1 rounded-md transition ${
                sourceFilter === 'ALL'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Tất cả
            </button>
            <button
              type="button"
              onClick={() => setSourceFilter('CELLPHONES')}
              className={`px-2.5 py-1 rounded-md transition ${
                sourceFilter === 'CELLPHONES'
                  ? 'bg-red-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              CellphoneS
            </button>
            <button
              type="button"
              onClick={() => setSourceFilter('HOANGHA')}
              className={`px-2.5 py-1 rounded-md transition ${
                sourceFilter === 'HOANGHA'
                  ? 'bg-emerald-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              Hoàng Hà
            </button>
          </div>

          {/* Confidence Filter Pills */}
          <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-0.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-medium shrink-0">
            <button
              type="button"
              onClick={() => setConfidenceFilter(confidenceFilter === 'HIGH' ? 'ALL' : 'HIGH')}
              className={`px-2 py-1 rounded-md transition ${
                confidenceFilter === 'HIGH'
                  ? 'bg-blue-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400'
              }`}
            >
              ≥75%
            </button>
            <button
              type="button"
              onClick={() => setConfidenceFilter(confidenceFilter === 'MID' ? 'ALL' : 'MID')}
              className={`px-2 py-1 rounded-md transition ${
                confidenceFilter === 'MID'
                  ? 'bg-amber-600 text-white font-bold shadow-xs'
                  : 'text-slate-600 dark:text-slate-400'
              }`}
            >
              &lt;75%
            </button>
          </div>
        </div>

        {/* Right: Remaining Counter */}
        <div className="flex items-center gap-2.5 shrink-0 ml-auto">
          <div className="text-xs text-orange-600 dark:text-orange-400 font-semibold bg-orange-50 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-900/60 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
            <span>Còn <strong>{queue.length}</strong> cặp SKU</span>
          </div>
        </div>
      </div>

      {/* 2. Main Split View Container */}
      {loading ? (
        <div className="h-[600px] flex items-center justify-center rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-400">
          Đang nạp dữ liệu hàng đợi đối soát...
        </div>
      ) : queue.length === 0 ? (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-16 text-center shadow-xs">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 dark:text-slate-200">
            Hàng đợi trống!
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            Toàn bộ sản phẩm đối thủ đều đã được khớp tự động hoặc đã hoàn thành quy trình đối soát thủ công.
          </p>
        </div>
      ) : (
        <div className="h-[calc(100vh-140px)] min-h-[580px] flex flex-col lg:flex-row gap-3.5 overflow-hidden">
          {/* Left Pane (32% width): Queue Navigation List */}
          <div className="w-full lg:w-[32%] shrink-0 h-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col">
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
          <div className="flex-1 lg:w-[68%] min-w-0 h-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs flex flex-col">
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
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-medium shadow-2xl animate-in fade-in slide-in-from-bottom-4 ${
          toast.type === 'error'
            ? 'bg-rose-900 text-white dark:bg-rose-950 dark:text-rose-100 border border-rose-700'
            : 'bg-slate-900 text-white dark:bg-white dark:text-slate-900'
        }`}>
          {toast.type === 'success' ? (
            <Check className="w-4 h-4 text-emerald-400 dark:text-emerald-600" />
          ) : toast.type === 'error' ? (
            <Info className="w-4 h-4 text-rose-300 dark:text-rose-400" />
          ) : (
            <Info className="w-4 h-4 text-amber-400 dark:text-amber-600" />
          )}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
};
