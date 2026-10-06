import React, { useMemo } from 'react';
import { Check, AlertTriangle, HelpCircle } from 'lucide-react';
import { SkuMappingPair } from '../../types/matching';

interface SkuSpecMatrixProps {
  pair: SkuMappingPair;
}

interface SpecRow {
  key: string;
  fptVal: string;
  compVal: string;
  status: 'MATCH' | 'DIFF' | 'PARTIAL';
}

export const SkuSpecMatrix: React.FC<SkuSpecMatrixProps> = ({ pair }) => {
  const specRows = useMemo(() => {
    const rows: SpecRow[] = [];
    const keysSeen = new Set<string>();

    // 1. Special row: Part Number / Model
    if (pair.fpt_part_number || pair.competitor_part_number) {
      keysSeen.add('Mã Part / Model');
      const fptPart = pair.fpt_part_number || '—';
      const compPart = pair.competitor_part_number || '—';
      const isPartDiff = pair.differing_attributes.some(d => 
        d.toLowerCase().includes('part') || d.toLowerCase().includes('mã')
      ) || (fptPart !== '—' && compPart !== '—' && fptPart !== compPart);

      rows.push({
        key: 'Mã Part / Model',
        fptVal: fptPart,
        compVal: compPart,
        status: isPartDiff ? 'DIFF' : (fptPart === compPart && fptPart !== '—' ? 'MATCH' : 'PARTIAL')
      });
    }

    // 2. Collect all keys from fpt_specs & competitor_specs
    const allKeys = [
      ...Object.keys(pair.fpt_specs || {}),
      ...Object.keys(pair.competitor_specs || {})
    ];

    allKeys.forEach((key) => {
      if (keysSeen.has(key)) return;
      keysSeen.add(key);

      const fptVal = pair.fpt_specs?.[key] || '—';
      const compVal = pair.competitor_specs?.[key] || '—';

      // Check if this attribute is explicitly mentioned in differing_attributes
      const isMentionedInDiff = pair.differing_attributes.some(d => 
        d.toLowerCase().includes(key.toLowerCase())
      );

      // Check if explicitly mentioned in matched_attributes
      const isMentionedInMatch = pair.matched_attributes.some(m =>
        m.toLowerCase().includes(key.toLowerCase())
      );

      let status: 'MATCH' | 'DIFF' | 'PARTIAL' = 'PARTIAL';

      if (isMentionedInDiff) {
        status = 'DIFF';
      } else if (isMentionedInMatch || (fptVal !== '—' && compVal !== '—' && fptVal.toLowerCase() === compVal.toLowerCase())) {
        status = 'MATCH';
      } else if (fptVal !== '—' && compVal !== '—' && fptVal !== compVal) {
        status = 'DIFF';
      } else {
        status = 'PARTIAL';
      }

      rows.push({ key, fptVal, compVal, status });
    });

    return rows;
  }, [pair]);

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden shadow-sm">
      <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <span>Bảng Đối Chiếu Thông Số Kỹ Thuật (Spec Matrix)</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-mono font-medium">
            {specRows.length} thông số
          </span>
        </h4>
        <span className="text-[11px] text-slate-500 dark:text-slate-400">
          Căn chỉnh từng dòng đối chiếu
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-100 dark:border-slate-800 text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider bg-slate-50/50 dark:bg-slate-800/30">
              <th className="py-2.5 px-4 w-[28%]">Thuộc tính</th>
              <th className="py-2.5 px-4 w-[33%] text-orange-600 dark:text-orange-400">FPT Shop (Chuẩn)</th>
              <th className="py-2.5 px-4 w-[33%]">{pair.competitor_source} (Crawled)</th>
              <th className="py-2.5 px-3 w-[6%] text-center">Khớp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {specRows.length === 0 ? (
              <tr>
                <td colSpan={4} className="py-6 text-center text-slate-400 text-xs">
                  Không có thông số kỹ thuật chi tiết để so sánh.
                </td>
              </tr>
            ) : (
              specRows.map((row) => {
                const isDiff = row.status === 'DIFF';
                const isMatch = row.status === 'MATCH';

                return (
                  <tr
                    key={row.key}
                    className={`transition-colors ${
                      isDiff
                        ? 'bg-amber-50/60 dark:bg-amber-950/20 border-l-2 border-l-amber-500'
                        : isMatch
                        ? 'hover:bg-slate-50/60 dark:hover:bg-slate-800/40'
                        : 'hover:bg-slate-50/40 dark:hover:bg-slate-800/20'
                    }`}
                  >
                    <td className="py-2.5 px-4 font-medium text-slate-700 dark:text-slate-300">
                      {row.key}
                    </td>

                    <td className="py-2.5 px-4 font-mono text-[11px] text-slate-900 dark:text-slate-100">
                      {row.fptVal}
                    </td>

                    <td className="py-2.5 px-4 font-mono text-[11px] text-slate-900 dark:text-slate-100">
                      {row.compVal}
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      {isMatch && (
                        <span
                          title="Trùng khớp hoàn toàn"
                          className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400"
                        >
                          <Check className="w-3 h-3 stroke-[3]" />
                        </span>
                      )}
                      {isDiff && (
                        <span
                          title="Phát hiện sai khác"
                          className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-100 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 animate-pulse"
                        >
                          <AlertTriangle className="w-3 h-3 stroke-[2.5]" />
                        </span>
                      )}
                      {row.status === 'PARTIAL' && (
                        <span
                          title="Chưa đầy đủ dữ liệu một bên"
                          className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400"
                        >
                          <HelpCircle className="w-3 h-3" />
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
