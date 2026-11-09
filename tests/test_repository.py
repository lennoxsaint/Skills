import json
import os
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

    def test_goal_is_installable_and_self_validating(self):
        payload = json.loads(self.run_cli("show", "goal").stdout)
        self.assertEqual(payload["path"], "goal")
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli("install", "goal", "--target-root", directory)
            installed = Path(directory) / "goal"
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertTrue((installed / "assets" / "goal.md.template").is_file())
            self.assertTrue((installed / "assets" / "progress.md.template").is_file())
            result = subprocess.run(
                [sys.executable, str(installed / "scripts" / "validate_goal_skill.py")],
                cwd=installed,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("PASS", result.stdout)

    def test_ambitious_is_installable(self):
        payload = json.loads(self.run_cli("show", "ambitious").stdout)
        self.assertEqual(payload["path"], "ambitious")
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli("install", "ambitious", "--target-root", directory)
            installed = Path(directory) / "ambitious"
            self.assertTrue((installed / "SKILL.md").is_file())
            for name in ("crew.md", "instruments.md", "judging.md", "report.md"):
                self.assertTrue((installed / "references" / name).is_file())
            for name in ("flight_check.mjs", "judge.mjs", "selftest.mjs"):
                self.assertTrue((installed / "scripts" / name).is_file())
            self.assertFalse(any((installed / "scripts").glob("test_*.py")))

    def test_hill_climb_is_installable(self):
        payload = json.loads(self.run_cli("show", "hill-climb").stdout)
        self.assertEqual(payload["path"], "hill-climb")
        with tempfile.TemporaryDirectory() as directory:
            self.run_cli("install", "hill-climb", "--target-root", directory)
            installed = Path(directory) / "hill-climb"
            self.assertTrue((installed / "SKILL.md").is_file())
            for name in ("answer-key.md", "hill-json.md", "safety.md"):
                self.assertTrue((installed / "references" / name).is_file())
            for name in ("hill.mjs", "climb.mjs", "score.mjs", "council.mjs", "board.mjs", "lib.mjs", "mine_tools.mjs", "selftest.mjs"):
                self.assertTrue((installed / "scripts" / name).is_file())
            self.assertFalse(any((installed / "scripts").glob("test_*.py")))

    def test_text_only_skills_install_with_their_references(self):
        expected = {
            "loop": ["references/rubric-adapters.md"],
            "adversarial-review": ["references/reviewer-contract.md"],
            "strategy-prompt": [],
        }
        for name, references in expected.items():
            payload = json.loads(self.run_cli("show", name).stdout)
            self.assertEqual(payload["path"], name)
            with tempfile.TemporaryDirectory() as directory:
                self.run_cli("install", name, "--target-root", directory)
                installed = Path(directory) / name
                self.assertTrue((installed / "SKILL.md").is_file(), name)
                self.assertTrue((installed / "agents" / "openai.yaml").is_file(), name)
                for reference in references:
                    self.assertTrue((installed / reference).is_file(), f"{name}: {reference}")

    def test_catalog_entries_tell_an_agent_when_to_use_each_skill(self):
        catalog = json.loads((REPO_ROOT / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(set(catalog["install"]), {"claude", "codex", "both", "update"})
        self.assertTrue((REPO_ROOT / catalog["agent_guide"]).is_file())
        for entry in catalog["skills"]:
            self.assertTrue(entry["use_when"].strip(), entry["name"])
            self.assertTrue(entry["try"].strip(), entry["name"])
            self.assertTrue(set(entry["hosts"]) <= {"claude", "codex"}, entry["name"])
        listing = self.run_cli("list").stdout
        self.assertIn("USE WHEN", listing)
        self.assertIn("hill-climb", listing)

    def test_llms_txt_carries_each_skill_with_its_try_prompt_and_needs(self):
        catalog = json.loads((REPO_ROOT / "catalog.json").read_text(encoding="utf-8"))
        lines = (REPO_ROOT / "llms.txt").read_text(encoding="utf-8").splitlines()
        for entry in catalog["skills"]:
            link = f"- [{entry['name']}](https://github.com/lennoxsaint/Skills/blob/main/{entry['path']}/SKILL.md)"
            matches = [line for line in lines if line.startswith(link)]
            self.assertEqual(len(matches), 1, entry["name"])
            self.assertIn(f'Try: "{entry["try"]}"', matches[0], entry["name"])
            self.assertIn(f"Needs: {entry['requires']}.", matches[0], entry["name"])

    def run_cli_with_homes(self, home, *args, check=True):
        environment = dict(os.environ)
        environment["CLAUDE_CONFIG_DIR"] = str(Path(home) / "claude-home")
        environment["CODEX_HOME"] = str(Path(home) / "codex-home")
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=REPO_ROOT,
            check=check,
            capture_output=True,
            text=True,
            env=environment,
        )

    def test_host_flag_installs_for_claude_codex_or_both(self):
        with tempfile.TemporaryDirectory() as home:
            claude = Path(home) / "claude-home" / "skills"
            codex = Path(home) / "codex-home" / "skills"
            self.run_cli_with_homes(home, "install", "goal", "--host", "claude")
            self.assertTrue((claude / "goal" / "SKILL.md").is_file())
            self.assertFalse((codex / "goal").exists())
            self.run_cli_with_homes(home, "install", "goal")
            self.assertTrue((codex / "goal" / "SKILL.md").is_file())
            result = self.run_cli_with_homes(home, "install", "hill-climb", "ambitious", "--host", "both")
            for root in (claude, codex):
                self.assertTrue((root / "hill-climb" / "SKILL.md").is_file())
                self.assertTrue((root / "ambitious" / "SKILL.md").is_file())
            self.assertIn("Try: ", result.stdout)

    def test_both_hosts_refuse_before_writing_anything(self):
        with tempfile.TemporaryDirectory() as home:
            claude = Path(home) / "claude-home" / "skills"
            codex = Path(home) / "codex-home" / "skills"
            self.run_cli_with_homes(home, "install", "goal", "--host", "codex")
            refused = self.run_cli_with_homes(home, "install", "goal", "--host", "both", check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("Refusing to overwrite", refused.stderr)
            self.assertFalse((claude / "goal").exists())

    def test_empty_target_root_is_refused_and_never_falls_back_to_a_host_folder(self):
        with tempfile.TemporaryDirectory() as home:
            refused = self.run_cli_with_homes(home, "install", "goal", "--target-root", "", "--update", check=False)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("--target-root is empty", refused.stderr)
            self.assertFalse((Path(home) / "codex-home").exists())
            self.assertFalse((Path(home) / "claude-home").exists())

    def test_both_hosts_sharing_one_folder_install_once(self):
        with tempfile.TemporaryDirectory() as home:
            shared = Path(home) / "shared-home"
            environment = dict(os.environ, CLAUDE_CONFIG_DIR=str(shared), CODEX_HOME=str(shared))
            result = subprocess.run(
                [sys.executable, str(CLI), "install", "goal", "save-10-percent", "--host", "both"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.count("Installed "), 2)
            self.assertIn("(claude+codex)", result.stdout)
            self.assertEqual(result.stdout.count("Needs: "), 2)
            self.assertEqual(result.stdout.count("Try: "), 2)
            self.assertTrue((shared / "skills" / "goal" / "SKILL.md").is_file())
            self.assertTrue((shared / "skills" / "save-10-percent" / "SKILL.md").is_file())

    def test_update_replaces_a_skill_and_keeps_a_backup_outside_the_skills_folder(self):
        with tempfile.TemporaryDirectory() as home:
            codex_home = Path(home) / "codex-home"
            installed = codex_home / "skills" / "goal"
            self.run_cli_with_homes(home, "install", "goal", "--host", "codex")
            (installed / "SKILL.md").write_text("my local edit\n", encoding="utf-8")
            result = self.run_cli_with_homes(home, "install", "goal", "--host", "codex", "--update")
            self.assertIn("Moved the previous copy to", result.stdout)
            self.assertIn("name: goal", (installed / "SKILL.md").read_text(encoding="utf-8"))
            backups = list((codex_home / "skills-backup").iterdir())
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "SKILL.md").read_text(encoding="utf-8"), "my local edit\n")
            self.assertEqual(sorted(path.name for path in (codex_home / "skills").iterdir()), ["goal"])

    def test_todo_check_ignores_code_formatting_only(self):
        sys.path.insert(0, str(CLI.parent))
        try:
            import skills
        finally:
            sys.path.pop(0)
        strip = skills.CODE_SPAN_PATTERN.sub
        self.assertNotIn("TODO", strip("", "Done when no `TODO` remains."))
        self.assertNotIn("TODO", strip("", "```json\n{\"goal\": \"TODO\"}\n```"))
        self.assertIn("TODO", strip("", "TODO: write this section"))

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
