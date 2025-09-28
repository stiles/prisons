"""
Prison data scrapers for different jurisdictions.
"""

from .federal import FederalScraper
from .california import CaliforniaScraper
from .new_york import NewYorkScraper
from .texas import TexasScraper
from .illinois import IllinoisScraper
from .florida import FloridaScraper

__all__ = ['FederalScraper', 'CaliforniaScraper', 'NewYorkScraper', 'TexasScraper', 'IllinoisScraper', 'FloridaScraper']
