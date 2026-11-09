"""Run the hill-climb checks from Python's unittest runner.

The validate and release workflows discover `test_*.py` in each skill's scripts folder.

Two fast checks run everywhere Node and git exist: every script parses, and `hill.mjs init`
creates a hill in a temp folder. The full self test (`node selftest.mjs`) needs the machine's
sandbox (`sandbox-exec` on macOS) and takes about 10 minutes, so it runs only when
`HILL_CLIMB_FULL_SELFTEST=1` is set. The macOS workflow sets it.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


def find_node(test: unittest.TestCase) -> str:
    node = shutil.which("node")
    if node is None:
        if os.environ.get("CI"):
            test.fail("Node 18+ is required in CI to check hill-climb/scripts")
        test.skipTest("Node is not installed")
    return node


class HillClimbScriptTests(unittest.TestCase):
    def test_every_script_parses(self):
        node = find_node(self)
        scripts = sorted(SCRIPTS.glob("*.mjs"))
        self.assertGreaterEqual(len(scripts), 8)
        for script in scripts:
            result = subprocess.run([node, "--check", str(script)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, f"{script.name}: {result.stderr[-2000:]}")

    def test_init_creates_a_scratch_hill(self):
        node = find_node(self)
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        with tempfile.TemporaryDirectory(prefix="hill-climb-test-") as root:
            hill, work = Path(root) / "hill", Path(root) / "work"
            result = subprocess.run(
                [node, str(SCRIPTS / "hill.mjs"), "init", str(hill), "--name", "smoke", "--scratch", "--worktree", str(work)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr)[-2000:])
            self.assertEqual(json.loads(result.stdout)["status"], "ok")
            spec = json.loads((hill / "hill.json").read_text(encoding="utf-8"))
            self.assertEqual(spec["branch"], "hill/smoke")
            self.assertEqual(spec["sandbox"], "auto")
            self.assertTrue((work / ".git").exists())
            for folder in ("cases/pool", "exemplars", "scorer", "runs"):
                self.assertTrue((hill / folder).is_dir(), folder)

    def test_full_selftest_passes(self):
        if os.environ.get("HILL_CLIMB_FULL_SELFTEST") != "1":
            self.skipTest("set HILL_CLIMB_FULL_SELFTEST=1 to run the full self test (needs the sandbox, takes about 10 minutes)")
        node = find_node(self)
        if shutil.which("sandbox-exec") is None and shutil.which("bwrap") is None:
            self.fail("the full self test needs sandbox-exec (macOS) or bwrap (Linux)")
        result = subprocess.run(
            [node, str(SCRIPTS / "selftest.mjs")],
            cwd=SCRIPTS,
            capture_output=True,
            text=True,
            timeout=3300,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output[-6000:])
        summary = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual(summary["status"], "ok", output[-6000:])
        self.assertGreater(summary["total"], 0)
        self.assertEqual(summary["passed"], summary["total"], output[-6000:])


if __name__ == "__main__":
    unittest.main()
