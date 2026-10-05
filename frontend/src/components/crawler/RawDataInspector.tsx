import React, { useState } from 'react';
import { Search, ExternalLink, Code2, ChevronDown, ChevronRight } from 'lucide-react';
import { CrawlResult } from '../../types/crawl';
import { formatCurrencyVND, formatDate } from '../../utils/formatters';

interface RawDataInspectorProps {
  items: CrawlResult[];
}

export const RawDataInspector: React.FC<RawDataInspectorProps> = ({ items }) => {
  const [search, setSearch] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('ALL');
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);

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

  const toggleExpand = (id: number) => {
    setExpandedRowId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
      {/* Top Filter Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
            Thanh Tra Dữ Liệu Cào Thô (Raw Data Inspector)
            <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
              PBI-015
            </span>
          </h3>
          <p className="text-[11px] text-slate-500">
            Xem dữ liệu thực tế thu thập được trước khi chuyển sang hệ thống đối soát SKU
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm theo tên hoặc URL..."
              className="text-xs pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500"
            />
          </div>

          <select
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-orange-500"
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
            <tr className="bg-slate-50/80 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
              <th className="py-2.5 px-3 w-8"></th>
              <th className="py-2.5 px-3">Nguồn</th>
              <th className="py-2.5 px-4">Tên sản phẩm cào được</th>
              <th className="py-2.5 px-3 text-right">Giá hiển thị</th>
              <th className="py-2.5 px-3 text-center">Trạng thái kho</th>
              <th className="py-2.5 px-3 text-center">Thời điểm cào</th>
              <th className="py-2.5 px-3 text-center">Trang gốc</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {filtered.map((item) => {
              const isExpanded = expandedRowId === item.id;
              return (
                <React.Fragment key={item.id}>
                  <tr className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => toggleExpand(item.id)}
                        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      >
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-700 dark:text-slate-300">
                      <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-mono">
                        {item.source}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 max-w-[320px]">
                      <div className="font-medium text-slate-900 dark:text-slate-100 truncate" title={item.product_name}>
                        {item.product_name}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-800 dark:text-slate-200">
                      {formatCurrencyVND(item.price)}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          item.is_in_stock
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-400'
                        }`}
                      >
                        {item.is_in_stock ? 'Còn hàng' : 'Hết hàng'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono text-[10px] text-slate-500">
                      {formatDate(item.crawled_at)}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1 inline-flex items-center text-slate-400 hover:text-orange-600 dark:hover:text-orange-400 transition"
                        title="Mở tab mới kiểm tra web đối thủ"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </td>
                  </tr>

                  {/* Expanded JSON Inspector */}
                  {isExpanded && (
                    <tr className="bg-slate-50 dark:bg-slate-950/60">
                      <td colSpan={7} className="p-4 pl-10 border-b border-slate-200 dark:border-slate-800">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-400 mb-2">
                          <Code2 className="w-3.5 h-3.5 text-orange-500" />
                          <span>Chi tiết thông số JSON trích xuất được:</span>
                        </div>
                        <pre className="text-[11px] font-mono p-3 rounded-lg bg-slate-900 text-slate-200 overflow-x-auto max-h-48">
                          {JSON.stringify(item.specifications || {}, null, 2)}
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
