import os
import json
import re
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import random

st.set_page_config(page_title="Healthcare Scheduler", layout="wide")

DISCLAIMER = (
    ":warning: **Not medical advice — for scheduling logistics only.** "
    "Always consult a qualified healthcare professional for medical decisions."
)

# ---------------------------------------------------------------------------
# AI PROVIDER ABSTRACTION
# ---------------------------------------------------------------------------

AI_PROVIDER = "gemini"

def _demo_response(prompt: str) -> str:
    if "triage" in prompt.lower() or "urgency" in prompt.lower():
        return (
            "**[DEMO MODE]**\n\n"
            "**Urgency Level:** Medium\n"
            "**Recommended Timing:** Within 3–5 business days\n\n"
            "Based on the described symptoms, this appears to be a non-emergency "
            "situation that warrants timely but not immediate attention. "
            "A standard appointment slot should be sufficient."
        )
    if "slot" in prompt.lower() or "schedul" in prompt.lower():
        today = date.today()
        return (
            "**[DEMO MODE]**\n\n"
            f"**Slot 1:** {today + timedelta(days=2)} at 9:00 AM — earliest available morning slot, "
            "good for medium-urgency cases.\n\n"
            f"**Slot 2:** {today + timedelta(days=3)} at 2:30 PM — afternoon availability, "
            "low wait time expected.\n\n"
            f"**Slot 3:** {today + timedelta(days=5)} at 11:00 AM — later option if patient needs flexibility."
        )
    return (
        "**[DEMO MODE]**\n\n"
        "Dear Patient,\n\n"
        "This is a friendly reminder about your upcoming appointment. "
        "Please arrive 10 minutes early and bring any relevant medical records. "
        "If you need to reschedule, contact us at least 24 hours in advance.\n\n"
        "Best regards,\nThe Scheduling Team"
    )


def _call_gemini(prompt: str) -> str:
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
    )
    return response.text


_last_ai_error: str = ""

def call_ai(prompt: str) -> tuple[str, bool]:
    global _last_ai_error
    try:
        if AI_PROVIDER == "gemini":
            result = _call_gemini(prompt)
            _last_ai_error = ""
            return result, False
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {AI_PROVIDER}")
    except Exception as e:
        _last_ai_error = f"{type(e).__name__}: {str(e)[:300]}"
        return _demo_response(prompt), True


# ---------------------------------------------------------------------------
# AGENT PROMPTS
# ---------------------------------------------------------------------------

def triage_agent(reason: str, patient_name: str, doctor: str) -> tuple[str, bool]:
    prompt = f"""
You are a medical scheduling triage assistant. Your job is scheduling logistics only — not clinical diagnosis.

Patient: {patient_name}
Assigned Doctor: {doctor}
Reason for visit: {reason}

Based solely on the stated reason, respond with:
1. Urgency Level: Low / Medium / High
2. Recommended appointment timing (e.g. "within 24 hours", "within 3–5 days", "routine, within 2 weeks")
3. A one-sentence scheduling note for the front desk

Format your response with clear bold labels. Keep it concise (3–4 lines max).
End with: "Not medical advice — for scheduling logistics only."
""".strip()
    return call_ai(prompt)


def scheduling_agent(patient_name: str, urgency: str, doctor: str, appointments_df: pd.DataFrame) -> tuple[str, bool]:
    booked = appointments_df[appointments_df["Doctor"] == doctor][["Date", "Time", "Status"]].to_string(index=False)
    prompt = f"""
You are a healthcare scheduling assistant. Suggest the 3 best available appointment slots.

New patient: {patient_name}
Doctor: {doctor}
Urgency: {urgency}
Already booked slots for {doctor}:
{booked}

Suggest 3 concrete date/time slots (avoid weekends) that are not already booked. For each slot give:
- The date and time
- A brief reason why this slot suits the urgency level

Format as a numbered list with bold slot labels. Today is {date.today()}.
End with: "Not medical advice — for scheduling logistics only."
""".strip()
    return call_ai(prompt)


def scheduling_agent_structured(patient_name: str, urgency: str, doctor: str, appointments_df: pd.DataFrame):
    """
    Like scheduling_agent, but asks the AI for JSON so we can render clickable,
    bookable slot buttons. Returns (list_of_slots, is_demo).
    Each slot is a dict: {"date","time","reason"}.
    """
    booked = appointments_df[appointments_df["Doctor"] == doctor][["Date", "Time", "Status"]].to_string(index=False)
    prompt = f"""
You are a healthcare scheduling assistant. Suggest the 3 best available appointment slots.

New patient: {patient_name}
Doctor: {doctor}
Urgency: {urgency}
Today is {date.today()}.
Already booked slots for {doctor}:
{booked}

Return ONLY valid JSON — a list of exactly 3 objects, no text before or after, no markdown fences.
Each object must have these keys:
- "date": a weekday date in YYYY-MM-DD format (no weekends), not already booked
- "time": a time like "09:00 AM"
- "reason": one short sentence on why this slot suits the urgency level

Example format:
[{{"date":"2026-06-01","time":"09:00 AM","reason":"Earliest slot, good for high urgency."}}]
""".strip()
    raw, is_demo = call_ai(prompt)
    slots = _parse_slots(raw, doctor, urgency)
    return slots, is_demo


def _parse_slots(raw: str, doctor: str, urgency: str):
    """Pull a list of slot dicts out of the AI's reply. Falls back to safe defaults."""
    # Try to find a JSON array in the response (strip code fences if present).
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            slots = []
            for item in data[:3]:
                if isinstance(item, dict) and "date" in item and "time" in item:
                    slots.append({
                        "date": str(item.get("date", "")),
                        "time": str(item.get("time", "")),
                        "reason": str(item.get("reason", "Suggested slot.")),
                    })
            if slots:
                return slots
        except Exception:
            pass
    # Fallback: generate three sensible weekday slots so the UI always works.
    return _fallback_slots(urgency)


def _fallback_slots(urgency: str):
    """Deterministic safe slots if the AI reply can't be parsed."""
    times = ["09:00 AM", "02:00 PM", "11:00 AM"]
    out = []
    d = date.today()
    added = 0
    offset = 1
    while added < 3:
        cand = d + timedelta(days=offset)
        offset += 1
        if cand.weekday() >= 5:  # skip Sat/Sun
            continue
        out.append({
            "date": str(cand),
            "time": times[added],
            "reason": f"Open weekday slot suitable for {urgency.lower()} urgency.",
        })
        added += 1
    return out


def communication_agent(patient_name: str, doctor: str, appt_date: str, appt_time: str, urgency: str) -> tuple[str, bool]:
    prompt = f"""
You are a healthcare communication assistant drafting a patient reminder message.

Patient: {patient_name}
Doctor: {doctor}
Appointment: {appt_date} at {appt_time}
Urgency level: {urgency}

Draft a short, warm, professional reminder message (3–4 sentences). Mention:
- The appointment date and time
- The doctor's name
- One practical preparation tip appropriate to the urgency level
- Contact info placeholder: [CLINIC_PHONE]

End with: "Not medical advice — for scheduling logistics only."
""".strip()
    return call_ai(prompt)


# ---------------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------------

DOCTORS = ["Dr. Smith", "Dr. Jones", "Dr. Brown"]
SPECIALTIES = {
    "Dr. Smith": "General Practice",
    "Dr. Jones": "Cardiology",
    "Dr. Brown": "Orthopedics",
}

if "appointments" not in st.session_state:
    today = date.today()
    st.session_state.appointments = pd.DataFrame([
        {"Patient Name": "Alice Johnson",  "DOB": "1985-03-12", "Phone": "555-0101", "Doctor": "Dr. Smith", "Date": str(today + timedelta(days=1)), "Time": "09:00 AM", "Reason": "Annual checkup",        "Status": "Confirmed", "Urgency": "Low"},
        {"Patient Name": "Bob Martinez",   "DOB": "1972-07-24", "Phone": "555-0102", "Doctor": "Dr. Jones", "Date": str(today + timedelta(days=2)), "Time": "10:30 AM", "Reason": "Heart palpitations",    "Status": "Pending",   "Urgency": "High"},
        {"Patient Name": "Carol Lee",      "DOB": "1990-11-05", "Phone": "555-0103", "Doctor": "Dr. Brown", "Date": str(today + timedelta(days=3)), "Time": "02:00 PM", "Reason": "Knee pain follow-up",   "Status": "Confirmed", "Urgency": "Medium"},
        {"Patient Name": "David Kim",      "DOB": "1968-01-30", "Phone": "555-0104", "Doctor": "Dr. Smith", "Date": str(today + timedelta(days=5)), "Time": "11:00 AM", "Reason": "Blood pressure check",  "Status": "Confirmed", "Urgency": "Medium"},
        {"Patient Name": "Emma Torres",    "DOB": "2001-06-18", "Phone": "555-0105", "Doctor": "Dr. Jones", "Date": str(today + timedelta(days=7)), "Time": "03:30 PM", "Reason": "EKG test",              "Status": "Pending",   "Urgency": "Medium"},
    ])

if "messages" not in st.session_state:
    st.session_state.messages = pd.DataFrame([
        {"Patient Name": "Alice Johnson", "Doctor": "Dr. Smith", "Date": str(date.today() - timedelta(days=2)), "Message": "Reminder: Your appointment is tomorrow at 9:00 AM.", "Type": "Reminder", "Status": "Sent"},
        {"Patient Name": "Bob Martinez",  "Doctor": "Dr. Jones", "Date": str(date.today() - timedelta(days=1)), "Message": "Please bring your most recent EKG results.",          "Type": "Pre-visit Instructions", "Status": "Sent"},
    ])

# --- PIPELINE STATE: tracks the journey of the current patient across agents ---
if "pipeline" not in st.session_state:
    st.session_state.pipeline = {
        "patient": None, "doctor": None, "urgency": None,
        "intake": False, "triage": False, "scheduling": False, "communication": False,
    }

# --- Widget-state defaults so the pipeline can pre-fill these programmatically ---
st.session_state.setdefault("sched_patient", "")
st.session_state.setdefault("sched_doc", DOCTORS[0])
st.session_state.setdefault("sched_urgency", "Medium")

# ---------------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------------

def urgency_color(level: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level.lower(), "⚪")


def ai_box(title: str, content: str, is_demo: bool):
    if is_demo:
        err = _last_ai_error
        badge = f" *(demo mode — reason: `{err}`)*" if err else " *(demo mode — GEMINI_API_KEY not set)*"
        st.warning(f"**{title}**{badge}\n\n{content}")
    else:
        st.info(f"**{title}**\n\n{content}")


def render_pipeline():
    """A breadcrumb bar showing which agents have run for the current patient."""
    p = st.session_state.pipeline
    patient = p.get("patient")
    steps = [("📋", "Intake", p["intake"]), ("🧠", "Triage", p["triage"]),
             ("📅", "Scheduling", p["scheduling"]), ("💬", "Communication", p["communication"])]
    html = ("<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;"
            "background:#f5f7fa;border:1px solid #dde3ea;border-radius:10px;padding:10px 14px;margin-bottom:10px'>"
            "<span style='font-weight:700;color:#444;margin-right:4px'>🔗 Agent Pipeline:</span>")
    for i, (icon, label, done) in enumerate(steps):
        if done:
            html += (f"<span style='background:#e3f1e6;border:1px solid #8ec79a;color:#1b6e2d;"
                     f"border-radius:20px;padding:4px 12px;font-size:0.85em;font-weight:600'>{icon} {label} ✓</span>")
        else:
            html += (f"<span style='background:#fff;border:1px solid #ccc;color:#999;"
                     f"border-radius:20px;padding:4px 12px;font-size:0.85em'>{icon} {label}</span>")
        if i < len(steps) - 1:
            html += "<span style='color:#bbb;font-weight:700'>→</span>"
    if patient:
        html += (f"<span style='margin-left:auto;color:#555;font-size:0.85em'>"
                 f"Current patient: <b>{patient}</b></span>")
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# TITLE + GLOBAL PIPELINE BAR
# ---------------------------------------------------------------------------

st.title("🏥 Healthcare Scheduling System")
render_pipeline()

tab1, tab2, tab3 = st.tabs(["📋 Intake", "📅 Scheduling", "💬 Communication"])

# ---------------------------------------------------------------------------
# TAB 1 — INTAKE
# ---------------------------------------------------------------------------

with tab1:
    st.warning(DISCLAIMER)
    st.header("Patient Intake")
    st.subheader("Register New Patient")

    with st.form("intake_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            dob  = st.date_input("Date of Birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
            phone = st.text_input("Phone Number")
        with col2:
            doctor = st.selectbox("Assign Doctor", DOCTORS)
            reason = st.text_area("Reason for Visit")
            st.text_input("Insurance Provider (optional)")

        submitted = st.form_submit_button("Register Patient & Run Triage")

    if submitted:
        if not name or not phone or not reason:
            st.error("Please fill in Name, Phone, and Reason for Visit.")
        else:
            with st.spinner("🧠 Triage Agent is assessing..."):
                triage_result, is_demo = triage_agent(reason, name, doctor)

            urgency_guess = "Medium"
            for level in ["High", "Medium", "Low"]:
                if level in triage_result:
                    urgency_guess = level
                    break

            ai_box("🧠 Triage Agent Assessment", triage_result, is_demo)

            appt_date = date.today() + timedelta(days=random.randint(1, 7))
            new_row = {
                "Patient Name": name,
                "DOB": str(dob),
                "Phone": phone,
                "Doctor": doctor,
                "Date": str(appt_date),
                "Time": "09:00 AM",
                "Reason": reason,
                "Status": "Pending",
                "Urgency": urgency_guess,
            }
            st.session_state.appointments = pd.concat(
                [st.session_state.appointments, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            st.success(f"Patient **{name}** registered. Urgency: {urgency_color(urgency_guess)} **{urgency_guess}** — appointment pending with **{doctor}**.")

            # === PIPELINE HAND-OFF #1: Triage -> Scheduling =================
            # Reset the pipeline for this new patient and carry context forward.
            st.session_state.pipeline = {
                "patient": name, "doctor": doctor, "urgency": urgency_guess,
                "intake": True, "triage": True, "scheduling": False, "communication": False,
            }
            # Pre-fill the Scheduling tab's inputs BEFORE Tab 2 renders below.
            st.session_state["sched_patient"] = name
            st.session_state["sched_doc"] = doctor
            st.session_state["sched_urgency"] = urgency_guess
            st.info(
                f"↪️ **Hand-off:** Triage flagged **{urgency_guess}** urgency. "
                f"The patient and urgency were sent to the **📅 Scheduling** tab automatically — "
                f"open it to see the suggested slots."
            )

    st.divider()
    st.subheader("Recent Intake Records")
    display_cols = ["Patient Name", "DOB", "Phone", "Doctor", "Urgency", "Status"]
    st.dataframe(st.session_state.appointments[display_cols], width="stretch", hide_index=True)

# ---------------------------------------------------------------------------
# TAB 2 — SCHEDULING
# ---------------------------------------------------------------------------

with tab2:
    st.warning(DISCLAIMER)
    st.header("Appointment Scheduling")

    col1, col2, col3 = st.columns(3)
    for i, doc in enumerate(DOCTORS):
        doc_appts = st.session_state.appointments[st.session_state.appointments["Doctor"] == doc]
        confirmed = len(doc_appts[doc_appts["Status"] == "Confirmed"])
        pending   = len(doc_appts[doc_appts["Status"] == "Pending"])
        [col1, col2, col3][i].metric(
            label=f"{doc} ({SPECIALTIES[doc]})",
            value=f"{confirmed} confirmed",
            delta=f"{pending} pending",
        )

    st.divider()
    st.subheader("🚦 Urgency Dashboard")

    appts = st.session_state.appointments.copy()
    high_pts   = appts[appts["Urgency"] == "High"][["Patient Name", "Doctor", "Date", "Time", "Reason", "Status"]]
    medium_pts = appts[appts["Urgency"] == "Medium"][["Patient Name", "Doctor", "Date", "Time", "Reason", "Status"]]
    low_pts    = appts[appts["Urgency"] == "Low"][["Patient Name", "Doctor", "Date", "Time", "Reason", "Status"]]

    urg_c1, urg_c2, urg_c3 = st.columns(3)

    with urg_c1:
        st.markdown(
            f"<div style='background:#ffd6d6;border-left:6px solid #cc0000;padding:10px 14px;border-radius:6px;margin-bottom:8px'>"
            f"<b style='color:#cc0000'>🔴 HIGH — {len(high_pts)} patient{'s' if len(high_pts) != 1 else ''}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if len(high_pts):
            for _, row in high_pts.iterrows():
                st.markdown(
                    f"<div style='background:#fff0f0;border:1px solid #ffaaaa;border-radius:5px;padding:8px 12px;margin-bottom:6px;font-size:0.9em'>"
                    f"<b>{row['Patient Name']}</b><br>"
                    f"👨‍⚕️ {row['Doctor']} &nbsp;|&nbsp; 📅 {row['Date']} {row['Time']}<br>"
                    f"<span style='color:#555'>{row['Reason']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No high-urgency patients.")

    with urg_c2:
        st.markdown(
            f"<div style='background:#fff8d6;border-left:6px solid #cc8800;padding:10px 14px;border-radius:6px;margin-bottom:8px'>"
            f"<b style='color:#cc8800'>🟡 MEDIUM — {len(medium_pts)} patient{'s' if len(medium_pts) != 1 else ''}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if len(medium_pts):
            for _, row in medium_pts.iterrows():
                st.markdown(
                    f"<div style='background:#fffcf0;border:1px solid #ffe08a;border-radius:5px;padding:8px 12px;margin-bottom:6px;font-size:0.9em'>"
                    f"<b>{row['Patient Name']}</b><br>"
                    f"👨‍⚕️ {row['Doctor']} &nbsp;|&nbsp; 📅 {row['Date']} {row['Time']}<br>"
                    f"<span style='color:#555'>{row['Reason']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No medium-urgency patients.")

    with urg_c3:
        st.markdown(
            f"<div style='background:#d6f5d6;border-left:6px solid #007700;padding:10px 14px;border-radius:6px;margin-bottom:8px'>"
            f"<b style='color:#007700'>🟢 LOW — {len(low_pts)} patient{'s' if len(low_pts) != 1 else ''}</b>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if len(low_pts):
            for _, row in low_pts.iterrows():
                st.markdown(
                    f"<div style='background:#f0fff0;border:1px solid #90ee90;border-radius:5px;padding:8px 12px;margin-bottom:6px;font-size:0.9em'>"
                    f"<b>{row['Patient Name']}</b><br>"
                    f"👨‍⚕️ {row['Doctor']} &nbsp;|&nbsp; 📅 {row['Date']} {row['Time']}<br>"
                    f"<span style='color:#555'>{row['Reason']}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No low-urgency patients.")

    st.divider()
    st.subheader("All Appointments")

    fc1, fc2 = st.columns(2)
    with fc1:
        filter_doctor = st.selectbox("Filter by Doctor", ["All"] + DOCTORS, key="filter_doctor")
    with fc2:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled"], key="filter_status")

    df = st.session_state.appointments.copy()
    if filter_doctor != "All":
        df = df[df["Doctor"] == filter_doctor]
    if filter_status != "All":
        df = df[df["Status"] == filter_status]
    st.dataframe(df, width="stretch", hide_index=True)

    st.divider()
    st.subheader("📅 Scheduling Agent — Find Best Slots")

    # Show a note when these fields were auto-filled by the Triage hand-off.
    _p = st.session_state.pipeline
    if _p.get("triage") and _p.get("patient") and st.session_state.get("sched_patient") == _p.get("patient"):
        st.caption(f"↪️ Auto-filled from the Triage Agent — urgency **{_p.get('urgency')}** carried over. Just click *Find Best Slots*.")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        sched_patient = st.text_input("Patient Name", placeholder="e.g. Jane Doe", key="sched_patient")
    with sc2:
        sched_doctor  = st.selectbox("Doctor", DOCTORS, key="sched_doc")
    with sc3:
        sched_urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High"], key="sched_urgency")

    if st.button("🔍 Find Best Slots"):
        if not sched_patient.strip():
            st.error("Please enter a patient name.")
        else:
            with st.spinner("📅 Scheduling Agent is finding optimal slots..."):
                slots, is_demo = scheduling_agent_structured(
                    sched_patient, sched_urgency, sched_doctor, st.session_state.appointments
                )
            # Stash the results so the buttons persist across reruns.
            st.session_state["sched_slots"] = slots
            st.session_state["sched_slots_demo"] = is_demo
            st.session_state["sched_slots_patient"] = sched_patient
            st.session_state["sched_slots_doctor"] = sched_doctor
            st.session_state["sched_slots_urgency"] = sched_urgency

            # === PIPELINE HAND-OFF #2: Scheduling -> Communication =========
            st.session_state.pipeline["scheduling"] = True
            st.session_state.pipeline["patient"] = sched_patient
            st.session_state.pipeline["doctor"] = sched_doctor
            st.session_state.pipeline["urgency"] = sched_urgency

    # --- Render the suggested slots as clickable, bookable buttons ---
    if st.session_state.get("sched_slots"):
        slots = st.session_state["sched_slots"]
        is_demo = st.session_state.get("sched_slots_demo", False)
        s_patient = st.session_state.get("sched_slots_patient", "")
        s_doctor = st.session_state.get("sched_slots_doctor", DOCTORS[0])
        s_urgency = st.session_state.get("sched_slots_urgency", "Medium")

        header = "📅 Scheduling Agent Suggestions"
        if is_demo:
            st.warning(f"**{header}** *(demo mode — reason: `{_last_ai_error}`)*\n\nClick a slot below to book it.")
        else:
            st.info(f"**{header}**\n\nClick a slot below to book it for **{s_patient}**.")

        slot_cols = st.columns(len(slots))
        for i, slot in enumerate(slots):
            with slot_cols[i]:
                st.markdown(
                    f"<div style='background:#eef4fb;border:1px solid #b8d2ee;border-radius:8px;"
                    f"padding:10px 12px;margin-bottom:8px;font-size:0.9em;min-height:96px'>"
                    f"<b>Option {i+1}</b><br>"
                    f"📅 {slot['date']}<br>🕐 {slot['time']}<br>"
                    f"<span style='color:#555'>{slot['reason']}</span></div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"✅ Book {slot['time']}", key=f"book_slot_{i}"):
                    # Book it: update existing patient row, or add a new one.
                    appts = st.session_state.appointments
                    mask = appts["Patient Name"] == s_patient
                    if mask.any():
                        appts.loc[mask, "Date"] = slot["date"]
                        appts.loc[mask, "Time"] = slot["time"]
                        appts.loc[mask, "Doctor"] = s_doctor
                        appts.loc[mask, "Status"] = "Confirmed"
                        appts.loc[mask, "Urgency"] = s_urgency
                    else:
                        st.session_state.appointments = pd.concat([appts, pd.DataFrame([{
                            "Patient Name": s_patient, "DOB": "", "Phone": "",
                            "Doctor": s_doctor, "Date": slot["date"], "Time": slot["time"],
                            "Reason": "Scheduled via Scheduling Agent",
                            "Status": "Confirmed", "Urgency": s_urgency,
                        }])], ignore_index=True)

                    # Hand-off to Communication with the booked details.
                    st.session_state["comm_doctor"] = s_doctor
                    if s_patient in st.session_state.appointments["Patient Name"].values:
                        st.session_state["comm_patient"] = s_patient
                    st.session_state.pop("sched_slots", None)  # clear the buttons
                    st.success(
                        f"✅ Booked **{s_patient}** with **{s_doctor}** on "
                        f"**{slot['date']} at {slot['time']}** (status: Confirmed). "
                        f"↪️ Sent to the **💬 Communication** tab."
                    )
                    st.rerun()

    st.divider()
    st.subheader("Update Appointment Status")

    with st.form("update_form"):
        uc1, uc2 = st.columns(2)
        with uc1:
            selected_patient = st.selectbox("Select Patient", st.session_state.appointments["Patient Name"].tolist())
        with uc2:
            new_status = st.selectbox("New Status", ["Confirmed", "Pending", "Cancelled"])
        if st.form_submit_button("Update Status"):
            st.session_state.appointments.loc[
                st.session_state.appointments["Patient Name"] == selected_patient, "Status"
            ] = new_status
            st.success(f"Updated **{selected_patient}**'s status to **{new_status}**.")
            st.rerun()

# ---------------------------------------------------------------------------
# TAB 3 — COMMUNICATION
# ---------------------------------------------------------------------------

with tab3:
    st.warning(DISCLAIMER)
    st.header("Patient Communication")

    st.subheader("💬 Communication Agent — Draft Reminder")

    patients = st.session_state.appointments["Patient Name"].unique().tolist()

    # If a hand-off pre-filled a patient who isn't in the list, fall back safely.
    if st.session_state.get("comm_patient") not in patients:
        st.session_state.pop("comm_patient", None)

    cm1, cm2 = st.columns(2)
    with cm1:
        comm_patient = st.selectbox("Patient", patients, key="comm_patient")
    with cm2:
        comm_doctor = st.selectbox("From Doctor", DOCTORS, key="comm_doctor")

    patient_row = st.session_state.appointments[
        st.session_state.appointments["Patient Name"] == comm_patient
    ]
    comm_date    = patient_row["Date"].values[0]    if len(patient_row) else str(date.today())
    comm_time    = patient_row["Time"].values[0]    if len(patient_row) else "TBD"
    comm_urgency = patient_row["Urgency"].values[0] if len(patient_row) and "Urgency" in patient_row.columns else "Medium"

    st.caption(f"Appointment on file: **{comm_date}** at **{comm_time}** · Urgency: {urgency_color(comm_urgency)} {comm_urgency}")

    if st.button("✍️ Draft Message"):
        with st.spinner("💬 Communication Agent is drafting..."):
            comm_result, is_demo = communication_agent(comm_patient, comm_doctor, comm_date, comm_time, comm_urgency)
        ai_box("💬 Communication Agent Draft", comm_result, is_demo)
        st.session_state["last_comm_draft"] = comm_result

        # === PIPELINE HAND-OFF #3: Communication complete ==================
        st.session_state.pipeline["communication"] = True
        st.session_state.pipeline["patient"] = comm_patient
        st.success("✅ **Pipeline complete** — all three agents have run for this patient.")

    if "last_comm_draft" in st.session_state:
        st.divider()
        st.subheader("Send Message")
        with st.form("message_form", clear_on_submit=True):
            msg_type = st.selectbox("Message Type", ["Reminder", "Pre-visit Instructions", "Follow-up", "Test Results", "General"])
            msg_body = st.text_area("Edit & Send", value=st.session_state["last_comm_draft"], height=150)
            if st.form_submit_button("Send Message"):
                if not msg_body:
                    st.error("Message cannot be empty.")
                else:
                    new_msg = {
                        "Patient Name": comm_patient,
                        "Doctor": comm_doctor,
                        "Date": str(date.today()),
                        "Message": msg_body,
                        "Type": msg_type,
                        "Status": "Sent",
                    }
                    st.session_state.messages = pd.concat(
                        [st.session_state.messages, pd.DataFrame([new_msg])],
                        ignore_index=True,
                    )
                    st.session_state.pop("last_comm_draft", None)
                    st.success(f"Message sent to **{comm_patient}**.")
                    st.rerun()

    st.divider()
    st.subheader("Message History")
    st.dataframe(st.session_state.messages, width="stretch", hide_index=True)