"""Evaluate a candidate against the local Marshmallow development task.

This uses an isolated working copy, not a security sandbox. Run trusted code only.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


def execute(command, cwd, *, timeout=120, env=None):
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True,
                                timeout=timeout, env=env, check=False)
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 124, f'Timed out after {timeout} seconds\n'


def evaluate(repository, candidate, test_patch, python, output, base_commit):
    repo = repository.resolve()
    candidate = candidate.resolve()
    test_patch = test_patch.resolve()
    # Preserve the venv executable path; resolving its symlink can bypass the venv.
    python = python.absolute()
    code, head = execute(['git', 'rev-parse', 'HEAD'], repo)
    if code or head.strip() != base_commit:
        raise ValueError('Repository HEAD does not match the task base commit')
    code, status = execute(['git', 'status', '--porcelain'], repo)
    if code or status.strip():
        raise ValueError('Repository must have a clean working tree')
    if not candidate.is_file() or not candidate.stat().st_size:
        raise ValueError('Candidate patch must be a non-empty file')
    if output.exists():
        raise ValueError('Output directory already exists')
    output.mkdir(parents=True)
    started = time.monotonic()
    result = {'status': 'error', 'evaluation': 'local adapted evaluation',
              'tests_passed': None, 'candidate_applied': False, 'base_commit': base_commit}
    with tempfile.TemporaryDirectory(prefix='swe-local-') as temp:
        work = Path(temp) / 'repo'
        shutil.copytree(repo, work, ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache'))
        code, stat = execute(['git', 'apply', '--numstat', str(candidate)], work)
        paths = [line.split('\t', 2)[-1] for line in stat.splitlines() if '\t' in line]
        if code or not paths or any(not name.startswith('src/') or '..' in Path(name).parts for name in paths):
            result['status'] = 'invalid_patch'
            log = 'Candidate must be a valid patch affecting only src/ files.\n' + stat
        else:
            code, log = execute(['git', 'apply', '--check', str(candidate)], work)
            if not code:
                code, log = execute(['git', 'apply', str(candidate)], work)
            if code:
                result['status'] = 'patch_did_not_apply'
            else:
                result['candidate_applied'] = True
                code, log = execute(['git', 'apply', '--check', str(test_patch)], work)
                if not code:
                    code, log = execute(['git', 'apply', str(test_patch)], work)
                if code:
                    result['status'] = 'test_setup_error'
                else:
                    env = os.environ.copy()
                    env['PYTHONPATH'] = str(work / 'src')
                    env['PYTHONDONTWRITEBYTECODE'] = '1'
                    code, log = execute([str(python), '-m', 'pytest', '-q', 'tests/test_marshalling.py'], work, env=env)
                    result['test_exit_code'] = code
                    result['tests_passed'] = code == 0
                    result['status'] = 'passed' if code == 0 else ('test_failed' if code == 1 else 'test_error')
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    (output / 'test-output.txt').write_text(log, encoding='utf-8')
    (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--task', type=Path, required=True, help='Public task JSON with base_commit')
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--test-patch', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        task = json.loads(args.task.read_text(encoding='utf-8'))
        result = evaluate(args.repository, args.candidate, args.test_patch, args.python, args.output, task['base_commit'])
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f'Error: {exc}\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
