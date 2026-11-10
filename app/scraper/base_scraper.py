# app/scraper/base_scraper.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, target_niche: str, max_results: int, **kwargs) -> List[Dict[str, str]]:
        pass
