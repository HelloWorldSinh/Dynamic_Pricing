from typing import Dict
from app.services.scrapers.base import BaseScraper
from app.services.scrapers.cellphones import CellphonesScraper
from app.services.scrapers.hoangha import HoanghaScraper
from app.services.scrapers.fpt import FptShopScraper
from app.schemas.crawl import SourceEnum


class ScraperFactory:
    """Factory để tạo và quản lý các scraper theo nguồn (Strategy Pattern)."""
    _scrapers: Dict[str, BaseScraper] = {
        SourceEnum.CELLPHONES.value: CellphonesScraper(),
        SourceEnum.HOANGHA.value: HoanghaScraper(),
        SourceEnum.FPTSHOP.value: FptShopScraper(),
    }

    @classmethod
    def get_scraper(cls, source: str) -> BaseScraper:
        source_key = source.lower()
        if source_key in cls._scrapers:
            return cls._scrapers[source_key]
        raise ValueError(
            f"Nguồn cào '{source}' chưa được hỗ trợ. Các nguồn khả dụng: {list(cls._scrapers.keys())}"
        )

    @classmethod
    def register_scraper(cls, source: str, scraper: BaseScraper):
        cls._scrapers[source.lower()] = scraper
