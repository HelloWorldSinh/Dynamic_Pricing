import React, { useState } from 'react';
import { Navbar, NavTab } from './Navbar';

interface AppLayoutProps {
  children: (props: { activeTab: NavTab; categoryFilter: string }) => React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<NavTab>('matrix');
  const [categoryFilter] = useState<string>('ALL');

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
