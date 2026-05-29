# Decisions

## 2026-05-25 - Establish Agent Memory Files

Decision: Use `AGENTS.md` for stable long-term repository instructions and `conversation_cache/` for mutable session/project memory.

Reason: Future autonomous coding-agent sessions need a consistent startup and persistence workflow without mixing temporary session logs into stable instructions.

Tradeoffs / impact: Adds maintenance overhead, but keeps source code authoritative and gives agents a clear place to update current state.

## 2026-05-25 - Treat Pipeline Outputs As Generated Artifacts

Decision: Treat `outputs/`, `data/processed/`, caches, and model artifacts as generated/local data.

Reason: Pipeline runs overwrite generated outputs and may use local-only data.

Tradeoffs / impact: Agents must run smoke checks carefully, but this avoids accidental churn/loss of generated evidence.

## 2026-05-26 - Keep Package-Based Architecture

Decision: Keep the current package-based architecture as the accepted convention.

Reason: Phase 1 baseline is already implemented and testable in package form.

Tradeoffs / impact: Limits ad-hoc restructuring but improves maintainability and module isolation.

## 2026-05-26 - Do Not Revert To Single-File Module Layout

Decision: Do not recreate old single-file modules such as `src/parser.py`, `src/scoring.py`, `src/exporter.py`, or `src/report.py`.

Reason: Reverting would create architectural drift and duplicate logic.

Tradeoffs / impact: Requires future contributors to follow package boundaries consistently.

## 2026-05-26 - Malformed Logs Are First-Class Records

Decision: Treat malformed log lines as first-class records instead of dropping them.

Reason: Security analysis needs traceability and failure visibility.

Tradeoffs / impact: Some downstream artifacts contain parse-error rows by design.

## 2026-05-26 - Preserve Raw Log And Original URL

Decision: Preserve original request evidence fields (`raw_log`, original URL field) across stages where applicable.

Reason: Investigation and forensic workflows require original request context.

Tradeoffs / impact: Schema must explicitly carry these fields across artifacts.

## 2026-05-26 - JSONL For Intermediate Artifacts

Decision: Use JSONL for intermediate stage outputs.

Reason: JSONL keeps per-record structure and is robust for incremental processing.

Tradeoffs / impact: Less spreadsheet-friendly than CSV, but better for structured pipelines.

## 2026-05-26 - CSV For Table Exports And Future Dataset Prep

Decision: Use CSV for table-style exports (`normalized_logs.csv`, `features.csv`, `alerts.csv`) and future ML dataset preparation.

Reason: CSV is simple for analysis and tooling interoperability.

Tradeoffs / impact: Nested fields must be flattened/serialized.

## 2026-05-26 - Report Outputs For Human And Machine Summary

Decision: Keep both `report.md` (human-readable) and `run_summary.json` (machine-readable).

Reason: Security operations and automation need different summary formats.

Tradeoffs / impact: Requires summary consistency checks across both outputs.

## 2026-05-26 - Keep Phase 2 ML Separate From Phase 1 Pipeline

Decision: Defer Phase 2 ML work until explicitly requested.

Reason: Current priority is Phase 1 stability, validation, schema consistency, and rule-based baseline quality.

Tradeoffs / impact: ML capabilities are intentionally unavailable in current scope.

## 2026-05-26 - Collector Continuation Merge Uses Indentation-Only Rule

Decision: Merge continuation lines only when a physical line starts with space or tab.

Reason: Previous character-class heuristic could merge valid new records (`hostname`, `::ffff:x.x.x.x`, `-` prefixes, header-like lines) and corrupt record boundaries.

Tradeoffs / impact: This conservative rule reduces false merges but will not catch all newline-injection continuations that do not start with indentation.

## 2026-05-26 - Collector Metadata And Warning Durability

Decision: Add optional collector provenance metadata to raw-stage records and append warning logs with timestamps.

Reason: Phase 1 needs traceability for decode behavior and merge behavior without breaking existing schema consumers.

Tradeoffs / impact: Raw-stage artifacts now include extra optional fields; downstream compatibility is preserved because existing fields are unchanged.

## 2026-05-28 - Keep AI Baseline Inference Flow Isolated In test_pipeline

Decision: Implement requested binary baseline AI inference as a separate `test_pipeline/` flow and do not integrate into Phase 1 `src/` pipeline.

Reason: Repository baseline remains Phase 1 non-ML for production path, while explicit user request requires an ML test flow.

Tradeoffs / impact: Maintains Phase 1 stability and architecture, but introduces separate ML-runtime dependencies when running real joblib model artifacts.

## 2026-05-28 - Use YAML Config For AI Test CLI

Decision: Store AI test pipeline paths/runtime parameters in `test_pipeline/pipeline_configs.yml` and keep CLI input minimal (`--input` required, `--config` optional).

Reason: Avoid long command lines and centralize model/scaler/output settings for repeatable runs.

Tradeoffs / impact: Adds one config file to maintain, but makes execution simpler and reduces argument drift.

## 2026-05-28 - Add Raw-to-AI Pre-Parser Stage

Decision: Add `test_pipeline/ai_input_parser.py` and run it before AI inference transforms.

Reason: AI flow input may be collector raw records (`parse_status=raw`) and must be converted to
`request_*` / `response_*` fields expected by `feature_columns.json`.

Tradeoffs / impact: Supports direct raw-log JSONL inference with less user preprocessing, but relies on
server-type parsers and may have limited coverage for incomplete IIS context lines.

## 2026-05-28 - Emit Pre-Parsed Debug Artifact In AI CLI

Decision: `test_pipeline/run_ai_pipeline.py` now writes both prediction output and
pre-parsed debug output (`{input_stem}_ai_preparsed.jsonl`) to the configured output directory.

Reason: Easier debugging/validation of the raw-to-AI parsing stage before encode/scale/predict steps.

Tradeoffs / impact: Adds one more generated file per run, but improves traceability for inference issues.

## 2026-05-28 - Field-Group Imputation With Normal ASCII Means

Decision: Add grouped missing-field behavior in AI encoding:
- fields in schema-mismatch group are imputed by `normal_ascii_mean_by_field.json`
- core request/response fields are not imputed by normal means when missing.

Reason: Apache/Nginx combined logs omit many SR-BH training headers; treating all missing values as empty could over-bias vectors toward a missing-pattern.

Tradeoffs / impact: Better alignment with training distribution for optional headers, while preserving visibility of parser/core-field anomalies.

## 2026-05-28 - Remove Separate Numeric-Field Encoding Branch

Decision: In AI encoding step, do not treat numeric columns separately; use training-compatible flow for all fields:
`value -> str(value).lower() -> mean ASCII`.

Reason: Keep inference preprocessing behavior aligned with training notebook assumptions.

Tradeoffs / impact: Numeric semantics are intentionally discarded in favor of strict compatibility with the trained preprocessing pipeline.

## 2026-05-29 - IIS Parser parse_lines Must Reuse BaseParser

Decision: Refactor `IISParser.parse_lines()` to call `BaseParser.parse_lines()` and only append IIS-specific `data_line_number`.

Reason: Avoid duplicated parse-status/event-id/schema logic drift and preserve central behavior in `BaseParser`.

Tradeoffs / impact: `data_line_number` semantics are explicit and easier to maintain; any base parser field changes now propagate to IIS automatically.

## 2026-05-29 - Keep URL Decoding Out Of Parser Stage

Decision: Keep IIS parser `raw_uri`/`original_url` as raw encoded values; do not decode `%xx` or `+` in parser.

Reason: Parser stage should preserve original request evidence, while URL decoding is already handled in preprocessor (`unquote_plus` flow).

Tradeoffs / impact: Parser output may contain encoded query text by design; downstream normalization/preprocessing remains responsible for decoded view.

## 2026-05-29 - Decouple Nginx Parser From Apache Inheritance

Decision: Make `NginxParser` inherit directly from `BaseParser` and move shared request/response-size helpers to base class.

Reason: Avoid unintended Apache-specific inheritance coupling while still reusing common Combined Log parsing helpers.

Tradeoffs / impact: Cleaner parser boundaries; shared logic now has one source of truth in `BaseParser`.

## 2026-05-29 - Centralize Parser Error Record Shape

Decision: Add `BaseParser._error_record(...)` and use it across Apache/Nginx/IIS parse-error returns.

Reason: Remove repeated hand-written error dicts and reduce schema drift risk when parser fields evolve.

Tradeoffs / impact: Lower maintenance cost; error schema consistency is now easier to enforce via tests.

## 2026-05-29 - Enforce Newline Marker Rejection In Request Field

Decision: Treat request fields containing newline markers (`\n`, `\r`, `\\n`, `\\r`) as parse errors in Apache/Nginx parsers.

Reason: Harden parser against newline-injection-like payloads that can otherwise pass request regex.

Tradeoffs / impact: Very uncommon raw requests containing these markers are flagged as parse-error by design.

## 2026-05-29 - Add File-Scoped Namespace To event_id In Pipeline Runs

Decision: Include a file-derived `source_id` namespace when building `event_id` for raw and parsed records during `run_pipeline`.

Reason: Prevent guaranteed cross-file collisions for identical `server_type`, `line_number`, and line content.

Tradeoffs / impact: `event_id` format may include an extra segment in pipeline outputs; continuity across pipeline stages is preserved.

## 2026-05-29 - Accept Unencoded Spaces In Request URI For Parser Robustness

Decision: Relax request-line parsing to allow spaces in `raw_uri` as long as the trailing HTTP version token remains present.

Reason: Real attack corpora (e.g., SQLi samples) may include unencoded spaces in request target text; strict `\S+` URI parsing caused false parse-errors and dropped attack context from structured fields.

Tradeoffs / impact: Parser is less RFC-strict but more robust for forensic/security datasets; newline-marker rejection remains in place.

## 2026-05-29 - Add Apache Tail Profile Support And Request-Quote Fallback

Decision: Extend Apache parser to support combined/common logs with optional trailing custom fields, and add permissive fallback patterns that tolerate embedded `"` characters inside request target.

Reason: Real attack datasets (`xss_access.log`) contained Apache lines with tail fields and quote-heavy payloads that strict `[^"]*` request matching could not parse.

Tradeoffs / impact: Parser accepts more malformed-but-security-relevant traffic for analysis; strictness is traded for better forensic coverage while keeping request-line post-validation and newline-marker rejection.

## 2026-05-29 - Support Request Lines Without HTTP Version

Decision: Add request parsing fallback for lines like `GET /path` with missing HTTP version token, setting `http_version=None`.

## 2026-05-29 - Use resolved_server_type As Single Runtime Truth

Decision: Remove dual-truth behavior between parser class constant (`server_type`) and runtime-selected server type by injecting `resolved_server_type` into `BaseParser`.

Reason: Pipeline now supports optional server auto-detection; all artifacts must consistently reflect one resolved runtime type across collector/parser/output naming/event_id.

Tradeoffs / impact: Parser classes still keep default `server_type` for standalone/parser-unit usage, but pipeline runtime overrides with `set_resolved_server_type(...)` to guarantee consistency.

## 2026-05-29 - Add convert.py For Multi-Format Input Canonicalization

Decision: Add `convert.py` (wrapper) + `src/converter/convert_flow.py` to convert `.txt`, `.csv`, `.json`, `.jsonl` into canonical JSONL outputs under `data/collected` or `data/parsered`, with optional shard splitting by size.

Reason: Real-world input sources are heterogeneous and often large; pipeline preparation needs a deterministic conversion step before Phase 1 processing.

Tradeoffs / impact: Additional pre-processing path introduces format-detection heuristics (`collected` vs `parsered`), which favor non-dropping conversion and may classify ambiguous records conservatively as `collected`.

## 2026-05-29 - Add Hierarchical server_type Detection In convert.py

Decision: Use layered `server_type` detection in converter records:
`--server-type` override > explicit record field > IIS schema markers > raw-line parser inference > input-path hint (`apache|nginx|iis`) > `unknown`.

Reason: Input data often lacks explicit `server_type`; Apache and Nginx combined-log lines are structurally similar and require deterministic fallback behavior.

Tradeoffs / impact: Detection remains heuristic for some ambiguous records, but folder-hint fallback reduces frequent `unknown` labels and wrong Apache/Nginx assignments in practical datasets.

## 2026-05-29 - Convert HTTP Request Blocks To parsered Records

Decision: Treat text blocks containing HTTP request-lines (`METHOD URI HTTP/x`) and headers as `parsered` records during conversion, including `Start - Id ... End - Id` wrappers.

Reason: These inputs are not CLF/W3C access-log lines; keeping them as raw collected lines causes parser stage failures and no usable structured output.

Tradeoffs / impact: Converter now performs lightweight request-block extraction (`http_method`, `raw_uri`, `http_version`, selected headers). Status/size remain default when absent in source.

## 2026-05-29 - Strengthen Normalizer Validation And Error Model

Decision: Refactor `src/normalizer/normalizer.py` to apply strict field validation, preserve normalization diagnostics, and enforce a stable declared schema via `COMMON_FIELDS`.

Reason: Existing behavior hid normalize-time failures (timestamp parsing, invalid method/IP/range values), mixed timestamp types, and did not separate missing vs invalid numeric values.

Tradeoffs / impact: More records can be marked `normalize_status=error` for invalid field values; however, output quality and forensic traceability improve via `normalize_errors`, normalized status flags, and consistent timestamp typing.

## 2026-05-29 - Parser Tests Should Prioritize Behavioral Contracts

Decision: Keep parser tests focused on externally observable behavior/schema invariants and avoid over-coupling to non-contract internals (exact source-code structure or optional internal profiling fields).

Reason: Internal refactors should not break tests when parser output contract remains valid.

Tradeoffs / impact: Tests become less brittle and better at catching true regressions, while still keeping explicit checks for schema and parse-error semantics.

Reason: Some scanners and HTTP/0.9-like traffic omit version and should not be forced into parse-error when method/target remain extractable.

Tradeoffs / impact: Request parser is more tolerant; malformed request lines that still contain HTTP version token but extra trailing garbage remain parse-error.

## 2026-05-29 - Keep `data_line_number` Null For IIS Error Rows

Decision: In `IISParser.parse_lines()`, assign `data_line_number` only on parse-success rows and use `None` for parse-error rows.

Reason: Carrying forward the previous success index into error rows is misleading during debugging and analysis.

Tradeoffs / impact: Clearer semantics for IIS line indexing; minor schema behavior change for error rows.

## 2026-05-29 - Document Quote Ambiguity As Known Parser Limitation

Decision: Explicitly document that unescaped double-quotes inside request payloads can remain ambiguous for regex-based CLF parsing if payload mimics trailing log tokens.

Reason: This cannot be fully resolved by regex tuning alone without stricter upstream escaping or parser grammar changes.

Tradeoffs / impact: Sets correct expectation for edge-case behavior; avoids overfitting fragile regex heuristics.

## 2026-05-29 - Materialize Parser Iterator In run_pipeline Before Counting/Summary

Decision: Keep `BaseParser.parse_lines()` as streaming iterator, but convert to list in `run_pipeline()` immediately after parser stage.

Reason: Pipeline stage/export/summary logic requires multi-pass access (`export`, `len(...)`, downstream transform loops). Using raw generator caused runtime `TypeError` and exhaustion side-effects.

Tradeoffs / impact: `run_pipeline()` uses more memory for parsed stage (already acceptable in current Phase 1 list-based flow), while preserving iterator contract for parser unit-level usage.

## 2026-05-29 - Simplify Converter To Single parser_results Output

Decision: Simplify `src/converter/convert_flow.py` so converter always emits parser-stage JSONL under `parser_results`, regardless of whether input is raw logs or parsered logs.

Reason: Reduce split-flow complexity (`collected` vs `parsered` output trees) and align converted artifacts directly with parser-module contract.

Tradeoffs / impact: Removed output-size shard option (`--max-file-size-mb`); converter no longer generates separate `data/collected` outputs.

## 2026-05-29 - Parse HTTP Request-Block Corpora As Structured Parser Records

Decision: In converter flow, detect request-block style payloads (`Start/End`, HTTP request line + headers) and map them directly into parser-stage success records instead of forcing CLF parser regex.

Reason: Security corpora like CIC-style anomalous traffic are HTTP request traces, not Apache/Nginx access-log lines; CLF parsing creates near-100% parse-error noise.

Tradeoffs / impact: `status_code`/`response_size` default to `0` when absent in source block, but request semantics (`http_method`, `raw_uri`, `http_version`, headers) are preserved for downstream normalization/detection.

## 2026-05-29 - Revert Converter To Raw Access-Log Output Only

Decision: Redesign `src/converter/convert_flow.py` to output only raw `.log` files under `data/raw/<server_type>/`, and remove converter-side parser-stage JSONL output.

Reason: Keep converter responsibility focused on input normalization to raw logs; parsing should remain in the main pipeline parser module.

Tradeoffs / impact: Structured/request-block datasets are converted into synthetic access-log lines with placeholder defaults for missing response fields.

## 2026-05-29 - Allow Shared decoded_* Fields Between Normalizer And Preprocessor

Decision: Treat `decoded_uri` and `decoded_query_string` as shared upstream fields; Preprocessor may reuse/overwrite them without raising overwrite warning/error.

Reason: These decoded fields are part of Normalizer output contract and are no longer exclusive to Preprocessor.

Tradeoffs / impact: Overwrite warnings remain active for `normalized_*`, `preprocess_*`, and `decode_depth_*`/related metadata, preserving double-preprocess detection where it matters.

## 2026-05-29 - Move decoded_uri/decoded_query_string Ownership To Preprocessor

Decision: Remove `decoded_uri` and `decoded_query_string` from Normalizer output schema and keep these fields owned by Preprocessor.

Reason: Decode semantics belong to request preprocessing; keeping decoded fields in both modules creates overlap and overwrite noise.

Tradeoffs / impact: Consumers needing decoded URI/query should read from preprocessor-stage artifacts, not normalizer-stage artifacts.

## 2026-05-29 - Add all_feature Stage For Feature-Only Flow

Decision: Add CLI stage `all_feature` to execute up to feature extraction without invoking detector/risk scoring.

Reason: Some workflows need deterministic feature output only and should not produce alert artifacts.

Tradeoffs / impact: `all_feature` emits feature CSV and returns `alerts=0`; no detector outputs are generated in this mode.

## 2026-05-29 - Add setup.py And Align Dependency Metadata

Decision: Add `setup.py` for package installation metadata, include `gdown` as core dependency, and define Python compatibility range.

Reason: Ensure reproducible installation path beyond raw `requirements.txt`, and satisfy data-download dependency needs.

Tradeoffs / impact: Runtime dependency surface increases slightly (`gdown`), while test/AI dependencies remain optional via extras.
