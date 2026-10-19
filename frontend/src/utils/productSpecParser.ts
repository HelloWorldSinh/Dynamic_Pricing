/**
 * ICT Product Specification Auto-Parser
 * Chuyên trách bóc tách các thông số kỹ thuật (CPU, RAM, Ổ cứng, Màn hình, GPU, Màu sắc...)
 * trực tiếp từ Tên sản phẩm khi dữ liệu specs từ scraper hoặc DB bị khuyết thiếu.
 */

export interface ParsedSpecs {
  cpu?: string;
  ram?: string;
  storage?: string;
  screen?: string;
  gpu?: string;
  color?: string;
  brand?: string;
  os?: string;
  partNumber?: string;
}

const BRAND_MAP: Record<string, string> = {
  apple: 'Apple',
  iphone: 'Apple',
  macbook: 'Apple',
  ipad: 'Apple',
  asus: 'ASUS',
  dell: 'Dell',
  hp: 'HP',
  lenovo: 'Lenovo',
  acer: 'Acer',
  msi: 'MSI',
  samsung: 'Samsung',
  galaxy: 'Samsung',
  xiaomi: 'Xiaomi',
  redmi: 'Xiaomi',
  poco: 'Xiaomi',
  oppo: 'OPPO',
  vivo: 'Vivo',
  realme: 'Realme',
  honor: 'Honor',
  tecno: 'Tecno',
};

const COLOR_PATTERNS = [
  'titan sa mạc', 'desert titanium',
  'titan tự nhiên', 'natural titanium',
  'titan đen', 'black titanium',
  'titan trắng', 'white titanium',
  'xám không gian', 'space gray', 'space grey',
  'đen không gian', 'space black',
  'xanh dương', 'xanh lam', 'blue', 'sky blue', 'sierra blue',
  'xanh lá', 'xanh lục', 'green', 'midnight green',
  'vàng cát', 'vàng', 'gold', 'starlight',
  'bạc', 'silver',
  'tím', 'purple',
  'hồng', 'pink', 'rose gold',
  'xám', 'gray', 'grey',
  'đỏ', 'red',
  'đen', 'black', 'midnight',
  'trắng', 'white',
];

export function extractSpecsFromTitle(title: string): ParsedSpecs {
  if (!title) return {};
  const t = title.trim();
  const lower = t.toLowerCase();
  const isLaptop = /\b(laptop|macbook|notebook|zenbook|vivobook|tuf|rog|ideapad|thinkpad|legion|loq|inspiron|vostro|victus|pavilion|omen|aspire|nitro|predator)\b/i.test(t);
  const isPhone = /\b(iphone|galaxy|redmi|poco|oppo|vivo|realme|tecno|xiaomi|điện thoại)\b/i.test(t);

  const res: ParsedSpecs = {};

  // 1. Thương hiệu (Brand)
  for (const [kw, brand] of Object.entries(BRAND_MAP)) {
    const reg = new RegExp(`\\b${kw}\\b`, 'i');
    if (reg.test(lower)) {
      res.brand = brand;
      break;
    }
  }

  // 2. CPU / Vi xử lý
  // Intel Core i3/i5/i7/i9 hoặc Core Ultra
  const intelMatch = t.match(/\b(?:Intel\s+)?(?:Core\s+)?(i[3579][-_ ]\d{4,5}[A-Z0-9]*|Core\s+Ultra\s*[579]\s*[-_ ]?\d{3}[A-Z0-9]*)/i);
  if (intelMatch) {
    const rawCpu = intelMatch[1].replace(/[-_]/g, ' ').replace(/\s+/g, ' ').trim();
    res.cpu = `Intel ${rawCpu.startsWith('i') ? 'Core ' + rawCpu : rawCpu}`;
  }

  // AMD Ryzen
  if (!res.cpu) {
    const amdMatch = t.match(/\b(?:AMD\s+)?(?:Ryzen|R)[-_ ]?([3579])[-_ ]?(\d{4}[A-Z0-9]*)/i);
    if (amdMatch) {
      res.cpu = `AMD Ryzen ${amdMatch[1]} ${amdMatch[2]}`;
    }
  }

  // Apple M-series
  if (!res.cpu) {
    const appleMMatch = t.match(/\b(M[1234](?:\s*(?:Pro|Max|Ultra))?)\b/i);
    if (appleMMatch) {
      res.cpu = `Apple ${appleMMatch[1].toUpperCase()}`;
    }
  }

  // Mobile CPUs: Apple A-series, Snapdragon, Dimensity, Helio, Exynos
  if (!res.cpu) {
    const mobileCpuMatch = t.match(/\b(A1[4-8]\s*(?:Pro|Bionic)?|Snapdragon\s*[0-9]+[a-zA-Z0-9\+ ]*|Dimensity\s*[0-9]+[a-zA-Z0-9 ]*|Helio\s*[A-Z0-9]+|Exynos\s*[0-9]+)\b/i);
    if (mobileCpuMatch) {
      res.cpu = mobileCpuMatch[1].trim();
    }
  }

  // 3. RAM & Ổ cứng (Storage/SSD)
  // Mẫu kết hợp thường gặp: "16GB/512GB", "8GB/256GB", "16GB / 1TB", "12GB 256GB", "8GB-128GB"
  const pairMatch = t.match(/\b(4|6|8|12|16|24|32|64)\s*GB\s*[/_\- ]\s*(64|128|256|512)\s*GB\b/i);
  const tbPairMatch = t.match(/\b(8|12|16|24|32|64)\s*GB\s*[/_\- ]\s*(1|2)\s*TB\b/i);

  if (pairMatch) {
    res.ram = `${pairMatch[1]}GB`;
    res.storage = isLaptop ? `${pairMatch[2]}GB SSD` : `${pairMatch[2]}GB`;
  } else if (tbPairMatch) {
    res.ram = `${tbPairMatch[1]}GB`;
    res.storage = `${tbPairMatch[2]}TB SSD`;
  } else {
    // Tìm RAM độc lập
    const ramStandalone = t.match(/(?:RAM|Bộ nhớ RAM)\s*[: ]?\s*(4|6|8|12|16|24|32|64)\s*GB\b/i) ||
      t.match(/\b(4|6|8|12|16|24|32|64)\s*GB\s*RAM\b/i);
    if (ramStandalone) {
      res.ram = `${ramStandalone[1]}GB`;
    }

    // Tìm Ổ cứng độc lập (SSD / ROM)
    const tbMatch = t.match(/\b(1|2)\s*TB\b/i);
    if (tbMatch) {
      res.storage = `${tbMatch[1]}TB SSD`;
    } else {
      const romMatch = t.match(/\b(64|128|256|512)\s*GB\s*(?:SSD|ROM|bộ nhớ)?\b/i) ||
        t.match(/\b(64|128|256|512)\s*GB\b/i);
      if (romMatch) {
        res.storage = isLaptop ? `${romMatch[1]}GB SSD` : `${romMatch[1]}GB`;
      }
    }
  }

  // 4. Màn hình (Screen)
  const screenInchMatch = t.match(/\b(13\.3|14|14\.0|15|15\.6|16|16\.0|17|17\.3|6\.1|6\.3|6\.36|6\.67|6\.7|6\.8|6\.9)\s*(?:inch|"|'')?\b/i);
  const displayTechMatch = t.match(/\b(OLED|AMOLED|Super Retina XDR|Dynamic AMOLED 2X|IPS|Retina|120Hz|144Hz|165Hz|2\.8K|FHD|QHD)\b/i);

  if (screenInchMatch && displayTechMatch) {
    res.screen = `${screenInchMatch[1]} inch ${displayTechMatch[1]}`;
  } else if (screenInchMatch && isLaptop) {
    res.screen = `${screenInchMatch[1]} inch`;
  } else if (displayTechMatch) {
    res.screen = displayTechMatch[1];
  }

  // 5. Card đồ họa (GPU - Cho Laptop)
  const gpuMatch = t.match(/\b(RTX\s*\d{4}(?:\s*Ti)?(?:\s*\d+GB)?|GTX\s*\d{4}(?:\s*Ti)?|Intel\s*Iris\s*Xe|Iris\s*Xe|Intel\s*Arc|Radeon\s*[0-9A-Z]*)\b/i);
  if (gpuMatch) {
    res.gpu = gpuMatch[1].trim();
  }

  // 6. Màu sắc (Color)
  for (const c of COLOR_PATTERNS) {
    const reg = new RegExp(`(?:^|\\s|,|\\()(${c})(?:\\s|,|\\)|$)`, 'i');
    const m = t.match(reg);
    if (m) {
      // Viết hoa chữ cái đầu cho đẹp
      res.color = m[1].split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
      break;
    }
  }

  // 7. Hệ điều hành (OS)
  if (/\b(macbook|imac|mac mini)\b/i.test(t)) {
    res.os = 'macOS';
  } else if (/\b(iphone|ipad)\b/i.test(t)) {
    res.os = /\bipad\b/i.test(t) ? 'iPadOS' : 'iOS';
  } else if (isLaptop) {
    res.os = /\bwin(?:dows)?\s*11\s*pro\b/i.test(t) ? 'Windows 11 Pro' : 'Windows 11 Home';
  } else if (isPhone) {
    res.os = 'Android';
  }

  // 8. Mã Part / Model Code
  const partBlacklist = /\b(core[-_ ]?i[3579]|ryzen[-_ ]?[3579]|rtx[-_ ]?\d{4}|gtx[-_ ]?\d{4}|intel|amd|nvidia|oled|amoled|ips|ddr[45]|gen[-_ ]?\d+|wifi[-_ ]?\d+|gb|tb|ssd|ram)\b/i;
  
  // Model dạng hyphen: A1505VA-L1114W, FA506NC-HN011W, AN515-58-52SP
  const hyphenParts = t.match(/\b([A-Za-z0-9]{2,8}(?:-[A-Za-z0-9]{2,8}){1,3})\b/g);
  if (hyphenParts) {
    for (const p of hyphenParts) {
      if (!partBlacklist.test(p) && /\d/.test(p) && /[a-zA-Z]/.test(p)) {
        res.partNumber = p.toUpperCase();
        break;
      }
    }
  }

  // Model Apple: MYD92ZP/A, MU773ZA/A
  if (!res.partNumber) {
    const applePart = t.match(/\b([A-Z0-9]{5,}\/(?:A|B|SA|VN|ZP))\b/i);
    if (applePart) {
      res.partNumber = applePart[1].toUpperCase();
    }
  }

  // Model Lenovo: 83UQ003NVN, 82XV00QPVM
  if (!res.partNumber) {
    const lenovoPart = t.match(/\b(8[0-9][A-Za-z0-9]{6,8})\b/);
    if (lenovoPart) {
      res.partNumber = lenovoPart[1].toUpperCase();
    }
  }

  return res;
}

/**
 * Chuẩn hóa chuỗi thông số để so khớp thông minh
 * (Ví dụ: "512GB SSD" và "512 GB" -> "512gb")
 */
export function normalizeSpecValue(val: string): string {
  if (!val || val === '—') return '';
  return val
    .toLowerCase()
    .replace(/\s*(ssd|rom|ram|bộ nhớ(?:\s*trong)?|ổ cứng|chính hãng|vn\/a|vna)\s*/gi, '')
    .replace(/["'”’]|inch/gi, '')
    .replace(/[-_]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * So khớp 2 thông số kỹ thuật (hỗ trợ so sánh mềm dẻo các đơn vị RAM/SSD)
 */
export function isSpecMatch(valA: string, valB: string): boolean {
  if (!valA || valA === '—' || !valB || valB === '—') return false;
  const normA = normalizeSpecValue(valA);
  const normB = normalizeSpecValue(valB);
  if (normA === normB) return true;
  // Bỏ toàn bộ khoảng trắng: "16 gb" vs "16gb"
  return normA.replace(/\s+/g, '') === normB.replace(/\s+/g, '');
}
