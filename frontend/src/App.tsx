import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import { AiChatProvider, useAiChat } from './context/AiChatContext';
import { AppLayout } from './components/layout/AppLayout';
import { PriceMatrixPage } from './pages/PriceMatrixPage';
import { PricingApprovalsPage } from './pages/PricingApprovalsPage';
import { SkuMatchingPage } from './pages/SkuMatchingPage';
import { CrawlManagerPage } from './pages/CrawlManagerPage';
import { ProductDetailModal } from './components/common/ProductDetailModal';
import { AiAssistantManager } from './components/ai/AiAssistantManager';
import { PriceComparisonItem } from './types/pricing';

const AppContent: React.FC = () => {
  const { askExplanationForSku, openExpanded } = useAiChat();
  const [selectedProduct, setSelectedProduct] = useState<PriceComparisonItem | null>(null);

  const handleExplainProduct = (product: PriceComparisonItem) => {
    askExplanationForSku(product.sku, product.name);
  };

  return (
    <AppLayout>
      {({ activeTab, categoryFilter }) => (
        <>
          {activeTab === 'matrix' && (
            <PriceMatrixPage
              categoryFilter={categoryFilter}
              onOpenProductDetail={(prod) => setSelectedProduct(prod)}
              onOpenAiExplain={handleExplainProduct}
            />
          )}

          {activeTab === 'approvals' && (
            <PricingApprovalsPage categoryFilter={categoryFilter} />
          )}

          {activeTab === 'mapping' && <SkuMatchingPage />}

          {activeTab === 'crawler' && <CrawlManagerPage />}

          {activeTab === 'ai' && (
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-8 text-center shadow-sm">
              <h3 className="text-base font-bold text-slate-900 dark:text-white mb-2">
                AI Pricing Studio
              </h3>
              <p className="text-xs text-slate-500 mb-4 max-w-md mx-auto">
                Khung làm việc AI Studio mở rộng cho phép tương tác chuyên sâu, truy vấn RAG bảng giá thị trường và phân tích quyết định giá.
              </p>
              <button
                onClick={openExpanded}
                className="px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-semibold text-xs shadow-lg shadow-orange-600/30 transition"
              >
                Mở Không Gian Phân Tích AI (Expanded Studio)
              </button>
            </div>
          )}

          {/* Product Detail Modal */}
          <ProductDetailModal
            product={selectedProduct}
            onClose={() => setSelectedProduct(null)}
            onAskAi={handleExplainProduct}
          />

          {/* Global Multi-state AI Assistant Widget (FAB -> Popup -> Expanded Drawer) */}
          <AiAssistantManager />
        </>
      )}
    </AppLayout>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AiChatProvider>
        <AppContent />
      </AiChatProvider>
    </ThemeProvider>
  );
};

export default App;
