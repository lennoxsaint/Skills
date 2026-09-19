import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "scripts" / "skills.py"


class PublicRepositoryTests(unittest.TestCase):
    def run_cli(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=REPO_ROOT,
            check=check,
            capture_output=True,
            text=True,
        )

    def test_catalog_lists_public_skills(self):
        result = self.run_cli("list")
        self.assertIn("email-triage-pro", result.stdout)
        self.assertIn("save-10-percent", result.stdout)
        self.assertIn("stable", result.stdout)

    def test_repository_validates(self):
        result = self.run_cli("validate")
        self.assertIn("PASS", result.stdout)

    def test_show_returns_catalog_entry(self):
        payload = json.loads(self.run_cli("show", "save-10-percent").stdout)
        self.assertEqual(payload["path"], "save-10-percent")
        self.assertEqual(payload["status"], "stable")

    def test_email_triage_pro_is_installable(self):
        payload = json.loads(self.run_cli("show", "email-triage-pro").stdout)
        self.assertEqual(payload["path"], "email-triage-pro")
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli("install", "email-triage-pro", "--target-root", directory)
            installed = Path(directory) / "email-triage-pro"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "references" / "feedback-learning.md").is_file())

    def test_install_is_safe_and_excludes_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli("install", "save-10-percent", "--target-root", directory)
            installed = Path(directory) / "save-10-percent"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertFalse(any((installed / "scripts").glob("test_*.py")))
            repeated = self.run_cli(
                "install", "save-10-percent", "--target-root", directory, check=False
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("Refusing to overwrite", repeated.stderr)

    def test_unknown_skill_fails_with_available_names(self):
        result = self.run_cli("show", "does-not-exist", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("save-10-percent", result.stderr)


if __name__ == "__main__":
    unittest.main()
