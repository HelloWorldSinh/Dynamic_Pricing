"""CellphoneS catalog scraper using official GraphQL API.

This module provides high-speed, direct catalog data collection for smartphones
and laptops from CellphoneS to feed into the dynamic pricing matching engine.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Protocol, Sequence

GRAPHQL_URL = "https://api.cellphones.com.vn/v2/graphql/query"
GRAPHQL_CATEGORIES = {
    "mobile": "3",
    "laptop": "380",
}

DEFAULT_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
)

USED_PRODUCT_RE = re.compile(
    r"da kich hoat|hang cu|doi tra|cu xuoc|cu tray|trung bay|refurbished|cu dep|da qua su dung",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ScrapedProduct:
    source: str
    name: str
    product_url: str
    price_vnd: int | None
    original_price_vnd: int | None
    raw_status: str | None
    crawled_at: datetime
    manufacturer: str | None = None
    part_number: str | None = None
    attributes: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CrawlConfig:
    category: str = "mobile"
    min_delay_seconds: float = 0.05
    max_delay_seconds: float = 0.2
    max_retries: int = 2
    max_products: int = 4000
    timeout_seconds: float = 15.0
    user_agents: tuple[str, ...] = DEFAULT_USER_AGENTS

    def __post_init__(self) -> None:
        if self.category not in GRAPHQL_CATEGORIES:
            raise ValueError(f"Category '{self.category}' must be one of: {list(GRAPHQL_CATEGORIES.keys())}")
        if self.min_delay_seconds < 0 or self.max_delay_seconds < self.min_delay_seconds:
            raise ValueError("Delay range must be non-negative and properly ordered")
        if self.max_retries < 0 or self.max_products < 1:
            raise ValueError("Retry and product limits must be valid")
        if not self.user_agents or any(not value.strip() for value in self.user_agents):
            raise ValueError("At least one non-empty User-Agent is required")


@dataclass(frozen=True, slots=True)
class CrawlReport:
    source: str
    crawled_at: datetime
    products: tuple[ScrapedProduct, ...]
    discovered_count: int
    rejected_count: int
    pages_crawled: int
    failed_urls: tuple[str, ...]
    truncated: bool
    truncation_reason: str | None

    @property
    def parsed_count(self) -> int:
        return len(self.products)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "crawled_at": self.crawled_at.isoformat(),
            "discovered_count": self.discovered_count,
            "parsed_count": self.parsed_count,
            "rejected_count": self.rejected_count,
            "pages_crawled": self.pages_crawled,
            "failed_urls": list(self.failed_urls),
            "truncated": self.truncated,
            "truncation_reason": self.truncation_reason,
            "products": [
                {
                    **asdict(product),
                    "crawled_at": product.crawled_at.isoformat(),
                }
                for product in self.products
            ],
        }


class AppendOnlyCrawlResultSink(Protocol):
    async def append_products(self, products: Sequence[ScrapedProduct]) -> None: ...


class CrawlError(RuntimeError):
    """Base exception for a failed CellphoneS crawl."""


class CellphoneSScraper:
    """High-performance async scraper for CellphoneS catalog via GraphQL API."""

    def __init__(
        self,
        config: CrawlConfig | None = None,
        *,
        sleeper=asyncio.sleep,
        rng: random.Random | None = None,
    ) -> None:
        self.config = config or CrawlConfig()
        self._sleep = sleeper
        self._rng = rng or random.Random()

    def _query_graphql_sync(self, query: str, user_agent: str) -> dict:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": user_agent,
        }
        req = urllib.request.Request(
            GRAPHQL_URL,
            data=json.dumps({"query": query}).encode("utf-8"),
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    async def scrape(self, sink: AppendOnlyCrawlResultSink | None = None) -> CrawlReport:
        captured_at = datetime.now(timezone.utc)
        cate_id = GRAPHQL_CATEGORIES.get(self.config.category, "3")
        products: dict[str, ScrapedProduct] = {}
        user_agent = self._rng.choice(self.config.user_agents)
        page = 1
        size = 100
        truncated = False
        truncation_reason: str | None = None
        failed_urls: list[str] = []
        rejected_count = 0

        while len(products) < self.config.max_products:
            query = f"""
            query {{
              products(
                filter: {{
                  static: {{
                    categories: ["{cate_id}"],
                    province_id: 30,
                    stock: {{ from: 0 }}
                  }}
                }},
                page: {page},
                size: {size},
                sort: [{{ view: desc }}]
              ) {{
                general {{
                  product_id
                  name
                  attributes
                  url_path
                  manufacturer
                }}
                filterable {{
                  price
                  special_price
                  stock
                }}
              }}
            }}
            """
            data = None
            for attempt in range(self.config.max_retries + 1):
                try:
                    data = await asyncio.to_thread(self._query_graphql_sync, query, user_agent)
                    break
                except Exception as exc:
                    if attempt >= self.config.max_retries:
                        failed_urls.append(GRAPHQL_URL)
                        raise CrawlError(f"CellphoneS GraphQL error after {attempt + 1} attempts: {exc}") from exc
                    await self._sleep(max(self.config.min_delay_seconds, 2**attempt))

            items = data.get("data", {}).get("products") if data else None
            if not items:
                break

            for item in items:
                gen = item.get("general", {})
                filt = item.get("filterable", {})
                attrs = gen.get("attributes", {})
                name = (gen.get("name") or "").strip()
                url_path = (gen.get("url_path") or "").strip()
                if not name or not url_path:
                    rejected_count += 1
                    continue

                product_url = f"https://cellphones.com.vn/{url_path}"
                norm_full = f"{name} {url_path}".lower()

                # Filter out used/clearance products
                cond = attrs.get("product_condition")
                if cond and cond != "Mới":
                    rejected_count += 1
                    continue
                if USED_PRODUCT_RE.search(norm_full):
                    rejected_count += 1
                    continue

                price = filt.get("special_price") or filt.get("price")
                orig_price = filt.get("price")
                stock = filt.get("stock", 0)
                raw_status = "Còn hàng" if stock and stock > 0 else "Hết hàng"

                prod = ScrapedProduct(
                    source="CellphoneS",
                    name=name,
                    product_url=product_url,
                    price_vnd=int(price) if price else None,
                    original_price_vnd=int(orig_price) if orig_price and int(orig_price) > (int(price) if price else 0) else None,
                    raw_status=raw_status,
                    crawled_at=captured_at,
                    manufacturer=gen.get("manufacturer") or attrs.get("manufacturer"),
                    part_number=attrs.get("laptop_part_number"),
                    attributes=attrs,
                )
                products.setdefault(product_url, prod)
                if len(products) >= self.config.max_products:
                    truncated = True
                    truncation_reason = "max_products reached"
                    break

            if len(items) < size or truncated:
                break
            page += 1
            await self._sleep(self._rng.uniform(self.config.min_delay_seconds, self.config.max_delay_seconds))

        report = CrawlReport(
            source="CellphoneS",
            crawled_at=captured_at,
            products=tuple(products.values()),
            discovered_count=len(products),
            rejected_count=rejected_count,
            pages_crawled=page - 1,
            failed_urls=tuple(dict.fromkeys(failed_urls)),
            truncated=truncated,
            truncation_reason=truncation_reason,
        )
        if sink is not None and report.products:
            await sink.append_products(report.products)
        return report


async def _main(args: argparse.Namespace) -> int:
    config = CrawlConfig(
        category=args.category,
        max_products=args.max_products,
    )
    try:
        report = await CellphoneSScraper(config).scrape()
    except CrawlError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 1 if report.failed_urls else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Crawl CellphoneS products via GraphQL API")
    parser.add_argument("--category", choices=["mobile", "laptop"], default="mobile", help="Category to crawl")
    parser.add_argument("--max-products", type=int, default=4000)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main(args)))


if __name__ == "__main__":
    main()
