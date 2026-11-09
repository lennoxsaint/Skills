# Hill Climb evaluation

Version: 1.0.0

## What was tested

This release is the private skill as of 4 Nov 2026 (the version with the blind judge stage), with private paths and product-specific notes replaced by general ones. One test fixture was renamed to a neutral server name, and one private folder name was dropped from the sandbox's list of writable agent-state folders.

Three small script fixes came out of the review of this public copy (see Review). None of them changes how a climb keeps, undoes, scores or stops.

The evidence here is about the **runner**: does it keep, undo, stop, resume and refuse the way the skill says it does. It is not a benchmark of how much a climb improves real work. That depends on the answer key you build.

## Self test

`node hill-climb/scripts/selftest.mjs` runs the whole loop with scripted fake climbers and fake judges. It makes no model calls and costs nothing.

| Run | Machine | Node | Result | Time |
|---|---|---|---|---|
| Private copy, 10 Nov 2026 | macOS (Apple silicon), with other work running | 24.22.1 | 261 of 261 checks passed | 10 min 21 s |
| Public copy before the review fixes, 10 Nov 2026 | same | 24.22.1 | 261 of 261 checks passed | 9 min 38 s |
| Public copy as shipped, run from a folder with a space in its path, 10 Nov 2026 | same | 24.22.1 | 261 of 261 checks passed | 11 min 24 s |

What the checks prove, by area:

| Area | What is proven |
|---|---|
| Keep or undo | A change that raises the score is kept as a commit. A change that does not is saved as a rejected ref and the folder is put back. A no-op and an out-of-scope edit are rejected. |
| Cheating | A diff that pastes a visible or hidden test input is rejected. An edit to the answer key stops the run as `tampered`. |
| Sandbox walls | A producer cannot read the hidden cases, the state or the runs, and cannot write the work folder. A climber cannot list, read or write the hill folder. Children get an allowlisted environment, so a secret in the parent environment does not reach them. A process that escapes its group is found, stopped and the attempt rejected. |
| Git safety | A climber cannot commit, move a ref, plant a hook or change git config with the sandbox on. With it off, those edits are caught, put back and the attempt is rejected. Symlinks, ignored files and leaving the branch are handled. |
| Kill and resume | The runner is stopped at each step of recording an outcome (after the decision is written, after the branch moves, after the restore, after the ledger line). The next start finishes that outcome exactly once and carries on. A `kill -9` mid-attempt loses no kept work, and the interrupted edits are saved. |
| Judge stage | The judges are blind: no target, baseline, test score or bar reaches their prompt. A verdict that misses a rubric category is refused. A higher total that loses a ship vote is rejected. A judge whose score rose is asked again before the rise counts. |
| Stop rules | Deadline, budget, stuck after a plateau, saturated and busy (a second runner on the same hill) each stop with their own status. The climb refuses to start before the owner approves, and blocks when an attempt leaves the branch. `--no-council` ends as `stage1_only`, never `done`. |
| Integrity | The ledger is hash-chained and `verify` finds an edited line. A broken ledger stops the runner. A second `freeze` archives the old run and needs a new approval. |
| Tools | The transcript miner finds every supported record shape in Claude Code and Codex sessions. `try`, `judge-test`, `council-test`, `raise` and the custom scorer contract behave as documented. |

## CI

- The **validate** workflow (Ubuntu) runs two fast checks on every push: every script parses, and `hill.mjs init --scratch` creates a hill in a temp folder.
- The **Hill Climb self test** workflow (macOS) runs the full self test when the skill changes.

## Trigger cases

[`tests/hill-climb/trigger-cases.json`](../tests/hill-climb/trigger-cases.json) holds 24 prompts that should load the skill and 24 near-misses that should not (quick polish, a plain "run the tests", a goal prompt, an ambitious ask). It is a regression bank for future description changes. It has not been run as a measured trigger benchmark, so no trigger rate is claimed.

## Review

Before the 4 Nov 2026 version was committed privately, a different model (GPT-6.1 Sol) reviewed the scripts read-only. It raised 12 findings. 10 were fixed before the commit and 2 were kept by design. That review is of the private copy.

The public copy had its own read-only review by GPT-6.1 Sol on 10 Nov 2026. Three of its findings were about this skill's scripts and all three were fixed:

- `selftest.mjs` and the command `hill.mjs approve` prints now resolve their own folder correctly when the path has a space in it.
- The transcript miner now prints `INCOMPLETE` with a file count when compressed sessions exist and `zstdcat` is missing. Before, it skipped them without a word.
- The guide now shows the self test command for both hosts.

One finding was kept by design: with `council` set to `[]` in `hill.json`, a climb that meets the test target ends as `done` with the reason `no council configured`. The owner chooses that setting before the freeze, and the guide now says so plainly.

## Limits

- **No real-work benchmark is published.** The self test proves the mechanics with fake agents. It does not show that a climb makes your product better, and no public numbers from private hills are claimed here.
- **The Linux `bwrap` path is untested.** The sandbox is tested on macOS `sandbox-exec` only.
- **Tested on Node 24.** The scripts use nothing newer than Node 18 features as far as we know, but older versions were not run.
- **The hidden tests sit on the same disk as the climber.** The sandbox, the leak check, the hash lock and the hidden-score gap guard them. For higher stakes, score on another user account or machine.
- **A score is only as good as its answer key.** If the climb hits the target and you still dislike the result, the fix is new cases from that dislike and a new freeze.
- **Judges are models.** Blind judges from two labs can still share a blind spot or differ from your taste. The board shows their critiques, not just the scores.
- **Timing-sensitive checks can be flaky on a loaded machine.** Escape detection runs after every sandboxed child.
- **Cost is yours to cap.** A climb is many agent sessions. Only Claude reports its dollar cost; Codex runs count as unknown cost.
