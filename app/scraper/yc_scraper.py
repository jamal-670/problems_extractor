# app/scraper/yc_scraper.py
import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
# bs4 is optional here but kept for unified parsing styles across your ecosystem
from bs4 import BeautifulSoup 
from .base_scraper import BaseScraper

class YCScraper(BaseScraper):
    async def scrape(self, target_niche: str, max_results: int, **kwargs) -> List[Dict[str, str]]:
        """
        Scrapes high-value macroeconomic problem prompts from Y Combinator's Request for Startups.
        
        Inputs:
            target_niche (str): Used to isolate specific technical prompts (e.g., 'AI', 'Fintech', 'Government')
        """
        url = "https://www.ycombinator.com/rfs"
        extracted_data = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                html = await page.content()
            except Exception as e:
                print(f"[YCScraper Error] Could not load RFS directory: {e}")
                html = ""
            finally:
                await browser.close()

        if not html:
            return extracted_data

        soup = BeautifulSoup(html, "html.parser")
        
        # YC organizes their problem briefs under distinctive header blocks (typically <h3> or <h4>)
        headings = soup.find_all(["h3", "h4"])
        
        for heading in headings:
            if len(extracted_data) >= max_results:
                break
                
            heading_title = heading.get_text().strip()
            
            # Find the paragraph content block describing why this problem matters to YC partners
            content_paragraphs = []
            sibling = heading.find_next_sibling()
            
            # Keep pulling subsequent sibling text blocks until reaching the next major section header
            while sibling and sibling.name not in ["h3", "h4"]:
                if sibling.name == "p":
                    content_paragraphs.append(sibling.get_text().strip())
                sibling = sibling.find_next_sibling()
                
            full_description = "\n".join(content_paragraphs)
            combined_text = f"YC Strategic Problem Title: {heading_title}\nDescription:\n{full_description}"
            
            # Check if this high-value YC thesis aligns with our active target pipeline query string
            if target_niche.lower() in combined_text.lower() and len(full_description) > 100:
                extracted_data.append({
                    "url": url,
                    "text": combined_text
                })
                
        return extracted_data
 