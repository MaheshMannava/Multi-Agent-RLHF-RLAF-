"""Prepare agent-visible task descriptions and validate benchmark predictions."""

import argparse
import json
from pathlib import Path


def public_task(row):
    """Whitelist fields: do not expose reference patches or evaluation tests."""
    fields = ("instance_id", "repo", "base_commit", "problem_statement")
    missing = [field for field in fields if not isinstance(row.get(field), str) or not row[field]]
    if missing:
        raise ValueError(f"Missing or invalid task fields: {', '.join(missing)}")
    return {field: row[field] for field in fields}


def validate_predictions(rows):
    """Validate the public SWE-bench prediction JSONL format."""
    seen = set()
    for line, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Line {line}: expected an object")
        for field in ("instance_id", "model_name_or_path", "model_patch"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"Line {line}: {field} must be a nonempty string")
        if row["instance_id"] in seen:
            raise ValueError(f"Line {line}: duplicate instance_id {row['instance_id']}")
        seen.add(row["instance_id"])
    if not seen:
        raise ValueError("No predictions provided")
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path, help="Predictions JSONL file")
    args = parser.parse_args()
    try:
        with args.predictions.open(encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
        count = validate_predictions(rows)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Invalid predictions: {exc}\n")
    print(f"Validated {count} prediction(s); patch applicability is checked by evaluation.")


if __name__ == "__main__":
    main()
