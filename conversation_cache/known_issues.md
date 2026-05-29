# Known Issues

No confirmed critical bugs are currently known.

Areas still requiring verification:
- `event_id` continuity across all artifacts in larger real datasets.
- memory behavior on very large logs: current Phase 1 pipeline still materializes multiple stage lists in-memory (`parsed_logs`, `normalized_logs`, `preprocessed_requests`, `scored_records`).
- parser limitation: logs with unescaped `"` inside request target are inherently ambiguous under regex-based CLF parsing when payload can mimic trailing `status/size/referrer/user-agent` tokens.
- Schema stability for optional collector metadata fields across repeated runs.
- Nginx custom-format coverage beyond currently supported profiles.
- IIS parser coverage for broader real W3C variants.
- `tests/test_parser.py` currently contains some brittle expectations (iterator-only contract, exact error-message text, source-code-shape assertions) that may fail despite correct parser behavior.
- `convert.py` synthesizes access-log lines for structured/request-block sources; generated placeholder values (`source_ip`, `status_code`, `response_size`, timestamp) may not reflect true response telemetry when source data is incomplete.
- `convert.py` `server_type` folder selection is still heuristic when `--server-type` is omitted and input path has no server hint.
- normalizer now strictly validates `source_ip` as IP literal; datasets using hostname/client-id style source fields may be flagged as `source_ip_invalid`.
- `tests/test_normalizer.py` currently has assertion drift vs active `Normalizer` contract (e.g. `request_target`/`unknown` server handling, missing-vs-invalid flags, parse/normalize error semantics), causing multiple test failures even when pipeline CLI flow succeeds.
- Rule-path operational behavior when switching between `configs/rules.yaml` and `src/rules/attack_patterns.yaml`.
- `report.md` and `run_summary.json` summary consistency for mixed parse outcomes.
- `.gitignore` behavior for generated output directories in different run locations.
- AI test flow (`test_pipeline/`) with real model artifacts:
  - `random_forest.joblib` is very large and may be memory-heavy at runtime.
  - real inference requires compatible scientific stack (`numpy`/`scikit-learn`) even though unit tests use fake joblib artifacts.
  - full-repo `pytest -q` can fail at collection in environments without `numpy` because `test_pipeline/test_ai_inference_flow.py` imports it directly.
  - raw IIS lines without prior `#Fields` context may not be fully parseable by pre-parser.
  - quality depends on `normal_ascii_mean_by_field.json`; stale or domain-mismatched means may bias optional-header imputation.

Environment note:
- Shell may print `/home/thanh/miniconda3/envs/easymocap/lib/libtinfo.so.6: no version information available`; this appears environment-specific and not project logic.
