"""
Web scrapers for the quant-estate project.
"""

from .selenium_scraper import SeleniumScraper
from .immobiliare.listing_scraper import ImmobiliareSeleniumScraper

__all__ = ["SeleniumScraper", "ImmobiliareSeleniumScraper"]
