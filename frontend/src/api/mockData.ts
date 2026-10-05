import { PriceComparisonItem, PricingRecommendation } from '../types/pricing';
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
    scenario: 'Kịch bản 4: DOH = 54d (>45d) & CellphoneS còn hàng -> Khuyến nghị hạ giá bám sát đối thủ',
    margin_impact_percent: -2.3,
    status: 'PENDING'
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
    scenario: 'Kịch bản 4 (Floor Guard): Đối thủ 14.290.000đ thấp hơn giá sàn -> Tự động cap về giá sàn 14.595.000đ',
    margin_impact_percent: -1.8,
    status: 'PENDING'
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
    scenario: 'Kịch bản 2: DOH thấp (18d), FPT cao hơn 2% -> Đề xuất giảm nhẹ 500k giữ lợi thế thương hiệu',
    margin_impact_percent: -0.8,
    status: 'PENDING'
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
  }
];

export const mockCrawlResults: CrawlResult[] = [
  {
    id: 1,
    source: 'CELLPHONES',
    product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA Core i5-13500H',
    url: 'https://cellphones.com.vn/laptop-asus-vivobook-15-oled-a1505va.html',
    price: 17890000,
    is_in_stock: true,
    specifications: {
      'CPU/Chip': 'Intel Core i5-13500H',
      RAM: '16 GB',
      'Bộ nhớ/RAM': '512 GB SSD',
      'Màn hình': '15.6 inch OLED FHD'
    },
    crawled_at: '2026-10-05T08:30:12Z'
  },
  {
    id: 2,
    source: 'HOANGHA',
    product_name: 'ASUS Vivobook 15 OLED A1505VA-L1114W Chính Hãng',
    url: 'https://hoanghamobile.com/laptop/asus-vivobook-15-oled-a1505va-l1114w',
    price: 17990000,
    is_in_stock: true,
    specifications: {
      'Hãng': 'ASUS',
      'CPU': 'Core i5-13500H',
      'RAM': '16 GB'
    },
    crawled_at: '2026-10-05T08:30:45Z'
  },
  {
    id: 3,
    source: 'FPT',
    product_name: 'Laptop ASUS Vivobook 15 OLED A1505VA-L1114W',
    url: 'https://fptshop.com.vn/may-tinh-xach-tay/asus-vivobook-15-oled-a1505va-l1114w',
    price: 18990000,
    is_in_stock: true,
    specifications: {
      CPU: 'Intel Core i5-13500H',
      RAM: '16 GB DDR4',
      SSD: '512 GB'
    },
    crawled_at: '2026-10-05T08:00:00Z'
  }
];
