"""
Web scrapers for the quant-estate project.
"""

from .immobiliare.scraper_ids import ImmobiliareIdScraper
from .immobiliare.scraper_listing import ImmobiliareListingScraper
from .selenium_scraper import SeleniumScraper

__all__ = ["SeleniumScraper", "ImmobiliareIdScraper", "ImmobiliareListingScraper"]
