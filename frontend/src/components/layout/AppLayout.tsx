import React, { useState } from 'react';
import { Sidebar, NavTab } from './Sidebar';
import { Navbar } from './Navbar';

interface AppLayoutProps {
  children: (props: { activeTab: NavTab; categoryFilter: string }) => React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<NavTab>('matrix');
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col transition-colors duration-200">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          isCollapsed ? 'ml-20' : 'ml-64'
        }`}
      >
        <Navbar
          activeTab={activeTab}
          categoryFilter={categoryFilter}
          onCategoryChange={setCategoryFilter}
        />

        <main className="flex-1 p-6 max-w-[1600px] w-full mx-auto">
          {children({ activeTab, categoryFilter })}
        </main>
      </div>
    </div>
  );
};
