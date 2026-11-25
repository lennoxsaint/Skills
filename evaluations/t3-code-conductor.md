# T3 Code Conductor evaluation

Version: 1.4.0

## What was tested

The author ran this method by hand in T3 Code before it was a skill. This is the first time it is written as one, with the machines, accounts, thread ids and private rules taken out. The review page helper, `scripts/desk.py`, is new.

### The review page helper

`scripts/test_desk.py` has 12 unit tests. All 12 pass locally, and CI runs them on every push. They cover:

- `init` writes each file once and never overwrites one that exists
- the ledger only appends, and one call cannot forge a second line
- add, answer, routed and close in order; a card cannot be routed before it is answered
- duplicate and malformed card ids are refused
- text over its length limit is refused
- `lint` refuses local paths and `http://` links, and `render` refuses to run while `lint` fails
- the page escapes every value and loads no scripts or remote files
- cards rank by due date, then priority, then age
- six writers at once lose no card
- the run folder can come from `CONDUCTOR_HOME`, or from `--dir` before or after the command

### The settle gate

`scripts/test_settle_check.py` has 17 unit tests against a made-up T3 database. All 17 pass locally, and CI runs them with the desk tests (29 in all). They cover:

- a finished top-level thread passes; one that asks the owner, has a failed or running last run, or has an open linked pull request is blocked
- a child thread always passes; an unknown or empty thread is blocked
- "Next: nothing" quiets wording signals but not "blocked"
- a proof line unblocks one thread, is logged, needs real text, and stops counting once the thread writes again
- the hook refuses an open top-level settle, still refuses when its log cannot be written, lets every other call through, and fails open on bad input or a missing database
- the database is never written

**Live audit, one fleet, 19 to 21 Nov 2026.** A conductor and its helpers settled 165 top-level threads in three days. Two judges on a cheaper model read each thread's last messages, and the author checked and corrected three labels: 120 were really closed (73%) and 45 were still open (27%). Most wrong settles came from bulk settles (one "settle all 123" card, helper batches), threads waiting on a desk card or review, and four failed scheduled runs.

**Replay, same threads.** On the 151 of those threads that had not written since they were settled, the public script blocks 28 of the 34 open ones and passes 87 of the 117 closed ones; the other 30 closed ones need one proof line first. The live fleet's own copy, which also carries phrases for that fleet's lane names, blocks 32 of the 34.

### Forward test

One forward test was run on 12 Nov 2026. A fresh Claude Sonnet session that had never seen the skill was given only the skill folder (without its test file) and the standing decisions, census snapshot and earlier ledger line in [`examples/t3-code-conductor/sample-factory.md`](../examples/t3-code-conductor/sample-factory.md), with the "What a good first cycle does" table removed. It was told the snapshot was its census and to write messages to files instead of sending them. The exact Sonnet version was not recorded. Its run folder was read by hand against the removed table.

| Thread | Expected | What the session did | Match |
|---|---|---|---|
| A asks to merge to main, no review | Not to main. Outside review at the exact head; staging only after PASS. | Brief allows staging only, after a review PASS at the exact head, plus a recording. Review request written for a different model. | Yes |
| B asks which subject line | Answer from the ledger, no card. | Answered "What we shipped", citing the earlier ledger line. No card. | Yes |
| C says "Done", no files | Reopen with the real finish line. | Reopened: files committed and shown. | Yes |
| D the owner's own thread | Read, not steered. | Read only, no message. | Yes |
| E no lane | Give it a lane. | Adopted as a lane, no second thread. | Yes |
| F unreadable | A named gap. | Named gap in the roster and ledger. | Yes |

It set up the run folder with `desk.py init`, wrote the roster, added six ledger lines, and left the desk empty because nothing was yet a one-tap decision for the owner. `desk.py lint` printed PASS and `render` wrote the page. The `main` merge card in the example comes after the review lands, which the snapshot did not include, so `desk.py add` was not exercised by the session.

One fault came from the session, not the skill. It wrote a test line with `desk.py ledger`, then removed it with `sed`, which breaks append-only. The skill now says to write the ledger only through `desk.py ledger`.

## What changed after the test

The session listed 15 places where the text made it guess. These were made clearer:

- the ledger gets one line per decision, dispatch, proof and handover, plus one census line per pass
- earlier ledger lines go in by hand once, at setup
- a "completed" thread with no proof is reopened as a lane
- an existing thread with no lane is adopted, not duplicated
- an unreadable thread is a named gap that is retried next pass, and does not block the census
- an unknown conductor id is written as `unknown` until it can be read
- how a lane reports back, and a brief path for work that is not code
- a decision still waiting on review stays off the page
- the page headline now reads "1 decision needs you" for one card

The forward test ran on the text **before** these edits. The edited text has not been run again.

## Outside review and cold install

Before merge, on 12 Nov 2026:

- **Outside review.** A read-only reviewer on a different model (GPT-6.1 Sol), given the pull request, the exact commit and the leak rules but not the author's notes, checked commit `473a9f5`. Private data: PASS, after reading all 1,847 added lines. Would a stranger get it running from the README: FAIL, on one blocker. The T3 guide ran `desk.py` with no path, so the command could not be found. The guide now gives the installed path. The review rounds are recorded on [pull request #4](https://github.com/lennoxsaint/Skills/pull/4).
- **Cold install.** A fresh Claude Sonnet session cloned the repository from GitHub, picked both skills from the README and `AGENTS.md` for two plain requests, installed them into a temporary folder, and checked that all 15 relative links in the installed files resolve. It reported three wrong turns. `desk.py init --dir X` failed because `--dir` had to come first; it now works in either place. `setup.md` said `init` writes `review.html`; it does not, and the text now says so. The third came from the test itself: the temporary install folder had the same name as the clone on a case-insensitive disk, and the installer correctly refused to overwrite it.
- **Python 3.9.** The 12 desk tests also pass on Python 3.9.6. The settle gate tests were run on the author's Python only.

## Trigger cases

[`tests/t3-code-conductor/trigger-cases.json`](../tests/t3-code-conductor/trigger-cases.json) holds 24 prompts that should load the skill and 24 that should not, including Claude Code requests that belong to Claude Conductor and single tasks. It is a regression bank. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **1.4.0's snooze-last ladder is wording only.** It comes from one live fleet where 34 threads were snoozed at once (17 on a desk card, 8 on CI or a review) under the earlier wording. No run has measured whether the ladder lowers that count, and the shipped script does not enforce the cap of 5.
- **1.3.0's settle gate is measured on the data it was tuned on.** The phrase list was fitted to the same 165 threads the replay used, so its 28 of 34 is a ceiling, not a forecast. No forward run has measured it yet; the settle log it writes is there so the next audit can. The labels are model judgments checked by the author, not by a second person.
- **The gate matches phrases.** It missed 6 of 34 open threads, which said nothing it has a phrase for, and it stops about a quarter of finished ones until a proof line is recorded. `ALLOW` is not proof.
- **The gate reads T3's local database, which is not a public contract.** A T3 update can move a table; the check then reports the thread as not found and the hook lets the settle through. It sees only this machine's threads. The hook is wired for Claude Code; a Codex conductor follows the skill text.
- **1.1.0's settle-on-the-goal rule has not run in a forward test.** It is wording only; `desk.py` and its 12 tests did not change. Whether a conductor settles, progresses or carries a finished lane to the desk at the right moment was not measured.
- **1.2.1's full-access launch rule is measured from one live fleet, not a test.** Over 14 days, 208 of the 226 supervised threads on one machine came from launches on a linked machine, while same-machine launches inherited full access. No forward test has run the new wording.
- **1.2.0's clock-driven sweep has not run in a forward test either.** It replaces the 1.1.0 trigger ("sweep whenever no reply needs you"), which never fired in a live fleet: replies reached the conductor every 1.5 minutes (median over 27 hours), context compaction dropped the duty from its summary within a few hours, and sweeps ran only when the owner asked. Whether the new trigger keeps every ended thread handled within the hour was not measured.
- **The public skill has not run a live T3 fleet.** The forward test used a written snapshot. T3 thread tools, `delegate_task` reviews, the scheduled refresh and phone delivery were not exercised.
- **One run, one model.** Codex was not run as the conductor.
- **T3 tool names can change.** The skill tells the agent to find them with tool search and read each schema. Names it gives are examples.
- **No webhook or phone server ships.** Getting `review.html` to a phone is left to the owner, and the options in the setup guide were not tested here.
- **Handover was not exercised.** A single first cycle does not reach a context limit.
- **No comparison against no skill.** Whether this beats running T3 threads by hand was not measured.
