# Current Status

## Current Objective

Stabilize and validate the Phase 1 non-ML pipeline with stronger collector/parser robustness while preserving schema compatibility, while keeping any ML testing flow isolated from `src/`.

## Completed Work

- CLI/pipeline updates for output/stage control:
  - Added `--stage` option with choices: `all`, `collect`, `parser`, `normalize`, `preprocess`, `detect`, `extract`.
  - Single-stage execution is supported (`--stage parser` runs only through parser stage and writes parser artifact output).
  - Output layout now uses module folders under `--output-dir`:
    - `collector_results/`
    - `parser_results/`
    - `normalizer_results/`
    - `preprocessor_results/`
    - `detector_results/`
    - `feature_results/`
  - Output file names now include `<server_type>_<input_stem>_...` and no longer depend on `apache_run/nginx_run/iis_run` folder names.
  - Default rules path moved from `data/labels/attack_patterns.yaml` to `src/rules/attack_patterns.yaml`.
  - `--output-dir` now defaults to `outputs` (no longer required to pass explicitly).
  - `--server-type` is now optional; pipeline auto-detects server type when omitted.
  - Fixed pipeline runtime regression after parser streaming migration:
    - `run_pipeline()` now materializes `parsed_logs` with `list(parser.parse_lines(...))`
      before export/count/summary steps, preventing generator `len(...)` crash and
      generator exhaustion side-effects.
- Input conversion utility added:
  - New CLI wrapper: `convert.py`
  - Core flow: `src/converter/convert_flow.py`
  - Supports input formats: `.txt`, `.log`, `.csv`, `.json`, `.jsonl`
  - Latest behavior update: converter now outputs **raw access-log `.log`** only (no parser-stage JSONL output).
  - Conversion rule: normalize heterogeneous inputs into Apache/Nginx-like access-log lines; drop extra fields.
  - Output location: `data/raw/<server_type>/converted_<input_stem>.log`
  - Removed parser coupling in converter flow (no convert+parser inside converter).
- Normalizer hardening update completed:
  - Fixed URI split bug where query could be incorrectly extracted from fragment.
  - `normalize_status` now reflects both parser errors and normalize-time validation errors.
  - Timestamp normalization is strict and type-consistent (`ISO 8601` or `None`), no raw fallback on parse failure.
  - `COMMON_FIELDS` is now enforced for output construction and includes `event_id`.
  - Added normalize-time validation for `source_ip`, `http_method`, `status_code`, `response_size`, and `server_type`.
  - Added `normalize_errors` list and merged normalize errors into `error_message`.
  - Added forensic/helper fields: `fragment`, `decoded_uri`, `decoded_query_string`, `request_target`.
  - Added missing/invalid flags to distinguish data quality states:
    - `status_code_missing`, `status_code_invalid`
    - `response_size_missing`, `response_size_invalid`
  - `user_agent`/`referrer` empty placeholders now normalize to `None` (instead of empty string).
- Parser test-suite review completed (`tests/test_parser.py`):
  - Coverage breadth is good for parser edge cases and IIS state behaviors.
  - Identified misalignment/brittleness areas:
    - parser-callsite assumptions can drift when parser contract changes between iterator/list usage
    - some assertions lock exact error-message strings and internal implementation details (`format_profile`, `inspect.getsource`)
    - missing regression case for pre-parsed JSONL ingestion path (double-parse risk)

- Phase 1 non-ML pipeline is implemented end-to-end.
- Primary CLI entrypoint: `src/main.py`.
- Compatibility wrapper: `main.py`.
- Pipeline outputs all required artifacts:
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
- Parser hardening completed:
  - Apache/Nginx parser behavior improved for format strictness and supported profiles.
  - IIS parser improved for quoted fields containing spaces.
  - IIS `parse_lines()` now reuses `BaseParser.parse_lines()` to avoid duplicated schema/event-id logic drift.
  - IIS `data_line_number` is now derived after base parsing and increments on parse-success rows.
  - `NginxParser` now inherits from `BaseParser` (not `ApacheParser`); shared request/size helpers are centralized in `BaseParser`.
  - Error-record construction is centralized with `BaseParser._error_record(...)` to keep parser error schema consistent.
  - IIS parser state is reset per `parse_lines()` call to avoid cross-file `#Fields` leakage on parser reuse.
  - Apache/Nginx request-field validation now rejects control markers (`\n`, `\r`, `\t`, `\\n`, `\\r`, `\\t`) as parse-error.
  - Request-line parsing now accepts unencoded spaces inside `raw_uri` (still requiring trailing HTTP version token), reducing false parse-errors on SQLi-style payload logs.
  - Apache parser now supports combined/common profiles with optional trailing custom fields (same robustness class as Nginx for tail fields).
  - Apache/Nginx parser include permissive request-quote fallback to handle attack-log payloads containing `"` inside request target while still requiring status/referrer/user-agent framing.
  - Apache/Nginx request-line parser now supports no-version requests (HTTP/0.9-style) via fallback (`GET /path`).
  - Request-field forbidden markers now include tab variants (`\t`, `\\t`) in addition to newline markers.
  - IIS `data_line_number` now remains `None` for parse-error rows to avoid misleading carry-over values.
  - Apache pattern-definition convention now matches Nginx (string patterns + compile in `PROFILE_PATTERNS`) for maintainability.
  - Parser regression coverage added for:
    - Nginx combined lines with trailing spaces
    - Nginx combined-with-tail preserving referrer/user-agent fields
    - Apache/Nginx newline-marker request rejection
    - Apache/Nginx request URI containing spaces
    - Apache/Nginx request line without HTTP version
    - Nginx request containing tab marker
    - Apache combined lines with trailing custom fields
    - Apache/Nginx request target containing embedded quote payloads
    - IIS parser state reset between parse runs
    - IIS encoded query preservation at parser stage (`raw_uri` / `original_url` unchanged)
  - Apache/Nginx parser no longer forces `original_url=None` inside `parse_line`; base parser sets `original_url` only when `raw_uri` exists.
- Collector hardening completed:
  - Continuation merge is now indentation-based (`space`/`tab`) to avoid false merges.
  - UTF-8 check avoids chunk-boundary false negatives (line-level verification).
  - Warning log appends with timestamps instead of overwriting.
  - Optional collector metadata is now available in raw-stage output:
    - `encoding_used`
    - `decode_error`
    - `had_bom`
    - `was_continuation_merged`
    - `physical_line_start`
    - `physical_line_end`
  - Collector summary counters are included in `run_summary.json`.
- Event identity continuity is implemented via stable `event_id` across pipeline stages.
- `event_id` generation now supports file-scoped namespace (`source_id`) so identical line numbers/content across different files do not collide.
- Added isolated AI test flow under `test_pipeline/` using binary baseline inference artifacts:
  - `test_pipeline/ai_inference_pipeline.py`
  - `test_pipeline/ai_input_parser.py`
  - `test_pipeline/run_ai_pipeline.py`
  - `test_pipeline/pipeline_configs.yml`
  - `test_pipeline/README.md`
  - `tests/test_ai_inference_pipeline.py`
- AI test flow currently implements:
  - strict feature-column selection from `feature_columns.json`
  - pre-parser stage that converts raw collector records (`parse_status=raw`) into
    `request_*` / `response_*` schema before AI transforms
  - no separate numeric-field branch in encoding; all feature values follow train-style
    `str(value).lower() -> mean ASCII`
  - grouped missing-value handling:
    - schema-mismatch fields imputed by `normal_ascii_mean_by_field.json`
    - core fields are not imputed by normal means (remain `0.0` when missing)
  - `log1p` transform
  - `scaler.transform(...)`
  - `model.predict(...)` with `label_mapping.json` (`0=Normal`, `1=Attack`)
  - optional `predict_proba(...)` extraction (`normal_probability`, `attack_probability`)
  - config-driven runtime (paths/params in YAML), CLI now only requires `--input`
  - default output under `outputs/` using `{input_stem}_ai_predictions.jsonl`
  - additional debug output under `outputs/` using `{input_stem}_ai_preparsed.jsonl`
    that stores pre-parsed `request_*` / `response_*` records used before AI transforms

## Blockers

- No critical blocker confirmed.
- Real-world IIS/W3C variant coverage still needs broader validation data.
- End-to-end runtime validation with the real `test_pipeline/random_forest.joblib` model is still environment-dependent (requires compatible ML runtime stack).

## Next Recommended Step

Validate on more real logs (Apache/Nginx/IIS custom formats), then tighten schema documentation and rule coverage.

## Files Modified

- `src/collector/read_flow.py`
- `src/collector/file_collector.py`
- `src/collector/collect_flow.py`
- `src/main.py`
- `convert.py`
- `src/converter/__init__.py`
- `src/converter/convert_flow.py`
- `src/parser/base_parser.py`
- `src/parser/apache_parser.py`
- `src/parser/nginx_parser.py`
- `src/parser/iis_parser.py`
- `src/normalizer/normalizer.py`
- `src/preprocessor/request_preprocessor.py`
- `src/detection/rule_detector.py`
- `test_pipeline/__init__.py`
- `test_pipeline/ai_inference_pipeline.py`
- `test_pipeline/ai_input_parser.py`
- `test_pipeline/run_ai_pipeline.py`
- `test_pipeline/pipeline_configs.yml`
- `test_pipeline/README.md`
- `tests/test_collector.py`
- `tests/test_parser.py`
- `tests/test_normalizer.py`
- `tests/test_preprocessor.py`
- `tests/test_rules.py`
- `tests/test_pipeline.py`
- `tests/test_convert.py`
- `tests/test_ai_inference_pipeline.py`

## Checks Run / Skipped

- Ran: `pytest -q tests/test_pipeline.py tests/test_collector.py tests/test_parser.py tests/test_normalizer.py tests/test_preprocessor.py tests/test_rules.py`
  - result: failed (18 failures, all in `tests/test_normalizer.py`; other selected suites passed)
- Ran: `pytest -q tests/test_pipeline.py` (passed: 1 test)
- Ran manual CLI smoke test:
  - `python -m src.main --input <tmp>/access.log --output-dir <tmp>/out --rules src/rules/attack_patterns.yaml`
  - result: pipeline finished, counts printed, and all expected stage artifacts generated
- Ran: `pytest -q tests/test_convert.py tests/test_pipeline.py` (passed: 5 tests)
- Ran: `python convert.py --input data/input/cisc_anomalousTraffic_test.txt`
  - result: `Raw lines: 25065`
  - output: `data/raw/apache/converted_cisc_anomalousTraffic_test.log`
- Ran: `pytest -q tests/test_parser.py` (passed: 27 tests)
- Ran: `pytest -q tests/test_pipeline.py` (passed: 1 test)
- Ran: `pytest -q tests` (passed: 69 tests)
- Ran: `pytest -q tests/test_convert.py tests/test_pipeline.py tests/test_rules.py` (passed: 10 tests)
- Ran: `pytest -q tests/test_collector.py tests/test_parser.py tests/test_normalizer.py tests/test_preprocessor.py tests/test_features.py tests/test_rules.py tests/test_scoring.py tests/test_pipeline.py tests/test_exporters_reporting.py tests/test_convert.py` (passed: 73 tests)
- Ran: `pytest -q tests/test_convert.py` (passed: 8 tests)
- Ran demo command:
  - `python -m src.main --input data/raw/nginx/sqli_access.log --server-type nginx --output-dir outputs/nginx_run --rules data/labels/attack_patterns.yaml`
  - result: `Parse errors: 0` (previously 7)
- Ran demo command:
  - `python -m src.main --input data/raw/apache/xss_access.log --server-type apache --output-dir outputs/apache_run --rules data/labels/attack_patterns.yaml`
  - result: `Parse errors: 0` (previously 11)
- Note: request payloads containing unescaped `"` remain fundamentally ambiguous in regex-based CLF parsing when payload text mimics trailing log tokens; this is documented as a known limitation.
- Attempted: `pytest -q` (failed during collection at `test_pipeline/test_ai_inference_flow.py` because `numpy` is missing in current environment)
- Rule-based Phase 1 pipeline remains unchanged in `src/`; AI flow is isolated in `test_pipeline/` for explicit ML testing requests only.
- Preprocessor overwrite-policy updated:
  - `decoded_uri` and `decoded_query_string` are now allowed as pre-existing fields (no overwrite error/warning).
  - overwrite warnings are still emitted when pre-existing `normalized_*`, `preprocess_*`, or `decode_depth_*`/related metadata fields are present.
- Ran: `pytest -q tests/test_preprocessor.py tests/test_pipeline.py` (passed: 20 tests)
- Normalizer/Preprocessor field-ownership adjustment:
  - `decoded_uri` and `decoded_query_string` were removed from Normalizer output schema.
  - Decode ownership is now Preprocessor-only for these fields.
  - Preprocessor accepts pre-existing `decoded_uri`/`decoded_query_string` without overwrite-error, but still warns on pre-existing `normalized_*`, `preprocess_*`, and `decode_depth_*` metadata fields.
- Ran: `pytest -q tests/test_normalizer.py tests/test_preprocessor.py tests/test_pipeline.py` (passed: 102 tests)
- Added pipeline stage `all_feature`:
  - Runs collector -> parser -> normalizer -> preprocessor -> feature extractor.
  - Does not run detector/risk scoring and does not emit alerts artifacts.
  - Emits `feature_results/<server>_<input>_features.csv` and returns counts with `alerts=0`.
- Ran: `pytest -q tests/test_pipeline.py tests/test_preprocessor.py` (passed: 21 tests)
- Updated `requirements.txt` to include full runtime/test dependencies used by repo codepaths:
  - core: `pyyaml`, `python-dateutil`
  - tests: `pytest`
  - isolated AI test flow: `joblib`, `numpy`, `pandas`, `scikit-learn`
- Packaging/dependency update:
  - Added `setup.py` with core install requirements (`pyyaml`, `python-dateutil`, `gdown`).
  - Added extras: `dev` (`pytest`) and `ai-test` (`joblib`, `numpy`, `pandas`, `scikit-learn`).
  - Declared Python compatibility in setup metadata: `>=3.10,<3.13`.
  - Updated `requirements.txt` to include `gdown`.
