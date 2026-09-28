import os
import smtplib
import ssl
import tomllib
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DatabaseConfig:
    backend: str
    target: str = field(repr=False)
    rootcert: str = field(default="system", repr=False)


def settings(runtime_secrets=None):
    """Read the same ignored TOML locally and in Community Cloud; env wins."""
    from accounts.errors import DatabaseError

    values = {}
    path = ROOT / ".streamlit" / "secrets.toml"
    if path.exists():
        try:
            with path.open("rb") as source:
                values.update(tomllib.load(source))
        except (OSError, ValueError):
            raise DatabaseError("Configuration des secrets invalide.") from None
    if runtime_secrets:
        values.update(runtime_secrets)
    values.update({key: value for key, value in os.environ.items() if key.startswith("DATAFLOW_")})
    return values


def database_config(*, migration=False, runtime_secrets=None):
    from accounts.errors import DatabaseError

    values = settings(runtime_secrets)
    key = "DATAFLOW_MIGRATION_DATABASE_URL" if migration else "DATAFLOW_DATABASE_URL"
    url = values.get(key)
    if url:
        if not isinstance(url, str) or not url.startswith(("postgresql://", "postgres://")):
            raise DatabaseError("Configuration PostgreSQL invalide.")
        return DatabaseConfig("postgresql", url, str(values.get("DATAFLOW_SSL_ROOT_CERT", "system")))
    # Presence of an empty URL is a configuration error, never a SQLite fallback.
    if key in values or migration:
        raise DatabaseError("Configuration PostgreSQL manquante.")
    if values.get("DATAFLOW_DB_BACKEND") == "sqlite":
        return DatabaseConfig("sqlite", database_path())
    raise DatabaseError("Configurez DATAFLOW_DATABASE_URL ou activez explicitement SQLite en local.")


def database_path():
    return str(Path(settings().get("DATAFLOW_DB_PATH", ROOT / "local-data" / "accounts.sqlite3")).resolve())


def smtp_ready():
    values = settings()
    return all(
        values.get(k)
        for k in ("DATAFLOW_SMTP_HOST", "DATAFLOW_SMTP_USER", "DATAFLOW_SMTP_PASSWORD", "DATAFLOW_SMTP_FROM")
    )


def send_reset_email(recipient, token):
    if not smtp_ready():
        raise RuntimeError("SMTP is not configured")
    values = settings()
    message = EmailMessage()
    message["From"] = values["DATAFLOW_SMTP_FROM"]
    message["To"] = recipient
    message["Subject"] = "DataFlow Studio — password reset / récupération / استعادة"
    message.set_content(
        "Votre code de récupération / Your recovery code / رمز الاستعادة:\n\n"
        + token
        + "\n\nFR : Dans DataFlow Studio, ouvrez « Réinitialiser le mot de passe » et saisissez ce code. "
        "Il expire dans 30 minutes et ne peut être utilisé qu’une fois. Si vous n’avez pas fait cette demande, ignorez ce message.\n\n"
        "EN: In DataFlow Studio, open 'Reset password' and enter this code. It expires in 30 minutes and can only be used once. "
        "If you did not request this, ignore this message.\n\n"
        "AR: افتح «إعادة تعيين كلمة المرور» في المنصة وأدخل هذا الرمز. تنتهي صلاحيته بعد 30 دقيقة ويُستخدم مرة واحدة فقط. "
        "إذا لم تطلب الاستعادة، فتجاهل هذه الرسالة."
    )
    host, port = values["DATAFLOW_SMTP_HOST"], int(values.get("DATAFLOW_SMTP_PORT", "587"))
    context = ssl.create_default_context()
    client = (
        smtplib.SMTP_SSL(host, port, timeout=15, context=context)
        if port == 465
        else smtplib.SMTP(host, port, timeout=15)
    )
    with client:
        if port != 465:
            client.starttls(context=context)
        client.login(values["DATAFLOW_SMTP_USER"], values["DATAFLOW_SMTP_PASSWORD"])
        client.send_message(message)
