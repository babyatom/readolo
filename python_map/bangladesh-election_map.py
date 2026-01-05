import folium
import pandas as pd
import json
from branca.element import IFrame, Element

# --- 1. SETTINGS & COLORS (READOLO Brand Integration) ---
division_colors = {
    'Dhaka': '#1a1a1a', 'Chattogram': '#CC0000', 'Rajshahi': '#008573',
    'Khulna': '#D4A017', 'Sylhet': '#6D4C41', 'Barishal': '#2E7D32',
    'Rangpur': '#C62828', 'Mymensingh': '#7B1FA2'
}

# --- 2. LOAD DATA ---
# This part stays exactly as you had it to ensure your CSV connects
df = pd.read_csv('candidates.csv')
grouped_data = {dist: group.to_dict('records') for dist, group in df.groupby('parent_district')}
dist_to_div = df.set_index('parent_district')['divisions'].to_dict()

with open('Bangladesh_map.geojson', 'r') as f:
    geojson_data = json.load(f)

# --- 3. MODAL DESIGN (READOLO Branded Popups) ---
def get_modal_html(dist_name, seats):
    seat_html = ""
    for seat in seats:
        candidates_block = ""
        for i in range(1, 6):
            name = seat.get(f'Candidate_{i}', 'N/A')
            img_url = seat.get(f'Img_{i}', 'https://placehold.co/300x300/cccccc/969696.png?text=Marka')
            candidates_block += f"""
            <div style="text-align:center; padding:10px; border:1px solid #eee; background:#fff;">
                <img src="{img_url}" style="width:50px; height:50px; border-radius:50%; object-fit:cover; margin-bottom:5px;">
                <div style="font-size:10px; font-weight:700; color:#1a1a1a; line-height:1.2;">{name}</div>
            </div>"""

        seat_html += f"""
        <div style="margin-bottom:20px; border-top: 4px solid #1a1a1a; padding-top:10px;">
            <div style="font-size:13px; font-weight:800; text-transform:uppercase; color:#CC0000; margin-bottom:8px;">
                {seat['constituency']}
            </div>
            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px;">
                {candidates_block}
            </div>
        </div>"""

    return f"""<div style="font-family:'Inter', sans-serif; min-width:320px; max-height:400px; overflow-y:auto; padding-right:10px;">
                <h2 style="font-size:22px; font-weight:800; letter-spacing:-1px; margin:0 0 15px 0; color:#1a1a1a;">{dist_name}</h2>
                {seat_html}
               </div>"""

# --- 4. BUILD THE MAP & INJECT DATA ---
m = folium.Map(location=[23.8, 90.3], zoom_start=7, tiles='CartoDB positron')

for feature in geojson_data['features']:
    dist_name = feature['properties'].get('shapeName', 'Unknown')
    seats = grouped_data.get(dist_name, [])
    div_name = dist_to_div.get(dist_name, "Unknown")
    fill_color = division_colors.get(div_name, "#808080")

    if seats:
        html_content = get_modal_html(dist_name, seats)
        popup_html = folium.Html(html_content, script=True)
        popup = folium.Popup(popup_html, max_width='90%')
    else:
        popup = folium.Popup(f"Data pending for {dist_name}")

    folium.GeoJson(
        feature,
        tooltip=f"<b>{dist_name}</b>",
        popup=popup,
        style_function=lambda x, fc=fill_color: {
            'fillColor': fc, 'color': 'white', 'weight': 1, 'fillOpacity': 0.7
        },
        highlight_function=lambda x: {'fillColor': '#333', 'fillOpacity': 0.9}
    ).add_to(m)

# --- 5. THE SIDEBAR & CSS OVERRIDE ---
sidebar_content = """
<div id="sidebar">
    <div class="badge">Intelligence</div>
    <h1>READ<span>OLO.</span></h1>
    <h2>Bangladesh 2026 Election Tracker</h2>
    <p>Advanced election insights and verified candidate mapping for the 2026 cycle.</p>

    <div style="display: flex; gap: 10px; margin: 20px 0;">
        <div class="stats-card" style="flex:1;">
            <div class="stats-val">300</div>
            <div class="stats-label">Total Seats</div>
        </div>
        <div class="stats-card" style="flex:1; border-left-color: #CC0000;">
            <div class="stats-val">64</div>
            <div class="stats-label">Districts</div>
        </div>
    </div>

    <div class="division-legend">
        <h4 class="section-title">Regional Divisions</h4>
        <div class="legend-grid">
            <div class="legend-item"><span style="background: #1a1a1a;"></span> Dhaka</div>
            <div class="legend-item"><span style="background: #CC0000;"></span> Chattogram</div>
            <div class="legend-item"><span style="background: #008573;"></span> Rajshahi</div>
            <div class="legend-item"><span style="background: #D4A017;"></span> Khulna</div>
            <div class="legend-item"><span style="background: #6D4C41;"></span> Sylhet</div>
            <div class="legend-item"><span style="background: #2E7D32;"></span> Barishal</div>
            <div class="legend-item"><span style="background: #C62828;"></span> Rangpur</div>
            <div class="legend-item"><span style="background: #7B1FA2;"></span> Mymensingh</div>
        </div>
    </div>

    <div class="footer-text">
        © 2026 READOLO Consulting. Unauthorized reproduction of data prohibited.
    </div>
</div>
"""

layout_css = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
<style>
    body { display: flex; flex-direction: row; margin: 0; height: 100vh; width: 100vw; overflow: hidden; font-family: 'Inter', sans-serif; }
    #sidebar {
        width: 380px; height: 100vh; background: white; box-shadow: 10px 0 30px rgba(0,0,0,0.05);
        z-index: 9999; padding: 40px 30px; display: flex; flex-direction: column; box-sizing: border-box; overflow-y: auto;
    }
    .folium-map { flex-grow: 1 !important; height: 100% !important; position: relative !important; }

    h1 { font-size: 28px; font-weight: 800; color: #1a1a1a; letter-spacing: -1.5px; margin: 15px 0; line-height: 1; }
    h1 span { color: #CC0000; font-weight: 300; }
    .badge { background: #CC0000; color: white; padding: 4px 12px; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; width: fit-content; }
    .stats-card { background: #f4f4f4; border-left: 4px solid #1a1a1a; padding: 20px; }
    .stats-val { font-size: 24px; font-weight: 800; color: #1a1a1a; }
    .stats-label { font-size: 10px; font-weight: 700; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .section-title { font-size: 12px; border-left: 3px solid #CC0000; padding-left: 10px; text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin-bottom: 15px; }
    .legend-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .legend-item { font-size: 11px; font-weight: 600; display: flex; align-items: center; }
    .legend-item span { width: 12px; height: 12px; margin-right: 8px; border-radius: 2px; }
    .footer-text { margin-top: auto; padding-top: 20px; font-size: 10px; color: #ccc; border-top: 1px solid #eee; }

    /* Fix Leaflet Popup Scrollbar */
    .leaflet-popup-content { margin: 15px; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #ddd; border-radius: 10px; }

    @media (max-width: 768px) {
        body { flex-direction: column; overflow: auto; }
        #sidebar { width: 100%; height: auto; min-height: fit-content; padding: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .folium-map { height: 60vh !important; width: 100% !important; }
    }
</style>
"""

# --- 6. FINAL ASSEMBLY ---
m.get_root().header.add_child(Element(layout_css))
m.get_root().html.add_child(Element(sidebar_content))

m.save("bangladesh-election-2026.html")
