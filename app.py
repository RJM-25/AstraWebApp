import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASTRA 2026 — Live Conference Portal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Session State ────────────────────────────────────────────────────────────
if "theme"         not in st.session_state: st.session_state.theme         = "dark"
if "admin_logged"  not in st.session_state: st.session_state.admin_logged  = False
if "edit_history"  not in st.session_state: st.session_state.edit_history  = {}   # {sheet: [df, df, ...]}
if "working_dfs"   not in st.session_state: st.session_state.working_dfs   = {}   # {sheet: df}

# ─── Theme Palettes ───────────────────────────────────────────────────────────
DARK = {
    "bg":      "#07111f",
    "bg2":     "#0d1c2e",
    "bg3":     "#122033",
    "card":    "#0f1e30",
    "border":  "rgba(100,180,255,0.12)",
    "text":    "#e8f4ff",
    "muted":   "#6a90b0",
    "accent":  "#3b9eff",
    "head":    "#ffffff",
    "tagbg":   "rgba(59,158,255,0.12)",
    "tagc":    "#3b9eff",
    "errbg":   "rgba(239,68,68,0.08)",
    "errbr":   "rgba(239,68,68,0.25)",
    "errc":    "#f87171",
}
LIGHT = {
    "bg":      "#f0f5fb",
    "bg2":     "#e4eef8",
    "bg3":     "#d8e8f5",
    "card":    "#ffffff",
    "border":  "rgba(10,60,120,0.14)",
    "text":    "#1a2e44",
    "muted":   "#5a7a9a",
    "accent":  "#1565c0",
    "head":    "#0a1e35",
    "tagbg":   "rgba(21,101,192,0.08)",
    "tagc":    "#1565c0",
    "errbg":   "rgba(180,0,0,0.06)",
    "errbr":   "rgba(180,0,0,0.2)",
    "errc":    "#b91c1c",
}

T = DARK if st.session_state.theme == "dark" else LIGHT

# ─── Venue & Campus Location Data ────────────────────────────────────────────
# Replace 0.000000 placeholder coords with real lat/lng for each location.
# Google Maps walking directions will open automatically when a user taps a venue.

VENUE_LOCATIONS = {
    # ── Conference Venues ──────────────────────────────────────────────────
    "MPH":       {"lat": 8.62766395564014, "lng": 77.03340807865644, "label": "Multi Purpose Hall"},
    "Council Hall":   {"lat":      8.62553480488843,"lng":      77.0341056752304, "label": "Aerospace Council Hall"},
    "Admin Council Hall":       {"lat":      8.626079060390595,"lng":      77.03391355711041, "label": "Admin Council Hall"},
    "SAC":    {"lat":      8.627402172318845,"lng":      77.03306660773214, "label": "Annapurna Mess (SAC Cafeteria)"},
    "C106":           {"lat":      8.62553480488843,"lng":      77.0341056752304, "label": "Aerospace Block D4, Room 106"},
    "C104":           {"lat":      8.62553480488843,"lng":      77.0341056752304, "label": "Aerospace Block D4, Room 104"},
    "C103":           {"lat":      8.62553480488843,"lng":      77.0341056752304, "label": "Aerospace Block D4, Room 103"},
    "C102":           {"lat":      8.62553480488843,"lng":      77.0341056752304, "label": "Aerospace Block D4, Room 102"},
    "D4 - CADD Lab":              {"lat":      8.62553480488843,"lng":      77.0341056752304, "label": "Aerospace CADD Lab (Room 204)"},
    "D1 - Computer Instructional Lab":   {"lat":      8.625559189211193,"lng":      77.03218363720273, "label": "Interdisciplinary block  (Room L004A)"},
    "D1 - Language Lab":   {"lat":      8.625559189211193, "lng":      77.03218363720273, "label": "Interdisciplinary block"},
}

CAMPUS_LOCATIONS = [
    # ── Hostels ────────────────────────────────────────────────────────────
    {
        "name":     "Dhanishtha Hostel (keynote speakers, VIPs)",
        "category": "Hostel",
        "icon":     "🏠",
        "lat":      8.628498547939218,
        "lng":      77.03340807865644,
        "note":     "AC Rooms  — warden room at entrance",
    },
    {
        "name":     "Ardhra Hostel (Gents Hostel)",
        "category": "Hostel",
        "icon":     "🏠",
        "lat":      8.62879957094873,
        "lng":      77.03391185300862,
        "note":     "Non-AC Rooms — warden room at entrance",
    },
    {
        "name":     "Dhruva Hostel (Ladies Hostel)",
        "category": "Hostel",
        "icon":     "🏠",
        "lat":      8.628074842821219,
        "lng":      77.03503507204742,
        "note":     "Non-AC Rooms — warden room at entrance",
    },
    # ── Mess / Cafeteria ───────────────────────────────────────────────────
    {
        "name":     "Annapurna Mess (SAC Cafeteria)",
        "category": "Mess",
        "icon":     "🍽️",
        "lat":      8.627402172318845,
        "lng":      77.03306660773214,
        "note":     "Student delegation dining area · Breakfast 7:15–9 AM · Lunch 12:15–2 PM · Dinner 7:15–9 PM",
    },
    {
        "name":     "Subhiksha Mess",
        "category": "Mess",
        "icon":     "🍽️",
        "lat":      8.627266429718395,
        "lng":      77.03506616776508,
        "note":     "Keynote Speakers and VIP dining area",
    },
    {
        "name":     "Cafeteria",
        "category": "Mess",
        "icon":     "🍽️",
        "lat":      8.628102198055187,
        "lng":      77.03516386928133,
        "note":     "cafeteria near the back gate, open 8 AM–10 PM with snacks and beverages",
    },
    # ── Key Buildings ──────────────────────────────────────────────────────
    {
        "name":     "Multi Purpose Hall (MPH)",
        "category": "Venue",
        "icon":     "🏛️",
        "lat":      8.62766395564014,
        "lng":      77.03340807865644,
        "note":     "Main conference venue — Keynotes Sessions",
    },
    {
        "name":     "Admin Council Hall",
        "category": "Venue",
        "icon":     "🏛️",
        "lat":      8.626079060390595,
        "lng":      77.03391355711041,
        "note":     "Paper Presentation Session",
    },
    {
        "name":     "Aerospace Block D4",
        "category": "Venue",
        "icon":     "🏛️",
        "lat":      8.62553480488843,
        "lng":      77.0341056752304,
        "note":     "Paper Presentation Session & MATLAB Workshop CADD Lab (Room 204)",
    },
    {
        "name":     "Interdisciplinary Block D1",
        "category": "Venue",
        "icon":     "🏛️",
        "lat":      8.625559189211193,
        "lng":      77.03218363720273,
        "note":     "ANSYS Workshop & Advanced Manufacturing Workshop",
    },
    
    {
        "name":     "Medical Centre",
        "category": "Facility",
        "icon":     "🏥",
        "lat":      8.628961797219286,
        "lng":      77.03432335272213,
        "note":     "Open 24 hrs during conference days",
    },
    {
        "name":     "ATM / Bank",
        "category": "Facility",
        "icon":     "🏧",
        "lat":      8.627542742224874,
        "lng":      77.03495836897278,
        "note":     "Near the back gate",
    },
    {
        "name":     "Main Gate",
        "category": "Facility",
        "icon":     "🚪",
        "lat":      8.627670286284625,
        "lng":      77.03215484977001,
        "note":     "Security check required for entry/exit during conference days",
    },
    {
        "name":     "Back Gate",
        "category": "Facility",
        "icon":     "🚪",
        "lat":      8.627800615138016,
        "lng":      77.03530992433558,
        "note":     "Security check required for entry/exit during conference days",
    },
]

CATEGORY_ORDER = ["Venue", "Hostel", "Mess", "Facility"]

def maps_url(lat, lng, label="Destination"):
    """Google Maps walking directions — current location → destination."""
    if lat == 0.0 and lng == 0.0:
        # Placeholder not filled yet — fall back to a name search
        q = label.replace(" ", "+")
        return f"https://www.google.com/maps/search/?api=1&query={q}"
    return (
        f"https://www.google.com/maps/dir/?api=1"
        f"&destination={lat},{lng}"
        f"&travelmode=walking"
    )

def venue_maps_url(location_str):
    """Look up a venue string in VENUE_LOCATIONS and return a maps URL."""
    loc = location_str.strip()
    # Exact match first, then partial
    if loc in VENUE_LOCATIONS:
        v = VENUE_LOCATIONS[loc]
        return maps_url(v["lat"], v["lng"], v["label"])
    for key, v in VENUE_LOCATIONS.items():
        if key.lower() in loc.lower() or loc.lower() in key.lower():
            return maps_url(v["lat"], v["lng"], v["label"])
    # No match — generic search
    q = loc.replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={q}"

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_conference_data():
    attendees_df = pd.read_excel("conference_data.xlsx", sheet_name="Attendees")
    schedule_df  = pd.read_excel("conference_data.xlsx", sheet_name="Schedule")
    attendees_df["Conference_ID"] = attendees_df["Conference_ID"].astype(str).str.strip()
    # Normalise schedule columns
    schedule_df["Start_Time"] = pd.to_datetime(
        schedule_df["Start_Time"].astype(str), format="mixed"
    ).dt.time
    schedule_df["End_Time"] = pd.to_datetime(
        schedule_df["End_Time"].astype(str), format="mixed"
    ).dt.time
    # Ensure Day column is a clean string
    schedule_df["Day"] = schedule_df["Day"].astype(str).str.strip()
    # Parse Date to a real date object for filtering (day-first format e.g. 12-07-2026 or 12/07/2026)
    parsed_dates = pd.to_datetime(
        schedule_df["Date"], dayfirst=True, errors="coerce"
    )
    schedule_df["_Date_raw"] = parsed_dates.dt.date
    schedule_df["Date"] = parsed_dates.dt.strftime("%b %d, %Y").fillna(
        schedule_df["Date"].astype(str)
    )
    return attendees_df, schedule_df

try:
    attendees_df, schedule_df = load_conference_data()
    DATA_OK = True
except Exception:
    attendees_df = schedule_df = None
    DATA_OK = False

# ─── Poster Discovery ─────────────────────────────────────────────────────────
POSTER_DIR = Path("posters")
SUPPORTED   = {".jpg", ".jpeg", ".png", ".webp"}

def get_posters():
    if not POSTER_DIR.exists():
        return []
    result = []
    for f in sorted(POSTER_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED:
            result.append({
                "path":  f,
                "name":  f.stem.replace("-", " ").replace("_", " ").title(),
                "track": "General",
                "file":  f.name,
            })
    for sub in sorted(POSTER_DIR.iterdir()):
        if sub.is_dir():
            track = sub.name.replace("-", " ").replace("_", " ").title()
            for f in sorted(sub.iterdir()):
                if f.is_file() and f.suffix.lower() in SUPPORTED:
                    result.append({
                        "path":  f,
                        "name":  f.stem.replace("-", " ").replace("_", " ").title(),
                        "track": track,
                        "file":  f.name,
                    })
    return result

POSTERS = get_posters()
TRACKS  = ["All"] + sorted({p["track"] for p in POSTERS})

# ─── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet">

<style>
#MainMenu {{visibility:hidden;}}
footer    {{visibility:hidden;}}
header    {{visibility:hidden;}}
section[data-testid="stSidebar"] {{display:none !important;}}

.stApp,
.stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"]
{{
    background-color: {T['bg']} !important;
    padding-top: 0 !important;
}}
.block-container {{padding: 1rem 0 4rem 0 !important; max-width: 100% !important;}}

html, body, [class*="css"] {{
    font-family: 'Barlow', sans-serif !important;
    color: {T['text']};
}}

.astra-topbar {{
    background: {T['bg2']};
    border-bottom: 0.5px solid {T['border']};
    padding: 0 2.5rem;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    margin-bottom: 0;
}}
.astra-brand {{display:flex; align-items:center; gap:14px;}}
.astra-logo  {{font-family:'Barlow Condensed',sans-serif; font-size:34px; font-weight:700; color:{T['accent']}; line-height:1;}}
.astra-yr    {{font-family:'Barlow Condensed',sans-serif; font-size:14px; color:{T['muted']}; letter-spacing:0.1em;}}
.astra-div   {{width:0.5px; height:30px; background:{T['border']};}}
.astra-full  {{font-size:12px; color:{T['muted']}; line-height:1.4; max-width:210px;}}
.astra-full strong {{color:{T['text']}; font-weight:500; font-size:13px; display:block;}}

.live-badge {{
    display:flex; align-items:center; gap:6px;
    background:rgba(239,68,68,0.10);
    border:0.5px solid rgba(239,68,68,0.28);
    border-radius:20px; padding:5px 14px;
    font-family:'Barlow Condensed',sans-serif;
    font-size:12px; font-weight:600; color:#f87171; letter-spacing:0.1em;
}}
.pulse-dot {{
    width:7px; height:7px; border-radius:50%; background:#ef4444;
    display:inline-block; animation:blink 1.4s ease-in-out infinite;
}}
@keyframes blink {{0%,100%{{opacity:1;}}50%{{opacity:0.25;}}}}

.page-wrap {{padding:1.75rem 2.5rem 0; max-width:980px; margin:0 auto;}}

.sec-head {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:12px; font-weight:600; letter-spacing:0.14em;
    text-transform:uppercase; color:{T['muted']};
    margin:1.5rem 0 1rem;
    display:flex; align-items:center; gap:10px;
}}
.sec-head::after {{content:''; flex:1; height:0.5px; background:{T['border']};}}

.hero-band {{
    background:{T['bg2']};
    border:0.5px solid {T['border']};
    border-radius:14px;
    padding:1.75rem 2rem;
    margin-bottom:1.75rem;
}}
.hero-title {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:30px; font-weight:700; color:{T['head']}; line-height:1.15;
}}
.hero-title span {{color:{T['accent']};}}
.hero-sub  {{font-size:13px; color:{T['muted']}; margin-top:6px; line-height:1.55;}}
.stat-row  {{display:flex; gap:2rem; margin-top:1rem; flex-wrap:wrap;}}
.stat-n    {{font-family:'Barlow Condensed',sans-serif; font-size:24px; font-weight:700; color:{T['accent']};}}
.stat-l    {{font-size:11px; color:{T['muted']}; text-transform:uppercase; letter-spacing:0.08em;}}

.live-grid  {{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:1.5rem;}}
.live-card  {{
    flex:1; min-width:150px;
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:10px;
    padding:12px 14px;
    display:flex; align-items:flex-start; gap:10px;
}}
.lc-name  {{font-size:13px; font-weight:500; color:{T['head']};}}
.lc-venue {{font-size:11px; color:{T['muted']}; margin-top:2px;}}
.lc-time  {{font-family:'Barlow Condensed',sans-serif; font-size:11px; color:{T['accent']}; margin-top:4px; letter-spacing:0.06em;}}

.result-card {{
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:12px;
    padding:1.25rem;
    margin-top:0.75rem;
}}
.result-top {{
    display:flex; align-items:center; gap:12px;
    margin-bottom:1rem; padding-bottom:1rem;
    border-bottom:0.5px solid {T['border']};
}}
.avatar {{
    width:42px; height:42px; border-radius:50%;
    background:{T['tagbg']}; border:0.5px solid {T['accent']};
    display:flex; align-items:center; justify-content:center;
    font-size:13px; font-weight:600; color:{T['accent']}; flex-shrink:0;
}}
.rname {{font-size:15px; font-weight:500; color:{T['head']};}}
.rid   {{font-size:12px; color:{T['muted']};}}
.dtile-grid {{display:grid; grid-template-columns:1fr 1fr; gap:8px;}}
.dtile {{background:{T['bg3']}; border-radius:8px; padding:10px 12px;}}
.dtile-l {{font-size:11px; color:{T['muted']}; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px;}}
.dtile-v {{font-size:14px; font-weight:500; color:{T['text']};}}
.dtile-hi{{font-size:14px; font-weight:500; color:{T['accent']};}}

.folder-info {{
    background:{T['bg2']};
    border:0.5px solid {T['border']};
    border-radius:10px; padding:1rem 1.25rem;
    font-size:13px; color:{T['muted']}; line-height:1.7;
    margin-bottom:1.25rem;
}}
.folder-info strong {{color:{T['text']}; font-weight:500;}}
.folder-info code {{
    font-size:12px;
    background:{T['bg3']};
    border:0.5px solid {T['border']};
    border-radius:4px; padding:1px 6px;
    color:{T['accent']};
}}

.poster-meta {{padding:8px 10px 12px;}}
.p-title {{font-size:13px; font-weight:500; color:{T['head']}; line-height:1.3;}}
.p-track {{font-family:'Barlow Condensed',sans-serif; font-size:11px; color:{T['accent']}; letter-spacing:0.08em; text-transform:uppercase; margin-top:3px;}}
.p-file  {{font-size:11px; color:{T['muted']}; margin-top:2px;}}

/* ── Day group header ── */
.day-header {{
    margin-top: 2.5rem;
    margin-bottom: 1.25rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #3b9eff; /* Uses your primary accent color line */
    display: flex; 
    align-items: baseline; 
    gap: 14px;
    background: transparent !important; /* Removes the old box background */
    border-top: none !important;
    border-left: none !important;
    border-right: none !important;
    border-radius: 0 !important;
}}
.day-label {{
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 28px !important; /* Made it significantly larger */
    font-weight: 700 !important; 
    color: #ffffff !important; /* High contrast text color (swaps with accent) */
    text-transform: uppercase; 
    letter-spacing: 0.05em;
    line-height: 1;
}}
.day-date {{
    font-family: 'Barlow', sans-serif !important;
    font-size: 14px !important; 
    color: #6a90b0 !important; /* Clean, muted text color */
    font-weight: 400;
}}

/* ── Schedule rows ── */
.srow {{
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:10px;
    padding:13px 16px;
    display:flex; align-items:flex-start; gap:14px;
    margin-bottom:8px;
}}
.stime  {{font-family:'Barlow Condensed',sans-serif; font-size:13px; color:{T['accent']}; min-width:120px; letter-spacing:0.04em; padding-top:1px;}}
.sname  {{font-size:14px; font-weight:500; color:{T['head']};}}
.svenue {{font-size:12px; color:{T['muted']}; margin-top:2px;}}
.sspkr  {{font-size:11px; color:{T['muted']}; margin-top:3px; font-style:italic;}}
.stag   {{
    display:inline-block;
    background:{T['tagbg']}; color:{T['tagc']};
    font-family:'Barlow Condensed',sans-serif;
    font-size:11px; padding:3px 9px; border-radius:4px;
    letter-spacing:0.06em; text-transform:uppercase; white-space:nowrap;
    margin-left:auto; flex-shrink:0;
}}

.stTextInput > div > div > input {{
    background:{T['bg3']} !important;
    border:0.5px solid {T['border']} !important;
    color:{T['text']} !important;
    border-radius:8px !important;
    font-size:14px !important;
    font-family:'Barlow',sans-serif !important;
}}
.stTextInput > div > div > input:focus {{
    border-color:{T['accent']} !important;
    box-shadow:none !important;
}}
.stTextInput label {{color:{T['muted']} !important; font-size:13px !important;}}

.stButton > button {{
    background:{T['accent']} !important;
    color:#fff !important;
    border:none !important;
    border-radius:8px !important;
    font-size:13px !important;
    font-weight:500 !important;
    padding:0.45rem 1.2rem !important;
    font-family:'Barlow',sans-serif !important;
}}
.stButton > button:hover {{opacity:0.85 !important;}}

div[data-baseweb="select"] > div {{
    background:{T['bg3']} !important;
    border:0.5px solid {T['border']} !important;
    border-radius:8px !important;
    color:{T['text']} !important;
}}
.stSelectbox label {{color:{T['muted']} !important; font-size:13px !important;}}

.stTabs [data-baseweb="tab-list"] {{
    background:{T['bg2']} !important;
    border-bottom:0.5px solid {T['border']} !important;
    gap:0 !important;
    padding: 0 2.5rem !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-family:'Barlow Condensed',sans-serif !important;
    font-size:14px !important;
    font-weight:600 !important;
    letter-spacing:0.1em !important;
    text-transform:uppercase !important;
    color:{T['muted']} !important;
    background:transparent !important;
    border-bottom:2px solid transparent !important;
    padding:14px 20px !important;
}}
.stTabs [aria-selected="true"] {{
    color:{T['accent']} !important;
    border-bottom:2px solid {T['accent']} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{display:none !important;}}
.stTabs [data-baseweb="tab-border"]    {{display:none !important;}}
.stTabs [data-baseweb="tab-panel"]     {{padding:0 !important; background:{T['bg']} !important;}}

div[data-testid="stAlert"] {{border-radius:8px !important;}}

/* ── Navigate button ── */
.nav-btn {{
    display:inline-flex; align-items:center; gap:5px;
    margin-top:7px;
    background:{T['tagbg']};
    border:0.5px solid {T['accent']}55;
    color:{T['accent']};
    border-radius:6px; padding:4px 10px;
    font-family:'Barlow Condensed',sans-serif;
    font-size:11px; font-weight:600; letter-spacing:0.07em;
    text-decoration:none; text-transform:uppercase;
    transition:background 0.15s;
}}
.nav-btn:hover {{ background:{T['accent']}33; color:{T['accent']}; text-decoration:none; }}

/* ── Campus location card ── */
.campus-card {{
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:12px;
    padding:14px 16px;
    display:flex; align-items:flex-start; gap:12px;
    margin-bottom:10px;
}}
.campus-icon {{ font-size:22px; flex-shrink:0; margin-top:2px; }}
.campus-name {{ font-size:14px; font-weight:500; color:{T['head']}; }}
.campus-note {{ font-size:12px; color:{T['muted']}; margin-top:3px; line-height:1.5; }}
.cat-pill {{
    display:inline-block;
    background:{T['tagbg']}; color:{T['tagc']};
    font-family:'Barlow Condensed',sans-serif;
    font-size:10px; padding:2px 8px; border-radius:4px;
    letter-spacing:0.07em; text-transform:uppercase;
    margin-bottom:4px;
}}

/* ── Admin login box ── */
.admin-login-wrap {{
    max-width:380px; margin:4rem auto; padding:2rem;
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:16px; text-align:center;
}}
.admin-login-title {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:22px; font-weight:700; color:{T['head']};
    margin-bottom:6px;
}}
.admin-login-sub {{
    font-size:12px; color:{T['muted']}; margin-bottom:1.5rem;
}}
/* ── Admin toolbar ── */
.admin-toolbar {{
    display:flex; align-items:center; gap:10px;
    padding:10px 0 14px; flex-wrap:wrap;
}}
.undo-count {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:11px; color:{T['muted']}; letter-spacing:0.07em;
}}
</style>
""", unsafe_allow_html=True)

# ─── Top Bar ──────────────────────────────────────────────────────────────────
top_left, top_right = st.columns([5, 1])
with top_left:
    st.markdown(f"""
    <div class="astra-topbar">
      <div class="astra-brand">
        <span class="astra-logo">ASTRA</span>
        <span class="astra-yr">2026</span>
        <div class="astra-div"></div>
        <div class="astra-full">
          <strong>3rd Edition</strong>
          Aerospace Symposium on Technological Research Advancements
        </div>
      </div>
      <div class="live-badge">
        <span class="pulse-dot"></span>&nbsp;LIVE
      </div>
    </div>
    """, unsafe_allow_html=True)

with top_right:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    mode_label = "☀️ Light mode" if st.session_state.theme == "dark" else "🌙 Dark mode"
    if st.button(mode_label, key="theme_btn", width="stretch"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab_portal, tab_posters, tab_schedule, tab_campus, tab_admin = st.tabs([
    "🏠  Portal",
    "🖼️  Event Posters",
    "📅  Schedule",
    "📍  Campus Map",
    "🔒  Admin",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PORTAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_portal:
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # Hero
    st.markdown(f"""
    <div class="hero-band">
      <div class="hero-title">ASTRA <span>2026</span> — Live Conference Portal</div>
      <div class="hero-sub">
        Aerospace Symposium on Technological Research Advancements · 3rd Edition<br>
        Enter your Conference ID to find your assigned track, venue and timing.
      </div>
      <div class="stat-row">
        <div><div class="stat-n">9</div><div class="stat-l">KeyNote <br> Sessions</div></div>
        <div><div class="stat-n">3</div><div class="stat-l">Workshops</div></div>
        <div><div class="stat-n">4</div><div class="stat-l">Tracks</div></div>
        <div><div class="stat-n">3</div><div class="stat-l">Days</div></div>
        <div><div class="stat-n">300+</div><div class="stat-l">Delegates</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Happening Now ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Happening now</div>', unsafe_allow_html=True)

    def _live_card(name, location, spkr, end_str):
        spkr_ln = (
            '<div class="lc-venue" style="font-style:italic;">'
            + spkr
            + '</div>'
        ) if spkr else ""
        nav = venue_maps_url(location)
        nav_btn = (
            '<a href="' + nav + '" target="_blank" class="nav-btn">📍 Navigate</a>'
        )
        return (
            '<div class="live-card">'
            '<span class="pulse-dot" style="margin-top:5px;flex-shrink:0;"></span>'
            '<div style="flex:1;">'
            + '<div class="lc-name">' + name + '</div>'
            + '<div class="lc-venue">' + location + '</div>'
            + spkr_ln
            + '<div class="lc-time">Ends ' + end_str + '</div>'
            + nav_btn
            + '</div></div>'
        )

    if DATA_OK:
        # 1. Fetch current time in UTC and seamlessly convert it to IST
        ist_zone = ZoneInfo("Asia/Kolkata")
        now_dt = datetime.now(timezone.utc).astimezone(ist_zone)
        today    = now_dt.date()
        now_time = now_dt.time()
        live_events = schedule_df[
            (schedule_df["_Date_raw"] == today) &
            (schedule_df["Start_Time"] <= now_time) &
            (now_time <= schedule_df["End_Time"])
        ]
        if not live_events.empty:
            cards_html = '<div class="live-grid">'
            for _, ev in live_events.iterrows():
                spkr    = str(ev.get("Speaker_Affiliation", "")).strip()
                spkr    = spkr if spkr and spkr != "nan" else ""
                end_str = ev["End_Time"].strftime("%H:%M")
                cards_html += _live_card(
                    str(ev["Event_Name"]),
                    str(ev["Location"]),
                    spkr,
                    end_str,
                )
            cards_html += '</div>'
            st.markdown(cards_html, unsafe_allow_html=True)
        else:
            conf_dates_sorted = sorted(schedule_df["_Date_raw"].dropna().unique())
            if conf_dates_sorted and today < conf_dates_sorted[0]:
                first = conf_dates_sorted[0].strftime("%b %d, %Y")
                msg = (
                    '<p style="color:' + T["muted"] + ';font-size:13px;margin-top:0;">'
                    'Conference begins on <strong style="color:' + T["text"] + ';">' + first + '</strong>. '
                    'Check the Schedule tab for the full programme.</p>'
                )
            elif conf_dates_sorted and today > conf_dates_sorted[-1]:
                msg = (
                    '<p style="color:' + T["muted"] + ';font-size:13px;margin-top:0;">'
                    'The conference has concluded. Thank you for attending ASTRA 2026.</p>'
                )
            else:
                msg = (
                    '<p style="color:' + T["muted"] + ';font-size:13px;margin-top:0;">'
                    'No sessions are active right now. Check the Schedule tab for the full timeline.</p>'
                )
            st.markdown(msg, unsafe_allow_html=True)
    else:
        cards_html = '<div class="live-grid">'
        for name, venue, end in [
            ("Opening Keynote",      "Auditorium · Hall A",  "10:30"),
            ("Propulsion Workshop",  "Lab Block · Room 204", "11:00"),
            ("Satellite Navigation", "Main Hall · Pod B",    "11:30"),
        ]:
            cards_html += _live_card(name, venue, "", end)
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)

    # ── Conference ID Lookup ───────────────────────────────────────────────
    st.markdown('<div class="sec-head">Find your track</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:{T["muted"]};margin-bottom:8px;">Enter the unique Conference ID printed on your registration pass.</p>', unsafe_allow_html=True)

    col_in, col_btn, col_pad = st.columns([3, 1, 2])
    with col_in:
        conf_id = st.text_input("Conference ID", placeholder="e.g. CONF-101",
                                label_visibility="collapsed", key="conf_id")
    with col_btn:
        st.button("Look up →", key="lookup_btn", width="stretch")

    if conf_id:
        cid = conf_id.strip().upper()
        if DATA_OK:
            match = attendees_df[attendees_df["Conference_ID"] == cid]
            if not match.empty:
                u = match.iloc[0]
                initials = "".join(w[0].upper() for w in str(u["Name"]).split() if w)
                # Cross-ref schedule for the attendee's track/session
                ts = schedule_df[
                    schedule_df["Event_Name"].str.lower() == str(u.get("Track", "")).lower()
                ]
                start_t = ts.iloc[0]["Start_Time"].strftime("%H:%M") if not ts.empty else "—"
                end_t   = ts.iloc[0]["End_Time"].strftime("%H:%M")   if not ts.empty else "—"
                st.markdown(f"""
                <div class="result-card">
                  <div class="result-top">
                    <div class="avatar">{initials}</div>
                    <div>
                      <div class="rname">{u['Name']}</div>
                      <div class="rid">{cid}</div>
                    </div>
                  </div>
                  <div class="dtile-grid">
                    <div class="dtile"><div class="dtile-l">Assigned track</div><div class="dtile-hi">{u.get('Track','—')}</div></div>
                    <div class="dtile">
                      <div class="dtile-l">Primary venue</div>
                      <div class="dtile-v">{u.get('Room','—')}</div>
                      <a href="{venue_maps_url(str(u.get('Room','')))}" target="_blank" class="nav-btn" style="margin-top:6px;display:inline-block;">📍 Navigate</a>
                    </div>
                    <div class="dtile"><div class="dtile-l">Track starts</div><div class="dtile-v">{start_t}</div></div>
                    <div class="dtile"><div class="dtile-l">Track ends</div><div class="dtile-v">{end_t}</div></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("Invalid Conference ID — please check your registration pass.")
        else:
            st.warning("conference_data.xlsx not found. Place it in the project root folder.")

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EVENT POSTERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_posters:
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    if not POSTERS:
        st.markdown(
            f'<div style="text-align:center;padding:4rem 1rem;color:{T["muted"]};">'
            f'<div style="font-size:48px;margin-bottom:1rem;opacity:0.3;">🖼️</div>'
            f'<div style="font-size:15px;font-weight:500;color:{T["text"]};margin-bottom:6px;">No posters found</div>'
            f'<div style="font-size:13px;">No poster images were found in the posters/ folder.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        def render_poster_grid(poster_list):
            COLS = 4
            for i in range(0, len(poster_list), COLS):
                row_items = poster_list[i: i + COLS]
                cols = st.columns(COLS)
                for col, poster in zip(cols, row_items):
                    with col:
                        st.image(str(poster["path"]), width="stretch")
                        st.markdown(
                            f'<div class="poster-meta">'
                            f'<div class="p-title">{poster["name"]}</div>'
                            f'<div class="p-track">{poster["track"]}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

        track_names = sorted({p["track"] for p in POSTERS})
        tab_labels  = ["All"] + track_names
        poster_tabs = st.tabs(tab_labels)

        with poster_tabs[0]:
            st.markdown(
                f'<div class="sec-head">{len(POSTERS)} poster{"s" if len(POSTERS) != 1 else ""}</div>',
                unsafe_allow_html=True,
            )
            render_poster_grid(POSTERS)

        for tab_obj, track in zip(poster_tabs[1:], track_names):
            with tab_obj:
                filtered = [p for p in POSTERS if p["track"] == track]
                st.markdown(
                    f'<div class="sec-head">{len(filtered)} poster{"s" if len(filtered) != 1 else ""}</div>',
                    unsafe_allow_html=True,
                )
                render_poster_grid(filtered)

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # Static fallback data (includes parallel tracks at 11:00)
    STATIC = [
        ("Day 1", "Aug 10, 2026", "08:30", "09:00", "08:30 – 09:00", "Registration & Welcome",      "Foyer · Main Entrance", "Organising Committee"),
        ("Day 1", "Aug 10, 2026", "09:00", "10:30", "09:00 – 10:30", "Opening Keynote",              "Auditorium · Hall A",   "Chief Guest"),
        ("Day 1", "Aug 10, 2026", "10:30", "11:00", "10:30 – 11:00", "Networking & Coffee Break",    "Level 2 Lounge",        ""),
        ("Day 1", "Aug 10, 2026", "11:00", "12:30", "11:00 – 12:30", "Propulsion Systems Workshop",  "Lab Block · Room 204",  "Dr. A. Nair"),
        ("Day 1", "Aug 10, 2026", "11:00", "12:30", "11:00 – 12:30", "Satellite Navigation Track",   "Main Hall · Pod B",     "Prof. R. Sharma"),
        ("Day 1", "Aug 10, 2026", "12:30", "13:30", "12:30 – 13:30", "Lunch Break",                  "Dining Hall",           ""),
        ("Day 1", "Aug 10, 2026", "13:30", "15:00", "13:30 – 15:00", "Robotics & ROS Session",       "Main Hall",             "Dr. S. Kumar"),
        ("Day 1", "Aug 10, 2026", "15:00", "16:30", "15:00 – 16:30", "AI in Aerospace Panel",        "Auditorium · Hall B",   "Panel"),
        ("Day 1", "Aug 10, 2026", "16:30", "17:00", "16:30 – 17:00", "Day 1 Closing Remarks",        "Auditorium · Hall A",   "Conference Chair"),
    ]

    def render_schedule_group(group_rows):
        """
        group_rows: list of dicts with keys:
            display_time, event_name, location, speaker
        Rows sharing the same (start, end) are parallel — rendered side-by-side.
        """
        from itertools import groupby as igrp

        # Sort by start time then group
        group_rows.sort(key=lambda r: r["start_key"])
        for _, slot_iter in igrp(group_rows, key=lambda r: r["start_key"]):
            slot = list(slot_iter)
            n = len(slot)
            if n == 1:
                row = slot[0]
                spkr_html = f'<div class="sspkr">🎤 {row["speaker"]}</div>' if row["speaker"] else ""
                st.markdown(
                    '<div class="srow">' +
                    f'<div class="stime">{row["display_time"]}</div>' +
                    '<div style="flex:1;">' +
                    f'<div class="sname">{row["event_name"]}</div>' +
                    f'<div class="svenue">{row["location"]}</div>' +
                    spkr_html +
                    '</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                # Parallel tracks — time label left, then n equal columns
                cols = st.columns([1] + [2] * n)
                with cols[0]:
                    st.markdown(
                        f'<div style="padding:14px 0 14px 4px;">' +
                        f'<div class="stime" style="min-width:unset;">{slot[0]["display_time"]}</div>' +
                        '</div>',
                        unsafe_allow_html=True,
                    )
                for col, row in zip(cols[1:], slot):
                    spkr_html = f'<div class="sspkr">🎤 {row["speaker"]}</div>' if row["speaker"] else ""
                    with col:
                        st.markdown(
                            '<div class="srow" style="margin-bottom:0;">' +
                            '<div style="flex:1;">' +
                            f'<div class="sname">{row["event_name"]}</div>' +
                            f'<div class="svenue">{row["location"]}</div>' +
                            spkr_html +
                            '</div></div>',
                            unsafe_allow_html=True,
                        )
                st.markdown('<div style="margin-bottom:8px;"></div>', unsafe_allow_html=True)

    if DATA_OK and not schedule_df.empty:
        st.markdown('<div class="sec-head">Full schedule</div>', unsafe_allow_html=True)

        grouped = schedule_df.groupby(["Day", "Date"], sort=False)
        for (day, date), group in grouped:
            st.markdown(
                '<div class="day-header">' +
                f'<span class="day-label">{day}</span>' +
                f'<span class="day-date">{date}</span>' +
                '</div>',
                unsafe_allow_html=True,
            )
            rows = []
            for _, r in group.iterrows():
                start_str = r["Start_Time"].strftime("%H:%M")
                end_str   = r["End_Time"].strftime("%H:%M")
                ts        = str(r.get("Time_Slot", "")).strip()
                disp      = ts if ts and ts != "nan" else f"{start_str} – {end_str}"
                spkr      = str(r.get("Speaker_Affiliation", "")).strip()
                rows.append({
                    "start_key":    start_str,
                    "display_time": disp,
                    "event_name":   r["Event_Name"],
                    "location":     r["Location"],
                    "speaker":      spkr if spkr != "nan" else "",
                })
            render_schedule_group(rows)

    else:
        st.markdown('<div class="sec-head">Day 1 — sample schedule</div>', unsafe_allow_html=True)
        current_day = None
        rows = []
        for day, date, s, e, ts, name, venue, spkr in STATIC:
            if day != current_day:
                if rows:
                    render_schedule_group(rows)
                    rows = []
                current_day = day
                st.markdown(
                    '<div class="day-header">' +
                    f'<span class="day-label">{day}</span>' +
                    f'<span class="day-date">{date}</span>' +
                    '</div>',
                    unsafe_allow_html=True,
                )
            rows.append({
                "start_key":    s,
                "display_time": ts,
                "event_name":   name,
                "location":     venue,
                "speaker":      spkr,
            })
        if rows:
            render_schedule_group(rows)

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CAMPUS MAP
# ══════════════════════════════════════════════════════════════════════════════
with tab_campus:
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    st.markdown(
        '<div class="hero-band" style="margin-bottom:1.5rem;">' +
        '<div class="hero-title">Campus <span>Locations</span></div>' +
        '<div class="hero-sub">Tap <strong>Navigate</strong> on any location to open Google Maps ' +
        'walking directions from your current position.</div>' +
        '</div>',
        unsafe_allow_html=True,
    )

    # Build category → locations map
    from collections import defaultdict
    cat_map = defaultdict(list)
    for loc in CAMPUS_LOCATIONS:
        cat_map[loc["category"]].append(loc)

    for cat in CATEGORY_ORDER:
        if cat not in cat_map:
            continue
        locs = cat_map[cat]
        st.markdown(
            '<div class="sec-head">' + cat + 's</div>',
            unsafe_allow_html=True,
        )
        # Two-column grid
        col_pairs = [locs[i:i+2] for i in range(0, len(locs), 2)]
        for pair in col_pairs:
            cols = st.columns(len(pair))
            for col, loc in zip(cols, pair):
                with col:
                    nav = maps_url(loc["lat"], loc["lng"], loc["name"])
                    placeholder_warn = (
                        '<div style="font-size:10px;color:#f59e0b;margin-top:4px;">'
                        '⚠ Coordinates not set yet</div>'
                    ) if loc["lat"] == 0.0 and loc["lng"] == 0.0 else ""
                    card_html = (
                        '<div class="campus-card">' +
                        '<div class="campus-icon">' + loc["icon"] + '</div>' +
                        '<div style="flex:1;">' +
                        '<div class="cat-pill">' + loc["category"] + '</div>' +
                        '<div class="campus-name">' + loc["name"] + '</div>' +
                        '<div class="campus-note">' + loc["note"] + '</div>' +
                        placeholder_warn +
                        '<a href="' + nav + '" target="_blank" class="nav-btn" style="margin-top:8px;">📍 Navigate</a>' +
                        '</div></div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ADMIN
# ══════════════════════════════════════════════════════════════════════════════
ADMIN_PASSWORD = "@$tra_2K2_six"   # ← change this to your preferred password

SHEET_LABELS = {
    "Attendees": "👥 Attendees",
    "Schedule":  "📅 Schedule",
}

def _push_history(sheet, df):
    """Push a snapshot of df onto the undo stack for sheet."""
    hist = st.session_state.edit_history.setdefault(sheet, [])
    hist.append(df.copy())
    # Keep max 20 snapshots
    if len(hist) > 20:
        st.session_state.edit_history[sheet] = hist[-20:]

def _save_to_excel(sheets_dict):
    """Write all sheets back to conference_data.xlsx."""
    try:
        with pd.ExcelWriter("conference_data.xlsx", engine="openpyxl") as writer:
            for sheet, df in sheets_dict.items():
                df.to_excel(writer, sheet_name=sheet, index=False)
        # Bust the Streamlit cache so the portal reloads fresh data
        load_conference_data.clear()
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

with tab_admin:
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    # ── Login gate ───────────────────────────────────────────────────────────
    if not st.session_state.admin_logged:
        st.markdown(
            '<div class="admin-login-wrap">' +
            '<div style="font-size:36px;margin-bottom:8px;">🔐</div>' +
            '<div class="admin-login-title">Admin Portal</div>' +
            '<div class="admin-login-sub">Enter the admin password to access the database editor.</div>' +
            '</div>',
            unsafe_allow_html=True,
        )
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            pwd = st.text_input("Password", type="password", key="admin_pwd",
                                placeholder="Enter admin password",
                                label_visibility="collapsed")
            if st.button("Unlock →", key="admin_login_btn", width="stretch"):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin_logged = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
        # ── Logged-in header ─────────────────────────────────────────────────
        hcol1, hcol2 = st.columns([6, 1])
        with hcol1:
            st.markdown(
                '<div class="hero-band" style="margin-bottom:1rem;">' +
                '<div class="hero-title">Admin <span>Database Editor</span></div>' +
                '<div class="hero-sub">Edit attendees and schedule directly. ' +
                'All changes are saved to <code>conference_data.xlsx</code>. ' +
                'Use Undo to roll back any sheet independently.</div>' +
                '</div>',
                unsafe_allow_html=True,
            )
        with hcol2:
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            if st.button("🚪 Logout", key="admin_logout", width="stretch"):
                st.session_state.admin_logged  = False
                st.session_state.working_dfs   = {}
                st.session_state.edit_history  = {}
                st.rerun()

        # ── Load working copies once ──────────────────────────────────────────
        if DATA_OK:
            for sheet in ["Attendees", "Schedule"]:
                if sheet not in st.session_state.working_dfs:
                    raw = pd.read_excel("conference_data.xlsx", sheet_name=sheet)
                    st.session_state.working_dfs[sheet] = raw.copy()
        else:
            st.warning("conference_data.xlsx not found — cannot load data for editing.")
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()

        # ── Per-sheet sub-tabs ────────────────────────────────────────────────
        sheet_tabs = st.tabs([SHEET_LABELS[s] for s in SHEET_LABELS])

        for tab_obj, sheet in zip(sheet_tabs, SHEET_LABELS.keys()):
            with tab_obj:
                wdf = st.session_state.working_dfs[sheet]
                hist = st.session_state.edit_history.get(sheet, [])

                # Toolbar row
                t1, t2, t3, t4 = st.columns([2, 2, 2, 4])
                with t1:
                    add_row = st.button(f"➕ Add row", key=f"add_{sheet}")
                with t2:
                    undo_disabled = len(hist) == 0
                    undo_btn = st.button(
                        f"↩ Undo ({len(hist)})",
                        key=f"undo_{sheet}",
                        disabled=undo_disabled,
                    )
                with t3:
                    save_btn = st.button(f"💾 Save to Excel", key=f"save_{sheet}")
                with t4:
                    st.markdown(
                        '<div class="undo-count">Changes are saved per-session. ' +
                        'Click Save to write to disk.</div>',
                        unsafe_allow_html=True,
                    )

                # Handle actions BEFORE rendering editor (avoids stale state)
                if add_row:
                    _push_history(sheet, wdf)
                    empty = pd.DataFrame([{c: "" for c in wdf.columns}])
                    st.session_state.working_dfs[sheet] = pd.concat(
                        [wdf, empty], ignore_index=True
                    )
                    st.rerun()

                if undo_btn and hist:
                    st.session_state.working_dfs[sheet] = hist.pop()
                    st.session_state.edit_history[sheet] = hist
                    st.rerun()

                if save_btn:
                    all_sheets = {
                        s: st.session_state.working_dfs[s]
                        for s in st.session_state.working_dfs
                    }
                    if _save_to_excel(all_sheets):
                        st.success(f"✅ {sheet} saved to conference_data.xlsx")

                # ── Editable data table ───────────────────────────────────────
                st.markdown(
                    f'<div class="sec-head">{sheet} — {len(wdf)} rows</div>',
                    unsafe_allow_html=True,
                )

                edited = st.data_editor(
                    st.session_state.working_dfs[sheet],
                    use_container_width=True,
                    num_rows="dynamic",
                    key=f"editor_{sheet}",
                )

                # Detect if user made edits via the table
                if not edited.equals(st.session_state.working_dfs[sheet]):
                    _push_history(sheet, st.session_state.working_dfs[sheet])
                    st.session_state.working_dfs[sheet] = edited.copy()

    st.markdown("</div>", unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="text-align:center;padding:2.5rem 0 1rem;font-size:11px;'
    f'color:{T["muted"]};font-family:\'Barlow Condensed\',sans-serif;letter-spacing:0.08em;">'
    f'ASTRA 2026 · Live Conference Schedule Subsystem · 3rd Edition</div>',
    unsafe_allow_html=True,
)