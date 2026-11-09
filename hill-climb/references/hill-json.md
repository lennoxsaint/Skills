# hill.json and the hill folder

`hill.mjs init` writes a template. Every key below is read by the scripts; anything not listed is ignored. Paths in `hill.json` are absolute unless noted. `validate`, `freeze`, `score`, `try` and the runner refuse out-of-range numbers, unknown enum values and malformed producer, scorer, judge, secondary and check settings.

## The hill folder

```
<hill>/
  hill.json            the spec (frozen)
  notes.md             learnings shown to every attempt (editable any time, not frozen)
  exemplars/<id>.json  labelled real outputs (frozen)
  references/<id>/     optional: the best products or versions the council compares the work with (frozen; manifest.json + files)
  cases/pool/          cases before the split
  cases/optimise/      visible tests (frozen)
  cases/holdout/       hidden tests, read-only after freeze (frozen)
  scorer/              produce.mjs and any helpers (frozen)
  build/               your scratch: mining output, builder scripts, trial scores (not frozen, hidden from the climber)
  cache/               judge answers, the producer's writable cache and council renders (cache/renders/<tree>-<hash>/)
  lock.json            hashes of every frozen file
  state.json           the runner's state: best, history, council, stage, earlier generations
  ledger.jsonl         hash-chained log of every freeze, baseline, attempt, council and stop
  runs/<n>/            each attempt: climber prompt, log, last message, scores, decision.json
  quarantine/<n>/      ignored files an attempt wrote, moved out of the work folder
  checkpoint.html      the owner's one-page answer key (from `brief`)
  board.html           the live scoreboard
  report.md            written when the runner stops
```

## Keys

| key | meaning |
| --- | --- |
| `name` | slug; the branch is `hill/<name>` |
| `goal` | one plain sentence; every prompt and the council see it |
| `workdir` | the climber's folder: a git worktree on `branch`, never inside the hill folder |
| `branch` | must start with `hill/` |
| `base_ref` | the commit the climb started from; the council reviews the diff against it |
| `climbable` | globs (relative to `workdir`) the climber may change; any other changed file rejects the attempt |
| `scope_ignore` | globs of ignored build and cache output the climber may regenerate (default: node_modules, .next, .turbo, coverage, caches); read-only to every sandboxed child |
| `sandbox_write` | extra folders every sandboxed child may write (relative to `workdir`, `~` allowed), for a tool cache that cannot change the score. Children otherwise write only their own temp folder, their cache and, for the climber, the work folder. Never `/` or the home folder |
| `sandbox_allow_read` | owner secret paths a child genuinely needs to read (e.g. `~/.npmrc` for npx); never `/` or the home folder |
| `produce.command` | shell command run in `workdir` once per case; stdin `{"id","input"}`, stdout = the output under test. Env: `HILL_WORKDIR`, `HILL_SCORER_DIR`, `HILL_CACHE_DIR`, and `HILL_MODEL` when `produce.model` is set. Offline and side-effect free |
| `produce.model` | the model the producer should run, passed as `HILL_MODEL` |
| `produce.pass_env` | environment variable names the producer needs beyond the allowlist (e.g. `CLAUDE_CODE_OAUTH_TOKEN`) |
| `produce.timeout_sec`, `produce.concurrency` | per case (default 300 s); parallel cases (default: top-level `concurrency`, 4) |
| `produce.workdir_writable` | `true` lets the producer write the work folder (default read-only) |
| `scorer.command` | optional batch replacement for `produce.command` (one process for many cases, e.g. a benchmark harness). It reads `{"cases":[{"id","input"}]}` from the file in `HILL_INPUTS` (a fresh folder holding nothing else: no checks, flags, split name or case files) and writes `{"outputs":[{"id","output"}]}` to `HILL_OUT`, every case exactly once with a string `id` (`{"id","error"}` fails that one case). The runner grades each output with the case's own checks, `repeats` and `pass_rule`, exactly like a producer's. A crash or timeout fails every case of the batch; a malformed, missing, extra or duplicate entry is a scoring error. Env as `produce.command` plus `HILL_MODEL` from `scorer.model`; `scorer.timeout_sec` (default 3600), `scorer.pass_env` |
| `judge` | default spec for `judge` checks: `{cli, model}`; default Claude Haiku |
| `metric.name`, `metric.unit`, `metric.target` | the score is % of visible cases passing; `target` is the stage 1 bar |
| `metric.holdout_gap_max` | max points the hidden score may trail the visible one (default 5) |
| `metric.secondary` | optional second number to climb once the score holds: `{name, command, direction: "down"\|"up", target, margin, timeout_sec, pass_env}`; `command` and `direction` are required. `command` runs in the produce sandbox and prints the number last on stdout (e.g. prompt tokens). It counts only when the command exits 0 in time and the last word is a finite number; anything else is a scoring error, never a value. Stage 1 needs its `target` met too |
| `climber` | agent spec (below); default Claude Opus, effort high, 1800 s |
| `council` | list of agent specs, from two labs; default GPT-6.1 Sol + Claude Opus. `[]` skips stage 2. The list order is the cascade: put the cheapest judge first. At the first council of a generation every judge is asked; after that a judge is asked only when every judge before it passes, so done always rests on a full-panel pass of one commit. A third lab is optional, e.g. `{"cli": "cmd", "name": "gemini", "command": "gemini-judge.sh"}` wrapping your Gemini CLI |
| `council_bar` | every judge must score every category at least this and say it would ship (default 9; whole or half points, e.g. 9.5) |
| `council_rubric` | optional list of 3-6 `{name, ask}` categories the judges score separately, in half points (1-10). A judge's score is its lowest category. Draft them from the owner's real critiques; for UI: typography, hierarchy, colour and contrast, consistency, iconography. Without it each judge gives one `overall` score |
| `council_render` | optional `{command, timeout_sec, pass_env}`: renders the work for the judges. Runs in `workdir` in the producer's sandbox with `HILL_RENDER_OUT` (a fresh folder), `HILL_WORKDIR`, `HILL_SCORER_DIR` and `HILL_CACHE_DIR`; it writes up to 8 files (png, jpeg, webp, or short text) plus `manifest.json` (`[{"file", "label"}]`) into `HILL_RENDER_OUT` (default timeout 600 s). Renders are cached by tree. The starting render (made by `brief`) goes to every round as a hidden control. Needed for `references/` |
| `council_tolerance` | points the visible score may dip below the best during stage 2 (default 0) |
| `review_focus` | one line on what the owner cares about most; given to the council |
| `stop.deadline` | ISO time; `--deadline` overrides. Scoring, the hidden check and the council are cut off at it (never a partial score) |
| `stop.plateau` | attempts without gain before **stuck** (default 10) |
| `stop.switch_every` | attempts without gain before the prompt orders a different approach (default 4) |
| `stop.min_switches` | switches required before **stuck** may fire (default 2) |
| `stop.max_attempts` | hard cap; `--max-attempts` overrides |
| `stop.budget_usd` | optional dollar cap on the climber, judges and judge checks together; stops as **budget**. Only Claude reports its cost: Codex and command agents are counted as runs of unknown cost, never as $0 |
| `stop.min_attempt_sec` | do not start an attempt with less time than this before the deadline (default 300) |
| `repeats`, `pass_rule` | run each case N times; `all` or `majority` must pass. `majority` needs an odd `repeats` of 3 or more (use 3 + `majority` for flaky producers) |
| `accept_margin` | points a change must gain to be kept (default 0) |
| `confirm_gains` | rescore a gain once before keeping it (for noisy scores) |
| `holdout_every` | measure the hidden tests every N keeps (default 3), and always before stage 1 can pass |
| `checkpoint` | `false` skips the owner approval (only for dry runs) |
| `sandbox` | `auto` (default) or `off`; see [safety.md](safety.md) |
| `calibration_min` | minimum exemplar TPR and TNR for `validate --run` and `freeze` (default 0.8) |
| `min_cases` | `{optimise: 20, holdout: 8}` minimums |
| `leak_min_chars` | test-input length that counts as pasted when it appears in a diff (default 40) |
| `show_failing` | failing tests shown per attempt (default 14) |
| `frozen_extra` | more files (relative to the hill folder) to hash into the lock |
| `commit_trailer` | text appended to every kept commit's message |
| `authority` | plain-language scope shown to every climber |

## Agent specs

`{cli, model, effort, timeout_sec, name, pass_env}` plus:
- `cli: "claude"` runs `claude -p --safe-mode` (no CLAUDE.md, skills, hooks or MCP servers). Climbers get Read, Edit, Write, Glob, Grep and Bash with `acceptEdits`; in print mode a Bash command runs only when it matches `allowed_tools`, e.g. `["Bash(npm test:*)"]`. Judges get Read, Glob and Grep only. `tools` overrides the tool list.
- `cli: "codex"` runs `codex exec --ignore-user-config --ignore-rules --ephemeral` with project docs, hooks and the other optional features off. It runs inside the hill sandbox with Codex's own sandbox off, since macOS sandboxes cannot nest; with `"sandbox": "off"` Codex's `workspace-write` (climbers) or `read-only` (judges) sandbox applies instead, and that one does not hide the hill folder.
- `cli: "cmd"` runs `command` in a shell with the prompt on stdin (and in `HILL_PROMPT_FILE`); for tests and custom agents.
- `sandbox: "off"` on one agent spec runs only that agent outside the hill sandbox, with the same exposure as the top-level switch; leave it unset.

Agents get the allowlisted environment plus their `pass_env`, so a nested `claude -p` starts clean on the machine's normal login. Climbers also get `HILL_ATTEMPT` and `HILL_WORKDIR`.

## Case and exemplar files

```json
{ "id": "c014", "input": "...", "origin": "real", "source": "~/.claude/projects/x/abc.jsonl#L120",
  "must_pass": false, "negative": false, "note": "why this case exists",
  "checks": [ { "name": "first tool", "type": "equals", "path": "tools[0]", "value": "get_connection_defaults" } ] }
```

An exemplar adds `"output": "<the real output>"` and `"label": "pass" | "fail"`. Check types are in [answer-key.md](answer-key.md).

## References (render hills)

`references/<id>/` holds one other product or version, in the same shape as a render: `manifest.json` (`[{"file": "home.png", "label": "home screen"}]`) and the files it names (at most 8; images of at most 5 MB, text of at most 100 KB). At most 6 references, and every reference plus the work and the control must fit in the 24 images a judge call takes. Each round every judge is asked twice. The **look call** sees only the versions to score: the work, every reference and the starting render under shuffled letters with neutral file names (`items/B/1.png`), no code, no diff and no manifest labels, so it can never tell which is which; it scores every one per category. The **review call** reads the code, the diff, the test outputs and the work's own screens (`render/1.png`) and gives the ship vote, the top fault and the critique. A render hill therefore costs two calls per judge per round. The work counts only by its **lead** over the best reference in the same look reply, so a judge's scale moving cancels out; a stage-2 change is kept only when neither the lowest lead nor the total lead slips and no ship vote is lost, and the total lead or the ship count rises. A judge whose score or lead rose is asked again before it counts. If the starting render has gone from the cache, rounds run without the control and say so (`control_missing`); run `brief` again to make it. Done needs every judge ahead of every reference. A judge whose score for an unchanged version moves more than 1 point is flagged as drift on the board and in the ledger.

A tested render command for a static page with headless Chrome on macOS (it never takes focus). Inside the hill sandbox Chrome needs its own sandbox off, since macOS sandboxes cannot nest and the hill sandbox still contains it, and its temp folder pointed at the run's `TMPDIR`:

```sh
export MAC_CHROMIUM_TMPDIR="$TMPDIR"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --no-sandbox --disable-gpu \
  --disable-crash-reporter --no-first-run --hide-scrollbars --user-data-dir="$(mktemp -d "$TMPDIR/chrome-XXXXXX")" \
  --window-size=1200,820 --screenshot="$HILL_RENDER_OUT/page.png" "file://$HILL_WORKDIR/index.html" >/dev/null 2>&1
test -s "$HILL_RENDER_OUT/page.png"
printf '[{"file":"page.png","label":"home page, desktop 1200x820"}]' > "$HILL_RENDER_OUT/manifest.json"
```

Make the reference screenshots at the same window size.
