from extensions import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(120))
    location = db.Column(db.String(120))
    hr_contact = db.Column(db.String(120))
    website = db.Column(db.String(200))
    about = db.Column(db.String(150))
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)

    jobs = db.relationship("JobPosition", backref="company", lazy=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    degree = db.Column(db.String(120))
    branch = db.Column(db.String(120))
    year = db.Column(db.String(50))
    contact = db.Column(db.String(20))
    cgpa = db.Column(db.Float)
    skills = db.Column(db.String(200))
    experience = db.Column(db.String(30))
    resume_link = db.Column(db.String(200))
    is_blocked = db.Column(db.Boolean, default=False)

    applications = db.relationship("Application", backref="student", lazy=True)


class JobPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    salary = db.Column(db.Float)
    location = db.Column(db.String(120))
    skills_required = db.Column(db.String(200))
    experience_required = db.Column(db.String(120))
    eligible_branch = db.Column(db.String(120))
    min_cgpa = db.Column(db.Float)
    eligible_year = db.Column(db.String(50))
    application_deadline = db.Column(db.DateTime)
    is_approved = db.Column(db.Boolean, default=False)
    is_rejected = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship("Application", backref="job", lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job_position.id"), nullable=False)
    status = db.Column(db.String(20), default="Applied")
    feedback = db.Column(db.String(500))
    interview_datetime = db.Column(db.DateTime)
    joining_date = db.Column(db.DateTime)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    placement = db.relationship("Placement", backref="application", uselist=False)


class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job_position.id"), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    position = db.Column(db.String(120))
    package = db.Column(db.Float)
    joining_date = db.Column(db.DateTime)
    placed_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExportJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")
    file_path = db.Column(db.String(300))
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
