import re
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db, cache
from models import User, Student, Company

auth_bp = Blueprint("auth", __name__)

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "")
    name = data.get("name", "").strip()

    if not email or not password or not role or not name:
        return jsonify({"message": "All fields are required"}), 400

    if not re.match(EMAIL_PATTERN, email):
        return jsonify({"message": "Please enter a valid email address"}), 400

    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400

    if role not in ["student", "company"]:
        return jsonify({"message": "Role must be student or company"}), 400

    if role == "student":
        cgpa = data.get("cgpa")
        if cgpa is not None and cgpa != "":
            try:
                cgpa = float(cgpa)
            except ValueError:
                return jsonify({"message": "CGPA must be a number"}), 400
            if cgpa < 0 or cgpa > 10:
                return jsonify({"message": "CGPA must be between 0 and 10"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()

    if role == "student":
        student = Student(
            user_id=new_user.id,
            name=name,
            degree=data.get("degree"),
            branch=data.get("branch"),
            year=data.get("year"),
            contact=data.get("contact"),
            cgpa=data.get("cgpa") or None,
            skills=data.get("skills"),
            experience=data.get("experience")
        )
        db.session.add(student)

    if role == "company":
        company = Company(
            user_id=new_user.id,
            name=name,
            industry=data.get("industry"),
            location=data.get("location"),
            hr_contact=data.get("hr_contact"),
            website=data.get("website"),
            about=data.get("about")
        )
        db.session.add(company)

    db.session.commit()

    cache.delete("admin_stats")
    cache.clear()

    return jsonify({"message": "Registered successfully"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid email or password"}), 401

    if user.role == "student":
        student = Student.query.filter_by(user_id=user.id).first()
        if student and student.is_blocked:
            return jsonify({"message": "Your account has been blocked by admin"}), 403

    if user.role == "company":
        company = Company.query.filter_by(user_id=user.id).first()
        if company and company.is_blocked:
            return jsonify({"message": "Your account has been blocked by admin"}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"access_token": token, "role": user.role}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    from flask_jwt_extended import get_jwt
    user_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify({"user_id": user_id, "role": claims.get("role")}), 200
