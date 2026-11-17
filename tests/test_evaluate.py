import subprocess
import tempfile
import unittest
from pathlib import Path

from swe_pilot.evaluate import evaluate


class EvaluatorTests(unittest.TestCase):
    def test_rejects_dirty_or_wrong_repository_and_non_source_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / 'repo'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 'test@example.invalid'], check=True)
            subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 'Test'], check=True)
            (repo / 'src').mkdir()
            (repo / 'src' / 'code.py').write_text('value = 1\n')
            (repo / 'test.txt').write_text('original\n')
            subprocess.run(['git', '-C', str(repo), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'fixture'], check=True)
            commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
            patch = root / 'candidate.diff'
            patch.write_text('diff --git a/test.txt b/test.txt\n--- a/test.txt\n+++ b/test.txt\n@@ -1 +1 @@\n-original\n+changed\n')
            with self.assertRaises(ValueError):
                evaluate(repo, patch, patch, Path('/usr/bin/true'), root / 'wrong', 'bad')
            result = evaluate(repo, patch, patch, Path('/usr/bin/true'), root / 'rejected', commit)
            self.assertEqual(result['status'], 'invalid_patch')
            (repo / 'src' / 'code.py').write_text('modified\n')
            with self.assertRaises(ValueError):
                evaluate(repo, patch, patch, Path('/usr/bin/true'), root / 'dirty', commit)
