"""
Web scrapers for the quant-estate project.
"""

from .selenium_scraper import SeleniumScraper
from .immobiliare.scraper_ids import ImmobiliareIdScraper

__all__ = ["SeleniumScraper", "ImmobiliareIdScraper"]
