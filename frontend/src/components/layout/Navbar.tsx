import React from 'react';
import { Sun, Moon, Database } from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { NavTab } from './Sidebar';

interface NavbarProps {
  activeTab: NavTab;
  categoryFilter: string;
  setCategoryFilter: (category: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  categoryFilter,
  setCategoryFilter,
}) => {
  const { theme, toggleTheme } = useTheme();

  const titles: Record<NavTab, { title: string; subtitle: string }> = {
    matrix: {
      title: 'Price Comparison Matrix',
      subtitle: 'Ma trận đối soát giá 3 bên: FPT Shop vs CellphoneS vs Hoàng Hà Mobile',
    },
    approvals: {
      title: 'Pricing Strategy & Approvals',
      subtitle: 'Gợi ý điều chỉnh giá theo tồn kho DOH & Quy tắc bảo vệ giá sàn',
    },
    mapping: {
      title: 'Manual SKU Mapping Queue',
      subtitle: 'Hàng đợi đối soát thủ công sản phẩm có độ tin cậy 60% – 79%',
    },
    crawler: {
      title: 'Crawl Operations & Raw Inspector',
      subtitle: 'Giám sát tiến trình cào dữ liệu, lịch trình tự động & kiểm tra dữ liệu thô',
    },
  };

  const current = titles[activeTab];

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20 transition-colors">
      {/* Title & Context */}
      <div>
        <h1 className="text-base font-bold text-slate-900 dark:text-white leading-tight">
          {current.title}
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">
          {current.subtitle}
        </p>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-3">
        {/* Quick Category Selector */}
        <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs">
          <button
            onClick={() => setCategoryFilter('ALL')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              categoryFilter === 'ALL'
                ? 'bg-white dark:bg-slate-700 text-orange-600 dark:text-orange-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Tất cả
          </button>
          <button
            onClick={() => setCategoryFilter('PHONE')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              categoryFilter === 'PHONE'
                ? 'bg-white dark:bg-slate-700 text-orange-600 dark:text-orange-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Điện thoại
          </button>
          <button
            onClick={() => setCategoryFilter('LAPTOP')}
            className={`px-3 py-1 rounded-md font-medium transition ${
              categoryFilter === 'LAPTOP'
                ? 'bg-white dark:bg-slate-700 text-orange-600 dark:text-orange-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Laptop
          </button>
        </div>

        {/* Backend Seam Status */}
        <div className="hidden md:flex items-center gap-2 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <Database className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-mono text-[11px]">API :8000</span>
        </div>

        {/* Theme Toggle Button */}
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
      </div>
    </header>
  );
};
