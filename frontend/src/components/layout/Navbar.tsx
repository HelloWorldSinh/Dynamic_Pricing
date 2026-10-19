import React from 'react';
import { 
  BarChart3, 
  CheckCheck, 
  GitCompare, 
  Database, 
  RefreshCw, 
  Sun, 
  Moon 
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';

export type NavTab = 'matrix' | 'approvals' | 'mapping' | 'feeds' | 'crawler';

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
}) => {
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    {
      id: 'matrix' as NavTab,
      label: 'Price Matrix',
      icon: BarChart3,
    },
    {
      id: 'approvals' as NavTab,
      label: 'Pricing Approvals',
      icon: CheckCheck,
    },
    {
      id: 'mapping' as NavTab,
      label: 'SKU Mapping Queue',
      icon: GitCompare,
    },
    {
      id: 'feeds' as NavTab,
      label: 'Competitor Feeds',
      icon: Database,
    },
    {
      id: 'crawler' as NavTab,
      label: 'Crawl Operations',
      icon: RefreshCw,
    },
  ];

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between sticky top-0 z-30 transition-colors shadow-sm">
      {/* Left: Brand Identity */}
      <div className="flex items-center gap-3 shrink-0">
        <div 
          onClick={() => setActiveTab('matrix')}
          className="cursor-pointer flex items-center gap-2.5 group"
        >
          <div className="w-9 h-9 rounded-lg bg-orange-600 flex items-center justify-center text-white font-black text-sm shadow-md shadow-orange-600/25 group-hover:scale-105 transition-transform">
            FPT
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-white leading-tight">
              Dynamic Pricing
            </span>
            <span className="text-[10px] text-slate-400 leading-tight">
              Retail Analytics
            </span>
          </div>
        </div>
      </div>

      {/* Center: Horizontal Navigation with Badges */}
      <nav className="hidden md:flex items-center gap-1 lg:gap-1.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 ${
                isActive
                  ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/30 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${
                  isActive ? 'text-orange-600 dark:text-orange-400' : 'text-slate-400 dark:text-slate-500'
                }`}
              />
              <span className="whitespace-nowrap">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Right: Theme Toggle & User Profile */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Dark Mode Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
          title={`Chuyển sang ${theme === 'dark' ? 'Light Mode' : 'Dark Mode'}`}
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-indigo-600" />
          )}
        </button>

        {/* Compact User Profile Pill */}
        <div className="flex items-center gap-2 pl-2 pr-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-xs select-none">
          <div className="w-6 h-6 rounded-full bg-orange-600 text-white flex items-center justify-center font-bold text-[10px] shrink-0">
            PA
          </div>
          <div className="flex flex-col">
            <span className="text-[11px] font-semibold text-slate-800 dark:text-slate-200 leading-none">
              Pricing Analyst
            </span>
            <span className="text-[9px] text-slate-400 leading-none mt-0.5">
              FPT Retail
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
