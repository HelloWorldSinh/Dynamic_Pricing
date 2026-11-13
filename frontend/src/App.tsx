import React, { useState, useEffect } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
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

interface TabContainerProps {
  activeTab: string;
  categoryFilter: string;
  onOpenProductDetail: (product: PriceComparisonItem) => void;
}

const TabContainer: React.FC<TabContainerProps> = ({
  activeTab,
  categoryFilter,
  onOpenProductDetail,
}) => {
  const [visitedTabs, setVisitedTabs] = useState<Set<string>>(() => new Set([activeTab]));

  useEffect(() => {
    setVisitedTabs((prev) => {
      if (prev.has(activeTab)) return prev;
      const next = new Set(prev);
      next.add(activeTab);
      return next;
    });
  }, [activeTab]);

  return (
    <>
      {visitedTabs.has('matrix') && (
        <div className={activeTab === 'matrix' ? 'block' : 'hidden'}>
          <PriceMatrixPage
            categoryFilter={categoryFilter}
            onOpenProductDetail={onOpenProductDetail}
          />
        </div>
      )}

      {visitedTabs.has('approvals') && (
        <div className={activeTab === 'approvals' ? 'block' : 'hidden'}>
          <PricingApprovalsPage categoryFilter={categoryFilter} />
        </div>
      )}

      {visitedTabs.has('mapping') && (
        <div className={activeTab === 'mapping' ? 'block' : 'hidden'}>
          <SkuMatchingPage />
        </div>
      )}

      {visitedTabs.has('crawler') && (
        <div className={activeTab === 'crawler' ? 'block' : 'hidden'}>
          <CrawlManagerPage />
        </div>
      )}
    </>
  );
};

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
          <TabContainer
            activeTab={activeTab}
            categoryFilter={categoryFilter}
            onOpenProductDetail={(prod) => setSelectedProduct(prod)}
          />

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
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AiChatProvider>
          <AppContent />
        </AiChatProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
