"""
Razorpay integration for the Astro Report Store.

- Orders are created server-side with a server-computed price.
- Signatures are verified with HMAC-SHA256 — the frontend is never trusted.
- If Razorpay keys are absent AND the app is in debug mode, a clearly-flagged
  DEV MODE lets local testing proceed with a simulated payment.
"""
import os
import hmac
import hashlib
import base64

import requests

RAZORPAY_API = "https://api.razorpay.com/v1"


def get_keys():
    return os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET")


def razorpay_configured() -> bool:
    key_id, key_secret = get_keys()
    return bool(key_id and key_secret)


def create_order(amount_inr: int, receipt: str) -> dict:
    """
    Create a Razorpay order. Amount is in whole rupees; Razorpay wants paise.
    Raises RuntimeError with a readable message on failure.
    """
    key_id, key_secret = get_keys()
    if not (key_id and key_secret):
        raise RuntimeError("Razorpay keys not configured")

    auth = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    resp = requests.post(
        f"{RAZORPAY_API}/orders",
        json={
            "amount": int(amount_inr) * 100,   # paise
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        },
        headers={"Authorization": f"Basic {auth}"},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Razorpay order creation failed ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Razorpay checkout signature verification:
    HMAC_SHA256(order_id + '|' + payment_id, key_secret) must equal signature.
    """
    _, key_secret = get_keys()
    if not key_secret:
        return False
    expected = hmac.new(
        key_secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Verify Razorpay's webhook HMAC before accepting a payment event."""
    _, key_secret = get_keys()
    if not key_secret:
        return False
    expected = hmac.new(key_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
