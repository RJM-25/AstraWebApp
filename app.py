import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from admin_schedule import render_admin_tab, apply_overrides, load_overrides

ist_now = datetime.now(
    ZoneInfo("Asia/Kolkata")
)

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ASTRA 2026 — Live Conference Portal",
    page_icon="assets/astraicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Session State ────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
if "menu_day_offset" not in st.session_state: st.session_state.menu_day_offset = 0
if "font_size" not in st.session_state:
    st.session_state.font_size = 100  # percent, default 100%

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

CONFERENCE_INFO = {
    "wifi": [
        {"label": "Delegate Network", "ssid": "IIST-EVENTS", "password": "Net@Space0406"},

    ],
    "contacts": [
        {"label": "Astra Coordinator 1", "icon": "📞", "value": "+91 8547874584"},
        {"label": "Astra Coordinator 2", "icon": "📞", "value": "+91 8893433624"},
        {"label": "Medical Centre",    "icon": "🏥", "value": "+91 471 2568669"},
        {"label": "CISF", "icon": "👤", "value": "+91 471 2568400"},
        {"label": "Women Helpline",    "icon": "🛡️", "value": "+91 9188755401"},
    ],
}

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
    "Main Gate": {"lat":      8.627670286284625,"lng":      77.03215484977001, "label": "Main Gate (Entrance)"},
}

CAMPUS_LOCATIONS = [
    # ── Hostels ────────────────────────────────────────────────────────────
    {
        "name":     "Dhanishtha Hostel (keynote speakers, VIPs)",
        "category": "Hostel",
        "icon":     "🏠",
        "lat":      8.62849250877032, 
        "lng":      77.0347411076061,
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
        "name":     "Thripthi Mess",
        "category": "Mess",
        "icon":     "🍽️",
        "lat":      8.627385651203852,
        "lng":      77.03500994613462,
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
    {
        "name":     "Library",
        "category": "Facility",
        "icon":     "📚",
        "lat":      8.6262964680692,
        "lng":      77.03407444831592,
        "note":     "Theme Based Exhibition, open 9 AM–8 PM",
    },
]

CATEGORY_ORDER = ["Venue", "Hostel", "Mess", "Facility"]

# ─── Conference Schedule Data ───────────────────────────────────────
from datetime import time as dtime, date as ddate
 
def _pt(s):
    parts = s.strip().split(":")
    return dtime(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
 
def _pd_date(s):
    d, m, y = s.strip().split(".")
    return ddate(int(y), int(m), int(d))

CONFERENCE_SCHEDULE = [

    # ──────────────────────────────────────────────────────────────
    # DAY 1
    # ──────────────────────────────────────────────────────────────
    {
        "day": "Day 1",
        "date": "04.06.2026",
        "sessions": [

            {
                "start_time": "07:45:00",
                "end_time": "09:00:00",
                "time_slot": "07:45 - 09:00",
                "event": "Registration",
                "location": "Main Gate"
            },

            {
                "start_time": "09:15:00",
                "end_time": "10:00:00",
                "time_slot": "09:15 - 10:00",
                "event": "Welcome and Inaugural Session",
                "location": "MPH"
            },

            {
                "start_time": "10:00:00",
                "end_time": "10:50:00",
                "time_slot": "10:00 - 10:50",
                "event": "Keynote Session 1: Optimal Computational Guidance for Challenging Space Missions",
                "speaker": "Prof. Radhakant Padhi (IISc Bangalore)",
                "location": "MPH"
            },

            {
                "start_time": "10:50:00",
                "end_time": "11:00:00",
                "time_slot": "10:50 - 11:00",
                "event": "High Tea",
                "location": "MPH"
            },

            {
                "start_time": "11:10:00",
                "end_time": "12:00:00",
                "time_slot": "11:10 - 12:00",
                "event": "Keynote Session 2: Continuous and Explosive Transitions in Thermoacoustic Systems",
                "speaker": "Prof. R I Sujith (IIT Madras)",
                "location": "MPH"
            },

            {
                "start_time": "12:00:00",
                "end_time": "13:15:00",
                "time_slot": "12:00 - 13:15",
                "event": "Lunch Break",
                "location": "SAC"
            },

            {
                "start_time": "13:15:00",
                "end_time": "14:05:00",
                "time_slot": "13:15 - 14:05",
                "event": "Keynote Session 3: From High-Performance to High-Efficiency",
                "speaker": "Dr. P Sasikumar (VSSC, ISRO)",
                "location": "MPH"
            },

            # Parallel Paper Sessions
            {
                "start_time": "14:05:00",
                "end_time": "16:20:00",
                "time_slot": "14:05 - 16:20",
                "event": "Paper Presentation Session 1",
                "parallel_tracks": [

                    {
                        "track": "TS-1",
                        "title": "Thermal Session",
                        "location": "Council Hall",
                        "session_chairs": ["Dr. Sujith R I", "Dr. Rajesh Sadanandan"]
                    },

                    {
                        "track": "AS-1",
                        "title": "Aerodynamics Session",
                        "location": "Conference Hall",
                        "session_chairs": [" Dr. Praveen Nair", "Dr. Aravind V"]
                    },

                    {
                        "track": "SS-1",
                        "title": "Structures Session",
                        "location": "C102",
                        "session_chairs": ["Dr. Anup S", "Dr. Mathiazhagan S"]
                    },

                    {
                        "track": "SS-2",
                        "title": "Structures Session",
                        "location": "C106",
                        "session_chairs": ["Dr. Bijudas C R", "Dr. Sam Noble"]
                    },

                    {
                        "track": "SS-3",
                        "title": "Structures Session",
                        "location": "Admin Council Hall",
                        "session_chairs": ["Dr. Praveen Krishna", "Dr. Aswathy M S"]
                    },

                    {
                        "track": "MS-1",
                        "title": "Manufacturing Session",
                        "location": "C103",
                        "session_chairs": ["Dr. P Sasikumar", "Dr. S G K Manikandan"]
                    },

                    {
                        "track": "TS-2",
                        "title": "Thermal Session",
                        "location": "C104",
                        "session_chairs": [" Dr. Salih A", "Dr. Mahesh S "]
                    }
                ]
            },

            {
                "start_time": "16:20:00",
                "end_time": "16:30:00",
                "time_slot": "16:20 - 16:30",
                "event": "Tea Break",
                "location": "MPH"
            },

            {
                "start_time": "16:30:00",
                "end_time": "17:00:00",
                "time_slot": "16:30 - 17:00",
                "event": "MathWorks Talk & ANSYS Talk",
                "location": "MPH"
            },

            {
                "start_time": "17:00:00",
                "end_time": "18:30:00",
                "time_slot": "17:00 - 18:30",
                "event": "Lab Visit & Sky Watch",
                "location": "Interdisciplinary Labs & Aerospace Labs"
            },

            {
                "start_time": "18:30:00",
                "end_time": "19:30:00",
                "time_slot": "18:30 - 19:30",
                "event": "Cultural Night",
                "location": "SAC"
            }

        ]
    },

    # ──────────────────────────────────────────────────────────────
    # DAY 2
    # ──────────────────────────────────────────────────────────────
    {
        "day": "Day 2",
        "date": "05.06.2026",
        "sessions": [

            {
                "start_time": "09:00:00",
                "end_time": "09:50:00",
                "time_slot": "09:00 - 09:50",
                "event": "Keynote Session 4: Shock Transitions in Gases and Liquids",
                "speaker": "Prof. G Rajesh (IIT Madras)",
                "location": "MPH"
            },

            {
                "start_time": "09:50:00",
                "end_time": "10:40:00",
                "time_slot": "09:50 - 10:40",
                "event": "Keynote Session 5: Vision-Based Autonomous Landing",
                "speaker": "Prof. Abhishek (IIT Kanpur)",
                "location": "MPH"
            },

            {
                "start_time": "10:40:00",
                "end_time": "10:50:00",
                "time_slot": "10:40 - 10:50",
                "event": "Tea Break",
                "location": "MPH"
            },

            {
                "start_time": "10:50:00",
                "end_time": "12:50:00",
                "time_slot": "10:50 - 12:50",
                "event": "DASSAULT Session",
                "location": "MPH"
            },

            {
                "start_time": "12:50:00",
                "end_time": "13:40:00",
                "time_slot": "12:50 - 13:40",
                "event": "Lunch Break",
                "location": "SAC"
            },

            {
                "start_time": "13:40:00",
                "end_time": "14:30:00",
                "time_slot": "13:40 - 14:30",
                "event": "Keynote Session 6",
                "speaker": "Prof. M Ravi Sankar (IIT Tirupati)",
                "location": "MPH"
            },

            {
                "start_time": "14:30:00",
                "end_time": "16:00:00",
                "time_slot": "14:30 - 16:00",
                "event": "Workshops Session I",
                "parallel_tracks": [
                    {"track":"MATLAB","location":"D4 - CADD Lab"},
                    {"track":"ANSYS","location":"D1 - Computer Instructional Lab"},
                    {"track":"Advanced Manufacturing","location":"D1 - Language Lab"}
                ]
            },

            {
                "start_time": "16:00:00",
                "end_time": "16:10:00",
                "time_slot": "16:00 - 16:10",
                "event": "Tea Break",
                "location": "MPH"
            },

            {
                "start_time": "16:10:00",
                "end_time": "18:30:00",
                "time_slot": "16:10 - 18:30",
                "event": "Workshops Session II",
                "parallel_tracks": [
                    {"track":"MATLAB","location":"D4 - CADD Lab"},
                    {"track":"Advanced Manufacturing","location":"D1 - Language Lab"}
                ]
            },

            {
                "start_time": "19:00:00",
                "end_time": "20:30:00",
                "time_slot": "19:00 - 20:30",
                "event": "Networking Dinner",
                "location": "SAC"
            }

        ]
    },

    # ──────────────────────────────────────────────────────────────
    # DAY 3
    # ──────────────────────────────────────────────────────────────
    {
        "day": "Day 3",
        "date": "06.06.2026",
        "sessions": [

            {
                "start_time": "09:00",
                "end_time": "09:50",
                "time_slot": "09:00 - 09:50",
                "event": "Keynote Session 7: Physics-Informed Machine Learning in CFD",
                "speaker": "Dr. Madhukar M Rao (ACRI Infotech)",
                "location": "MPH"
            },

            {
                "start_time": "09:50",
                "end_time": "10:40",
                "time_slot": "09:50 - 10:40",
                "event": "Keynote Session 8: Fluid Structures Interaction",
                "speaker": "Prof. Sanjay Mittal (IIT Kanpur)",
                "location": "MPH"
            },

            {
                "start_time": "10:40",
                "end_time": "10:50",
                "time_slot": "10:40 - 10:50",
                "event": "Tea Break",
                "location": "MPH"
            },

            {
                "start_time": "10:50",
                "end_time": "12:50",
                "time_slot": "10:50 - 12:50",
                "event": "Paper Presentation Session 2",
                "parallel_tracks": [

                    {
                        "track": "TS-3",
                        "title": "Thermal Session",
                        "location": "Council Hall",
                        "session_chairs": ["Dr. Deepu M" , "Dr. Shine S R"]
                    },

                    {
                        "track": "AS-2",
                        "title": "Aerodynamics Session",
                        "location": "C106",
                        "session_chairs": [" Dr. Vinoth B R" , "Dr. Mahesh S"]
                    },

                    {
                        "track": "AS-3",
                        "title": "Aerodynamics Session",
                        "location": "Conference Hall",
                        "session_chairs": [" Dr. Sanjay Mittal", "Dr. Manoj T Nair"]
                    },

                    {
                        "track": "AS-4",
                        "title": "Aerodynamics Session",
                        "location": "C102",
                        "session_chairs": [" Shri. Dinesh Kumar M" ," Dr. Dhayalan"]
                    },

                    {
                        "track": "SS-4",
                        "title": "Structures Session",
                        "location": "C104",
                        "session_chairs": [" Dr. Praveen Krishna", "Dr. Sam Noble"]
                    },

                    {
                        "track": "MS-2",
                        "title": "Manufacturing Session",
                        "location": "Admin Council Hall",
                        "session_chairs": [" Dr. Mamilla Ravi Sankar", "Dr. Sooraj V S"]
                    },

                    {
                        "track": "MS-3",
                        "title": "Manufacturing Session",
                        "location": "C103",
                        "session_chairs": [" Dr. Anil Kumar", "Dr. Anoop M S"]
                    }
                ]
            },

            {
                "start_time": "12:30",
                "end_time": "13:30",
                "time_slot": "12:30 - 13:30",
                "event": "Lunch Break",
                "location": "SAC"
            },

            {
                "start_time": "13:00",
                "end_time": "15:00",
                "time_slot": "13:00 - 15:00",
                "event": "Paper Presentation Session 3",
                "parallel_tracks": [

                    {
                        "track": "TS-4",
                        "title": "Thermal Session",
                        "location": "Admin Council Hall",
                        "session_chairs": [" Dr. Madhukar M Rao" , "Dr. Pradeep Kumar"]
                    },

                    {
                        "track": "AS-5",
                        "title": "Aerodynamics Session",
                        "location": "Conference Hall",
                        "session_chairs": ["Dr. Manu KV", "Dr. Ashish Bhole"]
                    },

                    {
                        "track": "AS-6",
                        "title": "Aerodynamics Session",
                        "location": "C102",
                        "session_chairs": ["Dr. Satheesh K", "Dr. Devendra Prakash Ghate"]
                    },

                    {
                        "track": "SS-5",
                        "title": "Structures Session",
                        "location": "C106",
                        "session_chairs": [" Dr. N R Rajesh", "Dr. Digendranath Swain"]
                    },

                    {
                        "track": "SS-6",
                        "title": "Structures Session",
                        "location": "C103",
                        "session_chairs": ["Dr. A K Ashraf", "Dr. Raveendranath P"]
                    },

                    {
                        "track": "MS-4",
                        "title": "Manufacturing Session",
                        "location": "C104",
                        "session_chairs": ["Dr. Prabhakaran K", "Dr. Arun D I"]
                    }
                ]
            },

            {
                "start_time": "15:00",
                "end_time": "15:10",
                "time_slot": "15:00 - 15:10",
                "event": "Tea Break",
                "location": "MPH"
            },

            {
                "start_time": "15:10",
                "end_time": "16:00",
                "time_slot": "15:10 - 16:00",
                "event": "Keynote Session 9: Experiments for Studying Necking in Ductile Materials",
                "speaker": "Dr. Digendranath Swain (Vikram Sarabhai Space Centre, ISRO)",
                "location": "MPH"
            },

            {
                "start_time": "16:00",
                "end_time": "17:00",
                "time_slot": "16:00 - 17:00",
                "event": "Valedictory Function",
                "location": "MPH"
            }

        ]
    }
] 
_overrides = load_overrides()
if _overrides:
    CONFERENCE_SCHEDULE = apply_overrides(CONFERENCE_SCHEDULE, _overrides)

def _sched_live_events():
    today    = ist_now.date()
    now_time = ist_now.time()
    live = []
    for day_block in CONFERENCE_SCHEDULE:
        if _pd_date(day_block["date"]) != today:
            continue
        for s in day_block["sessions"]:
            st_t = _pt(s["start_time"])
            en_t = _pt(s["end_time"])
            if st_t <= now_time <= en_t:
                if "parallel_tracks" in s:
                    # Emit one live card per track
                    for tr in s["parallel_tracks"]:
                        live.append({
                            "event_name": s["event"] + "  —  " + tr["track"]
                                          + (f': {tr["title"]}' if tr.get("title") else ""),
                            "location":   tr["location"],
                            "speaker":    "",
                            "session_chairs": tr.get("session_chairs", []),
                            "end_time":   en_t.strftime("%H:%M"),
                        })
                else:
                    live.append({
                        "event_name": s["event"],
                        "location":   s.get("location", ""),
                        "speaker":    s.get("speaker", ""),
                        "session_chairs": [],
                        "end_time":   en_t.strftime("%H:%M"),
                    })
    return live


def _sched_next_event():
    today    = ist_now.date()
    now_time = ist_now.time()
    for day_block in CONFERENCE_SCHEDULE:
        if _pd_date(day_block["date"]) != today:
            continue
        for s in day_block["sessions"]:
            st_t = _pt(s["start_time"])
            if st_t > now_time:
                if "parallel_tracks" in s:
                    # Show the parent session name + track count hint
                    tracks = s["parallel_tracks"]
                    track_summary = ", ".join(
                        tr["track"] for tr in tracks[:4]
                    ) + ("…" if len(tracks) > 4 else "")
                    return {
                        "event_name": s["event"],
                        "location":   track_summary,   # shown as meta line
                        "speaker":    f"{len(tracks)} parallel tracks",
                        "start_time": st_t.strftime("%H:%M"),
                        "end_time":   _pt(s["end_time"]).strftime("%H:%M"),
                    }
                return {
                    "event_name": s["event"],
                    "location":   s.get("location", ""),
                    "speaker":    s.get("speaker", ""),
                    "start_time": st_t.strftime("%H:%M"),
                    "end_time":   _pt(s["end_time"]).strftime("%H:%M"),
                }
    return None
 
def _sched_conf_dates():
    return sorted([_pd_date(d["date"]) for d in CONFERENCE_SCHEDULE])
 
def _sched_next_event():
    today    = ist_now.date()
    now_time = ist_now.time()
    for day_block in CONFERENCE_SCHEDULE:
        if _pd_date(day_block["date"]) != today:
            continue
        for s in day_block["sessions"]:
            st_t = _pt(s["start_time"])
            if st_t > now_time:
                if "parallel_tracks" in s:
                    # Show the parent session name + track count hint
                    tracks = s["parallel_tracks"]
                    track_summary = ", ".join(
                        tr["track"] for tr in tracks[:4]
                    ) + ("…" if len(tracks) > 4 else "")
                    return {
                        "event_name": s["event"],
                        "location":   track_summary,   # shown as meta line
                        "speaker":    f"{len(tracks)} parallel tracks",
                        "start_time": st_t.strftime("%H:%M"),
                        "end_time":   _pt(s["end_time"]).strftime("%H:%M"),
                    }
                return {
                    "event_name": s["event"],
                    "location":   s.get("location", ""),
                    "speaker":    s.get("speaker", ""),
                    "start_time": st_t.strftime("%H:%M"),
                    "end_time":   _pt(s["end_time"]).strftime("%H:%M"),
                }
    return None

# ─── Conference Menu Data ─────────────────────────────────────────────────────
MENU_SCHEDULE = [
    # ── 03.06.2026 (Wednesday) ─────────────────────────────────────────────
    {
        "date": "03.06.2026",
        "day": "Wednesday",
        "meal": "Dinner",
        "menu_items": [
            "Veg. Salad", 
            "Kerala Paratha", 
            "Chamba Rice, Plain Rice, Ghee Rice", 
            "Dal Tadka, Pindi channa", 
            "Rasam, Curd, Pickle"
        ],
        "non_veg_options": ["🍗 Butter chicken"],
        "dessert_addons": ["cutfruits"]
    },

    # ── 04.06.2026 (Thursday) ──────────────────────────────────────────────
    {
        "date": "04.06.2026",
        "day": "Thursday",
        "meal": "Breakfast",
        "menu_items": [
            "Idli, Sambar, Chutney", 
            "Bread, Butter & Jam", 
            "Coffee"
        ],
        "non_veg_options": ["🥚 Boiled egg"],
        "dessert_addons": []
    },
    {
        "date": "04.06.2026",
        "day": "Thursday",
        "meal": "High Tea",
        "menu_items": ["Coffee/Tea, Kozhukkatta, Samosa, Savory"],
        "non_veg_options": [],
        "dessert_addons": []
    },
    {
        "date": "04.06.2026",
        "day": "Thursday",
        "meal": "Lunch",
        "menu_items": [
            "Chappathy", 
            "Plain Rice, Chamba Rice, Tomato Rice", 
            "Veg mezhukku", 
            "Dum Aloo with Paneer, Dal, Chow chow thoran", 
            "Rasam, Raitha, Pickle, Appalam"
        ],
        "non_veg_options": ["🍗 Chicken Korma"],
        "dessert_addons": ["Fruit custard"]
    },
    {
        "date": "04.06.2026",
        "day": "Thursday",
        "meal": "Coffee & Snacks",
        "menu_items": ["Coffee / Tea & Cutlet, Cookies"],
        "non_veg_options": [],
        "dessert_addons": []
    },
    {
        "date": "04.06.2026",
        "day": "Thursday",
        "meal": "Dinner",
        "menu_items": [
            "Veg. Salad", 
            "Chapathi", 
            "Plain Rice, Chamba Rice, Corn pulao", 
            "Veg Makhini with Paneer, Dal Tadka", 
            "Rasam, Curd, Pickle"
        ],
        "non_veg_options": ["🍗 Chicken Kuruma"],
        "dessert_addons": ["cutfruits"]
    },

    # ── 05.06.2026 (Friday) ────────────────────────────────────────────────
    {
        "date": "05.06.2026",
        "day": "Friday",
        "meal": "Breakfast",
        "menu_items": [
            "Idiyappam, Black channa curry", 
            "Bread, Butter & Jam", 
            "Coffee"
        ],
        "non_veg_options": ["🥚 Scrambled eggs"],
        "dessert_addons": []
    },
    {
        "date": "05.06.2026",
        "day": "Friday",
        "meal": "Tea & snacks",
        "menu_items": ["Coffee/Tea, Salt Cookies & Cake"],
        "non_veg_options": [],
        "dessert_addons": []
    },
    {
        "date": "05.06.2026",
        "day": "Friday",
        "meal": "Lunch",
        "menu_items": [
            "Chappathy", 
            "Plain Rice, Chamba Rice, Peas pulao", 
            "Veg kofta curry, Sambar, Dal tadka, Bindi Thoran", 
            "Rasam, Raitha, Pickle, Appalam"
        ],
        "non_veg_options": ["🐟 Fish curry"],
        "dessert_addons": ["Vermicelli payasam"]
    },
    {
        "date": "05.06.2026",
        "day": "Friday",
        "meal": "Coffee & Snacks",
        "menu_items": ["Coffee/Tea & Veg puffs, Savory"],
        "non_veg_options": [],
        "dessert_addons": []
    },
    {
        "date": "05.06.2026",
        "day": "Friday",
        "meal": "Gala Dinner",
        "menu_items": [
            "Welcome drinks, Veg. Salad, Pasta salad", 
            "Chapathi, Kerala Paratha", 
            "Chamba Rice, Plain Rice, Veg Biriyani", 
            "Mix veg subji, Paneer butter masala", 
            "Veg Mezhukku, Dal Tadka, Pulissery", 
            "Rasam, Raitha, Applam, Pickle"
        ],
        "non_veg_options": ["🐟 Kerala Fish Crry", "🍗 Kadai chicken"],
        "dessert_addons": ["Ada Pradaman", "cutfruits"]
    },

    # ── 06.06.2026 (Saturday) ──────────────────────────────────────────────
    {
        "date": "06.06.2026",
        "day": "Saturday",
        "meal": "Breakfast",
        "menu_items": [
            "Dosa, Sambar, Chutney", 
            "Bread, Butter & Jam", 
            "Coffee"
        ],
        "non_veg_options": ["🥚 Omlette"],
        "dessert_addons": []
    },
    {
        "date": "06.06.2026",
        "day": "Saturday",
        "meal": "Tea & snacks",
        "menu_items": ["Coffee/Tea, Bananafritters, Masala Cookies"],
        "non_veg_options": [],
        "dessert_addons": []
    },
    {
        "date": "06.06.2026",
        "day": "Saturday",
        "meal": "Lunch",
        "menu_items": [
            "Chappathy", 
            "Plain Rice, Chamba Rice, Veg pulao", 
            "Aloo jeera, Ozhichu curry, Veg mezhukku", 
            "Rasam, Raitha, Pickle, Appalam"
        ],
        "non_veg_options": ["🍗 Chicken Curry"],
        "dessert_addons": ["Muhallabia"]
    },
    {
        "date": "06.06.2026",
        "day": "Saturday",
        "meal": "Coffee & Snacks",
        "menu_items": ["Coffee/Tea & urud vada, Savory"],
        "non_veg_options": [],
        "dessert_addons": []
    },
    {
        "date": "06.06.2026",
        "day": "Saturday",
        "meal": "Dinner",
        "menu_items": [
            "Veg. Salad", 
            "Wheat paratha", 
            "Plain Rice, Chamba Rice, Jeera coconut pulao", 
            "Malai Kofta, Dal Tadka", 
            "Rasam, Curd, Pickle"
        ],
        "non_veg_options": ["🥚 Egg Masala"],
        "dessert_addons": ["cutfruits"]
    },

    # ── 07.06.2026 (Sunday) ────────────────────────────────────────────────
    {
        "date": "07.06.2026",
        "day": "Sunday",
        "meal": "Breakfast",
        "menu_items": [
            "Rava Upma, Green gram curry", 
            "Bread, Butter & Jam", 
            "Tea"
        ],
        "non_veg_options": ["🥚 Scrambled eggs"],
        "dessert_addons": []
    }
]
MEAL_ICONS = {
    "Breakfast":       "🌅",
    "High Tea":        "☕",
    "Lunch":           "🍛",
    "Coffee & Snacks": "🍪",
    "Dinner":          "🌙",
}
def _parse_menu_date(ds):
    """Parse DD.MM.YYYY → date object."""
    from datetime import date
    try:
        d, m, y = ds.split(".")
        return date(int(y), int(m), int(d))
    except Exception:
        return None
 
# Unique conference days in order
_MENU_DAYS = []
_seen = set()
for _e in MENU_SCHEDULE:
    if _e["date"] not in _seen:
        _MENU_DAYS.append({"date": _e["date"], "day": _e["day"]})
        _seen.add(_e["date"])

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

def render_info_card():
    info = CONFERENCE_INFO

    # ── WiFi ──────────────────────────────────────────────────────────────
    wifi_rows = ""
    for w in info["wifi"]:
        wifi_rows += (
            f'<div class="wifi-row">'
            f'  <div>'
            f'    <div class="wifi-label">📶 {w["label"]}</div>'
            f'    <div class="wifi-ssid">{w["ssid"]}</div>'
            f'  </div>'
            f'  <div class="wifi-right">'
            f'    <span class="wifi-pass" '
            f'          id="wpass_{w["ssid"].replace(" ","_")}"'
            f'          onclick="'
            f'            navigator.clipboard.writeText(\'{w["password"]}\');\''
            f'            .then(()=>{{this.innerHTML=\'✅ Copied!\';setTimeout(()=>{{this.innerHTML=\'{w["password"]}\'}},1500)}});\''
            f'          " '
            f'          title="Tap to copy password"'
            f'          style="cursor:pointer;user-select:all;">'
            f'      {w["password"]}'
            f'    </span>'
            f'  </div>'
            f'</div>'
        )

    # ── Contacts ──────────────────────────────────────────────────────────
    contact_rows = ""
    for c in info["contacts"]:
        # Strip spaces/dashes for tel: URI
        raw_number = c["value"].split("·")[0].strip()
        tel_number = raw_number.replace(" ", "").replace("-", "")
        call_btn = (
            f'<a href="tel:{tel_number}" class="call-btn">📞 Call</a>'
            if tel_number.startswith("+") or tel_number.startswith("0")
            else ""
        )
        contact_rows += (
            f'<div class="info-row">'
            f'  <span class="info-row-icon">{c["icon"]}</span>'
            f'  <span class="info-row-label">{c["label"]}</span>'
            f'  <span class="info-row-value">{c["value"]}</span>'
            f'  {call_btn}'
            f'</div>'
        )

    st.markdown(
        f'<div class="info-card">'

        f'<div class="info-section-title">📶 &nbsp;WiFi Access</div>'
        + wifi_rows +

        f'<div class="info-section-title" style="margin-top:1.2rem;">📞 &nbsp;Emergency Contacts</div>'
        f'<div style="background:{T["bg3"]};border:0.5px solid {T["border"]};'
        f'border-radius:8px;padding:4px 12px;">'
        + contact_rows +
        f'</div>'

        f'</div>',
        unsafe_allow_html=True,
    )

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

:root {{
    --fs-scale: {st.session_state.font_size / 100};
}}
html, body, [class*="css"] {{
    font-family: 'Barlow', sans-serif !important;
    color: {T['text']};
    font-size: calc(16px * {st.session_state.font_size / 100}) !important;
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
.astra-logo  {{font-family:'Barlow Condensed',sans-serif; font-size:2.1em; font-weight:700; color:{T['accent']}; line-height:1;}}
.astra-yr    {{font-family:'Barlow Condensed',sans-serif; font-size:0.9em; color:{T['muted']}; letter-spacing:0.1em;}}
.astra-div   {{width:0.5px; height:30px; background:{T['border']};}}
.astra-full  {{font-size:0.78em; color:{T['muted']}; line-height:1.4; max-width:210px;}}
.astra-full strong {{color:{T['text']}; font-weight:500; font-size:0.85em; display:block;}}

.live-badge {{
    display:flex; align-items:center; gap:6px;
    background:rgba(239,68,68,0.10);
    border:0.5px solid rgba(239,68,68,0.28);
    border-radius:20px; padding:5px 14px;
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.78em; font-weight:600; color:#f87171; letter-spacing:0.1em;
}}
.pulse-dot {{
    width:7px; height:7px; border-radius:50%; background:#ef4444;
    display:inline-block; animation:blink 1.4s ease-in-out infinite;
}}
@keyframes blink {{0%,100%{{opacity:1;}}50%{{opacity:0.25;}}}}

.page-wrap {{padding:1.75rem 2.5rem 0; max-width:1200px; margin:0 auto;}}

.sec-head {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.78em; font-weight:600; letter-spacing:0.14em;
    text-transform:uppercase; color:{T['muted']};
    margin:1.5rem 0 1rem; padding:0 1rem;
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
    font-size:1.9em; font-weight:700; color:{T['head']}; line-height:1.15;
}}
.hero-title span {{color:{T['accent']};}}
.hero-sub  {{font-size:0.85em; color:{T['muted']}; margin-top:6px; line-height:1.55;}}
.stat-row  {{display:flex; gap:2rem; margin-top:1rem; flex-wrap:wrap;}}
.stat-n    {{font-family:'Barlow Condensed',sans-serif; font-size:1.5em; font-weight:700; color:{T['accent']};}}
.stat-l    {{font-size:0.72em; color:{T['muted']}; text-transform:uppercase; letter-spacing:0.08em;}}

.live-grid  {{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:1.5rem;}}
.live-card  {{
    flex:1; min-width:150px;
    background:{T['card']};
    border:0.5px solid {T['border']};
    border-radius:10px;
    padding:12px 14px;
    display:flex; align-items:flex-start; gap:10px;
}}
.lc-name  {{font-size:0.85em; font-weight:500; color:{T['head']};}}
.lc-venue {{font-size:0.72em; color:{T['muted']}; margin-top:2px;}}
.lc-time  {{font-family:'Barlow Condensed',sans-serif; font-size:0.72em; color:{T['accent']}; margin-top:4px; letter-spacing:0.06em;}}

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
    font-size:0.85em; font-weight:600; color:{T['accent']}; flex-shrink:0;
}}
.rname {{font-size:0.95em; font-weight:500; color:{T['head']};}}
.rid   {{font-size:0.78em; color:{T['muted']};}}
.dtile-grid {{display:grid; grid-template-columns:1fr 1fr; gap:8px;}}
.dtile {{background:{T['bg3']}; border-radius:8px; padding:10px 12px;}}
.dtile-l {{font-size:0.72em; color:{T['muted']}; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px;}}
.dtile-v {{font-size:0.9em; font-weight:500; color:{T['text']};}}
.dtile-hi{{font-size:0.9em; font-weight:500; color:{T['accent']};}}

.folder-info {{
    background:{T['bg2']};
    border:0.5px solid {T['border']};
    border-radius:10px; padding:1rem 1.25rem;
    font-size:0.85em; color:{T['muted']}; line-height:1.7;
    margin-bottom:1.25rem;
}}
.folder-info strong {{color:{T['text']}; font-weight:500;}}
.folder-info code {{
    font-size:0.78em;
    background:{T['bg3']};
    border:0.5px solid {T['border']};
    border-radius:4px; padding:1px 6px;
    color:{T['accent']};
}}

.poster-meta {{padding:8px 10px 12px;}}
.p-title {{font-size:0.85em; font-weight:500; color:{T['head']}; line-height:1.3;}}
.p-track {{font-family:'Barlow Condensed',sans-serif; font-size:0.72em; color:{T['accent']}; letter-spacing:0.08em; text-transform:uppercase; margin-top:3px;}}
.p-file  {{font-size:0.72em; color:{T['muted']}; margin-top:2px;}}

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
    line-height: 1; padding:0 1rem;
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
.stime  {{font-family:'Barlow Condensed',sans-serif; font-size:0.85em; color:{T['accent']}; min-width:120px; letter-spacing:0.04em; padding-top:1px;}}
.sname  {{font-size:0.9em; font-weight:500; color:{T['head']};}}
.svenue {{font-size:0.78em; color:{T['muted']}; margin-top:2px;}}
.sspkr  {{font-size:0.72em; color:{T['muted']}; margin-top:3px; font-style:italic;}}
.stag   {{
    display:inline-block;
    background:{T['tagbg']}; color:{T['tagc']};
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.72em; padding:3px 9px; border-radius:4px;
    letter-spacing:0.06em; text-transform:uppercase; white-space:nowrap;
    margin-left:auto; flex-shrink:0;
}}

.parallel-grid {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:8px;
    margin-top:10px;
}}

.parallel-card {{
    background:{T['bg3']};
    border:0.5px solid {T['border']};
    border-radius:8px;
    padding:10px 12px;
    transition:all 0.15s ease;
}}

.parallel-card:hover {{
    border-color:{T['accent']};
    transform:translateY(-1px);
}}

.parallel-track {{
    display:inline-block;
    background:{T['tagbg']};
    color:{T['tagc']};
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.72em;
    font-weight:700;
    letter-spacing:0.08em;
    text-transform:uppercase;
    padding:3px 8px;
    border-radius:4px;
    margin-bottom:6px;
}}

.parallel-title {{
    font-size:0.85em;
    font-weight:500;
    color:{T['head']};
    line-height:1.35;
}}

.parallel-location {{
    font-size:0.72em;
    color:{T['muted']};
    margin-top:5px;
}}

.parallel-header {{
    margin-top:10px;
    margin-bottom:4px;
    font-size:0.78em;
    color:{T['muted']};
    letter-spacing:0.04em;
}}

.stTextInput > div > div > input {{
    background:{T['bg3']} !important;
    border:0.5px solid {T['border']} !important;
    color:{T['text']} !important;
    border-radius:8px !important;
    font-size:0.9em !important;
    font-family:'Barlow',sans-serif !important;
}}
.stTextInput > div > div > input:focus {{
    border-color:{T['accent']} !important;
    box-shadow:none !important;
}}
.stTextInput label {{color:{T['muted']} !important; font-size:0.85em !important;}}

.stButton > button {{
    background:{T['accent']} !important;
    color:#fff !important;
    border:none !important;
    border-radius:8px !important;
    font-size:0.85em !important;
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
.stSelectbox label {{color:{T['muted']} !important; font-size:0.85em !important;}}

.stTabs [data-baseweb="tab-list"] {{
    background:{T['bg2']} !important;
    border-bottom:0.5px solid {T['border']} !important;
    gap:0 !important;
    padding: 0 2.5rem !important;
}}
.stTabs [data-baseweb="tab"] {{
    font-family:'Barlow Condensed',sans-serif !important;
    font-size:0.9em !important;
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
    font-size:0.72em; font-weight:600; letter-spacing:0.07em;
    text-decoration:none; text-transform:uppercase;
    transition:background 0.15s;
}}
.nav-btn:hover {{ background:{T['accent']}33; color:{T['accent']}; text-decoration:none; }}
/* ── Menu section ── */
.menu-section {{
    background:{T['bg2']};
    border:0.5px solid {T['border']};
    border-radius:12px;
    padding:1.25rem 1.4rem;
    margin-bottom:1rem;
}}
.menu-meal-header {{
    display:flex; align-items:center; gap:10px;
    margin-bottom:10px;
    padding-bottom:8px;
    border-bottom:0.5px solid {T['border']};
}}
.menu-meal-icon {{ font-size:20px; }}
.menu-meal-name {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:1em; font-weight:700; color:{T['head']};
    text-transform:uppercase; letter-spacing:0.08em;
}}
.menu-item {{
    font-size:0.85em; color:{T['text']};
    padding:3px 0; display:flex; align-items:baseline; gap:8px;
}}
.menu-item::before {{ content:'·'; color:{T['accent']}; font-weight:700; }}
.menu-tag {{
    display:inline-block; margin-top:8px; margin-right:5px;
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.72em; padding:3px 10px; border-radius:4px;
    letter-spacing:0.06em; text-transform:uppercase;
}}
.menu-tag.nonveg {{
    background:rgba(239,68,68,0.10); color:#f87171;
    border:0.5px solid rgba(239,68,68,0.25);
}}
.menu-tag.dessert {{
    background:rgba(168,85,247,0.10); color:#c084fc;
    border:0.5px solid rgba(168,85,247,0.25);
}}
.menu-day-header {{
    background:{T['bg3']};
    border:0.5px solid {T['border']};
    border-radius:10px;
    padding:10px 16px;
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:1rem;
}}
.menu-day-title {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:1.1em; font-weight:700; color:{T['head']};
}}
.menu-day-date {{
    font-size:0.78em; color:{T['muted']};
}}
.menu-no-data {{
    text-align:center; padding:2rem 1rem;
    color:{T['muted']}; font-size:0.85em;
}}

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
.campus-name {{ font-size:0.9em; font-weight:500; color:{T['head']}; }}
.campus-note {{ font-size:0.78em; color:{T['muted']}; margin-top:3px; line-height:1.5; }}
.cat-pill {{
    display:inline-block;
    background:{T['tagbg']}; color:{T['tagc']};
    font-family:'Barlow Condensed',sans-serif;
    font-size:10px; padding:2px 8px; border-radius:4px;
    letter-spacing:0.07em; text-transform:uppercase;
    margin-bottom:4px;
}}

/* ── Info Card ── */
.info-card {{
    background: {T['bg2']};
    border: 0.5px solid {T['border']};
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}}
.info-section-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: {T['muted']};
    margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
}}
.info-section-title::after {{
    content: ''; flex: 1; height: 0.5px; background: {T['border']};
}}
.wifi-row {{
    background: {T['bg3']};
    border: 0.5px solid {T['border']};
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 8px;
    display: flex; align-items: center;
    justify-content: space-between; gap: 12px;
    flex-wrap: wrap;
}}
.wifi-label {{
    font-size: 11px; color: {T['muted']};
    text-transform: uppercase; letter-spacing: 0.07em;
    margin-bottom: 3px;
}}
.wifi-ssid {{
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 17px; font-weight: 700; color: {T['head']};
}}
.wifi-right {{
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}}
.wifi-pass {{
    font-family: monospace;
    font-size: 14px; color: {T['accent']};
    background: {T['tagbg']};
    border: 0.5px solid {T['accent']}44;
    border-radius: 6px; padding: 5px 14px;
    letter-spacing: 0.08em; white-space: nowrap;
    cursor: pointer;
    user-select: all;
    transition: background 0.15s, color 0.15s;
}}
.wifi-pass:hover {{
    background: {T['accent']}22;
    border-color: {T['accent']}88;
}}

.wifi-connect-btn:hover {{ opacity: 0.82; }}
.info-row {{
    display: flex; align-items: center; gap: 10px;
    padding: 8px 0;
    border-bottom: 0.5px solid {T['border']};
    font-size: 13px;
}}
.info-row:last-child {{ border-bottom: none; }}
.info-row-icon  {{ font-size: 16px; flex-shrink: 0; width: 24px; text-align: center; }}
.info-row-label {{ color: {T['muted']}; min-width: 130px; font-size: 12px; }}
.info-row-value {{ color: {T['text']}; font-weight: 500; }}
.call-btn {{
    margin-left: auto;
    display: inline-flex; align-items: center; gap: 5px;
    background: {T['tagbg']};
    border: 0.5px solid {T['accent']}55;
    color: {T['accent']} !important;
    border-radius: 6px; padding: 4px 12px;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 12px; font-weight: 600;
    letter-spacing: 0.07em; text-transform: uppercase;
    text-decoration: none !important;
    white-space: nowrap;
}}
.call-btn:hover {{ background: {T['accent']}22; }}
 
/* ── Up Next card ── */
.upnext-wrap {{
    margin-top: 10px;
    margin-bottom: 4px;
}}
.upnext-label {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:0.72em; font-weight:700; letter-spacing:0.14em;
    text-transform:uppercase; color:{T['muted']};
    display:flex; align-items:center; gap:8px;
    margin-bottom:6px; padding:0 1rem;
}}
.upnext-label::after {{content:''; flex:1; height:0.5px; background:{T['border']};}}
.upnext-card {{
    background:{T['bg3']};
    border:0.5px solid {T['border']};
    border-left: 2px solid {T['accent']};
    border-radius:8px;
    padding:10px 14px;
    display:flex; align-items:center; gap:12px;
}}
.upnext-time-badge {{
    flex-shrink:0;
    background:{T['tagbg']};
    border:0.5px solid {T['accent']}55;
    border-radius:6px;
    padding:5px 10px;
    text-align:center;
}}
.upnext-time-starts {{
    font-size:10px; color:{T['muted']};
    font-family:'Barlow Condensed',sans-serif;
    letter-spacing:0.08em; text-transform:uppercase;
}}
.upnext-time-val {{
    font-family:'Barlow Condensed',sans-serif;
    font-size:1.1em; font-weight:700; color:{T['accent']};
    line-height:1.1;
}}
.upnext-name {{ font-size:0.85em; font-weight:500; color:{T['head']}; }}
.upnext-meta {{ font-size:0.72em; color:{T['muted']}; margin-top:2px; }}

/* ── Font size controls ── */
[data-testid="stButton"] > button[kind="secondary"] {{
    font-family: 'Barlow Condensed', sans-serif !important;
}}
 
""", unsafe_allow_html=True)

# ─── Top Bar ──────────────────────────────────────────────────────────────────
top_left, top_mid, top_right = st.columns([5, 2, 1])
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
with top_mid:
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        if st.button("𝐀−", key="font_down",
                     disabled=st.session_state.font_size <= 80,
                     use_container_width=True):
            st.session_state.font_size = max(80, st.session_state.font_size - 10)
            st.rerun()
    with f_col2:
        if st.button(
            f"{st.session_state.font_size}%",
            key="font_reset",
            use_container_width=True,
            help="Click to reset to default size"
        ):
            st.session_state.font_size = 100
            st.rerun()
    with f_col3:
        if st.button("𝐀+", key="font_up",
                     disabled=st.session_state.font_size >= 140,
                     use_container_width=True):
            st.session_state.font_size = min(140, st.session_state.font_size + 10)
            st.rerun()
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
    "⚙️  Admin",
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

    def _live_card(name, location, spkr, end_str, chairs=None):
        spkr_ln = (
            '<div class="lc-venue" style="font-style:italic;">'
            + spkr
            + '</div>'
        ) if spkr else ""
        chairs_ln = ""
        if chairs:
            chairs_joined = " · ".join(c.strip() for c in chairs)
            chairs_ln = (
                '<div style="font-size:0.72em;margin-top:5px;'
                'background:rgba(100,200,100,0.07);'
                'border-left:2px solid rgba(100,200,100,0.4);'
                'border-radius:0 4px 4px 0;padding:3px 8px;">'
                '<span style="font-size:10px;letter-spacing:0.07em;'
                'text-transform:uppercase;color:rgba(100,200,100,0.7);">Session Chairs</span><br>'
                '<span style="font-style:italic;">' + chairs_joined + '</span>'
                '</div>'
            )
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
            + chairs_ln
            + '<div class="lc-time">Ends ' + end_str + '</div>'
            + nav_btn
            + '</div></div>'
        )

    live_evs  = _sched_live_events()
    next_ev   = _sched_next_event()
 
    if live_evs:
        cards_html = '<div class="live-grid">'
        for ev in live_evs:
            cards_html += _live_card(ev["event_name"], ev["location"], ev["speaker"], ev["end_time"],chairs=ev.get("session_chairs", []),)
        cards_html += '</div>'
        st.markdown(cards_html, unsafe_allow_html=True)
    else:
        today_now      = ist_now.date()
        conf_dates_sorted = _sched_conf_dates()
        if conf_dates_sorted and today_now < conf_dates_sorted[0]:
            first = conf_dates_sorted[0].strftime("%B %d, %Y")
            msg = (
                '<p style="color:' + T["muted"] + ';font-size:0.85em;margin-top:0;padding:0 15px;">'
                + 'Conference begins on <strong style="color:' + T["text"] + ';">' + first + '</strong>. '
                + 'Check the Schedule tab for the full programme.</p>'
            )
        elif conf_dates_sorted and today_now > conf_dates_sorted[-1]:
            msg = (
                '<p style="color:' + T["muted"] + ';font-size:0.85em;margin-top:0;padding:0 15px;">'
                'The conference has concluded. Thank you for attending ASTRA 2026.</p>'
            )
        else:
            msg = (
                '<p style="color:' + T["muted"] + ';font-size:0.85em;margin-top:0;padding:0 15px;">'
                'No sessions are active right now. Check the Schedule tab for the full timeline.</p>'
            )
        st.markdown(msg, unsafe_allow_html=True)
 
    # ── Up Next ────────────────────────────────────────────────────────────
    if next_ev:
        spkr_meta = next_ev["location"]
        if next_ev["speaker"]:
            spkr_meta += "  ·  " + next_ev["speaker"]
        nav = venue_maps_url(next_ev["location"])
        upnext_html = (
            '<div class="upnext-wrap">'
            '<div class="upnext-label">Up next</div>'
            '<div class="upnext-card">'
            '<div class="upnext-time-badge">'
            '<div class="upnext-time-starts">Starts</div>'
            '<div class="upnext-time-val">' + next_ev["start_time"] + '</div>'
            '</div>'
            '<div style="flex:1;">'
            '<div class="upnext-name">' + next_ev["event_name"] + '</div>'
            '<div class="upnext-meta">' + spkr_meta + '</div>'
            '</div>'
            '<a href="' + nav + '" target="_blank" class="nav-btn">📍 Navigate</a>'
            '</div></div>'
        )
        st.markdown(upnext_html, unsafe_allow_html=True)

    # ── Info Card ─────────────────────────────────────────────
    st.markdown('<div class="sec-head">Conference info</div>', unsafe_allow_html=True)
    render_info_card()

     # ── Today's Menu ──────────────────────────────────────────────────────────
    st.markdown('<div class="sec-head">Conference menu</div>', unsafe_allow_html=True)
 
    today_date = ist_now.date()
 
    # Figure out which day index to show
    conf_day_dates = [_parse_menu_date(d["date"]) for d in _MENU_DAYS]
    # Find today's index in the conference days, else clamp offset
    try:
        today_idx = conf_day_dates.index(today_date)
    except ValueError:
        # Today not in conf days — find nearest future day
        future = [i for i, d in enumerate(conf_day_dates) if d and d >= today_date]
        today_idx = future[0] if future else 0
 
    display_idx = max(0, min(len(_MENU_DAYS) - 1, today_idx + st.session_state.menu_day_offset))
    display_day = _MENU_DAYS[display_idx]
    display_meals = [m for m in MENU_SCHEDULE if m["date"] == display_day["date"]]
 
    # Navigation row
    nav_l, nav_mid, nav_r = st.columns([1, 4, 1])
    with nav_l:
        if st.button("← Prev", key="menu_prev", disabled=(display_idx == 0), width="stretch"):
            st.session_state.menu_day_offset -= 1
            st.rerun()
    with nav_mid:
        is_today  = (_parse_menu_date(display_day["date"]) == today_date)
        day_label = ("Today · " if is_today else "") + display_day["day"] + "  " + display_day["date"]
        st.markdown(
            '<div class="menu-day-header">'
            + '<span class="menu-day-title">' + ("🍽️  " if is_today else "") + display_day["day"] + '</span>'
            + '<span class="menu-day-date">' + display_day["date"] + ('  ·  <strong style="color:#3b9eff;">TODAY</strong>' if is_today else "") + '</span>'
            + '</div>',
            unsafe_allow_html=True,
        )
    with nav_r:
        if st.button("Next →", key="menu_next", disabled=(display_idx == len(_MENU_DAYS) - 1), width="stretch"):
            st.session_state.menu_day_offset += 1
            st.rerun()
 
    if not display_meals:
        st.markdown('<div class="menu-no-data">No menu data available for this day.</div>', unsafe_allow_html=True)
    else:
        # Show 2 meals per row
        for i in range(0, len(display_meals), 2):
            pair = display_meals[i:i+2]
            cols = st.columns(len(pair))
            for col, meal in zip(cols, pair):
                with col:
                    icon = MEAL_ICONS.get(meal["meal"], "🍽️")
                    items_html = "".join(
                        '<div class="menu-item">' + item + '</div>'
                        for item in meal["menu_items"]
                    )
                    tags_html = ""
                    if meal["non_veg_options"]:
                        tags_html += "".join(
                            '<span class="menu-tag nonveg">' + nv + '</span>'
                            for nv in meal["non_veg_options"]
                        )
                    if meal["dessert_addons"]:
                        tags_html += "".join(
                            '<span class="menu-tag dessert">🍮 ' + d + '</span>'
                            for d in meal["dessert_addons"]
                        )
                    st.markdown(
                        '<div class="menu-section">'
                        + '<div class="menu-meal-header">'
                        + '<span class="menu-meal-icon">' + icon + '</span>'
                        + '<span class="menu-meal-name">' + meal["meal"] + '</span>'
                        + '</div>'
                        + items_html
                        + (('<div style="margin-top:8px;">' + tags_html + '</div>') if tags_html else "")
                        + '</div>',
                        unsafe_allow_html=True,
                    )
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
            f'<div style="font-size:0.95em;font-weight:500;color:{T["text"]};margin-bottom:6px;">No posters found</div>'
            f'<div style="font-size:0.85em;">No poster images were found in the posters/ folder.</div>'
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


    def render_schedule_group(group_rows):
        from itertools import groupby as igrp

        group_rows.sort(key=lambda r: r["start_key"])
        for _, slot_iter in igrp(group_rows, key=lambda r: r["start_key"]):
            slot = list(slot_iter)

            # ── Single (non-parallel) event ──────────────────────────────────
            if len(slot) == 1 and not slot[0].get("is_parallel"):
                row = slot[0]
                spkr_html = f'<div class="sspkr">🎤 {row["speaker"]}</div>' if row["speaker"] else ""
                st.markdown(
                    '<div class="srow">'
                    f'<div class="stime">{row["display_time"]}</div>'
                    '<div style="flex:1;">'
                    f'<div class="sname">{row["event_name"]}</div>'
                    f'<div class="svenue">{row["location"]}</div>'
                    + spkr_html +
                    '</div></div>',
                    unsafe_allow_html=True,
                )

            # ── Parallel tracks ───────────────────────────────────────────────
            else:
                event_name = slot[0]["event_name"]
                time_label = slot[0]["display_time"]

                track_cards = ""
                for row in slot:
                    track_id    = row["track"]
                    track_title = row.get("track_title", "")
                    venue       = row["location"]
                    chairs      = row.get("session_chairs", [])
                    nav_url     = venue_maps_url(venue)

                    title_line = (
                        f'<div style="font-size:0.78em;color:{T["muted"]};margin-top:2px;">{track_title}</div>'
                        if track_title else ""
                    )
                    chairs_line = ""
                    if chairs:
                        chairs_joined = " &nbsp;·&nbsp; ".join(c.strip() for c in chairs)
                        chairs_line = (
                            f'<div style="font-size:0.72em;margin-top:5px;'
                            f'background:rgba(100,200,100,0.07);'
                            f'border-left:2px solid rgba(100,200,100,0.4);'
                            f'border-radius:0 4px 4px 0;padding:3px 8px;">'
                            f'<span style="font-size:10px;letter-spacing:0.07em;'
                            f'text-transform:uppercase;color:rgba(100,200,100,0.7);">'
                            f'Session Chairs</span><br>'
                            f'<span style="color:{T["text"]};font-style:italic;">'
                            f'{chairs_joined}</span>'
                            f'</div>'
                        )
                    track_cards += (
                        f'<div class="parallel-card">'
                        f'<span class="parallel-track">{track_id}</span>'
                        + title_line +
                        f'<div class="parallel-location">📍 {venue}</div>'
                        + chairs_line +
                        f'<a href="{nav_url}" target="_blank" class="nav-btn" style="margin-top:6px;">Navigate</a>'
                        f'</div>'
                    )

                st.markdown(
                    f'<div class="srow">'
                    f'<div class="stime">{time_label}</div>'
                    f'<div style="flex:1;">'
                    f'<div class="sname">{event_name}</div>'
                    f'<div class="parallel-header">'
                    f'Parallel tracks — choose your session:</div>'
                    f'<div class="parallel-grid">{track_cards}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="sec-head">Full schedule</div>', unsafe_allow_html=True)
    today_sched = ist_now.date()
    for day_block in CONFERENCE_SCHEDULE:
        d_date    = _pd_date(day_block["date"])
        is_today  = (d_date == today_sched)
        date_disp = d_date.strftime("%b %d, %Y")
        today_badge = ' &nbsp;<span style="font-size:10px;background:#3b9eff22;color:#3b9eff;border-radius:4px;padding:2px 8px;letter-spacing:0.07em;">TODAY</span>' if is_today else ""
        st.markdown(
            '<div class="day-header">' +
            '<span class="day-label">' + day_block["day"] + '</span>' +
            '<span class="day-date">' + date_disp + today_badge + '</span>' +
            '</div>',
            unsafe_allow_html=True,
        )
        rows = []
        for s in day_block["sessions"]:
            if "parallel_tracks" in s:
                # One row per track, all sharing the same start_key
                for tr in s["parallel_tracks"]:
                    rows.append({
                        "start_key":    s["start_time"][:5],
                        "display_time": s["time_slot"],
                        "event_name":   s["event"],
                        "track":        tr["track"],
                        "track_title":  tr.get("title", ""),
                        "location":     tr["location"],
                        "session_chairs": tr.get("session_chairs", []),
                        "speaker":      "",
                        "is_parallel":  True,
                    })
            else:
                rows.append({
                    "start_key":    s["start_time"][:5],
                    "display_time": s["time_slot"],
                    "event_name":   s["event"],
                    "track":        s.get("track", ""),
                    "track_title":  "",
                    "location":     s.get("location", ""),
                    "session_chairs": [],
                    "speaker":      s.get("speaker", ""),
                    "is_parallel":  False,
                })
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
with tab_admin:
    render_admin_tab(CONFERENCE_SCHEDULE, T)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="text-align:center;padding:2.5rem 0 1rem;font-size:0.72em;'
    f'color:{T["muted"]};font-family:\'Barlow Condensed\',sans-serif;letter-spacing:0.08em;">'
    f'ASTRA 2026 · Live Conference Schedule Subsystem · 3rd Edition</div>',
    unsafe_allow_html=True,
)