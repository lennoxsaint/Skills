# T3 Code Conductor evaluation

Version: 1.0.0

## What was tested

The author ran this method by hand in T3 Code before it was a skill. This is the first time it is written as one, with the machines, accounts, thread ids and private rules taken out. The review page helper, `scripts/desk.py`, is new.

### The review page helper

`scripts/test_desk.py` has 11 unit tests. All 11 pass locally, and CI runs them on every push. They cover:

- `init` writes each file once and never overwrites one that exists
- the ledger only appends, and one call cannot forge a second line
- add, answer, routed and close in order; a card cannot be routed before it is answered
- duplicate and malformed card ids are refused
- text over its length limit is refused
- `lint` refuses local paths and `http://` links, and `render` refuses to run while `lint` fails
- the page escapes every value and loads no scripts or remote files
- cards rank by due date, then priority, then age
- six writers at once lose no card
- the run folder can come from `CONDUCTOR_HOME`

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

## Trigger cases

[`tests/t3-code-conductor/trigger-cases.json`](../tests/t3-code-conductor/trigger-cases.json) holds 24 prompts that should load the skill and 24 that should not, including Claude Code requests that belong to Claude Conductor and single tasks. It is a regression bank. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Limits

- **The public skill has not run a live T3 fleet.** The forward test used a written snapshot. T3 thread tools, `delegate_task` reviews, the scheduled refresh and phone delivery were not exercised.
- **One run, one model.** Codex was not run as the conductor.
- **T3 tool names can change.** The skill tells the agent to find them with tool search and read each schema. Names it gives are examples.
- **No webhook or phone server ships.** Getting `review.html` to a phone is left to the owner, and the options in the setup guide were not tested here.
- **Handover was not exercised.** A single first cycle does not reach a context limit.
- **No comparison against no skill.** Whether this beats running T3 threads by hand was not measured.
