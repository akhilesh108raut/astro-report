"""Transactional delivery emails via Resend."""
import html
import logging
import os

import requests

log = logging.getLogger("store.mailer")


def send_report_link(recipient: str, name: str, report_url: str) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("REPORT_FROM_EMAIL")
    if not api_key or not sender or not recipient:
        log.warning("Report email skipped: Resend or recipient is not configured")
        return False

    safe_name = html.escape(name or "there")
    safe_url = html.escape(report_url, quote=True)
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "astro-report-store/1.0",
        },
        json={
            "from": sender,
            "to": [recipient],
            "subject": "Your Astro Report is ready",
            "html": (
                f"<p>Hello {safe_name},</p>"
                "<p>Your personalised Vedic astrology report is ready.</p>"
                f'<p><a href="{safe_url}">Open your report</a></p>'
                "<p>Keep this link private.</p>"
            ),
        },
        timeout=15,
    )
    if response.ok:
        return True
    log.error("Resend delivery failed (%s): %s", response.status_code, response.text[:300])
    return False
