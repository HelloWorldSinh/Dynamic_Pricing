import React, { useState, useEffect, useCallback } from 'react';
import { Navbar, NavTab } from './Navbar';

const STORAGE_ACTIVE_TAB = 'dynamic_pricing_active_nav_tab';
const VALID_TABS: NavTab[] = ['matrix', 'approvals', 'mapping', 'feeds', 'crawler'];

const getInitialTab = (): NavTab => {
  if (typeof window !== 'undefined') {
    // 1. Ưu tiên URL hash (ví dụ: #mapping, #approvals)
    const hash = window.location.hash.replace(/^#\/?/, '').trim() as NavTab;
    if (VALID_TABS.includes(hash)) {
      return hash;
    }
    // 2. Fallback tới localStorage
    const saved = localStorage.getItem(STORAGE_ACTIVE_TAB) as NavTab;
    if (VALID_TABS.includes(saved)) {
      return saved;
    }
  }
  return 'matrix';
};

interface AppLayoutProps {
  children: (props: { activeTab: NavTab; categoryFilter: string }) => React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [activeTab, setActiveTabState] = useState<NavTab>(getInitialTab);
  const [categoryFilter] = useState<string>('ALL');

  const setActiveTab = useCallback((tab: NavTab) => {
    setActiveTabState(tab);
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_ACTIVE_TAB, tab);
      if (window.location.hash.replace(/^#\/?/, '') !== tab) {
        window.location.hash = tab;
      }
    }
  }, []);

  // Đồng bộ hash ban đầu nếu URL chưa có hash
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const currentHash = window.location.hash.replace(/^#\/?/, '').trim();
      if (!currentHash && activeTab) {
        window.location.hash = activeTab;
      }
    }
  }, [activeTab]);

  // Lắng nghe sự kiện hashchange khi người dùng bấm nút Back/Forward trên trình duyệt
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace(/^#\/?/, '').trim() as NavTab;
      if (VALID_TABS.includes(hash)) {
        setActiveTabState(hash);
        localStorage.setItem(STORAGE_ACTIVE_TAB, hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-200">
      {/* Top Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Content Area - 100% Viewport Width */}
      <main className="flex-1 w-full px-6 py-6 transition-all duration-200">
        {children({ activeTab, categoryFilter })}
      </main>
    </div>
  );
};

