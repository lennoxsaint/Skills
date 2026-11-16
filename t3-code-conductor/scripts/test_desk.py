import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

DESK = Path(__file__).resolve().parent / "desk.py"


def desk_module():
    """desk.py imported in-process, for checks too many to run one command at a time."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("desk", DESK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def test_outcomes_card_keeps_goal_and_history_in_order(self):
        self.run_desk("add", "c-lane", "--title", "Ship the pricing page now?", "--yes", "Ship it",
                      "--goal", "A pricing page that converts <better>",
                      "--outcome", "2026-11-14 09:10|Draft passed outside review",
                      "--outcome", "2026-11-15|Staging build green|https://ci.example.com/run/7")
        card = self.desk()["cards"]["c-lane"]
        self.assertEqual(card["goal"], "A pricing page that converts <better>")
        self.assertEqual([entry["text"] for entry in card["history"]],
                         ["Draft passed outside review", "Staging build green"])
        self.assertEqual(card["history"][1]["link"], "https://ci.example.com/run/7")
        self.assertEqual(card["history"][0]["link"], "")
        self.run_desk("render")
        page = (self.folder / "review.html").read_text(encoding="utf-8")
        self.assertIn('class="timeline"', page)
        self.assertIn("&lt;better&gt;", page)
        self.assertLess(page.index("Draft passed outside review"), page.index("Staging build green"))
        self.assertIn('href="https://ci.example.com/run/7"', page)

    def test_outcome_entries_are_checked(self):
        bad = [
            ("c-date", "yesterday|Did a thing"),
            ("c-empty", "2026-11-14|"),
            ("c-long", "2026-11-14|" + "x" * 141),
        ]
        for card_id, entry in bad:
            result = self.run_desk("add", card_id, "--title", "T", "--yes", "Y", "--outcome", entry, check=False)
            self.assertEqual(result.returncode, 1, card_id)
        many = []
        for day in range(1, 14):
            many += ["--outcome", f"2026-11-{day:02d}|step {day}"]
        result = self.run_desk("add", "c-many", "--title", "T", "--yes", "Y", *many, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.desk()["cards"], {})

    def test_lint_catches_local_paths_and_plain_links_in_history(self):
        self.run_desk("add", "c-hpath", "--title", "T", "--yes", "Y", "--outcome", "2026-11-14|Saved to /Users/someone/out")
        refused = self.run_desk("add", "c-hlink", "--title", "T", "--yes", "Y",
                                "--outcome", "2026-11-14|Built|http://example.com/run", check=False)
        self.assertEqual(refused.returncode, 1)
        self.hand_edit("c-hlink", history=[{"at": "2026-11-14", "text": "Built", "link": "http://example.com/run"}])
        self.run_desk("add", "c-goal", "--title", "T", "--yes", "Y", "--goal", "Fix ~/notes.md")
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        for card_id in ("c-hpath", "c-hlink", "c-goal"):
            self.assertIn(card_id, result.stdout)

    def hand_edit(self, card_id, **fields):
        self.run_desk("add", card_id, "--title", "T", "--yes", "Y")
        data = self.desk()
        data["cards"][card_id].update(fields)
        (self.folder / "desk.json").write_text(json.dumps(data), encoding="utf-8")

    def test_hand_edited_history_is_held_to_the_same_rules(self):
        bad = {
            "c-path-at": [{"at": "/Users/example/private.txt", "text": "Built"}],
            "c-feb30": [{"at": "2026-02-30", "text": "Built"}],
            "c-hour25": [{"at": "2026-11-14 25:00", "text": "Built"}],
            "c-long-at": [{"at": "2" * 4000, "text": "Built"}],
            "c-no-text": [{"at": "2026-11-14"}],
            "c-not-list": "broken",
            "c-null": None,
            "c-not-object": ["2026-11-14|Built"],
        }
        for card_id, history in bad.items():
            self.hand_edit(card_id, history=history)
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        for card_id in bad:
            self.assertIn(card_id, result.stdout)
        render = self.run_desk("render", check=False)
        self.assertEqual(render.returncode, 1)
        self.assertNotIn("Traceback", render.stderr)
        self.assertFalse((self.folder / "review.html").exists() and "private.txt" in (self.folder / "review.html").read_text(encoding="utf-8"))

    def test_hand_edited_fields_of_the_wrong_type_fail_lint_cleanly(self):
        bad = {"c-goal-num": {"goal": 42}, "c-goal-list": {"goal": ["Ship"]}, "c-goal-dict": {"goal": {"text": "Ship"}},
               "c-title-num": {"title": 7}, "c-links-str": {"links": "https://example.com"}, "c-links-null": {"links": None},
               "c-due-num": {"due": 5}, "c-priority-str": {"priority": "high"}}
        for card_id, fields in bad.items():
            self.hand_edit(card_id, **fields)
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        for card_id in bad:
            self.assertIn(card_id, result.stdout)
        render = self.run_desk("render", check=False)
        self.assertEqual(render.returncode, 1)
        self.assertNotIn("Traceback", render.stderr)

    def test_local_paths_after_any_punctuation_are_caught(self):
        self.run_desk("add", "c-colon", "--title", "T", "--yes", "Y", "--goal", "Fix:/Users/example/private.txt")
        self.run_desk("add", "c-bracket", "--title", "T", "--yes", "Y", "--outcome", "2026-11-14|Built [/Users/example/private.txt]")
        self.run_desk("add", "c-tmp", "--title", "T", "--yes", "Y", "--why", "Saved at /tmp/run/out.txt")
        self.run_desk("add", "c-volume", "--title", "Copy,/Volumes/Drive/x ok?", "--yes", "Y")
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        for card_id in ("c-colon", "c-bracket", "c-tmp", "c-volume"):
            self.assertIn(card_id, result.stdout)
        self.assertEqual(self.run_desk("render", check=False).returncode, 1)

    def test_https_links_that_mention_users_or_home_still_pass(self):
        self.run_desk("add", "c-ok", "--title", "Ship the home page?", "--yes", "Y",
                      "--link", "https://example.com/Users/guide", "--outcome", "2026-11-14|Merged|https://example.com/home/run/7")
        self.run_desk("lint")

    def test_a_local_path_right_after_an_https_link_is_caught(self):
        quoted = 'See "https://example.test/proof"(/Users/example/private.txt)'
        self.run_desk("add", "c-goal", "--title", "T", "--yes", "Y", "--goal", quoted)
        self.run_desk("add", "c-text", "--title", "T", "--yes", "Y", "--outcome", f"2026-11-14|{quoted}")
        self.hand_edit("c-title", title=quoted)
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        for card_id in ("c-goal", "c-text", "c-title"):
            self.assertIn(card_id, result.stdout)
        self.assertEqual(self.run_desk("render", check=False).returncode, 1)
        paths = ["/Users/example/private.txt", "/home/example/private.txt", "/Volumes/Drive/private.txt",
                 "/private/run/private.txt", "/tmp/run/private.txt", "~/private.txt", "C:\\private.txt", "file:///secret.txt"]
        missed = [(mark, path) for mark in "\"'<>`[]{}\\()|^ " for path in paths
                  if not desk_module().names_local_path(f"https://example.test/proof{mark}{path}")]
        self.assertEqual(missed, [])

    def test_a_path_word_inside_a_longer_word_is_not_a_path(self):
        self.run_desk("add", "c-metric", "--title", "Track the metric users/home/views?", "--yes", "Track it")
        self.run_desk("add", "c-docs", "--title", "Our docs/home/guide changed?", "--yes", "Y")
        self.run_desk("add", "c-key", "--title", "Is the JSON key /private/ reserved?", "--yes", "Y")
        self.run_desk("lint")
        self.run_desk("render")

    def test_an_outcome_link_of_the_wrong_type_fails_lint_cleanly(self):
        for n, link in enumerate([None, 0, False, [], {}]):
            self.hand_edit(f"c-link-{n}", history=[{"at": "2026-11-14", "text": "Built", "link": link}])
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        for n in range(5):
            self.assertIn(f"c-link-{n}", result.stdout)
        self.assertEqual(self.run_desk("render", check=False).returncode, 1)

    def test_links_must_name_a_host_a_phone_can_reach(self):
        bad = ["https://", "https:///Users/example/private.txt", "https://localhost/x", "https://127.0.0.1/x"]
        for n, link in enumerate(bad):
            self.hand_edit(f"c-host-{n}", links=[link])
        self.run_desk("add", "c-query", "--title", "T", "--yes", "Y", "--link", "https://example.test/search?q=desk&page=2")
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        for n in range(len(bad)):
            self.assertIn(f"c-host-{n}", result.stdout)
        self.assertNotIn("c-query", result.stdout)

    def test_a_quoted_folder_name_is_still_a_path(self):
        for card_id, goal in (("c-quoted", 'Saved to /Users/"example"/private.txt'),
                              ("c-angled", "Saved to /home/<example>/private.txt")):
            self.run_desk("add", card_id, "--title", "T", "--yes", "Y", "--goal", goal)
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        for card_id in ("c-quoted", "c-angled"):
            self.assertIn(card_id, result.stdout)
        self.assertEqual(self.run_desk("render", check=False).returncode, 1)
        self.assertFalse((self.folder / "review.html").exists())
        self.assertFalse(desk_module().names_local_path('Is the JSON key "/private/" reserved?'))

    def test_brackets_inside_a_query_stay_part_of_the_link(self):
        for card_id, goal in (("c-query", "https://example.test/?q=(all)&next=/Users/x"),
                              ("c-open", "https://example.test/search?next=(/Users/example/private.txt")):
            self.run_desk("add", card_id, "--title", "T", "--yes", "Y", "--goal", goal)
        self.run_desk("lint")
        self.run_desk("render")
        desk = desk_module()
        self.assertTrue(desk.names_local_path("https://example.test/proof(/Users/example/private.txt)"))
        self.assertTrue(desk.names_local_path('https://example.test/?q="/Users/example/private.txt"'))

    def test_valid_https_links_pass_after_parsing(self):
        links = ["https://bücher.example/x", "https://a@b.test/x", "https://example.test./x",
                 "https://example.test:000443/x", "https://user@例え.example.:00443/x"]
        for n, link in enumerate(links):
            self.run_desk("add", f"c-ok-{n}", "--title", "T", "--yes", "Y", "--link", link,
                          "--outcome", f"2026-11-14|Built|{link}")
        self.run_desk("lint")
        self.run_desk("render")

    def test_ip_literals_and_bad_ports_are_refused(self):
        bad = ["https://0x7f.0.0.1/x", "https://example.test:99999/x", "https://0177.0.0.1/x", "https://example.test:65536/x"]
        for n, link in enumerate(bad):
            refused = self.run_desk("add", f"c-bad-{n}", "--title", "T", "--yes", "Y",
                                    "--outcome", f"2026-11-14|Built|{link}", check=False)
            self.assertEqual(refused.returncode, 1, link)
            self.hand_edit(f"c-bad-{n}", links=[link], history=[{"at": "2026-11-14", "text": "Built", "link": link}])
        result = self.run_desk("lint", check=False)
        self.assertEqual(result.returncode, 1)
        for n in range(len(bad)):
            self.assertIn(f"c-bad-{n}", result.stdout)
        self.assertEqual(self.run_desk("render", check=False).returncode, 1)
        self.assertFalse((self.folder / "review.html").exists())
        desk = desk_module()
        for link in ("https://[::1]/x", "https://example.test:0/x", "https://1.2.3.0x4/x", "https://app.localhost/x",
                     "https://127.0.0.1\\@example.test/x", "https://example.test/a b"):
            self.assertFalse(desk.is_phone_link(link), link)

    def test_a_path_word_after_a_non_ascii_letter_is_not_a_path(self):
        for card_id, goal in (("c-accent", "é/Users/x"), ("c-cafe", "café/home/notes")):
            self.run_desk("add", card_id, "--title", "T", "--yes", "Y", "--goal", goal)
        self.run_desk("lint")
        self.run_desk("render")
        self.assertTrue(desk_module().names_local_path("Fix_/Users/example/private.txt"))

    def test_a_bar_inside_outcome_text_is_refused_at_add(self):
        result = self.run_desk("add", "c-bar", "--title", "T", "--yes", "Y",
                               "--outcome", "2026-11-14|Merged A | B|https://example.test/p", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("|", result.stderr)
        self.assertEqual(self.desk()["cards"], {})

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

    def test_dir_works_after_the_command_too(self):
        later = Path(self.temp.name) / "after"
        subprocess.run([sys.executable, str(DESK), "init", "--dir", str(later)], check=True, capture_output=True)
        subprocess.run([sys.executable, str(DESK), "add", "c-late", "--title", "Late?", "--yes", "y", "--dir", str(later)],
                       check=True, capture_output=True)
        self.assertIn("c-late", (later / "desk.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
