import React from 'react';
import { ExternalLink } from 'lucide-react';
import { PriceComparisonItem } from '../../types/pricing';
import { formatCurrencyVND } from '../../utils/formatters';
import { Modal } from './Modal';
import { Badge } from './Badge';
import { Button } from './Button';

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
    <Modal
      isOpen={!!product}
      onClose={onClose}
      title={product.name}
      subtitle={`SKU: ${product.sku}${product.part_number ? ` | PN: ${product.part_number}` : ''} | DANH MỤC: ${product.category}`}
      maxWidth="2xl"
    >
      <div className="space-y-4 text-xs">
        {/* Price & Competitor Comparison Cards */}
        <div>
          <div className="text-2xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
            VỊ THẾ GIÁ THỊ TRƯỜNG 3 BÊN
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {/* FPT */}
            <div className="p-3 rounded-xl border border-orange-300 dark:border-orange-800/80 bg-orange-50/20 dark:bg-orange-950/20">
              <div className="flex items-center justify-between">
                <span className="text-2xs font-bold text-orange-600 dark:text-orange-400 font-mono">
                  FPT SHOP
                </span>
                <Badge size="sm" variant="warning">CHUẨN</Badge>
              </div>
              <div className="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">
                {formatCurrencyVND(product.fpt_price)}
              </div>
              <div className="text-2xs text-slate-400 mt-1 font-mono">
                KHO: {product.inventory_quantity} | DOH: {product.doh}d
              </div>
            </div>

            {/* CellphoneS */}
            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850">
              <div className="flex items-center justify-between text-2xs font-bold text-slate-700 dark:text-slate-300 font-mono">
                <span>CELLPHONES</span>
                {product.cellphones && (
                  <a
                    href={product.cellphones.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-slate-400 hover:text-orange-600 p-0.5 rounded transition"
                    title="Mở liên kết CellphoneS"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
              <div className="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">
                {product.cellphones ? formatCurrencyVND(product.cellphones.price) : '—'}
              </div>
              <div className="text-2xs text-slate-400 mt-1">
                <Badge size="sm" variant={product.cellphones?.is_in_stock ? 'success' : 'neutral'}>
                  {product.cellphones?.is_in_stock ? 'CÒN HÀNG' : 'HẾT HÀNG'}
                </Badge>
              </div>
            </div>

            {/* Hoàng Hà */}
            <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850">
              <div className="flex items-center justify-between text-2xs font-bold text-slate-700 dark:text-slate-300 font-mono">
                <span>HOÀNG HÀ</span>
                {product.hoangha && (
                  <a
                    href={product.hoangha.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-slate-400 hover:text-orange-600 p-0.5 rounded transition"
                    title="Mở liên kết Hoàng Hà"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
              <div className="text-base font-bold font-mono text-slate-900 dark:text-white mt-1">
                {product.hoangha ? formatCurrencyVND(product.hoangha.price) : '—'}
              </div>
              <div className="text-2xs text-slate-400 mt-1">
                <Badge size="sm" variant={product.hoangha?.is_in_stock ? 'success' : 'neutral'}>
                  {product.hoangha?.is_in_stock ? 'CÒN HÀNG' : 'HẾT HÀNG'}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Specifications Breakdown */}
        <div>
          <div className="text-2xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-2">
            THÔNG SỐ KỸ THUẬT BÓC TÁCH
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs font-mono text-slate-400 uppercase block">Vi xử lý (CPU)</span>
              <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">
                Core i5-13500H / Snapdragon 8 Gen 3
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs font-mono text-slate-400 uppercase block">RAM &amp; Lưu trữ</span>
              <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">
                16 GB RAM | 512 GB SSD NVMe
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs font-mono text-slate-400 uppercase block">Màn hình</span>
              <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">
                OLED FHD 100% DCI-P3 600nits
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800">
              <span className="text-2xs font-mono text-slate-400 uppercase block">Pin &amp; Nguồn</span>
              <span className="font-semibold text-xs text-slate-800 dark:text-slate-200">
                50 Whrs Li-ion 3-cell Fast Charge
              </span>
            </div>
          </div>
        </div>

        {/* Pricing Guard Context */}
        <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-850 flex items-center justify-between">
          <div>
            <div className="font-bold text-slate-900 dark:text-white font-mono text-xs">
              GIÁ SÀN BẢO VỆ: {formatCurrencyVND(product.floor_price)}
            </div>
            <div className="text-2xs text-slate-500 font-mono mt-0.5">
              GIÁ VỐN: {formatCurrencyVND(product.cost_price)} (BIÊN AN TOÀN TỐI THIỂU: 5%)
            </div>
          </div>
          <Badge size="sm" variant="floor">
            FLOOR GUARD SAFE
          </Badge>
        </div>

        {/* Footer Actions */}
        <div className="pt-2 flex items-center justify-between border-t border-slate-100 dark:border-slate-800">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              onClose();
              onAskAi(product);
            }}
          >
            Hỏi AI Copilot về mã này
          </Button>

          <Button size="sm" variant="secondary" onClick={onClose}>
            Đóng
          </Button>
        </div>
      </div>
    </Modal>
  );
};
