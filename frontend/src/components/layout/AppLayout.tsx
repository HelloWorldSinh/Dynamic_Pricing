import React, { useState, useEffect, useCallback } from 'react';
import { Navbar, NavTab } from './Navbar';
import { ToastProvider } from '../../context/ToastContext';
import { ToastContainer } from '../common/ToastContainer';

const STORAGE_ACTIVE_TAB = 'dynamic_pricing_active_nav_tab';
const VALID_TABS: NavTab[] = ['matrix', 'approvals', 'mapping', 'crawler'];

const getInitialTab = (): NavTab => {
  if (typeof window !== 'undefined') {
    // 1. Ưu tiên URL hash (ví dụ: #matrix, #approvals, #mapping)
    const hash = window.location.hash.replace(/^#\/?/, '').trim();
    if (hash === 'dashboard' || hash === 'feeds') {
      window.location.hash = 'matrix';
      localStorage.setItem(STORAGE_ACTIVE_TAB, 'matrix');
      return 'matrix';
    }
    if (VALID_TABS.includes(hash as NavTab)) {
      return hash as NavTab;
    }
    // 2. Fallback tới localStorage
    const saved = localStorage.getItem(STORAGE_ACTIVE_TAB);
    if (saved === 'dashboard' || saved === 'feeds') {
      localStorage.setItem(STORAGE_ACTIVE_TAB, 'matrix');
      return 'matrix';
    }
    if (VALID_TABS.includes(saved as NavTab)) {
      return saved as NavTab;
    }
  }
  return 'matrix';
};

interface AppLayoutProps {
  children: (props: { 
    activeTab: NavTab; 
    categoryFilter: string;
    setActiveTab: (tab: NavTab) => void;
  }) => React.ReactNode;
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
      const hash = window.location.hash.replace(/^#\/?/, '').trim();
      if (hash === 'dashboard') {
        window.location.hash = 'matrix';
        setActiveTabState('matrix');
        localStorage.setItem(STORAGE_ACTIVE_TAB, 'matrix');
        return;
      }
      if (VALID_TABS.includes(hash as NavTab)) {
        setActiveTabState(hash as NavTab);
        localStorage.setItem(STORAGE_ACTIVE_TAB, hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  return (
    <ToastProvider>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-200">
        {/* Top Navigation Bar */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        {/* Main Content Area - Responsive padding and container */}
        <main className="flex-1 w-full max-w-[1720px] mx-auto px-4 sm:px-6 py-5 transition-all duration-200">
          {children({ activeTab, categoryFilter, setActiveTab })}
        </main>

        {/* Global Toast Container */}
        <ToastContainer />
      </div>
    </ToastProvider>
  );
};
