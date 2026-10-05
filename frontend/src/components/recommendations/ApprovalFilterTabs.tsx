import React from 'react';
import { Clock, CheckCheck, XCircle } from 'lucide-react';

interface ApprovalFilterTabsProps {
  currentTab: 'PENDING' | 'APPROVED' | 'REJECTED';
  onTabChange: (tab: 'PENDING' | 'APPROVED' | 'REJECTED') => void;
  counts: {
    pending: number;
    approved: number;
    rejected: number;
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
      icon: Clock,
      count: counts.pending,
      badgeColor: 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300',
    },
    {
      id: 'APPROVED' as const,
      label: 'Đã phê duyệt',
      icon: CheckCheck,
      count: counts.approved,
      badgeColor: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300',
    },
    {
      id: 'REJECTED' as const,
      label: 'Đã từ chối',
      icon: XCircle,
      count: counts.rejected,
      badgeColor: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    },
  ];

  return (
    <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 mb-6">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = currentTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all duration-150 ${
              isActive
                ? 'border-orange-500 text-orange-600 dark:text-orange-400 bg-orange-50/20 dark:bg-orange-950/20'
                : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            <span>{tab.label}</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${tab.badgeColor}`}>
              {tab.count}
            </span>
          </button>
        );
      })}
    </div>
  );
};
