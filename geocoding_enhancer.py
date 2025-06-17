#!/usr/bin/env python3
"""
Geocoding enhancer - add coordinates and districts to scraped venues
Run this after basic_full_scraper.py to add location data
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiohttp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeocodingEnhancer:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def geocode_venue(self, venue: Dict) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Geocode venue address and extract Berlin district"""
        try:
            # Use Nominatim geocoding service with detailed address breakdown
            query = f"{venue['address']}, Berlin, Germany"
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                'format': 'json',
                'q': query,
                'limit': 1,
                'addressdetails': 1,  # Get detailed address breakdown
                'extratags': 1       # Get additional tags
            }
            
            await asyncio.sleep(1.2)  # Rate limit for Nominatim (max 1 req/sec)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        result = data[0]
                        lat = float(result['lat'])
                        lon = float(result['lon'])
                        
                        # Extract district from address details
                        district = self.extract_district(result.get('address', {}))
                        
                        return lat, lon, district
            
            # Fallback: try simpler query
            simple_query = f"{venue['address'].split(',')[0]}, Berlin"
            params['q'] = simple_query
            
            await asyncio.sleep(1.2)
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and len(data) > 0:
                        result = data[0]
                        lat = float(result['lat'])
                        lon = float(result['lon'])
                        
                        district = self.extract_district(result.get('address', {}))
                        
                        return lat, lon, district
            
            logger.warning(f"Could not geocode {venue['name']}: {venue['address']}")
            return None, None, None
            
        except Exception as e:
            logger.error(f"Geocoding error for {venue['name']}: {e}")
            return None, None, None
    
    def extract_district(self, address_details: Dict) -> Optional[str]:
        """Extract Berlin district from Nominatim address details"""
        
        # Common Berlin district/neighborhood names in address components
        district_keys = [
            'suburb',           # Most common for Berlin districts
            'neighbourhood',    # Alternative spelling
            'city_district',    # Some areas use this
            'quarter',          # Some areas use this
            'district'          # Generic district
        ]
        
        for key in district_keys:
            if key in address_details:
                district = address_details[key]
                # Filter out non-district values
                if district and district != 'Berlin' and len(district) > 2:
                    return district
        
        # Fallback: check if postcode gives us district info
        postcode = address_details.get('postcode', '')
        if postcode.startswith('10'):
            # Map some common postcodes to districts (incomplete but helps)
            postcode_districts = {
                '10115': 'Mitte', '10117': 'Mitte', '10119': 'Mitte', '10178': 'Mitte', '10179': 'Mitte',
                '10435': 'Prenzlauer Berg', '10437': 'Prenzlauer Berg', '10439': 'Prenzlauer Berg',
                '10247': 'Friedrichshain', '10249': 'Friedrichshain',
                '10551': 'Moabit', '10553': 'Moabit', '10555': 'Moabit', '10559': 'Moabit',
                '10623': 'Charlottenburg', '10625': 'Charlottenburg', '10627': 'Charlottenburg',
                '10777': 'Schöneberg', '10779': 'Schöneberg', '10781': 'Schöneberg',
                '10963': 'Kreuzberg', '10965': 'Kreuzberg', '10967': 'Kreuzberg', '10969': 'Kreuzberg',
                '12043': 'Neukölln', '12045': 'Neukölln', '12047': 'Neukölln', '12049': 'Neukölln',
                '12051': 'Neukölln', '12053': 'Neukölln', '12055': 'Neukölln', '12057': 'Neukölln',
                '12059': 'Neukölln', '12099': 'Tempelhof', '12101': 'Tempelhof', '12103': 'Tempelhof',
                '12105': 'Tempelhof', '12107': 'Tempelhof', '12109': 'Tempelhof'
            }
            return postcode_districts.get(postcode)
        
        return None
    
    async def enhance_venues_batch(self, venues: List[Dict], batch_size: int = 50, 
                                 start_index: int = 0, progress_file: str = "venues_enhanced_progress.json") -> List[Dict]:
        """Add coordinates and districts to venues in batches with resume capability"""
        
        # Load existing progress if available
        enhanced_venues = self.load_progress(progress_file)
        
        if enhanced_venues and start_index == 0:
            logger.info(f"Resuming with {len(enhanced_venues)} venues already enhanced")
            start_index = len(enhanced_venues)
        
        logger.info(f"Enhancing venues from index {start_index}/{len(venues)} in batches of {batch_size}")
        
        for i in range(start_index, len(venues), batch_size):
            batch = venues[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(venues) + batch_size - 1) // batch_size
            
            logger.info(f"Processing batch {batch_num}/{total_batches} (venues {i+1}-{min(i+batch_size, len(venues))})")
            
            # Enhance batch with geocoding
            for j, venue in enumerate(batch):
                venue_index = i + j + 1
                logger.info(f"  🌍 Geocoding venue {venue_index}/{len(venues)}: {venue['name']}")
                
                # Skip if already has coordinates
                if venue.get('coordinates') and venue.get('district'):
                    logger.info(f"    ✅ Already has coordinates and district")
                    enhanced_venues.append(venue)
                    continue
                
                lat, lon, district = await self.geocode_venue(venue)
                
                venue['coordinates'] = [lat, lon] if lat and lon else None
                venue['district'] = district
                
                enhanced_venues.append(venue)
                
                coord_status = "✅" if lat and lon else "❌"
                district_status = f"🏘️ {district}" if district else "❓"
                logger.info(f"    {coord_status} Coordinates, {district_status}")
            
            # Save progress after each batch
            self.save_venues(enhanced_venues, progress_file)
            logger.info(f"✅ Batch {batch_num} complete! Progress saved.")
            
            # Save milestone backups every 5 batches
            if batch_num % 5 == 0:
                milestone_file = f"venues_enhanced_milestone_batch_{batch_num}.json"
                self.save_venues(enhanced_venues, milestone_file)
                logger.info(f"🏁 Milestone backup saved: {milestone_file}")
            
            # Brief pause between batches
            await asyncio.sleep(2)
        
        return enhanced_venues
    
    def load_progress(self, filename: str) -> List[Dict]:
        """Load existing progress from file"""
        try:
            if Path(filename).exists():
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load progress from {filename}: {e}")
        return []
    
    def save_venues(self, venues: List[Dict], filename: str):
        """Save venues to JSON file"""
        Path(filename).write_text(json.dumps(venues, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info(f"Saved {len(venues)} venues to {filename}")

async def main():
    """Enhance venues with geocoding data"""
    start_time = time.time()
    
    # Find the main Berlin venues file
    venue_files = [
        "venues_berlin.json",  # New standard filename
        "venues_all_progress.json",  # Legacy fallback
        "venues_all_complete.json"
    ]
    
    # Also check for timestamped backup files
    for file in Path(".").glob("venues_berlin_backup_*.json"):
        venue_files.append(str(file))
    for file in Path(".").glob("venues_all_complete_*.json"):
        venue_files.append(str(file))
    
    input_file = None
    for file in venue_files:
        if Path(file).exists():
            input_file = file
            break
    
    if not input_file:
        print("❌ No venue data file found!")
        print("Run scraper_berlin.py first to create venue data.")
        print("Example: python scraper_berlin.py --test")
        return
    
    print("🌍 GEOCODING ENHANCER")
    print("=" * 50)
    print(f"Input file: {input_file}")
    print("This will add coordinates and districts to all venues.")
    print("Progress is saved after each batch and can be resumed.")
    print()
    
    # Load venues
    with open(input_file, 'r', encoding='utf-8') as f:
        venues = json.load(f)
    
    print(f"Loaded {len(venues)} venues for enhancement")
    
    async with GeocodingEnhancer() as enhancer:
        # Enhance venues with geocoding
        enhanced_venues = await enhancer.enhance_venues_batch(
            venues,
            batch_size=20,  # Smaller batches for geocoding
            progress_file="venues_berlin_geocoding_progress.json"
        )
        
        # Update main file with enhanced data
        enhancer.save_venues(enhanced_venues, "venues_berlin.json")
        print(f"✅ Main file updated: venues_berlin.json")
        
        # Also create timestamped backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"venues_berlin_geocoded_{timestamp}.json"
        enhancer.save_venues(enhanced_venues, backup_file)
        print(f"💾 Backup created: {backup_file}")
        
        # Clean up progress file if successful
        progress_file = "venues_berlin_geocoding_progress.json"
        try:
            if Path(progress_file).exists():
                Path(progress_file).unlink()
                print(f"🧹 Cleaned up progress file: {progress_file}")
        except Exception as e:
            print(f"⚠️  Could not clean up progress file: {e}")
        
        # Summary
        elapsed = time.time() - start_time
        print()
        print("🎉 GEOCODING COMPLETE!")
        print("=" * 50)
        print(f"Total venues enhanced: {len(enhanced_venues)}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print(f"Main file: venues_berlin.json")
        print(f"Backup file: {backup_file}")
        
        # Statistics
        with_coords = sum(1 for v in enhanced_venues if v.get('coordinates'))
        districts = set(v['district'] for v in enhanced_venues if v.get('district'))
        
        print(f"\nStatistics:")
        print(f"- Venues with coordinates: {with_coords}/{len(enhanced_venues)} ({with_coords/len(enhanced_venues)*100:.1f}%)")
        print(f"- Unique districts found: {len(districts)}")
        print(f"- Districts: {sorted(districts)}")

if __name__ == "__main__":
    asyncio.run(main())