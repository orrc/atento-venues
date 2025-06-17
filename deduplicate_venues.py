#!/usr/bin/env python3
"""
Deduplicate venues and create clean final dataset
"""

import json
from pathlib import Path
from collections import Counter

def deduplicate_venues(input_file, output_file):
    """Remove duplicates from venue data"""
    
    print(f"🧹 DEDUPLICATION SCRIPT")
    print("=" * 30)
    print(f"Input: {input_file}")
    
    # Load venues
    with open(input_file, 'r', encoding='utf-8') as f:
        venues = json.load(f)
    
    original_count = len(venues)
    print(f"Original venues: {original_count}")
    
    # Check for duplicates by name
    names = [v['name'] for v in venues]
    name_counts = Counter(names)
    duplicates = {name: count for name, count in name_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n🔍 Found duplicates:")
        for name, count in sorted(duplicates.items()):
            print(f"  - '{name}': {count} copies")
        
        print(f"\nTotal duplicate venues: {sum(duplicates.values()) - len(duplicates)}")
    else:
        print("✅ No duplicates found!")
        return venues
    
    # Deduplicate by name (keep first occurrence)
    seen_names = set()
    deduplicated = []
    
    for venue in venues:
        name = venue['name']
        if name not in seen_names:
            deduplicated.append(venue)
            seen_names.add(name)
        else:
            print(f"  🗑️  Removed duplicate: {name}")
    
    cleaned_count = len(deduplicated)
    removed_count = original_count - cleaned_count
    
    print(f"\n📊 Results:")
    print(f"- Original: {original_count} venues")
    print(f"- Removed: {removed_count} duplicates")
    print(f"- Final: {cleaned_count} unique venues")
    print(f"- Reduction: {removed_count/original_count*100:.1f}%")
    
    # Save cleaned data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(deduplicated, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Clean dataset saved: {output_file}")
    
    # Statistics
    with_about = sum(1 for v in deduplicated if v.get('about'))
    with_website = sum(1 for v in deduplicated if v.get('website'))
    all_tags = set()
    for v in deduplicated:
        all_tags.update(v.get('tags', []))
    
    print(f"\n📈 Dataset Statistics:")
    print(f"- With description: {with_about}/{cleaned_count} ({with_about/cleaned_count*100:.1f}%)")
    print(f"- With website: {with_website}/{cleaned_count} ({with_website/cleaned_count*100:.1f}%)")
    print(f"- Unique tags: {len(all_tags)}")
    print(f"- Sample tags: {sorted(list(all_tags))[:10]}...")
    
    return deduplicated

def main():
    # Find the most recent complete file - prefer new standard filename
    candidates = [
        "venues_berlin.json",  # New standard filename
        "venues_all_progress.json"  # Legacy fallback
    ]
    
    # Add timestamped Berlin files (geocoded and backups)
    for file in Path(".").glob("venues_berlin_geocoded_*.json"):
        candidates.insert(1, str(file))  # Insert after main file
    for file in Path(".").glob("venues_berlin_backup_*.json"):
        candidates.append(str(file))
    
    # Add legacy timestamped complete files
    for file in Path(".").glob("venues_all_complete_*.json"):
        candidates.append(str(file))
    
    input_file = None
    for candidate in candidates:
        if Path(candidate).exists():
            input_file = candidate
            break
    
    if not input_file:
        print("❌ No venue data file found!")
        print("Run scraper_berlin.py first to create venue data.")
        return
    
    # Use standard clean filename
    output_file = "venues_berlin_clean.json"
    
    # Deduplicate
    clean_venues = deduplicate_venues(input_file, output_file)
    
    print(f"\n🎯 Next Steps:")
    print(f"1. Use {output_file} as your final dataset")
    print(f"2. Run: python geocoding_enhancer.py")
    print(f"3. Update web interface to use clean data")

if __name__ == "__main__":
    main()