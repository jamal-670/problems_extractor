# app/scraper/g2_scraper.py
import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class G2Scraper(BaseScraper):
    async def scrape(self, target_niche: str, max_results: int, **kwargs) -> List[Dict[str, str]]:
        """
        Scrapes B2B software reviews from G2.
        
        Inputs:
            target_niche (str): The product name or software category to target (e.g., 'hubspot', 'salesforce')
            max_results (int): Number of target reviews to fetch
        """
        extracted_data = []
        reviews_per_page = 10 # G2 typically loads 10 reviews per page
        page_number = 1
        
        # Format the name for the G2 URL string (e.g., "HubSpot CRM" -> "hubspot-crm")
        formatted_niche = target_niche.lower().replace(" ", "-")
        
        async with async_playwright() as p:
            # We run with headless=True, but pass parameters to appear human
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            # Loop through pages until we gather enough items to meet max_results
            while len(extracted_data) < max_results:
                url = f"https://g2.com{formatted_niche}/reviews?page={page_number}"
                print(f"[G2Scraper] Navigating to page {page_number}...")
                
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    # Use a dynamic randomized human-like delay to throw off anti-bot detection
                    await page.wait_for_timeout(4000) 
                    
                    html = await page.content()
                except Exception as e:
                    print(f"[G2Scraper Error] Blocked or failed to load page {page_number}: {e}")
                    break
                
                soup = BeautifulSoup(html, "html.parser")
                
                # G2 wraps reviews inside standard semantic item-mapped wrappers
                review_cards = soup.find_all("div", {"itemprop": "review"})
                
                if not review_cards:
                    print("[G2Scraper] No more review cards detected on this page. Stopping.")
                    break
                    
                for card in review_cards:
                    if len(extracted_data) >= max_results:
                        break
                        
                    # Extract the custom review text or specific complaints block
                    title_el = card.find("h3", {"itemprop": "name"})
                    title = title_el.get_text().strip() if title_el else ""
                    
                    # Target what users dislike (this is where real problem data hides)
                    dislike_heading = card.find(text="What do you dislike?")
                    dislike_text = ""
                    if dislike_heading:
                        # Find the next sibling paragraph text block element containing user complaints
                        dislike_div = dislike_heading.find_next("div")
                        if dislike_div:
                            dislike_text = dislike_div.get_text().strip()
                    
                    # If we couldn't find a direct dislike block, fallback to general review body layout text
                    if not dislike_text:
                        body_el = card.find("div", {"itemprop": "reviewBody"})
                        dislike_text = body_el.get_text().strip() if body_el else ""
                        
                    # Build custom payload string optimized specifically for your AI prompt processor step
                    full_text = f"Review Headline: {title}\nUser Complaints & Drawbacks:\n{dislike_text}"
                    
                    extracted_data.append({
                        "url": f"{url}#review-card",
                        "text": full_text
                    })
                
                # Increment the pagination tracker page number
                page_number += 1
                
            await browser.close()
            
        return extracted_data
