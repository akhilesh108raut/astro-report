"""
Astro Report Store — a self-contained storefront blueprint.

Mounts at /store. Shares the Flask app + SQLAlchemy instance but owns its
templates, static assets, models, pricing and payment flow. Nothing in the
3D Transit Observatory is imported or modified.
"""
import os

from . import models          # noqa: F401 — register tables with SQLAlchemy
from .routes import store_bp


@store_bp.record_once
def _create_tables(state):
    """Ensure store tables exist even if init_db ran before this import."""
    from database import db
    with state.app.app_context():
        db.create_all()


@store_bp.app_template_global()
def asset_version():
    """Cache-busting token for report_v2.css — changes only when the file
    itself changes (mtime), so browsers still cache it between edits."""
    css_path = os.path.join(os.path.dirname(__file__), "static", "css", "report_v2.css")
    try:
        return int(os.path.getmtime(css_path))
    except OSError:
        return 0


__all__ = ["store_bp"]
