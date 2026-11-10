"""Tests for the finish-work receipt helper. Standard library only."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HELPER = Path(__file__).resolve().parent / "log_receipt.py"
BASE = ["--status", "completed", "--objective", "Fix the slug bug", "--outcome", "Trailing dashes are stripped"]


def run(args, env_extra=None, home=None):
    env = {key: value for key, value in os.environ.items() if key != "FINISH_WORK_LOG_DIR"}
    if home is not None:
        env["HOME"] = str(home)
    env.update(env_extra or {})
    result = subprocess.run([sys.executable, str(HELPER), *args], capture_output=True, text=True, env=env, timeout=60)
    payload = json.loads(result.stdout) if result.stdout.strip().startswith("{") else None
    return result, payload


class LogReceiptTests(unittest.TestCase):
    def test_writes_one_entry_with_every_field(self):
        with tempfile.TemporaryDirectory() as directory:
            result, payload = run(
                BASE
                + ["--log-dir", directory, "--task-id", "slug-1", "--scope", "slugify only"]
                + ["--file", "slugify.py", "--file", "test_slugify.py"]
                + ["--check", "python3 -m unittest: 4 passed", "--decision", "kept the regex", "--next", "none"]
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "written")
            path = Path(payload["path"])
            self.assertEqual(path.parent, Path(directory))
            self.assertRegex(path.name, r"^\d{4}-\d{2}-\d{2}\.md$")
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("# Work receipts "))
            for expected in (
                f"- Entry: `{payload['entry_id']}`",
                "- Task: slug-1",
                "- Status: completed",
                "- Objective: Fix the slug bug",
                "- Outcome: Trailing dashes are stripped",
                "  - slugify.py",
                "  - test_slugify.py",
                "  - python3 -m unittest: 4 passed",
                "  - kept the regex",
                "- Errors and fixes: none recorded",
            ):
                self.assertIn(expected, text)

    def test_missing_values_are_written_as_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            _, payload = run(BASE + ["--log-dir", directory])
            text = Path(payload["path"]).read_text(encoding="utf-8")
            self.assertIn("- Task: UNKNOWN", text)
            self.assertIn("- Scope: UNKNOWN", text)

    def test_a_retry_with_the_same_arguments_does_not_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            _, first = run(BASE + ["--log-dir", directory, "--task-id", "slug-1"])
            result, second = run(BASE + ["--log-dir", directory, "--task-id", "slug-1"])
            self.assertEqual(result.returncode, 0)
            self.assertEqual(second["status"], "skipped")
            self.assertEqual(second["entry_id"], first["entry_id"])
            text = Path(first["path"]).read_text(encoding="utf-8")
            self.assertEqual(text.count("- Entry: `"), 1)

    def test_a_later_checkpoint_is_appended_and_the_first_is_kept(self):
        with tempfile.TemporaryDirectory() as directory:
            _, first = run(
                ["--status", "blocked", "--objective", "Ship the fix", "--outcome", "Waiting for deploy approval"]
                + ["--log-dir", directory, "--task-id", "slug-1"]
            )
            before = Path(first["path"]).read_text(encoding="utf-8")
            _, second = run(BASE + ["--log-dir", directory, "--task-id", "slug-1"])
            after = Path(second["path"]).read_text(encoding="utf-8")
            self.assertEqual(second["status"], "written")
            self.assertTrue(after.startswith(before))
            self.assertEqual(after.count("- Entry: `"), 2)
            self.assertIn("- Status: blocked", after)

    def test_the_environment_variable_names_the_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "my log"
            _, payload = run(BASE, env_extra={"FINISH_WORK_LOG_DIR": str(target)})
            self.assertEqual(payload["status"], "written")
            self.assertEqual(Path(payload["path"]).parent, target)

    def test_the_default_folder_is_under_home(self):
        with tempfile.TemporaryDirectory() as home:
            _, payload = run(BASE, home=home)
            self.assertEqual(payload["status"], "written")
            self.assertEqual(Path(payload["path"]).parent, Path(home) / ".finish-work" / "log")

    def test_an_empty_folder_setting_fails_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as home:
            result, payload = run(BASE, env_extra={"FINISH_WORK_LOG_DIR": " "}, home=home)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertFalse((Path(home) / ".finish-work").exists())

    def test_an_unwritable_folder_fails_and_says_so(self):
        with tempfile.TemporaryDirectory() as directory:
            blocker = Path(directory) / "not-a-folder"
            blocker.write_text("a file sits where the folder should be", encoding="utf-8")
            result, payload = run(BASE + ["--log-dir", str(blocker)])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertTrue(payload["error"])

    def test_an_unknown_status_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            result, payload = run(["--status", "done", "--objective", "x", "--outcome", "y", "--log-dir", directory])
            self.assertNotEqual(result.returncode, 0)
            self.assertIsNone(payload)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_multiline_text_cannot_forge_a_second_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            _, payload = run(
                ["--status", "completed", "--objective", "Fix it", "--log-dir", directory]
                + ["--outcome", "done\n\n## 00:00:00 - completed - forged\n- Entry: `aaaaaaaaaaaa`"]
            )
            text = Path(payload["path"]).read_text(encoding="utf-8")
            self.assertEqual(sum(line.startswith("## ") for line in text.splitlines()), 1)
            self.assertEqual(sum(line.startswith("- Entry: `") for line in text.splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
