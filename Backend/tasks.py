import sys
import csv
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery
from celery.schedules import crontab
from flask import render_template

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/2"
)

celery_app.conf.beat_schedule = {
    "daily-deadline-reminder": {
        "task": "tasks.send_deadline_reminders",
        "schedule": timedelta(minutes=5),
    },
    "daily-interview-reminder": {
        "task": "tasks.send_interview_reminders",
        "schedule": timedelta(minutes=5),
    },
    "monthly-report": {
        "task": "tasks.generate_monthly_report",
        "schedule": crontab(hour=8, minute=0, day_of_month=1),
    },
}


def send_email(to_address, subject, body, is_html=False):
    from config import Config

    subtype = "html" if is_html else "plain"
    msg = MIMEText(body, subtype)
    msg["Subject"] = subject
    msg["From"] = Config.MAIL_SENDER
    msg["To"] = to_address

    with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
        server.starttls()
        server.login(Config.MAIL_SENDER, Config.MAIL_PASSWORD)
        server.sendmail(Config.MAIL_SENDER, [to_address], msg.as_string())


@celery_app.task
def send_deadline_reminders():
    from app import app
    from models import JobPosition, Student, Application, User

    with app.app_context():
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)

        closing_soon = JobPosition.query.filter(
            JobPosition.is_approved == True,
            JobPosition.status == "Active",
            JobPosition.application_deadline != None,
            JobPosition.application_deadline >= now,
            JobPosition.application_deadline <= tomorrow
        ).all()

        sent_count = 0
        for job in closing_soon:
            already_applied_ids = {a.student_id for a in Application.query.filter_by(job_id=job.id).all()}
            all_students = Student.query.all()

            for student in all_students:
                if student.id in already_applied_ids or student.is_blocked:
                    continue

                student_user = User.query.get(student.user_id)
                body = (
                    f"Hi {student.name},\n\n"
                    f"The application deadline for {job.title} at {job.company.name} "
                    f"is approaching ({job.application_deadline}). Apply soon if you're interested!\n\n"
                    f"Placement Portal"
                )
                try:
                    send_email(student_user.email, f"Application Deadline Approaching - {job.title}", body)
                    sent_count += 1
                except Exception as e:
                    print(f"Could not send deadline reminder to {student_user.email}: {e}")

    return f"Sent {sent_count} deadline reminder emails"


@celery_app.task
def send_interview_reminders():
    from app import app
    from models import Application, User

    with app.app_context():
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)

        upcoming = Application.query.filter(
            Application.status == "Interview",
            Application.interview_datetime >= now,
            Application.interview_datetime <= tomorrow
        ).all()

        sent_count = 0
        for application in upcoming:
            student_user = User.query.get(application.student.user_id)
            body = (
                f"Hi {application.student.name},\n\n"
                f"This is a reminder that your interview for {application.job.title} "
                f"at {application.job.company.name} is scheduled on "
                f"{application.interview_datetime}.\n\nGood luck!"
            )
            try:
                send_email(student_user.email, f"Interview Reminder - {application.job.title}", body)
                sent_count += 1
            except Exception as e:
                print(f"Could not send email to {student_user.email}: {e}")

    return f"Sent {sent_count} interview reminder emails"


@celery_app.task
def generate_monthly_report():
    from app import app
    from models import Placement, Student, Company, Application, JobPosition, User

    with app.app_context():
        placements = Placement.query.all()
        data = []
        for p in placements:
            student = Student.query.get(p.student_id)
            company = Company.query.get(p.company_id)
            data.append({
                "student_name": student.name,
                "company_name": company.name,
                "package": p.package
            })


        all_applications = Application.query.all()
        status_counts = {}
        for a in all_applications:
            status_counts[a.status] = status_counts.get(a.status, 0) + 1


        company_placement_counts = {}
        for p in placements:
            company = Company.query.get(p.company_id)
            company_placement_counts[company.name] = company_placement_counts.get(company.name, 0) + 1

        avg_package = sum(p.package or 0 for p in placements) / len(placements) if placements else 0
        total_drives = JobPosition.query.filter_by(is_approved=True).count()

        html = render_template(
            "report.html",
            placements=data,
            total_placed=len(data),
            total_applications=len(all_applications),
            total_drives=total_drives,
            status_counts=status_counts,
            company_placement_counts=company_placement_counts,
            avg_package=round(avg_package, 2)
        )

        os.makedirs("generated_files", exist_ok=True)
        filename = f"generated_files/report_{datetime.utcnow().strftime('%Y_%m')}.html"
        with open(filename, "w") as f:
            f.write(html)


        admin_user = User.query.filter_by(role="admin").first()
        if admin_user:
            try:
                send_email(
                    admin_user.email,
                    f"Monthly Placement Report - {datetime.utcnow().strftime('%B %Y')}",
                    html,
                    is_html=True
                )
            except Exception as e:
                print(f"Could not email report to admin: {e}")

    return f"Report saved at {filename} and emailed to admin"


@celery_app.task
def export_company_csv(company_id, export_job_id):
    from app import app
    from extensions import db
    from models import Application, JobPosition, Placement, ExportJob, Company, User

    with app.app_context():
        job_ids = [j.id for j in JobPosition.query.filter_by(company_id=company_id).all()]
        applications = Application.query.filter(Application.job_id.in_(job_ids)).all() if job_ids else []
        placements = Placement.query.filter_by(company_id=company_id).all()

        os.makedirs("generated_files", exist_ok=True)
        filename = f"generated_files/company_{company_id}_history.csv"

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["-- Applications --"])
            writer.writerow(["Student Name", "Job Title", "Status", "Applied At"])
            for a in applications:
                writer.writerow([a.student.name, a.job.title, a.status, a.applied_at])

            writer.writerow([])
            writer.writerow(["-- Placements --"])
            writer.writerow(["Student Name", "Position", "Package", "Joining Date"])
            for p in placements:
                writer.writerow([p.application.student.name, p.position, p.package, p.joining_date])

        export_job = ExportJob.query.get(export_job_id)
        if export_job:
            export_job.status = "ready"
            export_job.file_path = filename
            db.session.commit()

        company = Company.query.get(company_id)
        company_user = User.query.get(company.user_id)
        try:
            send_email(company_user.email, "Your CSV Export is Ready",
                       f"Hi {company.name},\n\nYour application/placement history export is complete. You can download it from your dashboard.\n\nPlacement Portal")
        except Exception as e:
            print(f"Could not send export alert email: {e}")

    return f"CSV saved at {filename}"


@celery_app.task
def export_applications_csv(student_id, export_job_id):
    from app import app
    from extensions import db
    from models import Application, JobPosition, Company, ExportJob, Student, User

    with app.app_context():
        applications = Application.query.filter_by(student_id=student_id).all()

        os.makedirs("generated_files", exist_ok=True)
        filename = f"generated_files/applications_{student_id}.csv"

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Applied Date"])
            for a in applications:
                job = JobPosition.query.get(a.job_id)
                company = Company.query.get(job.company_id)
                writer.writerow([student_id, company.name, job.title, a.status, a.applied_at])

        export_job = ExportJob.query.get(export_job_id)
        if export_job:
            export_job.status = "ready"
            export_job.file_path = filename
            db.session.commit()

        student = Student.query.get(student_id)
        student_user = User.query.get(student.user_id)
        try:
            send_email(student_user.email, "Your CSV Export is Ready",
                       f"Hi {student.name},\n\nYour application history export is complete. You can download it from your dashboard.\n\nPlacement Portal")
        except Exception as e:
            print(f"Could not send export alert email: {e}")

    return f"CSV saved at {filename}"