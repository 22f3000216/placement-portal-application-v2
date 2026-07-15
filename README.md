# Placement Portal Application (PPA)

Full-stack placement management system built with Flask + Vue 3 (CLI) + Bootstrap + SQLite + Redis + Celery + JWT.

## Architecture
- Backend: Flask REST API, JWT-based authentication (Flask-JWT-Extended)
- Frontend: Vue 3 (Vue-CLI, Single File Components), Vue Router, Axios
- Backend and Frontend run as two separate servers (Flask on port 5000, Vue dev server on port 8080), connected via CORS

## How to Run

### 1. Install and start Redis
```
redis-server
```

### 2. Backend setup
```
cd Backend
pip install -r requirements.txt
python3 seed_admin.py
python3 app.py
```
Flask runs on http://127.0.0.1:5000

Admin login: admin@ppa.com / admin123

### 3. Frontend setup (separate terminal)
```
cd Frontend
npm install
npm run serve
```
Vue app runs on http://localhost:8080

### 4. Open the app
Go to http://localhost:8080 in your browser.

## Optional: Background jobs (Celery)
```
cd Backend
celery -A tasks.celery_app worker --loglevel=info
```

## Optional: Celery Beat (scheduled daily/monthly jobs)
```
cd Backend
celery -A tasks.celery_app beat --loglevel=info
```

## Optional: See real emails (MailHog)
Interview reminders, deadline reminders, and the monthly report are emailed via
Python's built-in smtplib to localhost:1025. Install MailHog to view them at
http://localhost:8025

## Roles
- Admin (admin@ppa.com / admin123): approve/reject companies and drives, search,
  blacklist, view all applications, view/download placement reports, view stats.
- Company: register profile (HR contact, website), post drives (eligibility
  criteria, deadline, skills, experience), view applicants, shortlist/
  interview/offer/reject with feedback, manage drive status, export CSV history.
- Student: register/edit profile (resume link, skills, experience), search and
  filter eligible drives, apply, track status, accept/decline offers, download
  offer letter, export CSV history.
