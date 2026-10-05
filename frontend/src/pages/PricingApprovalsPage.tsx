import React, { useState, useEffect } from 'react';
import { ApprovalFilterTabs } from '../components/recommendations/ApprovalFilterTabs';
import { BatchActionBar } from '../components/recommendations/BatchActionBar';
import { RecommendationTable } from '../components/recommendations/RecommendationTable';
import { PricingRecommendation } from '../types/pricing';
import { 
  getRecommendationsApi, 
  approveRecommendationApi, 
  rejectRecommendationApi 
} from '../api/pricingApi';

interface PricingApprovalsPageProps {
  categoryFilter: string;
}

export const PricingApprovalsPage: React.FC<PricingApprovalsPageProps> = ({
  categoryFilter,
}) => {
  const [recommendations, setRecommendations] = useState<PricingRecommendation[]>([]);
  const [currentTab, setCurrentTab] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const data = await getRecommendationsApi();
      setRecommendations(data);
    } catch (error) {
      console.error('Lỗi nạp danh sách đề xuất giá:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  // Filter items according to tab & category
  const filteredItems = recommendations.filter((r) => {
    if (r.status !== currentTab) return false;
    if (categoryFilter !== 'ALL' && r.category !== categoryFilter) return false;
    return true;
  });

  const counts = {
    pending: recommendations.filter((r) => r.status === 'PENDING').length,
    approved: recommendations.filter((r) => r.status === 'APPROVED').length,
    rejected: recommendations.filter((r) => r.status === 'REJECTED').length,
  };

  // Selection handlers
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleToggleSelectAll = () => {
    if (selectedIds.length === filteredItems.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredItems.map((i) => i.id));
    }
  };

  const handleClearSelection = () => {
    setSelectedIds([]);
  };

  // Actions
  const handleApprove = async (id: string) => {
    await approveRecommendationApi(id);
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'APPROVED' } : r))
    );
    setSelectedIds((prev) => prev.filter((i) => i !== id));
  };

  const handleReject = async (id: string) => {
    await rejectRecommendationApi(id);
    setRecommendations((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'REJECTED' } : r))
    );
    setSelectedIds((prev) => prev.filter((i) => i !== id));
  };

  const handleBatchApprove = async () => {
    for (const id of selectedIds) {
      await approveRecommendationApi(id);
    }
    setRecommendations((prev) =>
      prev.map((r) => (selectedIds.includes(r.id) ? { ...r, status: 'APPROVED' } : r))
    );
    setSelectedIds([]);
  };

  const handleBatchReject = async () => {
    for (const id of selectedIds) {
      await rejectRecommendationApi(id);
    }
    setRecommendations((prev) =>
      prev.map((r) => (selectedIds.includes(r.id) ? { ...r, status: 'REJECTED' } : r))
    );
    setSelectedIds([]);
  };

  return (
    <div>
      {/* Intro Header */}
      <div className="mb-4">
        <h2 className="text-base font-bold text-slate-900 dark:text-white">
          Pricing Approvals
        </h2>
      </div>

      {/* Tabs */}
      <ApprovalFilterTabs
        currentTab={currentTab}
        onTabChange={(tab) => {
          setCurrentTab(tab);
          setSelectedIds([]);
        }}
        counts={counts}
      />

      {/* Batch Action Bar */}
      <BatchActionBar
        selectedCount={selectedIds.length}
        onBatchApprove={handleBatchApprove}
        onBatchReject={handleBatchReject}
        onClearSelection={handleClearSelection}
      />

      {/* Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Đang nạp danh sách đề xuất giá...
        </div>
      ) : (
        <RecommendationTable
          items={filteredItems}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onToggleSelectAll={handleToggleSelectAll}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}
    </div>
  );
};
