import React from 'react';
import { Sun, Moon, User } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { cn } from '../../utils/cn';

export type NavTab = 'matrix' | 'approvals' | 'mapping' | 'crawler';

interface NavbarProps {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
}

interface NavItem {
  id: NavTab;
  label: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
}) => {
  const { theme, toggleTheme } = useTheme();

  const navItems: NavItem[] = [
    { id: 'matrix', label: 'Bảng giá thị trường' },
    { id: 'approvals', label: 'Duyệt giá đề xuất' },
    { id: 'mapping', label: 'Hàng đợi đối soát SKU' },
    { id: 'crawler', label: 'Vận hành cào' },
  ];

  return (
    <header className="h-14 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 md:px-6 flex items-center justify-between sticky top-0 z-30 transition-colors shadow-2xs">
      {/* Left: Brand Identity */}
      <div className="flex items-center gap-3 shrink-0 mr-4">
        <button 
          type="button"
          onClick={() => setActiveTab('matrix')}
          className="flex items-center gap-2.5 text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 rounded-md"
        >
          <div className="w-8 h-8 rounded-lg bg-orange-600 flex items-center justify-center text-white font-black text-xs tracking-wider shadow-xs group-hover:bg-orange-700 transition-colors">
            FPT
          </div>
          <div className="hidden sm:flex flex-col">
            <span className="font-bold text-xs tracking-tight text-slate-900 dark:text-white leading-tight">
              DYNAMIC PRICING
            </span>
            <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 tracking-wider leading-tight">
              ENTERPRISE PLATFORM
            </span>
          </div>
        </button>
      </div>

      {/* Center: Horizontal Navigation with Scrollable Support for Mobile */}
      <nav 
        className="flex items-center gap-1 overflow-x-auto no-scrollbar py-1 flex-1 max-w-3xl"
        aria-label="Điều hướng chính"
      >
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveTab(item.id)}
              className={cn(
                'px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap transition-all duration-150 relative border',
                isActive
                  ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800/60 border-transparent'
              )}
              aria-current={isActive ? 'page' : undefined}
            >
              {item.label}
              {isActive && (
                <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-orange-600 dark:bg-orange-500 rounded-full" />
              )}
            </button>
          );
        })}
      </nav>

      {/* Right: Theme Toggle & User Profile */}
      <div className="flex items-center gap-2.5 shrink-0 ml-4">
        {/* Dark Mode Toggle */}
        <button
          type="button"
          onClick={toggleTheme}
          className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-slate-600 transition"
          aria-label={`Chuyển giao diện sang ${theme === 'dark' ? 'sáng' : 'tối'}`}
          title={theme === 'dark' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400" />
          ) : (
            <Moon className="w-4 h-4 text-slate-600 dark:text-slate-300" />
          )}
        </button>

        {/* Compact User Profile Pill */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/60 text-2xs select-none">
          <div className="w-6 h-6 rounded-full bg-orange-100 dark:bg-orange-950/80 flex items-center justify-center text-orange-600 dark:text-orange-400 shrink-0">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-slate-800 dark:text-slate-200 leading-none">
              Pricing Analyst
            </span>
            <span className="text-[10px] text-slate-400 leading-none mt-0.5">
              FPT Retail
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
