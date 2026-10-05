import React, { useState, useMemo } from 'react';
import { 
  History, 
  Search, 
  ArrowRight, 
  TrendingDown, 
  TrendingUp, 
  Bot, 
  UserCheck, 
  CheckCircle2 
} from 'lucide-react';
import { PriceChangeHistoryItem } from '../../types/pricing';
import { formatCurrencyVND, formatPercent } from '../../utils/formatters';

interface PriceHistoryTableProps {
  items: PriceChangeHistoryItem[];
}

export const PriceHistoryTable: React.FC<PriceHistoryTableProps> = ({ items }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'ALL' | 'AI_RECOMMENDED' | 'MANUAL_CONFIG'>('ALL');

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Filter by type
      if (filterType !== 'ALL' && item.change_type !== filterType) {
        return false;
      }
      // Filter by search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchName = item.product_name.toLowerCase().includes(q);
        const matchSku = item.sku.toLowerCase().includes(q);
        const matchScenario = item.scenario.toLowerCase().includes(q);
        if (!matchName && !matchSku && !matchScenario) return false;
      }
      return true;
    });
  }, [items, searchQuery, filterType]);

  const formatDateTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      const pad = (n: number) => n.toString().padStart(2, '0');
      return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-4">
      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo mã SKU, tên sản phẩm hoặc kịch bản..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500"
          />
        </div>

        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setFilterType('ALL')}
            className={`px-3 py-1.5 rounded-lg font-medium transition ${
              filterType === 'ALL'
                ? 'bg-orange-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            Tất cả ({items.length})
          </button>
          <button
            onClick={() => setFilterType('AI_RECOMMENDED')}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
              filterType === 'AI_RECOMMENDED'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Đề xuất AI</span>
          </button>
          <button
            onClick={() => setFilterType('MANUAL_CONFIG')}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
              filterType === 'MANUAL_CONFIG'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Tự chỉnh tay</span>
          </button>
        </div>
      </div>

      {/* Main Table */}
      {filteredItems.length === 0 ? (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-12 text-center shadow-sm">
          <History className="w-8 h-8 text-slate-400 mx-auto mb-2 opacity-50" />
          <p className="text-xs text-slate-500">Chưa có bản ghi lịch sử thay đổi giá nào phù hợp.</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                  <th className="py-3 px-4">Thời gian áp dụng</th>
                  <th className="py-3 px-4">Sản phẩm &amp; SKU</th>
                  <th className="py-3 px-4 text-center">Biến động giá</th>
                  <th className="py-3 px-3 text-right">Chênh lệch</th>
                  <th className="py-3 px-3 text-center">Biên lợi nhuận</th>
                  <th className="py-3 px-3 text-center">Phương thức</th>
                  <th className="py-3 px-4">Căn cứ &amp; Ghi chú</th>
                  <th className="py-3 px-3 text-center">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {filteredItems.map((item) => {
                  const isDecrease = item.price_change < 0;

                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {/* Timestamp */}
                      <td className="py-3 px-4 whitespace-nowrap text-slate-500 dark:text-slate-400 font-mono">
                        {formatDateTime(item.changed_at)}
                      </td>

                      {/* Product & SKU */}
                      <td className="py-3 px-4 max-w-[240px]">
                        <div className="font-semibold text-slate-900 dark:text-slate-100 truncate" title={item.product_name}>
                          {item.product_name}
                        </div>
                        <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                          {item.sku}
                        </div>
                      </td>

                      {/* Old Price -> New Price */}
                      <td className="py-3 px-4 text-center whitespace-nowrap">
                        <div className="inline-flex items-center gap-2">
                          <span className="font-mono text-slate-400 line-through">
                            {formatCurrencyVND(item.old_price)}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                          <span className="font-mono font-bold text-slate-900 dark:text-white">
                            {formatCurrencyVND(item.new_price)}
                          </span>
                        </div>
                      </td>

                      {/* Price Change Amount & % */}
                      <td className="py-3 px-3 text-right whitespace-nowrap font-mono font-bold">
                        <span
                          className={`inline-flex items-center gap-1 ${
                            isDecrease
                              ? 'text-rose-600 dark:text-rose-400'
                              : 'text-emerald-600 dark:text-emerald-400'
                          }`}
                        >
                          {isDecrease ? (
                            <TrendingDown className="w-3.5 h-3.5" />
                          ) : (
                            <TrendingUp className="w-3.5 h-3.5" />
                          )}
                          <span>
                            {item.price_change > 0 ? '+' : ''}
                            {formatCurrencyVND(item.price_change)}
                          </span>
                        </span>
                        <div className="text-[10px] text-slate-400 font-normal">
                          {formatPercent(item.price_change_percent)}
                        </div>
                      </td>

                      {/* Margin % */}
                      <td className="py-3 px-3 text-center whitespace-nowrap font-mono font-bold">
                        <span className="px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900">
                          {formatPercent(item.margin_percent)}
                        </span>
                      </td>

                      {/* Change Type */}
                      <td className="py-3 px-3 text-center whitespace-nowrap">
                        {item.change_type === 'AI_RECOMMENDED' ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300">
                            <Bot className="w-3 h-3" />
                            <span>Đề xuất AI</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
                            <UserCheck className="w-3 h-3" />
                            <span>Tự chỉnh tay</span>
                          </span>
                        )}
                      </td>

                      {/* Scenario & By */}
                      <td className="py-3 px-4 max-w-[260px]">
                        <div className="text-[11px] text-slate-700 dark:text-slate-300 line-clamp-1" title={item.scenario}>
                          {item.scenario}
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          Bởi: <span className="font-medium text-slate-600 dark:text-slate-400">{item.changed_by}</span>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-3 text-center whitespace-nowrap">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Đã đồng bộ</span>
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
