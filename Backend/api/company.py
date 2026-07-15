import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import get_jwt_identity
from extensions import db, cache
from models import Company, JobPosition, Application, Student, Placement
from api.auth_utils import role_required

company_bp = Blueprint("company", __name__)


def _get_company():
    return Company.query.filter_by(user_id=get_jwt_identity()).first()


def _check_approved(company):
    if not company.is_approved:
        return jsonify({"message": "Your company dashboard will unlock once admin approves your registration"}), 403
    if company.is_blocked:
        return jsonify({"message": "Your company has been blocked by admin"}), 403
    return None



@company_bp.route("/profile", methods=["GET"])
@role_required("company")
def get_profile():
    company = _get_company()
    return jsonify({
        "name": company.name,
        "industry": company.industry,
        "location": company.location,
        "hr_contact": company.hr_contact,
        "website": company.website,
        "about": company.about,
        "is_approved": company.is_approved,
        "is_blocked": company.is_blocked
    }), 200


@company_bp.route("/profile", methods=["PUT"])
@role_required("company")
def update_profile():
    company = _get_company()
    data = request.get_json()

    name = data.get("name", "").strip()
    if not name:
        return jsonify({"message": "Company name cannot be empty"}), 400

    company.name = name
    company.industry = data.get("industry", company.industry)
    company.location = data.get("location", company.location)
    company.hr_contact = data.get("hr_contact", company.hr_contact)
    company.website = data.get("website", company.website)
    company.about = data.get("about", company.about)
    db.session.commit()
    return jsonify({"message": "Profile updated"}), 200


@company_bp.route("/placements", methods=["GET"])
@role_required("company")
def get_company_placements():
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    placements = Placement.query.filter_by(company_id=company.id).all()
    result = []
    for p in placements:
        result.append({
            "student_name": p.application.student.name,
            "position": p.position,
            "package": p.package,
            "joining_date": p.joining_date,
            "placed_at": p.placed_at
        })
    return jsonify(result), 200


@company_bp.route("/applications/export", methods=["POST"])
@role_required("company")
def export_company_data():
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    from models import ExportJob
    export_job = ExportJob(user_id=get_jwt_identity(), status="pending")
    db.session.add(export_job)
    db.session.commit()

    from tasks import export_company_csv
    export_company_csv.delay(company.id, export_job.id)
    return jsonify({"message": "CSV export started", "export_job_id": export_job.id}), 202


@company_bp.route("/applications/export/<int:export_job_id>/status", methods=["GET"])
@role_required("company")
def check_company_export_status(export_job_id):
    from models import ExportJob
    export_job = ExportJob.query.get_or_404(export_job_id)
    return jsonify({"status": export_job.status, "file_path": export_job.file_path}), 200


@company_bp.route("/applications/export/<int:export_job_id>/download", methods=["GET"])
@role_required("company")
def download_company_export_csv(export_job_id):
    from models import ExportJob
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
        download_name=f"company_history_{export_job_id}.csv"
    )


@company_bp.route("/dashboard-summary", methods=["GET"])
@role_required("company")
def dashboard_summary():
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    job_ids = [j.id for j in JobPosition.query.filter_by(company_id=company.id).all()]
    total_jobs = len(job_ids)
    total_applications = Application.query.filter(Application.job_id.in_(job_ids)).count() if job_ids else 0

    shortlisted = Application.query.filter(
        Application.job_id.in_(job_ids),
        Application.status.in_(["Shortlisted", "Interview", "Offer", "Placed"])
    ).all() if job_ids else []

    shortlisted_list = []
    for a in shortlisted:
        shortlisted_list.append({
            "student_name": a.student.name,
            "job_title": a.job.title,
            "status": a.status
        })

    return jsonify({
        "total_job_postings": total_jobs,
        "total_applications_received": total_applications,
        "shortlisted_candidates": shortlisted_list
    }), 200



@company_bp.route("/jobs", methods=["POST"])
@role_required("company")
def create_job():
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    data = request.get_json()
    title = data.get("title", "").strip()
    salary = data.get("salary")

    if not title:
        return jsonify({"message": "Job title is required"}), 400

    if salary is not None and salary != "":
        try:
            salary = float(salary)
            if salary < 0:
                return jsonify({"message": "Salary cannot be negative"}), 400
        except ValueError:
            return jsonify({"message": "Salary must be a number"}), 400

    new_job = JobPosition(
        company_id=company.id,
        title=title,
        description=data.get("description"),
        salary=salary,
        location=data.get("location"),
        skills_required=data.get("skills_required"),
        experience_required=data.get("experience_required"),
        eligible_branch=data.get("eligible_branch"),
        min_cgpa=(float(data.get("min_cgpa")) if data.get("min_cgpa") not in (None, "") else None),
        eligible_year=data.get("eligible_year"),
        application_deadline=(datetime.fromisoformat(data.get("application_deadline"))
                               if data.get("application_deadline") else None)
    )
    db.session.add(new_job)
    db.session.commit()

    cache.delete("admin_stats")
    return jsonify({"message": "Job created, waiting for admin approval"}), 201


@company_bp.route("/jobs", methods=["GET"])
@role_required("company")
def get_my_jobs():
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    jobs = JobPosition.query.filter_by(company_id=company.id).all()

    result = []
    for j in jobs:
        result.append({
            "id": j.id,
            "title": j.title,
            "skills_required": j.skills_required,
            "experience_required": j.experience_required,
            "eligible_branch": j.eligible_branch,
            "min_cgpa": j.min_cgpa,
            "eligible_year": j.eligible_year,
            "application_deadline": j.application_deadline,
            "is_approved": j.is_approved,
            "status": j.status,
            "application_count": len(j.applications)
        })
    return jsonify(result), 200


@company_bp.route("/jobs/<int:job_id>/status", methods=["PUT"])
@role_required("company")
def update_job_status(job_id):
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    job = JobPosition.query.get_or_404(job_id)
    if job.company_id != company.id:
        return jsonify({"message": "Access denied"}), 403

    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ["Active", "Closed"]:
        return jsonify({"message": "Status must be Active or Closed"}), 400

    job.status = new_status
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Job marked as {new_status}"}), 200



@company_bp.route("/jobs/<int:job_id>/applications", methods=["GET"])
@role_required("company")
def get_applications(job_id):
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    applications = Application.query.filter_by(job_id=job_id).all()
    result = []
    for a in applications:
        result.append({
            "application_id": a.id,
            "student_name": a.student.name,
            "degree": a.student.degree,
            "branch": a.student.branch,
            "contact": a.student.contact,
            "skills": a.student.skills,
            "experience": a.student.experience,
            "resume_link": a.student.resume_link,
            "cgpa": a.student.cgpa,
            "status": a.status,
            "interview_datetime": a.interview_datetime,
            "feedback": a.feedback
        })
    return jsonify(result), 200


@company_bp.route("/applications/<int:application_id>/status", methods=["PUT"])
@role_required("company")
def update_application_status(application_id):
    company = _get_company()
    denied = _check_approved(company)
    if denied:
        return denied

    data = request.get_json()
    new_status = data.get("status")
    feedback = data.get("feedback", "")

    valid_statuses = ["Shortlisted", "Interview", "Offer", "Rejected"]
    if new_status not in valid_statuses:
        return jsonify({"message": f"Status must be one of {valid_statuses}"}), 400

    application = Application.query.get_or_404(application_id)
    if application.job.company_id != company.id:
        return jsonify({"message": "Access denied"}), 403
    if application.status == "Placed":
        return jsonify({
            "message": "Placed application cannot be modified"
        }), 400
    application.status = new_status
    if feedback:
        application.feedback = feedback


    if new_status == "Interview":
        interview_datetime = data.get("interview_datetime")
        if not interview_datetime:
            return jsonify({"message": "interview_datetime is required for Interview status"}), 400
        application.interview_datetime = datetime.fromisoformat(interview_datetime)


    if new_status == "Offer":
        joining_date = data.get("joining_date")
        if not joining_date:
            return jsonify({
                "message": "Joining date is required"
            }), 400
        if joining_date:
            application.joining_date = datetime.fromisoformat(joining_date)

    db.session.commit()
    return jsonify({"message": "Application status updated"}), 200
