"""Standalone Astro Report Store application for Render."""
import os
from datetime import timedelta

from flask import Flask, redirect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from database import db
from routes import store_bp


def create_app():
    app = Flask(__name__)
    # Render terminates HTTPS before forwarding the request to Gunicorn.
    # Trust its forwarded scheme/host when generating report links in emails.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    production = os.getenv("FLASK_ENV", "development").lower() == "production"
    secret = os.getenv("SECRET_KEY")
    if production and not secret:
        raise RuntimeError("SECRET_KEY must be set in production")
    app.config.update(
        SECRET_KEY=secret or "local-development-only",
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///astro_report.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        DEBUG=not production,
    )
    CORS(app, resources={r"/store/api/*": {"origins": os.getenv("ALLOWED_ORIGINS", "*").split(",")}})
    db.init_app(app)
    app.register_blueprint(store_bp)

    @app.get("/")
    def index():
        return redirect("/store/")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    with app.app_context():
        db.create_all()
    return app


app = create_app()
