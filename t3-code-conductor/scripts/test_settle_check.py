import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GATE = Path(__file__).resolve().parent / "settle_check.py"

DONE = "All five checks pass and the pull request is merged. Proof is in the run folder. Next: nothing."
ASKS = "The draft is ready and the page is staged. It still needs your yes before it goes live. Your call."
PLAIN = "The export finished and the file is saved in the run folder where the brief asked for it to be."


class SettleGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "state.sqlite"
        self.log = Path(self.temp.name) / "run" / "settle-log.jsonl"
        con = sqlite3.connect(self.db)
        con.executescript(
            "create table orchestration_v2_projection_threads (thread_id text, title text, payload_json text);"
            "create table orchestration_v2_projection_runs (thread_id text, ordinal integer, status text);"
            "create table orchestration_v2_projection_messages "
            "(thread_id text, role text, created_at text, payload_json text);"
        )
        con.commit()
        con.close()

    def tearDown(self):
        self.temp.cleanup()

    def thread(self, tid, text, run="completed", parent=None, prs=None, at="2026-01-01T00:00:00.000Z"):
        payload = {"createdBy": "agent", "pullRequests": prs or []}
        if parent:
            payload["lineage"] = {"parentThreadId": parent}
        con = sqlite3.connect(self.db)
        con.execute("insert into orchestration_v2_projection_threads values (?,?,?)",
                    (tid, f"title {tid}", json.dumps(payload)))
        con.execute("insert into orchestration_v2_projection_runs values (?,?,?)", (tid, 1, run))
        con.execute("insert into orchestration_v2_projection_messages values (?,?,?,?)",
                    (tid, "assistant", at, json.dumps({"text": text})))
        con.commit()
        con.close()

    def gate(self, *args, stdin=None, env=None):
        full = dict(os.environ, T3_STATE_DB=str(self.db), CONDUCTOR_SETTLE_LOG=str(self.log))
        full.pop("T3CODE_THREAD_ID", None)
        full.update(env or {})
        return subprocess.run([sys.executable, str(GATE), *args], input=stdin,
                              capture_output=True, text=True, env=full)

    def verdict(self, tid):
        return json.loads(self.gate("--json", tid).stdout)[0]

    def hook(self, tool_input, env=None):
        return self.gate("--hook", stdin=json.dumps({"tool_input": tool_input}), env=env)

    def test_finished_root_is_allowed(self):
        self.thread("a", PLAIN)
        result = self.gate("a")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith("ALLOW"))

    def test_root_that_asks_the_owner_is_blocked(self):
        self.thread("a", ASKS)
        result = self.gate("a")
        self.assertEqual(result.returncode, 1)
        self.assertIn("asks the owner", result.stdout)

    def test_child_is_allowed_whatever_it_says(self):
        self.thread("kid", ASKS, parent="a")
        self.assertEqual(self.verdict("kid")["verdict"], "ALLOW")

    def test_failed_or_running_last_run_is_blocked(self):
        self.thread("f", PLAIN, run="failed")
        self.thread("r", PLAIN, run="running")
        self.assertEqual(self.verdict("f")["reasons"], ["last run failed"])
        self.assertEqual(self.verdict("r")["verdict"], "BLOCK")

    def test_open_linked_pull_request_is_blocked(self):
        self.thread("a", PLAIN, prs=[{"number": 7, "snapshot": {"state": "open", "isDraft": True}}])
        self.thread("b", PLAIN, prs=[{"number": 8, "snapshot": {"state": "merged"}}])
        self.assertIn("linked PR #7 is open (draft)", self.verdict("a")["reasons"])
        self.assertEqual(self.verdict("b")["verdict"], "ALLOW")

    def test_next_nothing_quiets_text_signals_but_not_blocked(self):
        self.thread("a", "The proof is filed. You answer the desk card whenever you like. Next: nothing.")
        self.thread("b", "BLOCKED on the sign-in, so this cannot go further today. Next: nothing.")
        self.assertEqual(self.verdict("a")["verdict"], "ALLOW")
        self.assertEqual(self.verdict("b")["verdict"], "BLOCK")

    def test_unknown_thread_and_empty_thread_are_blocked(self):
        self.thread("empty", "ok")
        self.assertEqual(self.verdict("nope")["kind"], "unknown")
        self.assertEqual(self.verdict("empty")["reasons"], ["no final message to read"])

    def test_proof_unblocks_and_is_logged(self):
        self.thread("a", ASKS)
        self.assertEqual(self.gate("--proof", "merged in pull request 12, run folder proof.md", "a").returncode, 0)
        after = self.verdict("a")
        self.assertEqual(after["verdict"], "ALLOW")
        self.assertIn("pull request 12", after["proof"])
        record = json.loads(self.log.read_text().splitlines()[-1])
        self.assertEqual(record["thread"], "a")
        self.assertTrue(record["signals"])

    def test_proof_older_than_the_last_message_does_not_count(self):
        self.thread("a", ASKS, at="2999-01-01T00:00:00.000Z")
        self.gate("--proof", "merged in pull request 12, run folder proof.md", "a")
        self.assertEqual(self.verdict("a")["verdict"], "BLOCK")

    def test_proof_needs_one_thread_and_real_text(self):
        self.thread("a", ASKS)
        self.thread("b", ASKS)
        self.assertNotEqual(self.gate("--proof", "done", "a").returncode, 0)
        self.assertNotEqual(self.gate("--proof", "merged in pull request 12", "a", "b").returncode, 0)
        self.assertFalse(self.log.exists())

    def test_hook_denies_an_open_root_and_logs_it(self):
        self.thread("a", ASKS)
        out = json.loads(self.hook({"action": "settle", "threadId": "a"}).stdout)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("SETTLE GATE", out["permissionDecisionReason"])
        self.assertEqual(json.loads(self.log.read_text().splitlines()[-1])["gate"], "BLOCK")

    def test_hook_still_denies_when_the_log_cannot_be_written(self):
        self.thread("a", ASKS)
        blocker = Path(self.temp.name) / "file"
        blocker.write_text("x")
        result = self.hook({"action": "settle", "threadId": "a"},
                           env={"CONDUCTOR_SETTLE_LOG": str(blocker / "settle-log.jsonl")})
        self.assertIn('"deny"', result.stdout)

    def test_hook_allows_everything_that_is_not_an_open_root_settle(self):
        self.thread("a", ASKS)
        self.thread("done", DONE)
        self.thread("kid", ASKS, parent="a")
        calls = [
            ({"action": "settle", "threadId": "done"}, None),
            ({"action": "settle", "threadId": "kid"}, None),
            ({"action": "snooze", "threadId": "a"}, None),
            ({"action": "unsettle", "threadId": "a"}, None),
            ({"action": "settle", "threadId": "a", "environmentId": "other-machine"}, None),
            ({"action": "settle", "threadId": "a"}, {"T3CODE_THREAD_ID": "a"}),
            ({"action": "settle", "threadId": "missing"}, None),
        ]
        for tool_input, env in calls:
            result = self.hook(tool_input, env=env)
            self.assertEqual((result.returncode, result.stdout), (0, ""), tool_input)

    def test_hook_fails_open_on_bad_input_or_a_missing_database(self):
        self.assertEqual(self.gate("--hook", stdin="not json").stdout, "")
        result = self.hook({"action": "settle", "threadId": "a"}, env={"T3_STATE_DB": str(self.db) + ".gone"})
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_hook_allows_after_proof(self):
        self.thread("a", ASKS)
        self.gate("--proof", "merged in pull request 12, run folder proof.md", "a")
        self.assertEqual(self.hook({"action": "settle", "threadId": "a"}).stdout, "")

    def test_owner_names_extend_the_owner_patterns(self):
        self.thread("a", "The copy is staged and the links were checked twice. It waits on Robin to pick a date.")
        self.assertEqual(self.verdict("a")["verdict"], "ALLOW")
        named = json.loads(self.gate("--json", "a", env={"CONDUCTOR_OWNER_NAMES": "Robin"}).stdout)[0]
        self.assertEqual(named["verdict"], "BLOCK")

    def test_the_database_is_never_written(self):
        self.thread("a", ASKS)
        before = self.db.read_bytes()
        self.gate("a")
        self.gate("--proof", "merged in pull request 12, run folder proof.md", "a")
        self.hook({"action": "settle", "threadId": "a"})
        self.assertEqual(self.db.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
