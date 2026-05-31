"""Shared utilities for all ScheduleMD pages."""
import os
import json
import re
import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# LOGO
# ---------------------------------------------------------------------------

def logo_html(size: str = "md", clickable_home: bool = True) -> str:
    """Returns inline HTML for the ScheduleMD logo."""
    sizes = {"sm": ("22px","0.95em"), "md": ("28px","1.1em"), "lg": ("42px","1.7em")}
    box, txt = sizes.get(size, sizes["md"])
    href = "/" if clickable_home else "#"
    p = _t()["primary"]
    return (
        f"<a href='/{href}' style='display:inline-flex;align-items:center;"
        f"gap:9px;text-decoration:none'>"
        f"<span style='background:{p};color:#fff;border-radius:8px;"
        f"width:{box};height:{box};display:inline-flex;align-items:center;"
        f"justify-content:center;font-weight:900;font-size:calc({box} * 0.55);"
        f"flex-shrink:0'>✚</span>"
        f"<span style='font-weight:800;font-size:{txt};color:{p};"
        f"letter-spacing:-0.02em;white-space:nowrap'>ScheduleMD</span>"
        f"</a>"
    )

# ---------------------------------------------------------------------------
# THEME SYSTEM
# ---------------------------------------------------------------------------

THEMES = {
    "Light": {
        "primary":  "#2d8a4e", "primary2": "#48b06a",
        "bg":       "#ffffff", "bg2":      "#f2f8f4",
        "text":     "#1a2e1f", "muted":    "#5a7a62",
        "border":   "#c8e0d0", "card":     "#ffffff",
        "header_bg":"rgba(255,255,255,0.96)",
        "tab_bg": "#e8f5ec", "tab_text": "#2d6b42",
        "metric_bg": "#ffffff", "metric_border": "#c8e0d0",
        "chat_bg": "#f5faf6", "chat_border": "#c8e0d0",
        "bubble_user_bg": "#2d8a4e", "bubble_user_text": "#ffffff",
        "bubble_bot_bg":  "#ffffff", "bubble_bot_text":  "#1a2e1f",
        "bubble_border":  "#d4e8d9",
        "app_bg": "",
        "urg_hi":  ("#ffd6d6","#cc0000","#cc0000","#fff0f0","#ffaaaa","#1a1a1a"),
        "urg_med": ("#fff8d6","#cc8800","#cc8800","#fffcf0","#ffe08a","#1a1a1a"),
        "urg_lo":  ("#d6f5d6","#007700","#007700","#f0fff0","#90ee90","#1a1a1a"),
    },
    "Dark": {
        "primary":  "#4db870", "primary2": "#2d8a4e",
        "bg":       "#0d1f14", "bg2":      "#162a1e",
        "text":     "#e8f5ec", "muted":    "#8ab896",
        "border":   "#1e3a28", "card":     "#162a1e",
        "header_bg":"rgba(13,31,20,0.96)",
        "tab_bg": "#162a1e", "tab_text": "#8ab896",
        "metric_bg": "#162a1e", "metric_border": "#1e3a28",
        "chat_bg": "#162a1e", "chat_border": "#1e3a28",
        "bubble_user_bg": "#4db870", "bubble_user_text": "#ffffff",
        "bubble_bot_bg":  "#1e3a28", "bubble_bot_text":  "#e8f5ec",
        "bubble_border":  "#1e3a28",
        "app_bg": "background-color:#0d1f14 !important; color:#e8f5ec !important;",
        "urg_hi":  ("#3a1a1a","#e05555","#ff9999","#2a1010","#883333","#f0d0d0"),
        "urg_med": ("#2a2510","#c49a00","#f0c030","#1e1c0a","#7a6000","#f0e8b0"),
        "urg_lo":  ("#1a2e1a","#3a9a3a","#66cc66","#111e11","#2a6a2a","#c0f0c0"),
    },
    "White": {
        "primary":  "#1a6b38", "primary2": "#2d8a4e",
        "bg":       "#ffffff", "bg2":      "#f9fdfb",
        "text":     "#111111", "muted":    "#4a6655",
        "border":   "#ddeee3", "card":     "#ffffff",
        "header_bg":"rgba(255,255,255,0.97)",
        "tab_bg": "#f0f7f3", "tab_text": "#1a6b38",
        "metric_bg": "#ffffff", "metric_border": "#ddeee3",
        "chat_bg": "#f9fdfb", "chat_border": "#ddeee3",
        "bubble_user_bg": "#1a6b38", "bubble_user_text": "#ffffff",
        "bubble_bot_bg":  "#ffffff", "bubble_bot_text":  "#111111",
        "bubble_border":  "#ddeee3",
        "app_bg": "background-color:#ffffff;",
        "urg_hi":  ("#ffd6d6","#cc0000","#cc0000","#fff0f0","#ffaaaa","#1a1a1a"),
        "urg_med": ("#fff8d6","#cc8800","#cc8800","#fffcf0","#ffe08a","#1a1a1a"),
        "urg_lo":  ("#d6f5d6","#007700","#007700","#f0fff0","#90ee90","#1a1a1a"),
    },
    "Access": {
        "primary":  "#0072b2", "primary2": "#0091d9",
        "bg":       "#f6f6f6", "bg2":      "#edf3f8",
        "text":     "#0a0a0a", "muted":    "#4f6070",
        "border":   "#a0bdd4", "card":     "#ffffff",
        "header_bg":"rgba(246,246,246,0.96)",
        "tab_bg": "#dce9f5", "tab_text": "#002a44",
        "metric_bg": "#ffffff", "metric_border": "#a0bdd4",
        "chat_bg": "#f0f4f8", "chat_border": "#a0bdd4",
        "bubble_user_bg": "#0072b2", "bubble_user_text": "#ffffff",
        "bubble_bot_bg":  "#ffffff", "bubble_bot_text":  "#0a0a0a",
        "bubble_border":  "#b8cfe0",
        "app_bg": "background-color:#f6f6f6;",
        "urg_hi":  ("#fbeccc","#e69f00","#8a5a00","#fdf4e0","#e69f00","#2a1a00"),
        "urg_med": ("#d4e7f4","#0072b2","#004c78","#e8f2fb","#0072b2","#002040"),
        "urg_lo":  ("#e2e2e2","#555555","#222222","#f0f0f0","#aaaaaa","#1a1a1a"),
    },
}

FONT_ZOOM   = {"Small": "0.88", "Medium": "1.0", "Large": "1.14"}
_FONT_OPTS  = ["Small", "Medium", "Large"]
_COLOR_OPTS = ["Light", "Dark", "White", "Access"]


def _t() -> dict:
    return THEMES[st.session_state.get("_theme_color", "Light")]


def apply_theme():
    t = _t()
    zoom = FONT_ZOOM[st.session_state.get("_theme_font", "Medium")]
    p = t["primary"]; bdr = t["border"]; bg = t["bg2"]
    m = t["muted"]; txt = t["text"]; card = t["card"]
    hbg = t["header_bg"]

    st.markdown(f"""
<style>
  /* ── Hide Streamlit default chrome ── */
  header[data-testid="stHeader"] {{ display:none !important; }}
  #MainMenu {{ visibility:hidden !important; }}
  footer {{ visibility:hidden !important; }}
  [data-testid="stSidebar"] {{ display:none !important; }}
  [data-testid="collapsedControl"] {{ display:none !important; }}
  [data-testid="stSidebarNav"] {{ display:none !important; }}

  /* ── Full-width layout ── */
  .stApp {{ zoom:{zoom}; {t["app_bg"]} }}
  .block-container {{
    max-width:100% !important;
    padding:0 !important;
  }}
  section[data-testid="stMain"] {{ padding:0 !important; }}

  /* ── Fixed footer (pure HTML element, no Streamlit) ── */
  #smd-footer {{
    position:fixed; bottom:0; left:0; right:0; height:44px;
    z-index:998; background:{hbg};
    backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
    border-top:1px solid {bdr};
    display:flex; align-items:center; justify-content:space-between;
    padding:0 28px; font-size:.76em; color:{m};
  }}

  /* ── Sticky green header ── */
  #smd-header {{
    position:sticky; top:0; z-index:999;
    background:linear-gradient(135deg,{p},{t["primary2"]});
    box-shadow:0 2px 16px rgba(0,0,0,.15);
    padding:0 28px;
    display:flex; align-items:center; justify-content:space-between;
    gap:10px;
  }}

  /* ── Content wrapper ── */
  #smd-content {{ padding:16px 0 52px 0; }}

  /* ── Header nav buttons — white text on green ── */
  #smd-nav-row .stButton > button {{
    background:transparent !important; border:none !important;
    border-bottom:2px solid transparent !important;
    border-radius:0 !important; color:rgba(255,255,255,.82) !important;
    font-weight:600 !important; font-size:.9em !important;
    padding:16px 14px !important;
    box-shadow:none !important; transform:none !important;
    transition:color .15s, border-color .15s !important;
  }}
  #smd-nav-row .stButton > button:hover {{
    color:#fff !important; background:rgba(255,255,255,.12) !important;
    border-bottom:2px solid #fff !important;
    box-shadow:none !important; transform:none !important;
  }}
  /* Logo button — bold white */
  #smd-nav-row [data-testid="column"]:first-child .stButton > button {{
    color:#fff !important; font-weight:900 !important;
    font-size:1.1em !important; border-bottom:none !important;
    padding:16px 8px !important; letter-spacing:-0.01em !important;
    text-shadow:0 1px 3px rgba(0,0,0,.2) !important;
  }}
  /* Gear popover — white on green */
  #smd-nav-row [data-testid="stPopover"] > button {{
    background:rgba(255,255,255,.18) !important;
    border:1.5px solid rgba(255,255,255,.4) !important;
    border-radius:8px !important; color:#fff !important;
    padding:6px 10px !important; margin:8px 0 !important;
    box-shadow:none !important; transform:none !important;
  }}
  #smd-nav-row [data-testid="stPopover"] > button:hover {{
    background:rgba(255,255,255,.3) !important;
    border-color:#fff !important;
  }}

  /* ── Regular page buttons ── */
  .stButton > button {{
    border-radius:8px; font-weight:600;
    border:1.5px solid {p}; color:{p}; background:transparent;
    transition:all .15s ease;
  }}
  .stButton > button:hover {{
    background:{p} !important; color:#fff !important;
    transform:translateY(-1px);
    box-shadow:0 4px 14px -4px {p}88;
  }}

  /* ── Inputs ── */
  .stSelectbox > div > div, .stMultiSelect > div > div {{
    border-radius:8px !important; border-color:{bdr} !important;
    background:{card} !important;
  }}
  .stTextInput > div > div > input, .stTextArea textarea {{
    border-radius:8px !important; background:{card} !important;
    border-color:{bdr} !important; color:{txt} !important;
  }}

  /* ── Metrics ── */
  [data-testid="stMetric"] {{
    background:{card}; border:1px solid {bdr};
    border-radius:12px; padding:16px 18px;
    box-shadow:0 2px 8px -4px rgba(0,0,0,.06);
  }}
  [data-testid="stMetricValue"] {{ font-size:1.8em !important; font-weight:800; color:{p}; }}
  [data-testid="stMetricLabel"] {{ font-size:.76em !important; font-weight:600; opacity:.55;
    text-transform:uppercase; letter-spacing:.1em; }}

  /* ── DataFrame ── */
  [data-testid="stDataFrame"] {{
    border-radius:12px; border:1px solid {bdr};
    box-shadow:0 2px 8px -4px rgba(0,0,0,.06); overflow:hidden;
  }}
  [data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius:12px !important; border-color:{bdr} !important;
    background:{bg} !important;
  }}

  /* ── Typography ── */
  h1,h2,h3 {{ letter-spacing:-0.02em; color:{txt}; }}
  hr {{ border-color:{bdr}; margin:8px 0; }}
  [data-testid="stPopover"] > div {{ border-radius:12px !important; }}

  /* ── Chat FAB — high visibility ── */
  #smd-chat-fab {{
    position:fixed; bottom:58px; right:28px; z-index:9999;
    width:64px; height:64px; border-radius:50%;
    background:{p};
    border:4px solid #ffffff;
    box-shadow:0 4px 24px rgba(0,0,0,.35), 0 0 0 2px {p}66;
    display:flex; align-items:center; justify-content:center;
    cursor:pointer; font-size:26px;
    transition:transform .18s, box-shadow .18s;
    text-decoration:none; color:#fff;
  }}
  #smd-chat-fab:hover {{
    transform:scale(1.12);
    box-shadow:0 6px 32px rgba(0,0,0,.4), 0 0 0 4px {p}44;
  }}
</style>""", unsafe_allow_html=True)


def render_header(current_page: str = ""):
    """
    Sticky header: HTML shell (#smd-header) wraps a Streamlit columns row
    (#smd-nav-row) so position:sticky works and the nav buttons stay in flow.
    """
    # Open the sticky header shell
    st.markdown("<div id='smd-header'>", unsafe_allow_html=True)
    st.markdown("<div id='smd-nav-row'>", unsafe_allow_html=True)

    c_logo, c_sp, c_about, c_fb, c_cal, c_gear = st.columns(
        [2.2, 2.5, 0.9, 0.9, 0.9, 0.5]
    )
    with c_logo:
        if st.button("✚  ScheduleMD", key="hdr_logo"):
            st.session_state.page = "home"; st.rerun()
    with c_about:
        if st.button("About Us",  key="hdr_about", use_container_width=True):
            st.session_state.page = "about"; st.rerun()
    with c_fb:
        if st.button("Feedback",  key="hdr_fb",    use_container_width=True):
            st.session_state.page = "feedback"; st.rerun()
    with c_cal:
        if st.button("Calendar",  key="hdr_cal",   use_container_width=True):
            st.session_state.page = "calendar"; st.rerun()
    with c_gear:
        with st.popover("⚙️", use_container_width=True):
            st.markdown("**Display Settings**")
            st.caption("Font Size")
            st.radio("fs", _FONT_OPTS, horizontal=True,
                     key="_theme_font", label_visibility="collapsed")
            st.caption("Color Theme")
            st.radio("ct", _COLOR_OPTS, key="_theme_color",
                     label_visibility="collapsed")
            st.caption("*Access* = Okabe-Ito — colorblind-safe.")
            st.divider()
            st.markdown("**AI Mode**")
            st.toggle("Demo mode only", key="demo_mode",
                      help="Force demo responses — no API calls made.")

    st.markdown("</div></div>", unsafe_allow_html=True)

    # JS to apply green background + sticky to the header row's DOM wrapper
    t2 = _t()
    p_hex  = t2["primary"]
    p2_hex = t2["primary2"]
    import streamlit.components.v1 as _components
    _components.html(f"""
<script>
(function() {{
  var pg = "{p_hex}", pg2 = "{p2_hex}";
  function applyHeader() {{
    var doc = window.parent.document;
    // Find first stHorizontalBlock (our header columns)
    var hb = doc.querySelector('[data-testid="stHorizontalBlock"]');
    if (!hb) return;
    // Walk up to the element-container wrapper
    var wrapper = hb.parentElement;
    if (!wrapper) return;
    wrapper.style.setProperty('background','linear-gradient(135deg,'+pg+','+pg2+')','important');
    wrapper.style.setProperty('position','sticky','important');
    wrapper.style.setProperty('top','0','important');
    wrapper.style.setProperty('z-index','999','important');
    wrapper.style.setProperty('box-shadow','0 2px 16px rgba(0,0,0,.14)','important');
    wrapper.style.setProperty('padding','0 24px','important');
    // White text on all buttons in the header
    hb.querySelectorAll('button').forEach(function(b) {{
      b.style.setProperty('color','#fff','important');
      b.style.setProperty('border-color','transparent','important');
      b.style.setProperty('background','transparent','important');
      b.style.setProperty('font-weight','700','important');
    }});
    // Logo button — extra bold
    var logoBtns = hb.querySelectorAll('[data-testid="column"]:first-child button');
    logoBtns.forEach(function(b) {{
      b.style.setProperty('font-weight','900','important');
      b.style.setProperty('font-size','1.05em','important');
    }});
  }}
  applyHeader();
  setInterval(applyHeader, 250);
}})();
</script>
""", height=0)

    # Open the content wrapper (closed by render_footer)
    st.markdown("<div id='smd-content'>", unsafe_allow_html=True)


def render_footer():
    """Closes the content wrapper and renders the fixed footer."""
    t = _t(); p = t["primary"]
    year = date.today().year
    st.markdown("</div>", unsafe_allow_html=True)  # close #smd-content
    st.markdown(
        f"<div id='smd-footer'>"
        f"<span>© {year} <strong style='color:{p}'>ScheduleMD</strong>"
        f" · HackJPS 2026 · Healthcare Track</span>"
        f"<span>Built with ❤️ for better healthcare scheduling</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

DOCTORS = ["Dr. Smith", "Dr. Jones", "Dr. Brown"]
SPECIALTIES = {
    "Dr. Smith": "General Practice",
    "Dr. Jones": "Cardiology",
    "Dr. Brown": "Orthopedics",
}

_WF_DEFAULT = {
    "stage": "idle",
    "patient": None, "dob": None, "phone": None, "insurance": None,
    "doctor": None, "urgency": None, "reason": None,
    "appt_date": None, "appt_time": None,
    "pending_slots": [], "comm_draft": None,
}


def init_session_state():
    """Initialize all session state keys. Safe to call multiple times."""
    st.session_state.setdefault("_theme_color", "Light")
    st.session_state.setdefault("_theme_font",  "Medium")
    st.session_state.setdefault("chat_open",    False)
    st.session_state.setdefault("chat",         [])
    st.session_state.setdefault("wf",           dict(_WF_DEFAULT))
    st.session_state.setdefault("feedback_submitted", False)
    st.session_state.setdefault("feedback_rating", 0)
    st.session_state.setdefault("demo_mode",    False)

    if "appointments" not in st.session_state:
        today = date.today()
        st.session_state.appointments = pd.DataFrame([
            {"Patient Name": "Alice Johnson",  "DOB": "1985-03-12", "Phone": "555-0101",
             "Doctor": "Dr. Smith", "Date": str(today+timedelta(days=1)),
             "Time": "09:00 AM", "Reason": "Annual checkup",       "Status": "Confirmed", "Urgency": "Low"},
            {"Patient Name": "Bob Martinez",   "DOB": "1972-07-24", "Phone": "555-0102",
             "Doctor": "Dr. Jones", "Date": str(today+timedelta(days=2)),
             "Time": "10:30 AM", "Reason": "Heart palpitations",   "Status": "Pending",   "Urgency": "High"},
            {"Patient Name": "Carol Lee",      "DOB": "1990-11-05", "Phone": "555-0103",
             "Doctor": "Dr. Brown", "Date": str(today+timedelta(days=3)),
             "Time": "02:00 PM", "Reason": "Knee pain follow-up",  "Status": "Confirmed", "Urgency": "Medium"},
            {"Patient Name": "David Kim",      "DOB": "1968-01-30", "Phone": "555-0104",
             "Doctor": "Dr. Smith", "Date": str(today+timedelta(days=5)),
             "Time": "11:00 AM", "Reason": "Blood pressure check", "Status": "Confirmed", "Urgency": "Medium"},
            {"Patient Name": "Emma Torres",    "DOB": "2001-06-18", "Phone": "555-0105",
             "Doctor": "Dr. Jones", "Date": str(today+timedelta(days=7)),
             "Time": "03:30 PM", "Reason": "EKG test",             "Status": "Pending",   "Urgency": "Medium"},
        ])

    if "messages" not in st.session_state:
        st.session_state.messages = pd.DataFrame([
            {"Patient Name": "Alice Johnson", "Doctor": "Dr. Smith",
             "Date": str(date.today()-timedelta(days=2)),
             "Message": "Reminder: Your appointment is tomorrow at 9:00 AM.",
             "Type": "Reminder", "Status": "Sent"},
            {"Patient Name": "Bob Martinez",  "Doctor": "Dr. Jones",
             "Date": str(date.today()-timedelta(days=1)),
             "Message": "Please bring your most recent EKG results.",
             "Type": "Pre-visit Instructions", "Status": "Sent"},
        ])


# ---------------------------------------------------------------------------
# AI PROVIDER ABSTRACTION  — priority: OpenAI → Gemini → Demo
# ---------------------------------------------------------------------------

_last_ai_error: str  = ""
_active_provider: str = "—"


def _demo_response(prompt: str) -> str:
    if "triage" in prompt.lower() or "urgency" in prompt.lower():
        # Extract ONLY the "Reason for visit:" line — ignore instructions that
        # mention emergency examples like "chest pain, difficulty breathing".
        reason_line = ""
        for line in prompt.splitlines():
            if "reason for visit:" in line.lower():
                reason_line = line.split(":", 1)[-1].strip().lower()
                break
        p = reason_line if reason_line else ""   # only check the actual reason

        if any(kw in p for kw in ["chest pain","difficulty breathing","stroke",
                                   "unconscious","severe bleeding","heart attack",
                                   "not breathing","seizure"]):
            level = "Emergency"
            timing = "Call emergency services now"
            note   = "Life-threatening signs — do not schedule a regular appointment."
        elif any(kw in p for kw in ["high fever","infection","fracture","acute",
                                    "severe pain","cannot walk","vomiting",
                                    "ear pain","ear ache","sore throat","fever"]):
            level = "High"
            timing = "Within 24–48 hours"
            note   = "Urgent but non-life-threatening — prioritize an early slot."
        elif any(kw in p for kw in ["checkup","check-up","check up","physical",
                                    "routine","annual","follow-up","wellness",
                                    "normal","general","regular","monitoring",
                                    "prescription refill","referral"]):
            level = "Low"
            timing = "Routine, within 2 weeks"
            note   = "Routine visit — a standard scheduled slot is appropriate."
        else:
            level = "Medium"
            timing = "Within 3–5 business days"
            note   = "Moderate concern — a standard appointment within the week is appropriate."
        return (
            f"**Urgency Level:** {level}\n"
            f"**Recommended Timing:** {timing}\n"
            f"**Scheduling Note:** {note}\n\n"
            "Not medical advice — for scheduling logistics only."
        )
    if "slot" in prompt.lower() or "schedul" in prompt.lower():
        # Return valid JSON so _parse_slots renders real bookable buttons
        today = date.today()
        slots = []
        offset, added = 1, 0
        times   = ["09:00 AM", "02:30 PM", "11:00 AM"]
        reasons = ["Earliest available morning slot.",
                   "Afternoon slot, low wait time expected.",
                   "Later option for patient flexibility."]
        while added < 3:
            cand = today + timedelta(days=offset); offset += 1
            if cand.weekday() >= 5: continue
            slots.append({"date": str(cand), "time": times[added],
                           "reason": reasons[added]})
            added += 1
        return json.dumps(slots)
    return (
        "Dear Patient,\n\nThis is a friendly reminder about your upcoming appointment. "
        "Please arrive 10 minutes early and bring any relevant medical records. "
        "Call us at [CLINIC_PHONE] if you need to reschedule.\n\n"
        "Not medical advice — for scheduling logistics only."
    )


def _call_openai(prompt: str) -> str:
    from openai import OpenAI
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200, temperature=0.3,
    )
    return resp.choices[0].message.content


def _call_gemini(prompt: str) -> str:
    from google import genai
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    client = genai.Client(api_key=key)
    return client.models.generate_content(model="gemini-flash-latest", contents=prompt).text


def call_ai(prompt: str) -> tuple[str, bool]:
    global _last_ai_error, _active_provider
    if st.session_state.get("demo_mode", False):
        _active_provider = "Demo mode (forced)"
        _last_ai_error   = ""
        return _demo_response(prompt), True
    errors = []
    if os.environ.get("OPENAI_API_KEY",""):
        try:
            r = _call_openai(prompt); _last_ai_error = ""
            _active_provider = "OpenAI · gpt-4o-mini"; return r, False
        except Exception as e:
            errors.append(f"OpenAI: {type(e).__name__}: {str(e)[:120]}")
    if os.environ.get("GEMINI_API_KEY",""):
        try:
            r = _call_gemini(prompt); _last_ai_error = ""
            _active_provider = "Gemini · flash"; return r, False
        except Exception as e:
            errors.append(f"Gemini: {type(e).__name__}: {str(e)[:120]}")
    _active_provider = "Demo mode"
    _last_ai_error = " | ".join(errors) if errors else "No API keys configured"
    return _demo_response(prompt), True


# ---------------------------------------------------------------------------
# SPECIALIST AGENTS
# ---------------------------------------------------------------------------

def triage_agent(reason: str, patient_name: str, doctor: str) -> tuple[str, bool]:
    prompt = f"""You are a medical scheduling triage assistant (scheduling logistics only).
Patient: {patient_name} | Doctor: {doctor} | Reason: {reason}
Respond with:
1. Urgency Level: Emergency / High / Medium / Low
   - Emergency ONLY for life-threatening signs (chest pain, stroke, severe bleeding, unconscious).
2. Recommended timing
3. One-sentence scheduling note
Format with bold labels. 3-4 lines max.
End with: "Not medical advice — for scheduling logistics only."
""".strip()
    return call_ai(prompt)


def scheduling_agent_structured(patient_name: str, urgency: str, doctor: str,
                                appointments_df: pd.DataFrame):
    booked = appointments_df[appointments_df["Doctor"]==doctor][["Date","Time","Status"]].to_string(index=False)
    prompt = f"""Healthcare scheduling assistant. Suggest 3 best appointment slots.
Patient: {patient_name} | Doctor: {doctor} | Urgency: {urgency} | Today: {date.today()}
Booked for {doctor}: {booked}
Return ONLY valid JSON list of 3 objects (no fences): [{{"date":"YYYY-MM-DD","time":"09:00 AM","reason":"..."}}]
Avoid weekends. Avoid already-booked slots.""".strip()
    raw, is_demo = call_ai(prompt)
    return _parse_slots(raw, doctor, urgency), is_demo


def _parse_slots(raw: str, doctor: str, urgency: str):
    cleaned = raw.replace("```json","").replace("```","").strip()
    m = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            slots = [{"date":str(i.get("date","")),
                      "time":str(i.get("time","")),
                      "reason":str(i.get("reason","Suggested slot."))}
                     for i in data[:3]
                     if isinstance(i,dict) and "date" in i and "time" in i]
            if slots: return slots
        except Exception:
            pass
    return _fallback_slots(urgency)


def _fallback_slots(urgency: str):
    times = ["09:00 AM","02:00 PM","11:00 AM"]
    out=[]; d=date.today(); added=0; offset=1
    while added<3:
        cand = d+timedelta(days=offset); offset+=1
        if cand.weekday()>=5: continue
        out.append({"date":str(cand),"time":times[added],
                    "reason":f"Open weekday slot for {urgency.lower()} urgency."})
        added+=1
    return out


def communication_agent(patient_name: str, doctor: str, appt_date: str,
                        appt_time: str, urgency: str) -> tuple[str, bool]:
    prompt = f"""Healthcare communication assistant drafting a patient reminder.
Patient: {patient_name} | Doctor: {doctor} | Appointment: {appt_date} at {appt_time} | Urgency: {urgency}
Draft a short, warm, professional reminder (3–4 sentences).
Mention: date/time, doctor's name, one preparation tip, contact placeholder [CLINIC_PHONE].
End with: "Not medical advice — for scheduling logistics only."
""".strip()
    return call_ai(prompt)


# ---------------------------------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------------------------------

def _auto_assign_doctor(appointments_df: pd.DataFrame) -> str:
    counts = {doc: 0 for doc in DOCTORS}
    confirmed = appointments_df[appointments_df["Status"]=="Confirmed"]
    for doc in DOCTORS:
        counts[doc] = len(confirmed[confirmed["Doctor"]==doc])
    return min(counts, key=counts.get)


def _demo_orchestrator(user_msg: str, chat_history: list,
                       wf: dict, auto_doc: str) -> dict:
    """
    Scripted demo conversation — no API calls, follows the realistic clinic flow:
      idle → asks name → run_triage → registering (DOB → reason) →
      triage_done → scheduling → slot_selected → comm_ready
    """
    msg_lower = user_msg.lower().strip()
    stage     = wf.get("stage", "idle")
    patient   = wf.get("patient") or ""

    def _r(text, action="none", name="", reason="", doctor=None, urgency=""):
        return {"text": text, "action": action,
                "patient_name": name or patient or "",
                "reason":  reason  or (wf.get("reason")  or ""),
                "doctor":  doctor  or (wf.get("doctor")  or auto_doc),
                "urgency": urgency or (wf.get("urgency") or ""),
                "is_demo": True}

    # ── IDLE ──────────────────────────────────────────────────────────────────
    if stage == "idle":
        words = msg_lower.split()
        # Spelling-tolerant: "new" + any word starting with "pat" (patient, paitient…)
        is_new_pt = ("new" in words and any(w.startswith("pat") for w in words))
        for kw in ["new patient", "new pt", "register", "add patient"]:
            if kw in msg_lower:
                is_new_pt = True; break
        if is_new_pt:
            # Extract anything after the "new patient" keywords as the name
            rest = ""
            for kw in ["new patient", "new pt", "register", "add patient",
                       "new paitient", "new patiant", "new pt"]:
                if kw in msg_lower:
                    rest = user_msg[msg_lower.index(kw)+len(kw):].strip(" ,.")
                    break
            if not rest and "new" in words:
                # grab everything after "new [pat...]"
                idx = next((i for i,w in enumerate(words) if w.startswith("pat")), -1)
                if idx >= 0:
                    rest = " ".join(user_msg.split()[idx+1:]).strip(" ,.")
            if rest:
                return _r(f"Got it! Registering **{rest}**. "
                          f"First, what is their **date of birth**?",
                          "run_triage", name=rest, reason="general visit")
            return _r("Alright, new patient coming in! "
                      "Could I get their **full name** please?")

        # Check if previous bot message asked for a name
        prev_asked_name = any(
            "name" in m["content"].lower()
            for m in chat_history[-3:]
            if m["role"] == "assistant"
        )
        if prev_asked_name and 1 <= len(user_msg.split()) <= 5:
            return _r(f"Got it! Registering **{user_msg}**. "
                      f"What is their **date of birth**?",
                      "run_triage", name=user_msg, reason="general visit")

        return _r("Hi! Say **\"new patient [name]\"** to register someone, "
                  "or ask about today's schedule.")

    # ── TRIAGE DONE ───────────────────────────────────────────────────────────
    if stage == "triage_done":
        for doc in DOCTORS:
            if doc.split(".")[1].strip().lower() in msg_lower or doc.lower() in msg_lower:
                return _r(f"Switched to **{doc}**. Finding the best slots now...",
                          "run_scheduling", doctor=doc)
        return _r(f"Finding the best available slots for **{patient}** "
                  f"with **{wf.get('doctor', auto_doc)}**...",
                  "run_scheduling")

    # ── SLOT SELECTED ─────────────────────────────────────────────────────────
    if stage == "slot_selected":
        return _r(f"Great! Drafting a reminder for **{patient}**...",
                  "run_communication")

    # Default
    return _r("I'm ready to help! What would you like to do next?")


def orchestrator_agent(user_msg: str, chat_history: list,
                       appointments_df: pd.DataFrame, wf: dict) -> dict:
    auto_doc = _auto_assign_doctor(appointments_df)

    # Use scripted demo orchestrator when demo mode is forced
    if st.session_state.get("demo_mode", False):
        return _demo_orchestrator(user_msg, chat_history, wf, auto_doc)

    history = "".join(
        f"{'Receptionist' if m['role']=='user' else 'AI'}: {m['content']}\n"
        for m in chat_history[-6:]
    )
    today_str = str(date.today())
    appt_sum = (f"{len(appointments_df)} total. "
                f"Today: {len(appointments_df[appointments_df['Date']==today_str])}.")
    prompt = f"""You are ScheduleMD AI, a smart clinic front-desk orchestrator.
Agents available: Triage, Scheduling, Communication.
Doctors: {', '.join(DOCTORS)} | Auto-assigned (lightest schedule): {auto_doc}
Appointments: {appt_sum} | Workflow stage: {wf['stage']} | Current patient: {wf['patient'] or 'none'}

Conversation:
{history}
Receptionist: "{user_msg}"

Respond ONLY with valid JSON (no fences):
{{"text":"response (1-3 sentences)","action":"run_triage|run_scheduling|run_communication|none|emergency",
"patient_name":"","reason":"","doctor":"","urgency":""}}

Rules:
- New patient + symptoms + stage=idle → run_triage, extract name/reason, doctor={auto_doc}
- Stage=triage_done + doctor known → run_scheduling
- Stage=slot_selected → run_communication
- Life-threatening symptoms → emergency
- Otherwise → none
- Be warm and professional. Offer to change the auto-assigned doctor.
""".strip()

    raw, is_demo = call_ai(prompt)
    if is_demo:
        return {"text": f"⚠️ AI unavailable — {_last_ai_error}",
                "action":"none","patient_name":"","reason":"",
                "doctor":auto_doc,"urgency":"","is_demo":True}
    try:
        cleaned = raw.replace("```json","").replace("```","").strip()
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            d = json.loads(m.group(0))
            return {"text":str(d.get("text","I'm here to help.")),
                    "action":str(d.get("action","none")),
                    "patient_name":str(d.get("patient_name","")),
                    "reason":str(d.get("reason","")),
                    "doctor":str(d.get("doctor",auto_doc)) or auto_doc,
                    "urgency":str(d.get("urgency","")),
                    "is_demo":False}
    except Exception:
        pass
    return {"text":raw[:400],"action":"none","patient_name":"","reason":"",
            "doctor":auto_doc,"urgency":"","is_demo":False}


# ---------------------------------------------------------------------------
# CHAT LOGIC
# ---------------------------------------------------------------------------

def _add_msg(role: str, content: str, agent: str = None, is_demo: bool = False):
    st.session_state.chat.append(
        {"role":role,"content":content,"agent":agent,"is_demo":is_demo})


def _urgency_from_text(text: str) -> str:
    # Check explicit "Urgency Level: X" line first (avoids "non-emergency" false match)
    for line in text.splitlines():
        if "urgency level:" in line.lower() or "urgency:" in line.lower():
            for lvl in ["Emergency", "High", "Medium", "Low"]:
                if lvl.lower() in line.lower():
                    return lvl
    # Fallback for free-text AI responses
    for lvl in ["Emergency", "High", "Medium", "Low"]:
        if f" {lvl.lower()} " in f" {text.lower()} ":
            return lvl
    return "Medium"


def _run_triage():
    wf = st.session_state.wf
    result, is_demo = triage_agent(wf["reason"] or "general visit", wf["patient"], wf["doctor"])
    urgency = _urgency_from_text(result)
    wf["urgency"] = urgency
    appts = st.session_state.appointments
    mask = appts["Patient Name"].str.lower() == wf["patient"].lower()
    if mask.any():
        st.session_state.appointments.loc[mask,"Urgency"] = urgency
    if urgency == "Emergency":
        _add_msg("assistant",
            "🚨 **POSSIBLE MEDICAL EMERGENCY** — Please direct this patient to call "
            "**911** or the nearest emergency room immediately. Do **not** schedule "
            "a regular appointment.",
            agent="🧠 Triage Agent", is_demo=is_demo)
        st.session_state.wf = dict(_WF_DEFAULT)
    else:
        _add_msg("assistant", result, agent="🧠 Triage Agent", is_demo=is_demo)
        _add_msg("assistant",
            f"**{wf['patient']}** is triaged as **{urgency}**. "
            f"Auto-assigned to **{wf['doctor']}** (lightest schedule). "
            f"Want a different doctor, or shall I find available slots?")
        wf["stage"] = "triage_done"


def _run_scheduling():
    wf = st.session_state.wf
    slots, is_demo = scheduling_agent_structured(
        wf["patient"], wf["urgency"] or "Medium",
        wf["doctor"], st.session_state.appointments)
    wf["pending_slots"] = slots
    _add_msg("assistant",
        f"Here are the best slots for **{wf['patient']}** with **{wf['doctor']}**:",
        agent="📅 Scheduling Agent", is_demo=is_demo)
    wf["stage"] = "scheduling"


def _run_communication():
    wf = st.session_state.wf
    draft, is_demo = communication_agent(
        wf["patient"], wf["doctor"],
        wf["appt_date"], wf["appt_time"], wf["urgency"] or "Medium")
    wf["comm_draft"] = draft
    _add_msg("assistant",
        f"Here's the reminder draft for **{wf['patient']}**. Edit if needed:",
        agent="💬 Communication Agent", is_demo=is_demo)
    wf["stage"] = "comm_ready"


def handle_user_input(user_msg: str):
    user_msg = user_msg.strip()
    if not user_msg: return
    _add_msg("user", user_msg)
    wf = st.session_state.wf
    appts = st.session_state.appointments

    # Registration state machine
    if wf["stage"] == "registering":
        demo = st.session_state.get("demo_mode", False)
        if wf["dob"] is None:
            wf["dob"] = user_msg
            if demo:
                _add_msg("assistant",
                    f"Got it. What's the **nature of {wf['patient']}'s visit**?")
            else:
                _add_msg("assistant",
                    f"Got it. What's **{wf['patient']}'s** phone number?")
        elif wf["phone"] is None:
            if demo:
                # In demo mode: this message is the reason — skip phone/insurance
                wf["phone"]     = "555-0000"
                wf["insurance"] = "N/A"
                wf["reason"]    = user_msg
                st.session_state.appointments = pd.concat([appts, pd.DataFrame([{
                    "Patient Name": wf["patient"], "DOB": wf["dob"],
                    "Phone": wf["phone"], "Doctor": wf["doctor"],
                    "Date": str(date.today()+timedelta(days=3)),
                    "Time": "09:00 AM", "Reason": wf["reason"],
                    "Status": "Pending", "Urgency": "Medium"
                }])], ignore_index=True)
                _add_msg("assistant",
                    f"✅ **{wf['patient']}** registered. Running triage...")
                wf["stage"] = "triage_running"
                _run_triage()
            else:
                wf["phone"] = user_msg
                _add_msg("assistant", "Insurance provider? (type **skip** if none)")
        elif wf["insurance"] is None:
            wf["insurance"] = user_msg if user_msg.lower() != "skip" else "N/A"
            st.session_state.appointments = pd.concat([appts, pd.DataFrame([{
                "Patient Name":wf["patient"],"DOB":wf["dob"],"Phone":wf["phone"],
                "Doctor":wf["doctor"],"Date":str(date.today()+timedelta(days=3)),
                "Time":"09:00 AM","Reason":wf["reason"],"Status":"Pending","Urgency":"Medium"
            }])], ignore_index=True)
            _add_msg("assistant", f"✅ **{wf['patient']}** registered. Running triage...")
            wf["stage"] = "triage_running"
            _run_triage()
        st.rerun(); return

    # Doctor override check
    if wf["stage"] == "triage_done":
        for doc in DOCTORS:
            if doc.lower() in user_msg.lower():
                wf["doctor"] = doc
                _add_msg("assistant", f"Switched to **{doc}**. Finding slots...")
                wf["stage"] = "scheduling"
                _run_scheduling()
                st.rerun(); return

    # Orchestrator
    with st.spinner("🤖 Thinking..."):
        result = orchestrator_agent(user_msg, st.session_state.chat, appts, wf)

    action  = result.get("action", "none")
    patient = (result.get("patient_name") or "").strip()
    reason  = (result.get("reason")       or "").strip()
    doctor  = (result.get("doctor")       or "").strip() or _auto_assign_doctor(appts)
    is_demo = result.get("is_demo",False)

    if result["text"]:
        _add_msg("assistant", result["text"], is_demo=is_demo)

    if action == "emergency":
        st.session_state.wf = dict(_WF_DEFAULT); st.rerun(); return

    if action == "run_triage" and patient:
        existing = appts[appts["Patient Name"].str.lower() == patient.lower()]
        if existing.empty:
            wf["stage"]="registering"; wf["patient"]=patient
            wf["reason"]=reason; wf["doctor"]=doctor
            _add_msg("assistant",
                f"I don't have **{patient}** on file. Let me register them.\n\n"
                f"What's their **date of birth**? (e.g. 1990-03-15)")
        else:
            wf["stage"]="triage_running"; wf["patient"]=patient
            wf["reason"]=reason; wf["doctor"]=doctor
            _run_triage()
        st.rerun(); return

    if action == "run_scheduling" and wf["stage"] == "triage_done":
        wf["stage"] = "scheduling"; _run_scheduling(); st.rerun(); return

    if action == "run_communication" and wf["stage"] == "slot_selected":
        wf["stage"] = "comm_running"; _run_communication(); st.rerun(); return

    st.rerun()


def book_slot(slot: dict):
    wf = st.session_state.wf
    appts = st.session_state.appointments
    mask = appts["Patient Name"].str.lower() == wf["patient"].lower()
    if mask.any():
        st.session_state.appointments.loc[mask,"Date"]   = slot["date"]
        st.session_state.appointments.loc[mask,"Time"]   = slot["time"]
        st.session_state.appointments.loc[mask,"Doctor"] = wf["doctor"]
        st.session_state.appointments.loc[mask,"Status"] = "Confirmed"
        st.session_state.appointments.loc[mask,"Urgency"]= wf["urgency"] or "Medium"
    else:
        st.session_state.appointments = pd.concat([appts, pd.DataFrame([{
            "Patient Name":wf["patient"],"DOB":wf.get("dob",""),
            "Phone":wf.get("phone",""),"Doctor":wf["doctor"],
            "Date":slot["date"],"Time":slot["time"],
            "Reason":wf["reason"] or "","Status":"Confirmed",
            "Urgency":wf["urgency"] or "Medium",
        }])], ignore_index=True)
    wf["appt_date"]=slot["date"]; wf["appt_time"]=slot["time"]
    wf["pending_slots"]=[]; wf["stage"]="slot_selected"
    _add_msg("assistant",
        f"✅ **Booked!** {wf['patient']} → {wf['doctor']} on "
        f"**{slot['date']} at {slot['time']}**. Drafting reminder...")
    _run_communication(); st.rerun()


def send_reminder(body: str):
    wf = st.session_state.wf
    st.session_state.messages = pd.concat([
        st.session_state.messages,
        pd.DataFrame([{"Patient Name":wf["patient"],"Doctor":wf["doctor"],
                       "Date":str(date.today()),"Message":body,
                       "Type":"Reminder","Status":"Sent"}])
    ], ignore_index=True)
    _add_msg("assistant",
        f"📲 Reminder sent to **{wf['patient']}**. Ready for the next patient!")
    st.session_state.wf = dict(_WF_DEFAULT); st.rerun()
