import { PriceComparisonItem, PricingRecommendation, PriceChangeHistoryItem } from '../types/pricing';
import { SkuMappingPair } from '../types/matching';
import { CrawlResult } from '../types/crawl';

export const mockPriceMatrix: PriceComparisonItem[] = [
  {
    id: 'sku-001',
    sku: 'FPT-ASUS-VIVO15',
    name: 'Laptop ASUS Vivobook 15 OLED A1505VA-L1114W',
    category: 'LAPTOP',
    brand: 'ASUS',
    part_number: 'A1505VA-L1114W',
    fpt_price: 18990000,
    cellphones: {
      source: 'CELLPHONES',
      price: 17890000,
      url: 'https://cellphones.com.vn/laptop-asus-vivobook-15-oled-a1505va.html',
      is_in_stock: true,
      product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA Core i5-13500H'
    },
    hoangha: {
      source: 'HOANGHA',
      price: 17990000,
      url: 'https://hoanghamobile.com/laptop/asus-vivobook-15-oled-a1505va-l1114w',
      is_in_stock: true,
      product_name: 'ASUS Vivobook 15 OLED A1505VA-L1114W Chính Hãng'
    },
    min_competitor_price: 17890000,
    price_diff: 1100000,
    price_diff_percent: 6.15, // > 5% -> DANGER
    confidence_score: 100,
    match_tier: 'EXACT_PART_NUMBER',
    doh: 54, // > 45 days -> Slow moving
    inventory_quantity: 42,
    cost_price: 16500000,
    floor_price: 17325000, // Cost + 5% min margin
    status: 'DANGER'
  },
  {
    id: 'sku-002',
    sku: 'FPT-IPHONE-16PM-256',
    name: 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
    category: 'PHONE',
    brand: 'Apple',
    part_number: 'MYWV3VN/A',
    fpt_price: 34990000,
    cellphones: {
      source: 'CELLPHONES',
      price: 34290000,
      url: 'https://cellphones.com.vn/iphone-16-pro-max.html',
      is_in_stock: true,
      product_name: 'Apple iPhone 16 Pro Max 256GB'
    },
    hoangha: {
      source: 'HOANGHA',
      price: 34190000,
      url: 'https://hoanghamobile.com/dien-thoai-di-dong/iphone-16-pro-max-256gb',
      is_in_stock: false, // Out of stock!
      product_name: 'iPhone 16 Pro Max (256GB) - VN/A'
    },
    min_competitor_price: 34290000,
    price_diff: 700000,
    price_diff_percent: 2.04, // 1-5% -> WARNING
    confidence_score: 100,
    match_tier: 'EXACT_PART_NUMBER',
    doh: 18,
    inventory_quantity: 115,
    cost_price: 31000000,
    floor_price: 32550000,
    status: 'WARNING'
  },
  {
    id: 'sku-003',
    sku: 'FPT-LENOVO-LOQ-15',
    name: 'Laptop Gaming Lenovo LOQ 15IAX9 i5 12450HX/RTX 3050',
    category: 'LAPTOP',
    brand: 'Lenovo',
    part_number: '83GS001RVN',
    fpt_price: 19490000,
    cellphones: {
      source: 'CELLPHONES',
      price: 19990000,
      url: 'https://cellphones.com.vn/laptop-lenovo-loq-15iax9.html',
      is_in_stock: true,
      product_name: 'Laptop Lenovo Gaming LOQ 15IAX9 83GS001RVN'
    },
    hoangha: {
      source: 'HOANGHA',
      price: 19490000,
      url: 'https://hoanghamobile.com/laptop/lenovo-loq-15iax9',
      is_in_stock: true,
      product_name: 'Lenovo LOQ 15IAX9 (83GS001RVN)'
    },
    min_competitor_price: 19490000,
    price_diff: 0,
    price_diff_percent: 0,
    confidence_score: 100,
    match_tier: 'EXACT_PART_NUMBER',
    doh: 28,
    inventory_quantity: 60,
    cost_price: 17200000,
    floor_price: 18060000,
    status: 'EQUAL'
  },
  {
    id: 'sku-004',
    sku: 'FPT-SS-S25-ULTRA',
    name: 'Samsung Galaxy S25 Ultra 12GB 256GB',
    category: 'PHONE',
    brand: 'Samsung',
    part_number: 'SM-S938B',
    fpt_price: 29990000,
    cellphones: {
      source: 'CELLPHONES',
      price: 31490000,
      url: 'https://cellphones.com.vn/samsung-galaxy-s25-ultra.html',
      is_in_stock: true,
      product_name: 'Samsung Galaxy S25 Ultra 12GB 256GB'
    },
    hoangha: {
      source: 'HOANGHA',
      price: 30990000,
      url: 'https://hoanghamobile.com/dien-thoai-di-dong/samsung-galaxy-s25-ultra',
      is_in_stock: true,
      product_name: 'Samsung Galaxy S25 Ultra (12GB/256GB)'
    },
    min_competitor_price: 30990000,
    price_diff: -1000000,
    price_diff_percent: -3.23, // FPT rẻ hơn 3.23% -> SAFE
    confidence_score: 95,
    match_tier: 'NORMALIZED_ATTRIBUTE',
    doh: 12,
    inventory_quantity: 88,
    cost_price: 26500000,
    floor_price: 27825000,
    status: 'SAFE'
  },
  {
    id: 'sku-005',
    sku: 'FPT-DELL-INSP-3520',
    name: 'Laptop Dell Inspiron 3520 i5 1235U/16GB/512GB',
    category: 'LAPTOP',
    brand: 'Dell',
    part_number: 'N3520-i5U165W11',
    fpt_price: 15490000,
    cellphones: {
      source: 'CELLPHONES',
      price: 14290000,
      url: 'https://cellphones.com.vn/laptop-dell-inspiron-3520.html',
      is_in_stock: true,
      product_name: 'Laptop Dell Inspiron 15 3520 25P231'
    },
    min_competitor_price: 14290000,
    price_diff: 1200000,
    price_diff_percent: 8.4, // > 5% -> DANGER
    confidence_score: 85,
    match_tier: 'NORMALIZED_ATTRIBUTE',
    doh: 62, // > 60 days! High danger
    inventory_quantity: 35,
    cost_price: 13900000,
    floor_price: 14595000, // Note: Competitor (14.29M) < Floor (14.595M) -> Need Floor Protection!
    status: 'DANGER'
  }
];

export const mockRecommendations: PricingRecommendation[] = [
  {
    id: 'rec-001',
    sku: 'FPT-ASUS-VIVO15',
    product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA-L1114W',
    category: 'LAPTOP',
    brand: 'ASUS',
    current_price: 18990000,
    suggested_price: 17890000,
    floor_price: 17325000,
    cost_price: 16500000,
    is_floor_protected: false,
    doh: 54,
    inventory_quantity: 42,
    min_competitor_price: 17890000,
    competitor_name: 'CellphoneS',
    competitor_in_stock: true,
    cellphones_price: 17890000,
    cellphones_in_stock: true,
    hoangha_price: 17990000,
    hoangha_in_stock: true,
    scenario: 'Kịch bản 4: DOH = 54d (>45d) & CellphoneS còn hàng -> Khuyến nghị hạ giá bám sát đối thủ',
    margin_impact_percent: -2.3,
    status: 'PENDING',
    composite_score: -0.85,
    demand_score: 0.0,
    inventory_score: -2.0,
    competitor_score: -1.0,
  },
  {
    id: 'rec-002',
    sku: 'FPT-DELL-INSP-3520',
    product_name: 'Laptop Dell Inspiron 3520 i5 1235U/16GB/512GB',
    category: 'LAPTOP',
    brand: 'Dell',
    current_price: 15490000,
    suggested_price: 14595000, // Capped at Floor Price!
    floor_price: 14595000,
    cost_price: 13900000,
    is_floor_protected: true, // Floor protection triggered!
    doh: 62,
    inventory_quantity: 35,
    min_competitor_price: 14290000,
    competitor_name: 'CellphoneS',
    competitor_in_stock: true,
    cellphones_price: 14290000,
    cellphones_in_stock: true,
    hoangha_price: 14490000,
    hoangha_in_stock: true,
    scenario: 'Kịch bản 4 (Floor Guard): Đối thủ 14.290.000đ thấp hơn giá sàn -> Tự động cap về giá sàn 14.595.000đ',
    margin_impact_percent: -1.8,
    status: 'PENDING',
    composite_score: -1.25,
    demand_score: -1.0,
    inventory_score: -2.0,
    competitor_score: -2.0,
  },
  {
    id: 'rec-003',
    sku: 'FPT-IPHONE-16PM-256',
    product_name: 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
    category: 'PHONE',
    brand: 'Apple',
    current_price: 34990000,
    suggested_price: 34490000,
    floor_price: 32550000,
    cost_price: 31000000,
    is_floor_protected: false,
    doh: 18,
    inventory_quantity: 115,
    min_competitor_price: 34290000,
    competitor_name: 'CellphoneS',
    competitor_in_stock: true,
    cellphones_price: 34290000,
    cellphones_in_stock: true,
    hoangha_price: 34390000,
    hoangha_in_stock: true,
    scenario: 'Kịch bản 2: DOH thấp (18d), FPT cao hơn 2% -> Đề xuất giảm nhẹ 500k giữ lợi thế thương hiệu',
    margin_impact_percent: -0.8,
    status: 'PENDING',
    composite_score: 0.65,
    demand_score: 1.0,
    inventory_score: 1.0,
    competitor_score: -1.0,
  }
];

export const mockPriceHistory: PriceChangeHistoryItem[] = [
  // iPhone 16 Pro Max - 3 revisions
  {
    id: 'hist-001',
    sku: 'FPT-IPHONE-16PM-256',
    product_name: 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
    category: 'PHONE',
    old_price: 35490000,
    new_price: 34990000,
    price_change: -500000,
    price_change_percent: -1.41,
    cost_price: 31000000,
    floor_price: 32550000,
    margin_percent: 11.4,
    change_type: 'AI_RECOMMENDED',
    scenario: 'Kịch bản 2: Cạnh tranh đợt mở bán, bám sát CellphoneS',
    changed_by: 'Pricing Analyst',
    changed_at: '2026-10-04T16:20:00Z',
    status: 'SYNCED_POS'
  },
  {
    id: 'hist-001-prev1',
    sku: 'FPT-IPHONE-16PM-256',
    product_name: 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
    category: 'PHONE',
    old_price: 35990000,
    new_price: 35490000,
    price_change: -500000,
    price_change_percent: -1.39,
    cost_price: 31000000,
    floor_price: 32550000,
    margin_percent: 12.6,
    change_type: 'MANUAL_CONFIG',
    scenario: 'Chỉnh tay theo chiến dịch ra mắt mở bán tuần đầu',
    changed_by: 'Senior Pricing Manager',
    changed_at: '2026-09-28T10:15:00Z',
    status: 'SYNCED_POS'
  },
  {
    id: 'hist-001-prev2',
    sku: 'FPT-IPHONE-16PM-256',
    product_name: 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
    category: 'PHONE',
    old_price: 36490000,
    new_price: 35990000,
    price_change: -500000,
    price_change_percent: -1.37,
    cost_price: 31000000,
    floor_price: 32550000,
    margin_percent: 13.8,
    change_type: 'AI_RECOMMENDED',
    scenario: 'Thiết lập mức giá niêm yết cạnh tranh ban đầu',
    changed_by: 'Automated AI System',
    changed_at: '2026-09-20T08:00:00Z',
    status: 'SYNCED_POS'
  },

  // Samsung Galaxy S24 Ultra - 3 revisions
  {
    id: 'hist-002',
    sku: 'FPT-SS-S24U-256',
    product_name: 'Samsung Galaxy S24 Ultra 12GB 256GB Xám Titan',
    category: 'PHONE',
    old_price: 27990000,
    new_price: 26890000,
    price_change: -1100000,
    price_change_percent: -3.93,
    cost_price: 24200000,
    floor_price: 25410000,
    margin_percent: 10.0,
    change_type: 'MANUAL_CONFIG',
    scenario: 'Chỉnh tay theo chương trình Flash Sale cuối tuần (DOH: 38d)',
    changed_by: 'Senior Pricing Manager',
    changed_at: '2026-10-03T09:15:00Z',
    status: 'SYNCED_POS'
  },
  {
    id: 'hist-002-prev1',
    sku: 'FPT-SS-S24U-256',
    product_name: 'Samsung Galaxy S24 Ultra 12GB 256GB Xám Titan',
    category: 'PHONE',
    old_price: 28990000,
    new_price: 27990000,
    price_change: -1000000,
    price_change_percent: -3.45,
    cost_price: 24200000,
    floor_price: 25410000,
    margin_percent: 13.5,
    change_type: 'AI_RECOMMENDED',
    scenario: 'Kịch bản 1: Hoàng Hà hạ giá S24 Ultra, AI đề xuất khớp giá',
    changed_by: 'Pricing Analyst',
    changed_at: '2026-09-25T14:30:00Z',
    status: 'SYNCED_POS'
  },
  {
    id: 'hist-002-prev2',
    sku: 'FPT-SS-S24U-256',
    product_name: 'Samsung Galaxy S24 Ultra 12GB 256GB Xám Titan',
    category: 'PHONE',
    old_price: 29990000,
    new_price: 28990000,
    price_change: -1000000,
    price_change_percent: -3.33,
    cost_price: 24200000,
    floor_price: 25410000,
    margin_percent: 16.5,
    change_type: 'MANUAL_CONFIG',
    scenario: 'Chương trình ưu đãi ngày đôi giữa tháng 9',
    changed_by: 'Pricing Specialist',
    changed_at: '2026-09-15T09:00:00Z',
    status: 'SYNCED_POS'
  },

  // MacBook Air M3 - 2 revisions
  {
    id: 'hist-003',
    sku: 'FPT-MAC-AIR-M3',
    product_name: 'MacBook Air 13 inch M3 8GB 256GB Midnight',
    category: 'LAPTOP',
    old_price: 26990000,
    new_price: 25990000,
    price_change: -1000000,
    price_change_percent: -3.7,
    cost_price: 23500000,
    floor_price: 24675000,
    margin_percent: 9.8,
    change_type: 'AI_RECOMMENDED',
    scenario: 'Kịch bản 4: Hoàng Hà Mobile giảm giá sốc, FPT đồng bộ giá mới',
    changed_by: 'Pricing Analyst',
    changed_at: '2026-10-02T14:45:00Z',
    status: 'SYNCED_POS'
  },
  {
    id: 'hist-003-prev1',
    sku: 'FPT-MAC-AIR-M3',
    product_name: 'MacBook Air 13 inch M3 8GB 256GB Midnight',
    category: 'LAPTOP',
    old_price: 27990000,
    new_price: 26990000,
    price_change: -1000000,
    price_change_percent: -3.57,
    cost_price: 23500000,
    floor_price: 24675000,
    margin_percent: 12.9,
    change_type: 'AI_RECOMMENDED',
    scenario: 'Tối ưu hóa biên lợi nhuận chiến dịch Back to School',
    changed_by: 'Pricing Analyst',
    changed_at: '2026-09-22T11:00:00Z',
    status: 'SYNCED_POS'
  },

  // ASUS Vivobook 15 - 2 revisions
  {
    id: 'hist-004',
    sku: 'FPT-ASUS-VIVO15',
    product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA-L1114W',
    category: 'LAPTOP',
    old_price: 19490000,
    new_price: 18990000,
    price_change: -500000,
    price_change_percent: -2.57,
    cost_price: 16500000,
    floor_price: 17325000,
    margin_percent: 13.1,
    change_type: 'AI_RECOMMENDED',
    scenario: 'Cân đối mức giá xả hàng tồn kho DOH > 45 ngày',
    changed_by: 'Pricing Analyst',
    changed_at: '2026-10-01T15:30:00Z',
    status: 'SYNCED_POS'
  },
  {
    id: 'hist-004-prev1',
    sku: 'FPT-ASUS-VIVO15',
    product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA-L1114W',
    category: 'LAPTOP',
    old_price: 19990000,
    new_price: 19490000,
    price_change: -500000,
    price_change_percent: -2.5,
    cost_price: 16500000,
    floor_price: 17325000,
    margin_percent: 15.3,
    change_type: 'MANUAL_CONFIG',
    scenario: 'Ưu đãi sinh viên đầu năm học mới',
    changed_by: 'Pricing Specialist',
    changed_at: '2026-09-18T10:00:00Z',
    status: 'SYNCED_POS'
  }
];


export const mockMappingQueue: SkuMappingPair[] = [
  {
    id: 'map-001',
    fpt_sku: 'FPT-HP-PAV-14',
    fpt_name: 'Laptop HP Pavilion 14-dv2073TU i5 1235U/16GB/512GB/Vàng',
    fpt_part_number: '7C0V2PA',
    fpt_price: 16990000,
    fpt_specs: {
      CPU: 'Intel Core i5-1235U',
      RAM: '16 GB',
      'Bộ nhớ/RAM': '512 GB SSD',
      'Màn hình': '14 inch FHD IPS',
      'Màu sắc': 'Warm Gold'
    },
    competitor_source: 'CELLPHONES',
    competitor_name: 'Laptop HP Pavilion 14-DV2074TU 7C0V3PA Bạc',
    competitor_url: 'https://cellphones.com.vn/laptop-hp-pavilion-14-dv2074tu.html',
    competitor_price: 16490000,
    competitor_part_number: '7C0V3PA',
    competitor_specs: {
      CPU: 'Intel Core i5-1235U',
      RAM: '16 GB',
      'Bộ nhớ/RAM': '512 GB SSD',
      'Màn hình': '14 inch FHD IPS',
      'Màu sắc': 'Natural Silver'
    },
    confidence_score: 74,
    matched_attributes: ['CPU i5-1235U', 'RAM 16GB', 'SSD 512GB', 'Màn hình 14" FHD'],
    differing_attributes: ['Mã Part: 7C0V2PA vs 7C0V3PA', 'Màu: Vàng vs Bạc'],
    status: 'PENDING'
  },
  {
    id: 'map-002',
    fpt_sku: 'FPT-XIAOMI-14T-512',
    fpt_name: 'Xiaomi 14T 5G 12GB 512GB Đen Titan',
    fpt_price: 13990000,
    fpt_specs: {
      CPU: 'MediaTek Dimensity 8300-Ultra',
      RAM: '12 GB',
      'Bộ nhớ/RAM': '512 GB',
      Pin: '5000 mAh'
    },
    competitor_source: 'HOANGHA',
    competitor_name: 'Xiaomi 14T (12GB/512GB) - Chính Hãng DGW',
    competitor_url: 'https://hoanghamobile.com/dien-thoai-di-dong/xiaomi-14t-12gb-512gb',
    competitor_price: 13290000,
    competitor_specs: {
      CPU: 'Dimensity 8300 Ultra',
      RAM: '12 GB',
      'Bộ nhớ/RAM': '512 GB'
    },
    confidence_score: 78,
    matched_attributes: ['Chip Dimensity 8300', 'RAM 12GB', 'ROM 512GB'],
    differing_attributes: ['Thiếu mã màu trên web đối thủ'],
    status: 'PENDING'
  },
  {
    id: 'map-003',
    fpt_sku: 'FPT-IP16PM-256',
    fpt_name: 'iPhone 16 Pro Max 256GB Titan Sa Mạc',
    fpt_part_number: 'MYWV3VN/A',
    fpt_price: 34990000,
    fpt_specs: {
      Chip: 'Apple A18 Pro 6 nhân',
      RAM: '8 GB',
      'Bộ nhớ/RAM': '256 GB',
      'Màn hình': '6.9 inch Super Retina XDR OLED 120Hz',
      'Màu sắc': 'Titan Sa Mạc'
    },
    competitor_source: 'CELLPHONES',
    competitor_name: 'iPhone 16 Pro Max 256GB | Chính Hãng VN/A - Vàng Sa Mạc',
    competitor_url: 'https://cellphones.com.vn/iphone-16-pro-max.html',
    competitor_price: 34490000,
    competitor_part_number: 'MYWV3VN/A',
    competitor_specs: {
      Chip: 'Apple A18 Pro',
      RAM: '8 GB',
      'Bộ nhớ/RAM': '256 GB',
      'Màn hình': '6.9 inch Super Retina XDR 120Hz',
      'Màu sắc': 'Desert Titanium'
    },
    confidence_score: 79,
    matched_attributes: ['Chip A18 Pro', 'RAM 8GB', 'ROM 256GB', 'Màn hình 6.9" 120Hz', 'Part MYWV3VN/A'],
    differing_attributes: ['Tên màu đối thủ ghi Desert Titanium (tiếng Anh)'],
    status: 'PENDING'
  },
  {
    id: 'map-004',
    fpt_sku: 'FPT-ASUS-VIVO15-OLED',
    fpt_name: 'Laptop ASUS Vivobook 15 OLED A1505VA i5 13500H/16GB/512GB/Bạc',
    fpt_part_number: 'A1505VA-L1114W',
    fpt_price: 18990000,
    fpt_specs: {
      CPU: 'Intel Core i5-13500H (12C/16T)',
      RAM: '16 GB DDR4',
      'Bộ nhớ/RAM': '512 GB PCIe 4.0 SSD',
      'Màn hình': '15.6 inch OLED 2.8K 120Hz',
      'Màu sắc': 'Cool Silver (Bạc)'
    },
    competitor_source: 'HOANGHA',
    competitor_name: 'ASUS Vivobook 15 OLED A1505VA-L1114W Chính Hãng',
    competitor_url: 'https://hoanghamobile.com/laptop/asus-vivobook-15-oled-a1505va-l1114w',
    competitor_price: 17990000,
    competitor_part_number: 'A1505VA-L1114W',
    competitor_specs: {
      CPU: 'Core i5-13500H',
      RAM: '16 GB',
      'Bộ nhớ/RAM': '512 GB SSD',
      'Màn hình': '15.6 inch OLED 2.8K',
      'Màu sắc': 'Bạc'
    },
    confidence_score: 77,
    matched_attributes: ['Mã Part A1505VA-L1114W', 'CPU i5-13500H', 'RAM 16GB', 'SSD 512GB', 'Màn hình 15.6" OLED'],
    differing_attributes: ['Chính sách bảo hành: 2 năm chính hãng vs 24 tháng Hoàng Hà'],
    status: 'PENDING'
  },
  {
    id: 'map-005',
    fpt_sku: 'FPT-SS-S24FE-128',
    fpt_name: 'Samsung Galaxy S24 FE 8GB 128GB Xanh Topaz',
    fpt_part_number: 'SM-S721B',
    fpt_price: 15490000,
    fpt_specs: {
      Chip: 'Exynos 2400e 10 nhân',
      RAM: '8 GB',
      'Bộ nhớ/RAM': '128 GB',
      'Màn hình': '6.7 inch Dynamic AMOLED 2X 120Hz',
      Pin: '4700 mAh'
    },
    competitor_source: 'CELLPHONES',
    competitor_name: 'Samsung Galaxy S24 FE (8GB 128GB) - Đã kích hoạt bảo hành điện tử',
    competitor_url: 'https://cellphones.com.vn/samsung-galaxy-s24-fe.html',
    competitor_price: 13990000,
    competitor_specs: {
      Chip: 'Exynos 2400e',
      RAM: '8 GB',
      'Bộ nhớ/RAM': '128 GB',
      'Màn hình': '6.7 inch Dynamic AMOLED 2X'
    },
    confidence_score: 68,
    matched_attributes: ['Chip Exynos 2400e', 'RAM 8GB', 'ROM 128GB', 'Màn 6.7" AMOLED'],
    differing_attributes: ['Tình trạng máy: Hàng nguyên seal vs Đã kích hoạt BHĐT', 'Thiếu màu sắc'],
    status: 'PENDING'
  },
  {
    id: 'map-006',
    fpt_sku: 'FPT-DELL-INSP-3520',
    fpt_name: 'Laptop Dell Inspiron 3520 i5 1235U/16GB/512GB/Đen',
    fpt_part_number: 'N3520-i5U165W11',
    fpt_price: 15490000,
    fpt_specs: {
      CPU: 'Intel Core i5-1235U (10C/12T)',
      RAM: '16 GB DDR4 3200MHz',
      'Bộ nhớ/RAM': '512 GB M.2 PCIe NVMe SSD',
      'Màn hình': '15.6 inch FHD 120Hz',
      'Màu sắc': 'Carbon Black (Đen)'
    },
    competitor_source: 'CELLPHONES',
    competitor_name: 'Laptop Dell Inspiron 15 3520 25P231 i5 1235U',
    competitor_url: 'https://cellphones.com.vn/laptop-dell-inspiron-3520.html',
    competitor_price: 14290000,
    competitor_part_number: '25P231',
    competitor_specs: {
      CPU: 'Core i5-1235U',
      RAM: '16 GB',
      'Bộ nhớ/RAM': '512 GB SSD',
      'Màn hình': '15.6 inch FHD'
    },
    confidence_score: 65,
    matched_attributes: ['CPU i5-1235U', 'RAM 16GB', 'SSD 512GB', 'Kích thước 15.6 inch'],
    differing_attributes: ['Mã Part FPT N3520-i5U165W11 vs Đối thủ 25P231', 'Tần số quét màn hình: 120Hz vs 60Hz'],
    status: 'PENDING'
  }
];

export const mockCrawlResults: CrawlResult[] = [
  {
    id: 'cr-001',
    source: 'CELLPHONES',
    product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA Core i5-13500H/16GB/512GB',
    url: 'https://cellphones.com.vn/laptop-asus-vivobook-15-oled-a1505va.html',
    price: 17890000,
    original_price: 19990000,
    is_in_stock: true,
    category: 'LAPTOP',
    specifications: {
      'CPU/Chip': 'Intel Core i5-13500H (12 nhân 16 luồng)',
      'RAM': '16 GB DDR4 3200MHz',
      'Bộ nhớ/SSD': '512 GB M.2 NVMe PCIe 3.0',
      'Màn hình': '15.6 inch OLED 2.8K 120Hz 600 nits',
      'Đồ họa': 'Intel Iris Xe Graphics',
      'Trọng lượng': '1.7 kg',
      'Pin': '50 Whr 3-cell Li-ion'
    },
    crawled_at: '2026-10-07T08:30:12Z'
  },
  {
    id: 'cr-002',
    source: 'HOANGHA',
    product_name: 'ASUS Vivobook 15 OLED A1505VA-L1114W Chính Hãng',
    url: 'https://hoanghamobile.com/laptop/asus-vivobook-15-oled-a1505va-l1114w',
    price: 17990000,
    original_price: 19990000,
    is_in_stock: true,
    category: 'LAPTOP',
    specifications: {
      'Hãng': 'ASUS',
      'CPU': 'Intel Core i5-13500H',
      'RAM': '16 GB',
      'Ổ cứng': '512 GB SSD PCIe',
      'Màn hình': '15.6 inch OLED 2.8K',
      'Bảo hành': '24 tháng chính hãng'
    },
    crawled_at: '2026-10-07T08:30:45Z'
  },
  {
    id: 'cr-003',
    source: 'CELLPHONES',
    product_name: 'Apple iPhone 16 Pro Max 256GB - Chính Hãng VN/A Titan Sa Mạc',
    url: 'https://cellphones.com.vn/iphone-16-pro-max.html',
    price: 34290000,
    original_price: 34990000,
    is_in_stock: true,
    category: 'PHONE',
    specifications: {
      'Chipset': 'Apple A18 Pro 6 lõi',
      'RAM': '8 GB',
      'Bộ nhớ trong': '256 GB',
      'Màn hình': '6.9 inch Super Retina XDR OLED 120Hz',
      'Camera sau': 'Chính 48MP + Góc rộng 48MP + Tele 5x 12MP',
      'Chất liệu viền': 'Titan cấp 5 hoàn thiện nhám'
    },
    crawled_at: '2026-10-07T09:15:20Z'
  },
  {
    id: 'cr-004',
    source: 'HOANGHA',
    product_name: 'iPhone 16 Pro Max (256GB) - VN/A Titan Tự Nhiên',
    url: 'https://hoanghamobile.com/dien-thoai-di-dong/iphone-16-pro-max-256gb',
    price: 34190000,
    original_price: 34990000,
    is_in_stock: false,
    category: 'PHONE',
    specifications: {
      'Chip': 'Apple A18 Pro',
      'RAM': '8 GB',
      'Bộ nhớ trong': '256 GB',
      'Màn hình': '6.9 inch OLED ProMotion 120Hz',
      'Pin': 'Hỗ trợ sạc nhanh MagSafe 25W'
    },
    crawled_at: '2026-10-07T09:12:10Z'
  },
  {
    id: 'cr-005',
    source: 'CELLPHONES',
    product_name: 'Samsung Galaxy S24 Ultra 12GB 256GB Xám Titan',
    url: 'https://cellphones.com.vn/samsung-galaxy-s24-ultra.html',
    price: 25990000,
    original_price: 31990000,
    is_in_stock: true,
    category: 'PHONE',
    specifications: {
      'Chipset': 'Snapdragon 8 Gen 3 for Galaxy (4nm)',
      'RAM': '12 GB',
      'Bộ nhớ': '256 GB UFS 4.0',
      'Màn hình': '6.8 inch Dynamic LTPO AMOLED 2X 120Hz 2600 nits',
      'Bút cảm ứng': 'S-Pen tích hợp có Bluetooth',
      'Pin': '5000 mAh sạc nhanh 45W'
    },
    crawled_at: '2026-10-07T08:50:00Z'
  },
  {
    id: 'cr-006',
    source: 'HOANGHA',
    product_name: 'Samsung Galaxy S24 Ultra (12GB/256GB) - Chính hãng',
    url: 'https://hoanghamobile.com/dien-thoai-di-dong/samsung-galaxy-s24-ultra-12gb-256gb',
    price: 25790000,
    original_price: 31990000,
    is_in_stock: true,
    category: 'PHONE',
    specifications: {
      'Vi xử lý': 'Qualcomm Snapdragon 8 Gen 3',
      'RAM': '12 GB',
      'Bộ nhớ': '256 GB',
      'Camera': '200MP + 50MP + 12MP + 10MP',
      'Kháng nước': 'IP68'
    },
    crawled_at: '2026-10-07T08:52:15Z'
  },
  {
    id: 'cr-007',
    source: 'CELLPHONES',
    product_name: 'Apple MacBook Air 13 inch M3 2024 (8GB RAM / 256GB SSD) Midnight',
    url: 'https://cellphones.com.vn/macbook-air-m3-13-inch-8gb-256gb.html',
    price: 25490000,
    original_price: 27990000,
    is_in_stock: true,
    category: 'LAPTOP',
    specifications: {
      'Chip': 'Apple M3 8 nhân CPU 8 nhân GPU',
      'RAM': '8 GB Unified Memory',
      'SSD': '256 GB',
      'Màn hình': '13.6 inch Liquid Retina 500 nits',
      'Trọng lượng': '1.24 kg',
      'Cổng kết nối': 'MagSafe 3, 2x Thunderbolt / USB 4'
    },
    crawled_at: '2026-10-07T07:45:00Z'
  },
  {
    id: 'cr-008',
    source: 'HOANGHA',
    product_name: 'MacBook Air 13" M3 (8GB/256GB) - Chính hãng Apple Việt Nam',
    url: 'https://hoanghamobile.com/laptop/macbook-air-13-m3-8gb-256gb',
    price: 25290000,
    original_price: 27990000,
    is_in_stock: true,
    category: 'LAPTOP',
    specifications: {
      'CPU': 'Apple M3 8-core',
      'GPU': '8-core GPU',
      'RAM': '8 GB',
      'Ổ cứng': '256 GB SSD',
      'Màn hình': '13.6 inch Retina True Tone'
    },
    crawled_at: '2026-10-07T07:46:12Z'
  },
  {
    id: 'cr-009',
    source: 'CELLPHONES',
    product_name: 'Laptop HP Pavilion 14-dv2074TU i5 1235U/16GB/512GB Bạc (7C0V3PA)',
    url: 'https://cellphones.com.vn/laptop-hp-pavilion-14-dv2074tu.html',
    price: 16490000,
    original_price: 17990000,
    is_in_stock: true,
    category: 'LAPTOP',
    specifications: {
      'CPU': 'Intel Core i5-1235U 10 nhân 12 luồng',
      'RAM': '16 GB DDR4 3200',
      'SSD': '512 GB PCIe NVMe',
      'Màn hình': '14.0 inch Full HD IPS viền mỏng',
      'Mã Part': '7C0V3PA'
    },
    crawled_at: '2026-10-07T06:10:00Z'
  },
  {
    id: 'cr-010',
    source: 'CELLPHONES',
    product_name: 'Xiaomi 14T Pro 5G 12GB 512GB Titan Đen',
    url: 'https://cellphones.com.vn/xiaomi-14t-pro.html',
    price: 16490000,
    original_price: 17990000,
    is_in_stock: false,
    category: 'PHONE',
    specifications: {
      'Vi xử lý': 'MediaTek Dimensity 9300+ (4nm)',
      'RAM': '12 GB LPDDR5X',
      'Bộ nhớ': '512 GB UFS 4.0',
      'Ống kính': 'Leica Summilux 50MP',
      'Màn hình': '6.67 inch AMOLED 144Hz 4000 nits',
      'Sạc nhanh': '120W HyperCharge'
    },
    crawled_at: '2026-10-07T08:00:15Z'
  },
  {
    id: 'cr-011',
    source: 'HOANGHA',
    product_name: 'Xiaomi 14T Pro (12GB/512GB) - Chính hãng DGW',
    url: 'https://hoanghamobile.com/dien-thoai-di-dong/xiaomi-14t-pro-12gb-512gb',
    price: 16290000,
    original_price: 17990000,
    is_in_stock: true,
    category: 'PHONE',
    specifications: {
      'Chip': 'MediaTek Dimensity 9300+',
      'RAM': '12 GB',
      'Bộ nhớ': '512 GB',
      'Màn hình': '6.67 inch 1.5K 144Hz',
      'Camera': 'Leica 50MP'
    },
    crawled_at: '2026-10-07T08:05:00Z'
  },
  {
    id: 'cr-012',
    source: 'HOANGHA',
    product_name: 'Laptop Dell Inspiron 15 3520 (25P231) Core i5-1235U / 16GB / 512GB',
    url: 'https://hoanghamobile.com/laptop/dell-inspiron-3520-25p231',
    price: 14290000,
    original_price: 15990000,
    is_in_stock: true,
    category: 'LAPTOP',
    specifications: {
      'CPU': 'Intel Core i5-1235U',
      'RAM': '16 GB DDR4',
      'Ổ cứng': '512 GB SSD M.2',
      'Màn hình': '15.6 inch FHD 120Hz',
      'Part Number': '25P231'
    },
    crawled_at: '2026-10-07T07:15:30Z'
  }
];

