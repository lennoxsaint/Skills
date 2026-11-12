import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DESK = Path(__file__).resolve().parent / "desk.py"


class DeskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name) / "run"
        self.run_desk("init")

    def tearDown(self):
        self.temp.cleanup()

    def run_desk(self, *args, check=True):
        result = subprocess.run(
            [sys.executable, str(DESK), "--dir", str(self.folder), *args],
            capture_output=True, text=True,
        )
        if check and result.returncode != 0:
            self.fail(f"desk.py {' '.join(args)} failed: {result.stderr}")
        return result

    def desk(self):
        return json.loads((self.folder / "desk.json").read_text(encoding="utf-8"))

    def test_init_creates_files_and_never_overwrites(self):
        for name in ("CONDUCTOR.md", "ROSTER.md", "LEDGER.md", "STANDING.md", "desk.json"):
            self.assertTrue((self.folder / name).is_file(), name)
        (self.folder / "STANDING.md").write_text("mine", encoding="utf-8")
        result = json.loads(self.run_desk("init").stdout)
        self.assertEqual(result["created"], [])
        self.assertEqual((self.folder / "STANDING.md").read_text(encoding="utf-8"), "mine")

    def test_ledger_appends_and_keeps_old_lines(self):
        self.run_desk("ledger", "census: 12 open, 12 mapped")
        self.run_desk("ledger", "dispatched lane-a")
        text = (self.folder / "LEDGER.md").read_text(encoding="utf-8")
        self.assertIn("census: 12 open, 12 mapped", text)
        self.assertLess(text.index("census"), text.index("dispatched lane-a"))

    def test_ledger_line_cannot_forge_a_second_line(self):
        self.run_desk("ledger", "one\n- fake line")
        lines = [line for line in (self.folder / "LEDGER.md").read_text(encoding="utf-8").splitlines() if line.startswith("- ")]
        self.assertEqual(len(lines), 1)

    def test_add_answer_route_flow(self):
        self.run_desk("add", "c-launch", "--title", "Ship the launch page?", "--yes", "Ship it", "--lane", "web")
        self.assertEqual(self.desk()["cards"]["c-launch"]["state"], "open")
        refused = self.run_desk("routed", "c-launch", "--lane", "web", check=False)
        self.assertEqual(refused.returncode, 1)
        self.run_desk("answer", "c-launch", "--choice", "yes", "--note", "after lunch")
        self.run_desk("routed", "c-launch", "--lane", "web")
        card = self.desk()["cards"]["c-launch"]
        self.assertEqual((card["state"], card["choice"], card["routed_to"]), ("done", "yes", "web"))

    def test_duplicate_and_bad_ids_are_refused(self):
        self.run_desk("add", "c-one", "--title", "One", "--yes", "Yes")
        self.assertEqual(self.run_desk("add", "c-one", "--title", "Again", "--yes", "Yes", check=False).returncode, 1)
        self.assertEqual(self.run_desk("add", "Bad Id", "--title", "x", "--yes", "y", check=False).returncode, 1)

    def test_over_long_text_is_refused(self):
        result = self.run_desk("add", "c-long", "--title", "x" * 121, "--yes", "y", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("limit", result.stderr)

    def test_lint_catches_local_paths_and_plain_links(self):
        self.run_desk("add", "c-path", "--title", "Look at the cut", "--yes", "Approve",
                      "--why", "The file is at /Users/someone/cut.mp4")
        self.run_desk("add", "c-link", "--title", "Read the doc", "--yes", "Approve", "--link", "http://example.com/doc")
        self.run_desk("add", "c-home", "--title", "Notes", "--yes", "Approve", "--why", "see ~/notes.md")
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("c-path", result.stdout)
        self.assertIn("c-link", result.stdout)
        self.assertIn("c-home", result.stdout)
        render = self.run_desk("render", check=False)
        self.assertEqual(render.returncode, 1)

    def test_render_escapes_text_and_loads_nothing_remote(self):
        self.run_desk("add", "c-xss", "--title", "<script>alert(1)</script>", "--yes", "Yes <b>now</b>",
                      "--link", "https://example.com/a?b=1&c=2")
        self.run_desk("render")
        page = (self.folder / "review.html").read_text(encoding="utf-8")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<b>", page)
        self.assertNotIn(" src=", page)
        self.assertNotIn("<link", page)
        self.assertIn("answer c-xss yes", page)

    def test_show_ranks_due_first_then_priority(self):
        self.run_desk("add", "c-later", "--title", "Later", "--yes", "y", "--priority", "1")
        self.run_desk("add", "c-due", "--title", "Due", "--yes", "y", "--due", "2026-01-02", "--priority", "5")
        self.run_desk("add", "c-urgent", "--title", "Urgent", "--yes", "y", "--priority", "1", "--due", "2026-01-02")
        order = [card["id"] for card in json.loads(self.run_desk("show", "--json").stdout)]
        self.assertEqual(order, ["c-urgent", "c-due", "c-later"])

    def test_parallel_writers_lose_no_cards(self):
        procs = [
            subprocess.Popen([sys.executable, str(DESK), "--dir", str(self.folder), "add", f"c-{n}", "--title", f"Card {n}", "--yes", "y"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for n in range(6)
        ]
        for proc in procs:
            proc.communicate()
            self.assertEqual(proc.returncode, 0)
        self.assertEqual(len(self.desk()["cards"]), 6)
        self.assertFalse((self.folder / ".desk.lock").exists())

    def test_conductor_home_environment_variable_picks_the_folder(self):
        other = Path(self.temp.name) / "from-env"
        env = dict(os.environ, CONDUCTOR_HOME=str(other))
        subprocess.run([sys.executable, str(DESK), "init"], check=True, capture_output=True, env=env)
        self.assertTrue((other / "desk.json").is_file())


if __name__ == "__main__":
    unittest.main()
