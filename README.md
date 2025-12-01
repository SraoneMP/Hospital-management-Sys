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
celery -A celery_app worker --pool=solo --loglevel=info
celery -A celery_app beat --loglevel=info
```
### MailHog (Email Testing)
MailHog web interface: **http://localhost:8025**

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


## Default Admin

Email: admin@hospital.local
Password: admin123




