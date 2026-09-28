"""Run all tests against an isolated, TLS-enabled local PostgreSQL cluster.

Requires PostgreSQL binaries and the project's dev dependencies. Does not use
any Supabase URL or touch existing databases. Keeps logs in .postgres-test/.
"""

import argparse
import os
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from accounts.config import DatabaseConfig  # noqa: E402
from accounts.migrate import migrate_schema  # noqa: E402


def certificate(directory):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=2))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    (directory / "server.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    private_key = directory / "server.key"
    private_key.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        )
    )
    private_key.chmod(0o600)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bin-dir", required=True, type=Path)
    args = parser.parse_args()
    suffix = ".exe" if os.name == "nt" else ""
    binaries = args.bin_dir.resolve()
    directory = ROOT / ".postgres-test" / str(uuid4())
    directory.mkdir(parents=True)
    certificate(directory)
    password_file = directory / "test-password.txt"
    password_file.write_text("local-test-only\n", encoding="ascii")
    password_file.chmod(0o600)
    data = directory / "data"
    flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

    def run_checked(command, *, timeout=90, env=None):
        # A PostgreSQL child can inherit Windows pipe handles after pg_ctl exits.
        # File-backed output avoids communicate() waiting for a live server's EOF.
        output_path = directory / (Path(command[0]).stem + "-" + uuid4().hex[:8] + ".log")
        with output_path.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=env,
                stdout=output,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                **flags,
            )
        print(output_path.read_text(encoding="utf-8", errors="replace"), flush=True)
        result.check_returncode()
        return result

    print(f"Test PostgreSQL : {directory.name}", flush=True)
    run_checked(
        [
            str(binaries / ("initdb" + suffix)),
            "-D",
            str(data),
            "-U",
            "postgres",
            "--auth=scram-sha-256",
            "--encoding=UTF8",
            "--no-locale",
            "--pwfile",
            str(password_file),
        ],
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with (data / "postgresql.conf").open("a", encoding="utf-8") as output:
        output.write(f"\nlisten_addresses='127.0.0.1'\nport={port}\nssl=on\n")
        output.write(f"ssl_cert_file='{(directory / 'server.crt').as_posix()}'\n")
        output.write(f"ssl_key_file='{(directory / 'server.key').as_posix()}'\n")
    # All TCP clients, including tests, must use encrypted/password-authenticated connections.
    (data / "pg_hba.conf").write_text("hostssl all all 127.0.0.1/32 scram-sha-256\n", encoding="ascii")
    control = [str(binaries / ("pg_ctl" + suffix)), "-D", str(data)]
    run_checked(control + ["-l", str(directory / "server.log"), "-w", "start"])
    try:
        base = f"postgresql://postgres:local-test-only@localhost:{port}/"
        rootcert = str(directory / "server.crt")
        with psycopg.connect(
            base + "postgres?hostaddr=127.0.0.1",
            autocommit=True,
            sslmode="verify-full",
            sslrootcert=rootcert,
            connect_timeout=10,
            gssencmode="disable",
        ) as db:
            db.execute("CREATE DATABASE dataflow_test")
        config = DatabaseConfig("postgresql", base + "dataflow_test?hostaddr=127.0.0.1", rootcert)
        print("Application des migrations sur la base de test", flush=True)
        migrate_schema(config)
        with psycopg.connect(
            config.target,
            autocommit=True,
            sslmode="verify-full",
            sslrootcert=rootcert,
            connect_timeout=10,
            gssencmode="disable",
        ) as db:
            db.execute("ALTER ROLE dataflow_app LOGIN PASSWORD 'local-app-test-only'")
        env = os.environ.copy()
        env.update(
            DATAFLOW_TEST_ADMIN_URL=config.target,
            DATAFLOW_TEST_APP_URL=f"postgresql://dataflow_app:local-app-test-only@localhost:{port}/dataflow_test?hostaddr=127.0.0.1",
            DATAFLOW_TEST_ROOT_CERT=rootcert,
            PYTHONIOENCODING="utf-8",
        )
        # Fresh, task-owned paths avoid inherited temporary-folder ACLs on Windows.
        test_temp = directory / "pytest-temp"
        assert test_temp.resolve().is_relative_to((ROOT / ".postgres-test").resolve())
        assert not test_temp.exists()
        print("Execution de la suite SQLite + PostgreSQL", flush=True)
        return run_checked(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--junitxml=.postgres-test/results.xml",
                f"--basetemp={test_temp}",
                "-o",
                f"cache_dir={directory / 'pytest-cache'}",
            ],
            env=env,
            timeout=300,
        ).returncode
    finally:
        run_checked(control + ["-m", "fast", "-w", "stop"])


if __name__ == "__main__":
    raise SystemExit(main())
