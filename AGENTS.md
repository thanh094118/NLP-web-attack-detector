# AGENTS.md

## Repository Status

This project is in **Phase 1**: a **non-ML MVP pipeline** for web access log parsing and rule-based web attack detection.

Current baseline status:
- Phase 1 pipeline is implemented end-to-end.
- Package-based architecture is the accepted convention and must be preserved.
- Do not rebuild from scratch.
- Do not start Phase 2 ML unless explicitly requested.

Phase 2 ML remains deferred. Do not add TF-IDF, n-gram ML, embeddings, vector search, deep learning, Isolation Forest, or realtime ML inference in Phase 1 tasks.

## Entrypoints

Primary CLI:
- `python -m src.main --input <access.log> --server-type <apache|nginx|iis> --output-dir <output_dir>`

Compatibility wrapper:
- `python main.py --input <access.log> --server-type <apache|nginx|iis> --output-dir <output_dir>`

## Architecture (Preserve)

Keep current package layout:
- `src/main.py`
- `src/collector/`
- `src/parser/`
- `src/normalizer/`
- `src/preprocessor/`
- `src/detection/`
- `src/features/`
- `src/scoring/`
- `src/exporters/`
- `src/reporting/`

Do not revert to single-file legacy modules.
Do not recreate:
- `src/parser.py`
- `src/scoring.py`
- `src/exporter.py`
- `src/report.py`

## Pipeline Outputs

Per run, expected artifacts:
- `raw_lines.jsonl`
- `parsed_logs.jsonl`
- `normalized_logs.jsonl`
- `normalized_logs.csv`
- `preprocessed_requests.jsonl`
- `features.csv`
- `alerts.jsonl`
- `alerts.csv`
- `report.md`
- `run_summary.json`

Collector-related optional metadata fields (raw stage):
- `encoding_used`
- `decode_error`
- `had_bom`
- `was_continuation_merged`
- `physical_line_start`
- `physical_line_end`

## Data/Schema Invariants

- Malformed logs are first-class records; do not silently drop them.
- Preserve `raw_log` and original URL field (`original_url` or equivalent).
- Preserve parse status/error fields where applicable.
- Keep output schemas stable; add optional fields conservatively.
- Preserve `event_id` (or equivalent stable identifier) across artifacts when possible.

## Collector Rules

- Continuation merge is intentionally conservative: merge only when continuation line starts with space/tab.
- Do not reintroduce broad heuristics that may merge valid record starts (hostname, IPv6-mapped forms, `-` prefixes, custom textual starts).

## Workflow Rules

Before code changes:
- Read `AGENTS.md`.
- Read relevant `conversation_cache/*` (at minimum: `current_status.md`, `known_issues.md`, `edge_cases.md`, `datasets.md`).

After code changes:
- Update `conversation_cache/current_status.md`.
- Update relevant cache files (`decisions.md`, `todo.md`, `known_issues.md`, `edge_cases.md`, `datasets.md`) when affected.

Engineering style:
- Prefer small, focused changes.
- Add/update tests for functional behavior changes.
- Run `pytest` after code changes.

## Commands

Environment:
- `pip install -r requirements.txt`
- `conda env create -f environment.yml`

Tests:
- `pytest -q`
- `PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider`

## Git Hygiene

Do not commit generated/local artifacts:
- `outputs/`
- `data/processed/`
- `__pycache__/`
- `.pytest_cache/`
- large local datasets or local-only log corpora
