from flask import Flask, send_from_directory
import os
from config import Config
from extensions import db, jwt, cors, cache

from api.auth import auth_bp
from api.admin import admin_bp
from api.company import company_bp
from api.student import student_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    cors.init_app(app, origins=["http://localhost:8080"])

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(student_bp, url_prefix="/api/student")

    with app.app_context():
        db.create_all()

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
