"""Run the Node self test for the ambitious skill from Python's unittest runner.

The release and validate workflows discover `test_*.py` in each skill's scripts folder,
so this wrapper makes them run `node selftest.mjs`. In CI a missing Node is a failure;
on a local machine without Node the test is skipped.
"""

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


class AmbitiousSelfTest(unittest.TestCase):
    def test_node_selftest_passes(self):
        node = shutil.which("node")
        if node is None:
            if os.environ.get("CI"):
                self.fail("Node 18+ is required in CI to run ambitious/scripts/selftest.mjs")
            self.skipTest("Node is not installed")
        result = subprocess.run(
            [node, str(SCRIPTS / "selftest.mjs")],
            cwd=SCRIPTS,
            capture_output=True,
            text=True,
            timeout=600,
        )
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output[-4000:])
        summary = re.search(r"(\d+)/(\d+) passed", output)
        self.assertIsNotNone(summary, output[-4000:])
        passed, total = map(int, summary.groups())
        self.assertGreater(total, 0)
        self.assertEqual(passed, total, output[-4000:])


if __name__ == "__main__":
    unittest.main()
