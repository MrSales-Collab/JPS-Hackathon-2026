# Healthcare Scheduling App

A Streamlit-based healthcare scheduling application with patient intake, appointment management, and patient communication tools.

## Run & Operate

- `streamlit run app.py` — run the healthcare scheduling app (port 5000)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 8080)

## Stack

- Python 3.11 + Streamlit (main app)
- pnpm workspaces, Node.js 24, TypeScript 5.9 (API server)

## Where things live

- `app.py` — main Streamlit application (Intake, Scheduling, Communication tabs)
- `.streamlit/config.toml` — Streamlit server config (port 5000, headless, 0.0.0.0)
- `scripts/src/main.py` — standalone Python script

## Product

Three-tab healthcare scheduling interface:
- **Intake** — register new patients and assign them to a doctor
- **Scheduling** — view and update appointments across Dr. Smith, Dr. Jones, and Dr. Brown
- **Communication** — send messages/reminders to patients and view message history

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Streamlit session state holds appointments and messages in memory (no database yet)
- Do not change `.streamlit/config.toml` — server settings are pre-configured

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
