# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Readolo is a full-stack consulting website and election intelligence platform for Bangladesh 2026 elections. It combines:
- A corporate consulting website (static HTML/CSS/JS)
- A Python-based election mapping system using Folium
- A web scraper for candidate data collection

## Project Structure

```
readolo/
├── readolo_website/           # Main website (static HTML/CSS/JS)
│   ├── components/            # Reusable nav.html and footer.html
│   ├── insights/              # Election intelligence section
│   └── services/              # Service detail pages (8 pages)
├── python_map/                # Election mapping generation
│   ├── bangladesh-election_map.py    # Main Folium script
│   ├── candidates.csv                # Candidate data
│   └── Bangladesh_map.geojson        # District boundaries
└── candidate_scraper/         # Wikipedia scraper for candidate data
```

## Commands

### Website Development
```bash
# Serve website locally (no build required)
cd readolo_website && python -m http.server 8000
```

### Election Map Generation
```bash
cd python_map && python bangladesh-election_map.py
# Generates: bangladesh-election-2026.html (self-contained 2.4MB file)
```

### Candidate Scraping
```bash
cd candidate_scraper && python candidate_scrape.py
# Requires: links.csv with Wikipedia URLs
# Generates: detailed_election_results.csv
```

### Python Dependencies
```
folium pandas beautifulsoup4 requests branca
```

## Architecture

### Website (readolo_website/)
- **No build tools** - pure static HTML/CSS/JS
- **Component injection** - `script.js` injects nav.html and footer.html via JavaScript on DOMContentLoaded
- **CSS variables** - `--abc-dark` (#1a1a1a), `--abc-red` (#CC0000), `--abc-silver` (#f4f4f4)
- **Responsive** - mobile-first design with 768px breakpoint

### Election Map (python_map/)
**Data flow:**
1. Load `candidates.csv` (candidate names, parties, images, constituencies)
2. Load `Bangladesh_map.geojson` (district boundary polygons)
3. Group by `parent_district` and `divisions`
4. Generate Folium map with 8 division-colored GeoJSON layers
5. Output self-contained HTML with embedded interactive map

**Division color scheme:**
- Dhaka: #1a1a1a, Chattogram: #CC0000, Rajshahi: #008573
- Khulna: #D4A017, Sylhet: #6D4C41, Barishal: #2E7D32
- Rangpur: #C62828, Mymensingh: #7B1FA2

### Web Scraper (candidate_scraper/)
- Scrapes Wikipedia election tables
- 1-second delay between requests (rate limiting)
- Requires User-Agent header (403 without it)

## Critical Implementation Notes

1. **Map regeneration required** - After editing `candidates.csv`, run the Python script to regenerate the HTML map
2. **Mobile map interaction** - Two-finger touch to pan (single finger scrolls page)
3. **Map sizing** - Call `mapObject.invalidateSize()` after DOM manipulation
4. **Generated map is committed** - The 2.4MB `bangladesh-election-2026.html` is checked into git
5. **No package.json** - This is Python + HTML/CSS/JS, not Node-based

## Data Schema

**candidates.csv columns:**
- Districts, District Name Clean, Electoral Name Clean, constituency, url
- parent_district, divisions
- Candidate_1-5, Party_1-5, Img_1-5 (up to 5 candidates per constituency)
