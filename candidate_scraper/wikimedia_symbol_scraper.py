"""
Wikimedia Commons Symbol Image Scraper
Searches for Bangladesh election symbol images and builds symbol_images.json
"""

import requests
import json
import time
from pathlib import Path

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OUTPUT_FILE = "symbol_images.json"

# Bengali symbol name -> English name for searching
# Based on official EC symbols list
SYMBOLS = {
    # Major parties (already have images)
    "ধানের শীষ": "sheaf of paddy BNP Bangladesh",
    "দাঁড়িপাল্লা": "scales balance Jamaat Bangladesh election",
    "লাঙ্গল": "plough Jatiya Party Bangladesh",
    "হাতপাখা": "hand fan Islami Andolan Bangladesh",
    "দেওয়াল ঘড়ি": "wall clock Khelafat Majlis Bangladesh",
    "কাস্তে": "sickle Communist Party Bangladesh",

    # Common symbols needing images
    "ট্রাক": "truck vehicle",
    "ফুটবল": "football soccer ball",
    "আপেল": "apple fruit",
    "ঘোড়া": "horse",
    "মই": "ladder",
    "রিকশা": "rickshaw Bangladesh",
    "কাঁচি": "scissors",
    "মোটর সাইকেল": "motorcycle",
    "ঈগল": "eagle bird",
    "শাপলা কলি": "water lily shapla Bangladesh",
    "তারা": "star",
    "আম": "mango fruit",
    "ডাব": "coconut green",
    "চেয়ার": "chair",
    "হরিণ": "deer",
    "কলম": "pen",
    "ছড়ি": "walking stick cane",
    "মোমবাতি": "candle",
    "নারিকেল গাছ": "coconut palm tree",
    "টেলিভিশন": "television TV",
    "হাতুড়ি": "hammer",
    "কবুতর": "pigeon dove",
    "নৌকা": "boat",
    "বই": "book",
    "টর্চ": "torch flashlight",
    "ময়ূর": "peacock",
    "সূর্যমুখী ফুল": "sunflower",
    "গোলাপ ফুল": "rose flower",
    "আনারস": "pineapple",
    "হাতি": "elephant",
    "উট": "camel",
    "সিংহ": "lion",
    "বাঘ": "tiger",
    "গরু": "cow cattle",
    "ছাতা": "umbrella",
    "গাছ": "tree",
    "চাবি": "key",
    "তালা": "padlock lock",
    "ঘড়ি": "watch clock",
    "কুড়াল": "axe",
    "বেলচা": "shovel spade",
    "হাঁস": "duck",
    "মোরগ": "rooster chicken",
    "কাক": "crow",
    "চিল": "kite bird",
    "বাজ": "hawk falcon",
    "পেঁচা": "owl",
    "টিয়া": "parrot",
    "মাছ": "fish",
    "কুমির": "crocodile",
    "সাপ": "snake",
    "কচ্ছপ": "turtle tortoise",
    "ব্যাঙ": "frog",
    "প্রজাপতি": "butterfly",
    "মৌমাছি": "bee honeybee",
    "পিঁপড়া": "ant",
    "জাহাজ": "ship boat",
    "বিমান": "airplane aircraft",
    "ট্রেন": "train locomotive",
    "বাস": "bus",
    "মোটরগাড়ি (কার)": "car automobile",
    "সাইকেল": "bicycle cycle",
    "হেলিকপ্টার": "helicopter",
    "রকেট": "rocket",
    "কম্পিউটার": "computer",
    "মোবাইল ফোন": "mobile phone cellphone",
    "রেডিও": "radio",
    "ক্যামেরা": "camera",
    "ঘণ্টা": "bell",
    "ড্রাম": "drum",
    "গিটার": "guitar",
    "বাঁশি": "flute",
    "তবলা": "tabla drum",
    "ফুলদানি": "flower vase",
    "চশমা": "glasses spectacles",
    "জুতা": "shoe",
    "টুপি": "hat cap",
    "ব্যাগ": "bag",
    "বালতি": "bucket pail",
    "কলসি": "pitcher water pot",
    "থালা": "plate dish",
    "গ্লাস": "glass tumbler",
    "চামচ": "spoon",
    "কাপ": "cup",
    "চায়ের কেটলি": "teapot kettle",
    "লন্ঠন": "lantern lamp",
    "বাতি": "lamp light",
    "পাখা": "fan ceiling fan",
    "সেলাই মেশিন": "sewing machine",
    "তুলা দাঁড়ি": "cotton scale balance",
    "নোঙ্গর": "anchor",
    "চাকা": "wheel",
    "স্বতন্ত্র": "",  # Independent - no symbol
}

# Known working URLs (manually verified)
KNOWN_URLS = {
    "ধানের শীষ": "https://upload.wikimedia.org/wikipedia/commons/c/c9/Bangladesh_Nationalist_Party_election_symbol_Black_%26_White.svg",
    "দাঁড়িপাল্লা": "https://upload.wikimedia.org/wikipedia/commons/f/f2/Daripalla.png",
    "লাঙ্গল": "https://upload.wikimedia.org/wikipedia/commons/b/b7/Symbol_of_Jatiya_Party.jpg",
    "হাতপাখা": "https://upload.wikimedia.org/wikipedia/commons/0/01/Symbol_of_Islami_Andolan_Bangladesh.svg",
    "দেওয়াল ঘড়ি": "https://upload.wikimedia.org/wikipedia/commons/c/c6/Wall_clock%2C_Election_Symbol_of_the_Khelafat_Majlis.png",
    "কাস্তে": "https://upload.wikimedia.org/wikipedia/commons/6/68/Election_Symbol_of_the_Communist_Party_of_Bangladesh.png",
    "স্বতন্ত্র": "",
}


def search_commons(query, limit=5):
    """Search Wikimedia Commons for images"""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{query} filetype:bitmap OR filetype:drawing",
        "srnamespace": 6,  # File namespace
        "srlimit": limit,
        "format": "json"
    }
    try:
        response = requests.get(COMMONS_API, params=params, timeout=10)
        data = response.json()
        return data.get("query", {}).get("search", [])
    except Exception as e:
        print(f"  Error searching: {e}")
        return []


def get_image_url(title):
    """Get direct URL for a Commons file"""
    params = {
        "action": "query",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json"
    }
    try:
        response = requests.get(COMMONS_API, params=params, timeout=10)
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            imageinfo = page.get("imageinfo", [])
            if imageinfo:
                return imageinfo[0].get("url", "")
    except Exception as e:
        print(f"  Error getting URL: {e}")
    return ""


def main():
    print("=" * 60)
    print("Wikimedia Commons Symbol Image Scraper")
    print("=" * 60)

    # Start with known URLs
    symbol_images = dict(KNOWN_URLS)

    # Search for remaining symbols
    for bengali, english in SYMBOLS.items():
        if bengali in symbol_images and symbol_images[bengali]:
            print(f"✓ {bengali}: Already have URL")
            continue

        if not english:  # Skip empty (like স্বতন্ত্র)
            symbol_images[bengali] = ""
            continue

        print(f"\nSearching: {bengali} ({english})...")
        results = search_commons(english)

        if results:
            # Get the first result's URL
            title = results[0].get("title", "")
            url = get_image_url(title)
            if url:
                print(f"  Found: {title}")
                symbol_images[bengali] = url
            else:
                print(f"  No URL for: {title}")
                symbol_images[bengali] = ""
        else:
            print(f"  No results found")
            symbol_images[bengali] = ""

        time.sleep(0.5)  # Rate limiting

    # Save results
    output_path = Path(__file__).parent / OUTPUT_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(symbol_images, f, ensure_ascii=False, indent=2)

    # Count results
    found = sum(1 for v in symbol_images.values() if v)
    total = len(symbol_images)

    print("\n" + "=" * 60)
    print(f"COMPLETE: {found}/{total} symbols have images")
    print(f"Output saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
