"""Module trích xuất đặc trưng (Feature Extractor) cho sản phẩm công nghệ (ICT)."""

import re
from typing import List, Optional, Set
from app.services.matching.models import SkuFeatures


class FeatureExtractor:
    """Chuyên trách bóc tách các thuộc tính kỹ thuật từ tên sản phẩm:
    - Thương hiệu (Brand)
    - Part-Number (có Negative Blacklist loại trừ CPU/GPU)
    - Dung lượng RAM và ROM
    - Định danh Model cứng (Hard Model Identifier)
    """

    BRAND_MAP = {
        "apple": "apple", "iphone": "apple", "macbook": "apple", "ipad": "apple",
        "samsung": "samsung", "galaxy": "samsung",
        "xiaomi": "xiaomi", "redmi": "xiaomi", "poco": "xiaomi",
        "oppo": "oppo", "vivo": "vivo", "realme": "realme", "tecno": "tecno",
        "tcl": "tcl", "zte": "zte",
        "acer": "acer", "asus": "asus", "lenovo": "lenovo", "dell": "dell",
        "hp": "hp", "msi": "msi", "honor": "honor",
        "tcl": "tcl", "infinix": "infinix", "itel": "itel",
        "nokia": "nokia", "masstel": "masstel", "sony": "sony", "huawei": "huawei"
    }

    # Bảng chuẩn hóa màu sắc sản phẩm
    COLOR_MAP = {
        "titan tự nhiên": "titanium", "natural titanium": "titanium",
        "space black": "black", "đen không gian": "black",
        "space gray": "gray", "space grey": "gray", "xám không gian": "gray",
        "sierra blue": "blue", "sky blue": "blue", "xanh dương": "blue", "xanh lam": "blue",
        "xanh lá": "green", "xanh lục": "green", "midnight green": "green",
        "midnight": "black", "starlight": "white",
        "đen": "black", "black": "black",
        "trắng": "white", "white": "white",
        "xanh": "blue", "blue": "blue",
        "titan": "titanium", "titanium": "titanium",
        "vàng": "gold", "gold": "gold",
        "bạc": "silver", "silver": "silver",
        "tím": "purple", "purple": "purple",
        "hồng": "pink", "pink": "pink", "rose": "pink",
        "xám": "gray", "gray": "gray", "grey": "gray",
        "đỏ": "red", "red": "red",
        "cam": "orange", "orange": "orange"
    }

    LAPTOP_LINES = (
        "macbook air", "macbook pro", "macbook",
        "aspire 7", "aspire go", "aspire lite", "nitro v", "nitro lite", "nitro", "predator", "swift",
        "vivobook go", "vivobook s14", "vivobook 14", "vivobook", "tuf gaming", "rog strix", "zenbook",
        "ideapad slim", "ideapad gaming", "loq", "legion", "thinkbook",
        "inspiron", "vostro", "latitude", "pavilion", "victus", "omen", "katana"
    )

    # Blacklist loại trừ mã linh kiện chung không được coi là Part-Number sản phẩm
    PART_BLACKLIST_PATTERNS = [
        re.compile(r"^(?:CORE[-_]?)?[IR][3579][-_]\d+", re.I),           # i5-12500H, r5-7535HS, i7-13700H
        re.compile(r"^(?:RTX|GTX)[-_]\d+", re.I),                       # RTX-3050, GTX-1650
        re.compile(r"^\d+[-_]\d+[-_]?(?:INCH)?$", re.I),               # 15-6, 14-0, 15-6-INCH
        re.compile(r"^(?:WIN|WINDOWS)[-_]\d+", re.I),                   # WIN-11
        re.compile(r"^(?:FHD|QHD|UHD|OLED|IPS)[-_]", re.I),             # FHD-144HZ
    ]

    @classmethod
    def detect_brand(cls, text: str) -> Optional[str]:
        """Chuẩn hóa và nhận diện thương hiệu chuẩn (Brand Normalization)."""
        if not text:
            return None
        t = text.lower()
        for kw, canonical in cls.BRAND_MAP.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", t):
                return canonical
        return None

    @classmethod
    def extract_color(cls, text: str) -> Optional[str]:
        """Trích xuất và chuẩn hóa màu sắc từ tên sản phẩm."""
        if not text:
            return None
        t = text.lower()
        for kw, canonical in sorted(cls.COLOR_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if re.search(r"(?:\b|\s)" + re.escape(kw) + r"(?:\b|\s|$)", t):
                return canonical
        return None

    @classmethod
    def is_blacklisted_part(cls, part: str) -> bool:
        """Kiểm tra mã part có phải là tên linh kiện CPU/GPU/Màn hình hay không."""
        return any(p.search(part) for p in cls.PART_BLACKLIST_PATTERNS)

    @classmethod
    def extract_part_numbers(cls, text: str) -> List[str]:
        """Trích xuất danh sách Part-Number hợp lệ từ tên sản phẩm.
        Hỗ trợ:
        - Acer: A715-59G-57TU, AN515-58-52SP, ANV15-52-50VA
        - Asus: X1404VA-EB355W, FA506NCG-HN329W, UX3407QA-QD299WS
        - Lenovo: 83UQ003NVN, 83RQ002PVN, 83GS001RVN
        - MSI / HP / Dell: B13VEK-2440VN, v.v.
        Tự động lọc bỏ các mã linh kiện chip CPU, card GPU nhờ Blacklist.
        """
        if not text:
            return []
        p1 = re.findall(r"\b[A-Za-z0-9]{2,}-[A-Za-z0-9]{2,}(?:-[A-Za-z0-9]{2,})*\b", text)
        p2 = re.findall(r"\b8[0-9][A-Za-z0-9]{6,8}\b", text)
        parts = set(p1 + p2)

        valid_parts: Set[str] = set()
        for p in parts:
            p_upper = p.upper()
            if len(p_upper) >= 6 and any(c.isdigit() for c in p_upper):
                if not cls.is_blacklisted_part(p_upper):
                    valid_parts.add(p_upper)

        return list(valid_parts)

    @staticmethod
    def clean_product_name(text: str) -> str:
        """Làm sạch các từ ngữ marketing gây nhiễu."""
        if not text:
            return ""
        t = text.lower()
        t = re.sub(r"\|\s*chính hãng\s*(?:vn/a)?", "", t)
        t = re.sub(
            r"\b(điện thoại|laptop|máy tính xách tay|máy tính bảng|chính hãng|vn/a|đã kích hoạt|cũ đẹp|đổi trả|5g|4g|lte|mới 100%|new)\b",
            "",
            t
        )
        t = re.sub(r"[-–|/]", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    @staticmethod
    def extract_storage(text: str) -> List[str]:
        """Trích xuất danh sách dung lượng bộ nhớ trong ROM/SSD (VD: 128gb, 256gb, 512gb, 1tb, 2tb)."""
        if not text:
            return []
        found = []
        for m in re.finditer(r"\b(64|128|256|512)\s*gb\b", text, re.I):
            found.append(f"{m.group(1)}gb".lower())
        for m in re.finditer(r"\b(1|2)\s*tb\b", text, re.I):
            found.append(f"{m.group(1)}tb".lower())
        return list(set(found))

    @staticmethod
    def extract_ram(text: str) -> List[str]:
        """Trích xuất dung lượng RAM (VD: 4gb, 6gb, 8gb, 12gb, 16gb, 24gb, 32gb)."""
        if not text:
            return []
        found = [f"{m.group(1)}gb".lower() for m in re.finditer(r"\b(4|6|8|12|16|24|32)\s*gb\b", text, re.I)]
        return list(set(found))

    @classmethod
    def extract_model_identifier(cls, text: str) -> Optional[str]:
        """Trích xuất định danh model cốt lõi (Hard Model Constraint).
        Ngăn chặn việc ghép sai thế hệ hoặc sai dòng máy (VD: iPhone 18 vs iPhone 14, Z Fold8 vs S25).
        """
        if not text:
            return None
        t = text.lower()

        # 1. iPhone
        ip = re.search(r"\biphone\s*(\d+|se|x|xs|xr)\s*(pro\s*max|pro|plus|mini|e)?\b", t)
        if ip:
            gen = ip.group(1)
            sub = (ip.group(2) or "").replace(" ", "")
            return f"iphone_{gen}_{sub}"

        # 2. Samsung
        ss = re.search(r"\bgalaxy\s*(z\s*fold|z\s*flip|s|a|m)\s*(\d+)\s*(ultra|plus|fe|edge)?\b", t)
        if ss:
            series = ss.group(1).replace(" ", "")
            num = ss.group(2)
            sub = ss.group(3) or ""
            return f"samsung_{series}{num}_{sub}"

        # 3. Xiaomi / Redmi / Poco
        redmi = re.search(r"\b(?:xiaomi\s+)?(redmi\s*note\s*\d+[a-z]?|redmi\s*\d+[a-z]?|poco\s*[a-z0-9]+|xiaomi\s*\d+[a-z]?)\b", t)
        if redmi:
            return re.sub(r"\s+", "_", redmi.group(1).strip())

        # 4. Oppo
        oppo = re.search(r"\boppo\s*(find\s*[a-z0-9]+|reno\s*[a-z0-9]+|a\s*\d+[a-z]?)\s*(ultra|pro|plus|fe|s)?\b", t)
        if oppo:
            main = oppo.group(1).replace(" ", "_")
            sub = oppo.group(2) or ""
            return f"oppo_{main}_{sub}".rstrip("_")

        # 5. Tecno
        tecno = re.search(r"\btecno\s+(spark|pova|camon)\s*(\d+[a-z]?|\w+)?\b", t)
        if tecno:
            series = tecno.group(1).lower()
            num = (tecno.group(2) or "").lower()
            return f"tecno_{series}_{num}".rstrip("_")

        # 6. TCL
        tcl = re.search(r"\btcl\s*(\d+\s*se|\d+\s*e|\d+[a-z]?)\b", t)
        if tcl:
            m = re.sub(r"\s+", "_", tcl.group(1).strip())
            return f"tcl_{m}"

        # 7. Vivo
        vivo = re.search(r"\bvivo\s*(v\s*\d+[a-z]?|y\s*\d+[a-z]?|x\s*\d+[a-z]?|t\s*\d+[a-z]?)\b", t)
        if vivo:
            v_val = re.sub(r"\s+", "", vivo.group(1).lower())
            return f"vivo_{v_val}"

        # 8. Realme
        realme = re.search(r"\brealme\s*(c\s*\d+[a-z]?|note\s*\d+[a-z]?|\d+[a-z]?)\b", t)
        if realme:
            r_val = re.sub(r"\s+", "", realme.group(1).lower())
            return f"realme_{r_val}"

        # 9. Honor
        honor = re.search(r"\bhonor\s*(x\s*\d+[a-z]?|\d+[a-z]?)\b", t)
        if honor:
            h_val = re.sub(r"\s+", "", honor.group(1).lower())
            return f"honor_{h_val}"

        # 10. Laptop Series
        for line in cls.LAPTOP_LINES:
            if line in t:
                return line.replace(" ", "_")

        return None

    @classmethod
    def extract_features(cls, sku_id: str, sku_name: str) -> SkuFeatures:
        """Trích xuất toàn bộ đặc trưng chuẩn của một sản phẩm."""
        clean_name = cls.clean_product_name(sku_name)
        return SkuFeatures(
            sku_id=sku_id,
            sku_name=sku_name,
            clean_name=clean_name,
            brand=cls.detect_brand(sku_name),
            parts=cls.extract_part_numbers(sku_name),
            model_id=cls.extract_model_identifier(sku_name),
            ram=cls.extract_ram(clean_name),
            rom=cls.extract_storage(clean_name),
            color=cls.extract_color(sku_name),
        )
