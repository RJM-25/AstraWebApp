"""
admin_schedule.py
─────────────────
Drop-in admin tab for ASTRA 2026 Streamlit app.
Paste the render_admin_tab() call inside your admin tab block.

Features
────────
• Password-protected admin login (uses st.secrets["ADMIN_PASSWORD"])
• Edit any event name / location / speaker
• Change start time → all following events on that day shift by the same delta
• Change end time   → validates it doesn't exceed next event's start
• Parallel track location editing
• Changes saved to schedule_overrides.json (loaded at app start to patch
  CONFERENCE_SCHEDULE in-memory — no original data file is touched)
• Full reset button to wipe all overrides
• Poster upload (with optional subfolder/track) and delete
"""

import json
import hmac
import shutil
import streamlit as st
from pathlib import Path
from datetime import datetime, time as dtime, timedelta
from copy import deepcopy

OVERRIDES_PATH = Path("schedule_overrides.json")
POSTER_DIR     = Path("posters")
SUPPORTED_EXT  = {".jpg", ".jpeg", ".png", ".webp"}

# ─────────────────────────────────────────────────────────────────────────────
# Poster helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_all_posters():
    """
    Returns list of dicts:
      { path, name, track, rel_path (str, relative to posters/) }
    Root-level files -> track = "General"
    Sub-folder files -> track = folder name (title-cased)
    """
    if not POSTER_DIR.exists():
        return []
    result = []
    for f in sorted(POSTER_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXT:
            result.append({
                "path":     f,
                "name":     f.stem.replace("-", " ").replace("_", " ").title(),
                "track":    "General",
                "rel_path": f.name,
            })
    for sub in sorted(POSTER_DIR.iterdir()):
        if sub.is_dir():
            track = sub.name.replace("-", " ").replace("_", " ").title()
            for f in sorted(sub.iterdir()):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXT:
                    result.append({
                        "path":     f,
                        "name":     f.stem.replace("-", " ").replace("_", " ").title(),
                        "track":    track,
                        "rel_path": f"{sub.name}/{f.name}",
                    })
    return result


def _get_tracks():
    """Return existing track folder names (title-cased), sorted."""
    if not POSTER_DIR.exists():
        return []
    return sorted(
        sub.name.replace("-", " ").replace("_", " ").title()
        for sub in POSTER_DIR.iterdir()
        if sub.is_dir()
    )


def _track_to_folder(track):
    """'Thermal Session' -> 'thermal-session'."""
    return track.strip().lower().replace(" ", "-")


def _save_poster(uploaded_file, track):
    """
    Save uploaded_file into posters/ (General) or posters/<track-folder>/.
    Returns the saved Path.
    """
    POSTER_DIR.mkdir(exist_ok=True)
    if track == "General":
        dest_dir = POSTER_DIR
    else:
        dest_dir = POSTER_DIR / _track_to_folder(track)
        dest_dir.mkdir(exist_ok=True)

    safe_name = uploaded_file.name.replace(" ", "_")
    dest = dest_dir / safe_name

    counter = 1
    stem    = dest.stem
    suffix  = dest.suffix
    while dest.exists():
        dest = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    dest.write_bytes(uploaded_file.getbuffer())
    return dest


def _delete_poster(rel_path):
    """Delete posters/<rel_path>. Returns True on success."""
    target = POSTER_DIR / rel_path
    if target.exists() and target.is_file():
        target.unlink()
        parent = target.parent
        if parent != POSTER_DIR and not any(parent.iterdir()):
            parent.rmdir()
        return True
    return False

# ─────────────────────────────────────────────────────────────────────────────
# Persistence helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_overrides() -> dict:
    if not OVERRIDES_PATH.exists():
        return {}
    try:
        return json.loads(OVERRIDES_PATH.read_text())
    except Exception:
        return {}


def save_overrides(data: dict):
    OVERRIDES_PATH.write_text(json.dumps(data, indent=2))


def apply_overrides(schedule: list, overrides: dict) -> list:
    """
    Returns a deep-copied schedule with overrides patched in.
    Override keys: "day_index:session_index" → dict of field patches
    Track overrides: "day_index:session_index:track_index" → dict
    """
    schedule = deepcopy(schedule)
    for key, patch in overrides.items():
        parts = key.split(":")
        if len(parts) == 2:
            di, si = int(parts[0]), int(parts[1])
            try:
                session = schedule[di]["sessions"][si]
                session.update(patch)
            except (IndexError, KeyError):
                pass
        elif len(parts) == 3:
            di, si, ti = int(parts[0]), int(parts[1]), int(parts[2])
            try:
                track = schedule[di]["sessions"][si]["parallel_tracks"][ti]
                track.update(patch)
            except (IndexError, KeyError):
                pass
    return schedule


# ─────────────────────────────────────────────────────────────────────────────
# Time helpers
# ─────────────────────────────────────────────────────────────────────────────

def _to_minutes(t_str: str) -> int:
    """'HH:MM' or 'HH:MM:SS' → total minutes since midnight."""
    parts = t_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _from_minutes(m: int) -> str:
    """Total minutes → 'HH:MM:SS'."""
    m = max(0, min(m, 23 * 60 + 59))
    return f"{m // 60:02d}:{m % 60:02d}:00"


def _fmt_display(t_str: str) -> str:
    """'HH:MM:SS' → 'HH:MM'."""
    parts = t_str.strip().split(":")
    return f"{parts[0]}:{parts[1]}"


def _time_slot(start: str, end: str) -> str:
    return f"{_fmt_display(start)} - {_fmt_display(end)}"


def shift_following_sessions(day_sessions: list, from_index: int, delta_minutes: int, overrides: dict, day_index: int):
    """
    Shift start_time, end_time, time_slot of all sessions AFTER from_index
    by delta_minutes (can be negative).  Writes results into overrides.
    """
    for si in range(from_index, len(day_sessions)):
        s = day_sessions[si]
        new_start = _from_minutes(_to_minutes(s["start_time"]) + delta_minutes)
        new_end   = _from_minutes(_to_minutes(s["end_time"])   + delta_minutes)
        key = f"{day_index}:{si}"
        if key not in overrides:
            overrides[key] = {}
        overrides[key]["start_time"] = new_start
        overrides[key]["end_time"]   = new_end
        overrides[key]["time_slot"]  = _time_slot(new_start, new_end)


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

def _check_admin_password(entered: str) -> bool:
    try:
        correct = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        correct = "admin2026"          # fallback if secrets not set
    return hmac.compare_digest(entered.strip(), correct.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Main renderer  (call this inside your admin tab)
# ─────────────────────────────────────────────────────────────────────────────

def render_admin_tab(CONFERENCE_SCHEDULE: list, T: dict):
    """
    Parameters
    ──────────
    CONFERENCE_SCHEDULE : the original schedule list from your main app
    T                   : your active theme palette dict
    """

    # ── Auth gate ────────────────────────────────────────────────────────────
    if "admin_authed" not in st.session_state:
        st.session_state.admin_authed = False

    if not st.session_state.admin_authed:
        st.markdown(
            f"""
            <div style="max-width:380px;margin:4rem auto;
                        background:{T['bg2']};border:0.5px solid {T['border']};
                        border-radius:14px;padding:2rem 2.2rem;">
              <div style="font-family:'Barlow Condensed',sans-serif;
                          font-size:22px;font-weight:700;color:{T['head']};
                          margin-bottom:4px;">🔒 Admin Access</div>
              <div style="font-size:12px;color:{T['muted']};margin-bottom:1.4rem;">
                  ASTRA 2026 · Schedule Management
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            pwd = st.text_input("Admin password", type="password", key="admin_pwd_input")
            if st.button("Login", key="admin_login_btn", use_container_width=True):
                if _check_admin_password(pwd):
                    st.session_state.admin_authed = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        return

    # ── Load overrides & build working schedule ───────────────────────────────
    overrides = load_overrides()
    working   = apply_overrides(CONFERENCE_SCHEDULE, overrides)

    # ── Header ───────────────────────────────────────────────────────────────
    h_col, btn_col = st.columns([5, 1])
    with h_col:
        st.markdown(
            f'<div style="font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:26px;font-weight:700;color:{T["head"]};'
            f'padding:1.2rem 2.5rem 0.5rem;">'
            f'⚙️ &nbsp;Schedule Admin Panel</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", key="admin_logout"):
            st.session_state.admin_authed = False
            st.rerun()

    # ── Reset all overrides ───────────────────────────────────────────────────
    with st.expander("⚠️  Danger Zone — Reset all schedule changes", expanded=False):
        st.warning("This will revert every edit back to the original schedule.")
        if st.button("🗑️  Reset ALL overrides", key="reset_all"):
            save_overrides({})
            st.success("All overrides cleared. Reload the app to see changes.")
            st.rerun()

    st.markdown(
        f'<div style="height:0.5px;background:{T["border"]};margin:0.5rem 2.5rem 1.5rem;"></div>',
        unsafe_allow_html=True,
    )

    # ── Day selector ─────────────────────────────────────────────────────────
    day_labels = [f'{d["day"]}  ·  {d["date"]}' for d in working]
    selected_day_label = st.selectbox(
        "Select day to edit",
        day_labels,
        key="admin_day_sel",
    )
    day_index  = day_labels.index(selected_day_label)
    day_block  = working[day_index]
    orig_block = CONFERENCE_SCHEDULE[day_index]

    st.markdown(
        f'<div style="font-family:\'Barlow Condensed\',sans-serif;'
        f'font-size:14px;color:{T["muted"]};padding:0.25rem 0 1rem;">'
        f'{len(day_block["sessions"])} sessions on this day</div>',
        unsafe_allow_html=True,
    )

    # ── Session list ─────────────────────────────────────────────────────────
    for si, session in enumerate(day_block["sessions"]):
        orig_session = orig_block["sessions"][si]
        session_key  = f"{day_index}:{si}"
        is_parallel  = "parallel_tracks" in session

        # Collapsible per session
        with st.expander(
            f'**{session["time_slot"]}** — {session["event"]}',
            expanded=False,
        ):

            # ── Time editing ─────────────────────────────────────────────────
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                f'text-transform:uppercase;color:{T["muted"]};margin-bottom:8px;">'
                f'⏱ Time</div>',
                unsafe_allow_html=True,
            )

            t_col1, t_col2, t_col3 = st.columns([2, 2, 3])

            cur_start_m = _to_minutes(session["start_time"])
            cur_end_m   = _to_minutes(session["end_time"])

            with t_col1:
                new_start_str = st.text_input(
                    "Start time (HH:MM)",
                    value=_fmt_display(session["start_time"]),
                    key=f"start_{day_index}_{si}",
                )
            with t_col2:
                new_end_str = st.text_input(
                    "End time (HH:MM)",
                    value=_fmt_display(session["end_time"]),
                    key=f"end_{day_index}_{si}",
                )
            with t_col3:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                apply_time = st.button(
                    "✅ Apply & cascade",
                    key=f"apply_time_{day_index}_{si}",
                    use_container_width=True,
                )

            if apply_time:
                # ── Parse inputs ─────────────────────────────────────────────
                try:
                    nh, nm = [int(x) for x in new_start_str.strip().split(":")]
                    new_start_m = nh * 60 + nm
                except ValueError:
                    st.error("Invalid start time format. Use HH:MM")
                    st.stop()
                try:
                    eh, em = [int(x) for x in new_end_str.strip().split(":")]
                    new_end_m = eh * 60 + em
                except ValueError:
                    st.error("Invalid end time format. Use HH:MM")
                    st.stop()

                # ── Validate end > start ──────────────────────────────────────
                if new_end_m <= new_start_m:
                    st.error("End time must be after start time.")
                    st.stop()

                # ── Check end doesn't exceed next session's original start ─────
                if si + 1 < len(day_block["sessions"]):
                    next_start_m = _to_minutes(day_block["sessions"][si + 1]["start_time"])
                    if new_end_m > next_start_m:
                        st.error(
                            f"End time {new_end_str} exceeds next session's "
                            f"start ({_fmt_display(day_block['sessions'][si+1]['start_time'])}). "
                            f"Use Apply & cascade to shift following sessions instead."
                        )
                        st.stop()

                # ── Compute delta on START time for cascade ───────────────────
                start_delta = new_start_m - cur_start_m
                end_delta   = new_end_m   - cur_end_m

                # Patch this session
                if session_key not in overrides:
                    overrides[session_key] = {}
                overrides[session_key]["start_time"] = _from_minutes(new_start_m)
                overrides[session_key]["end_time"]   = _from_minutes(new_end_m)
                overrides[session_key]["time_slot"]  = _time_slot(
                    _from_minutes(new_start_m), _from_minutes(new_end_m)
                )

                # Cascade start delta to all following sessions
                if start_delta != 0 and si + 1 < len(day_block["sessions"]):
                    shift_following_sessions(
                        day_block["sessions"],
                        from_index=si + 1,
                        delta_minutes=start_delta,
                        overrides=overrides,
                        day_index=day_index,
                    )

                save_overrides(overrides)
                st.success(
                    f"✅ Time updated. "
                    + (
                        f"{len(day_block['sessions']) - si - 1} following session(s) "
                        f"shifted by {start_delta:+d} min."
                        if start_delta != 0 else "No cascade needed."
                    )
                )
                st.rerun()

            # ── Event name ───────────────────────────────────────────────────
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                f'text-transform:uppercase;color:{T["muted"]};margin:12px 0 6px;">'
                f'📝 Event Details</div>',
                unsafe_allow_html=True,
            )

            n_col1, n_col2 = st.columns([4, 1])
            with n_col1:
                new_name = st.text_input(
                    "Event name",
                    value=session["event"],
                    key=f"name_{day_index}_{si}",
                )
            with n_col2:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("Save", key=f"save_name_{day_index}_{si}", use_container_width=True):
                    if session_key not in overrides:
                        overrides[session_key] = {}
                    overrides[session_key]["event"] = new_name
                    save_overrides(overrides)
                    st.success("Event name updated.")
                    st.rerun()

            # ── Location / Speaker (non-parallel only) ───────────────────────
            if not is_parallel:
                l_col1, l_col2 = st.columns([4, 1])
                with l_col1:
                    new_loc = st.text_input(
                        "Location",
                        value=session.get("location", ""),
                        key=f"loc_{day_index}_{si}",
                    )
                with l_col2:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("Save", key=f"save_loc_{day_index}_{si}", use_container_width=True):
                        if session_key not in overrides:
                            overrides[session_key] = {}
                        overrides[session_key]["location"] = new_loc
                        save_overrides(overrides)
                        st.success("Location updated.")
                        st.rerun()

                if "speaker" in orig_session or session.get("speaker"):
                    s_col1, s_col2 = st.columns([4, 1])
                    with s_col1:
                        new_spkr = st.text_input(
                            "Speaker",
                            value=session.get("speaker", ""),
                            key=f"spkr_{day_index}_{si}",
                        )
                    with s_col2:
                        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                        if st.button("Save", key=f"save_spkr_{day_index}_{si}", use_container_width=True):
                            if session_key not in overrides:
                                overrides[session_key] = {}
                            overrides[session_key]["speaker"] = new_spkr
                            save_overrides(overrides)
                            st.success("Speaker updated.")
                            st.rerun()

            # ── Parallel tracks ──────────────────────────────────────────────
            if is_parallel:
                st.markdown(
                    f'<div style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                    f'text-transform:uppercase;color:{T["muted"]};margin:12px 0 8px;">'
                    f'🔀 Parallel Tracks</div>',
                    unsafe_allow_html=True,
                )
                for ti, track in enumerate(session["parallel_tracks"]):
                    track_key = f"{day_index}:{si}:{ti}"
                    with st.container():
                        st.markdown(
                            f'<div style="background:{T["bg3"]};border:0.5px solid {T["border"]};'
                            f'border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
                            f'<span style="font-family:\'Barlow Condensed\',sans-serif;'
                            f'font-size:13px;font-weight:700;color:{T["accent"]};">'
                            f'{track["track"]}</span>'
                            f'<span style="font-size:12px;color:{T["muted"]};margin-left:8px;">'
                            f'{track.get("title","")}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        tr_c1, tr_c2, tr_c3 = st.columns([2, 2, 1])
                        with tr_c1:
                            new_tr_loc = st.text_input(
                                "Location",
                                value=track.get("location", ""),
                                key=f"trloc_{day_index}_{si}_{ti}",
                            )
                        with tr_c2:
                            chairs = track.get("session_chairs", [])
                            new_chairs_str = st.text_input(
                                "Session chairs (comma separated)",
                                value=", ".join(chairs),
                                key=f"trchair_{day_index}_{si}_{ti}",
                            )
                        with tr_c3:
                            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                            if st.button("Save", key=f"save_tr_{day_index}_{si}_{ti}", use_container_width=True):
                                if track_key not in overrides:
                                    overrides[track_key] = {}
                                overrides[track_key]["location"] = new_tr_loc
                                overrides[track_key]["session_chairs"] = [
                                    c.strip() for c in new_chairs_str.split(",") if c.strip()
                                ]
                                save_overrides(overrides)
                                st.success(f"Track {track['track']} updated.")
                                st.rerun()

            # ── Revert this session ───────────────────────────────────────────
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            if st.button(
                f"↩️ Revert session to original",
                key=f"revert_{day_index}_{si}",
            ):
                # Remove all keys belonging to this session and its tracks
                keys_to_del = [
                    k for k in list(overrides.keys())
                    if k == session_key or k.startswith(f"{session_key}:")
                ]
                for k in keys_to_del:
                    del overrides[k]
                save_overrides(overrides)
                st.success("Session reverted to original.")
                st.rerun()

    # ── Override summary ─────────────────────────────────────────────────────
    if overrides:
        with st.expander(f"📋 Active overrides ({len(overrides)} keys)", expanded=False):
            st.json(overrides)

    # ═══════════════════════════════════════════════════════════════════════
    # POSTER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="height:1px;background:{T["border"]};margin:2rem 0 1.5rem;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="font-family:\'Barlow Condensed\',sans-serif;'        f'font-size:22px;font-weight:700;color:{T["head"]};margin-bottom:1rem;">'        f'🖼️ &nbsp;Poster Management</div>',
        unsafe_allow_html=True,
    )

    render_poster_admin(T)


def render_poster_admin(T: dict):
    """
    Poster upload + delete section.
    Call standalone or via render_admin_tab (which calls it automatically).
    Requires admin auth to already be confirmed by the parent.
    """

    posters = _get_all_posters()
    tracks  = _get_tracks()

    # ── Upload section ────────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:{T["bg2"]};border:0.5px solid {T["border"]};'        f'border-radius:12px;padding:1.2rem 1.4rem;margin-bottom:1.5rem;">'        f'<div style="font-size:11px;font-weight:700;letter-spacing:0.12em;'        f'text-transform:uppercase;color:{T["muted"]};margin-bottom:12px;">'        f'📤 Upload Posters</div>',
        unsafe_allow_html=True,
    )

    up_col1, up_col2 = st.columns([3, 2])
    with up_col1:
        uploaded_files = st.file_uploader(
            "Choose image files (JPG, PNG, WEBP)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="poster_uploader",
        )
    with up_col2:
        track_options = ["General"] + tracks + ["+ New track"]
        selected_track = st.selectbox(
            "Upload to track / folder",
            track_options,
            key="poster_track_sel",
        )

        new_track_name = ""
        if selected_track == "+ New track":
            new_track_name = st.text_input(
                "New track name",
                placeholder="e.g. Aerodynamics",
                key="new_track_input",
            )

    st.markdown("</div>", unsafe_allow_html=True)

    target_track = new_track_name.strip() if selected_track == "+ New track" else selected_track

    if uploaded_files:
        if st.button(
            f"💾 Save {len(uploaded_files)} file(s) to '{target_track}'",
            key="poster_save_btn",
            type="primary",
        ):
            if not target_track:
                st.error("Please enter a track name.")
            else:
                saved = []
                errors = []
                for uf in uploaded_files:
                    try:
                        p = _save_poster(uf, target_track)
                        saved.append(p.name)
                    except Exception as e:
                        errors.append(f"{uf.name}: {e}")
                if saved:
                    st.success(f"✅ Saved {len(saved)} poster(s): {', '.join(saved)}")
                if errors:
                    for err in errors:
                        st.error(err)
                st.rerun()

    # ── Existing posters grid ─────────────────────────────────────────────
    if not posters:
        st.markdown(
            f'<div style="text-align:center;padding:3rem 1rem;color:{T["muted"]};'            f'font-size:13px;">No posters yet. Upload some above.</div>',
            unsafe_allow_html=True,
        )
        return

    # Group by track
    from collections import defaultdict
    by_track = defaultdict(list)
    for p in posters:
        by_track[p["track"]].append(p)

    track_order = ["General"] + sorted(t for t in by_track if t != "General")

    for track in track_order:
        if track not in by_track:
            continue
        track_posters = by_track[track]

        st.markdown(
            f'<div style="font-size:11px;font-weight:700;letter-spacing:0.12em;'            f'text-transform:uppercase;color:{T["muted"]};'            f'margin:1.2rem 0 0.8rem;'            f'display:flex;align-items:center;gap:10px;">'            f'{track} &nbsp;<span style="font-weight:400;font-size:10px;">'            f'({len(track_posters)} file(s))</span>'            f'<span style="flex:1;height:0.5px;background:{T["border"]};display:inline-block;margin-left:6px;"></span>'            f'</div>',
            unsafe_allow_html=True,
        )

        COLS = 4
        for i in range(0, len(track_posters), COLS):
            row_items = track_posters[i:i + COLS]
            cols = st.columns(COLS)
            for col, poster in zip(cols, row_items):
                with col:
                    # Thumbnail
                    st.image(str(poster["path"]), use_container_width=True)

                    # File name
                    st.markdown(
                        f'<div style="font-size:12px;font-weight:500;'                        f'color:{T["head"]};margin:4px 0 2px;'                        f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'                        f'max-width:100%;" title="{poster["name"]}">'                        f'{poster["name"]}</div>'                        f'<div style="font-size:10px;color:{T["muted"]};margin-bottom:6px;">'                        f'{poster["path"].name}</div>',
                        unsafe_allow_html=True,
                    )

                    # Delete button — uses a confirm pattern via session_state
                    del_key     = f"del_{poster['rel_path'].replace('/', '_').replace('.', '_')}"
                    confirm_key = f"confirm_{del_key}"

                    if st.session_state.get(confirm_key):
                        # Second click confirms
                        dc1, dc2 = st.columns(2)
                        with dc1:
                            if st.button("✅ Yes", key=f"yes_{del_key}", use_container_width=True):
                                if _delete_poster(poster["rel_path"]):
                                    st.session_state[confirm_key] = False
                                    st.success(f"Deleted {poster['path'].name}")
                                    st.rerun()
                                else:
                                    st.error("Delete failed.")
                        with dc2:
                            if st.button("❌ No", key=f"no_{del_key}", use_container_width=True):
                                st.session_state[confirm_key] = False
                                st.rerun()
                    else:
                        if st.button(
                            "🗑️ Delete",
                            key=del_key,
                            use_container_width=True,
                        ):
                            st.session_state[confirm_key] = True
                            st.rerun()