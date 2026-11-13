import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 phút: dữ liệu được coi là tươi, chuyển tab không gọi DB
      gcTime: 10 * 60 * 1000,   // 10 phút: lưu trữ trong bộ nhớ đệm trước khi giải phóng
      refetchOnWindowFocus: false, // Tránh re-fetch phiền hà khi focus lại tab trình duyệt
      retry: 1,                 // Thử lại 1 lần nếu network gặp sự cố
    },
  },
});
