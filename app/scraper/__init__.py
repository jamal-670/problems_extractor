# app/scraper/__init__.py
from .base_scraper import BaseScraper
from .reddit_scraper import RedditScraper
from .upwork_scraper import UpworkScraper
from .g2_scraper import G2Scraper
from .fix_my_itch_scraper import RazorpayScraper
from .yc_scraper import YCScraper
from .loopdrop_scraper import LootDropScraper

__all__ = [
    "BaseScraper", 
    "RedditScraper", 
    "UpworkScraper", 
    "G2Scraper", 
    "RazorpayScraper", 
    "YCScraper",
    "LootDropScraper"
]
