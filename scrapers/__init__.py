"""
Prison data scrapers for different jurisdictions.
"""

from .federal import FederalScraper
from .california import CaliforniaScraper
from .new_york import NewYorkScraper
from .texas import TexasScraper
from .illinois import IllinoisScraper
from .florida import FloridaScraper
from .pennsylvania import PennsylvaniaScraper
from .georgia import GeorgiaScraper
from .north_carolina import NorthCarolinaScraper
from .michigan import MichiganScraper

__all__ = ['FederalScraper', 'CaliforniaScraper', 'NewYorkScraper', 'TexasScraper', 'IllinoisScraper', 'FloridaScraper', 'PennsylvaniaScraper', 'GeorgiaScraper', 'NorthCarolinaScraper', 'MichiganScraper']
