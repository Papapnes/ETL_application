# Reusable ETL workflow

Status: original design brief. A local pilot is now implemented; see [README.md](README.md) for the actual supported scope and limits. This document also contains future-stage intentions that are not all implemented.

## Objective

Reduce repeated file preparation by saving import settings, transformations, validation rules, and export settings as reusable recipes. Keep original inputs unchanged and make each output traceable to its inputs and recipe version.

## User journey

1. Add files or select an input folder.
2. Detect supported formats and preview extracted datasets.
3. Select sheets, tables, or nested records to import.
4. Inspect data profiles and configure cleaning rules.
5. Preview changes, rejected rows, and validation results.
6. Save a recipe and run it across compatible files.
7. Export approved datasets and a run report.

## Workflow stages

| Stage | Behavior | Result |
|---|---|---|
| Intake | Record file name, size, checksum, and detected format; reject unsupported inputs explicitly | Input manifest |
| Extract | Use a format-specific adapter; preserve sheet, page, table, or record location | Raw datasets with provenance |
| Profile | Measure row counts, missing values, candidate types, duplicates, and structural inconsistencies | Quality profile |
| Transform | Apply explicitly configured, ordered rules | Prepared datasets and change counts |
| Validate | Check required columns, types, keys, ranges, and reference relationships | Passed checks and quarantined records |
| Load | Write outputs only after the configured quality gate passes | Versioned output datasets |
| Record | Save recipe version, input hashes, errors, warnings, and output paths | Run report |

## Format coverage plan

Support is a declared adapter capability, not a promise that every possible file can be interpreted.

| Family | Proposed initial behavior | Decisions requiring attention |
|---|---|---|
| CSV, TSV, delimited TXT | Read records with configurable encoding, separator, quoting, and headers | Ambiguous delimiters or encodings; malformed rows |
| XLS, XLSX | Select sheets and header rows; extract each table separately | Merged cells, formulas versus cached values, multiple tables per sheet |
| JSON, JSONL | Read record arrays or select a nested record path | Flattening objects; exploding arrays changes row counts |
| Parquet | Preserve typed columns | Nested fields and incompatible schemas across files |
| XML | Select repeating record elements | Namespaces, attributes, and nested records |
| Text-based PDF | Extract candidate tables and text with page references | Layout-dependent extraction requires preview and review |
| Scanned PDF and images | Optional OCR stage followed by extraction | OCR dependencies, uncertain characters, and review requirements |
| Other formats | Return an unsupported-format result and allow a future adapter | Never silently treat an unknown file as CSV |

## Reusable transformations

- Rename columns and normalize whitespace using explicit rules.
- Convert types with specified date formats, decimal separators, and time zones.
- Map known missing-value markers while preserving meaningful values such as zero.
- Remove duplicates using a chosen key and retention rule.
- Replace values through maintained mapping tables.
- Filter records, derive columns, split fields, and reshape tables.
- Append compatible datasets; join using explicit keys and expected cardinality.

Type inference proposes a schema. It must preserve identifiers with leading zeros and flag ambiguous dates. Missing-value replacement, duplicate removal, and array expansion must be visible recipe choices rather than silent defaults.

## Recipe contents

Each versioned recipe contains input selection, adapter settings, selected sheets or record paths, expected schema, ordered transformations, validation rules, error policy, and output settings. A recipe should run without repeating interactive configuration once its inputs conform to the expected structure.

## Failure and rerun behavior

- Preserve raw inputs and keep outputs outside watched input folders.
- Detect schema drift before applying transformations; require a mapping or fail affected files according to policy.
- Quarantine invalid records with their source location and reason. Never silently discard parse errors.
- Record per-file outcomes so one failed input does not conceal successful or incomplete processing.
- Use input checksums and recipe versions to identify repeated runs; make skip versus reprocess behavior explicit.
- Write outputs to a staging location and finalize only after successful validation and writing.
- For database loading, define transaction boundaries and an explicit append, replace, or upsert policy before enabling writes.
- Keep sensitive record values out of operational logs by default.

## Suggested first milestone

Implement batch import for CSV/TSV, JSON/JSONL, XLS/XLSX, and text-based PDF; dataset previews; reusable cleaning recipes; validation and quarantine; CSV/Parquet export; and run reports. Treat PDF extraction as review-required. Add OCR, further adapters, scheduling, and database destinations in subsequent milestones.

## Acceptance criteria

1. A saved recipe processes a second compatible batch without re-entering settings.
2. Every output is traceable to its source and recipe version.
3. Malformed rows, unsupported files, and schema changes produce explicit outcomes.
4. Leading-zero identifiers and ambiguous dates are handled according to configured rules.
5. Duplicate removal and joins report their effect on row counts.
6. Failed exports do not leave apparently complete final outputs.
7. PDF-derived datasets cannot pass a required review gate without recorded review.

## Decisions pending

- Interaction: local upload app, folder-processing pipeline, or AI-guided workflow.
- Main destination: analysis files, Power BI preparation, or a database.
- Representative source files and typical batch sizes for implementation and verification.
