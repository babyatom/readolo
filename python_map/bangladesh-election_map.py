import folium
import pandas as pd
import json
from branca.element import Element

# --- 1. SETTINGS & COLORS ---
division_colors = {
    'Dhaka': '#1a1a1a', 'Chattogram': '#CC0000', 'Rajshahi': '#008573',
    'Khulna': '#D4A017', 'Sylhet': '#6D4C41', 'Barishal': '#2E7D32',
    'Rangpur': '#C62828', 'Mymensingh': '#7B1FA2'
}

# --- 2. LOAD DATA ---
df = pd.read_csv('candidates.csv')
grouped_data = {dist: group.to_dict('records') for dist, group in df.groupby('parent_district')}
dist_to_div = df.set_index('parent_district')['divisions'].to_dict()

with open('Bangladesh_map.geojson', 'r') as f:
    geojson_data = json.load(f)

# --- 3. INITIALIZE MAP (No Tiles, No Zoom Control) ---
m = folium.Map(
    location=[23.8, 90.3],
    zoom_start=6,
    tiles=None,
    zoom_control=False,
    scrollWheelZoom=False
)

# --- 4. PREPARE DATA FOR JS ---
data_json = json.dumps(grouped_data)

# Add GeoJSON to the map
geojson_layer = folium.GeoJson(
    geojson_data,
    style_function=lambda feature: {
        'fillColor': division_colors.get(dist_to_div.get(feature['properties'].get('shapeName'), 'Unknown'), "#808080"),
        'color': 'white',
        'weight': 1,
        'fillOpacity': 0.7
    },
    highlight_function=lambda x: {'fillColor': '#333', 'fillOpacity': 0.9}
).add_to(m)

# --- 5. CUSTOM HTML STRUCTURE ---
# --- 5. UPDATED CUSTOM UI & FIXES ---
custom_ui = f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap" rel="stylesheet">
<style>
    :root {{ --primary: #CC0000; --dark: #1a1a1a; }}
    body {{ font-family: 'Inter', sans-serif; margin: 0; padding: 0; background: #f8fafc; overflow-x: hidden; }}

    .page-container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}

    header {{ margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 20px; }}
    h1 {{ font-size: 32px; font-weight: 800; color: var(--dark); margin: 0; letter-spacing: -1.5px; }}
    h1 span {{ color: var(--primary); font-weight: 300; }}

    /* Containerized Map Fixes */
    #map-wrapper {{
        position: relative;
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
        border: 1px solid #e2e8f0;
        background: white;
        margin-bottom: 20px;
        box-sizing: border-box; /* Fixes the 'cut off' edge */
    }}

    /* This forces the map to fill the container properly */
    .folium-map {{
        height: 550px !important;
        width: 100% !important;
        position: relative !important;
        display: block;
    }}

    /* The Bottom Sheet */
    #details-panel {{
        position: fixed; bottom: -100%; left: 0; right: 0;
        background: white; z-index: 10000; padding: 30px;
        border-top-left-radius: 25px; border-top-right-radius: 25px;
        box-shadow: 0 -10px 40px rgba(0,0,0,0.2);
        transition: bottom 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        max-height: 80vh; overflow-y: auto;
    }}
    #details-panel.active {{ bottom: 0; }}

    .close-btn {{
        float: right; background: #f1f1f1; border: none; padding: 10px 20px;
        border-radius: 30px; cursor: pointer; font-weight: 800; font-size: 12px;
    }}

    /* Mobile adjustments */
    @media (max-width: 600px) {{
        .folium-map {{ height: 450px !important; }}
        .page-container {{ padding: 15px; }}
    }}
</style>
<div id="nav-placeholder"></div>
<div class="page-container">
    <header>
        <div style="background: var(--primary); color: white; padding: 4px 12px; font-size: 10px; font-weight: 800; width: fit-content; margin-bottom: 10px;">INTELLIGENCE</div>
        <h1>READ<span>OLO.</span></h1>
        <p>Bangladesh 2026 Election Tracker: Advanced Regional Mapping</p>
    </header>

    <div id="map-wrapper">
        </div>

    <div style="padding: 15px; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; font-size: 13px; color: #64748b; line-height: 1.5;">
        <strong>Navigation:</strong> Use one finger to scroll the page. Use <b>two fingers</b> to move the map. Tap any district to view candidates.
    </div>
</div>

<div id="details-panel">
    <button class="close-btn" onclick="closePanel()">CLOSE</button>
    <div id="panel-body"></div>
</div>

<div id="footer-placeholder"></div>
<script src="../script.js"></script>

<script>
    const electionData = {data_json};

    function closePanel() {{
        document.getElementById('details-panel').classList.remove('active');
    }}

    document.addEventListener("DOMContentLoaded", function() {{
        const mapElement = document.querySelector('.folium-map');
        const mapObject = window[mapElement.id];
        const wrapper = document.getElementById('map-wrapper');

        // Move map into wrapper
        wrapper.appendChild(mapElement);

        // --- THE CENTERING & OVERFLOW FIX ---
        setTimeout(() => {{
            mapObject.invalidateSize(); // Forces map to re-check its container size

            // Re-center and zoom to the Bangladesh shapes
            const geoLayer = window['{geojson_layer.get_name()}'];
            if (geoLayer) {{
                mapObject.fitBounds(geoLayer.getBounds(), {{ padding: [20, 20] }});
            }}
        }}, 300);

        // Two-finger scroll for mobile
        if (L.Browser.mobile) {{
            mapObject.dragging.disable();
            mapObject.on('touchstart', function(e) {{
                if (e.originalEvent.touches.length >= 2) mapObject.dragging.enable();
                else mapObject.dragging.disable();
            }});
        }}

        // Click detection for shapes
        const geoLayer = window['{geojson_layer.get_name()}'];
        geoLayer.on('click', function(e) {{
            const distName = e.layer.feature.properties.shapeName;
            const seats = electionData[distName] || [];
            showDetails(distName, seats);
            L.DomEvent.stopPropagation(e);
        }});
    }});

    function showDetails(distName, seats) {{
        const panel = document.getElementById('details-panel');
        const body = document.getElementById('panel-body');

        let html = `<h2 style="margin-top:0; font-size:26px; letter-spacing:-1px;">${{distName}}</h2>`;

        if(seats.length === 0) {{
            html += "<p>Candidate verification in progress...</p>";
        }} else {{
            seats.forEach(seat => {{
                html += `
                <div style="margin-bottom: 25px; border-top: 1px solid #eee; padding-top: 15px;">
                    <div style="color:var(--primary); font-weight:800; text-transform:uppercase; font-size:12px; margin-bottom:10px;">${{seat.constituency}}</div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px;">`;

                for(let i=1; i<=15; i++) {{
                    const name = seat['Candidate_' + i];
                    const party = seat['Party_' + i] || '';
                    const symbol = seat['Symbol_' + i] || '';
                    const img = seat['Img_' + i] || 'https://placehold.co/100x100?text=Marka';
                    if(name && name !== 'N/A') {{
                        html += `
                        <div style="text-align:center; border:1px solid #f1f5f9; padding:8px; border-radius:8px;">
                            <img src="${{img}}" style="width:50px; height:50px; object-fit:contain; margin-bottom:5px;">
                            <div style="font-size:10px; font-weight:700; color:var(--dark);">${{name}}</div>
                            <div style="font-size:8px; color:#666; margin-top:2px;">${{party}}</div>
                            ${{symbol ? `<div style="font-size:7px; color:#888; margin-top:2px;">${{symbol}}</div>` : ''}}
                        </div>`;
                    }}
                }}
                html += `</div></div>`;
            }});
        }}

        body.innerHTML = html;
        panel.classList.add('active');
    }}
</script>
"""

# --- 6. ASSEMBLE ---
m.get_root().html.add_child(Element(custom_ui))
m.save("bangladesh-election-2026.html")
