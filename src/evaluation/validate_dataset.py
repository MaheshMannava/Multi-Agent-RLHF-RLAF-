"""Validate a JSONL debugging dataset and print a compact summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import validate_sample


def validate_dataset(path: Path) -> int:
    samples = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                samples.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"line {line_number}: invalid JSON: {exc}")
                return 1

    validations = [validate_sample(sample) for sample in samples]
    valid_count = sum(validation.valid for validation in validations)
    syntax_count = sum(validation.bug_type == "syntax" for validation in validations)
    logic_count = sum(validation.bug_type == "logic" for validation in validations)

    print(f"Dataset: {path}")
    print(f"Samples: {len(samples)} ({syntax_count} syntax, {logic_count} logic)")
    print(f"Valid samples: {valid_count}/{len(samples)}")

    for validation in validations:
        if not validation.valid:
            print(f"- {validation.bug_id}: {', '.join(validation.problems)}")

    return 0 if valid_count == len(samples) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="Path to a JSONL dataset")
    args = parser.parse_args()
    return validate_dataset(args.dataset)


if __name__ == "__main__":
    raise SystemExit(main())
