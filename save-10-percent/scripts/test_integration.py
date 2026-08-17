#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "save-10-percent"
SCRIPTS = SKILL_DIR / "scripts"


def run_script(name, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *map(str, args)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def run_repo_script(name, *args):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / name), *map(str, args)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


class CommandLineWorkflowTests(unittest.TestCase):
    def test_synthetic_pipeline_reaches_exhaustive_aud_70_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            normalized = root / "normalized.json"
            reconciled = root / "reconciled.json"
            coverage = root / "coverage.json"
            recurring = root / "recurring.json"
            baseline = root / "baseline.json"
            run_script(
                "normalize_transactions.py",
                REPO_ROOT / "examples" / "save-10-percent" / "sample-transactions.csv",
                normalized,
                "--account-id",
                "checking",
                "--account-type",
                "checking",
            )
            normalized_payload = json.loads(normalized.read_text())
            manifest = normalized_payload["source_manifest"]
            self.assertEqual(manifest["period_start"], "2025-03-03")
            self.assertEqual(manifest["period_end"], "2026-03-20")
            run_script("reconcile_transactions.py", normalized, reconciled)
            run_script("assess_coverage.py", reconciled, REPO_ROOT / "examples" / "save-10-percent" / "sample-scope.json", coverage)
            run_script("detect_recurring.py", reconciled, recurring)
            run_script("build_baseline.py", recurring, coverage, baseline)
            coverage_payload = json.loads(coverage.read_text())
            baseline_payload = json.loads(baseline.read_text())
            self.assertEqual(coverage_payload["coverage_state"], "exhaustive_pass")
            self.assertEqual(coverage_payload["account_coverage"][0]["covered_calendar_months"], 13)
            self.assertEqual(baseline_payload["monthly_controllable_spend"], 70)
            self.assertEqual(baseline_payload["ten_percent_target"], 7)
            self.assertEqual(len(baseline_payload["baseline_hash"]), 64)
            self.assertEqual(len(coverage_payload["source_content_hashes"]), 1)
            self.assertEqual(len(coverage_payload["reconciliation_hash"]), 64)

    def test_release_zip_is_deterministic_and_contains_only_skill_folder(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.zip"
            second = Path(directory) / "second.zip"
            run_repo_script("build_skill_release.py", SKILL_DIR, first)
            run_repo_script("build_skill_release.py", SKILL_DIR, second)
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), hashlib.sha256(second.read_bytes()).hexdigest())
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
            self.assertIn("save-10-percent/SKILL.md", names)
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))
            self.assertFalse(any(Path(name).name.startswith("test_") for name in names))
            self.assertTrue(all(name.startswith("save-10-percent/") for name in names))

    def test_case_cli_resumes_from_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            created = run_script("case_state.py", "create", "--root", directory, "--currency", "AUD")
            case_dir = json.loads(created.stdout)["case_dir"]
            run_script("case_state.py", "transition", case_dir, "scope", "--data", '{"scope_confirmed": true}')
            shown = run_script("case_state.py", "show", case_dir)
            self.assertEqual(json.loads(shown.stdout)["snapshot"]["state"], "scope")


if __name__ == "__main__":
    unittest.main()
