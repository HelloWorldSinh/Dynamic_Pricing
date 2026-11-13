import React from 'react';

interface InteractivePromptChipsProps {
  suggestions?: string[];
  tableData?: Record<string, any>[];
  onSelectPrompt: (prompt: string) => void;
}

export const InteractivePromptChips: React.FC<InteractivePromptChipsProps> = ({
  suggestions,
  tableData,
  onSelectPrompt,
}) => {
  // 1. Thu thập danh sách gợi ý từ backend
  const explicitSuggestions = suggestions || [];

  // 2. Tự động trích xuất gợi ý từ bảng sản phẩm (nếu có SKU)
  const productChips: string[] = [];
  if (tableData && tableData.length > 0) {
    tableData.slice(0, 4).forEach((row) => {
      const sku = row.SKU || row.sku;
      if (sku) {
        const chipText = `Phân tích mã ${sku}`;
        if (!explicitSuggestions.includes(chipText) && !productChips.includes(chipText)) {
          productChips.push(chipText);
        }
      }
    });
  }

  const allPrompts = [...explicitSuggestions, ...productChips];
  if (allPrompts.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60 flex flex-col gap-2">
      <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
        Tương tác &amp; Câu hỏi gợi ý:
      </div>
      <div className="flex flex-wrap gap-2">
        {allPrompts.map((prompt, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectPrompt(prompt)}
            className="text-xs text-left px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 hover:border-orange-500 dark:hover:border-orange-500 hover:text-orange-600 dark:hover:text-orange-400 text-slate-700 dark:text-slate-300 transition shadow-2xs cursor-pointer font-medium"
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
};

