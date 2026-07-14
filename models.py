"""
Astro Report Store — database models.

Kept fully separate from the observatory models (distinct table names,
`store_` prefix) so nothing in the existing platform is touched.
"""
import json
import uuid as uuid_lib
from datetime import datetime

from database import db


def _new_uuid() -> str:
    return uuid_lib.uuid4().hex


class Purchase(db.Model):
    """One row per report purchase attempt (created → paid / failed)."""
    __tablename__ = 'store_purchases'

    id        = db.Column(db.Integer, primary_key=True)
    uuid      = db.Column(db.String(32), unique=True, nullable=False,
                          index=True, default=_new_uuid)
    # This standalone storefront deliberately has no accounts table.  A report
    # is owned through the signed browser session after payment.
    user_id   = db.Column(db.Integer, nullable=True)

    # Birth details (what the chart was built from)
    name        = db.Column(db.String(120), default='')
    email       = db.Column(db.String(255), nullable=True, index=True)
    mobile      = db.Column(db.String(20), nullable=True)
    birth_place = db.Column(db.String(200), default='')
    year        = db.Column(db.Integer, nullable=False)
    month       = db.Column(db.Integer, nullable=False)
    day         = db.Column(db.Integer, nullable=False)
    hour        = db.Column(db.Integer, nullable=False)
    minute      = db.Column(db.Integer, nullable=False)
    lat         = db.Column(db.Float, nullable=False)
    lon         = db.Column(db.Float, nullable=False)
    timezone    = db.Column(db.Float, default=5.5)
    language    = db.Column(db.String(8), default='en')  # report output language

    # Money — price is locked server-side at order creation time
    price_paid  = db.Column(db.Integer, nullable=True)          # INR, whole rupees
    currency    = db.Column(db.String(8), default='INR')
    status      = db.Column(db.String(24), default='created',
                            index=True)  # created | paid | failed

    razorpay_order_id   = db.Column(db.String(64), nullable=True, index=True)
    razorpay_payment_id = db.Column(db.String(64), nullable=True)
    razorpay_signature  = db.Column(db.String(160), nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    paid_at     = db.Column(db.DateTime, nullable=True)

    report = db.relationship('Report', backref='purchase', uselist=False, lazy=True)

    @staticmethod
    def total_paid() -> int:
        return Purchase.query.filter_by(status='paid').count()


class Report(db.Model):
    """The generated report — chart JSON + AI JSON, cached forever."""
    __tablename__ = 'store_reports'

    id           = db.Column(db.Integer, primary_key=True)
    uuid         = db.Column(db.String(32), unique=True, nullable=False,
                             index=True, default=_new_uuid)
    purchase_id  = db.Column(db.Integer, db.ForeignKey('store_purchases.id'),
                             nullable=False)
    chart_json   = db.Column(db.Text, nullable=False)   # compact-encoded engine output
    ai_json      = db.Column(db.Text, nullable=True)    # Claude Haiku sections (cached)
    generated_at = db.Column(db.DateTime, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def chart(self) -> dict:
        return json.loads(self.chart_json)

    def ai(self) -> dict | None:
        return json.loads(self.ai_json) if self.ai_json else None


class PaymentEvent(db.Model):
    """Audit log of every payment lifecycle event."""
    __tablename__ = 'store_payment_events'

    id          = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('store_purchases.id'),
                            nullable=False, index=True)
    event       = db.Column(db.String(40), nullable=False)
    # order_created | payment_verified | signature_mismatch | dev_simulated | cancelled
    detail      = db.Column(db.Text, default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


class PricingHistory(db.Model):
    """One row every time the live price tier changes."""
    __tablename__ = 'store_pricing_history'

    id                = db.Column(db.Integer, primary_key=True)
    price             = db.Column(db.Integer, nullable=False)
    total_reports_at  = db.Column(db.Integer, nullable=False)
    changed_at        = db.Column(db.DateTime, default=datetime.utcnow)
