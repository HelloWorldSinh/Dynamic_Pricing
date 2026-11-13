import React from 'react';
import { AiFloatingButton } from './AiFloatingButton';
import { ExpandedAiDrawer } from './ExpandedAiDrawer';

export const AiAssistantManager: React.FC = () => {
  return (
    <>
      {/* State 1: Floating Action Button */}
      <AiFloatingButton />

      {/* State 2: Full-screen Studio Modal */}
      <ExpandedAiDrawer />
    </>
  );
};
