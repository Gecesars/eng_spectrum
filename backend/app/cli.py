from __future__ import annotations

import click

from flask.cli import with_appcontext

from app.extensions import db
from app.models import User
from app.services.auth import hash_password
from app.services.email import build_confirm_email, send_email
from app.services.anatel_loader import import_anatel_xml, import_aerodromes_json


@click.group(name="engspec")
def engspec_cli() -> None:
    """Comandos administrativos do Engenharia de Espectro."""


@engspec_cli.command("create-user")
@click.option("--email", required=True)
@click.option("--password", required=True)
@click.option("--verified/--no-verified", default=True)
@with_appcontext
def create_user(email: str, password: str, verified: bool) -> None:
    email = email.strip().lower()
    existing = User.query.filter_by(email=email).first()
    if existing:
        raise click.ClickException("User already exists")
    user = User(
        email=email,
        email_verified=verified,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()
    click.echo(f"Created user {email} (verified={verified})")


@engspec_cli.command("set-password")
@click.option("--email", required=True)
@click.option("--password", required=True)
@with_appcontext
def set_password(email: str, password: str) -> None:
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException("User not found")
    user.password_hash = hash_password(password)
    db.session.commit()
    click.echo(f"Password updated for {email}")


@engspec_cli.command("verify-user")
@click.option("--email", required=True)
@with_appcontext
def verify_user(email: str) -> None:
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException("User not found")
    user.email_verified = True
    db.session.commit()
    click.echo(f"User {email} verified")


@engspec_cli.command("list-users")
@with_appcontext
def list_users() -> None:
    users = User.query.order_by(User.created_at.desc()).all()
    for user in users:
        status = "verified" if user.email_verified else "pending"
        click.echo(f"{user.email} ({status})")


@engspec_cli.command("delete-user")
@click.option("--email", required=True)
@with_appcontext
def delete_user(email: str) -> None:
    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException("User not found")
    db.session.delete(user)
    db.session.commit()
    click.echo(f"User {email} removed")


@engspec_cli.command("send-confirmation")
@click.option("--email", required=True)
@with_appcontext
def send_confirmation(email: str) -> None:
    from app.services.auth import create_email_token
    from flask import current_app

    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        raise click.ClickException("User not found")
    token = create_email_token(user, "confirm_email", current_app.config["EMAIL_TOKEN_TTL_HOURS"])
    subject, body = build_confirm_email(token)
    send_email(user.email, subject, body)
    click.echo(f"Confirmation sent to {email}")


@engspec_cli.command("import-anatel")
@click.option("--source", multiple=True, required=True, help="Arquivo XML de plano básico (pode repetir)")
@click.option("--truncate/--no-truncate", default=False, help="Limpar tabela antes de importar")
@with_appcontext
def import_anatel(source: tuple[str, ...], truncate: bool) -> None:
    total = 0
    for path in source:
        total += import_anatel_xml(path, truncate=truncate)
        truncate = False
    click.echo(f"Imported {total} records")


@engspec_cli.command("import-aerodromes")
@click.option("--source", required=True, help="Arquivo JSON de aeródromos")
@click.option("--truncate/--no-truncate", default=False)
@with_appcontext
def import_aerodromes(source: str, truncate: bool) -> None:
    count = import_aerodromes_json(source, truncate=truncate)
    click.echo(f"Imported {count} aerodromes")
