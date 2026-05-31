import streamlit as st
import streamlit.components.v1 as components
from datetime import date
from utils import (
    init_session_state, apply_theme, _t, logo_html,
    DOCTORS, SPECIALTIES, _WF_DEFAULT, _active_provider,
    _FONT_OPTS, _COLOR_OPTS,
    handle_user_input, book_slot, send_reminder,
    scheduling_agent_structured, render_footer, render_header,
)

st.set_page_config(page_title="ScheduleMD", page_icon="🩺", layout="wide")
init_session_state()

# Page routing state
st.session_state.setdefault("page", "home")

apply_theme()

# render_header imported from utils

# ---------------------------------------------------------------------------
# PAGE: HOME
# ---------------------------------------------------------------------------

def page_home():
    t = _t(); p = t["primary"]

    hero_l, hero_r = st.columns([3, 2], gap="large")
    with hero_l:
        st.markdown(f"""
<div style='padding:3rem 2rem 1rem 2.5rem;position:relative'>
  <div style='position:absolute;top:-20px;left:-10px;width:160px;height:160px;
    background:radial-gradient(circle,{p}18 1.5px,transparent 1.5px);
    background-size:18px 18px;border-radius:50%;pointer-events:none'></div>
  <div style='position:relative'>
    <div style='font-size:clamp(3rem,7vw,5.2rem);font-weight:900;
      line-height:1;letter-spacing:-0.04em;color:{p};
      font-family:Georgia,serif;margin-bottom:.3rem'>ScheduleMD</div>
    <div style='font-size:1.05em;font-weight:600;letter-spacing:.18em;
      text-transform:uppercase;color:{t["muted"]};margin-bottom:1.1rem'>
      Welcome, Scheduler</div>
    <div style='font-size:1em;color:{t["muted"]};max-width:420px;
      line-height:1.75;margin-bottom:2rem'>
      AI-powered front-desk assistant — handles triage, scheduling,
      and patient reminders so your team can focus on care.
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
        if st.button("LET'S START ORGANIZING  →", key="cta"):
            st.session_state.page = "calendar"; st.rerun()

    with hero_r:
        st.markdown("<div style='padding:2rem 1rem'>", unsafe_allow_html=True)
        for (icon, label, bg, color), pos in zip(
            [("👨‍⚕️","Smart Triage",   "#e8f5ec", p),
             ("📅","Easy Scheduling", "#f0f8ff", "#0072b2"),
             ("🤝","Team Ready",      "#fff8e8", "#c49a00")],
            ["margin-left:60px;margin-bottom:-28px",
             "margin-left:0px;margin-bottom:-28px",
             "margin-left:80px"]
        ):
            st.markdown(f"""
<div style='display:inline-block;{pos}'>
  <div style='width:155px;height:155px;border-radius:50%;
    background:linear-gradient(135deg,{bg},{color}22);
    border:3px solid {color}44;
    display:flex;flex-direction:column;align-items:center;
    justify-content:center;box-shadow:0 8px 24px {color}22'>
    <div style='font-size:2.8em'>{icon}</div>
    <div style='font-size:.7em;font-weight:600;color:{color};
      margin-top:5px;text-align:center;padding:0 10px'>{label}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Quick-link cards
    _muted = t['muted']
    st.markdown(f"<div style='padding:.5rem 2.5rem 0;font-size:.78em;font-weight:700;"
                f"letter-spacing:.15em;text-transform:uppercase;color:{_muted}'"
                f">Where would you like to go?</div>", unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns(3, gap="medium")
    _cs = (f"border:1.5px solid {t['border']};border-radius:16px;padding:28px 24px;"
           f"background:{t['card']};box-shadow:0 4px 16px -6px rgba(0,0,0,.08);"
           f"text-align:center")
    for col, icon, title, desc, page_key, highlight in [
        (cc1, "📖", "About Us",    "Why we built this and the problem we're solving.", "about",    False),
        (cc2, "💬", "Feedback",    "Help us improve with your thoughts and rating.",   "feedback", False),
        (cc3, "📅", "Calendar",    "View appointments and chat with the AI assistant.","calendar", True),
    ]:
        extra = f";border-color:{p};background:linear-gradient(135deg,{t['bg2']},{t['card']})" if highlight else ""
        title_color = p if highlight else t["text"]
        with col:
            st.markdown(f"""
<div style='{_cs}{extra}'>
  <div style='font-size:2.3em;margin-bottom:10px'>{icon}</div>
  <div style='font-weight:700;font-size:1.05em;color:{title_color};margin-bottom:6px'>{title}</div>
  <div style='font-size:.85em;color:{t["muted"]};line-height:1.5'>{desc}</div>
</div>""", unsafe_allow_html=True)
            if st.button(f"Open {title} →", key=f"card_{page_key}", use_container_width=True):
                st.session_state.page = page_key; st.rerun()

    st.markdown(f"<div style='padding:1.5rem 2.5rem .5rem;display:flex;gap:8px;align-items:center'>"
                f"<div style='width:8px;height:8px;border-radius:50%;background:{p}'></div>"
                f"<div style='width:8px;height:8px;border-radius:50%;background:{p}66'></div>"
                f"<div style='width:8px;height:8px;border-radius:50%;background:{p}33'></div>"
                f"<div style='font-size:.75em;color:{t['muted']};margin-left:8px'>"
                f"HackJPS 2026 · Healthcare Track · Best Use of AI/ML</div></div>",
                unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: CALENDAR
# ---------------------------------------------------------------------------

def _render_calendar_table():
    """Shared calendar table used in both layouts."""
    t = _t(); p = t["primary"]
    today_str = str(date.today())
    appts = st.session_state.appointments
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(appts))
    m2.metric("Today", len(appts[appts["Date"] == today_str]))
    m3.metric("Confirmed", len(appts[appts["Status"] == "Confirmed"]))
    m4.metric("Urgent", len(appts[appts["Urgency"].isin(["High","Emergency"])]))

    fc1, fc2, fc3 = st.columns([1,1.5,1.5])
    with fc1:
        f_doc = st.selectbox("Doctor", ["All"]+DOCTORS, key="cal_doc",
                             label_visibility="collapsed")
    with fc2:
        f_urg = st.multiselect("Urgency", ["Emergency","High","Medium","Low"],
                               default=[], key="cal_urg", placeholder="All urgencies",
                               label_visibility="collapsed")
    with fc3:
        f_sta = st.multiselect("Status", ["Confirmed","Pending","Cancelled"],
                               default=[], key="cal_sta", placeholder="All statuses",
                               label_visibility="collapsed")
    df = appts.copy()
    if f_doc != "All": df = df[df["Doctor"]==f_doc]
    if f_urg:          df = df[df["Urgency"].isin(f_urg)]
    if f_sta:          df = df[df["Status"].isin(f_sta)]
    df = df.sort_values(["Date","Time"]).reset_index(drop=True)
    urg_c = {
        "Emergency": (t["urg_hi"][0], t["urg_hi"][5]),
        "High":      (t["urg_hi"][3], t["urg_hi"][5]),
        "Medium":    (t["urg_med"][3],t["urg_med"][5]),
        "Low":       (t["urg_lo"][3], t["urg_lo"][5]),
    }
    def _sr(row):
        bg,fg = urg_c.get(row.get("Urgency",""),("",""))
        return [f"background-color:{bg};color:{fg};font-weight:500"]*len(row) if bg else [""]*len(row)
    cols = ["Date","Time","Patient Name","Doctor","Urgency","Status","Reason"]
    df_show = df[[c for c in cols if c in df.columns]]
    h = 380 if st.session_state.chat_open else 460
    if not df_show.empty:
        st.dataframe(df_show.style.apply(_sr,axis=1),
                     use_container_width=True, hide_index=True, height=h)
    else:
        st.info("No appointments match the current filters.")


def _render_rufus_panel():
    """Rufus-style AI chat side panel — all interactions in one column."""
    t = _t(); p = t["primary"]; wf = st.session_state.wf

    # ── Panel header ──────────────────────────────────────────────────────
    st.markdown(f"""
<div style='background:linear-gradient(135deg,{p},{t["primary2"]});
  border-radius:14px 14px 0 0;padding:14px 18px;
  display:flex;align-items:center;justify-content:space-between;
  box-shadow:0 2px 8px {p}44'>
  <div style='display:flex;align-items:center;gap:10px'>
    <div style='width:36px;height:36px;border-radius:50%;
      background:rgba(255,255,255,.25);
      display:flex;align-items:center;justify-content:center;
      font-size:18px'>✚</div>
    <div style='color:#fff'>
      <div style='font-weight:800;font-size:1em;letter-spacing:-.01em'>AI Assistant</div>
      <div style='font-size:.72em;opacity:.8'>Triage · Schedule · Remind</div>
    </div>
  </div>
  <span style='background:rgba(255,255,255,.2);color:#fff;
    border-radius:20px;padding:3px 10px;font-size:.7em;font-weight:600'>
    {_active_provider}
  </span>
</div>
""", unsafe_allow_html=True)

    # ── Scrollable messages ────────────────────────────────────────────────
    with st.container(height=360, border=True):
        chat = st.session_state.chat
        if not chat:
            st.markdown(f"""
<div style='text-align:center;padding:30px 8px;color:{t["muted"]};font-size:.9em'>
  👋 Hi! Tell me about a new patient or ask about today's schedule.<br><br>
  <em style='font-size:.88em'>"New patient Sarah, bad sore throat and fever"</em>
</div>""", unsafe_allow_html=True)
        else:
            for msg in chat:
                role    = msg["role"]
                content = msg["content"]
                agent   = msg.get("agent")
                is_demo = msg.get("is_demo", False)

                if role == "user":
                    c1, c2 = st.columns([1, 4])
                    with c2:
                        st.markdown(
                            f"<div style='background:{t['bubble_user_bg']};"
                            f"color:{t['bubble_user_text']};border-radius:16px 16px 4px 16px;"
                            f"padding:9px 13px;font-size:.88em;line-height:1.45;'>"
                            f"{content}</div>",
                            unsafe_allow_html=True)
                elif agent:
                    ac = {"🧠 Triage Agent":(t["urg_hi"][1],t["urg_hi"][3]),
                          "📅 Scheduling Agent":(p,t["bg2"]),
                          "💬 Communication Agent":("#c79a3c","#fffbf0")}
                    bc, cbg = ac.get(agent,(p,t["bg2"]))
                    db = " *(demo)*" if is_demo else ""
                    _tc = t['text']
                    st.markdown(
                        f"<div style='border-left:4px solid {bc};background:{cbg};"
                        f"border-radius:0 10px 10px 0;padding:9px 13px;margin:2px 0;"
                        f"font-size:.85em;line-height:1.5;color:{_tc}'>"
                        f"<b style='color:{bc}'>{agent}{db}</b><br>{content}</div>",
                        unsafe_allow_html=True)
                else:
                    dm = " *(demo)*" if is_demo else ""
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(
                            f"<div style='background:{t['bubble_bot_bg']};"
                            f"color:{t['bubble_bot_text']};"
                            f"border:1px solid {t['bubble_border']};"
                            f"border-radius:16px 16px 16px 4px;"
                            f"padding:9px 13px;font-size:.88em;line-height:1.45'>"
                            f"{content}{dm}</div>",
                            unsafe_allow_html=True)

    # ── Slot booking ───────────────────────────────────────────────────────
    if wf["stage"] == "scheduling" and wf.get("pending_slots"):
        sc = st.columns(min(len(wf["pending_slots"][:3]), 3))
        for i, sl in enumerate(wf["pending_slots"][:3]):
            with sc[i]:
                st.markdown(f"<div style='text-align:center;font-size:.8em;"
                            f"font-weight:600;color:{p};padding:4px 0'>"
                            f"📅 {sl['date']}<br>{sl['time']}</div>",
                            unsafe_allow_html=True)
                if st.button("Book", key=f"sl_{i}", use_container_width=True):
                    book_slot(sl)
        if st.button("🔄 More options", key="more_sl", use_container_width=True):
            more, _ = scheduling_agent_structured(
                wf["patient"], wf["urgency"] or "Medium",
                wf["doctor"], st.session_state.appointments)
            seen = {(s["date"],s["time"]) for s in wf["pending_slots"]}
            for s in more:
                if (s["date"],s["time"]) not in seen:
                    wf["pending_slots"].append(s); seen.add((s["date"],s["time"]))
            st.rerun()

    # ── Reminder send ──────────────────────────────────────────────────────
    if wf["stage"] == "comm_ready" and wf.get("comm_draft"):
        with st.form("send_form", clear_on_submit=True):
            edited = st.text_area("Edit reminder:", value=wf["comm_draft"], height=90,
                                  label_visibility="collapsed")
            if st.form_submit_button("📲 Send reminder (simulated)", use_container_width=True):
                send_reminder(edited)

    # ── Input bar ──────────────────────────────────────────────────────────
    # Voice input component — uses Web Speech API (Chrome / Edge only)
    _p = t["primary"]; _bdr = t["border"]; _bg2 = t["bg2"]
    components.html(f"""
<style>
  body {{ margin:0; padding:0; background:transparent; overflow:hidden; }}
  #micBtn {{
    width:38px; height:38px; border-radius:8px;
    background:transparent; border:1.5px solid {_bdr};
    font-size:17px; cursor:pointer; display:flex;
    align-items:center; justify-content:center;
    transition:all .15s; margin:0; padding:0;
  }}
  #micBtn:hover {{ background:{_bg2}; border-color:{_p}; }}
  #micBtn.rec {{
    background:{_p}; border-color:{_p}; color:#fff;
    animation: pulse .8s infinite;
  }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.55}} }}
</style>
<button id="micBtn" onclick="toggleMic()" title="Voice input — Chrome/Edge only">🎤</button>
<script>
var _recog = null, _recording = false;
function toggleMic() {{
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {{ alert('Voice input requires Chrome or Edge.'); return; }}
  if (_recording) {{ if (_recog) _recog.stop(); return; }}
  _recog = new SR();
  _recog.lang = 'en-US';
  _recog.interimResults = false;
  _recog.continuous = false;
  _recog.onstart = function() {{
    _recording = true;
    var b = document.getElementById('micBtn');
    b.classList.add('rec'); b.textContent = '🔴';
  }};
  _recog.onresult = function(e) {{
    var txt = e.results[0][0].transcript;
    var doc = window.parent.document;
    var inputs = doc.querySelectorAll('input[type="text"]');
    for (var i=0; i<inputs.length; i++) {{
      if (inputs[i].placeholder === 'Ask AI Assistant...') {{
        var setter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,'value').set;
        setter.call(inputs[i], txt);
        inputs[i].dispatchEvent(new Event('input',{{bubbles:true}}));
        break;
      }}
    }}
  }};
  _recog.onend = function() {{
    _recording = false;
    var b = document.getElementById('micBtn');
    b.classList.remove('rec'); b.textContent = '🎤';
  }};
  _recog.onerror = function() {{
    _recording = false;
    var b = document.getElementById('micBtn');
    b.classList.remove('rec'); b.textContent = '🎤';
  }};
  _recog.start();
}}
</script>
""", height=46)

    with st.form("chat_form", clear_on_submit=True):
        inp_c, send_c = st.columns([5, 1])
        with inp_c:
            msg_in = st.text_input("msg", placeholder="Ask AI Assistant...",
                                   label_visibility="collapsed")
        with send_c:
            sent = st.form_submit_button("Send", use_container_width=True)

    rw1, rw2 = st.columns([3, 1])
    with rw2:
        if st.button("🗑️ New Chat", key="new_chat_btn", use_container_width=True):
            st.session_state.chat = []
            st.session_state.wf = dict(_WF_DEFAULT)
            st.rerun()

    if sent and msg_in.strip():
        handle_user_input(msg_in)


def page_calendar():
    t = _t(); p = t["primary"]
    chat_open = st.session_state.chat_open

    # Page header row: title + chat toggle button
    h1, h2 = st.columns([5, 1])
    with h1:
        _mut = t['muted']
        _tc = t['text']; _mut = t['muted']
        st.markdown(
            f"<div style='padding:14px 28px 2px'>"
            f"<div style='font-size:1.75em;font-weight:800;color:{_tc};"
            f"letter-spacing:-.02em;line-height:1.1'>📅 Appointment Calendar</div>"
            f"<div style='font-size:.82em;color:{_mut};margin-top:3px'>"
            f"View, filter and manage all clinic appointments</div>"
            f"</div>",
            unsafe_allow_html=True)
    with h2:
        st.markdown("<div style='padding-top:16px'>", unsafe_allow_html=True)
        btn_lbl = "✕ Close Chat" if chat_open else "💬 AI Chat"
        if st.button(btn_lbl, key="chat_toggle", use_container_width=True):
            st.session_state.chat_open = not chat_open
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Main layout: calendar always left, chat panel slides in on right
    if chat_open:
        col_cal, col_chat = st.columns([3, 2], gap="small")
        with col_cal:
            _render_calendar_table()
        with col_chat:
            _render_rufus_panel()
    else:
        _render_calendar_table()

# ---------------------------------------------------------------------------
# PAGE: ABOUT US
# ---------------------------------------------------------------------------

def page_about():
    t = _t(); p = t["primary"]
    st.markdown(f"""
<div style='padding:3rem 4rem 2rem;max-width:900px;margin:0 auto'>
  <div style='font-size:.78em;font-weight:700;letter-spacing:.2em;
    text-transform:uppercase;color:{p};margin-bottom:12px'>Our Story</div>
  <h1 style='font-size:clamp(2rem,4vw,3rem);font-weight:900;
    letter-spacing:-.03em;color:{t["text"]};line-height:1.1;margin-bottom:1rem'>
    A real person.<br>A real headache.</h1>
  <p style='font-size:1.05em;color:{t["muted"]};max-width:600px;line-height:1.75'>
    We're not diagnosing anyone — we're handing the front desk a smart assistant
    for the scheduling grind.</p>
</div>
<div style='padding:0 4rem 2.5rem;max-width:900px;margin:0 auto'>
  <div style='border-left:5px solid {p};padding:20px 28px;
    background:{t["bg2"]};border-radius:0 14px 14px 0;
    box-shadow:0 4px 16px -6px {p}33'>
    <div style='font-size:1.22em;font-style:italic;font-weight:600;
      color:{t["text"]};line-height:1.5;margin-bottom:12px'>
      "There are too many phone calls to make, and patients get annoyed
      when their appointments keep changing."</div>
    <div style='font-size:.85em;color:{t["muted"]};font-weight:600'>
      — Aryan's sister, front-desk receptionist · Our north star</div>
  </div>
</div>
""", unsafe_allow_html=True)

    p1, p2, p3 = st.columns(3, gap="medium")
    for col, icon, title, body in [
        (p1, "📞", "Too Many Calls",      "Hours lost dialing patients to find a time that works — every single day."),
        (p2, "🔀", "Constant Reshuffles", "Cancellations force manual re-juggling of the entire schedule from scratch."),
        (p3, "😤", "Frustrated Patients", "Changing appointments and missed reminders leave patients and staff stressed."),
    ]:
        with col:
            st.markdown(f"""
<div style='border:1.5px solid {t["border"]};border-radius:16px;
  padding:26px 22px;background:{t["card"]};
  box-shadow:0 3px 12px -6px rgba(0,0,0,.08)'>
  <div style='font-size:2.1em;margin-bottom:12px'>{icon}</div>
  <div style='font-weight:700;font-size:1em;color:{t["text"]};margin-bottom:7px'>{title}</div>
  <div style='font-size:.87em;color:{t["muted"]};line-height:1.6'>{body}</div>
</div>""", unsafe_allow_html=True)

    st.markdown(f"""
<div style='padding:2.5rem 4rem 1rem;max-width:900px;margin:0 auto'>
  <div style='font-size:.78em;font-weight:700;letter-spacing:.2em;
    text-transform:uppercase;color:{p};margin-bottom:18px'>Our solution</div>
  <h2 style='font-size:1.7em;font-weight:800;letter-spacing:-.02em;
    color:{t["text"]};margin-bottom:.7rem'>One orchestrator. Three specialist agents.</h2>
</div>
""", unsafe_allow_html=True)

    ag1, ag2, ag3 = st.columns(3, gap="medium")
    for col, icon, label, color, body, tag in [
        (ag1,"🧠","01 · Triage",        p,         "Reads symptoms → urgency + timing for the front desk.","analyze → priority"),
        (ag2,"📅","02 · Scheduling",    "#0072b2",  "Finds open slots that match urgency; books & searches.","calendar brain"),
        (ag3,"💬","03 · Communication", "#c79a3c",  "Drafts confirmation & reminder, tone-matched to urgency.","draft → send"),
    ]:
        with col:
            st.markdown(f"""
<div style='border:1.5px solid {color}44;border-radius:16px;
  padding:26px 22px;background:{t["card"]};
  box-shadow:0 3px 12px -6px {color}33'>
  <div style='font-size:1.9em;margin-bottom:9px'>{icon}</div>
  <div style='font-size:.7em;font-weight:700;letter-spacing:.15em;
    text-transform:uppercase;color:{t["muted"]};margin-bottom:5px'>{label}</div>
  <div style='font-size:.88em;color:{t["text"]};line-height:1.6;margin-bottom:12px'>{body}</div>
  <span style='background:{color}18;color:{color};border-radius:100px;
    padding:3px 11px;font-size:.74em;font-weight:700'>{tag}</span>
</div>""", unsafe_allow_html=True)

    st.markdown(f"""
<div style='padding:2rem 4rem 3rem;max-width:900px;margin:0 auto;
  font-size:.78em;color:{t["muted"]}'>
  HackJPS 2026 · Healthcare Track · Best Use of AI/ML
</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# PAGE: FEEDBACK
# ---------------------------------------------------------------------------

def page_feedback():
    t = _t(); p = t["primary"]
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(f"""
<div style='padding:3rem 0 1.5rem;text-align:center'>
  <div style='font-size:.78em;font-weight:700;letter-spacing:.2em;
    text-transform:uppercase;color:{p};margin-bottom:10px'>Share your thoughts</div>
  <div style='font-size:2.2em;font-weight:900;letter-spacing:-.03em;
    color:{t["text"]};margin-bottom:.5rem'>Feedback Form</div>
  <div style='font-size:1em;font-style:italic;color:{t["muted"]};
    opacity:.7;font-weight:600;max-width:440px;margin:0 auto;line-height:1.6'>
    "Great products are built on honest feedback. Your thoughts
    shape the future of ScheduleMD."</div>
</div>
""", unsafe_allow_html=True)

        if st.session_state.get("feedback_submitted"):
            st.success("🎉 Thank you! Your feedback helps us make ScheduleMD better.")
            if st.button("Submit another response"):
                st.session_state.feedback_submitted = False
                st.session_state.feedback_rating = 0
                st.rerun()
        else:
            _tt = t['text']
            st.markdown(f"<div style='font-weight:700;font-size:.9em;color:{_tt};margin-bottom:8px'>How would you rate ScheduleMD?</div>", unsafe_allow_html=True)
            sc = st.columns(5)
            cur = st.session_state.get("feedback_rating", 0)
            labels = ["Terrible","Poor","Okay","Good","Excellent"]
            for i, sc_col in enumerate(sc):
                with sc_col:
                    n = i+1
                    if st.button("⭐" if n<=cur else "☆", key=f"s{n}", help=labels[i], use_container_width=True):
                        st.session_state.feedback_rating = n; st.rerun()

            if cur > 0:
                st.markdown(f"<div style='text-align:center;font-size:.85em;font-weight:600;color:{p};margin-bottom:8px'>{labels[cur-1]} — {cur}/5 ⭐</div>", unsafe_allow_html=True)

            with st.form("fb_form", clear_on_submit=True):
                thoughts = st.text_area("Your thoughts", placeholder="Put your thoughts here...",
                                        height=140, label_visibility="collapsed")
                sub = st.form_submit_button("Submit Feedback →", use_container_width=True)
            if sub:
                if cur == 0:
                    st.warning("Please select a star rating.")
                else:
                    if "feedback_entries" not in st.session_state:
                        st.session_state.feedback_entries = []
                    st.session_state.feedback_entries.append({"rating":cur,"thoughts":thoughts})
                    st.session_state.feedback_submitted = True
                    st.rerun()

        entries = st.session_state.get("feedback_entries",[])
        if entries:
            avg = sum(e["rating"] for e in entries)/len(entries)
            _bdr = t['border']; _mut = t['muted']
            _s = "s" if len(entries) != 1 else ""
            st.markdown(
                f"<div style='margin-top:1.5rem;padding-top:1rem;"
                f"border-top:1px solid {_bdr};display:flex;gap:16px;align-items:center'>"
                f"<div style='text-align:center'>"
                f"<div style='font-size:2em;font-weight:900;color:{p}'>{avg:.1f}</div>"
                f"<div style='font-size:.74em;color:{_mut};font-weight:600'>AVG RATING</div>"
                f"</div><div style='font-size:.85em;color:{_mut}'>"
                f"{len(entries)} response{_s} received</div></div>",
                unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------------

render_header(current_page=st.session_state.page)

page = st.session_state.page
if   page == "home":     page_home()
elif page == "calendar": page_calendar()
elif page == "about":    page_about()
elif page == "feedback": page_feedback()
else:                    page_home()

render_footer()
