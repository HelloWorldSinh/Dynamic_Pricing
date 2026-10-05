import React, { useState, useEffect, useMemo } from 'react';
import { GitCompare, CheckCircle2 } from 'lucide-react';
import { SkuDiffCard } from '../components/mapping/SkuDiffCard';
import { Pagination } from '../components/common/Pagination';
import { SkuMappingPair } from '../types/matching';
import { 
  getSkuMappingQueueApi, 
  approveSkuMappingApi, 
  rejectSkuMappingApi 
} from '../api/pricingApi';

export const SkuMatchingPage: React.FC = () => {
  const [queue, setQueue] = useState<SkuMappingPair[]>([]);
  const [loading, setLoading] = useState(true);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const data = await getSkuMappingQueueApi();
      setQueue(data.filter((item) => item.status === 'PENDING'));
    } catch (error) {
      console.error('Lỗi nạp hàng đợi đối soát SKU:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const totalPages = Math.ceil(queue.length / pageSize) || 1;

  // Auto-clamp page if items are removed
  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(Math.max(1, totalPages));
    }
  }, [totalPages, currentPage]);

  const paginatedQueue = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return queue.slice(start, start + pageSize);
  }, [queue, currentPage, pageSize]);

  const handleApprove = async (id: string) => {
    await approveSkuMappingApi(id);
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  const handleReject = async (id: string) => {
    await rejectSkuMappingApi(id);
    setQueue((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <div>
      {/* Intro Header */}
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            SKU Mapping Queue
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 font-semibold font-mono">
              Confidence 60% – 79%
            </span>
          </h2>
        </div>

        <div className="text-xs text-slate-500 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-3 py-2 rounded-xl flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-orange-500" />
          <span><strong className="font-bold text-slate-900 dark:text-white">{queue.length}</strong> items to review</span>
        </div>
      </div>

      {/* Main List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Đang nạp dữ liệu hàng đợi đối soát...
        </div>
      ) : queue.length === 0 ? (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
            Hàng đợi trống!
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Toàn bộ sản phẩm đều đã được đối soát chính xác 100% hoặc vượt ngưỡng tự động.
          </p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {paginatedQueue.map((pair) => (
              <SkuDiffCard
                key={pair.id}
                pair={pair}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))}
          </div>

          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={queue.length}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={(newSize) => {
              setPageSize(newSize);
              setCurrentPage(1);
            }}
            pageSizeOptions={[3, 5, 10, 20]}
            itemLabel="cặp đối soát"
          />
        </>
      )}
    </div>
  );
};
