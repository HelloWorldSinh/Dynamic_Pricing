import React, { useState } from 'react';
import { CalendarClock, ShieldAlert, Check } from 'lucide-react';

export const CronSchedulePanel: React.FC = () => {
  const [isEnabled, setIsEnabled] = useState(true);

  return (
    <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="p-2 rounded-lg bg-orange-500/10 text-orange-600 dark:text-orange-400">
            <CalendarClock className="w-5 h-5" />
          </span>
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <span>Scheduled Scraping</span>
              <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 font-semibold font-mono">
                Active
              </span>
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-medium">
            <span className="text-slate-400">Status:</span>
            <span className={isEnabled ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-500'}>
              {isEnabled ? 'Running' : 'Paused'}
            </span>
          </div>

          <button
            onClick={() => setIsEnabled(!isEnabled)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              isEnabled
                ? 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                : 'bg-orange-600 hover:bg-orange-500 text-white'
            }`}
          >
            {isEnabled ? 'Pause Schedule' : 'Enable Schedule'}
          </button>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Check className="w-4 h-4 text-emerald-500" />
          <span>Slot 1: <strong>08:00 AM</strong></span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Check className="w-4 h-4 text-emerald-500" />
          <span>Slot 2: <strong>06:00 PM</strong></span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <ShieldAlert className="w-4 h-4 text-amber-500" />
          <span>Auto Retry: <strong>10 minutes</strong></span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Next Run: <strong>Today 06:00 PM</strong></span>
        </div>
      </div>
    </div>
  );
};
