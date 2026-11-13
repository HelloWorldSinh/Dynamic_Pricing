import React, { useState } from 'react';
import { ExternalLink, X } from 'lucide-react';
import { CrawlResult } from '../../types/crawl';
import { formatCurrencyVND, formatDate } from '../../utils/formatters';
import { Badge } from '../common/Badge';

interface RawDataInspectorProps {
  items: CrawlResult[];
}

export const RawDataInspector: React.FC<RawDataInspectorProps> = ({ items }) => {
  const [search, setSearch] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('ALL');
  const [expandedRowId, setExpandedRowId] = useState<string | number | null>(null);

  const filtered = items.filter((item) => {
    if (selectedSource !== 'ALL' && item.source !== selectedSource) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        item.product_name.toLowerCase().includes(q) ||
        item.url.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const toggleExpand = (id: string | number) => {
    setExpandedRowId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs overflow-hidden">
      {/* Top Filter Header */}
      <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-xs font-bold text-slate-900 dark:text-white tracking-tight">
            Dữ liệu cào thô (Raw Data Inspector)
          </h3>
        </div>

        <div className="flex items-center gap-2.5">
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo tên hoặc URL..."
              className="text-xs px-3 py-1.5 rounded-md border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none font-medium cursor-pointer"
          >
            <option value="ALL">Mọi nguồn cào</option>
            <option value="CELLPHONES">CellphoneS</option>
            <option value="HOANGHA">Hoàng Hà Mobile</option>
            <option value="FPT">FPT Shop</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 font-semibold text-xs sticky top-0 z-10">
              <th className="py-2.5 px-3 w-10 text-center">Chi tiết</th>
              <th className="py-2.5 px-3">Nguồn</th>
              <th className="py-2.5 px-4">Tên sản phẩm cào được</th>
              <th className="py-2.5 px-3 text-right">Giá hiển thị</th>
              <th className="py-2.5 px-3 text-center">Trạng thái kho</th>
              <th className="py-2.5 px-3 text-center">Thời điểm cào</th>
              <th className="py-2.5 px-3 text-center">Trang gốc</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
            {filtered.map((item) => {
              const isExpanded = expandedRowId === item.id;
              return (
                <React.Fragment key={item.id}>
                  <tr className="even:bg-white dark:even:bg-slate-900 odd:bg-slate-50/50 dark:odd:bg-slate-800/30 hover:bg-orange-50/40 dark:hover:bg-slate-800/60 transition">
                    <td className="py-2.5 px-3 text-center">
                      <button
                        type="button"
                        onClick={() => toggleExpand(item.id)}
                        className="text-xs font-mono font-bold text-slate-500 hover:text-orange-600 dark:hover:text-orange-400 w-5 h-5 inline-flex items-center justify-center rounded hover:bg-slate-100 dark:hover:bg-slate-800"
                        title={isExpanded ? 'Thu gọn' : 'Mở rộng chi tiết'}
                      >
                        {isExpanded ? '−' : '+'}
                      </button>
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge
                        size="sm"
                        variant={item.source === 'CELLPHONES' ? 'danger' : item.source === 'HOANGHA' ? 'warning' : 'info'}
                      >
                        {item.source}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-4 max-w-sm">
                      <span className="font-semibold text-slate-900 dark:text-slate-100 block truncate" title={item.product_name}>
                        {item.product_name}
                      </span>
                      <span className="text-2xs font-mono text-slate-400 truncate block">
                        {item.url}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900 dark:text-white">
                      {formatCurrencyVND(item.price)}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <Badge
                        size="sm"
                        variant={item.is_in_stock ? 'success' : 'neutral'}
                      >
                        {item.is_in_stock ? 'CÒN HÀNG' : 'HẾT HÀNG'}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono text-2xs text-slate-500">
                      {formatDate(item.crawled_at)}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 p-0.5 rounded transition"
                        title="Mở liên kết gốc"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </td>
                  </tr>

                  {/* Expanded JSON Inspector */}
                  {isExpanded && (
                    <tr>
                      <td colSpan={7} className="p-4 bg-slate-950 text-slate-200">
                        <div className="text-2xs font-mono font-bold uppercase text-slate-400 mb-2">
                          THÔNG SỐ BÓC TÁCH (PARSED SPECIFICATIONS) &amp; RAW JSON
                        </div>
                        <pre className="text-2xs font-mono text-slate-300 overflow-x-auto max-h-72 p-3 rounded bg-slate-900 border border-slate-800">
                          {JSON.stringify(item, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
