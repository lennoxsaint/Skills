"""Tests for the finish-work receipt helper. Standard library only."""

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

HELPER = Path(__file__).resolve().parent / "log_receipt.py"
BASE = ["--status", "completed", "--objective", "Fix the slug bug", "--outcome", "Trailing dashes are stripped"]


def clean_env(env_extra=None, home=None):
    env = {key: value for key, value in os.environ.items() if key != "FINISH_WORK_LOG_DIR"}
    if home is not None:
        env["HOME"] = str(home)
    env.update(env_extra or {})
    return env


def run(args, env_extra=None, home=None, cwd=None):
    result = subprocess.run(
        [sys.executable, str(HELPER), *args],
        capture_output=True, text=True, env=clean_env(env_extra, home), timeout=60, cwd=cwd,
    )
    payload = json.loads(result.stdout) if result.stdout.strip().startswith("{") else None
    return result, payload


def entry_lines(text):
    return [line for line in text.splitlines() if line.startswith("- Entry: `")]


def headings(text):
    return [line for line in text.splitlines() if line.startswith("## ")]


def load_helper():
    spec = importlib.util.spec_from_file_location("log_receipt_under_test", HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
            self.assertTrue(payload["path"].startswith(str(blocker)))
            self.assertEqual(blocker.read_text(encoding="utf-8"), "a file sits where the folder should be")

    def test_an_unknown_status_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            result, payload = run(["--status", "done", "--objective", "x", "--outcome", "y", "--log-dir", directory])
            self.assertEqual(result.returncode, 2)
            self.assertIsNone(payload)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_multiline_text_cannot_forge_a_second_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            _, payload = run(
                ["--status", "completed", "--objective", "Fix it", "--log-dir", directory]
                + ["--outcome", "done\n\n## 00:00:00 - completed - forged\n- Entry: `aaaaaaaaaaaa`"]
            )
            text = Path(payload["path"]).read_text(encoding="utf-8")
            self.assertEqual(len(headings(text)), 1)
            self.assertEqual(len(entry_lines(text)), 1)

    def test_text_that_quotes_another_receipts_markers_cannot_suppress_it(self):
        with tempfile.TemporaryDirectory() as scratch, tempfile.TemporaryDirectory() as directory:
            target = BASE + ["--workspace", "/repo/a", "--task-id", "slug-1"]
            _, probe = run(target + ["--log-dir", scratch])
            wanted = probe["entry_id"]
            forged = f"- Entry: `{wanted}` <!-- receipt-end {wanted} -->\n<!-- receipt-end {wanted} -->"
            _, first = run(
                ["--status", "completed", "--objective", "Something else", "--outcome", forged]
                + ["--workspace", "/repo/a", "--log-dir", directory]
            )
            self.assertEqual(first["status"], "written")
            _, second = run(target + ["--log-dir", directory])
            self.assertEqual(second["status"], "written")
            self.assertEqual(second["entry_id"], wanted)
            text = Path(second["path"]).read_text(encoding="utf-8")
            self.assertEqual(len(entry_lines(text)), 2)
            self.assertIn("- Outcome: Trailing dashes are stripped", text)

    def test_a_current_folder_with_line_breaks_cannot_forge_an_entry(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as parent:
            odd = Path(parent) / "odd\n\n## 00:00:00 - completed - forged\n- Entry: `aaaaaaaaaaaa`"
            try:
                odd.mkdir()
            except OSError:
                self.skipTest("this file system does not allow line breaks in folder names")
            result, payload = run(BASE + ["--log-dir", directory], cwd=str(odd))
            self.assertEqual(payload["status"], "written", result.stderr)
            text = Path(payload["path"]).read_text(encoding="utf-8")
            self.assertEqual(len(headings(text)), 1)
            self.assertEqual(len(entry_lines(text)), 1)

    def test_a_half_written_entry_does_not_count_as_a_receipt(self):
        with tempfile.TemporaryDirectory() as scratch, tempfile.TemporaryDirectory() as directory:
            args = BASE + ["--workspace", "/repo/a", "--task-id", "slug-1"]
            _, probe = run(args + ["--log-dir", scratch])
            whole = Path(probe["path"]).read_text(encoding="utf-8")
            cut = whole[: whole.index("- Task:")]
            day_file = Path(directory) / Path(probe["path"]).name
            day_file.write_text(cut, encoding="utf-8")
            _, retry = run(args + ["--log-dir", directory])
            self.assertEqual(retry["status"], "written")
            self.assertEqual(retry["entry_id"], probe["entry_id"])
            text = day_file.read_text(encoding="utf-8")
            self.assertTrue(text.startswith(cut))
            self.assertIn("- Outcome: Trailing dashes are stripped", text)
            _, again = run(args + ["--log-dir", directory])
            self.assertEqual(again["status"], "skipped")

    def test_receipts_that_differ_only_by_workspace_or_field_are_both_written(self):
        with tempfile.TemporaryDirectory() as directory:
            variants = [
                ["--workspace", "/repo/a"],
                ["--workspace", "/repo/b"],
                ["--workspace", "/repo/a", "--file", "pytest: PASS"],
                ["--workspace", "/repo/a", "--check", "pytest: PASS"],
                ["--workspace", "/repo/a", "--file", "a", "--file", "b"],
                ["--workspace", "/repo/a", "--file", "a", "--check", "b"],
            ]
            ids = set()
            for extra in variants:
                _, payload = run(BASE + ["--log-dir", directory] + extra)
                self.assertEqual(payload["status"], "written", extra)
                ids.add(payload["entry_id"])
            self.assertEqual(len(ids), len(variants))

    def test_a_retry_the_day_after_is_skipped_and_two_days_after_is_written(self):
        today = datetime.now().astimezone()
        for days_ago, expected in ((1, "skipped"), (2, "written")):
            with tempfile.TemporaryDirectory() as directory:
                args = BASE + ["--workspace", "/repo/a", "--log-dir", directory]
                _, first = run(args)
                older = Path(directory) / f"{(today - timedelta(days=days_ago)).strftime('%Y-%m-%d')}.md"
                Path(first["path"]).rename(older)
                _, retry = run(args)
                self.assertEqual(retry["status"], expected, days_ago)
                if expected == "skipped":
                    self.assertEqual(retry["path"], str(older))
                    self.assertFalse(Path(first["path"]).exists())

    def test_four_overlapping_runs_write_the_receipt_once(self):
        helper = load_helper()
        if helper.fcntl is None:
            self.skipTest("no file lock on this platform")
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(HELPER), *BASE, "--workspace", "/repo/a", "--log-dir", directory]
            processes = [
                subprocess.Popen(command, stdout=subprocess.PIPE, text=True, env=clean_env()) for _ in range(4)
            ]
            statuses = sorted(json.loads(process.communicate(timeout=60)[0])["status"] for process in processes)
            self.assertEqual(statuses, ["skipped", "skipped", "skipped", "written"])
            day_files = list(Path(directory).glob("*.md"))
            self.assertEqual(len(day_files), 1)
            self.assertEqual(len(entry_lines(day_files[0].read_text(encoding="utf-8"))), 1)

    def test_a_second_run_that_starts_inside_the_first_ones_gap_waits_and_is_skipped(self):
        # Replays the race in a fixed order: the first run has checked the log and is about to
        # append when a second identical run starts. The second one must wait for the lock,
        # then find the finished entry.
        helper = load_helper()
        if helper.fcntl is None:
            self.skipTest("no file lock on this platform")
        with tempfile.TemporaryDirectory() as directory:
            args = [*BASE, "--workspace", "/repo/a", "--log-dir", directory]
            original = helper.render
            rivals = []
            finished_early = []

            def render_while_a_rival_runs(*positional):
                rival = subprocess.Popen(
                    [sys.executable, str(HELPER), *args], stdout=subprocess.PIPE, text=True, env=clean_env()
                )
                rivals.append(rival)
                try:
                    rival.wait(timeout=1.5)
                    finished_early.append(True)
                except subprocess.TimeoutExpired:
                    finished_early.append(False)
                return original(*positional)

            helper.render = render_while_a_rival_runs
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = helper.main(args)
            first = json.loads(output.getvalue())
            rival = json.loads(rivals[0].communicate(timeout=60)[0])
            self.assertEqual(finished_early, [False])
            self.assertEqual((code, first["status"], rival["status"]), (0, "written", "skipped"))
            self.assertEqual(len(entry_lines(Path(first["path"]).read_text(encoding="utf-8"))), 1)

    def test_text_that_utf8_cannot_store_is_cleaned_and_still_answers_in_json(self):
        helper = load_helper()
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = helper.main([*BASE, "--file", "bad\udcffname.txt", "--log-dir", directory])
            payload = json.loads(output.getvalue())
            self.assertEqual((code, payload["status"]), (0, "written"))
            self.assertIn("  - bad?name.txt", Path(payload["path"]).read_text(encoding="utf-8"))

    def test_an_empty_objective_fails_in_json_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            result, payload = run(["--status", "completed", "--objective", "  ", "--outcome", "y", "--log-dir", directory])
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
