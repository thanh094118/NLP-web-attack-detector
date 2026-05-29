from pathlib import Path

from src.converter.convert_flow import convert_file


def _read_lines(path: Path):
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_convert_txt_access_log_keeps_raw_shape(tmp_path: Path):
    input_path = tmp_path / "access.txt"
    input_path.write_text(
        '83.149.9.216 - - [17/May/2015:10:05:03 +0000] "GET /img.png HTTP/1.1" 200 203023 "-" "Mozilla/5.0"\n',
        encoding="utf-8",
    )

    summary = convert_file(input_path=input_path, output_root=tmp_path / "data/raw")
    output_path = Path(summary["output"])

    assert summary["counts"]["raw_lines"] == 1
    assert output_path.exists()
    lines = _read_lines(output_path)
    assert len(lines) == 1
    assert lines[0].startswith("83.149.9.216 - - [17/May/2015:10:05:03 +0000]")


def test_convert_http_request_block_to_access_log_line(tmp_path: Path):
    input_path = tmp_path / "block.txt"
    input_path.write_text(
        "Start - Id: 11044\n"
        "class: Attack\n"
        "GET http://localhost:8080/tienda1/publico/caracteristicas.jsp?idA=2 HTTP/1.1\n"
        "User-Agent: Mozilla/5.0\n"
        "Host: localhost:8080\n"
        "End - Id: 11044\n",
        encoding="utf-8",
    )

    summary = convert_file(input_path=input_path, output_root=tmp_path / "data/raw")
    lines = _read_lines(Path(summary["output"]))

    assert summary["counts"]["raw_lines"] == 1
    assert '"GET http://localhost:8080/tienda1/publico/caracteristicas.jsp?idA=2 HTTP/1.1"' in lines[0]
    assert '"Mozilla/5.0"' in lines[0]


def test_convert_structured_csv_to_access_log_line(tmp_path: Path):
    input_path = tmp_path / "sec.csv"
    input_path.write_text(
        "timestamp,source_ip,http_method,raw_uri,status_code,response_size,user_agent,referrer\n"
        "2025-06-30T23:59:58.997-0400,10.0.0.1,GET,/a,200,123,UA,-\n",
        encoding="utf-8",
    )

    summary = convert_file(input_path=input_path, output_root=tmp_path / "data/raw", server_type="nginx")
    output_path = Path(summary["output"])
    lines = _read_lines(output_path)

    assert summary["server_type"] == "nginx"
    assert summary["counts"]["raw_lines"] == 1
    assert output_path.parent.name == "nginx"
    assert '"GET /a HTTP/1.1" 200 123' in lines[0]


def test_convert_parsered_jsonl_to_access_log_line(tmp_path: Path):
    input_path = tmp_path / "parsed.jsonl"
    input_path.write_text(
        '{"http_method":"POST","raw_uri":"/login","http_version":"HTTP/1.1","status_code":401,"response_size":0,"user_agent":"ua","referrer":"-","source_ip":"1.2.3.4"}\n',
        encoding="utf-8",
    )

    summary = convert_file(input_path=input_path, output_root=tmp_path / "data/raw")
    lines = _read_lines(Path(summary["output"]))

    assert summary["counts"]["raw_lines"] == 1
    assert lines[0].startswith("1.2.3.4 - - [")
    assert '"POST /login HTTP/1.1" 401 0 "-" "ua"' in lines[0]
