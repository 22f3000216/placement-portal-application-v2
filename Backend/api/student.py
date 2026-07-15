import os
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, send_file, current_app
from flask_jwt_extended import get_jwt_identity
from extensions import db, cache
from models import JobPosition, Application, Student, Company, Placement, ExportJob
from tasks import export_applications_csv
from api.auth_utils import role_required
from werkzeug.utils import secure_filename

student_bp = Blueprint("student", __name__)


def _get_student():
    return Student.query.filter_by(user_id=get_jwt_identity()).first()


def _check_eligibility(student, job):
    if job.eligible_branch:
        allowed_branches = [b.strip().lower() for b in job.eligible_branch.split(",")]
        if not student.branch or student.branch.strip().lower() not in allowed_branches:
            return False, f"This drive is only open to students from: {job.eligible_branch}"

    if job.min_cgpa is not None:
        if student.cgpa is None:
            return False, "Please update your CGPA in your profile before applying"
        if student.cgpa < job.min_cgpa:
            return False, f"This drive requires a minimum CGPA of {job.min_cgpa}"

    if job.eligible_year:
        if not student.year or student.year.strip().lower() != job.eligible_year.strip().lower():
            return False, f"This drive is only open to: {job.eligible_year}"

    if job.application_deadline and datetime.utcnow() > job.application_deadline:
        return False, "The application deadline for this drive has passed"

    return True, None



@student_bp.route("/profile", methods=["GET"])
@role_required("student")
def get_profile():
    student = _get_student()
    return jsonify({
        "name": student.name,
        "degree": student.degree,
        "branch": student.branch,
        "year": student.year,
        "contact": student.contact,
        "cgpa": student.cgpa,
        "skills": student.skills,
        "experience": student.experience,
        "resume_link": student.resume_link
    }), 200


@student_bp.route("/profile", methods=["PUT"])
@role_required("student")
def update_profile():
    student = _get_student()
    data = request.get_json()

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"message": "Name cannot be empty"}), 400

    cgpa = data.get("cgpa")
    if cgpa is not None and cgpa != "":
        try:
            cgpa = float(cgpa)
            if cgpa < 0 or cgpa > 10:
                return jsonify({"message": "CGPA must be between 0 and 10"}), 400
        except ValueError:
            return jsonify({"message": "CGPA must be a number"}), 400
        student.cgpa = cgpa

    student.name = name
    student.degree = data.get("degree", student.degree)
    student.branch = data.get("branch", student.branch)
    student.year = data.get("year", student.year)
    student.contact = data.get("contact", student.contact)
    student.skills = data.get("skills", student.skills)
    student.experience = data.get("experience", student.experience)
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200

@student_bp.route("/resume/upload", methods=["POST"])
@role_required("student")
def upload_resume():
    student = _get_student()

    if "resume" not in request.files:
        return jsonify({"message": "Please select a PDF file"}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"message": "Please select a PDF file"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"message": "Only PDF files are allowed"}), 400

    filename = secure_filename(f"resume_student_{student.id}.pdf")

    file.save(
        os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    )

    student.resume_link = f"http://localhost:5000/uploads/{filename}"
    db.session.commit()

    return jsonify({
        "message": "Resume uploaded successfully"
    }), 200

def _student_jobs_cache_key():
    return f"student_jobs_{get_jwt_identity()}_{request.query_string.decode()}"


@student_bp.route("/jobs", methods=["GET"])
@role_required("student")
@cache.cached(timeout=30, key_prefix=_student_jobs_cache_key)
def get_open_jobs():


    query = request.args.get("q", "").strip()
    eligible_only = request.args.get("eligible_only", "").lower() == "true"
    student = _get_student()

    jobs_query = JobPosition.query.filter_by(is_approved=True, status="Active")
    if query:
        jobs_query = jobs_query.join(Company).filter(
            (JobPosition.title.ilike(f"%{query}%")) |
            (JobPosition.skills_required.ilike(f"%{query}%")) |
            (Company.name.ilike(f"%{query}%"))
        )
    jobs = jobs_query.all()

    result = []
    for j in jobs:
        is_eligible, reason = _check_eligibility(student, j)
        if eligible_only and not is_eligible:
            continue
        result.append({
            "id": j.id,
            "title": j.title,
            "company_name": j.company.name,
            "salary": j.salary,
            "location": j.location,
            "skills_required": j.skills_required,
            "experience_required": j.experience_required,
            "eligible_branch": j.eligible_branch,
            "min_cgpa": j.min_cgpa,
            "eligible_year": j.eligible_year,
            "application_deadline": j.application_deadline,
            "is_eligible": is_eligible,
            "eligibility_reason": reason
        })
    return jsonify(result), 200


@student_bp.route("/jobs/<int:job_id>/apply", methods=["POST"])
@role_required("student")
def apply_job(job_id):
    student = _get_student()
    if not student.resume_link or not student.resume_link.strip():
        return jsonify({
            "message": "Please add your resume link before applying."
        }), 400
    
    placed = Placement.query.filter_by(
        student_id=student.id
    ).first()

    if placed:
        return jsonify({
            "message": "You are already placed and cannot apply for new jobs."
        }), 400

    job = JobPosition.query.get_or_404(job_id)
    if not job.is_approved or job.status != "Active":
        return jsonify({"message": "This job is not open for applications"}), 400

    is_eligible, reason = _check_eligibility(student, job)
    if not is_eligible:
        return jsonify({"message": reason}), 400

    already_applied = Application.query.filter_by(
        student_id=student.id, job_id=job_id
    ).first()
    if already_applied:
        return jsonify({"message": "You already applied to this job"}), 400

    new_application = Application(student_id=student.id, job_id=job_id)
    db.session.add(new_application)
    db.session.commit()

    cache.delete("admin_stats")
    return jsonify({"message": "Applied successfully"}), 201



@student_bp.route("/applications", methods=["GET"])
@role_required("student")
def get_my_applications():
    student = _get_student()
    applications = Application.query.filter_by(student_id=student.id).all()

    result = []
    for a in applications:
        result.append({
            "id": a.id,
            "job_title": a.job.title,
            "company_name": a.job.company.name,
            "status": a.status,
            "interview_datetime": a.interview_datetime,
            "feedback": a.feedback,
            "applied_at": a.applied_at
        })
    return jsonify(result), 200


@student_bp.route("/applications/<int:application_id>/accept-offer", methods=["POST"])
@role_required("student")
def accept_offer(application_id):
    student = _get_student()
    application = Application.query.get_or_404(application_id)

    if application.student_id != student.id:
        return jsonify({"message": "Access denied"}), 403
    if application.status != "Offer":
        return jsonify({"message": "No pending offer for this application"}), 400

    existing = Placement.query.filter_by(
        application_id=application.id
    ).first()

    if existing:
        return jsonify({
            "message": "Placement already exists"
        }), 400
    
    application.status = "Placed"

    placement = Placement(
        student_id=application.student_id,
        company_id=application.job.company_id,
        job_id=application.job_id,
        application_id=application.id,
        position=application.job.title,
        package=application.job.salary,
        joining_date=application.joining_date
    )
    db.session.add(placement)
    db.session.commit()
    return jsonify({"message": "Offer accepted, congratulations!"}), 200


@student_bp.route("/applications/<int:application_id>/decline-offer", methods=["POST"])
@role_required("student")
def decline_offer(application_id):
    student = _get_student()
    application = Application.query.get_or_404(application_id)

    if application.student_id != student.id:
        return jsonify({"message": "Access denied"}), 403
    if application.status != "Offer":
        return jsonify({"message": "No pending offer for this application"}), 400

    application.status = "Rejected"
    db.session.commit()
    return jsonify({"message": "Offer declined"}), 200



@student_bp.route("/placement/offer-letter", methods=["GET"])
@role_required("student")
def download_offer_letter():
    student = _get_student()
    placement = Placement.query.filter_by(student_id=student.id).first()

    if not placement:
        return jsonify({"message": "No placement record found yet"}), 404

    company = Company.query.get(placement.company_id)

    letter_text = f"""PLACEMENT OFFER LETTER

Dear {student.name},

Congratulations! You have been placed at {company.name}
for the position of {placement.position}.

Package: {placement.package}
Joining Date: {placement.joining_date.strftime('%d-%m-%Y') if placement.joining_date else 'To be communicated'}
Date of Offer: {placement.placed_at.strftime('%d-%m-%Y')}

This is a system-generated placement confirmation.
"""
    return Response(
        letter_text,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=offer_letter.txt"}
    )



@student_bp.route("/applications/export", methods=["POST"])
@role_required("student")
def export_applications():
    student = _get_student()

    export_job = ExportJob(user_id=get_jwt_identity(), status="pending")
    db.session.add(export_job)
    db.session.commit()

    export_applications_csv.delay(student.id, export_job.id)
    return jsonify({"message": "CSV export started", "export_job_id": export_job.id}), 202


@student_bp.route("/applications/export/<int:export_job_id>/status", methods=["GET"])
@role_required("student")
def check_export_status(export_job_id):
    export_job = ExportJob.query.get_or_404(export_job_id)
    return jsonify({"status": export_job.status, "file_path": export_job.file_path}), 200


@student_bp.route("/applications/export/<int:export_job_id>/download", methods=["GET"])
@role_required("student")
def download_export_csv(export_job_id):
    export_job = ExportJob.query.get_or_404(export_job_id)

    if str(export_job.user_id) != str(get_jwt_identity()):
        return jsonify({"message": "Access denied"}), 403

    if export_job.status != "ready" or not export_job.file_path:
        return jsonify({"message": "Export is not ready yet"}), 400

    if not os.path.exists(export_job.file_path):
        return jsonify({"message": "Export file not found on server"}), 404

    return send_file(
        os.path.abspath(export_job.file_path),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"my_applications_{export_job_id}.csv"
    )
