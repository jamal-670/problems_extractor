# app/scraper/razorpay_scraper.py
import asyncio
from typing import List, Dict
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper

class RazorpayScraper(BaseScraper):
    async def scrape(self, target_niche: str, max_results: int, **kwargs) -> List[Dict[str, str]]:
        """
        Scrapes crowdsourced micro-SME problems from Razorpay's 'Fix My Itch' interface.
        
        Inputs:
            target_niche (str): Used here to filter content semantically in the text body matching 
                                targeted business sectors (e.g., 'Logistics', 'B2B', 'Retail').
        """
        url = "https://razorpay.com/m/fix-my-itch/"
        extracted_data = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000) # Give dynamic dashboard modules breathing room to load
                html = await page.content()
            except Exception as e:
                print(f"[RazorpayScraper Error] Failed to fetch layout: {e}")
                html = ""
            finally:
                await browser.close()

        if not html:
            return extracted_data

        soup = BeautifulSoup(html, "html.parser")
        
        # Look for problem cards, list items, or paragraph descriptions matching common layout structures
        # Note: We pull generic text nodes first; we can refine the specific CSS selectors later as we explore the platform UI
        problem_elements = soup.find_all(["li", "p", "div"])
        
        for element in problem_elements:
            if len(extracted_data) >= max_results:
                break
                
            text_content = element.get_text().strip()
            
            # Initial operational filter: Ensure it contains our target keyword sector (e.g. 'logistics') 
            # and contains enough detailed text length to be a valid problem statement
            if len(text_content) > 60 and target_niche.lower() in text_content.lower():
                # Avoid inserting exact duplicates if multiple layout sub-elements contain the same string
                if not any(d['text'] == text_content for d in extracted_data):
                    extracted_data.append({
                        "url": url,
                        "text": f"Razorpay Crowdsourced Problem:\n{text_content}"
                    })
                    
        return extracted_data
