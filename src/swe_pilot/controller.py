"""Build an agent prompt and record a simulated or OpenRouter patch proposal."""
import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from .data import public_task


def build_prompt(task, repository, paths):
    task = public_task(task)
    files = []
    root = repository.resolve()
    for name in paths:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Invalid source path: {name}")
        files.append(f"--- {name} ---\n{path.read_text(encoding='utf-8')}")
    return ("Fix the following issue. Return ONLY a valid unified git diff. "
            "Ensure each @@ hunk header has accurate old and new line counts, "
            "and include a final newline. Change source files only, do not change tests.\n\n"
            f"Issue:\n{task['problem_statement']}\n\n" + "\n\n".join(files))


def propose(prompt, model, key):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0, "max_tokens": 6000,
                       "reasoning": {"max_tokens": 1024}}).encode()
    request = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            message = json.load(exc).get('error', {}).get('message', 'No details')
        except (ValueError, AttributeError):
            message = 'No details'
        raise ValueError(f'OpenRouter HTTP {exc.code}: {message}') from None
    choice = data["choices"][0]
    return choice["message"].get("content") or "", data.get("usage", {}), choice.get("finish_reason")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', type=Path, required=True, help='JSON task record')
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--file', action='append', required=True, help='Source path, relative to repository')
    parser.add_argument('--output', type=Path, required=True, help='New run directory')
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--mock-patch', type=Path, help='Existing patch used to simulate the model')
    choice.add_argument('--model', help='OpenRouter free model ID ending in :free')
    args = parser.parse_args()
    if args.model and not args.model.endswith(':free'):
        parser.error('Only explicit OpenRouter free model IDs ending in :free are allowed')
    if args.output.exists():
        parser.error('Output directory already exists; choose a new one')
    task = json.loads(args.task.read_text(encoding='utf-8'))
    current = subprocess.check_output(['git', '-C', str(args.repository), 'rev-parse', 'HEAD'], text=True).strip()
    if current != task.get('base_commit'):
        parser.error('Repository HEAD does not match task base_commit')
    if subprocess.check_output(['git', '-C', str(args.repository), 'status', '--porcelain'], text=True).strip():
        parser.error('Repository must have a clean working tree')
    prompt = build_prompt(task, args.repository, args.file)
    started = time.monotonic()
    if args.mock_patch:
        patch = args.mock_patch.read_text(encoding='utf-8')
        usage = {}
        model = 'simulated'
        finish_reason = None
    else:
        key = os.environ.get('OPENROUTER_API_KEY')
        if not key:
            parser.error('OPENROUTER_API_KEY is not set')
        try:
            patch, usage, finish_reason = propose(prompt, args.model, key)
        except (ValueError, urllib.error.URLError) as exc:
            parser.exit(1, f'Model request failed: {exc}\n')
        model = args.model
    if patch.startswith('```'):
        parts = patch.splitlines()
        if parts[-1].strip() == '```':
            patch = '\n'.join(parts[1:-1]) + '\n'
    args.output.mkdir(parents=True)
    (args.output / 'prompt.txt').write_text(prompt, encoding='utf-8')
    (args.output / 'patch.diff').write_text(patch, encoding='utf-8')
    (args.output / 'proposal.json').write_text(json.dumps({'instance_id': task['instance_id'],
        'model': model, 'simulated': bool(args.mock_patch), 'source_files': args.file,
        'elapsed_seconds': round(time.monotonic() - started, 3), 'usage': usage,
        'finish_reason': finish_reason}, indent=2) + '\n')
    if not patch.strip():
        parser.exit(1, f'Model returned no patch text (finish reason: {finish_reason}); details saved to {args.output}\n')
    print(f"Saved {'simulated' if args.mock_patch else 'model'} proposal to {args.output}")


if __name__ == '__main__':
    main()
