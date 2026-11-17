import unittest

from swe_pilot.data import public_task, validate_predictions


class DataTests(unittest.TestCase):
    def test_agent_never_receives_reference_fields(self):
        row = {"instance_id": "x", "repo": "o/r", "base_commit": "abc", "problem_statement": "issue", "patch": "secret", "test_patch": "secret", "FAIL_TO_PASS": ["hidden"]}
        self.assertEqual(set(public_task(row)), {"instance_id", "repo", "base_commit", "problem_statement"})

    def test_incomplete_task_fails(self):
        with self.assertRaises(ValueError):
            public_task({"instance_id": "x"})

    def test_predictions_reject_duplicates_and_empty_patches(self):
        row = {"instance_id": "x", "model_name_or_path": "model", "model_patch": "diff"}
        self.assertEqual(validate_predictions([row]), 1)
        with self.assertRaises(ValueError):
            validate_predictions([row, row])
        with self.assertRaises(ValueError):
            validate_predictions([{**row, "model_patch": ""}])
