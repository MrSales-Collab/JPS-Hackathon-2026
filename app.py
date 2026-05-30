import os
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
# Swap providers by editing only this section.
# Current provider: Google Gemini (free tier)
# To switch: replace the body of _call_gemini() or point AI_PROVIDER elsewhere.
# ---------------------------------------------------------------------------

AI_PROVIDER = "gemini"   # change to "anthropic", "openai", etc. when ready

def _demo_response(prompt: str) -> str:
    """Fallback used when no API key is configured or the provider is rate-limited."""
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
    import google.generativeai as genai
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


def call_ai(prompt: str) -> tuple[str, bool]:
    """
    Single entry point for all AI calls.
    Returns (response_text, is_demo).
    is_demo=True means the fallback was used (no key, quota exceeded, etc.).
    To switch providers: change AI_PROVIDER above, or add a new _call_<provider>() branch.
    """
    try:
        if AI_PROVIDER == "gemini":
            return _call_gemini(prompt), False
        # Future providers:
        # elif AI_PROVIDER == "anthropic":
        #     return _call_anthropic(prompt), False
        # elif AI_PROVIDER == "openai":
        #     return _call_openai(prompt), False
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {AI_PROVIDER}")
    except Exception:
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

# ---------------------------------------------------------------------------
# UI HELPERS
# ---------------------------------------------------------------------------

def urgency_color(level: str) -> str:
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(level.lower(), "⚪")


def ai_box(title: str, content: str, is_demo: bool):
    """Render a labeled AI result box with a demo badge when applicable."""
    badge = " *(demo mode — add API key for live results)*" if is_demo else ""
    st.info(f"**{title}**{badge}\n\n{content}")


# ---------------------------------------------------------------------------
# TITLE
# ---------------------------------------------------------------------------

st.title("🏥 Healthcare Scheduling System")

# ---------------------------------------------------------------------------
# TAB 1 — INTAKE
# ---------------------------------------------------------------------------

tab1, tab2, tab3 = st.tabs(["📋 Intake", "📅 Scheduling", "💬 Communication"])

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

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        sched_patient = st.text_input("Patient Name", placeholder="e.g. Jane Doe", key="sched_patient")
    with sc2:
        sched_doctor  = st.selectbox("Doctor", DOCTORS, key="sched_doc")
    with sc3:
        sched_urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High"], index=1, key="sched_urgency")

    if st.button("🔍 Find Best Slots"):
        if not sched_patient.strip():
            st.error("Please enter a patient name.")
        else:
            with st.spinner("📅 Scheduling Agent is finding optimal slots..."):
                sched_result, is_demo = scheduling_agent(
                    sched_patient, sched_urgency, sched_doctor, st.session_state.appointments
                )
            ai_box("📅 Scheduling Agent Suggestions", sched_result, is_demo)

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
    st.dataframe(st.session_state.messages, use_container_width=True, hide_index=True)
