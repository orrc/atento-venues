#!/usr/bin/env python3
"""
Check Berlin venue scraping progress - unified progress tracking

Works with the new standardized filenames from scraper_berlin.py
"""

import json
from pathlib import Path
from datetime import datetime
import argparse

def analyze_venues(venues):
    """Analyze venue data and return statistics"""
    stats = {
        'total': len(venues),
        'with_address': sum(1 for v in venues if v.get('address')),
        'with_description': sum(1 for v in venues if v.get('about')),
        'with_website': sum(1 for v in venues if v.get('website')),
        'with_tags': sum(1 for v in venues if v.get('tags')),
        'with_coordinates': sum(1 for v in venues if v.get('coordinates')),
        'with_district': sum(1 for v in venues if v.get('district')),
    }
    
    # Collect unique tags and districts
    all_tags = set()
    all_districts = set()
    
    for venue in venues:
        if venue.get('tags'):
            all_tags.update(venue['tags'])
        if venue.get('district'):
            all_districts.add(venue['district'])
    
    stats['unique_tags'] = len(all_tags)
    stats['unique_districts'] = len(all_districts)
    
    return stats

def format_file_info(filepath):
    """Get formatted file information"""
    path = Path(filepath)
    if not path.exists():
        return None
    
    stat = path.stat()
    size_mb = stat.st_size / (1024 * 1024)
    modified = datetime.fromtimestamp(stat.st_mtime)
    
    return {
        'size_mb': size_mb,
        'modified': modified,
        'path': str(path)
    }

def check_progress():
    """Check current scraping progress"""
    print("🏛️  BERLIN VENUE SCRAPING PROGRESS")
    print("=" * 50)
    
    # Check main files
    main_files = [
        'venues_berlin.json',           # Main output
        'venues_berlin_progress.json',  # Progress file
        'venues_berlin_temp.json'       # Temp file
    ]
    
    # Check for milestone and backup files
    milestone_files = list(Path(".").glob("venues_berlin_milestone_*.json"))
    backup_files = list(Path(".").glob("venues_berlin_backup_*.json"))
    
    found_data = False
    
    print("\n📁 MAIN FILES:")
    print("-" * 30)
    
    for filename in main_files:
        file_info = format_file_info(filename)
        if file_info:
            found_data = True
            print(f"✅ {filename}")
            print(f"   Size: {file_info['size_mb']:.1f} MB")
            print(f"   Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Try to load and analyze
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    venues = json.load(f)
                    stats = analyze_venues(venues)
                    
                    print(f"   Venues: {stats['total']}")
                    print(f"   Completeness:")
                    print(f"     - Address: {stats['with_address']}/{stats['total']} ({stats['with_address']/stats['total']*100:.1f}%)")
                    print(f"     - Description: {stats['with_description']}/{stats['total']} ({stats['with_description']/stats['total']*100:.1f}%)")
                    print(f"     - Website: {stats['with_website']}/{stats['total']} ({stats['with_website']/stats['total']*100:.1f}%)")
                    print(f"     - Tags: {stats['with_tags']}/{stats['total']} ({stats['with_tags']/stats['total']*100:.1f}%)")
                    if stats['with_coordinates'] > 0:
                        print(f"     - Coordinates: {stats['with_coordinates']}/{stats['total']} ({stats['with_coordinates']/stats['total']*100:.1f}%)")
                    if stats['with_district'] > 0:
                        print(f"     - District: {stats['with_district']}/{stats['total']} ({stats['with_district']/stats['total']*100:.1f}%)")
                    
                    print(f"   Diversity:")
                    print(f"     - Unique tags: {stats['unique_tags']}")
                    if stats['unique_districts'] > 0:
                        print(f"     - Districts: {stats['unique_districts']}")
                    
            except Exception as e:
                print(f"   ⚠️  Error reading file: {e}")
            print()
        else:
            print(f"❌ {filename} - Not found")
    
    # Show milestone files
    if milestone_files:
        print(f"\n🏁 MILESTONE FILES ({len(milestone_files)}):")
        print("-" * 30)
        for file in sorted(milestone_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:  # Show latest 5
            file_info = format_file_info(file)
            print(f"📄 {file.name}")
            print(f"   Size: {file_info['size_mb']:.1f} MB")
            print(f"   Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if len(milestone_files) > 5:
            print(f"   ... and {len(milestone_files) - 5} more milestone files")
    
    # Show backup files
    if backup_files:
        print(f"\n💾 BACKUP FILES ({len(backup_files)}):")
        print("-" * 30)
        for file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:  # Show latest 3
            file_info = format_file_info(file)
            print(f"📄 {file.name}")
            print(f"   Size: {file_info['size_mb']:.1f} MB")
            print(f"   Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check log file
    log_file = Path("scraper_berlin.log")
    if log_file.exists():
        print(f"\n📋 LOG FILE:")
        print("-" * 30)
        file_info = format_file_info(log_file)
        print(f"📄 {log_file.name}")
        print(f"   Size: {file_info['size_mb']:.1f} MB")
        print(f"   Modified: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show last few log lines
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"   Last entries:")
                    for line in lines[-3:]:
                        print(f"     {line.strip()}")
        except Exception as e:
            print(f"   ⚠️  Error reading log: {e}")
    
    if not found_data:
        print("\n❌ No venue data found!")
        print("\nTo start scraping:")
        print("   # Test mode (2 pages, ~50 venues)")
        print("   python scraper_berlin.py --test")
        print()
        print("   # Full scrape (all venues)")
        print("   python scraper_berlin.py")
        print()
        print("   # Custom limits")
        print("   python scraper_berlin.py --max-pages 5 --max-venues 100")
    else:
        print(f"\n✅ Data found! Use the web interface:")
        print("   python serve.py")
        print("   # Then open http://localhost:8001")

def main():
    parser = argparse.ArgumentParser(description='Check Berlin venue scraping progress')
    parser.add_argument('--detailed', action='store_true', help='Show detailed venue analysis')
    
    args = parser.parse_args()
    
    check_progress()
    
    if args.detailed and Path('venues_berlin.json').exists():
        print(f"\n🔍 DETAILED ANALYSIS:")
        print("-" * 30)
        
        with open('venues_berlin.json', 'r', encoding='utf-8') as f:
            venues = json.load(f)
        
        # Show top tags
        tag_counts = {}
        for venue in venues:
            for tag in venue.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        if tag_counts:
            print("Top 10 tags:")
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"   {tag}: {count}")
        
        # Show districts if available
        district_counts = {}
        for venue in venues:
            district = venue.get('district')
            if district:
                district_counts[district] = district_counts.get(district, 0) + 1
        
        if district_counts:
            print(f"\nDistricts ({len(district_counts)}):")
            for district, count in sorted(district_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {district}: {count}")

if __name__ == "__main__":
    main()