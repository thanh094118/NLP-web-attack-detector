# Datasets

## Phase 1 Requirements

Current Phase 1 validation requires raw `access.log` samples from:
- Apache
- Nginx
- IIS

Labeled ML datasets are **not required** for Phase 1.

## Phase 1 Dataset Purpose

Phase 1 datasets are used to validate:
- collector behavior (decode path, BOM handling, continuation merge behavior)
- parser robustness
- normalizer output stability
- preprocessor transformations
- rule-based detection behavior
- export artifacts (JSONL/CSV)
- reporting outputs (`report.md`, `run_summary.json`)
- compatibility with pre-parsed JSONL records used as parser-stage input in conversion workflows

## Rules Dataset

- Preferred runtime rule path: `configs/rules.yaml`
- Runtime/default rules path: `src/rules/attack_patterns.yaml`

## Output Validation Targets

Expected per-run artifacts:
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

Optional collector metadata now expected in `raw_lines.jsonl`:
- `encoding_used`
- `decode_error`
- `had_bom`
- `was_continuation_merged`
- `physical_line_start`
- `physical_line_end`

Additional normalizer quality/forensic fields now expected in `normalized_logs.jsonl`:
- `fragment`
- `request_target`
- `normalize_errors`
- `status_code_missing`
- `status_code_invalid`
- `response_size_missing`
- `response_size_invalid`

## Input Conversion Dataset Path

`convert.py` now canonicalizes heterogeneous inputs (`.txt/.log/.csv/.json/.jsonl`) into raw access-log output:
- `data/raw/<server_type>/converted_<input_stem>.log`

## Phase 2 Outlook

Phase 2 may later use labeled benign/anomaly datasets for ML training/evaluation, but this remains intentionally deferred.

## Isolated AI Test Assets

For explicit ML test runs only (outside the Phase 1 rule-based baseline), `test_pipeline/` contains:
- `feature_columns.json`
- `label_mapping.json`
- `normal_ascii_mean_by_field.json` (per-field normal ASCII means for optional-field imputation)
- `scaler.joblib`
- `random_forest.joblib` (baseline binary model)
- additional comparison models (`decision_tree.joblib`, `logistic_regression.joblib`, `sgd_classifier.joblib`)

Expected AI test input for `test_pipeline/run_ai_pipeline.py`:
- JSONL where each line is a parsed request/log record (dictionary-like)
- Missing fields are filled by pipeline defaults before inference.

Expected AI test outputs:
- `{input_stem}_ai_predictions.jsonl` (prediction/label/probability)
- `{input_stem}_ai_preparsed.jsonl` (debug pre-parsed request/response schema before AI transforms)
