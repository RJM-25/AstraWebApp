import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASTRA 2026 — Live Conference Portal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Session State ────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

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

# ─── Data Loading ─────────────────────────────────────────────────────────────
@st.cache_data
def load_conference_data():
    attendees_df = pd.read_excel("conference_data.xlsx", sheet_name="Attendees")
    schedule_df  = pd.read_excel("conference_data.xlsx", sheet_name="Schedule")
    attendees_df["Conference_ID"] = attendees_df["Conference_ID"].astype(str).str.strip()
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
    # Root-level images → track "General"
    for f in sorted(POSTER_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED:
            result.append({
                "path":  f,
                "name":  f.stem.replace("-", " ").replace("_", " ").title(),
                "track": "General",
                "file":  f.name,
            })
    # Sub-folder images → track = folder name
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
# Injected ONCE — uses Python f-string so every color variable is a real hex value,
# never a CSS variable that Streamlit might strip.
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;600;700&family=Barlow:wght@300;400;500&display=swap" rel="stylesheet">

<style>
/* ── Hide Streamlit chrome ── */
#MainMenu {{visibility:hidden;}}
footer    {{visibility:hidden;}}
header    {{visibility:hidden;}}
section[data-testid="stSidebar"] {{display:none !important;}}

/* ── Page background ── */
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

/* ── Global font ── */
html, body, [class*="css"] {{
    font-family: 'Barlow', sans-serif !important;
    color: {T['text']};
}}

/* ── Topbar ── */
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

/* ── Content wrapper ── */
.page-wrap {{padding:1.75rem 2.5rem 0; max-width:980px; margin:0 auto;}}

/* ── Section heading ── */
.sec-head {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:12px; font-weight:600; letter-spacing:0.14em;
    text-transform:uppercase; color:{T['muted']};
    margin:1.5rem 0 1rem;
    display:flex; align-items:center; gap:10px;
}}
.sec-head::after {{content:''; flex:1; height:0.5px; background:{T['border']};}}

/* ── Hero band ── */
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

/* ── Live event cards ── */
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

/* ── Result card ── */
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

/* ── Folder info box ── */
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

/* ── Poster card labels ── */
.poster-meta {{padding:8px 10px 12px;}}
.p-title {{font-size:13px; font-weight:500; color:{T['head']}; line-height:1.3;}}
.p-track {{font-family:'Barlow Condensed',sans-serif; font-size:11px; color:{T['accent']}; letter-spacing:0.08em; text-transform:uppercase; margin-top:3px;}}
.p-file  {{font-size:11px; color:{T['muted']}; margin-top:2px;}}

/* ── Schedule rows ── */
.srow {{
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:10px;
    padding:13px 16px;
    display:flex; align-items:center; gap:14px;
    margin-bottom:8px;
}}
.stime  {{font-family:'Barlow Condensed',sans-serif; font-size:13px; color:{T['accent']}; min-width:105px; letter-spacing:0.04em;}}
.sname  {{font-size:14px; font-weight:500; color:{T['head']};}}
.svenue {{font-size:12px; color:{T['muted']}; margin-top:2px;}}
.stag   {{
    display:inline-block;
    background:{T['tagbg']}; color:{T['tagc']};
    font-family:'Barlow Condensed',sans-serif;
    font-size:11px; padding:3px 9px; border-radius:4px;
    letter-spacing:0.06em; text-transform:uppercase; white-space:nowrap;
}}

/* ── Streamlit widget overrides ── */
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

/* Tab styling */
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

/* Error / success alerts */
div[data-testid="stAlert"] {{border-radius:8px !important;}}
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
    if st.button(mode_label, key="theme_btn", use_container_width=True):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab_portal, tab_posters, tab_schedule = st.tabs([
    "🏠  Portal",
    "🖼️  Event Posters",
    "📅  Schedule",
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
        <div><div class="stat-n">24</div><div class="stat-l">Sessions</div></div>
        <div><div class="stat-n">6</div><div class="stat-l">Tracks</div></div>
        <div><div class="stat-n">3</div><div class="stat-l">Days</div></div>
        <div><div class="stat-n">400+</div><div class="stat-l">Delegates</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Happening Now ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Happening now</div>', unsafe_allow_html=True)

    live_html = '<div class="live-grid">'
    if DATA_OK:
        now = datetime.now().time()
        schedule_df["_s"] = pd.to_datetime(schedule_df["Start_Time"].astype(str), format="mixed").dt.time
        schedule_df["_e"] = pd.to_datetime(schedule_df["End_Time"].astype(str),   format="mixed").dt.time
        live_events = schedule_df[(schedule_df["_s"] <= now) & (now <= schedule_df["_e"])]
        if not live_events.empty:
            for _, ev in live_events.iterrows():
                live_html += f"""
                <div class="live-card">
                  <span class="pulse-dot" style="margin-top:5px;flex-shrink:0;"></span>
                  <div>
                    <div class="lc-name">{ev['Event_Name']}</div>
                    <div class="lc-venue">{ev['Location']}</div>
                    <div class="lc-time">Ends {str(ev['End_Time'])[:5]}</div>
                  </div>
                </div>"""
        else:
            live_html += f'<p style="color:{T["muted"]};font-size:13px;">No sessions are active right now. Check the Schedule tab for the full timeline.</p>'
    else:
        # Sample fallback
        samples = [
            ("Opening Keynote",      "Auditorium · Hall A",  "10:30"),
            ("Propulsion Workshop",  "Lab Block · Room 204", "11:00"),
            ("Satellite Navigation", "Main Hall · Pod B",    "11:30"),
        ]
        for name, venue, end in samples:
            live_html += f"""
            <div class="live-card">
              <span class="pulse-dot" style="margin-top:5px;flex-shrink:0;"></span>
              <div>
                <div class="lc-name">{name}</div>
                <div class="lc-venue">{venue}</div>
                <div class="lc-time">Ends {end}</div>
              </div>
            </div>"""
    live_html += "</div>"
    st.markdown(live_html, unsafe_allow_html=True)

    # ── Conference ID Lookup ───────────────────────────────────────────────
    st.markdown('<div class="sec-head">Find your track</div>', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:13px;color:{T["muted"]};margin-bottom:8px;">Enter the unique Conference ID printed on your registration pass.</p>', unsafe_allow_html=True)

    col_in, col_btn, col_pad = st.columns([3, 1, 2])
    with col_in:
        conf_id = st.text_input("Conference ID", placeholder="e.g. CONF-101",
                                label_visibility="collapsed", key="conf_id")
    with col_btn:
        do_lookup = st.button("Look up →", key="lookup_btn", use_container_width=True)

    if conf_id:
        cid = conf_id.strip().upper()
        if DATA_OK:
            match = attendees_df[attendees_df["Conference_ID"] == cid]
            if not match.empty:
                u = match.iloc[0]
                initials = "".join(w[0].upper() for w in str(u["Name"]).split() if w)
                # cross-ref schedule for timing
                ts = schedule_df[schedule_df["Event_Name"].str.lower() == str(u["Track"]).lower()]
                start_t = str(ts.iloc[0]["Start_Time"])[:5] if not ts.empty else "—"
                end_t   = str(ts.iloc[0]["End_Time"])[:5]   if not ts.empty else "—"
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
                    <div class="dtile"><div class="dtile-l">Assigned track</div><div class="dtile-hi">{u['Track']}</div></div>
                    <div class="dtile"><div class="dtile-l">Primary venue</div><div class="dtile-v">{u['Room']}</div></div>
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

    st.markdown(f"""
    <div class="folder-info">
      <strong>How to add your posters</strong><br>
      Drop your poster images into a folder named <code>posters/</code> in the same directory as <code>app.py</code>.
      You can also create sub-folders — each sub-folder name becomes a track filter category.
      Supported formats: <code>.jpg</code> &nbsp; <code>.jpeg</code> &nbsp; <code>.png</code> &nbsp; <code>.webp</code>
    </div>
    """, unsafe_allow_html=True)

    if not POSTERS:
        st.markdown(f"""
        <div style="text-align:center;padding:4rem 1rem;color:{T['muted']};">
          <div style="font-size:48px;margin-bottom:1rem;opacity:0.3;">🖼️</div>
          <div style="font-size:15px;font-weight:500;color:{T['text']};margin-bottom:6px;">No posters found</div>
          <div style="font-size:13px;line-height:1.7;">
            Create a <code style="background:{T['bg3']};border-radius:4px;padding:1px 6px;color:{T['accent']};">posters/</code>
            folder in your project root and add your event poster images.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        cf1, cf2 = st.columns([2, 4])
        with cf1:
            sel_track = st.selectbox("Filter by track", TRACKS, key="poster_filter")
        filtered = POSTERS if sel_track == "All" else [p for p in POSTERS if p["track"] == sel_track]
        st.markdown(f'<div class="sec-head">{len(filtered)} poster{"s" if len(filtered) != 1 else ""}</div>', unsafe_allow_html=True)

        COLS = 4
        for i in range(0, len(filtered), COLS):
            row = filtered[i: i + COLS]
            cols = st.columns(COLS)
            for col, poster in zip(cols, row):
                with col:
                    st.image(str(poster["path"]), use_container_width=True)
                    st.markdown(f"""
                    <div class="poster-meta">
                      <div class="p-title">{poster['name']}</div>
                      <div class="p-track">{poster['track']}</div>
                      <div class="p-file">{poster['file']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SCHEDULE
# ══════════════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.markdown('<div class="page-wrap">', unsafe_allow_html=True)

    STATIC = [
        ("08:30 – 09:00", "Registration & Welcome",      "Foyer · Main Entrance", "All"),
        ("09:00 – 10:30", "Opening Keynote",              "Auditorium · Hall A",   "Keynote"),
        ("10:30 – 11:00", "Networking & Coffee Break",    "Level 2 Lounge",        "Break"),
        ("11:00 – 12:30", "Propulsion Systems Workshop",  "Lab Block · Room 204",  "Workshop"),
        ("11:00 – 12:30", "Satellite Navigation Track",   "Main Hall · Pod B",     "Track"),
        ("12:30 – 13:30", "Lunch Break",                  "Dining Hall",           "Break"),
        ("13:30 – 15:00", "Robotics & ROS Session",       "Main Hall",             "Track"),
        ("15:00 – 16:30", "AI in Aerospace Panel",        "Auditorium · Hall B",   "Panel"),
        ("16:30 – 17:00", "Day 1 Closing Remarks",        "Auditorium · Hall A",   "Plenary"),
    ]

    if DATA_OK and not schedule_df.empty:
        st.markdown('<div class="sec-head">Full schedule</div>', unsafe_allow_html=True)
        for _, row in schedule_df.iterrows():
            tag  = str(row.get("Type", "Session"))
            s    = str(row["Start_Time"])[:5]
            e    = str(row["End_Time"])[:5]
            st.markdown(f"""
            <div class="srow">
              <div class="stime">{s} – {e}</div>
              <div style="flex:1;">
                <div class="sname">{row['Event_Name']}</div>
                <div class="svenue">{row['Location']}</div>
              </div>
              <span class="stag">{tag}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="sec-head">Day 1 — sample schedule</div>', unsafe_allow_html=True)
        for time, name, venue, tag in STATIC:
            st.markdown(f"""
            <div class="srow">
              <div class="stime">{time}</div>
              <div style="flex:1;">
                <div class="sname">{name}</div>
                <div class="svenue">{venue}</div>
              </div>
              <span class="stag">{tag}</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="text-align:center;padding:2.5rem 0 1rem;font-size:11px;'
    f'color:{T["muted"]};font-family:\'Barlow Condensed\',sans-serif;letter-spacing:0.08em;">'
    f'ASTRA 2026 · Live Conference Schedule Subsystem · 3rd Edition</div>',
    unsafe_allow_html=True,
)