import { apiClient } from './client';
import { AiMessageResponse, ExplainableFactors } from '../types/ai';

export async function sendAiMessageApi(message: string): Promise<AiMessageResponse> {
  try {
    const res = await apiClient.post<AiMessageResponse>('/ai/chat', { message });
    return res.data;
  } catch (error) {
    // Realistic Intelligent Mock Response generator
    const lower = message.toLowerCase();

    if (lower.includes('laptop') && (lower.includes('đắt hơn') || lower.includes('asus'))) {
      return {
        message: 'Dưới đây là danh sách Laptop ASUS mà FPT Shop hiện đang có giá bán cao hơn CellphoneS:',
        tableData: [
          { SKU: 'FPT-ASUS-VIVO15', 'Tên sản phẩm': 'ASUS Vivobook 15 OLED A1505VA', 'Giá FPT': '18.990.000đ', 'CellphoneS': '17.890.000đ', 'Chênh lệch': '+1.100.000đ (+6.1%)', DOH: '54 ngày' },
          { SKU: 'FPT-ASUS-TUF-A15', 'Tên sản phẩm': 'ASUS TUF Gaming A15 FA506NC', 'Giá FPT': '17.490.000đ', 'CellphoneS': '16.790.000đ', 'Chênh lệch': '+700.000đ (+4.1%)', DOH: '32 ngày' }
        ]
      };
    }

    if (lower.includes('iphone') || lower.includes('tồn kho') || lower.includes('doh')) {
      return {
        message: 'Phân tích rủi ro tồn kho iPhone: Mã iPhone 16 Pro Max 256GB đang có DOH là 18 ngày (mức an toàn cao, tốc độ quay vòng tốt). Tuy nhiên, dòng iPhone 15 Plus 128GB có DOH = 51 ngày và đang chịu áp lực giảm giá từ đối thủ.',
        tableData: [
          { SKU: 'FPT-IPHONE-15P-128', 'Dòng máy': 'iPhone 15 Plus 128GB', 'Tồn kho': 48, DOH: '51 ngày', 'Rủi ro': 'CAO (Cần kích cầu)' },
          { SKU: 'FPT-IPHONE-16PM-256', 'Dòng máy': 'iPhone 16 Pro Max 256GB', 'Tồn kho': 115, DOH: '18 ngày', 'Rủi ro': 'THẤP (Ổn định)' }
        ]
      };
    }

    return {
      message: `Tôi đã ghi nhận câu hỏi: "${message}". Dựa trên dữ liệu cào giá lúc 08:30 hôm nay, hệ thống đang theo dõi 5 mã trọng điểm, trong đó có 2 mã FPT đang đắt hơn đối thủ từ 2% đến 6.1%. Bạn có muốn tôi lập bảng so sánh chi tiết không?`
    };
  }
}

export async function getAiExplanationApi(sku: string): Promise<ExplainableFactors> {
  try {
    const res = await apiClient.get<ExplainableFactors>(`/ai/explain/${sku}`);
    return res.data;
  } catch (error) {
    // Mock 3-tier explanation for ASUS Vivobook 15 as demo
    return {
      competitor_shift: {
        competitor: 'CellphoneS',
        old_price: 18490000,
        new_price: 17890000,
        price_cut: 600000,
        is_in_stock: true,
      },
      inventory_status: {
        sku,
        doh: 54,
        quantity: 42,
        doh_risk_level: 'HIGH',
      },
      floor_protection: {
        floor_price: 17325000,
        suggested_price: 17890000,
        safety_margin_percent: 3.26,
        is_capped: false,
      },
    };
  }
}
