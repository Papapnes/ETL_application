from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pandas as pd

MAX_BYTES = 25 * 1024 * 1024
MAX_ROWS = 100_000
MAX_COLUMNS = 300
MAX_TABLES = 50
SUPPORTED = ["csv", "tsv", "txt", "json", "jsonl", "xlsx", "xls", "parquet", "pdf"]
META = ["_etl_source", "_etl_table", "_etl_record", "_etl_sha256"]
TYPES = ["Texte", "Entier", "Décimal", "Date", "Booléen"]


class ETLError(ValueError):
    """An actionable input or configuration error."""


@dataclass
class Dataset:
    name: str
    table: str
    sha256: str
    frame: pd.DataFrame
    options: dict
    review_required: bool = False

    @property
    def key(self):
        return f"{self.name} · {self.table} · {self.sha256[:8]}"


def _frame(rows, columns=None):
    df = pd.DataFrame(rows, columns=columns)
    if len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ETLError("Limite dépassée : 100 000 lignes ou 300 colonnes par table.")
    names = [str(c).strip() for c in df.columns]
    if not names or any(not c for c in names):
        raise ETLError("Les en-têtes doivent être présents et non vides.")
    if len(set(names)) != len(names):
        raise ETLError("En-têtes en double : renommez-les dans le fichier source.")
    if any(c.startswith("_etl_") for c in names):
        raise ETLError("Le préfixe _etl_ est réservé à la traçabilité.")
    df.columns = names
    # Text staging avoids implicit interpretation of dates or leading-zero identifiers.
    for c in df:
        df[c] = (
            df[c]
            .map(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v)
            .astype("string")
        )
    return df.reset_index(drop=True)


def extract(name: str, content: bytes, options: dict | None = None) -> list[Dataset]:
    options = dict(options or {})
    if not content:
        raise ETLError("Le fichier est vide.")
    if len(content) > MAX_BYTES:
        raise ETLError("Le fichier dépasse 25 Mo.")
    ext = Path(name).suffix.lower().lstrip(".")
    if ext not in SUPPORTED:
        raise ETLError(f"Format .{ext} non pris en charge.")
    digest = hashlib.sha256(content).hexdigest()
    frames = []
    try:
        if ext in {"csv", "tsv", "txt"}:
            encoding = options.get("encoding", "utf-8-sig")
            text = content.decode(encoding)
            delimiter = options.get("delimiter")
            if not delimiter:
                if ext == "tsv":
                    delimiter = "\t"
                else:
                    try:
                        delimiter = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|").delimiter
                    except csv.Error:
                        delimiter = ","
            if delimiter not in [",", ";", "\t", "|"]:
                raise ETLError("Séparateur non pris en charge.")
            options.update(encoding=encoding, delimiter=delimiter)
            reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
            headers = next(reader, None)
            if headers is None:
                raise ETLError("Aucun en-tête dans le fichier.")
            rows = []
            for n, row in enumerate(reader, 2):
                if len(row) != len(headers):
                    raise ETLError(f"Enregistrement {n} : {len(row)} champs au lieu de {len(headers)}.")
                rows.append(row)
                if len(rows) > MAX_ROWS:
                    raise ETLError("Limite de 100 000 lignes dépassée.")
            frames.append(("Données", _frame(rows, headers)))
        elif ext in {"json", "jsonl"}:
            text = content.decode("utf-8-sig")
            if ext == "jsonl":
                records = [json.loads(line) for line in text.splitlines() if line.strip()]
            else:
                records = json.loads(text)
                for part in options.get("json_path", "").split("."):
                    if part:
                        records = records[part]
            if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
                raise ETLError(
                    "JSON attendu : liste d’objets. Indiquez le chemin vers cette liste si nécessaire."
                )
            # Keep nested values as JSON text; no silent flattening/collisions or row multiplication.
            frames.append(("Données", _frame(records)))
        elif ext in {"xlsx", "xls"}:
            if ext == "xlsx":
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    if sum(i.file_size for i in archive.infolist()) > 200 * 1024 * 1024:
                        raise ETLError("Classeur décompressé trop volumineux (limite 200 Mo).")
            header = int(options.get("header_row", 1))
            if header < 1 or header > 100:
                raise ETLError("La ligne d’en-tête doit être comprise entre 1 et 100.")
            with pd.ExcelFile(io.BytesIO(content), engine="openpyxl" if ext == "xlsx" else "xlrd") as book:
                if len(book.sheet_names) > MAX_TABLES:
                    raise ETLError("Maximum 50 feuilles par classeur.")
                for sheet in book.sheet_names:
                    raw = book.parse(
                        sheet, header=None, dtype="string", keep_default_na=False, nrows=MAX_ROWS + header + 1
                    )
                    if raw.empty:
                        continue
                    if len(raw) < header:
                        raise ETLError(f"Feuille {sheet} : ligne d’en-tête absente.")
                    frames.append((sheet, _frame(raw.iloc[header:].values.tolist(), raw.iloc[header - 1])))
        elif ext == "parquet":
            import pyarrow.parquet as pq

            table = pq.ParquetFile(io.BytesIO(content))
            if table.metadata.num_rows > MAX_ROWS:
                raise ETLError("Limite de 100 000 lignes dépassée.")
            frames.append(("Données", _frame(table.read().to_pandas())))
        elif ext == "pdf":
            import pdfplumber

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                if len(pdf.pages) > 100:
                    raise ETLError("Maximum 100 pages PDF.")
                for page_no, page in enumerate(pdf.pages, 1):
                    for table_no, table in enumerate(page.extract_tables(), 1):
                        if len(table) >= 2:
                            frames.append((f"Page {page_no} · table {table_no}", _frame(table[1:], table[0])))
                        if len(frames) > MAX_TABLES:
                            raise ETLError("Maximum 50 tables PDF.")
            if not frames:
                raise ETLError(
                    "Aucune table détectée. Les PDF scannés nécessitent un OCR, non inclus dans cette version."
                )
        if not frames:
            raise ETLError("Aucune table exploitable dans ce fichier.")
        return [Dataset(Path(name).name, label, digest, df, options, ext == "pdf") for label, df in frames]
    except ETLError:
        raise
    except (UnicodeError, csv.Error, ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile) as exc:
        raise ETLError(
            f"Lecture impossible ({type(exc).__name__}). Vérifiez le format et les paramètres d’import."
        ) from exc


def profile(df: pd.DataFrame) -> dict:
    missing = df.isna() | df.astype("string").apply(lambda s: s.str.strip().eq("")).fillna(False)
    cells = df.size
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing": int(missing.sum().sum()),
        "completeness": round(100 * (1 - missing.sum().sum() / cells), 1) if cells else 0.0,
        "duplicates": int(df.duplicated().sum()),
        "column_profile": pd.DataFrame(
            {
                "Colonne": df.columns,
                "Valeurs manquantes": missing.sum().values,
                "Valeurs distinctes": df.nunique(dropna=True).values,
            }
        ),
    }


def default_recipe(columns: list[str]) -> dict:
    return {
        "version": 1,
        "name": "Ma recette",
        "expected_columns": list(columns),
        "trim": True,
        "null_markers": [""],
        "deduplicate": False,
        "duplicate_keys": [],
        "rules": [
            dict(
                column=c,
                target=c,
                type="Texte",
                required=False,
                fill="",
                case="Conserver",
                decimal=".",
                date_format="%Y-%m-%d",
                minimum="",
                maximum="",
            )
            for c in columns
        ],
    }


def validate_recipe(recipe: dict):
    if not isinstance(recipe, dict) or recipe.get("version") != 1:
        raise ETLError("Version de recette non prise en charge (version 1 attendue).")
    if not isinstance(recipe.get("name"), str) or not recipe["name"].strip():
        raise ETLError("Donnez un nom à la recette.")
    cols, rules = recipe.get("expected_columns"), recipe.get("rules")
    if (
        not isinstance(cols, list)
        or not cols
        or len(cols) > MAX_COLUMNS
        or not all(isinstance(c, str) and c for c in cols)
        or len(set(cols)) != len(cols)
    ):
        raise ETLError("Schéma attendu invalide.")
    if not isinstance(rules, list) or len(rules) != len(cols) or not all(isinstance(r, dict) for r in rules):
        raise ETLError("Une règle est nécessaire pour chaque colonne.")
    if [r.get("column") for r in rules] != cols:
        raise ETLError("Les règles doivent correspondre aux colonnes attendues, dans le même ordre.")
    targets = [r.get("target") for r in rules]
    if not all(isinstance(c, str) and c.strip() and not c.startswith("_etl_") for c in targets):
        raise ETLError("Noms de sortie invalides ou réservés.")
    if len(set(targets)) != len(targets):
        raise ETLError("Deux colonnes ne peuvent pas avoir le même nom de sortie.")
    if not isinstance(recipe.get("null_markers"), list) or not all(
        isinstance(v, str) for v in recipe["null_markers"]
    ):
        raise ETLError("Les marqueurs de valeurs manquantes doivent être une liste de textes.")
    for key in ("trim", "deduplicate"):
        if type(recipe.get(key)) is not bool:
            raise ETLError(f"Paramètre booléen invalide : {key}.")
    keys = recipe.get("duplicate_keys")
    if not isinstance(keys, list) or not all(isinstance(k, str) and k in cols for k in keys):
        raise ETLError("Clé de dédoublonnage inconnue.")
    for rule in rules:
        if rule.get("type") not in TYPES or rule.get("case") not in ["Conserver", "Minuscules", "Majuscules"]:
            raise ETLError("Type ou transformation de texte invalide.")
        if type(rule.get("required")) is not bool:
            raise ETLError("Le contrôle obligatoire doit être booléen.")
        if not all(
            isinstance(rule.get(k), str) for k in ["fill", "decimal", "date_format", "minimum", "maximum"]
        ):
            raise ETLError("Paramètres de colonne incomplets.")
        if rule["decimal"] not in [".", ","]:
            raise ETLError("Séparateur décimal invalide.")
        if rule["type"] == "Date" and not rule["date_format"]:
            raise ETLError("Un format de date explicite est obligatoire.")
        bounds = []
        for bound in ("minimum", "maximum"):
            value = rule[bound]
            if value:
                try:
                    number = float(value)
                except ValueError as exc:
                    raise ETLError("Les bornes doivent être numériques (point décimal).") from exc
                if rule["type"] not in ["Entier", "Décimal"] or not math.isfinite(number):
                    raise ETLError("Les bornes finies sont réservées aux colonnes numériques.")
                bounds.append(number)
        if len(bounds) == 2 and bounds[0] > bounds[1]:
            raise ETLError("La borne minimale dépasse la borne maximale.")


def load_recipe(content: bytes) -> dict:
    if len(content) > 1024 * 1024:
        raise ETLError("La recette dépasse 1 Mo.")
    try:
        recipe = json.loads(content)
    except (ValueError, UnicodeError) as exc:
        raise ETLError("Recette JSON illisible.") from exc
    validate_recipe(recipe)
    return recipe


def run(datasets: list[Dataset], recipe: dict, reviewed: set[str] | None = None) -> dict:
    validate_recipe(recipe)
    recipe = deepcopy(recipe)
    if not datasets:
        raise ETLError("Sélectionnez au moins une table.")
    reviewed = reviewed or set()
    sources, parts = [], []
    if sum(len(d.frame) for d in datasets) > MAX_ROWS:
        raise ETLError("Le lot dépasse 100 000 lignes. Traitez-le en plusieurs lots.")
    for d in datasets:
        if d.review_required and d.key not in reviewed:
            raise ETLError(f"Vérifiez l’extraction PDF avant de poursuivre : {d.name} / {d.table}.")
        if set(d.frame.columns) != set(recipe["expected_columns"]):
            raise ETLError(
                f"Schéma incompatible : {d.name} / {d.table}. Choisissez des tables de même structure."
            )
        part = d.frame[recipe["expected_columns"]].copy()
        part[META[0]], part[META[1]] = d.name, d.table
        part[META[2]] = range(1, len(part) + 1)
        part[META[3]] = d.sha256
        parts.append(part)
        sources.append(
            dict(
                file=d.name,
                table=d.table,
                sha256=d.sha256,
                rows=len(part),
                import_options=d.options,
                pdf_reviewed=d.review_required and d.key in reviewed,
            )
        )
    raw = pd.concat(parts, ignore_index=True)
    clean = raw.copy()
    errors = [[] for _ in range(len(raw))]
    audit = []

    def flag(mask, reason):
        for i in mask.fillna(False)[lambda s: s].index:
            errors[i].append(reason)

    for rule in recipe["rules"]:
        c = rule["column"]
        s = raw[c].astype("string")
        if recipe["trim"]:
            s = s.str.strip()
        s = s.mask(s.isin(recipe["null_markers"]))
        if rule["fill"] != "":
            s = s.fillna(rule["fill"])
        if rule["case"] == "Minuscules":
            s = s.str.lower()
        elif rule["case"] == "Majuscules":
            s = s.str.upper()
        if rule["required"]:
            flag(s.isna() | s.eq(""), f"{c} : valeur obligatoire")
        kind = rule["type"]
        if kind in ["Entier", "Décimal"]:
            normalized = s.str.replace(rule["decimal"], ".", regex=False)
            # No implicit thousands separator or exponent conversion for identifiers.
            syntax = normalized.str.fullmatch(r"[+-]?\d+(?:\.\d+)?").fillna(False)
            numeric = pd.to_numeric(normalized.where(syntax), errors="coerce")
            finite = numeric.map(lambda x: pd.notna(x) and math.isfinite(float(x)))
            valid = syntax & finite
            if kind == "Entier":
                # Limit integers to exact IEEE-754 range to avoid silent rounding during coercion.
                exact_integer = normalized.map(
                    lambda v: (
                        bool(re.fullmatch(r"[+-]?\d+(?:\.\d+)?", v))
                        and Decimal(v) == Decimal(v).to_integral_value()
                        and abs(Decimal(v)) <= 2**53 - 1
                        if isinstance(v, str)
                        else False
                    )
                )
                valid &= exact_integer
            flag(s.notna() & ~valid, f"{c} : conversion {kind.lower()} impossible")
            converted = numeric.where(valid).astype("Int64" if kind == "Entier" else "Float64")
            for bound, op in [("minimum", "lt"), ("maximum", "gt")]:
                if rule[bound]:
                    flag(getattr(converted, op)(float(rule[bound])), f"{c} : hors borne {bound}")
            s = converted
        elif kind == "Date":
            try:
                converted = pd.to_datetime(s, format=rule["date_format"], errors="coerce", exact=True)
            except (ValueError, TypeError) as exc:
                raise ETLError(f"{c} : format de date invalide.") from exc
            flag(s.notna() & converted.isna(), f"{c} : date invalide ({rule['date_format']})")
            s = converted
        elif kind == "Booléen":
            converted = s.str.lower().map(
                {
                    "true": True,
                    "false": False,
                    "vrai": True,
                    "faux": False,
                    "oui": True,
                    "non": False,
                    "1": True,
                    "0": False,
                }
            )
            flag(s.notna() & converted.isna(), f"{c} : booléen invalide")
            s = converted.astype("boolean")
        clean[c] = s
        audit.append(
            {
                "column": c,
                "output": rule["target"],
                "type": kind,
                "changed_cells": int((raw[c].fillna("").astype(str) != s.fillna("").astype(str)).sum()),
            }
            if kind == "Texte"
            else {"column": c, "output": rule["target"], "type": kind}
        )
    valid_before_duplicates = pd.Series([not e for e in errors], index=raw.index, dtype=bool)
    duplicates = pd.Series(False, index=raw.index)
    if recipe["deduplicate"]:
        keys = recipe["duplicate_keys"] or recipe["expected_columns"]
        duplicates.loc[valid_before_duplicates] = clean.loc[valid_before_duplicates].duplicated(
            keys, keep="first"
        )
        flag(duplicates, "Doublon : première ligne valide conservée")
    rejected_mask = pd.Series([bool(e) for e in errors], index=raw.index, dtype=bool)
    accepted = clean.loc[~rejected_mask].rename(columns={r["column"]: r["target"] for r in recipe["rules"]})
    rejected = raw.loc[rejected_mask].copy()
    rejected["_etl_issues"] = [" ; ".join(errors[i]) for i in rejected.index]
    report = dict(
        run_id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
        app_version="0.2.0",
        recipe_name=recipe["name"],
        recipe_sha256=hashlib.sha256(json_bytes(recipe)).hexdigest(),
        input_rows=len(raw),
        accepted_rows=len(accepted),
        rejected_rows=len(rejected),
        duplicate_rows=int(duplicates.sum()),
        sources=sources,
        transformations=audit,
        issue_counts=pd.Series([reason for row in errors for reason in row], dtype="string")
        .value_counts()
        .to_dict(),
    )
    return dict(
        accepted=accepted.reset_index(drop=True),
        rejected=rejected.reset_index(drop=True),
        report=report,
        recipe=recipe,
    )


def json_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def spreadsheet_safe(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    safe, count = df.copy(), 0
    for col in safe:
        # Only strings can become formulas; preserve actual negative numbers as numbers.
        mask = safe[col].map(lambda v: isinstance(v, str) and bool(re.match(r"^[\s]*[=+@-]", v))).astype(bool)
        count += int(mask.sum())
        if mask.any():
            safe[col] = safe[col].astype(object)
            safe.loc[mask, col] = "'" + safe.loc[mask, col].astype(str)
    return safe, count


def bundle(result: dict, output_format: str, allow_rejected: bool = False) -> bytes:
    if len(result["rejected"]) and not allow_rejected:
        raise ETLError(
            "Confirmez l’export des seules lignes valides ; les autres seront jointes en quarantaine."
        )
    if output_format not in ["CSV", "Excel", "Parquet"]:
        raise ETLError("Format de sortie inconnu.")
    if result["accepted"].empty:
        raise ETLError("Aucune ligne valide à exporter.")
    out = io.BytesIO()
    accepted, protected = spreadsheet_safe(result["accepted"])
    rejected, rejected_protected = spreadsheet_safe(result["rejected"])
    report = {
        **result["report"],
        "output_format": output_format,
        "spreadsheet_cells_escaped": (protected if output_format != "Parquet" else 0) + rejected_protected,
        "partial_export_acknowledged": bool(len(rejected) and allow_rejected),
    }
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        if output_format == "CSV":
            archive.writestr("donnees.csv", accepted.to_csv(index=False, sep=";").encode("utf-8-sig"))
        elif output_format == "Excel":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                accepted.to_excel(writer, sheet_name="Données", index=False)
            archive.writestr("donnees.xlsx", buffer.getvalue())
        else:
            archive.writestr("donnees.parquet", result["accepted"].to_parquet(index=False))
        archive.writestr("quarantaine.csv", rejected.to_csv(index=False, sep=";").encode("utf-8-sig"))
        archive.writestr("rapport.json", json_bytes(report))
        archive.writestr("recette.json", json_bytes(result["recipe"]))
        archive.writestr(
            "LIRE-MOI.txt",
            (
                "Atelier ETL — export local\nLes colonnes _etl_ permettent de remonter à la source.\n"
                "_etl_record : numéro de l’enregistrement de données (hors en-tête), pas ligne physique.\n"
                "CSV : UTF-8 BOM, séparateur point-virgule.\n"
                "Les textes pouvant être interprétés comme formules sont préfixés par une apostrophe dans CSV/Excel.\n"
                "Parquet conserve les valeurs textuelles originales. Les décimaux sont des flottants.\n"
                "Les lignes en quarantaine contiennent les valeurs originales et les motifs de rejet.\n"
            ).encode("utf-8"),
        )
    return out.getvalue()
