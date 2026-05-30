import streamlit as st
import pandas as pd
from datetime import date, time, timedelta
import random

st.set_page_config(page_title="Healthcare Scheduler", layout="wide")

st.title("Healthcare Scheduling System")

DOCTORS = ["Dr. Smith", "Dr. Jones", "Dr. Brown"]

SPECIALTIES = {
    "Dr. Smith": "General Practice",
    "Dr. Jones": "Cardiology",
    "Dr. Brown": "Orthopedics",
}

if "appointments" not in st.session_state:
    today = date.today()
    st.session_state.appointments = pd.DataFrame([
        {
            "Patient Name": "Alice Johnson",
            "DOB": "1985-03-12",
            "Phone": "555-0101",
            "Doctor": "Dr. Smith",
            "Date": str(today + timedelta(days=1)),
            "Time": "09:00 AM",
            "Reason": "Annual checkup",
            "Status": "Confirmed",
        },
        {
            "Patient Name": "Bob Martinez",
            "DOB": "1972-07-24",
            "Phone": "555-0102",
            "Doctor": "Dr. Jones",
            "Date": str(today + timedelta(days=2)),
            "Time": "10:30 AM",
            "Reason": "Heart palpitations",
            "Status": "Pending",
        },
        {
            "Patient Name": "Carol Lee",
            "DOB": "1990-11-05",
            "Phone": "555-0103",
            "Doctor": "Dr. Brown",
            "Date": str(today + timedelta(days=3)),
            "Time": "02:00 PM",
            "Reason": "Knee pain follow-up",
            "Status": "Confirmed",
        },
        {
            "Patient Name": "David Kim",
            "DOB": "1968-01-30",
            "Phone": "555-0104",
            "Doctor": "Dr. Smith",
            "Date": str(today + timedelta(days=5)),
            "Time": "11:00 AM",
            "Reason": "Blood pressure check",
            "Status": "Confirmed",
        },
        {
            "Patient Name": "Emma Torres",
            "DOB": "2001-06-18",
            "Phone": "555-0105",
            "Doctor": "Dr. Jones",
            "Date": str(today + timedelta(days=7)),
            "Time": "03:30 PM",
            "Reason": "EKG test",
            "Status": "Pending",
        },
    ])

if "messages" not in st.session_state:
    st.session_state.messages = pd.DataFrame([
        {
            "Patient Name": "Alice Johnson",
            "Doctor": "Dr. Smith",
            "Date": str(date.today() - timedelta(days=2)),
            "Message": "Reminder: Your appointment is tomorrow at 9:00 AM.",
            "Type": "Reminder",
            "Status": "Sent",
        },
        {
            "Patient Name": "Bob Martinez",
            "Doctor": "Dr. Jones",
            "Date": str(date.today() - timedelta(days=1)),
            "Message": "Please bring your most recent EKG results to your appointment.",
            "Type": "Pre-visit Instructions",
            "Status": "Sent",
        },
    ])

tab1, tab2, tab3 = st.tabs(["Intake", "Scheduling", "Communication"])

with tab1:
    st.header("Patient Intake")
    st.subheader("Register New Patient")

    with st.form("intake_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            dob = st.date_input("Date of Birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
            phone = st.text_input("Phone Number")
        with col2:
            doctor = st.selectbox("Assign Doctor", DOCTORS)
            reason = st.text_area("Reason for Visit")
            insurance = st.text_input("Insurance Provider (optional)")

        submitted = st.form_submit_button("Register Patient & Schedule Appointment")

        if submitted:
            if not name or not phone or not reason:
                st.error("Please fill in all required fields (Name, Phone, Reason).")
            else:
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
                }
                st.session_state.appointments = pd.concat(
                    [st.session_state.appointments, pd.DataFrame([new_row])],
                    ignore_index=True,
                )
                st.success(f"Patient **{name}** registered and appointment scheduled with **{doctor}** on **{appt_date}**.")

    st.divider()
    st.subheader("Recent Intake Records")
    st.dataframe(
        st.session_state.appointments[["Patient Name", "DOB", "Phone", "Doctor", "Status"]],
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.header("Appointment Scheduling")

    col1, col2, col3 = st.columns(3)
    for i, doctor in enumerate(DOCTORS):
        doctor_appts = st.session_state.appointments[
            st.session_state.appointments["Doctor"] == doctor
        ]
        confirmed = len(doctor_appts[doctor_appts["Status"] == "Confirmed"])
        pending = len(doctor_appts[doctor_appts["Status"] == "Pending"])
        col = [col1, col2, col3][i]
        with col:
            st.metric(label=f"{doctor} ({SPECIALTIES[doctor]})", value=f"{confirmed} confirmed", delta=f"{pending} pending")

    st.divider()
    st.subheader("All Appointments")

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_doctor = st.selectbox("Filter by Doctor", ["All"] + DOCTORS, key="filter_doctor")
    with filter_col2:
        filter_status = st.selectbox("Filter by Status", ["All", "Confirmed", "Pending", "Cancelled"], key="filter_status")

    df = st.session_state.appointments.copy()
    if filter_doctor != "All":
        df = df[df["Doctor"] == filter_doctor]
    if filter_status != "All":
        df = df[df["Status"] == filter_status]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Update Appointment Status")

    with st.form("update_form"):
        update_col1, update_col2 = st.columns(2)
        with update_col1:
            patient_options = st.session_state.appointments["Patient Name"].tolist()
            selected_patient = st.selectbox("Select Patient", patient_options)
        with update_col2:
            new_status = st.selectbox("New Status", ["Confirmed", "Pending", "Cancelled"])
        update_btn = st.form_submit_button("Update Status")
        if update_btn:
            st.session_state.appointments.loc[
                st.session_state.appointments["Patient Name"] == selected_patient, "Status"
            ] = new_status
            st.success(f"Updated **{selected_patient}**'s appointment to **{new_status}**.")
            st.rerun()

with tab3:
    st.header("Patient Communication")

    st.subheader("Send Message to Patient")

    with st.form("message_form", clear_on_submit=True):
        msg_col1, msg_col2 = st.columns(2)
        with msg_col1:
            msg_patient = st.selectbox(
                "Patient",
                st.session_state.appointments["Patient Name"].unique().tolist(),
            )
            msg_doctor = st.selectbox("From Doctor", DOCTORS, key="msg_doctor")
        with msg_col2:
            msg_type = st.selectbox("Message Type", ["Reminder", "Pre-visit Instructions", "Follow-up", "Test Results", "General"])
        msg_body = st.text_area("Message", height=100)
        send_btn = st.form_submit_button("Send Message")

        if send_btn:
            if not msg_body:
                st.error("Please enter a message.")
            else:
                new_msg = {
                    "Patient Name": msg_patient,
                    "Doctor": msg_doctor,
                    "Date": str(date.today()),
                    "Message": msg_body,
                    "Type": msg_type,
                    "Status": "Sent",
                }
                st.session_state.messages = pd.concat(
                    [st.session_state.messages, pd.DataFrame([new_msg])],
                    ignore_index=True,
                )
                st.success(f"Message sent to **{msg_patient}**.")

    st.divider()
    st.subheader("Message History")
    st.dataframe(st.session_state.messages, use_container_width=True, hide_index=True)
