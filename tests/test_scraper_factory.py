import pytest
from app.services.scrapers.factory import ScraperFactory
from app.services.scrapers.cellphones import CellphonesScraper
from app.services.scrapers.hoangha import HoanghaScraper


def test_scraper_factory_returns_cellphones():
    scraper = ScraperFactory.get_scraper("cellphones")
    assert isinstance(scraper, CellphonesScraper)
    assert scraper.source_name == "CELLPHONES"


def test_scraper_factory_returns_hoangha():
    scraper = ScraperFactory.get_scraper("hoangha")
    assert isinstance(scraper, HoanghaScraper)
    assert scraper.source_name == "HOANGHA"


def test_scraper_factory_raises_value_error_for_unknown_source():
    with pytest.raises(ValueError, match="chưa được hỗ trợ"):
        ScraperFactory.get_scraper("unknown_source")
