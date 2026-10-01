"""Crawl CellphoneS catalogs and match their offers to the local SKU workbook.

Run from the repository root with::

    python -m backend.scripts.match_cellphones_to_dim_product

High-precision multi-tier matching aligns local SKUs against CellphoneS offerings
using manufacturer part-numbers, exact model codes, specification matching, and
similarity heuristics.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Ensure immediate unbuffered output for terminal and log viewers
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from backend.app.scrapers.cellphones import (
    CellphoneSScraper,
    CrawlConfig,
    CrawlError,
    CrawlReport,
    ScrapedProduct,
)


PART_NUMBER_RE = re.compile(
    r"(?<![a-z0-9])([a-z0-9]+(?:-[a-z0-9]+){1,3})(?![a-z0-9])",
    re.I,
)
PAREN_CODE_RE = re.compile(r"\(([a-z0-9]{6,10})\)", re.I)
MODEL_CODE_RE = re.compile(r"\b([a-z]{1,3}\d{4,6}[a-z0-9]*)\b", re.I)
LONG_PART_NUMBER_RE = re.compile(r"(?<![a-z0-9])([a-z0-9]{8,})(?![a-z0-9])", re.I)
STORAGE_RE = re.compile(r"\b(32gb|64gb|128gb|256gb|512gb|1tb|2tb)\b", re.I)
RAM_RE = re.compile(r"\b([3468]|12|16|24|32|48)\s*gb\b", re.I)
WORD_RE = re.compile(r"[a-z0-9]+")
USED_PRODUCT_RE = re.compile(
    r"da kich hoat|hang cu|doi tra|cu xuoc can|cu tray xuoc|hang trung bay|refurbished|cu dep|da qua su dung",
    re.I,
)
LOW_INFORMATION_TOKENS = {
    "dien",
    "thoai",
    "may",
    "tinh",
    "laptop",
    "smartphone",
    "san",
    "pham",
    "chinh",
    "hang",
    "the",
    "he",
    "moi",
    "vn",
    "vna",
}

KNOWN_BRANDS = (
    "acer",
    "asus",
    "apple",
    "macbook",
    "iphone",
    "dell",
    "hp",
    "lenovo",
    "msi",
    "samsung",
    "xiaomi",
    "oppo",
    "vivo",
    "realme",
    "honor",
    "tecno",
    "nubia",
    "itel",
    "masstel",
    "nokia",
    "mobell",
    "viettel",
)


@dataclass(frozen=True, slots=True)
class InputSku:
    sku_id: str
    sku_name: str
    category: str
    brand: str


@dataclass(frozen=True, slots=True)
class MatchResult:
    sku: InputSku
    product: ScrapedProduct | None
    match_status: str
    similarity_score: int | None
    reason: str


@dataclass(slots=True)
class IndexedProduct:
    product: ScrapedProduct
    norm: str
    compact_norm: str
    part_numbers: set[str]
    brand: str
    storages: set[str]
    modifiers: list[str]
    tokens: set[str]


def normalise_text(value: str) -> str:
    value = value.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text.casefold()).strip()


def detect_brand(text: str) -> str:
    norm = normalise_text(text)
    for b in KNOWN_BRANDS:
        if b in norm:
            if b in ("macbook", "iphone"):
                return "apple"
            return b
    return "other"


def load_skus(path: Path, sheet_name: str = "dim_product") -> list[InputSku]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet_name not in workbook.sheetnames:
            available = ", ".join(workbook.sheetnames)
            raise ValueError(f"Sheet '{sheet_name}' not found in {path}; available: {available}")
        sheet = workbook[sheet_name]
        header_values = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), ())
        headers = {
            str(value).strip().casefold(): index
            for index, value in enumerate(header_values)
            if value is not None
        }
        missing = [name for name in ("sku_id", "sku_name") if name not in headers]
        if missing:
            raise ValueError(f"Missing required column(s) in {sheet_name}: {', '.join(missing)}")

        rows: list[InputSku] = []
        seen_ids: set[str] = set()
        for row_number, values in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            sku_id_value = values[headers["sku_id"]] if headers["sku_id"] < len(values) else None
            sku_name_value = values[headers["sku_name"]] if headers["sku_name"] < len(values) else None
            if sku_id_value is None and sku_name_value is None:
                continue
            if sku_id_value is None or sku_name_value is None:
                raise ValueError(f"Incomplete SKU row at {sheet_name}!{row_number}")

            sku_id = str(sku_id_value).strip()
            sku_name = str(sku_name_value).strip()
            if not sku_id or not sku_name:
                raise ValueError(f"Blank SKU ID or name at {sheet_name}!{row_number}")
            if sku_id in seen_ids:
                raise ValueError(f"Duplicate sku_id '{sku_id}' at {sheet_name}!{row_number}")
            seen_ids.add(sku_id)
            normalized_name = normalise_text(sku_name)
            category = "laptop" if re.search(r"\b(laptop|macbook)\b", normalized_name) else "mobile"
            brand = detect_brand(sku_name)
            rows.append(InputSku(sku_id=sku_id, sku_name=sku_name, category=category, brand=brand))
        return rows
    finally:
        workbook.close()


def part_numbers(value: str) -> set[str]:
    normalized = normalise_text(value)
    found: set[str] = set()
    for match in PART_NUMBER_RE.finditer(normalized):
        code = match.group(1)
        segments = code.split("-")
        if (code.count("-") >= 2 and len(re.sub(r"[^a-z0-9]", "", code)) >= 8) or (
            len(segments) == 2 and min(map(len, segments)) >= 5
        ):
            found.add(re.sub(r"[^a-z0-9]", "", code))
    for match in PAREN_CODE_RE.finditer(normalized):
        found.add(re.sub(r"[^a-z0-9]", "", match.group(1)))
    for match in MODEL_CODE_RE.finditer(normalized):
        code = match.group(1)
        if any(char.isdigit() for char in code) and any(char.isalpha() for char in code):
            found.add(re.sub(r"[^a-z0-9]", "", code))
    for match in LONG_PART_NUMBER_RE.finditer(normalized):
        code = match.group(1)
        if re.search(r"[a-z]", code) and re.search(r"\d", code):
            found.add(re.sub(r"[^a-z0-9]", "", code))
    return found


def extract_modifiers(text: str) -> list[str]:
    mods = []
    if "pro max" in text:
        mods.append("pro max")
    elif "pro" in text:
        mods.append("pro")
    if "plus" in text:
        mods.append("plus")
    if "ultra" in text:
        mods.append("ultra")
    if "lite" in text:
        mods.append("lite")
    if "fe" in text:
        mods.append("fe")
    if "16e" in text:
        mods.append("16e")
    if "17e" in text:
        mods.append("17e")
    return mods


def _is_comparable_product(product: ScrapedProduct) -> bool:
    cond = product.attributes.get("product_condition") if product.attributes else None
    if cond and cond != "Mới":
        return False
    return not USED_PRODUCT_RE.search(normalise_text(f"{product.name} {product.product_url}"))


def index_products(products: list[ScrapedProduct]) -> list[IndexedProduct]:
    """Pre-index product metadata once to make matching instant."""
    indexed = []
    for p in products:
        if not _is_comparable_product(p):
            continue
        norm = normalise_text(f"{p.name} {p.product_url}")
        compact = re.sub(r"[^a-z0-9]", "", norm)
        codes = part_numbers(f"{p.name} {p.product_url}")
        attrs_pn = p.part_number or (p.attributes.get("laptop_part_number") if p.attributes else None)
        if attrs_pn:
            codes.add(re.sub(r"[^a-z0-9]", "", normalise_text(str(attrs_pn))))

        brand = detect_brand(norm)
        storages = set(STORAGE_RE.findall(norm))
        mods = extract_modifiers(norm)
        tokens = {t for t in WORD_RE.findall(norm) if len(t) > 1 and t not in LOW_INFORMATION_TOKENS}

        indexed.append(
            IndexedProduct(
                product=p,
                norm=norm,
                compact_norm=compact,
                part_numbers=codes,
                brand=brand,
                storages=storages,
                modifiers=mods,
                tokens=tokens,
            )
        )
    return indexed


def match_laptop(sku: InputSku, indexed_candidates: list[IndexedProduct]) -> MatchResult:
    sku_norm = normalise_text(sku.sku_name)
    input_codes = part_numbers(sku.sku_name)

    # 1. Exact Part-Number matching
    if input_codes:
        exact = [
            ip.product
            for ip in indexed_candidates
            if input_codes & ip.part_numbers or any(code in ip.compact_norm for code in input_codes)
        ]
        if len(exact) == 1:
            return MatchResult(
                sku,
                exact[0],
                "exact_part_number",
                100,
                "Exact manufacturer part-number matched in CellphoneS listing or specs.",
            )
        if len(exact) > 1:
            # Pick best match
            sku_tokens = {t for t in WORD_RE.findall(sku_norm) if len(t) > 1 and t not in LOW_INFORMATION_TOKENS}
            best_p = max(exact, key=lambda p: len(sku_tokens & {t for t in WORD_RE.findall(normalise_text(p.name))}))
            return MatchResult(
                sku,
                best_p,
                "exact_part_number",
                100,
                f"Exact part-number matched across {len(exact)} listings; best candidate selected.",
            )

    # 2. MacBook specific spec matching
    if "macbook" in sku_norm:
        sku_storages = set(STORAGE_RE.findall(sku_norm))
        sku_rams = set(r.replace(" ", "") for r in RAM_RE.findall(sku_norm))
        for ip in indexed_candidates:
            if "macbook" not in ip.norm:
                continue
            # Chip series
            chip_ok = True
            for chip in ("m4 pro", "m4 max", "m3 max", "m3 pro", "m5", "m4", "m3"):
                if chip in sku_norm:
                    chip_ok = chip in ip.norm
                    break
            if not chip_ok:
                continue
            # Screen size
            screen_ok = True
            for screen in ("13 inch", "14 inch", "15 inch", "16 inch", "13", "14", "15", "16"):
                if screen in sku_norm:
                    screen_ok = screen in ip.norm
                    break
            if not screen_ok:
                continue
            p_rams = set(r.replace(" ", "") for r in RAM_RE.findall(ip.norm))
            if sku_storages == ip.storages and (not sku_rams or sku_rams == p_rams):
                return MatchResult(
                    sku,
                    ip.product,
                    "spec_match",
                    95,
                    "MacBook chip generation, screen size, RAM, and storage matched.",
                )

    # 3. High-confidence Token Fallback
    sku_tokens = {t for t in WORD_RE.findall(sku_norm) if len(t) > 1 and t not in LOW_INFORMATION_TOKENS}
    scored = []
    for ip in indexed_candidates:
        common = sku_tokens & ip.tokens
        if len(common) >= 3:
            score = round(100 * (2 * len(common)) / (len(sku_tokens) + len(ip.tokens)))
            if score >= 45:
                scored.append((score, ip.product))
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return MatchResult(
            sku,
            scored[0][1],
            "review",
            scored[0][0],
            "High token similarity candidate; review model configuration manually.",
        )

    return MatchResult(
        sku,
        None,
        "unmatched",
        None,
        "No matching model or part-number found in CellphoneS catalog.",
    )


def match_mobile(sku: InputSku, indexed_candidates: list[IndexedProduct]) -> MatchResult:
    sku_norm = normalise_text(sku.sku_name)
    sku_brand = sku.brand

    sku_storages = STORAGE_RE.findall(sku_norm)
    sku_storage = sku_storages[-1] if sku_storages else None
    sku_mods = extract_modifiers(sku_norm)

    filtered_candidates: list[IndexedProduct] = []
    for ip in indexed_candidates:
        if sku_brand != "other" and sku_brand != ip.brand:
            continue
        if sku_storage and sku_storage not in ip.storages:
            continue

        # Strict modifier alignment
        if "pro max" in sku_mods and "pro max" not in ip.modifiers:
            continue
        if "pro" in sku_mods and "pro max" not in sku_mods and ("pro" not in ip.modifiers or "pro max" in ip.modifiers):
            continue
        if "plus" in sku_mods and "plus" not in ip.modifiers:
            continue
        if "ultra" in sku_mods and "ultra" not in ip.modifiers:
            continue
        if "lite" in sku_mods and "lite" not in ip.modifiers:
            continue
        if "fe" in sku_mods and "fe" not in ip.modifiers:
            continue
        if not sku_mods and ip.modifiers:
            continue

        filtered_candidates.append(ip)

    if not filtered_candidates:
        return MatchResult(
            sku,
            None,
            "unmatched",
            None,
            "No active CellphoneS listing matching the specific model and storage tier.",
        )

    clean_sku = re.sub(r"\b(4g|5g|chinh hang|vn/a|nfc|dien thoai|smartphone)\b", "", sku_norm)
    tokens = [w for w in clean_sku.split() if len(w) > 1 and w not in LOW_INFORMATION_TOKENS]

    scored = []
    for ip in filtered_candidates:
        score = sum(1 for t in tokens if t in ip.norm)
        scored.append((score, ip.product))
    scored.sort(key=lambda item: item[0], reverse=True)

    if scored and scored[0][0] >= max(len(tokens) - 1, 2):
        best_product = scored[0][1]
        best_score = scored[0][0]
        status = "exact_part_number" if best_score == len(tokens) or len(scored) == 1 else "spec_match"
        sim_val = round(100 * (best_score / len(tokens))) if tokens else 100
        return MatchResult(
            sku,
            best_product,
            status,
            sim_val,
            f"Brand, model line, and storage capacity ({sku_storage or 'base'}) matched exactly.",
        )

    return MatchResult(
        sku,
        None,
        "unmatched",
        None,
        "No sufficiently matching variant found for this mobile phone SKU.",
    )


def match_sku(sku: InputSku, indexed_candidates: list[IndexedProduct]) -> MatchResult:
    if sku.category == "laptop":
        return match_laptop(sku, indexed_candidates)
    return match_mobile(sku, indexed_candidates)


def normalize_stock_status(raw_status: str | None) -> str:
    status = normalise_text(raw_status or "")
    if not status:
        return "unknown"
    if re.search(r"sap ve hang|dat truoc|tam het|het hang|out of stock|sold out", status):
        return "out_of_stock"
    if re.search(r"con hang|san hang|available", status):
        return "in_stock"
    return "unknown"


def _product_row(result: MatchResult) -> list[object]:
    product = result.product
    price = product.price_vnd if product else None
    orig_price = product.original_price_vnd if product else None
    discount_pct = (
        round((orig_price - price) / orig_price * 100, 1)
        if price and orig_price and orig_price > price
        else None
    )
    return [
        result.sku.sku_id,
        result.sku.sku_name,
        result.sku.category,
        result.sku.brand.upper(),
        product.name if product else None,
        product.product_url if product else None,
        price,
        orig_price,
        discount_pct,
        normalize_stock_status(product.raw_status) if product else "unknown",
        result.match_status,
        result.similarity_score,
        result.reason,
        product.crawled_at.isoformat() if product else None,
    ]


def _format_sheet(sheet, headers: list[str], rows: list[list[object]]) -> None:
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    thin_border = Border(
        left=Side(style="thin", color="E0E0E0"),
        right=Side(style="thin", color="E0E0E0"),
        top=Side(style="thin", color="E0E0E0"),
        bottom=Side(style="thin", color="E0E0E0"),
    )

    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = PatternFill("solid", fgColor="1B365D")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    sheet.row_dimensions[1].height = 28

    for column_index, header in enumerate(headers, start=1):
        values = [str(sheet.cell(row, column_index).value or "") for row in range(1, min(sheet.max_row, 100) + 1)]
        width = min(max(max(map(len, values), default=0) + 3, 12), 65)
        sheet.column_dimensions[get_column_letter(column_index)].width = width

    for row_index in range(2, sheet.max_row + 1):
        for column_index, header in enumerate(headers, start=1):
            cell = sheet.cell(row_index, column_index)
            cell.border = thin_border
            if header.endswith("price_vnd"):
                cell.number_format = '#,##0 "₫"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif header.endswith("pct"):
                cell.number_format = '0.0"%"'
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif header in ("sku_id", "category", "brand", "match_status", "stock_status"):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(vertical="center", wrap_text=True)


def write_output(
    output_path: Path,
    results: list[MatchResult],
    reports: dict[str, CrawlReport],
) -> None:
    workbook = Workbook()

    # 1. Matches Sheet
    matches = workbook.active
    matches.title = "Matches"
    match_headers = [
        "sku_id",
        "sku_name",
        "category",
        "brand",
        "cellphones_name",
        "cellphones_url",
        "price_vnd",
        "original_price_vnd",
        "discount_pct",
        "stock_status",
        "match_status",
        "similarity_score",
        "match_reason",
        "crawled_at",
    ]
    _format_sheet(matches, match_headers, [_product_row(result) for result in results])

    # 2. CellphoneS_Data Sheet
    raw_sheet = workbook.create_sheet("CellphoneS_Data")
    raw_headers = [
        "name",
        "category",
        "brand",
        "price_vnd",
        "original_price_vnd",
        "discount_pct",
        "stock_status",
        "part_number",
        "product_url",
        "crawled_at",
    ]
    raw_rows = []
    seen_urls: set[str] = set()
    for cat, report in reports.items():
        for p in report.products:
            if p.product_url in seen_urls:
                continue
            seen_urls.add(p.product_url)
            price = p.price_vnd
            orig_price = p.original_price_vnd
            discount_pct = (
                round((orig_price - price) / orig_price * 100, 1)
                if price and orig_price and orig_price > price
                else None
            )
            brand = (p.manufacturer or detect_brand(p.name)).upper()
            raw_rows.append([
                p.name,
                cat,
                brand,
                price,
                orig_price,
                discount_pct,
                normalize_stock_status(p.raw_status),
                p.part_number,
                p.product_url,
                p.crawled_at.isoformat() if p.crawled_at else None,
            ])
    _format_sheet(raw_sheet, raw_headers, raw_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)


async def run(args: argparse.Namespace) -> int:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve() if args.output else (
        input_path.parent / f"cellphones_dim_product_matches_{datetime.now().astimezone():%Y%m%d_%H%M%S}.xlsx"
    )
    if input_path == output_path:
        raise ValueError("Output path must differ from the input workbook path")

    skus = load_skus(input_path, sheet_name=args.sheet)
    if not skus:
        raise ValueError(f"No SKU rows found in {input_path} / {args.sheet}")

    skus_by_category: dict[str, list[InputSku]] = defaultdict(list)
    for sku in skus:
        skus_by_category[sku.category].append(sku)

    reports: dict[str, CrawlReport] = {}
    errors: dict[str, str] = {}

    for category in ("mobile", "laptop"):
        if not skus_by_category.get(category):
            continue

        config = CrawlConfig(
            category=category,
            max_products=args.max_products_per_category,
        )
        print(f"Crawling CellphoneS {category} catalog live via GraphQL...")
        try:
            reports[category] = await CellphoneSScraper(config).scrape()
            print(f"-> Successfully collected {len(reports[category].products)} {category} offers.")
        except CrawlError as exc:
            errors[category] = str(exc)
            print(f"-> {category} crawl failed: {exc}")

    # Pre-index candidates for lightning-fast matching
    print("Pre-indexing crawled offerings for multi-tier matching...")
    indexed_by_category = {
        category: index_products(list(report.products))
        for category, report in reports.items()
    }

    print(f"Matching {len(skus)} SKUs against CellphoneS inventory...")
    matches = [
        match_sku(sku, indexed_by_category.get(sku.category, []))
        for sku in skus
    ]

    write_output(
        output_path,
        matches,
        reports,
    )

    counts: dict[str, int] = defaultdict(int)
    for result in matches:
        counts[result.match_status] += 1

    print("\n" + "=" * 65)
    print(f"[OK] Matching Completed! Saved {len(matches)} SKU rows to:")
    print(f"     {output_path.absolute()}")
    print("=" * 65)
    print(f"[*] Total SKUs: {len(matches)}")
    print(f"    - Exact Matches (Part-Number/Model): {counts['exact_part_number']} ({counts['exact_part_number']/len(matches)*100:.1f}%)")
    print(f"    - Spec Matches (Chip/Storage/RAM):  {counts['spec_match']} ({counts['spec_match']/len(matches)*100:.1f}%)")
    print(f"    - Review Matches (Fuzzy token):      {counts['review']} ({counts['review']/len(matches)*100:.1f}%)")
    print(f"    - Unmatched (Not on CellphoneS):     {counts['unmatched']} ({counts['unmatched']/len(matches)*100:.1f}%)")
    matched_total = len(matches) - counts['unmatched']
    print(f"[+] Overall Coverage Rate: {matched_total/len(matches)*100:.1f}% ({matched_total}/{len(matches)} SKUs)")
    print("=" * 65 + "\n")

    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Match dim_product SKUs to CellphoneS phone/laptop listings and save an Excel snapshot."
    )
    parser.add_argument("--input", default="data/dim_product.xlsx", help="Input workbook path")
    parser.add_argument("--sheet", default="dim_product", help="Input worksheet name")
    parser.add_argument("--output", help="Output workbook path; defaults to timestamped file in data/")
    parser.add_argument("--max-products-per-category", type=int, default=4000)
    args = parser.parse_args()

    if args.max_products_per_category < 1:
        parser.error("product limit must be positive")

    try:
        raise SystemExit(asyncio.run(run(args)))
    except (CrawlError, OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
