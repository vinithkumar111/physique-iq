# PhysiqueIQ

PhysiqueIQ is a modern fitness coaching platform built with FastAPI, Jinja2, SQLAlchemy, and SQLite. It provides role-based dashboards for admins, trainers, and members, along with AI-style coaching support and workout/nutrition tracking.

## Features

- Admin dashboard for user and platform management
- Trainer dashboard for member rosters and plan creation
- Member dashboard for profile, workouts, nutrition, measurements, and AI coach interaction
- JWT-based authentication with role-based access control
- SQLite-backed persistence for users, profiles, and plans
- Responsive UI with Bootstrap and custom styling

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- Jinja2 Templates
- SQLite
- Pydantic
- pytest

## Project Structure

- app/ - application package with routes, auth, models, schemas, and database setup
- templates/ - HTML templates for the dashboards and auth pages
- static/ - static assets such as CSS and JS
- tests/ - regression tests for authentication and dashboard features

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/vinithkumar111/physique-iq.git
cd physique-iq
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python main.py
```

Or with uvicorn:

```bash
.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### 5. Access the app

Open your browser at:

- http://127.0.0.1:8000/login

## Default Seed Accounts

- Admin: admin@physiqueiq.com / adminpassword
- Trainer: trainer@physiqueiq.com / trainerpassword
- Member: member@physiqueiq.com / memberpassword

## Testing

Run the test suite with:

```bash
pytest -q
```
