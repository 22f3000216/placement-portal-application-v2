"""
Run this any time to fire the reminder jobs immediately, without waiting
for Celery Beat's schedule. Useful for testing/demo - check MailHog at
http://localhost:8025 right after running this.

Needs: redis-server running, and the celery worker running
       (celery -A tasks.celery_app worker --loglevel=info -P solo)

Usage (from the Backend/ folder, with venv active):
    python trigger_reminders_now.py
"""
from tasks import send_deadline_reminders, send_interview_reminders

print("Triggering send_deadline_reminders...")
r1 = send_deadline_reminders.delay()
print("  ->", r1.get(timeout=15))

print("Triggering send_interview_reminders...")
r2 = send_interview_reminders.delay()
print("  ->", r2.get(timeout=15))

print("\nDone. Check MailHog at http://localhost:8025 for the emails.")
print("If it says 'Sent 0 emails', it means there's no job with a deadline")
print("in the next 24 hours (or no interview in the next 24 hours) that a")
print("student hasn't already applied to - not a bug, just no matching data yet.")
