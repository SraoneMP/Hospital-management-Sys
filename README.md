# Hospital Management System (HMS)

Web-based hospital management system using Flask (backend) and Vue.js (frontend).

## Features

- Admin: Manage doctors, patients, departments, appointments
- Doctor: View schedule, update availability, add treatments
- Patient: Register, book/reschedule/cancel appointments, view history
- JWT authentication and role-based access
- Redis caching and Celery background jobs

## Quick Start

### Backend
1. Python 3.8+, Redis required
2. Setup:
  ```powershell
  cd backend
  python -m venv .venv
  .venv\Scripts\Activate
  pip install -r requirements.txt
  python app.py
  ```

### Frontend
1. Node.js 16+
2. Setup:
  ```powershell
  cd frontend
  npm install
  npm run dev
  ```

### Redis & Celery
Start Redis, then in backend:
```powershell
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

## Project Structure

backend/: Flask app, models, API, Celery tasks
frontend/: Vue.js SPA, components, views
exports/: Generated reports

## Main API Endpoints

- `/api/auth` (POST/PUT): Register/login
- `/api/admin/*`: Admin management
- `/api/doctor/*`: Doctor dashboard
- `/api/patient/*`: Patient dashboard
- `/api/appointments`: Appointment management

## Environment Variables

Create `.env` in backend/ with keys for Flask, JWT, Redis, email, etc.

## Default Admin

Email: admin@hospital.local
Password: admin123

## Notes

- SQLite for development; use PostgreSQL/MySQL for production
- Build frontend for deployment and serve with Nginx/Apache


# Hospital Management System (HMS)

This is a web-based hospital management system built with Flask (backend) and Vue.js (frontend).

## Features

- Admin: Manage doctors, patients, departments, appointments
- Doctor: View schedule, update availability, add treatments
- Patient: Register, book/reschedule/cancel appointments, view history
- JWT authentication and role-based access
- Redis caching and Celery background jobs

## Quick Start

### Backend
1. Install Python 3.8+, Redis
2. Create virtual environment and install requirements:
  ```powershell
  cd backend
  python -m venv .venv
  .venv\Scripts\Activate
  pip install -r requirements.txt
  python app.py
  ```

### Frontend
1. Install Node.js 16+
2. Install dependencies and start dev server:
  ```powershell
  cd frontend
  npm install
  npm run dev
  ```

### Redis & Celery
Start Redis server, then in backend:
```powershell
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

## Project Structure

backend/: Flask app, models, API, Celery tasks
frontend/: Vue.js SPA, components, views
exports/: Generated reports

## API Endpoints

- `/api/auth` (POST/PUT): Register/login
- `/api/admin/*`: Admin management
- `/api/doctor/*`: Doctor dashboard
- `/api/patient/*`: Patient dashboard
- `/api/appointments`: Appointment management

## Environment Variables

Create `.env` in backend/ with keys for Flask, JWT, Redis, email, etc.

## Default Admin

Email: admin@hospital.local
Password: admin123

## Notes

- SQLite used for development; switch to PostgreSQL/MySQL for production
- For deployment, build frontend and serve with Nginx/Apache


