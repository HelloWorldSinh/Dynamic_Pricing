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
              Lịch Cào Giá Tự Động (Scheduled Scraping)
              <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 font-semibold">
                PBI-005 Active
              </span>
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Tự động kích hoạt cào 2 lần mỗi ngày vào lúc <strong>08:00</strong> và <strong>18:00</strong>. Tự động thử lại sau 10 phút nếu thất bại.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs font-medium">
            <span className="text-slate-400">Trạng thái:</span>
            <span className={isEnabled ? 'text-emerald-600 dark:text-emerald-400 font-bold' : 'text-slate-500'}>
              {isEnabled ? 'Đang chạy (Enabled)' : 'Tạm dừng (Paused)'}
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
            {isEnabled ? 'Tạm dừng lịch' : 'Bật lịch cào'}
          </button>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Check className="w-4 h-4 text-emerald-500" />
          <span>Khung giờ 1: <strong>08:00 Sáng</strong> (Đầu ngày)</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <Check className="w-4 h-4 text-emerald-500" />
          <span>Khung giờ 2: <strong>18:00 Chiều</strong> (Cuối ngày)</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <ShieldAlert className="w-4 h-4 text-amber-500" />
          <span>Auto Retry: <strong>1 lần sau 10 phút</strong></span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Lần cào kế tiếp: <strong>Hôm nay 18:00</strong></span>
        </div>
      </div>
    </div>
  );
};
