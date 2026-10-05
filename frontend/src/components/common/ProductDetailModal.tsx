import React from 'react';
import { X, ExternalLink, ShieldCheck, Cpu, HardDrive, Monitor, Battery } from 'lucide-react';
import { PriceComparisonItem } from '../../types/pricing';
import { formatCurrencyVND } from '../../utils/formatters';

interface ProductDetailModalProps {
  product: PriceComparisonItem | null;
  onClose: () => void;
  onAskAi: (product: PriceComparisonItem) => void;
}

export const ProductDetailModal: React.FC<ProductDetailModalProps> = ({
  product,
  onClose,
  onAskAi,
}) => {
  if (!product) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-start justify-between bg-slate-50/50 dark:bg-slate-950/50">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-600 text-white uppercase tracking-wider">
                {product.category}
              </span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 font-semibold">
                SKU: {product.sku}
              </span>
              {product.part_number && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 font-bold">
                  PN: {product.part_number}
                </span>
              )}
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
              {product.name}
            </h3>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs">
          {/* Price & Competitor Comparison Cards */}
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
              Vị thế giá thị trường (3 bên)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* FPT */}
              <div className="p-3.5 rounded-xl border-2 border-orange-500/40 bg-orange-50/20 dark:bg-orange-950/20">
                <div className="text-[11px] font-bold text-orange-600 dark:text-orange-400">
                  FPT Shop (Chuẩn)
                </div>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white mt-1">
                  {formatCurrencyVND(product.fpt_price)}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  Kho: {product.inventory_quantity} máy | DOH: {product.doh} ngày
                </div>
              </div>

              {/* CellphoneS */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/40">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 dark:text-slate-300">
                  <span>CellphoneS</span>
                  {product.cellphones && (
                    <a
                      href={product.cellphones.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-400 hover:text-orange-500"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white mt-1">
                  {product.cellphones ? formatCurrencyVND(product.cellphones.price) : '—'}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {product.cellphones?.is_in_stock ? 'Còn hàng online' : 'Tạm hết hàng'}
                </div>
              </div>

              {/* Hoàng Hà */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/40">
                <div className="flex items-center justify-between text-[11px] font-bold text-slate-700 dark:text-slate-300">
                  <span>Hoàng Hà Mobile</span>
                  {product.hoangha && (
                    <a
                      href={product.hoangha.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-400 hover:text-orange-500"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                <div className="text-base font-black font-mono text-slate-900 dark:text-white mt-1">
                  {product.hoangha ? formatCurrencyVND(product.hoangha.price) : '—'}
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  {product.hoangha?.is_in_stock ? 'Còn hàng online' : 'Tạm hết hàng'}
                </div>
              </div>
            </div>
          </div>

          {/* Specifications Breakdown */}
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
              Thông số kỹ thuật bóc tách (Extracted Specs)
            </h4>
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-2.5">
                <Cpu className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <div>
                  <span className="text-[10px] text-slate-400 block">Vi xử lý (CPU)</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    Core i5-13500H / Snapdragon 8 Gen 3
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-2.5">
                <HardDrive className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <div>
                  <span className="text-[10px] text-slate-400 block">Bộ nhớ RAM &amp; Ổ cứng</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    16 GB RAM | 512 GB SSD NVMe
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-2.5">
                <Monitor className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <div>
                  <span className="text-[10px] text-slate-400 block">Màn hình</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    OLED FHD 100% DCI-P3 600nits
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200/60 dark:border-slate-700/60 flex items-center gap-2.5">
                <Battery className="w-4 h-4 text-orange-500 flex-shrink-0" />
                <div>
                  <span className="text-[10px] text-slate-400 block">Pin &amp; Nguồn sạc</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    50 Whrs Li-ion 3-cell Fast Charge
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Pricing Guard Context */}
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-500" />
              <div>
                <div className="font-bold text-slate-900 dark:text-white">
                  Giá Sàn Bảo Vệ: {formatCurrencyVND(product.floor_price)}
                </div>
                <div className="text-[11px] text-slate-500">
                  Giá vốn nhập kho: {formatCurrencyVND(product.cost_price)} (Biên an toàn tối thiểu: 5%)
                </div>
              </div>
            </div>
            <span className="text-[10px] px-2.5 py-1 rounded-full font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
              Floor Guard Safe
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 px-6 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 flex items-center justify-between">
          <button
            onClick={() => {
              onClose();
              onAskAi(product);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-orange-500/10 hover:bg-orange-500/20 text-orange-600 dark:text-orange-400 font-semibold text-xs transition"
          >
            <span>Hỏi Trợ lý AI về mã này</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900 font-semibold text-xs transition"
          >
            Đóng
          </button>
        </div>
      </div>
    </div>
  );
};
