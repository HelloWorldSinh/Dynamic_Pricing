import React from 'react';
import { AiFloatingButton } from './AiFloatingButton';
import { CompactChatPopup } from './CompactChatPopup';
import { ExpandedAiDrawer } from './ExpandedAiDrawer';

export const AiAssistantManager: React.FC = () => {
  return (
    <>
      {/* State 1: Floating Action Button */}
      <AiFloatingButton />

      {/* State 2: Compact Popup Chat Widget (380px) */}
      <CompactChatPopup />

      {/* State 3: Expanded Studio / Wide Drawer (750px) */}
      <ExpandedAiDrawer />
    </>
  );
};
