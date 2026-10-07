from abc import ABC, abstractmethod
from typing import Optional, List, Any
from app.schemas.crawl import ScrapedProductItem


class BaseScraper(ABC):
    """Abstract Base Class cho tất cả Scraper (Strategy Pattern).
    Cung cấp interface chuẩn mực, che giấu toàn bộ logic cào chi tiết bên trong.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Tên nguồn cào: FPTSHOP, CELLPHONES, HOANGHA."""
        pass

    @abstractmethod
    def scrape_product(self, url: str) -> Optional[ScrapedProductItem]:
        """Cào thông tin chi tiết một sản phẩm từ URL."""
        pass

    @abstractmethod
    def scrape_category(
        self,
        category: str,
        limit: Optional[int] = None,
        on_progress: Optional[Any] = None,
    ) -> List[ScrapedProductItem]:
        """Cào danh sách sản phẩm theo ngành hàng (phone/laptop). Nếu limit=None hoặc <= 0, cào toàn bộ các trang từ đầu đến cuối.
        on_progress(current_page, total_pages, scraped_count, message): callback thông báo tiến độ.
        """
        pass
