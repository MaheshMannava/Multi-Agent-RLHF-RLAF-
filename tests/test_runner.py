import json
import unittest
from pathlib import Path

from src.evaluation.runner import evaluate_code, validate_sample


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PILOT_DATASET = PROJECT_ROOT / "data" / "processed" / "pilot.jsonl"


def load_pilot_samples():
    with PILOT_DATASET.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class RunnerTests(unittest.TestCase):
    def test_syntax_error_is_detected_without_running_tests(self):
        result = evaluate_code("def broken(x)\n    return x\n", [])

        self.assertFalse(result.compiles)
        self.assertIsNone(result.tests_passed)
        self.assertEqual(result.error_type, "SyntaxError")


    def test_corrected_logic_program_passes_tests(self):
        source = "def add(a, b):\n    return a + b\n"
        tests = [
            "from solution import add\n\n"
            "def test_add():\n"
            "    assert add(2, 3) == 5\n"
        ]

        result = evaluate_code(source, tests)

        self.assertTrue(result.compiles)
        self.assertTrue(result.tests_passed)
        self.assertTrue(result.success)


    def test_pilot_dataset_has_valid_before_after_behavior(self):
        samples = load_pilot_samples()

        self.assertEqual(len(samples), 20)
        self.assertEqual(sum(sample["bug_type"] == "syntax" for sample in samples), 10)
        self.assertEqual(sum(sample["bug_type"] == "logic" for sample in samples), 10)

        validations = [validate_sample(sample) for sample in samples]

        self.assertTrue(all(validation.valid for validation in validations), validations)
