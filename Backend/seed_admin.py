from app import app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

ADMIN_EMAIL = "admin@ppa.com"
ADMIN_PASSWORD = "admin123"

with app.app_context():
    db.create_all()

    existing_admin = User.query.filter_by(email=ADMIN_EMAIL).first()
    if existing_admin:
        print(f"Admin already exists: {ADMIN_EMAIL}")
    else:
        admin = User(
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created successfully: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
