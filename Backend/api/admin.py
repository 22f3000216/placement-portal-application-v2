from flask import Blueprint, jsonify, request
from extensions import db, cache
from models import Company, JobPosition, Placement, Student, Application, User
from tasks import generate_monthly_report
from api.auth_utils import role_required

admin_bp = Blueprint("admin", __name__)



@admin_bp.route("/stats", methods=["GET"])
@role_required("admin")
@cache.cached(timeout=30, key_prefix="admin_stats")
def get_stats():
    return jsonify({
        "total_students": Student.query.count(),
        "total_companies": Company.query.count(),
        "total_jobs": JobPosition.query.count(),
        "total_applications": Application.query.count()
    }), 200



@admin_bp.route("/companies", methods=["GET"])
@role_required("admin")
@cache.cached(timeout=30, key_prefix="admin_companies_search", query_string=True)
def get_companies():

    query = request.args.get("q", "").strip()
    companies_query = Company.query
    if query:
        companies_query = companies_query.filter(
            (Company.name.ilike(f"%{query}%")) | (Company.industry.ilike(f"%{query}%"))
        )
    companies = companies_query.all()

    result = []
    for c in companies:
        result.append({
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "location": c.location,
            "is_approved": c.is_approved,
            "is_rejected": c.is_rejected,
            "is_blocked": c.is_blocked
        })
    return jsonify(result), 200


@admin_bp.route("/companies/<int:company_id>/approve", methods=["PUT"])
@role_required("admin")
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_approved = True
    company.is_rejected = False
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Company approved"}), 200


@admin_bp.route("/companies/<int:company_id>/reject", methods=["PUT"])
@role_required("admin")
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_approved = False
    company.is_rejected = True
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Company registration rejected"}), 200


@admin_bp.route("/companies/<int:company_id>/block", methods=["PUT"])
@role_required("admin")
def block_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_blocked = True
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Company blocked"}), 200


@admin_bp.route("/companies/<int:company_id>/unblock", methods=["PUT"])
@role_required("admin")
def unblock_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_blocked = False
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Company unblocked"}), 200


@admin_bp.route("/companies/<int:company_id>", methods=["DELETE"])
@role_required("admin")
def remove_company(company_id):
    company = Company.query.get_or_404(company_id)

    jobs = JobPosition.query.filter_by(company_id=company.id).all()
    for job in jobs:
        Application.query.filter_by(job_id=job.id).delete()
        db.session.delete(job)
    db.session.delete(company)
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Company removed"}), 200



@admin_bp.route("/students", methods=["GET"])
@role_required("admin")
@cache.cached(timeout=30, key_prefix="admin_students_search", query_string=True)
def get_students():

    query = request.args.get("q", "").strip()
    students_query = Student.query
    if query:
        if query.isdigit():
            students_query = students_query.filter(
                (Student.id == int(query)) | (Student.contact.ilike(f"%{query}%"))
            )
        else:
            students_query = students_query.filter(
                (Student.name.ilike(f"%{query}%")) | (Student.contact.ilike(f"%{query}%"))
            )
    students = students_query.all()

    result = []
    for s in students:
        result.append({
            "id": s.id,
            "name": s.name,
            "contact": s.contact,
            "degree": s.degree,
            "branch": s.branch,
            "cgpa": s.cgpa,
            "skills": s.skills,
            "experience": s.experience,
            "resume_link": s.resume_link,
            "is_blocked": s.is_blocked
        })
    return jsonify(result), 200


@admin_bp.route("/students/<int:student_id>/block", methods=["PUT"])
@role_required("admin")
def block_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blocked = True
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Student blocked"}), 200


@admin_bp.route("/students/<int:student_id>/unblock", methods=["PUT"])
@role_required("admin")
def unblock_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blocked = False
    db.session.commit()
    _clear_search_caches()
    return jsonify({"message": "Student unblocked"}), 200



@admin_bp.route("/jobs/pending", methods=["GET"])
@role_required("admin")
def get_pending_jobs():
    jobs = JobPosition.query.filter_by(is_approved=False, is_rejected=False).all()
    result = []
    for j in jobs:
        result.append({"id": j.id, "title": j.title, "company_name": j.company.name})
    return jsonify(result), 200


@admin_bp.route("/jobs", methods=["GET"])
@role_required("admin")
@cache.cached(timeout=30, key_prefix="admin_jobs_search", query_string=True)
def get_all_jobs():

    query = request.args.get("q", "").strip()
    jobs_query = JobPosition.query
    if query:
        jobs_query = jobs_query.join(Company).filter(
            (JobPosition.title.ilike(f"%{query}%")) | (Company.name.ilike(f"%{query}%"))
        )
    jobs = jobs_query.all()

    result = []
    for j in jobs:
        result.append({
            "id": j.id,
            "title": j.title,
            "company_name": j.company.name,
            "is_approved": j.is_approved,
            "is_rejected": j.is_rejected,
            "status": j.status,
            "application_count": len(j.applications)
        })
    return jsonify(result), 200


@admin_bp.route("/jobs/<int:job_id>/approve", methods=["PUT"])
@role_required("admin")
def approve_job(job_id):
    job = JobPosition.query.get_or_404(job_id)
    job.is_approved = True
    job.is_rejected = False
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Job approved"}), 200


@admin_bp.route("/jobs/<int:job_id>/reject", methods=["PUT"])
@role_required("admin")
def reject_job(job_id):
    job = JobPosition.query.get_or_404(job_id)
    job.is_approved = False
    job.is_rejected = True
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Placement drive rejected"}), 200


@admin_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
@role_required("admin")
def remove_job(job_id):
    job = JobPosition.query.get_or_404(job_id)
    Application.query.filter_by(job_id=job.id).delete()
    db.session.delete(job)
    db.session.commit()
    cache.clear()
    return jsonify({"message": "Job removed"}), 200



@admin_bp.route("/applications", methods=["GET"])
@role_required("admin")
def get_all_applications():
    applications = Application.query.all()
    result = []
    for a in applications:
        result.append({
            "id": a.id,
            "student_name": a.student.name,
            "job_title": a.job.title,
            "company_name": a.job.company.name,
            "status": a.status
        })
    return jsonify(result), 200


@admin_bp.route("/applications/<int:application_id>", methods=["DELETE"])
@role_required("admin")
def remove_application(application_id):
    application = Application.query.get_or_404(application_id)
    db.session.delete(application)
    db.session.commit()
    return jsonify({"message": "Application removed"}), 200



@admin_bp.route("/placements", methods=["GET"])
@role_required("admin")
def get_placements():
    placements = Placement.query.all()
    result = []
    for p in placements:
        result.append({
            "student_name": p.student_id and Student.query.get(p.student_id).name,
            "company_name": p.company_id and Company.query.get(p.company_id).name,
            "position": p.position,
            "package": p.package
        })
    return jsonify(result), 200


@admin_bp.route("/reports/generate", methods=["POST"])
@role_required("admin")
def trigger_report():
    generate_monthly_report.delay()
    return jsonify({"message": "Report generation started"}), 202


@admin_bp.route("/reports", methods=["GET"])
@role_required("admin")
def list_reports():
    import os
    folder = "generated_files"
    if not os.path.exists(folder):
        return jsonify([]), 200
    files = [f for f in os.listdir(folder) if f.startswith("report_")]
    files.sort(reverse=True)
    return jsonify(files), 200


@admin_bp.route("/reports/<filename>", methods=["GET"])
@role_required("admin")
def view_report(filename):
    import os
    from flask import Response
    folder = "generated_files"
    filepath = os.path.join(folder, filename)
    if not filename.startswith("report_") or not os.path.exists(filepath):
        return jsonify({"message": "Report not found"}), 404
    with open(filepath) as f:
        content = f.read()
    return Response(content, mimetype="text/html")


def _clear_search_caches():


    cache.clear()
