import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid, formataddr
from datetime import datetime

import time
import threading

from sql_queries import get_setting, get_system_settings

_CONFIG_CACHE = None
_CONFIG_CACHE_TIME = 0


def clear_config_cache():
    """Clear cached settings so next send re-fetches from DB."""
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME
    _CONFIG_CACHE = None
    _CONFIG_CACHE_TIME = 0


def _get_config():
    """Resolve email config with in-memory caching to prevent multi-second DB latency."""
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME
    now = time.time()
    if _CONFIG_CACHE and (now - _CONFIG_CACHE_TIME) < 300:
        return _CONFIG_CACHE

    settings = get_system_settings()
    sender_email    = os.environ.get("SENDER_EMAIL")   or settings.get("sender_email",   "")
    sender_password = os.environ.get("SENDER_PASSWORD") or settings.get("sender_password", "")
    admin_email     = os.environ.get("ADMIN_EMAIL")    or settings.get("admin_email",    "")
    _CONFIG_CACHE = (sender_email, sender_password, admin_email)
    _CONFIG_CACHE_TIME = now
    return _CONFIG_CACHE


def send_alert_async(message: str, subject: str = None, to_email: str = None):
    """
    Fire-and-forget background email sender.
    Does not block HTTP requests, responding immediately to the user.
    """
    t = threading.Thread(target=send_alert, args=(message, subject, to_email), daemon=True)
    t.start()
    return t


def send_alert(message: str, subject: str = None, to_email: str = None) -> bool:
    """
    Send an email alert via Gmail SMTP with proper headers and multipart HTML.
    Uses the sender_email + sender_password (Gmail App Password) from DB/env.
    Returns True if successful, False otherwise.
    """
    sender_email, sender_password, admin_email = _get_config()
    recipient     = to_email or admin_email
    email_subject = subject or "Security Alert — Tech Africa IT Secure Access System"

    if not sender_email or not sender_password:
        print("[EMAIL ERROR] sender_email or sender_password is not configured.", flush=True)
        return False

    if not recipient:
        print("[EMAIL ERROR] No recipient email configured.", flush=True)
        return False

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Clean plain-text body
    text_body = (
        f"Tech Africa IT Secure Access System\n"
        f"Date: {now}\n\n"
        f"{message}\n\n"
        f"--\nTech Africa IT Security & Support Team"
    )

    print(f"[EMAIL DEBUG] Sending to {recipient} via Gmail SMTP...", flush=True)

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr(("Tech Africa IT Support", sender_email))
        msg["To"] = recipient
        msg["Subject"] = email_subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain="gmail.com")
        msg["Reply-To"] = sender_email

        # Clean HTML body formatted for deliverability
        formatted_message = message.replace('\n', '<br>')
        html_body = f"""<!DOCTYPE html>
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
    {formatted_message}
  </div>
  <div class="foot">
    Tech Africa IT Secure Access System &bull; Automated Notification
  </div>
</div>
</body>
</html>"""

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Use STARTTLS on port 587 (more compatible with cloud hosts like Render)
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())

        print(f"[EMAIL SUCCESS] Sent to {recipient} | Subject: {email_subject}", flush=True)
        return True

    except smtplib.SMTPAuthenticationError:
        print("[EMAIL ERROR] Gmail authentication failed. Check sender_email and sender_password (App Password).", flush=True)
        return False
    except Exception as e:
        print(f"[EMAIL ERROR] Unexpected error: {e}", flush=True)
        return False


def send_intrusion_alert(username: str, reason: str, ip_address: str = None):
    """
    Convenience wrapper for intrusion-specific alerts sent to the admin.
    """
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
