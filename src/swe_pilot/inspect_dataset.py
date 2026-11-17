"""Inspect public SWE-bench Lite task metadata without printing reference patches."""

import argparse

from datasets import load_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--instance", default="marshmallow-code__marshmallow-1343")
    args = parser.parse_args()
    data = load_dataset("SWE-bench/SWE-bench_Lite", split=args.split)
    matches = [row for row in data if row["instance_id"] == args.instance]
    print("Dataset: SWE-bench/SWE-bench_Lite")
    print(f"Split: {args.split}; rows: {len(data)}")
    if not matches:
        parser.error(f"Instance {args.instance} not found in {args.split}")
    task = matches[0]
    print(f"Instance: {task['instance_id']}")
    print(f"Repository: {task['repo']}")
    print(f"Base commit: {task['base_commit']}")
    print("\nIssue description:\n")
    print(task["problem_statement"])


if __name__ == "__main__":
    main()
