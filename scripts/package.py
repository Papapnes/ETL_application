"""Package only source, documentation and synthetic examples; never session data."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / "deliverables" / "DataFlow-Studio-0.2.zip"
output.parent.mkdir(exist_ok=True)
files = [
    ROOT / name
    for name in (
        "app.py",
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "ETL_WORKFLOW.md",
        "Lancer.cmd",
        ".gitignore",
    )
]
for directory, pattern in (
    ("etl", "*.py"),
    ("accounts", "*.py"),
    ("accounts/migrations", "*.sql"),
    ("ui", "*.py"),
    ("tests", "*.py"),
    ("scripts", "*.py"),
    ("docs", "*.md"),
    ("examples", "*.csv"),
    ("examples", "*.json"),
    (".streamlit", "*.toml"),
    (".github/workflows", "*.yml"),
):
    files.extend((ROOT / directory).glob(pattern))
with ZipFile(output, "w", ZIP_DEFLATED) as archive:
    for path in sorted(files):
        if path.name == "secrets.toml":
            continue
        archive.write(path, "DataFlow-Studio/" + path.relative_to(ROOT).as_posix())
with ZipFile(output) as archive:
    assert archive.testzip() is None
    print(f"Package verified: {len(archive.namelist())} files, {output.stat().st_size} bytes")
print(output)
