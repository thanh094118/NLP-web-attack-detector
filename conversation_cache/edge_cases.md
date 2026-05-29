# Edge Cases

Phase 1 pipeline must preserve and test:

- malformed log line
- empty line
- extremely long URL
- URL with percent encoding
- double encoded payload
- path traversal payload
- SQL injection payload
- XSS payload
- command injection payload
- missing user-agent
- missing referer
- invalid HTTP method
- invalid status code
- IIS-specific field missing
- non-UTF-8 input with latin-1 fallback path
- suspicious scanner user-agent
- request containing newline-like encoded payload such as `%0a` or `%0d%0a`

Collector-specific edge cases:
- only indentation-based continuation merge (`space`/`tab`) is merged
- non-indented lines like `Injected-Header: abc` must not be merged into previous record
- valid record starts such as hostname, `::ffff:1.2.3.4`, and `-` prefix must remain separate records
- UTF-8 decode warnings should not miss errors at chunk boundaries
- warning log file should append history across runs

Parser-specific edge cases:
- Apache/Nginx unexpected trailing fields should not be silently accepted as valid Apache records
- Nginx combined format with extra trailing custom fields should parse when core fields remain intact
- Apache combined/common format with trailing custom fields should parse when core fields remain intact
- Nginx combined format with trailing spaces after user-agent should still parse as success
- Apache/Nginx request target containing unencoded spaces should parse when request still ends with valid HTTP version token
- Apache/Nginx request line without HTTP version token should parse (`http_version=None`) for HTTP/0.9-like traffic
- Apache/Nginx request target containing embedded double-quote payload should parse when full log framing (status/referrer/user-agent) remains valid
- Apache/Nginx request field containing control-marker payloads (`\n`, `\r`, `\t`, `\\n`, `\\r`, `\\t`) should be parse-error
- Apache/Nginx quote-heavy payloads without proper escaping remain an inherent regex parsing limitation if payload text mimics trailing log tokens
- Nginx logs with missing core fields or field-order mismatch should become parse-error records
- IIS quoted user-agent/referer containing spaces should parse correctly
- IIS `data_line_number` should increment only on parse-success rows (headers/comments excluded); parse-error rows should keep `data_line_number=None`
- IIS parser should reset `#Fields` state per `parse_lines()` run (no cross-file field leakage)
- IIS parser should preserve encoded query text in `raw_uri`/`original_url`; URL decoding is handled in preprocessor stage
- parser stage should not re-parse pre-parsed JSONL records (avoid treating structured JSON object text as raw Apache/Nginx/IIS line)

Invariants:
- parse-error records must keep `raw_log`, parse flags, and `error_message`
- stages should not crash on malformed/unexpected records

AI test-flow edge cases (`test_pipeline/`):
- input record missing one or more `feature_columns.json` fields must be filled (`""` for string, `0` for numeric)
- input can be single dict or list of dicts (or DataFrame-like via `to_dict(orient="records")`)
- raw collector record (`parse_status=raw`) should be pre-parsed into request/response schema before AI transforms
- empty/missing optional schema-mismatch fields should be imputed with per-field normal ASCII means
- missing core request/response fields should remain `0.0` after encoding (no normal-mean imputation)
- all fields (including numeric-looking values) should be encoded via `str(value).lower() -> mean ASCII`
- `predict_proba` may be unavailable; pipeline should still return label/prediction
- IIS raw-line parsing requires valid field context; missing `#Fields` can reduce parse completeness

Input-conversion edge cases (`convert.py`):
- `.txt`/`.log` lines already matching access-log style should be preserved as raw lines
- request-block text (`Start/End`, HTTP request-line + headers) should be converted to one synthetic access-log line
- `.csv` / `.json` / `.jsonl` structured rows should be mapped to synthetic access-log lines (drop extra fields)
- mixed-type input files should still produce one raw `.log` output
- `server_type` may need fallback from parent folder name (`apache`/`nginx`/`iis`) when content-based inference is ambiguous
- output should be written under `data/raw/<server_type>/converted_<input_stem>.log`

Normalizer-specific edge cases:
- URI containing fragment with `?` should not leak pseudo-query from fragment into `query_string`
- invalid timestamp input should output `timestamp=None` and include `timestamp_invalid` in `normalize_errors`
- malformed `source_ip` should not pass through as-is
- non-whitelisted HTTP methods should be flagged (`http_method_invalid`)
- status code outside `100..599` should be flagged (`status_code_invalid`)
- negative/invalid response size should be flagged (`response_size_invalid`)
- missing/placeholder numeric values should be distinguished from invalid values via `*_missing` and `*_invalid` flags
- missing/invalid `parse_status` should not silently become `success`
