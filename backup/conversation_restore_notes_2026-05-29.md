# Conversation Backup (2026-05-29)

## Key fixes completed in this session

1. `src/main.py`
- Added dedicated feature CSV exporter to avoid metadata header contamination in `features.csv`:
  - `feature_csv_exporter = CSVExporter()`
  - Use `feature_csv_exporter.export(feature_rows, stage_file("extract", "features.csv"))`

2. `src/features/feature_extractor.py`
- Removed redundant/collinear features from `FEATURE_NAMES` and extraction output.

3. `src/main.py::build_feature_row`
- Changed feature row to model-focused output (only `feature_*`, excluding metadata/text).

4. `src/scoring/risk_engine.py`
- Switched special-char bonus from removed aggregate count to per-field sum.

5. `src/converter/convert_flow.py`
- `_iter_text_entries()` groups request-line + headers into one mapping.
- Added `_parse_request_line(...)` helper.
- Converts HTTP request-block input into one synthetic access-log line.

6. Tests updated
- `tests/test_features.py`
- `tests/test_scoring.py`
- `tests/test_convert.py`

## Backup artifacts
- `backup/wip_fixes.patch`
- `backup/conversation_restore_notes_2026-05-29.md`

## Restore
- `git apply --check backup/wip_fixes.patch`
- `git apply backup/wip_fixes.patch`
