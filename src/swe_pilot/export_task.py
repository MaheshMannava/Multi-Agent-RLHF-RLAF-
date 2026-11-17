"""Export one public task from SWE-bench Lite to a JSON file."""
import argparse
import json
from pathlib import Path
from datasets import load_dataset
from .data import public_task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', default='marshmallow-code__marshmallow-1343')
    parser.add_argument('--split', choices=['dev', 'test'], default='dev')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    dataset = load_dataset('SWE-bench/SWE-bench_Lite', split=args.split)
    task = next((row for row in dataset if row['instance_id'] == args.instance), None)
    if task is None:
        parser.error('Instance not found in split')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(public_task(task), indent=2) + '\n', encoding='utf-8')
    print(f'Exported {args.instance} from {args.split} to {args.output}')


if __name__ == '__main__':
    main()
