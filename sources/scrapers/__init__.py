"""
Web scrapers for the quant-estate project.
"""

from .selenium_scraper import SeleniumScraper
from .immobiliare.scraper_ids import ImmobiliareIdScraper
from .immobiliare.scraper_listing import ImmobiliareListingScraper

__all__ = ["SeleniumScraper", "ImmobiliareIdScraper", "ImmobiliareListingScraper"]
