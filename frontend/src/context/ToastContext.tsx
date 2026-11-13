import React, { createContext, useContext, useState, useCallback } from 'react';

export type ToastType = 'success' | 'warning' | 'danger' | 'info';

export interface ToastMessage {
  id: string;
  title: string;
  message?: string;
  type: ToastType;
}

export interface ToastOptions {
  title: string;
  message?: string;
  type?: ToastType;
  duration?: number;
}

interface ToastContextValue {
  toasts: ToastMessage[];
  showToast: (options: ToastOptions) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ title, message, type = 'info', duration = 3500 }: ToastOptions) => {
      const id = Date.now().toString(36) + Math.random().toString(36).substring(2, 6);
      const newToast: ToastMessage = { id, title, message, type };

      setToasts((prev) => [...prev.slice(-3), newToast]); // Giữ tối đa 4 toast cùng lúc

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast }}>
      {children}
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

