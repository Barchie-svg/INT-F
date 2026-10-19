import os
import time
import threading
import requests
from datetime import datetime

from sql_queries import get_system_settings

# ─────────────────────────────────────────────
#  Config cache — avoids hitting DB on every email
# ─────────────────────────────────────────────
_CONFIG_CACHE = None
_CONFIG_CACHE_TIME = 0

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def clear_config_cache():
    """Clear cached settings so next send re-fetches from DB."""
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME
    _CONFIG_CACHE = None
    _CONFIG_CACHE_TIME = 0


def _get_config():
    """
    Resolve email config with in-memory caching (5 min TTL).

    Priority:
      1. Environment variables  (set these on Render)
      2. Supabase system_settings table  (set via Admin Dashboard)

    Returns: (brevo_api_key, sender_email, admin_email)
    """
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME
    now = time.time()
    if _CONFIG_CACHE and (now - _CONFIG_CACHE_TIME) < 300:
        return _CONFIG_CACHE

    settings = get_system_settings()

    # BREVO_API_KEY: env var takes priority; fall back to sender_password DB column
    # (so existing DB-stored values still work without a migration)
    brevo_api_key = (
        os.environ.get("BREVO_API_KEY")
        or settings.get("sender_password", "")
    )
    sender_email = (
        os.environ.get("SENDER_EMAIL")
        or settings.get("sender_email", "")
    )
    admin_email = (
        os.environ.get("ADMIN_EMAIL")
        or settings.get("admin_email", "")
    )

    _CONFIG_CACHE = (brevo_api_key, sender_email, admin_email)
    _CONFIG_CACHE_TIME = now
    return _CONFIG_CACHE


# ─────────────────────────────────────────────
#  HTML email template (unchanged look)
# ─────────────────────────────────────────────
def _build_html(message: str) -> str:
    formatted = message.replace('\n', '<br>')
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6fa; margin: 0; padding: 24px; }}
  .box {{ max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.05); }}
  .top {{ background: #4f6ef7; color: #ffffff; padding: 20px 24px; text-align: left; }}
  .top h2 {{ margin: 0; font-size: 18px; font-weight: 700; }}
  .main {{ padding: 28px 24px; color: #1e293b; line-height: 1.6; font-size: 15px; }}
  .foot {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 14px 24px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="box">
  <div class="top">
    <h2>Tech Africa IT Portal</h2>
  </div>
  <div class="main">
    {formatted}
  </div>
  <div class="foot">
    Tech Africa IT Secure Access System &bull; Automated Notification
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────
#  Core send function — Brevo REST API over HTTPS
# ─────────────────────────────────────────────
def send_alert(message: str, subject: str = None, to_email: str = None) -> bool:
    """
    Send an email via the Brevo Transactional Email API (HTTPS/port 443).
    This replaces the previous SMTP approach which is blocked on Render.

    Returns True on success, False on any failure.
    """
    brevo_api_key, sender_email, admin_email = _get_config()
    recipient     = to_email or admin_email
    email_subject = subject or "Security Alert — Tech Africa IT Secure Access System"

    # ── Validate config ────────────────────────────────────────────────
    if not brevo_api_key:
        print("[EMAIL ERROR] BREVO_API_KEY is not set. "
              "Add it in Render → Environment variables.", flush=True)
        return False

    if not sender_email:
        print("[EMAIL ERROR] SENDER_EMAIL is not set.", flush=True)
        return False

    if not recipient:
        print("[EMAIL ERROR] No recipient email configured. "
              "Set ADMIN_EMAIL env var or update System Settings in the Admin Dashboard.", flush=True)
        return False

    # ── Build payload ──────────────────────────────────────────────────
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text_body = (
        f"Tech Africa IT Secure Access System\n"
        f"Date: {now}\n\n"
        f"{message}\n\n"
        f"--\nTech Africa IT Security & Support Team"
    )

    payload = {
        "sender":      {"name": "Tech Africa IT Support", "email": sender_email},
        "to":          [{"email": recipient}],
        "subject":     email_subject,
        "textContent": text_body,
        "htmlContent": _build_html(message),
    }

    headers = {
        "accept":       "application/json",
        "content-type": "application/json",
        "api-key":      brevo_api_key,
    }

    print(f"[EMAIL DEBUG] Sending via Brevo API to: {recipient} | Subject: {email_subject}", flush=True)

    # ── Call Brevo API ─────────────────────────────────────────────────
    try:
        response = requests.post(
            BREVO_API_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )

        if response.status_code in (200, 201):
            print(f"[EMAIL SUCCESS] Sent to {recipient} | "
                  f"Brevo messageId: {response.json().get('messageId', 'n/a')}", flush=True)
            return True
        else:
            print(f"[EMAIL ERROR] Brevo API returned {response.status_code}: {response.text}", flush=True)
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"[EMAIL ERROR] Network error calling Brevo API: {e}", flush=True)
        return False
    except requests.exceptions.Timeout:
        print("[EMAIL ERROR] Brevo API request timed out.", flush=True)
        return False
    except Exception as e:
        print(f"[EMAIL ERROR] Unexpected error: {e}", flush=True)
        return False


# ─────────────────────────────────────────────
#  Async wrapper — fire-and-forget (preserves existing behaviour)
# ─────────────────────────────────────────────
def send_alert_async(message: str, subject: str = None, to_email: str = None):
    """
    Non-blocking email send — runs in a background thread so HTTP
    responses are instant even if the API call takes a second or two.
    """
    t = threading.Thread(target=send_alert, args=(message, subject, to_email), daemon=True)
    t.start()
    return t


# ─────────────────────────────────────────────
#  Convenience wrapper — intrusion alerts to admin
# ─────────────────────────────────────────────
def send_intrusion_alert(username: str, reason: str, ip_address: str = None):
    """Send a security/intrusion alert to the configured admin email."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "INTRUSION / SECURITY EVENT DETECTED",
        "",
        f"Employee : {username}",
        f"Reason   : {reason}",
        f"Time     : {now}",
    ]
    if ip_address:
        lines.append(f"IP Addr  : {ip_address}")
    lines.append("")
    lines.append("Action taken: Account has been LOCKED automatically.")
    lines.append("Please review the intrusion log in the admin dashboard.")

    send_alert(
        message="\n".join(lines),
        subject=f"Security Alert: Account Locked - {username}"
    )
