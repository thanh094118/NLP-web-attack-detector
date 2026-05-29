# Web Server Log Parser + Rule-Based Attack Detection

This project is a non-ML cybersecurity pipeline for parsing web access logs and detecting suspicious requests with YAML rules plus hand-crafted features.

Current phase scope:
- Included: collector, parser, normalizer, request preprocessor, rule detector, feature extraction, risk scoring, exporting, markdown reporting.
- Not included yet: AI/NLP or ML training/detection (TF-IDF, Logistic Regression, SVM, Isolation Forest, deep learning, vector search).

## Environment

Conda:

```bash
conda env create -f environment.yml
conda activate vdt
```

Pip:

```bash
pip install -r requirements.txt
```

## Run The Pipeline

Expected CLI:

```bash
python -m src.main --input data/raw/apache/access.log
```

With explicit rules file:

```bash
```

## Required Arguments

- `--input`: path to one access log file
- `--server-type` (optional): `apache`, `nginx`, or `iis` (if omitted, pipeline auto-detects)
- `--output-dir` (optional): output directory for one run (default: `outputs`)
- `--rules` (optional): YAML rule file path (default: `src/rules/attack_patterns.yaml`)
- `--stage` (optional): `all` (default) or one stage: `collect`, `parser`, `normalize`, `preprocess`, `detect`, `extract`

## Output Files

One full run writes artifacts into module folders under `--output-dir`:

- `collector_results/<server>_<input_stem>_raw_lines.jsonl`
- `parser_results/<server>_<input_stem>_parsed_logs.jsonl`
- `normalizer_results/<server>_<input_stem>_normalized_logs.jsonl`
- `normalizer_results/<server>_<input_stem>_normalized_logs.csv`
- `preprocessor_results/<server>_<input_stem>_preprocessed_requests.jsonl`
- `feature_results/<server>_<input_stem>_features.csv`
- `detector_results/<server>_<input_stem>_alerts.jsonl`
- `detector_results/<server>_<input_stem>_alerts.csv`
- `<server>_<input_stem>_report.md`
- `<server>_<input_stem>_run_summary.json`

## Convert Diverse Inputs

Convert `.txt`, `.csv`, `.json`, `.jsonl` into canonical JSONL records for pipeline ingestion prep:

```bash
python convert.py --input <input_file>
```

Optional split by file size (MB), for large inputs:

```bash
python convert.py --input <input_file> --max-file-size-mb 500
```

Conversion output folders:

- `data/collected/converted_<input_stem>.jsonl` (or `_partNNN.jsonl` when split)
- `data/parsered/converted_<input_stem>.jsonl` (or `_partNNN.jsonl` when split)

## Tests

Run all tests:

```bash
pytest -q
```

Cache-free run:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider
```
