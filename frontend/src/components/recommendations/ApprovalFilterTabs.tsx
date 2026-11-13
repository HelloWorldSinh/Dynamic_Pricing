import React from 'react';
import { ApprovalTabType } from '../../types/pricing';
import { Badge } from '../common/Badge';

interface ApprovalFilterTabsProps {
  currentTab: ApprovalTabType;
  onTabChange: (tab: ApprovalTabType) => void;
  counts: {
    pending: number;
    approved: number;
    rejected: number;
    history?: number;
  };
}

export const ApprovalFilterTabs: React.FC<ApprovalFilterTabsProps> = ({
  currentTab,
  onTabChange,
  counts,
}) => {
  const tabs = [
    {
      id: 'PENDING' as const,
      label: 'Chờ duyệt',
      count: counts.pending,
      variant: 'warning' as const,
    },
    {
      id: 'APPROVED' as const,
      label: 'Đã phê duyệt',
      count: counts.approved,
      variant: 'success' as const,
    },
    {
      id: 'REJECTED' as const,
      label: 'Đã từ chối',
      count: counts.rejected,
      variant: 'neutral' as const,
    },
    {
      id: 'HISTORY' as const,
      label: 'Lịch sử thay đổi giá',
      count: counts.history ?? 0,
      variant: 'info' as const,
    },
  ];

  return (
    <div className="flex items-center gap-1.5 border-b border-slate-200 dark:border-slate-800 mb-4 overflow-x-auto no-scrollbar">
      {tabs.map((tab) => {
        const isActive = currentTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-all duration-150 whitespace-nowrap ${
              isActive
                ? 'border-orange-600 text-orange-600 dark:text-orange-400 bg-orange-50/20 dark:bg-orange-950/20'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <span>{tab.label}</span>
            <Badge size="sm" variant={tab.variant}>
              {tab.count}
            </Badge>
          </button>
        );
      })}
    </div>
  );
};
