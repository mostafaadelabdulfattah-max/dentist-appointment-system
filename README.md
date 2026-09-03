# AI-Powered Dentist Appointment System

A Django + PostgreSQL web application for booking dental appointments, with
a rule-based AI assistant that helps patients pick the right specialty and
dentist. Built as my graduation project from ITI , following the provided SRS.

## Features

- Patient registration, login, logout, and profile management
- Browse dentists, view their specialty and weekly working schedule
- Real-time appointment availability, generated from each dentist's schedule
- Appointment booking with **backend-enforced** double-booking prevention
  (a database constraint is the final safety net, not just a Python check)
- Upcoming appointments, appointment history, and cancellation
- Dentist dashboard: view appointments, confirm/update their status
- Administrator management of dentists, specialties, schedules, and
  appointments via the Django admin site
- AI Appointment Assistant: patients describe a dental problem in plain
  language and get a recommended specialty + real, bookable dentist/time
  suggestions — it explicitly does **not** diagnose

## Technology Stack

- **Backend:** Python, Django
- **Database:** PostgreSQL
- **Frontend:** Django Templates, HTML, CSS, Vanilla JavaScript (no frontend
  framework, per project constraints)

## System Actors

| Actor | Capabilities |
|---|---|
| Patient | Register, log in, browse dentists, book/cancel appointments, view history, use the AI assistant, edit their own profile |
| Dentist | Log in, view their own appointments, confirm/update appointment status |
| Administrator | Manage dentists, specialties, schedules, and appointments via `/admin/` |
| AI Assistant | Recommends a specialty and real available appointments from a patient's description — navigation only, never a diagnosis |

## Project Structure

```
dentist_appointment_system/
├── manage.py
├── config/              # settings, root urls, wsgi/asgi
├── accounts/            # Patient profile, auth views, role decorators
├── dentists/            # Specialty, Dentist, DentistSchedule + admin CRUD
├── appointments/        # Availability logic, booking, cancellation, dentist dashboard
├── ai_assistant/        # Specialty recommendation service + assistant page
├── templates/           # Shared templates (base.html, home.html, per-app subfolders)
├── static/               # css/, js/, images/
├── requirements.txt
├── .env.example
└── .gitignore
```

## Installation



### 1. Clone/unzip and enter the project folder

```bash
cd dentist_appointment_system
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## PostgreSQL Setup

```sql
CREATE DATABASE dentist_appointment_db;
CREATE USER dentist_app_user WITH PASSWORD 'choose_a_real_password';
ALTER ROLE dentist_app_user SET client_encoding TO 'utf8';
ALTER ROLE dentist_app_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE dentist_app_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE dentist_appointment_db TO dentist_app_user;
```

On PostgreSQL 15+, also run:
```sql
\c dentist_appointment_db
GRANT ALL ON SCHEMA public TO dentist_app_user;
```

## Environment Variables

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

```text
DEBUG=True
SECRET_KEY=<a real secret key>
DB_NAME=dentist_appointment_db
DB_USER=dentist_app_user
DB_PASSWORD=<your real password>
DB_HOST=localhost
DB_PORT=5432
```

**Set `DEBUG=False` before deploying anywhere public** — with `DEBUG=True`,
Django shows detailed error pages that can leak internal information.

## Running the Project

```bash
python manage.py migrate
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` (or whichever port you choose — some
environments reserve port 8000, in which case use e.g. `runserver 8080`).

## Creating an Admin User

```bash
python manage.py createsuperuser
```

Log in at `/admin/` to manage specialties, dentists, schedules, and
appointments. Dentist accounts are created here (as a regular `User`, then
linked to a `Dentist` record) — there's no public dentist self-registration,
by design.

## Testing

Run Django's test suite:

```bash
python manage.py test
```

## API Documentation

Most pages are server-rendered Django views. One JSON endpoint exists,
used by the booking page's JavaScript:

### `GET /appointments/available-slots/`

Returns the available appointment times for a dentist on a given date.
**Requires login.**

**Query parameters:**
| Param | Type | Example |
|---|---|---|
| `dentist_id` | integer | `3` |
| `date` | `YYYY-MM-DD` | `2026-09-14` |

**Response:**
```json
{"slots": ["09:00", "09:30", "10:30"]}
```

Or, for an invalid date:
```json
{"error": "Please select a valid appointment date."}
```

This endpoint only controls what the browser *displays*. The actual
booking (`POST /appointments/book/<dentist_id>/`) independently re-checks
availability in `appointments/services.py` before creating anything — the
JSON endpoint is never trusted as the security boundary.

## AI Assistant

The assistant (`ai_assistant/services.py`) uses keyword matching to map a
patient's description to a dental specialty (see `SPECIALTY_KEYWORDS`), then
looks up real dentists in that specialty and their real next available
slots using the exact same availability function the booking page uses. It
always includes a fixed disclaimer and never diagnoses.

If you later want to swap in a real AI API, `identify_specialty_name()` is
the only function that needs to change — keep an API key in `.env`, never
hard-coded, following the same pattern as `SECRET_KEY` and the database
credentials above.

## Database Design

| Model | Purpose | Key relationships |
|---|---|---|
| `Patient` | Extra profile fields for a patient | 1:1 with Django `User` |
| `Specialty` | A dental specialty (e.g. General Dentistry) | — |
| `Dentist` | Extra profile fields for a dentist | 1:1 with `User`, FK to `Specialty` |
| `DentistSchedule` | One working day/time-block for a dentist | FK to `Dentist` |
| `Appointment` | A booked appointment | FK to `Patient` and `Dentist`; unique constraint on `(dentist, date, start_time)` for non-cancelled rows |

Administrators aren't a separate model — an admin is simply a Django `User`
with `is_staff=True`, using Django's built-in admin site.

## Future Improvements

(Explicitly out of scope for this version, per the SRS: online payments,
video consultations, patient–dentist chat, notifications, a mobile app, or
any non-vanilla-JS frontend framework.)

- Automated email/SMS reminders for upcoming appointments
- A real AI API integration behind `identify_specialty_name()`
- Dentist-facing schedule editing UI (currently managed via `/admin/`)
- Pagination for large dentist/appointment lists

## License

This is my ITI graduation project, built for educational purposes.
No license is specified — please contact the author before reusing.
