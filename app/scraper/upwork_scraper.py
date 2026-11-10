# app/scraper/upwork_scraper.py
import urllib.parse
from typing import List, Dict
import feedparser
from .base_scraper import BaseScraper

class UpworkScraper(BaseScraper):
    async def scrape(self, target_niche: str, max_results: int, **kwargs) -> List[Dict[str, str]]:
        """
        Scrapes job postings from Upwork's public RSS feed.
        
        Inputs:
            target_niche (str): Interpreted here as the search query keyword (e.g., 'data entry', 'accounting')
            max_results (int): Max number of jobs to fetch
        """
        extracted_data = []
        
        # 1. Safely URL-encode the niche keyword parameter (e.g., converts 'data entry' to 'data%20entry')
        encoded_query = urllib.parse.quote(target_niche)
        
        # 2. Construct the public Upwork RSS Atom feed search URL
        rss_url = f"https://upwork.com{encoded_query}&sort=recency"
        
        try:
            # 3. Ingest and parse the XML layout payload 
            # (Runs fast via network stream, no headless browser overhead needed here)
            feed = feedparser.parse(rss_url)
            
            # Check if feed parsed correctly or returned empty results
            if not feed.entries:
                print(f"[UpworkScraper] No job postings found or feed restricted for query: '{target_niche}'")
                return extracted_data

            # 4. Map the entries to our strict output contract schema
            for entry in feed.entries[:max_results]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "")
                
                # Upwork includes payment details & descriptions inside the summary element
                summary = getattr(entry, "summary", "").strip()
                
                # Bundle text information together for holistic semantic pattern parsing
                full_text = f"Job Title: {title}\nJob Details & Requirements:\n{summary}"
                
                extracted_data.append({
                    "url": link,
                    "text": full_text
                })
                
        except Exception as e:
            print(f"[UpworkScraper Error] Failed to process feed: {e}")
            
        return extracted_data
