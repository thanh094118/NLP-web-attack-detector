from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional

SERVER_TYPE_CHOICES = ("apache", "nginx", "iis")
_REQUEST_LINE_PATTERN = re.compile(r"^(?P<method>[A-Z]{2,16})\s+(?P<target>\S.*?)(?:\s+(?P<version>HTTP/\d(?:\.\d)?))?$")
_START_BLOCK_PATTERN = re.compile(r"^Start\s*-\s*Id\s*:\s*.+$", re.IGNORECASE)
_END_BLOCK_PATTERN = re.compile(r"^End\s*-\s*Id\s*:\s*.+$", re.IGNORECASE)

_URI_KEYS = ("raw_uri", "original_url", "uri", "url", "uri_path", "path", "request_uri", "cs_uri_stem")
_QUERY_KEYS = ("query_string", "query", "cs_uri_query")
_METHOD_KEYS = ("http_method", "method", "verb", "cs_method")
_STATUS_KEYS = ("status_code", "status", "http_status", "response_status", "sc_status")
_SIZE_KEYS = ("response_size", "bytes", "size", "content_length", "response_content_length", "sc_bytes")
_SOURCE_IP_KEYS = ("source_ip", "ip", "client_ip", "remote_addr", "c_ip")
_UA_KEYS = ("user_agent", "ua", "cs_user_agent")
_REFERRER_KEYS = ("referrer", "referer", "cs_referer")
_HTTP_VERSION_KEYS = ("http_version", "protocol", "request_protocol")
_TIMESTAMP_KEYS = ("timestamp", "time", "date_time", "datetime", "@timestamp", "date")


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert heterogeneous inputs (.txt/.log/.csv/.json/.jsonl) to raw access.log lines"
    )
    parser.add_argument("--input", required=True, help="Input file path (.txt, .log, .csv, .json, .jsonl)")
    parser.add_argument(
        "--output-root",
        default="data/raw",
        help="Output root directory for .log files (default: data/raw)",
    )
    parser.add_argument(
        "--server-type",
        choices=SERVER_TYPE_CHOICES,
        default=None,
        help="Optional server_type override for output folder naming",
    )
    return parser


def main() -> None:
    args = build_cli().parse_args()
    summary = convert_file(
        input_path=args.input,
        output_root=args.output_root,
        server_type=args.server_type,
    )

    print("[+] Conversion finished")
    print(f"[+] Input file: {summary['input_path']}")
    print(f"[+] Server type: {summary['server_type']}")
    print(f"[+] Raw lines: {summary['counts']['raw_lines']}")
    print(f"[+] Output file: {summary['output']}")


def convert_file(
    *,
    input_path: str | Path,
    output_root: str | Path = "data/raw",
    server_type: Optional[str] = None,
) -> Dict[str, Any]:
    source_path = Path(input_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Input file not found: {source_path}")
    if not source_path.is_file():
        raise ValueError(f"Input path is not a file: {source_path}")

    items = list(_iter_input_items(source_path))
    resolved_server_type = server_type or _detect_server_type_from_path(source_path) or "apache"
    resolved_server_type = resolved_server_type.lower()

    raw_lines: List[str] = []
    for item in items:
        for line in _to_raw_log_lines(item):
            if line.strip():
                raw_lines.append(line.strip())

    output_root_path = Path(output_root)
    output_dir = output_root_path / resolved_server_type
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"converted_{source_path.stem}.log"
    output_path.write_text("\n".join(raw_lines) + ("\n" if raw_lines else ""), encoding="utf-8")

    return {
        "input_path": str(source_path),
        "server_type": resolved_server_type,
        "counts": {"raw_lines": len(raw_lines)},
        "output": str(output_path),
    }


def _iter_input_items(path: Path) -> Iterator[Any]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".log"}:
        yield from _iter_text_entries(path)
        return
    if suffix == ".csv":
        yield from _iter_csv_rows(path)
        return
    if suffix in {".json", ".jsonl"}:
        yield from _iter_json_rows(path)
        return
    raise ValueError(f"Unsupported input extension: {suffix}. Supported: .txt, .log, .csv, .json, .jsonl")


def _iter_text_entries(path: Path) -> Iterator[str]:
    mode: Optional[str] = None
    current_block: List[str] = []
    is_first_line = True

    with path.open("rb") as handle:
        for raw_line in handle:
            if is_first_line and raw_line.startswith(b"\xef\xbb\xbf"):
                raw_line = raw_line[3:]
            is_first_line = False

            try:
                line = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                line = raw_line.decode("latin-1")

            line = line.rstrip("\r\n")

            if mode == "block":
                if line.strip():
                    current_block.append(line)
                if _is_end_block_line(line):
                    yield "\\n".join(current_block)
                    current_block = []
                    mode = None
                continue

            if mode == "request":
                if _is_start_block_line(line):
                    if current_block:
                        yield "\\n".join(current_block)
                    current_block = [line]
                    mode = "block"
                    continue

                if _is_request_line(line) and current_block:
                    yield "\\n".join(current_block)
                    current_block = [line]
                    mode = "request"
                    continue

                if not line.strip():
                    if current_block:
                        yield "\\n".join(current_block)
                    current_block = []
                    mode = None
                    continue

                current_block.append(line)
                continue

            if not line.strip():
                continue

            if _is_start_block_line(line):
                current_block = [line]
                mode = "block"
                continue

            if _is_request_line(line):
                current_block = [line]
                mode = "request"
                continue

            yield line

    if current_block:
        yield "\\n".join(current_block)


def _iter_csv_rows(path: Path) -> Iterator[Dict[str, Any]]:
    errors: List[Exception] = []
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    return
                for row in reader:
                    yield {str(k): v for k, v in row.items()}
            return
        except (UnicodeDecodeError, csv.Error) as exc:
            errors.append(exc)
    if errors:
        raise ValueError(f"Cannot parse CSV input: {path}") from errors[-1]


def _iter_json_rows(path: Path) -> Iterator[Any]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                text = line.strip()
                if text:
                    yield json.loads(text)
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        for item in data:
            yield item
        return

    if isinstance(data, dict):
        records = data.get("records")
        if isinstance(records, list):
            for item in records:
                yield item
            return
        yield data
        return

    yield {"value": data}


def _to_raw_log_lines(item: Any) -> List[str]:
    if isinstance(item, str):
        return _from_text_item(item)

    if isinstance(item, Mapping):
        return [_from_mapping_item(item)]

    return [str(item)]


def _from_text_item(text: str) -> List[str]:
    clean = str(text).strip()
    if not clean:
        return []

    if _looks_like_access_log(clean):
        return [clean]

    block = _parse_http_request_block(clean)
    if block is not None:
        return [_build_access_log_line(block)]

    request_line = _extract_request_line(clean)
    if request_line is not None:
        method, target, version = _split_request_line(request_line)
        return [_build_access_log_line({
            "http_method": method,
            "raw_uri": target,
            "http_version": version,
            "user_agent": "-",
            "referrer": "-",
        })]

    return [clean]


def _from_mapping_item(item: Mapping[str, Any]) -> str:
    normalized = _normalize_keys(item)

    if "raw_line" in normalized and isinstance(normalized.get("raw_line"), str):
        raw_line = str(normalized.get("raw_line") or "").strip()
        if _looks_like_access_log(raw_line):
            return raw_line

    request_block = _pick_text(normalized, "raw_log", "raw_line", "line", "message")
    block_parsed = _parse_http_request_block(request_block) if request_block else None

    uri = _pick_text(normalized, *_URI_KEYS)
    query = _pick_text(normalized, *_QUERY_KEYS)
    if uri and query and "?" not in uri:
        uri = f"{uri}?{query}"

    method = _pick_text(normalized, *_METHOD_KEYS)
    http_version = _pick_text(normalized, *_HTTP_VERSION_KEYS)
    if not http_version:
        http_version = "HTTP/1.1"

    payload = {
        "source_ip": _pick_text(normalized, *_SOURCE_IP_KEYS) or "0.0.0.0",
        "timestamp": _pick_text(normalized, *_TIMESTAMP_KEYS),
        "http_method": method or (block_parsed or {}).get("http_method") or "GET",
        "raw_uri": uri or (block_parsed or {}).get("raw_uri") or "/",
        "http_version": http_version or (block_parsed or {}).get("http_version") or "HTTP/1.1",
        "status_code": _pick_int(normalized, *_STATUS_KEYS, default=200),
        "response_size": _pick_int(normalized, *_SIZE_KEYS, default=0),
        "referrer": _pick_text(normalized, *_REFERRER_KEYS) or (block_parsed or {}).get("referrer") or "-",
        "user_agent": _pick_text(normalized, *_UA_KEYS) or (block_parsed or {}).get("user_agent") or "-",
    }

    return _build_access_log_line(payload)


def _build_access_log_line(payload: Mapping[str, Any]) -> str:
    source_ip = str(payload.get("source_ip") or "0.0.0.0").strip() or "0.0.0.0"
    timestamp = _to_apache_timestamp(payload.get("timestamp"))
    method = str(payload.get("http_method") or "GET").strip().upper() or "GET"
    raw_uri = str(payload.get("raw_uri") or "/").strip() or "/"
    http_version = str(payload.get("http_version") or "HTTP/1.1").strip() or "HTTP/1.1"
    status_code = _to_int(payload.get("status_code"), default=200)
    response_size = _to_int(payload.get("response_size"), default=0)
    referrer = _escape_quoted(str(payload.get("referrer") or "-"))
    user_agent = _escape_quoted(str(payload.get("user_agent") or "-"))

    request = f"{method} {raw_uri} {http_version}".strip()
    request = _escape_quoted(request)

    return f'{source_ip} - - [{timestamp}] "{request}" {status_code} {response_size} "{referrer}" "{user_agent}"'


def _to_apache_timestamp(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "-":
        return datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S %z")

    formats = (
        "%d/%b/%Y:%H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
    )
    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%d/%b/%Y:%H:%M:%S %z")
        except ValueError:
            continue

    return datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S %z")


def _escape_quoted(value: str) -> str:
    return value.replace('"', '\\"')


def _looks_like_access_log(text: str) -> bool:
    return bool(re.match(r'^\S+\s+\S+\s+\S+\s+\[[^\]]+\]\s+".*"\s+\d{3}\s+\S+', text))


def _parse_http_request_block(raw_block: str) -> Optional[Dict[str, Any]]:
    request_line = _extract_request_line(raw_block)
    if not request_line:
        return None

    method, target, version = _split_request_line(request_line)
    headers = _extract_headers(raw_block, request_line)

    return {
        "http_method": method,
        "raw_uri": target,
        "http_version": version,
        "user_agent": headers.get("user-agent") or "-",
        "referrer": headers.get("referer") or headers.get("referrer") or "-",
        "source_ip": headers.get("x-forwarded-for") or "0.0.0.0",
        "status_code": 200,
        "response_size": 0,
    }


def _extract_headers(raw_block: str, request_line: str) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    request_seen = False
    for line in str(raw_block).split("\\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if not request_seen:
            if stripped == request_line:
                request_seen = True
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


def _extract_request_line(value: str) -> Optional[str]:
    for line in str(value).split("\\n"):
        candidate = line.strip()
        if _is_request_line(candidate):
            return candidate
    return None


def _split_request_line(request_line: str) -> tuple[str, str, str]:
    match = _REQUEST_LINE_PATTERN.match(request_line.strip())
    if not match:
        return "GET", "/", "HTTP/1.1"
    method = match.group("method")
    target = match.group("target")
    version = match.group("version") or "HTTP/1.1"
    return method, target, version


def _is_start_block_line(line: str) -> bool:
    return bool(_START_BLOCK_PATTERN.match(line.strip()))


def _is_end_block_line(line: str) -> bool:
    return bool(_END_BLOCK_PATTERN.match(line.strip()))


def _is_request_line(line: str) -> bool:
    return bool(_REQUEST_LINE_PATTERN.match(line.strip()))


def _detect_server_type_from_path(input_path: Path) -> Optional[str]:
    for segment in input_path.parts:
        name = str(segment).strip().lower()
        if name in SERVER_TYPE_CHOICES:
            return name
    return None


def _normalize_keys(record: Mapping[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in record.items():
        text = str(key).strip().strip('"').strip("'").lower()
        text = text.replace("-", "_").replace(" ", "_")
        text = text.replace("(", "_").replace(")", "")
        while "__" in text:
            text = text.replace("__", "_")
        normalized[text] = value
    return normalized


def _pick_value(record: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in record:
            value = record[key]
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            return value
    return None


def _pick_text(record: Mapping[str, Any], *keys: str) -> str:
    value = _pick_value(record, *keys)
    if value is None:
        return ""
    text = str(value).strip()
    if text == "-":
        return ""
    return text


def _pick_int(record: Mapping[str, Any], *keys: str, default: int) -> int:
    value = _pick_value(record, *keys)
    return _to_int(value, default=default)


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
