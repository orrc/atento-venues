#!/usr/bin/env python3
"""
Unified Berlin Venue Scraper - Parameterizable scraper for Atento voucher venues

Features:
- Test mode: scrape limited venues/pages for testing
- Full mode: scrape all venues with resume capability  
- Consistent output filename: venues_berlin.json
- Progressive saving with milestone backups
- Comprehensive logging and progress tracking
"""

import asyncio
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper_berlin.log')
    ]
)
logger = logging.getLogger(__name__)

class BerlinVenueScraper:
    def __init__(self, test_mode: bool = False, max_pages: int = None, max_venues: int = None):
        self.base_url = "https://atentogutschein.de"
        self.session = None
        self.test_mode = test_mode
        self.max_pages = max_pages or (2 if test_mode else 89)  # Default 2 pages for test, 89 for full
        self.max_venues = max_venues
        
        # Standardized filenames
        self.main_output = "venues_berlin.json"
        self.progress_file = "venues_berlin_progress.json" 
        self.temp_file = "venues_berlin_temp.json"
        
        logger.info(f"🚀 Berlin Venue Scraper initialized")
        logger.info(f"   Mode: {'TEST' if test_mode else 'FULL'}")
        logger.info(f"   Max pages: {self.max_pages}")
        if max_venues:
            logger.info(f"   Max venues: {max_venues}")
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        
    async def get_page(self, url: str) -> Optional[str]:
        """Fetch a single page with error handling and rate limiting"""
        try:
            await asyncio.sleep(0.3)  # Rate limiting
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_venues_clean(self, html: str) -> List[Dict]:
        """Parse venues using clean CSS selectors"""
        soup = BeautifulSoup(html, 'html.parser')
        venues = []
        
        # Look for venue containers
        venue_containers = (
            soup.select('div.p-4') or  # Primary pattern
            soup.select('div[class*="p-4"]') or  # Flexible class matching
            # Fallback: find divs that contain h3 with merchant links
            [div for div in soup.find_all('div') if div.find('h3') and div.find('a', href=lambda x: x and '/marketplace_merchants/' in x)]
        )
        
        for container in venue_containers:
            venue_data = self.extract_venue_from_container(container)
            if venue_data:
                venues.append(venue_data)
        
        return venues
    
    def extract_venue_from_container(self, container) -> Optional[Dict]:
        """Extract venue data from a container div"""
        
        # Extract venue name and URL from h3 > a
        h3 = container.find('h3')
        if not h3:
            return None
            
        link = h3.find('a', href=lambda x: x and '/marketplace_merchants/' in x)
        if not link:
            return None
        
        venue_name = link.get_text(strip=True)
        venue_url = link.get('href')
        venue_slug = venue_url.split('/marketplace_merchants/')[-1].split('?')[0]
        
        # Extract address
        address = ""
        address_p = (
            container.select_one('p.text-gray-600') or
            container.select_one('p[class*="text-gray"]') or
            container.find('p', class_=lambda x: x and 'gray' in x) or
            next((p for p in container.find_all('p') 
                  if 'berlin' in p.get_text().lower() and 
                  any(indicator in p.get_text().lower() for indicator in ['str', 'straße', 'platz', 'allee'])), None)
        )
        
        if address_p:
            import re
            address_text = address_p.get_text(strip=True)
            address = re.sub(r'^[^\w]*', '', address_text).strip()
        
        # Extract tags from span elements (using working scraper logic)
        tags = []
        tag_spans = (
            container.select('span.inline-block') or
            container.select('span[class*="bg-blue"]') or
            container.select('span[class*="rounded"]') or
            # Fallback: look for spans with short text content
            [span for span in container.find_all('span') 
             if span.get_text(strip=True) and len(span.get_text(strip=True)) < 25]
        )
        
        for span in tag_spans:
            tag_text = span.get_text(strip=True)
            if (tag_text and 
                tag_text != venue_name and 
                tag_text not in address and
                len(tag_text) < 30):
                tags.append(tag_text)
        
        return {
            "name": venue_name,
            "slug": venue_slug,
            "address": address,
            "tags": list(set(tags)),  # Remove duplicates
            "detail_url": f"{self.base_url}{venue_url}"
        }
    
    async def get_venue_details(self, venue: Dict) -> Dict:
        """Get detailed info from venue detail page"""
        detail_html = await self.get_page(venue['detail_url'])
        if not detail_html:
            return venue
        
        soup = BeautifulSoup(detail_html, 'html.parser')
        
        # Extract "About" section - look for h3 with "About" followed by content (working scraper logic)
        about_section = ""
        about_heading = soup.find('h3', string=lambda x: x and 'About' in x)
        if about_heading:
            # Look for the next element with substantial text
            sibling = about_heading.find_next_sibling()
            while sibling:
                text = sibling.get_text(strip=True)
                if text and len(text) > 50:
                    about_section = text
                    break
                sibling = sibling.find_next_sibling()
        
        # Extract website URL - look for external links with "Visit Website" text (working scraper logic)
        website_url = ""
        website_links = soup.find_all('a', href=lambda x: x and x.startswith('http') and 'atentogutschein.de' not in x)
        for link in website_links:
            if 'visit website' in link.get_text().lower() or 'website' in link.get_text().lower():
                website_url = link.get('href', '')
                break
        
        venue.update({
            "about": about_section,
            "website": website_url
        })
        
        return venue
    
    async def scrape_progressive(self, start_page: int = 1) -> List[Dict]:
        """Progressive scraping with resume capability"""
        
        logger.info(f"🔍 Starting progressive scrape")
        logger.info(f"   Pages: {start_page} to {self.max_pages}")
        
        # Load existing progress if available
        all_venues = self.load_progress()
        start_venue_count = len(all_venues)
        
        # Determine starting page based on existing venues
        if all_venues and start_page == 1:
            # Estimate start page based on venues already scraped (roughly 20-25 venues per page)
            estimated_page = max(1, len(all_venues) // 22)
            logger.info(f"📊 Found {len(all_venues)} existing venues, resuming from estimated page {estimated_page}")
            start_page = estimated_page
        
        # Use the correct URL pattern from working scraper
        base_url = f"{self.base_url}/en/communities/lokale-favoriten-gutschein?q%5Bcity_or_address_postal_code_cont%5D=Berlin"
        
        for page_num in range(start_page, self.max_pages + 1):
            logger.info(f"📄 Processing page {page_num}/{self.max_pages}")
            
            if page_num == 1:
                page_url = base_url
            else:
                page_url = f"{base_url}&page={page_num}"
            
            html_content = await self.get_page(page_url)
            
            if not html_content:
                logger.error(f"❌ Failed to fetch page {page_num}, stopping")
                break
            
            page_venues = self.parse_venues_clean(html_content)
            logger.info(f"   Found {len(page_venues)} venues on page {page_num}")
            
            # Get detailed info for each venue
            for i, venue in enumerate(page_venues):
                detailed_venue = await self.get_venue_details(venue)
                all_venues.append(detailed_venue)
                
                if self.max_venues and len(all_venues) >= self.max_venues:
                    logger.info(f"🎯 Reached max venues limit ({self.max_venues})")
                    break
            
            # Save progress after each page
            self.save_venues(all_venues, self.progress_file)
            logger.info(f"💾 Progress saved: {len(all_venues)} total venues")
            
            # Milestone backup every 10 pages
            if page_num % 10 == 0:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                milestone_file = f"venues_berlin_milestone_p{page_num}_{timestamp}.json"
                self.save_venues(all_venues, milestone_file)
                logger.info(f"🏁 Milestone backup: {milestone_file}")
            
            # Check if we've hit venue limit
            if self.max_venues and len(all_venues) >= self.max_venues:
                break
        
        logger.info(f"✅ Scraping completed!")
        logger.info(f"   Total venues: {len(all_venues)}")
        logger.info(f"   New venues: {len(all_venues) - start_venue_count}")
        
        return all_venues
    
    def load_progress(self) -> List[Dict]:
        """Load existing progress from file"""
        try:
            if Path(self.progress_file).exists():
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    venues = json.load(f)
                    logger.info(f"📂 Loaded {len(venues)} venues from {self.progress_file}")
                    return venues
        except Exception as e:
            logger.warning(f"Could not load progress from {self.progress_file}: {e}")
        return []
    
    def save_venues(self, venues: List[Dict], filename: str):
        """Save venues to JSON file"""
        try:
            Path(filename).write_text(
                json.dumps(venues, indent=2, ensure_ascii=False), 
                encoding='utf-8'
            )
            logger.debug(f"💾 Saved {len(venues)} venues to {filename}")
        except Exception as e:
            logger.error(f"Failed to save venues to {filename}: {e}")
    
    def finalize_output(self, venues: List[Dict]):
        """Save final output and clean up temporary files"""
        
        # Save main output file
        self.save_venues(venues, self.main_output)
        logger.info(f"✅ Final output saved: {self.main_output} ({len(venues)} venues)")
        
        # Create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"venues_berlin_backup_{timestamp}.json"
        self.save_venues(venues, backup_file)
        logger.info(f"💾 Backup created: {backup_file}")
        
        # Clean up progress file if successful
        try:
            if Path(self.progress_file).exists():
                Path(self.progress_file).unlink()
                logger.info(f"🧹 Cleaned up progress file: {self.progress_file}")
        except Exception as e:
            logger.warning(f"Could not clean up progress file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Berlin Venue Scraper')
    parser.add_argument('--test', action='store_true', help='Test mode (2 pages, ~50 venues)')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scrape')
    parser.add_argument('--max-venues', type=int, help='Maximum venues to scrape')
    parser.add_argument('--start-page', type=int, default=1, help='Starting page number')
    
    args = parser.parse_args()
    
    async def run_scraper():
        async with BerlinVenueScraper(
            test_mode=args.test,
            max_pages=args.max_pages,
            max_venues=args.max_venues
        ) as scraper:
            
            venues = await scraper.scrape_progressive(start_page=args.start_page)
            scraper.finalize_output(venues)
            
            # Show final stats
            print(f"\n🎉 SCRAPING COMPLETE!")
            print(f"   Total venues: {len(venues)}")
            print(f"   Output file: {scraper.main_output}")
            print(f"   Mode: {'TEST' if args.test else 'FULL'}")
    
    asyncio.run(run_scraper())

if __name__ == "__main__":
    main()