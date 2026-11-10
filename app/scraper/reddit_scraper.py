# app/scraper/reddit_scraper.py
import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class RedditScraper(BaseScraper):
    async def scrape(self, target_niche: str, max_results: int) -> List[Dict[str, str]]:
        # Target the 'new' feed of the specified niche subreddit
        url = f"https://reddit.com{target_niche}/new/"
        extracted_data = []

        async with async_playwright() as p:
            # Launch browser headlessly to save system execution overhead
            browser = await p.chromium.launch(headless=True)
            
            # Mimic a realistic modern desktop browser fingerprint to reduce blocking
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # Open the target platform page
                await page.goto(url, wait_until="networkidle", timeout=30000)
                # Wait slightly for client-side JavaScript components to finish rendering
                await page.wait_for_timeout(3000)
                html = await page.content()
            except Exception as e:
                print(f"[RedditScraper Error] Failed to load webpage: {e}")
                html = ""
            finally:
                await browser.close()

        if not html:
            return extracted_data

        # Standardize HTML parsing using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Target custom shreddit web elements containing layout content
        posts = soup.find_all("shreddit-post")
        
        for post in posts[:max_results]:
            title = post.get("post-title", "").strip()
            permalink = post.get("permalink", "")
            full_url = f"https://reddit.com{permalink}"
            
            # Locate the child div that houses the text description
            content_div = post.find("div", {"slot": "text-body"})
            body_text = content_div.get_text().strip() if content_div else ""
            
            # Bundle title and context together into a clean text block for the LLM
            full_text = f"Title: {title}\nBody: {body_text}"
            
            # Append the data using the standardized dictionary keys
            extracted_data.append({
                "url": full_url,
                "text": full_text
            })
            
        return extracted_data
