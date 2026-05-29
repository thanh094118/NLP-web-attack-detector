# Todo

## High Priority

- Align `tests/test_parser.py` contract with current parser behavior (`parse_lines` list vs iterator expectation) and remove brittle assertions on exact internal messages when not part of API contract.
- Add regression tests for pre-parsed JSONL input path in parser stage to prevent double-parse failures.
- Validate CLI behavior against README with real Apache/Nginx/IIS logs.
- Expand IIS W3C fixture coverage (quoted fields, missing fields, field-order variance).
- Verify `event_id` continuity across all artifacts in mixed parse-success/parse-error datasets.
- Ensure local test environment includes `numpy`/`scikit-learn` or gate AI tests, so full `pytest -q` is runnable without collection failure.
- Verify collector metadata integrity in `raw_lines.jsonl` and `run_summary.json`:
  - `encoding_used`
  - `decode_error`
  - `had_bom`
  - `was_continuation_merged`
  - `physical_line_start`
  - `physical_line_end`
- Verify rule loading path behavior (`configs/rules.yaml` vs `src/rules/attack_patterns.yaml`) under operational runs.
- Validate `convert.py` on large real datasets (>1GB) for shard-size accuracy and conversion throughput.
- Validate normalizer strict validation behavior on real logs (especially `source_ip`, `http_method`, IIS timestamp strict formats) and tune false-positive rate.

## Medium Priority

- Add more parser edge tests for Apache/Nginx custom formats beyond current supported profiles.
- Evaluate non-regex/state-machine parser strategy for CLF lines with unescaped quote-heavy payloads (current regex approach has documented ambiguity limits).
- Design streaming/iterator execution path for very large logs to reduce peak RAM usage while keeping required output artifacts.
- Add schema documentation for each output artifact (required vs optional fields).
- Add small reusable sample logs under `data/sample/` for regression runs.
- Expand rule-based detection patterns carefully with deterministic tests.
- Validate `test_pipeline/run_ai_pipeline.py` with real parsed records and real `random_forest.joblib` runtime environment.
- Add regression fixture for AI test flow with stable expected prediction/probability output.
- Validate quality impact of field-group imputation (`normal_ascii_mean_by_field.json`) on real Apache/Nginx raw inputs.
- Add guard/check for stale or mismatched `normal_ascii_mean_by_field.json` against current `feature_columns.json`.

## Deferred

- TF-IDF
- n-gram
- Logistic Regression
- SVM
- Naive Bayes
- Isolation Forest
- embeddings
- vector search
- deep learning
- realtime ML inference
