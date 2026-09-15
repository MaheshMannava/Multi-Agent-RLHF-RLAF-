"""Evaluate Python debugging samples in isolated temporary directories.

The evaluator is deliberately small and deterministic. It performs syntax
checking in-process with ``ast.parse`` and runs test code in a subprocess with
a timeout. The pilot dataset is trusted research input; do not use this
runner as a security sandbox for arbitrary third-party programs.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


_FAILED_TEST_RE = re.compile(r"FAILED\s+([^\s]+)")


@dataclass(frozen=True)
class EvaluationResult:
    """Result of compiling and, when possible, testing one Python program."""

    compiles: bool
    tests_passed: Optional[bool]
    success: bool
    timed_out: bool = False
    return_code: Optional[int] = None
    error_type: Optional[str] = None
    failing_tests: tuple[str, ...] = field(default_factory=tuple)
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class SampleValidation:
    """Validation result for both the buggy and corrected versions."""

    bug_id: str
    bug_type: str
    buggy: EvaluationResult
    corrected: EvaluationResult
    valid: bool
    problems: tuple[str, ...] = field(default_factory=tuple)


def _syntax_error_result(source: str) -> Optional[EvaluationResult]:
    """Return a failed result for invalid Python, or ``None`` if valid."""

    try:
        ast.parse(source, filename="solution.py")
    except SyntaxError as exc:
        message = f"{exc.msg} (line {exc.lineno})"
        return EvaluationResult(
            compiles=False,
            tests_passed=None,
            success=False,
            return_code=1,
            error_type="SyntaxError",
            stderr=message,
        )
    return None


def _extract_failing_tests(output: str) -> tuple[str, ...]:
    """Extract pytest node IDs when they are present in captured output."""

    return tuple(dict.fromkeys(_FAILED_TEST_RE.findall(output)))


def evaluate_code(
    source: str,
    tests: Sequence[str] | None = None,
    *,
    timeout_seconds: float = 3.0,
) -> EvaluationResult:
    """Compile and optionally test a Python source string.

    ``tests`` contains Python source for a pytest module. Tests should import
    functions from ``solution.py``. The program and tests are written to a
    temporary directory, and pytest is invoked without a shell.
    """

    started = time.perf_counter()
    syntax_failure = _syntax_error_result(source)
    if syntax_failure is not None:
        return syntax_failure

    test_sources = list(tests or [])
    if not test_sources:
        return EvaluationResult(
            compiles=True,
            tests_passed=True,
            success=True,
            duration_seconds=time.perf_counter() - started,
        )

    with tempfile.TemporaryDirectory(prefix="debug_eval_") as temp_dir:
        root = Path(temp_dir)
        (root / "solution.py").write_text(source, encoding="utf-8")
        (root / "test_solution.py").write_text(
            "\n\n".join(test_sources) + "\n", encoding="utf-8"
        )

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = str(root)

        if importlib.util.find_spec("pytest") is not None:
            command = [sys.executable, "-m", "pytest", "-q", "test_solution.py"]
        else:
            # The pilot tests intentionally use plain test functions with
            # assertions. This fallback keeps the evaluator runnable before
            # optional dependencies are installed; the normal path uses
            # pytest as specified by the project requirements.
            (root / "run_tests.py").write_text(
                """import importlib\nimport sys\nimport traceback\n\nmodule = importlib.import_module('test_solution')\nfailures = 0\ncount = 0\nfor name in sorted(dir(module)):\n    if not name.startswith('test_'):\n        continue\n    test = getattr(module, name)\n    if not callable(test):\n        continue\n    count += 1\n    try:\n        test()\n    except Exception:\n        failures += 1\n        print(f'FAILED test_solution.py::{name}')\n        traceback.print_exc()\nif failures:\n    print(f'{failures} failed, {count - failures} passed')\n    sys.exit(1)\nprint(f'{count} passed')\n""",
                encoding="utf-8",
            )
            command = [sys.executable, "run_tests.py"]

        try:
            completed = subprocess.run(
                command,
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            return EvaluationResult(
                compiles=True,
                tests_passed=False,
                success=False,
                timed_out=True,
                error_type="Timeout",
                stdout=stdout,
                stderr=stderr,
                duration_seconds=time.perf_counter() - started,
            )

    combined_output = f"{completed.stdout}\n{completed.stderr}"
    passed = completed.returncode == 0
    error_type = None if passed else "TestFailure"
    if "ModuleNotFoundError" in combined_output:
        error_type = "MissingDependency"
    elif "ERROR" in combined_output and "pytest" in combined_output:
        error_type = "TestCollectionError"

    return EvaluationResult(
        compiles=True,
        tests_passed=passed,
        success=passed,
        return_code=completed.returncode,
        error_type=error_type,
        failing_tests=_extract_failing_tests(combined_output),
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )


def validate_sample(
    sample: Mapping[str, Any], *, timeout_seconds: float = 3.0
) -> SampleValidation:
    """Check that a dataset sample has the expected before/after behavior.

    A valid syntax sample should fail compilation before repair and succeed
    after repair. A valid logic sample should compile before repair, fail at
    least one test, and pass all tests after repair.
    """

    bug_id = str(sample["bug_id"])
    bug_type = str(sample["bug_type"])
    tests = sample.get("tests", [])
    buggy = evaluate_code(sample["buggy_code"], tests, timeout_seconds=timeout_seconds)
    corrected = evaluate_code(sample["correct_code"], tests, timeout_seconds=timeout_seconds)

    problems: list[str] = []
    if not corrected.success:
        problems.append("correct_code_does_not_pass")

    if bug_type == "syntax":
        if buggy.compiles:
            problems.append("syntax_bug_compiles_before_repair")
    elif bug_type == "logic":
        if not buggy.compiles:
            problems.append("logic_bug_does_not_compile_before_repair")
        elif buggy.tests_passed:
            problems.append("logic_bug_tests_pass_before_repair")
    else:
        problems.append("unknown_bug_type")

    return SampleValidation(
        bug_id=bug_id,
        bug_type=bug_type,
        buggy=buggy,
        corrected=corrected,
        valid=not problems,
        problems=tuple(problems),
    )
