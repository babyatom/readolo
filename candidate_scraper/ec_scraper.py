"""
Bangladesh Election Commission (EC) Portal Scraper
Scrapes candidate data for the 13th National Parliament Election (2026)
from http://103.183.38.66

Requirements:
- VPN connection to Bangladesh (portal only accessible from BD IPs)
- pip install requests pandas beautifulsoup4
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import json
import time
import re
import sys
from pathlib import Path

# --- CONFIGURATION ---
BASE_URL = "http://103.183.38.66"
ELECTION_ID = 478  # 13th National Parliament Election (Feb 12, 2026)
CANDIDATE_TYPE = 1  # Member of Parliament
STATUS_ID = 11  # 11=Finalized candidates (চূড়ান্ত)
OUTPUT_FILE = "../python_map/candidates.csv"
MAPPING_FILE = "district_division_mapping.json"
SYMBOL_IMAGES_FILE = "symbol_images.json"  # Symbol name → image URL mapping
DELAY_SECONDS = 0.5  # Delay between API calls
MAX_CANDIDATES = 15  # Max candidates per constituency (actual max is 14)

# District name fixes to match GeoJSON spellings
DISTRICT_NAME_FIXES = {
    'Brahmanbaria': 'Brahamanbaria',
    'Moulvibazar': 'Maulvibazar',
    'Netrokona': 'Netrakona'
}
# ---------------------


def check_connection():
    """Check if EC portal is accessible (requires BD VPN)"""
    try:
        response = requests.get(BASE_URL, timeout=10)
        if response.status_code == 200:
            print("✓ Connected to EC portal")
            return True
    except Exception as e:
        print(f"✗ Cannot connect to EC portal: {e}")
        print("  Make sure you have VPN connected to Bangladesh")
        return False
    return False


def load_division_mapping():
    """Load district-to-division mapping"""
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create reverse lookup: district_id -> (division_name, district_name_en)
    mapping = {}
    for division_name, division_data in data['divisions'].items():
        for district_id, district_name in division_data['districts'].items():
            mapping[district_id] = {
                'division': division_name,
                'district_en': district_name
            }
    return mapping


def load_symbol_images():
    """Load symbol name to image URL mapping (for major parties only)"""
    try:
        with open(SYMBOL_IMAGES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {SYMBOL_IMAGES_FILE} not found, using candidate photos")
        return {}


def get_symbol_image(symbol_name, symbol_images):
    """Get image URL for a symbol name, returns empty string if not found"""
    import unicodedata
    if not symbol_name:
        return ''
    # Try direct match first
    if symbol_name in symbol_images:
        return symbol_images[symbol_name]
    # Try normalized match (handles Bengali Unicode variations)
    norm_name = unicodedata.normalize('NFC', symbol_name)
    for key, url in symbol_images.items():
        if unicodedata.normalize('NFC', key) == norm_name:
            return url
    return ''


def get_districts():
    """Fetch all districts for the 2026 election"""
    url = f"{BASE_URL}/election-settings/get-election-zilla"
    params = {'electionID': ELECTION_ID}

    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    return data.get('zillas', [])


def get_constituencies(zilla_id):
    """Fetch constituencies for a given district"""
    url = f"{BASE_URL}/election/get-setting-constituency"
    params = {
        'zillaID': zilla_id,
        'electionID': ELECTION_ID
    }

    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    return data.get('constituencies', [])


def get_candidates(zilla_id, constituency_id):
    """Fetch candidates for a given constituency (returns HTML)"""
    url = f"{BASE_URL}/get/candidate/data"
    params = {
        'election_id': ELECTION_ID,
        'zilla_id': zilla_id,
        'constituency_id': constituency_id,
        'candidate_type': CANDIDATE_TYPE,
    }
    if STATUS_ID:
        params['status_id'] = STATUS_ID

    response = requests.get(url, params=params, timeout=30)
    return response.text


def parse_candidates_html(html):
    """Parse HTML table rows to extract candidate data including symbol names"""
    soup = BeautifulSoup(html, 'html.parser')
    candidates = []

    for row in soup.find_all('tr'):
        # Only get <td> elements (serial number is <th>)
        cols = row.find_all('td')
        if len(cols) >= 4:
            # Column structure (td only): [0]=Name, [1]=Photo, [2]=Party, [3]=Symbol
            name = cols[0].get_text(strip=True)
            party = cols[2].get_text(strip=True)
            symbol = cols[3].get_text(strip=True)  # NEW: Election symbol name

            # Extract image URL (candidate photo)
            img_tag = cols[1].find('img')
            img_url = img_tag.get('src', '') if img_tag else ''

            if name:
                candidates.append({
                    'name': name,
                    'party': party,
                    'symbol': symbol,  # NEW
                    'img': img_url
                })

    return candidates


def bengali_to_english_number(bn_str):
    """Convert Bengali numerals to English"""
    bn_digits = '০১২৩৪৫৬৭৮৯'
    en_digits = '0123456789'

    result = bn_str
    for bn, en in zip(bn_digits, en_digits):
        result = result.replace(bn, en)
    return result


def parse_constituency_name(bn_name):
    """
    Parse Bengali constituency name like 'ঢাকা-১' to 'Dhaka-1'
    Returns tuple: (district_bn, number)
    """
    # Match pattern: text followed by dash and Bengali/English numbers
    match = re.match(r'(.+)-([০-৯0-9]+)', bn_name)
    if match:
        district_bn = match.group(1)
        number = bengali_to_english_number(match.group(2))
        return district_bn, number
    return bn_name, ''


def main():
    print("=" * 60)
    print("Bangladesh EC Portal Candidate Scraper")
    print("13th National Parliament Election (Feb 12, 2026)")
    print("=" * 60)

    # Check connection
    if not check_connection():
        sys.exit(1)

    # Load division mapping
    print("\nLoading district-division mapping...")
    division_mapping = load_division_mapping()
    print(f"✓ Loaded mapping for {len(division_mapping)} districts")

    # Load symbol images mapping
    print("\nLoading symbol images mapping...")
    symbol_images = load_symbol_images()
    print(f"✓ Loaded {len(symbol_images)} symbol image mappings")

    # Fetch all districts
    print("\nFetching districts...")
    districts = get_districts()
    print(f"✓ Found {len(districts)} districts")

    # Collect all data
    all_rows = []
    total_constituencies = 0
    total_candidates = 0

    for i, district in enumerate(districts):
        zilla_id = district['zillaID']
        zilla_name_bn = district['zilla_name']

        # Get division and English name from mapping
        mapping = division_mapping.get(zilla_id, {})
        division = mapping.get('division', 'Unknown')
        district_en = mapping.get('district_en', zilla_name_bn)

        # Apply district name fixes to match GeoJSON
        district_en = DISTRICT_NAME_FIXES.get(district_en, district_en)

        print(f"\n[{i+1}/{len(districts)}] {district_en} ({division})")

        # Fetch constituencies for this district
        constituencies = get_constituencies(zilla_id)
        print(f"  Found {len(constituencies)} constituencies")

        for const in constituencies:
            const_id = const['constituencyID']
            const_name_bn = const['constituency_name']

            # Parse constituency name
            _, const_num = parse_constituency_name(const_name_bn)
            constituency_code = f"{district_en}-{const_num}" if const_num else const_name_bn

            # Fetch candidates
            time.sleep(DELAY_SECONDS)
            html = get_candidates(zilla_id, const_id)
            candidates = parse_candidates_html(html)

            print(f"    {constituency_code}: {len(candidates)} candidates")
            total_constituencies += 1
            total_candidates += len(candidates)

            # Build row for CSV
            row = {
                'Districts': zilla_name_bn,
                'District Name Clean': district_en,
                'Electoral Name Clean': const_name_bn,
                'constituency': constituency_code,
                'url': '',  # Can add Wikipedia URL if needed
                'parent_district': district_en,
                'divisions': division,
            }

            # Add candidates (up to MAX_CANDIDATES)
            for j in range(MAX_CANDIDATES):
                if j < len(candidates):
                    party = candidates[j]['party']
                    symbol = candidates[j].get('symbol', '')
                    # Use symbol image if available, otherwise use candidate photo
                    symbol_img = get_symbol_image(symbol, symbol_images)
                    img_url = symbol_img if symbol_img else candidates[j]['img']

                    row[f'Candidate_{j+1}'] = candidates[j]['name']
                    row[f'Party_{j+1}'] = party
                    row[f'Symbol_{j+1}'] = symbol  # NEW: Symbol name
                    row[f'Img_{j+1}'] = img_url
                else:
                    row[f'Candidate_{j+1}'] = ''
                    row[f'Party_{j+1}'] = ''
                    row[f'Symbol_{j+1}'] = ''  # NEW
                    row[f'Img_{j+1}'] = ''

            all_rows.append(row)

    # Create DataFrame with proper column order
    columns = [
        'Districts', 'District Name Clean', 'Electoral Name Clean',
        'constituency', 'url', 'parent_district', 'divisions',
    ]
    # Add candidate columns dynamically (including Symbol)
    for i in range(1, MAX_CANDIDATES + 1):
        columns.extend([f'Candidate_{i}', f'Party_{i}', f'Symbol_{i}', f'Img_{i}'])

    df = pd.DataFrame(all_rows, columns=columns)

    # Save to CSV
    output_path = Path(__file__).parent / OUTPUT_FILE
    df.to_csv(output_path, index=False, encoding='utf-8')

    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    print(f"Total constituencies: {total_constituencies}")
    print(f"Total candidates: {total_candidates}")
    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()
