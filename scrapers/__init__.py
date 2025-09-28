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
from .virginia import VirginiaScraper
from .washington import WashingtonScraper
from .arizona import ArizonaScraper
from .tennessee import TennesseeScraper
from .massachusetts import MassachusettsScraper
from .indiana import IndianaScraper

__all__ = ['FederalScraper', 'CaliforniaScraper', 'NewYorkScraper', 'TexasScraper', 'IllinoisScraper', 'FloridaScraper', 'PennsylvaniaScraper', 'GeorgiaScraper', 'NorthCarolinaScraper', 'MichiganScraper', 'VirginiaScraper', 'WashingtonScraper', 'ArizonaScraper', 'TennesseeScraper', 'MassachusettsScraper', 'IndianaScraper']
