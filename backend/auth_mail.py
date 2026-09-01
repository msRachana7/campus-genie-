"""SMTP delivery. Credentials remain only in backend/.env."""
import os
import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode, urlsplit
from fastapi import HTTPException


def mail_settings():
    username = os.getenv("EMAIL_USER", "").strip()
    password = os.getenv("EMAIL_PASS", "").replace(" ", "")
    base = os.getenv("CLIENT_URL", "http://localhost:3000").rstrip("/")
    parsed = urlsplit(base)
    valid_scheme = parsed.scheme == "https" or (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"})
    if not valid_scheme or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise HTTPException(503, "Set CLIENT_URL to the frontend HTTPS URL (HTTP is allowed only for localhost).")
    if not username or not password:
        raise HTTPException(503, "Email delivery is not configured. Set EMAIL_USER and EMAIL_PASS in backend/.env.")
    return username, password, base


def send_link(email, action, raw_token):
    username, password, base = mail_settings()
    # Fragments are not sent to the web server or in Referer headers.
    link = base + "/#" + urlencode({"auth_action": action, "token": raw_token})
    message = EmailMessage()
    message["From"] = username
    message["To"] = email
    message["Subject"] = "Reset your Campus Genie password" if action == "reset" else "Verify your Campus Genie email"
    lifetime = "15 minutes" if action == "reset" else "24 hours"
    message.set_content(
        f"Open this link to {'reset your password' if action == 'reset' else 'verify your email'}:\n\n{link}\n\n"
        f"It expires in {lifetime} and can be used once.\n"
        "Only continue if you requested this action. Otherwise ignore this email.\n"
        "Campus Genie will never ask for your college/Google account password."
    )
    try:
        port = int(os.getenv("SMTP_PORT", "465"))
        host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=15, context=ssl.create_default_context()) as smtp:
                smtp.login(username, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=15) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
                smtp.login(username, password)
                smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        # Do not return SMTP responses, tokens, credentials or recipient data.
        raise HTTPException(503, "The verification/reset email could not be sent. Check the backend SMTP settings, then request a new link.") from None
