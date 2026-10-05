import React from 'react';
import { 
  BarChart3, 
  CheckCheck, 
  GitCompare, 
  RefreshCw, 
  Bot, 
  ChevronLeft, 
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

export type NavTab = 'matrix' | 'approvals' | 'mapping' | 'crawler' | 'ai';

interface SidebarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  isCollapsed: boolean;
  setIsCollapsed: (collapsed: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  isCollapsed,
  setIsCollapsed,
}) => {
  const navItems = [
    {
      id: 'matrix' as NavTab,
      label: 'Price Matrix',
      description: 'So sánh giá 3 bên',
      icon: BarChart3,
      badge: 'Live',
    },
    {
      id: 'approvals' as NavTab,
      label: 'Pricing Approvals',
      description: 'Duyệt giá theo DOH',
      icon: CheckCheck,
      badge: '5 chờ duyệt',
    },
    {
      id: 'mapping' as NavTab,
      label: 'SKU Mapping Queue',
      description: 'Đối soát 60-79%',
      icon: GitCompare,
      badge: '3',
    },
    {
      id: 'crawler' as NavTab,
      label: 'Crawl Operations',
      description: 'Giám sát 3 nguồn',
      icon: RefreshCw,
    },
    {
      id: 'ai' as NavTab,
      label: 'AI Pricing Studio',
      description: 'Hỏi đáp & Explainable AI',
      icon: Bot,
      badge: 'RAG',
    },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen transition-all duration-300 ease-in-out border-r flex flex-col justify-between
        bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-200
        ${isCollapsed ? 'w-20' : 'w-64'}`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-orange-600 flex items-center justify-center text-white font-black text-lg shadow-lg shadow-orange-600/30 flex-shrink-0">
              FPT
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-white truncate">
                  Dynamic Pricing
                </span>
                <span className="text-[11px] font-medium text-orange-600 dark:text-orange-400 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 inline" /> Floor Protected
                </span>
              </div>
            )}
          </div>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition"
            title={isCollapsed ? 'Mở rộng menu' : 'Thu gọn menu'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-150 group relative
                  ${
                    isActive
                      ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 font-semibold border border-orange-500/30'
                      : 'hover:bg-slate-100 dark:hover:bg-slate-800/60 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
                  }`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-5 h-5 flex-shrink-0 transition-transform group-hover:scale-110 ${
                    isActive ? 'text-orange-600 dark:text-orange-400' : 'text-slate-500 dark:text-slate-400'
                  }`}
                />
                {!isCollapsed && (
                  <div className="flex-1 flex items-center justify-between min-w-0">
                    <div className="truncate">
                      <div className="text-xs font-medium leading-none">{item.label}</div>
                      <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-1 truncate">
                        {item.description}
                      </div>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ml-2 flex-shrink-0 ${
                          isActive
                            ? 'bg-orange-600 text-white'
                            : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer Actor Profile */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3 p-2 rounded-xl bg-slate-50 dark:bg-slate-800/40">
          <div className="w-8 h-8 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-xs text-slate-700 dark:text-slate-200">
            PA
          </div>
          {!isCollapsed && (
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                Pricing Analyst
              </div>
              <div className="text-[10px] text-slate-500 truncate">Single User / FPT Retail</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
