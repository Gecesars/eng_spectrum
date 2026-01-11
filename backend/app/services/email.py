from __future__ import annotations

import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to_email: str, subject: str, body: str) -> None:
    host = current_app.config["SMTP_HOST"]
    port = current_app.config["SMTP_PORT"]
    user = current_app.config["SMTP_USER"]
    password = current_app.config["SMTP_PASS"]
    sender = current_app.config["SMTP_FROM"]
    use_tls = current_app.config["SMTP_USE_TLS"]
    use_ssl = current_app.config.get("SMTP_USE_SSL", False)

    if not host:
        raise RuntimeError("SMTP_HOST not configured")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    with smtp_class(host, port, timeout=10) as server:
        if use_tls and not use_ssl:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(message)


def build_confirm_email(token: str) -> tuple[str, str]:
    base_url = current_app.config["APP_BASE_URL"].rstrip("/")
    subject = "Confirme seu e-mail - Engenharia de Espectro"
    body = (
        "Use o token abaixo para confirmar seu cadastro:\n\n"
        f"{token}\n\n"
        f"Ou acesse: {base_url}/confirm?token={token}\n"
    )
    return subject, body


def build_reset_email(token: str) -> tuple[str, str]:
    base_url = current_app.config["APP_BASE_URL"].rstrip("/")
    subject = "Redefinição de senha - Engenharia de Espectro"
    body = (
        "Use o token abaixo para redefinir sua senha:\n\n"
        f"{token}\n\n"
        f"Ou acesse: {base_url}/reset?token={token}\n"
    )
    return subject, body
