import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def database_path():
    return str(Path(os.environ.get("DATAFLOW_DB_PATH", ROOT / "local-data" / "accounts.sqlite3")).resolve())


def smtp_ready():
    return all(
        os.environ.get(k)
        for k in ("DATAFLOW_SMTP_HOST", "DATAFLOW_SMTP_USER", "DATAFLOW_SMTP_PASSWORD", "DATAFLOW_SMTP_FROM")
    )


def send_reset_email(recipient, token):
    if not smtp_ready():
        raise RuntimeError("SMTP is not configured")
    message = EmailMessage()
    message["From"] = os.environ["DATAFLOW_SMTP_FROM"]
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
    host, port = os.environ["DATAFLOW_SMTP_HOST"], int(os.environ.get("DATAFLOW_SMTP_PORT", "587"))
    context = ssl.create_default_context()
    client = (
        smtplib.SMTP_SSL(host, port, timeout=15, context=context)
        if port == 465
        else smtplib.SMTP(host, port, timeout=15)
    )
    with client:
        if port != 465:
            client.starttls(context=context)
        client.login(os.environ["DATAFLOW_SMTP_USER"], os.environ["DATAFLOW_SMTP_PASSWORD"])
        client.send_message(message)
