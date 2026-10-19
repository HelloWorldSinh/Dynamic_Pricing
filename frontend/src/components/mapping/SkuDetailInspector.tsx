import React, { useMemo } from 'react';
import { ExternalLink, CheckCircle2 } from 'lucide-react';
import { SkuMappingPair } from '../../types/matching';
import { ConfidenceMeter } from './ConfidenceMeter';
import { formatCurrencyVND } from '../../utils/formatters';
import { extractSpecsFromTitle, isSpecMatch, ParsedSpecs } from '../../utils/productSpecParser';

interface SkuDetailInspectorProps {
  pair: SkuMappingPair | null;
  currentIndex: number;
  totalInQueue: number;
  onApprove: (id: string) => void;
  onReject: (id: string) => void;
}

interface SpecRowData {
  key: string;
  fptVal: string;
  compVal: string;
  status: 'MATCH' | 'DIFF' | 'MISSING';
  isTokenDiff?: boolean;
  fptExtracted?: boolean;
  compExtracted?: boolean;
}

// Token diff helper to highlight differing words/tokens between FPT and Competitor
function renderTokenDiff(textA: string, textB: string, isTarget: boolean) {
  if (!textA || textA === '—' || !textB || textB === '—') {
    return textA;
  }

  // Tokenize preserving whitespace and delimiters
  const tokensA = textA.split(/(\s+|[,\-\/\(\)])/);
  const wordsBSet = new Set(
    textB
      .toLowerCase()
      .split(/[\s,\-\/\(\)]+/)
      .filter(Boolean)
  );

  return (
    <span>
      {tokensA.map((part, idx) => {
        const clean = part.trim().toLowerCase();
        if (!clean || /^[\s,\-\/\(\)]+$/.test(part)) {
          return <span key={idx}>{part}</span>;
        }
        const matches = wordsBSet.has(clean);
        if (matches) {
          return <span key={idx}>{part}</span>;
        }
        return (
          <span
            key={idx}
            className={`px-1 py-0.2 rounded font-mono font-bold transition-colors inline-block ${
              isTarget
                ? 'bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800'
                : 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-800'
            }`}
            title={`Sai khác: "${part}"`}
          >
            {part}
          </span>
        );
      })}
    </span>
  );
}

export const SkuDetailInspector: React.FC<SkuDetailInspectorProps> = ({
  pair,
  currentIndex,
  totalInQueue,
  onApprove,
  onReject,
}) => {
  if (!pair) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
        <CheckCircle2 className="w-10 h-10 text-emerald-500 mb-2" />
        <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
          Hàng đợi đối soát trống!
        </h3>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Toàn bộ SKU trong danh sách đều đã được xử lý xong hoặc tự động đối soát chính xác 100%.
        </p>
      </div>
    );
  }

  // Construct Complete Spec Rows for Unified Diff Table
  const tableRows = useMemo(() => {
    const rows: SpecRowData[] = [];
    const keysHandled = new Set<string>();

    const fptParsed = extractSpecsFromTitle(pair.fpt_name);
    const compParsed = extractSpecsFromTitle(pair.competitor_name);

    const getStatus = (fpt: string, comp: string, keyName: string): 'MATCH' | 'DIFF' | 'MISSING' => {
      if (!fpt || fpt === '—' || !comp || comp === '—') return 'MISSING';
      const isMentionedInDiff = pair.differing_attributes?.some((d) =>
        d.toLowerCase().includes(keyName.toLowerCase())
      );
      if (isMentionedInDiff) return 'DIFF';
      return isSpecMatch(fpt, comp) ? 'MATCH' : 'DIFF';
    };

    // 1. Tên sản phẩm
    keysHandled.add('Tên sản phẩm');
    rows.push({
      key: 'Tên sản phẩm',
      fptVal: pair.fpt_name,
      compVal: pair.competitor_name,
      status: pair.fpt_name.trim().toLowerCase() === pair.competitor_name.trim().toLowerCase() ? 'MATCH' : 'DIFF',
      isTokenDiff: true,
    });

    // 2. Mã Part / Model
    keysHandled.add('Mã Part / Model');
    const fptPart = pair.fpt_part_number || fptParsed.partNumber || '—';
    const compPart = pair.competitor_part_number || compParsed.partNumber || '—';
    rows.push({
      key: 'Mã Part / Model',
      fptVal: fptPart,
      compVal: compPart,
      status: getStatus(fptPart, compPart, 'part'),
      isTokenDiff: true,
      fptExtracted: !pair.fpt_part_number && !!fptParsed.partNumber,
      compExtracted: !pair.competitor_part_number && !!compParsed.partNumber,
    });

    // 3. Giá bán niêm yết
    keysHandled.add('Giá bán niêm yết');
    rows.push({
      key: 'Giá bán niêm yết',
      fptVal: formatCurrencyVND(pair.fpt_price),
      compVal: formatCurrencyVND(pair.competitor_price),
      status: pair.fpt_price === pair.competitor_price ? 'MATCH' : 'DIFF',
      isTokenDiff: false,
    });

    // 4. Standard technical attributes
    const standardAttrs: Array<{
      key: string;
      fptKeys: string[];
      compKeys: string[];
      fallbackKey?: keyof ParsedSpecs;
    }> = [
      { key: 'CPU / Vi xử lý', fptKeys: ['CPU', 'Vi xử lý', 'Chipset', 'Chip'], compKeys: ['CPU', 'Vi xử lý', 'Chipset', 'Chip'], fallbackKey: 'cpu' },
      { key: 'RAM', fptKeys: ['RAM', 'Bộ nhớ/RAM', 'Dung lượng RAM'], compKeys: ['RAM', 'Bộ nhớ/RAM', 'Dung lượng RAM'], fallbackKey: 'ram' },
      { key: 'Ổ cứng', fptKeys: ['Ổ cứng', 'Storage', 'Bộ nhớ trong', 'Ổ cứng/SSD', 'ROM'], compKeys: ['Ổ cứng', 'Storage', 'Bộ nhớ trong', 'Ổ cứng/SSD', 'ROM'], fallbackKey: 'storage' },
      { key: 'Card đồ họa', fptKeys: ['Card đồ họa', 'GPU', 'VGA'], compKeys: ['Card đồ họa', 'GPU', 'VGA'], fallbackKey: 'gpu' },
      { key: 'Màn hình', fptKeys: ['Màn hình', 'Độ phân giải', 'Kích thước màn hình'], compKeys: ['Màn hình', 'Độ phân giải', 'Kích thước màn hình'], fallbackKey: 'screen' },
      { key: 'Màu sắc', fptKeys: ['Màu sắc', 'Color', 'Màu'], compKeys: ['Màu sắc', 'Color', 'Màu'], fallbackKey: 'color' },
      { key: 'Hệ điều hành', fptKeys: ['HĐH', 'Hệ điều hành', 'OS'], compKeys: ['HĐH', 'Hệ điều hành', 'OS'], fallbackKey: 'os' },
      { key: 'Hãng sản xuất', fptKeys: ['Hãng', 'Thương hiệu', 'Nhà sản xuất'], compKeys: ['Hãng', 'Thương hiệu', 'Nhà sản xuất'], fallbackKey: 'brand' },
      { key: 'Pin', fptKeys: ['Pin', 'Dung lượng pin'], compKeys: ['Pin', 'Dung lượng pin'] },
    ];

    standardAttrs.forEach((spec) => {
      keysHandled.add(spec.key);
      let fVal = '—';
      let cVal = '—';
      let fExtracted = false;
      let cExtracted = false;

      for (const k of spec.fptKeys) {
        if (pair.fpt_specs && pair.fpt_specs[k] && pair.fpt_specs[k].trim() && pair.fpt_specs[k] !== '—') {
          fVal = pair.fpt_specs[k]!;
          break;
        }
      }
      if (fVal === '—' && spec.fallbackKey && fptParsed[spec.fallbackKey]) {
        fVal = fptParsed[spec.fallbackKey]!;
        fExtracted = true;
      }

      for (const k of spec.compKeys) {
        if (pair.competitor_specs && pair.competitor_specs[k] && pair.competitor_specs[k].trim() && pair.competitor_specs[k] !== '—') {
          cVal = pair.competitor_specs[k]!;
          break;
        }
      }
      if (cVal === '—' && spec.fallbackKey && compParsed[spec.fallbackKey]) {
        cVal = compParsed[spec.fallbackKey]!;
        cExtracted = true;
      }

      rows.push({
        key: spec.key,
        fptVal: fVal,
        compVal: cVal,
        status: getStatus(fVal, cVal, spec.key),
        fptExtracted: fExtracted,
        compExtracted: cExtracted,
      });
    });

    // 5. Add any remaining keys from specs or differing_attributes
    const allCustomKeys = [
      ...Object.keys(pair.fpt_specs || {}),
      ...Object.keys(pair.competitor_specs || {}),
    ];

    allCustomKeys.forEach((k) => {
      if (
        k === 'summary' ||
        keysHandled.has(k) ||
        ['CPU', 'RAM', 'Bộ nhớ/RAM', 'Ổ cứng', 'Màn hình', 'HĐH', 'Pin', 'Hãng', 'GPU', 'Card đồ họa', 'Màu sắc'].includes(k)
      ) {
        return;
      }
      keysHandled.add(k);
      const fVal = pair.fpt_specs?.[k] || '—';
      const cVal = pair.competitor_specs?.[k] || '—';
      rows.push({
        key: k,
        fptVal: fVal,
        compVal: cVal,
        status: getStatus(fVal, cVal, k),
      });
    });

    return rows;
  }, [pair]);

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900 rounded-xl overflow-hidden">
      {/* Workbench Action Header Bar */}
      <div className="px-5 py-3 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-950/40 px-2 py-0.5 rounded border border-orange-200 dark:border-orange-800">
            SKU: {pair.fpt_sku}
          </span>
          <span className="text-xs text-slate-400 font-medium">
            #{currentIndex + 1} / {totalInQueue} trong hàng đợi
          </span>
          <ConfidenceMeter score={pair.confidence_score} />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onReject(pair.id)}
            className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 hover:border-rose-200 dark:border-rose-800 text-xs font-semibold transition shadow-xs cursor-pointer"
            title="Từ chối ghép cặp"
          >
            Từ chối
          </button>

          <button
            type="button"
            onClick={() => onApprove(pair.id)}
            className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shadow-xs cursor-pointer"
            title="Xác nhận khớp 100%"
          >
            Khớp 100%
          </button>
        </div>
      </div>

      {/* Unified Side-by-Side Diff Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 z-10 bg-slate-100/90 dark:bg-slate-800/90 backdrop-blur-xs border-b border-slate-200 dark:border-slate-700 text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            <tr>
              <th className="py-2.5 px-4 w-[20%]">Thuộc tính</th>
              <th className="py-2.5 px-4 w-[38%] text-orange-600 dark:text-orange-400">
                FPT Shop
              </th>
              <th className="py-2.5 px-4 w-[32%]">
                <div className="flex items-center justify-between">
                  <span>{pair.competitor_source}</span>
                  {pair.competitor_url && (
                    <a
                      href={pair.competitor_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[10px] text-blue-600 dark:text-blue-400 hover:underline normal-case font-medium"
                      title="Mở website đối thủ để kiểm tra thực tế"
                    >
                      <span>Web gốc</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </th>
              <th className="py-2.5 px-3 w-[10%] text-center">Trạng thái</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/70">
            {tableRows.map((row) => {
              const isDiff = row.status === 'DIFF';
              const isMatch = row.status === 'MATCH';
              const isMissing = row.status === 'MISSING';

              return (
                <tr
                  key={row.key}
                  className={`transition-colors ${
                    isDiff
                      ? 'bg-amber-50/60 dark:bg-amber-950/20 border-l-2 border-l-amber-500'
                      : isMatch
                      ? 'hover:bg-slate-50/50 dark:hover:bg-slate-800/30'
                      : 'hover:bg-slate-50/30 dark:hover:bg-slate-800/20'
                  }`}
                >
                  {/* Column 1: Attribute Name */}
                  <td className="py-2.5 px-4 font-semibold text-slate-700 dark:text-slate-300 align-top">
                    {row.key}
                  </td>

                  {/* Column 2: FPT Value */}
                  <td className="py-2.5 px-4 font-mono text-[11px] text-slate-900 dark:text-slate-100 align-top leading-relaxed">
                    {row.fptVal === '—' ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-400 font-sans font-medium">
                        Chưa cập nhật
                      </span>
                    ) : (
                      <span>
                        {row.isTokenDiff ? renderTokenDiff(row.fptVal, row.compVal, false) : row.fptVal}
                      </span>
                    )}
                  </td>

                  {/* Column 3: Competitor Value */}
                  <td className="py-2.5 px-4 font-mono text-[11px] text-slate-900 dark:text-slate-100 align-top leading-relaxed">
                    {row.compVal === '—' ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900/60 font-sans font-medium">
                        Chưa cập nhật
                      </span>
                    ) : (
                      <span>
                        {row.isTokenDiff ? renderTokenDiff(row.compVal, row.fptVal, true) : row.compVal}
                      </span>
                    )}
                  </td>

                  {/* Column 4: Match Status */}
                  <td className="py-2.5 px-3 text-center align-top">
                    {isMatch && (
                      <span className="inline-block text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-2.5 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">
                        Khớp
                      </span>
                    )}
                    {isDiff && (
                      <span className="inline-block text-[10px] font-bold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 px-2.5 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                        Sai khác
                      </span>
                    )}
                    {isMissing && (
                      <span className="inline-block text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                        Chưa có
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
