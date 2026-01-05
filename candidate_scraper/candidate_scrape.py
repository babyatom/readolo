import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# --- CONFIGURATION ---
INPUT_FILE = 'links.csv'
OUTPUT_FILE = 'detailed_election_results.csv'
URL_COLUMN = 'url'  # <--- Changed this to match your CSV output
# ---------------------

def scrape_election_table(url):
    try:
        # Wikipedia requires a User-Agent to avoid 403 Forbidden errors
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        # Handle links that don't exist
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Target the "General Election 2026" Table
        target_table = None
        for caption in soup.find_all('caption'):
            if "General Election 2026" in caption.get_text():
                target_table = caption.find_parent('table')
                break
        
        if not target_table:
            return []

        candidates_data = []
        # 2. Iterate through rows (skipping header)
        for row in target_table.find_all('tr')[1:]:
            cols = row.find_all(['td', 'th'])
            
            # Identify footer rows to stop scraping
            row_text = row.get_text(strip=True)
            if any(term in row_text for term in ["Majority", "Turnout", "Registered"]):
                break
            
            # Based on your HTML: 
            # cols[1] is Party, cols[2] is Candidate
            if len(cols) >= 3:
                party = cols[1].get_text(strip=True)
                candidate = cols[2].get_text(strip=True)
                
                if party and candidate:
                    candidates_data.extend([candidate, party])
        
        return candidates_data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# --- Main Logic ---

# 1. Load your CSV
df = pd.read_csv(INPUT_FILE)

# Clean column names just in case of hidden spaces
df.columns = df.columns.str.strip()

all_results = []

print(f"Starting scrape for {len(df)} rows...")

for index, row in df.iterrows():
    # Make sure we use the correct column name here
    url = row[URL_COLUMN]
    
    print(f"[{index+1}/{len(df)}] Scraping: {url}")
    
    scraped_info = scrape_election_table(url)
    
    # Keep original data + append new scraped columns
    combined_row = row.tolist() + scraped_info
    all_results.append(combined_row)
    
    # Gentle delay to be kind to Wikipedia's servers
    time.sleep(1)

# 2. Build final DataFrame
final_df = pd.DataFrame(all_results)

# 3. Re-apply original headers + generic headers for new data
original_headers = df.columns.tolist()
extra_cols_count = len(final_df.columns) - len(original_headers)
new_headers = original_headers + [f"Extra_{i}" for i in range(extra_cols_count)]
final_df.columns = new_headers

# 4. Save
final_df.to_csv(OUTPUT_FILE, index=False)
print(f"\nSuccess! Saved results to {OUTPUT_FILE}")
