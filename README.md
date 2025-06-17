# Atento Voucher Venues - Berlin

A unified web scraper and interactive browser for Atento voucher venues in Berlin.

## Background
I got an Atento gift voucher, which apparently can be used at many venues. But using their [website](http://atentogutschein.de/en/) to find venues is really painful, with awful navigation, terrible search, a broken map, and is slow to load.

Therefore I scraped the venue data (for Berlin) into a JSON file, with the hope that I could more easily find venues by creating [my own web interface](https://voucher.orr.dev/).

So I did that — or rather an LLM did it for me. Everything in this repo, including the README below, was written by [Claude Code](https://www.anthropic.com/claude-code).

## Features

### 🕷️ **Unified Scraping System**
- **Parameterizable scraper** with test and full modes
- **Progressive scraping** with automatic resume capability
- **Smart parsing** extracts venue name, address, tags, descriptions, and websites
- **Geocoding enhancement** adds coordinates and Berlin district information
- **Rate-limited requests** with comprehensive error handling and logging
- **Milestone backups** and automatic cleanup of temporary files

### 🌐 **Enhanced Web Interface**
- **Smart search** by venue name and description content
- **Advanced filtering** by categories/tags with AND/OR logic toggle
- **District filtering** with organized Berlin area groups
- **Multiple view modes** - Grid, List, and interactive Map
- **Visual enhancements** - Category emojis, selection indicators, improved formatting
- **Persistent preferences** - Selected filters saved in localStorage
- **Responsive design** for mobile and desktop
- **Berlin-focused map** with coordinate validation and rich popups

### 📊 **Data Structure**
```json
{
  "name": "Dussmann das KulturKaufhaus",
  "slug": "dussmann-das-kulturkaufhaus",
  "address": "Friedrichstr. 90, Berlin", 
  "tags": ["Culture", "Bookstore", "Shop"],
  "district": "Mitte",
  "coordinates": [52.518369, 13.3890173],
  "about": "The KulturKaufhaus Dussmann in the tradition-rich city...",
  "website": "http://www.kulturkaufhaus.de",
  "detail_url": "https://atentogutschein.de/en/marketplace_merchants/..."
}
```

## Quick Start

### 1. View Current Data
```bash
python serve.py
# Open http://localhost:8001 in your browser
```

### 2. Scrape Fresh Data

#### Test Mode (Recommended for Testing)
```bash
# Scrape 2 pages, ~50 venues for testing
python scraper_berlin.py --test

# Or limit to specific number of venues
python scraper_berlin.py --test --max-venues 10
```

#### Full Production Scrape
```bash
# Scrape all venues (~2,000+ venues, ~89 pages)
python scraper_berlin.py

# Custom limits for partial scrapes
python scraper_berlin.py --max-pages 20 --max-venues 500
```

### 3. Complete Processing Pipeline

```bash
# 1. Scrape venues (creates venues_berlin.json)
python scraper_berlin.py

# 2. Remove duplicates (optional, creates venues_berlin_clean.json)
python deduplicate_venues.py

# 3. Add coordinates and districts (enhances venues_berlin.json)
python geocoding_enhancer.py

# 4. Deploy to web interface
cp venues_berlin.json public/venues_berlin.json

# 5. View results
python serve.py
```

## Progressive Scraping & Resume

### How Resume Works
The scraper **automatically resumes** where it left off - no manual page calculation needed:

1. **Automatic detection**: Scraper counts existing venues and estimates the resume page
2. **Progress tracking**: `venues_berlin_progress.json` tracks real-time progress
3. **Milestone backups**: Automatic backups every 10 pages (`venues_berlin_milestone_p20_timestamp.json`)
4. **Graceful interruption**: Stop with Ctrl+C, restart with same command
5. **Auto-cleanup**: Progress files automatically deleted on successful completion

### Resume Examples
```bash
# Start scraping
python scraper_berlin.py

# [Interrupted at page 25]
# Restart - automatically resumes from ~page 25
python scraper_berlin.py

# [Completes successfully]
# venues_berlin.json created, progress files cleaned up
```

### Geocoding Resume
The geocoding enhancer also has **automatic resume**:

```bash
# Start geocoding
python geocoding_enhancer.py

# [Interrupted after 500 venues]
# Restart - automatically continues from venue 501
python geocoding_enhancer.py

# [Completes successfully]  
# venues_berlin.json updated, progress files cleaned up
```

## Command Line Options

### Main Scraper (`scraper_berlin.py`)
```bash
# Test mode with defaults (2 pages, ~50 venues)
python scraper_berlin.py --test

# Custom test limits
python scraper_berlin.py --test --max-venues 25
python scraper_berlin.py --test --max-pages 5

# Full scrape with custom limits
python scraper_berlin.py --max-pages 30
python scraper_berlin.py --max-venues 1000

# Resume from specific page (rarely needed)
python scraper_berlin.py --start-page 15
```

### Progress Monitoring
```bash
# Quick progress check
python check_progress_berlin.py

# Detailed analysis with tag/district statistics
python check_progress_berlin.py --detailed
```

## File Structure

### Core Scripts
- **`scraper_berlin.py`** - Main unified scraper with test/full modes
- **`geocoding_enhancer.py`** - Add coordinates and Berlin districts
- **`deduplicate_venues.py`** - Remove duplicate venues (optional)
- **`check_progress_berlin.py`** - Monitor progress and analyze data

### Support Files
- **`serve.py`** - Local web server for testing
- **`requirements.txt`** - Python dependencies

### Data Files (Auto-generated)
- **`venues_berlin.json`** - Main output file (final dataset)
- **`venues_berlin_backup_TIMESTAMP.json`** - Timestamped backups
- **`venues_berlin_geocoded_TIMESTAMP.json`** - Geocoding backups
- **`venues_berlin_progress.json`** - Temporary progress (auto-cleaned)
- **`venues_berlin_geocoding_progress.json`** - Geocoding progress (auto-cleaned)
- **`venues_berlin_milestone_pXX_TIMESTAMP.json`** - Milestone backups

### Web Interface
- **`public/index.html`** - Web interface
- **`public/venues_berlin.json`** - Production data for web interface

### Logs
- **`scraper_berlin.log`** - Comprehensive scraping logs

## Production Workflow

### Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Test scraper
python scraper_berlin.py --test --max-venues 5

# Verify web interface
python serve.py
# Check http://localhost:8001/public/
```

### Full Data Pipeline
```bash
# 1. Scrape all venues (~30-60 minutes)
python scraper_berlin.py

# 2. Clean data (optional - removes duplicates)
python deduplicate_venues.py

# 3. Add location data (~10-20 minutes)
python geocoding_enhancer.py

# 4. Deploy to web interface
cp venues_berlin.json public/venues_berlin.json

# 5. Commit and deploy (auto-deploys to Cloudflare Workers)
git add public/venues_berlin.json
git commit -m "Update venue data - $(date '+%Y-%m-%d')"
git push
```

### Monitoring During Scraping
```bash
# In another terminal, monitor progress
python check_progress_berlin.py

# View recent log entries
tail -f scraper_berlin.log

# Check milestone files
ls -la venues_berlin_milestone_*.json
```

## Web Interface Features

### Enhanced Functionality
- **Smart search** - Searches both venue names and descriptions
- **Organized categories** - 65+ food tags properly categorized
- **District groups** - Berlin areas organized by Central/North/South/East/West
- **Visual indicators** - Blue outlines show categories with active selections
- **Category emojis** - Quick visual identification (🍽️ dining, 🛍️ shopping, etc.)
- **Improved formatting** - Addresses show district inline: "Friedrichstr. 90, Mitte"
- **Persistent state** - Selected filters and category expand/collapse saved

### View Modes
- **Grid View** - Card layout with category emojis and rich content
- **List View** - Compact vertical layout  
- **Map View** - Interactive map with Berlin coordinate validation

### Search & Filtering
- **Name & description search** - Find venues by any text content
- **Tag filtering** - AND/OR logic for precise results
- **District filtering** - Organized by Berlin geographical areas
- **Combined filtering** - Mix search, tags, and districts

## Troubleshooting

### Common Issues

**Scraper fails with HTTP errors:**
```bash
# Check your internet connection and try again
python scraper_berlin.py --test --max-venues 2
```

**Resume not working:**
```bash
# Check for progress file
ls venues_berlin_progress.json

# Manual resume from specific page
python scraper_berlin.py --start-page 25
```

**Geocoding fails:**
```bash
# Check if main file exists
ls venues_berlin.json

# Monitor geocoding progress
python check_progress_berlin.py
```

**Web interface shows no data:**
```bash
# Check data file exists in public directory
ls public/venues_berlin.json

# Verify server is running on correct port
python serve.py
# Open http://localhost:8001/public/
```

### File Recovery

**Lost main file but have backups:**
```bash
# Use most recent backup
cp venues_berlin_backup_LATEST.json venues_berlin.json
```

**Corrupted progress file:**
```bash
# Remove and restart
rm venues_berlin_progress.json
python scraper_berlin.py
```

### Performance Tips

- **Use test mode** for development: `--test --max-venues 10`
- **Monitor with progress checker** during long scrapes
- **Resume capability** means interruptions are not a problem
- **Milestone backups** provide recovery points every 10 pages

## Dependencies

```bash
pip install aiohttp beautifulsoup4 asyncio
```

See `requirements.txt` for complete list.

## Development

### Testing Changes
```bash
# Quick test with minimal data
python scraper_berlin.py --test --max-venues 3

# Test full pipeline
python scraper_berlin.py --test
python deduplicate_venues.py
python geocoding_enhancer.py
python check_progress_berlin.py --detailed
```

### Data Analysis
```bash
# View comprehensive statistics
python check_progress_berlin.py --detailed

# Analyze specific backup
# (manually load JSON and analyze in Python)
```

This unified system provides a robust, resumable, and production-ready solution for scraping and managing Berlin venue data with a modern web interface.