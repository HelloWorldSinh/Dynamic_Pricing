import React from 'react';

interface AiDataTableProps {
  data: Record<string, any>[];
  onAnalyze?: (sku: string) => void;
}

export const AiDataTable: React.FC<AiDataTableProps> = ({ data, onAnalyze }) => {
  if (!data || data.length === 0) return null;

  const headers = Object.keys(data[0]);
  const hasSkuColumn = headers.some((h) => h.toUpperCase() === 'SKU');

  const renderCellContent = (header: string, val: any) => {
    const headerLower = header.toLowerCase();

    // Định dạng cột DOH: cảnh báo rủi ro tồn kho cao nếu DOH >= 45 ngày
    if (headerLower.includes('doh')) {
      const numericVal = parseInt(String(val).replace(/\D/g, ''), 10);
      const isRisk = !isNaN(numericVal) && numericVal >= 45;

      return (
        <span
          className={`inline-block px-2 py-0.5 rounded text-[11px] font-mono font-semibold border ${
            isRisk
              ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-400 dark:border-rose-900/60'
              : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/60'
          }`}
          title={isRisk ? 'Cảnh báo DOH >= 45 ngày: Rủi ro đọng vốn cao' : 'DOH an toàn'}
        >
          {val}
        </span>
      );
    }

    // Định dạng cột SKU
    if (header.toUpperCase() === 'SKU') {
      return (
        <span className="font-mono font-bold text-orange-600 dark:text-orange-400 text-[11px]">
          {val}
        </span>
      );
    }

    // Định dạng cột giá tiền
    if (headerLower.includes('giá') || headerLower.includes('price')) {
      return (
        <span className="font-mono font-medium text-slate-900 dark:text-slate-100">
          {val}
        </span>
      );
    }

    // Mặc định
    return <span className="font-medium text-slate-700 dark:text-slate-300">{val}</span>;
  };

  return (
    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-900 shadow-xs">
      <div className="p-2.5 px-4 bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center justify-between">
        <span className="uppercase tracking-wider text-[11px]">
          Bảng Dữ Liệu Chi Tiết ({data.length} sản phẩm)
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono font-semibold">
          LIVE DATA
        </span>
      </div>

      <div className="overflow-x-auto max-h-80 overflow-y-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 z-10">
            <tr className="bg-slate-100/90 dark:bg-slate-800/90 text-[11px] font-semibold text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700 backdrop-blur-xs">
              {headers.map((header) => (
                <th key={header} className="p-2.5 px-3.5 whitespace-nowrap">
                  {header}
                </th>
              ))}
              {hasSkuColumn && onAnalyze && (
                <th className="p-2.5 px-3.5 text-right whitespace-nowrap font-semibold">
                  Thao tác
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {data.map((row, rIdx) => {
              const sku = row.SKU || row.sku;
              return (
                <tr
                  key={rIdx}
                  className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                >
                  {headers.map((header) => (
                    <td key={header} className="p-2.5 px-3.5 whitespace-nowrap">
                      {renderCellContent(header, row[header])}
                    </td>
                  ))}
                  {hasSkuColumn && onAnalyze && (
                    <td className="p-2.5 px-3.5 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => sku && onAnalyze(String(sku))}
                        className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-orange-50 dark:bg-slate-800 dark:hover:bg-orange-950/40 text-slate-700 hover:text-orange-600 dark:text-slate-300 dark:hover:text-orange-400 border border-slate-200 dark:border-slate-700 hover:border-orange-300 dark:hover:border-orange-800 text-[11px] font-semibold transition cursor-pointer"
                        title={`Phân tích chuyên sâu 3 lớp cho mã ${sku}`}
                      >
                        Phân tích
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
