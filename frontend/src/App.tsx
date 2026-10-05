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
  const { askExplanationForSku } = useAiChat();
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
