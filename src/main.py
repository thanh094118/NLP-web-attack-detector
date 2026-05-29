import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional

from src.collector.file_collector import FileCollector
from src.detection.rule_detector import RuleDetector
from src.exporters.csv_exporter import CSVExporter
from src.exporters.jsonl_exporter import JSONLExporter
from src.exporters.markdown_exporter import MarkdownExporter
from src.features.feature_extractor import FeatureExtractor
from src.normalizer.normalizer import Normalizer
from src.parser.apache_parser import ApacheParser
from src.parser.iis_parser import IISParser
from src.parser.nginx_parser import NginxParser
from src.preprocessor.request_preprocessor import RequestPreprocessor
from src.reporting.postprocessor import PostProcessor
from src.reporting.report_generator import ReportGenerator
from src.scoring.risk_engine import RiskEngine


DEFAULT_RULES_PATH = "src/rules/attack_patterns.yaml"
STAGE_CHOICES = ("all", "collect", "parser", "normalize", "preprocess", "detect", "extract")

RECORD_PREFERRED_COLUMNS = [
    "event_id",
    "line_number",
    "parse_status",
    "parse_error",
    "error_message",
    "timestamp",
    "source_ip",
    "http_method",
    "original_url",
    "uri",
    "query_string",
    "status_code",
    "response_size",
    "user_agent",
    "referrer",
    "server_type",
    "risk_score",
    "risk_level",
    "final_label",
    "attack_type",
    "matched_rule_ids",
]

ALERT_PREFERRED_COLUMNS = [
    "event_id",
    "line_number",
    "timestamp",
    "source_ip",
    "http_method",
    "original_url",
    "uri",
    "query_string",
    "status_code",
    "response_size",
    "server_type",
    "rule_label",
    "rule_score",
    "rule_severity",
    "risk_score",
    "risk_level",
    "final_label",
    "attack_type",
    "matched_rule_ids",
    "matched_rules",
    "normalized_request",
    "raw_log",
]


def get_parser(server_type: str):
    value = server_type.lower()
    if value == "apache":
        return ApacheParser()
    if value == "nginx":
        return NginxParser()
    if value == "iis":
        return IISParser()
    raise ValueError(f"Unsupported server type: {server_type}")


def _build_event_id(*, server_type: str, line_number: int, raw_line: str, source_id: Optional[str] = None) -> str:
    digest = hashlib.sha1(str(raw_line).encode("utf-8", errors="ignore")).hexdigest()[:12]
    if source_id:
        return f"{server_type.lower()}:{line_number}:{source_id}:{digest}"
    return f"{server_type.lower()}:{line_number}:{digest}"


def to_raw_line_records(lines: List[str], server_type: str, source_id: Optional[str] = None) -> List[Dict]:
    records = []
    for idx, line in enumerate(lines, start=1):
        records.append({
            "event_id": _build_event_id(
                server_type=server_type,
                line_number=idx,
                raw_line=line,
                source_id=source_id,
            ),
            "line_number": idx,
            "server_type": server_type.lower(),
            "raw_line": line,
            "parse_status": "raw",
            "parse_error": False,
            "error_message": None,
        })
    return records


def to_raw_line_records_with_metadata(
    read_records: List[Dict],
    server_type: str,
    source_id: Optional[str] = None,
) -> List[Dict]:
    records: List[Dict] = []
    for idx, item in enumerate(read_records, start=1):
        line = item.get("line", "")
        records.append({
            "event_id": _build_event_id(
                server_type=server_type,
                line_number=idx,
                raw_line=line,
                source_id=source_id,
            ),
            "line_number": idx,
            "server_type": server_type.lower(),
            "raw_line": line,
            "parse_status": "raw",
            "parse_error": False,
            "error_message": None,
            "encoding_used": item.get("encoding_used"),
            "decode_error": bool(item.get("decode_error", False)),
            "had_bom": bool(item.get("had_bom", False)),
            "was_continuation_merged": bool(item.get("was_continuation_merged", False)),
            "physical_line_start": item.get("physical_line_start"),
            "physical_line_end": item.get("physical_line_end"),
        })
    return records


def build_feature_row(record: Dict) -> Dict:
    row = {
        "line_number": record.get("line_number"),
        "event_id": record.get("event_id"),
        "parse_status": record.get("parse_status"),
        "parse_error": record.get("parse_error"),
        "error_message": record.get("error_message"),
        "source_ip": record.get("source_ip"),
        "http_method": record.get("http_method"),
        "original_url": record.get("original_url"),
        "uri": record.get("uri"),
        "query_string": record.get("query_string"),
        "normalized_request": record.get("normalized_request"),
        "server_type": record.get("server_type"),
    }
    for key, value in record.items():
        if key.startswith("feature_"):
            row[key] = value
    return row


def build_alert_record(record: Dict) -> Dict:
    return {
        "line_number": record.get("line_number"),
        "event_id": record.get("event_id"),
        "timestamp": record.get("timestamp"),
        "source_ip": record.get("source_ip"),
        "http_method": record.get("http_method"),
        "original_url": record.get("original_url"),
        "uri": record.get("uri"),
        "query_string": record.get("query_string"),
        "status_code": record.get("status_code"),
        "response_size": record.get("response_size"),
        "user_agent": record.get("user_agent"),
        "referrer": record.get("referrer"),
        "server_type": record.get("server_type"),
        "rule_label": record.get("rule_label"),
        "rule_score": record.get("rule_score"),
        "rule_severity": record.get("rule_severity"),
        "risk_score": record.get("risk_score"),
        "risk_level": record.get("risk_level"),
        "final_label": record.get("final_label"),
        "attack_type": record.get("attack_type"),
        "attack_types": record.get("attack_types", []),
        "matched_rule_ids": record.get("matched_rule_ids", []),
        "matched_rules": record.get("matched_rules", []),
        "normalized_request": record.get("normalized_request"),
        "parse_status": record.get("parse_status"),
        "parse_error": record.get("parse_error"),
        "error_message": record.get("error_message"),
        "raw_log": record.get("raw_log"),
    }


def detect_server_type(lines: List[str]) -> str:
    non_empty = [line for line in lines if str(line).strip()]
    if any(str(line).lstrip().startswith("#Fields:") for line in non_empty):
        return "iis"
    if any(str(line).lstrip().startswith("#Software:") for line in non_empty):
        return "iis"

    sample = non_empty[:200]
    apache_ok = sum(1 for row in ApacheParser().parse_lines(sample) if row.get("parse_status") == "success")
    nginx_ok = sum(1 for row in NginxParser().parse_lines(sample) if row.get("parse_status") == "success")
    if nginx_ok > apache_ok:
        return "nginx"
    return "apache"


def run_pipeline(
    *,
    input_path: str | Path,
    server_type: Optional[str],
    output_dir: str | Path,
    rules_path: str = DEFAULT_RULES_PATH,
    stage: str = "all",
) -> Dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    input_stem = Path(input_path).stem

    stage_to_module_dir = {
        "collect": "collector_results",
        "parser": "parser_results",
        "normalize": "normalizer_results",
        "preprocess": "preprocessor_results",
        "detect": "detector_results",
        "extract": "feature_results",
    }

    def stage_file(stage_name: str, suffix: str) -> Path:
        base = output_path / stage_to_module_dir[stage_name]
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{prefix}_{suffix}"

    collector = FileCollector(str(input_path))
    normalizer = Normalizer()
    preprocessor = RequestPreprocessor()
    detector = RuleDetector(rules_path=rules_path)
    feature_extractor = FeatureExtractor()
    risk_engine = RiskEngine()

    jsonl_exporter = JSONLExporter()
    csv_exporter = CSVExporter(preferred_fieldnames=RECORD_PREFERRED_COLUMNS)
    alert_csv_exporter = CSVExporter(preferred_fieldnames=ALERT_PREFERRED_COLUMNS)
    markdown_exporter = MarkdownExporter()

    read_records = collector.read_records()
    raw_lines = [item.get("line", "") for item in read_records]
    resolved_server_type = (server_type or detect_server_type(raw_lines)).lower()
    parser = get_parser(resolved_server_type)
    parser.set_resolved_server_type(resolved_server_type)
    source_id = hashlib.sha1(str(Path(input_path).resolve()).encode("utf-8", errors="ignore")).hexdigest()[:8]
    parser.set_event_namespace(source_id)
    prefix = f"{resolved_server_type}_{input_stem}"
    raw_line_records = to_raw_line_records_with_metadata(read_records, resolved_server_type, source_id=source_id)
    jsonl_exporter.export(raw_line_records, stage_file("collect", "raw_lines.jsonl"))
    if stage == "collect":
        return {"stage": stage, "output_dir": str(output_path), "counts": {"raw_lines": len(raw_line_records)}}

    parsed_logs = list(parser.parse_lines(raw_lines))
    jsonl_exporter.export(parsed_logs, stage_file("parser", "parsed_logs.jsonl"))
    if stage == "parser":
        return {"stage": stage, "output_dir": str(output_path), "counts": {"raw_lines": len(raw_line_records), "parsed_logs": len(parsed_logs)}}

    normalized_logs = [normalizer.normalize(row) for row in parsed_logs]
    jsonl_exporter.export(normalized_logs, stage_file("normalize", "normalized_logs.jsonl"))
    csv_exporter.export(normalized_logs, stage_file("normalize", "normalized_logs.csv"))
    if stage == "normalize":
        return {"stage": stage, "output_dir": str(output_path), "counts": {"raw_lines": len(raw_line_records), "parsed_logs": len(parsed_logs), "normalized_logs": len(normalized_logs)}}

    preprocessed_requests = [preprocessor.preprocess(row) for row in normalized_logs]
    jsonl_exporter.export(preprocessed_requests, stage_file("preprocess", "preprocessed_requests.jsonl"))
    if stage == "preprocess":
        return {"stage": stage, "output_dir": str(output_path), "counts": {"raw_lines": len(raw_line_records), "parsed_logs": len(parsed_logs), "normalized_logs": len(normalized_logs), "preprocessed_requests": len(preprocessed_requests)}}

    scored_records: List[Dict] = []
    feature_rows: List[Dict] = []
    alerts: List[Dict] = []

    for request in preprocessed_requests:
        detected = detector.detect(request)
        features = feature_extractor.extract(request)

        record = dict(request)
        record.update(detected)
        for key, value in features.items():
            record[f"feature_{key}"] = value

        record.update(risk_engine.score(record))
        scored_records.append(record)
        feature_rows.append(build_feature_row(record))

        if record.get("should_alert"):
            alerts.append(build_alert_record(record))

    if stage in ("all", "extract"):
        csv_exporter.export(feature_rows, stage_file("extract", "features.csv"))
    if stage in ("all", "detect"):
        jsonl_exporter.export(alerts, stage_file("detect", "alerts.jsonl"))
        alert_csv_exporter.export(alerts, stage_file("detect", "alerts.csv"))

    if stage in ("detect", "extract"):
        return {
            "stage": stage,
            "output_dir": str(output_path),
            "counts": {
                "raw_lines": len(raw_line_records),
                "parsed_logs": len(parsed_logs),
                "normalized_logs": len(normalized_logs),
                "preprocessed_requests": len(preprocessed_requests),
                "alerts": len(alerts),
                "features": len(feature_rows),
            },
        }

    postprocessor = PostProcessor()
    summary = postprocessor.build_summary(
        input_path=str(Path(input_path)),
        server_type=resolved_server_type,
        output_dir=str(output_path),
        rules_path=rules_path,
        raw_lines=raw_line_records,
        parsed_logs=parsed_logs,
        normalized_logs=normalized_logs,
        preprocessed_requests=preprocessed_requests,
        scored_records=scored_records,
        alerts=alerts,
    )
    summary["collector"] = {
        "decode_error_records": sum(1 for row in raw_line_records if row.get("decode_error")),
        "had_bom_records": sum(1 for row in raw_line_records if row.get("had_bom")),
        "continuation_merged_records": sum(1 for row in raw_line_records if row.get("was_continuation_merged")),
    }

    report_text = ReportGenerator().generate(summary, alerts)
    markdown_exporter.export(report_text, output_path / f"{prefix}_report.md")

    run_summary_path = output_path / f"{prefix}_run_summary.json"
    run_summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    return summary


def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Web Server Log Parser + Rule-based Web Attack Detection (non-ML pipeline)"
    )
    parser.add_argument("--input", required=True, help="Path to one access log file")
    parser.add_argument(
        "--server-type",
        required=False,
        choices=("apache", "nginx", "iis"),
        help="Input log server type (optional, auto-detected when omitted)",
    )
    parser.add_argument("--output-dir", default="outputs", help="Directory for all generated outputs")
    parser.add_argument("--rules", default=DEFAULT_RULES_PATH, help="YAML rule file path")
    parser.add_argument("--stage", default="all", choices=STAGE_CHOICES, help="Run one stage only or full pipeline")
    return parser


def main() -> None:
    cli = build_cli()
    args = cli.parse_args()

    summary = run_pipeline(
        input_path=args.input,
        server_type=args.server_type,
        output_dir=args.output_dir,
        rules_path=args.rules,
        stage=args.stage,
    )

    counts = summary.get("counts", {})
    print("[+] Pipeline finished")
    print(f"[+] Raw lines: {counts.get('raw_lines', 0)}")
    print(f"[+] Parsed logs: {counts.get('parsed_logs', 0)}")
    print(f"[+] Parse errors: {counts.get('parse_errors', 0)}")
    print(f"[+] Alerts: {counts.get('alerts', 0)}")
    collector_info = summary.get("collector", {})
    print(f"[+] Decode fallback records: {collector_info.get('decode_error_records', 0)}")
    print(f"[+] Output dir: {summary.get('output_dir')}")


if __name__ == "__main__":
    main()
