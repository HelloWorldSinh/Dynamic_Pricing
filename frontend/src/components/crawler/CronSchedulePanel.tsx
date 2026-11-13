import React, { useState } from 'react';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';

export const CronSchedulePanel: React.FC = () => {
  const [isEnabled, setIsEnabled] = useState(true);

  return (
    <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs mb-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              Lịch cào định kỳ tự động (Cron Jobs)
            </span>
            <Badge size="sm" variant={isEnabled ? 'success' : 'neutral'}>
              {isEnabled ? 'Đang kích hoạt' : 'Tạm dừng'}
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Tự động kích hoạt cào đối thủ vào các khung giờ vàng biến động giá thị trường.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            size="sm"
            variant={isEnabled ? 'secondary' : 'primary'}
            onClick={() => setIsEnabled(!isEnabled)}
          >
            {isEnabled ? 'Tạm dừng lịch cào' : 'Kích hoạt lại'}
          </Button>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300">
          <span className="text-2xs text-slate-400 block font-medium">Khung giờ 1</span>
          <strong className="text-slate-900 dark:text-white font-semibold text-xs font-mono">08:00 sáng</strong>
          <span className="text-2xs text-slate-400 block mt-0.5">Hàng ngày</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300">
          <span className="text-2xs text-slate-400 block font-medium">Khung giờ 2</span>
          <strong className="text-slate-900 dark:text-white font-semibold text-xs font-mono">18:00 chiều</strong>
          <span className="text-2xs text-slate-400 block mt-0.5">Hàng ngày</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300">
          <span className="text-2xs text-slate-400 block font-medium">Tự động thử lại</span>
          <strong className="text-amber-600 dark:text-amber-400 font-semibold text-xs">Cách 10 phút</strong>
          <span className="text-2xs text-slate-400 block mt-0.5">Nếu phát sinh lỗi</span>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-slate-700 dark:text-slate-300">
          <span className="text-2xs text-slate-400 block font-medium">Lần chạy kế tiếp</span>
          <strong className="text-emerald-600 dark:text-emerald-400 font-semibold text-xs font-mono">18:00 hôm nay</strong>
          <span className="text-2xs text-slate-400 block mt-0.5">Đã lên lịch</span>
        </div>
      </div>
    </div>
  );
};
