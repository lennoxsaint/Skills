# Scope, authority and integrity

## What the climber may touch
- Only files matching `climbable` in the work folder, on the `hill/<name>` branch. Any other changed file rejects the attempt.
- Climbers run as fresh sessions without the owner's MCP servers, skills or hooks (`claude -p --safe-mode`, `codex exec --ignore-user-config`), so they cannot reach publishing, email, payment or production tools. Keep it that way: give a climber shell access only through narrow `allowed_tools` patterns (tests, the scorer), and keep producers offline.
- The runner never publishes, sends, deploys, pushes or merges. Landing the result (step 9) is the lead agent's job, under the owner's normal rules for that repo.

## Sandbox
With `"sandbox": "auto"` (the default) every producer, check, custom scorer, judge and climber (Claude or Codex) runs inside the machine's sandbox: `sandbox-exec` on macOS, `bwrap` on Linux. The runner refuses to start when neither exists.

Writes are denied everywhere by default. Each process may write only its own private temp folder, the folders in the table, the `sandbox_write` folders from `hill.json`, terminal devices, and the run-state files the `claude` and `codex` CLIs keep, under both `CLAUDE_CONFIG_DIR` and `~/.claude` (never their settings, hooks, skills, plugins, MCP config or auto-memory).

| process | sees | may write |
| --- | --- | --- |
| producer, `command` check, secondary command | everything except the hill folder, plus `scorer/` and `hill.json` | `cache/produce/` only; the work folder is read-only (`produce.workdir_writable: true` lifts that) |
| custom scorer | the same, plus one fresh inputs folder holding only `{"cases":[{"id","input"}]}` | its output folder and `cache/produce/` |
| judge | everything except the hill folder | nothing beyond `sandbox_write` |
| climber | everything except the hill folder | the work folder and its own `runs/<n>/agent/` |

So the hidden cases, the runs, the state and the ledger are out of reach of everything the runner starts. Two allowances: processes may **stat** the folders above an allowed path inside the hill folder (Node needs this to load a script; it reveals existence and modified time, not contents or listings), and the scorer's own files are readable by design.

Inside the work folder, git's admin folders (`.git`, the worktree's git dir and the shared common dir) and every `scope_ignore` path are read-only to all children, so no child can commit, move a ref, plant a hook or change output the diff never shows. Owner secrets (`~/.ssh`, `~/.aws`, `~/.config/gh`, `~/.netrc`, `~/.docker`, `~/.kube`, gcloud, 1Password, git credentials, `~/.npmrc`, `~/.env`) are unreadable; `sandbox_allow_read` re-opens one a scorer genuinely needs.

Children get an allowlisted environment (PATH, HOME, locale, proxy and CA settings, CLI config folders). Anything else a producer, check or agent needs, such as `CLAUDE_CODE_OAUTH_TOKEN`, must be named in that spec's `pass_env`. Name variables, never paste values.

Codex agents run inside the same sandbox with Codex's own sandbox switched off (`-s danger-full-access`), because macOS sandboxes cannot nest. The hill sandbox is their boundary: it hides the hill folder and Codex's global `AGENTS.md`, skills, plugins and memories, and denies writes outside the work folder; Codex's rules, project docs and hooks are switched off by flag. `"sandbox": "off"` runs everything unprotected (Codex falls back to its own `workspace-write` or `read-only` sandbox, which does not hide the hill folder); `validate` warns and it needs a re-freeze.

**Escaped processes.** Every child runs in its own process group, and the group is stopped when the child exits. A process that leaves the group (setsid, double fork) and outlives the child is found by its run token, by working in the run's private temp folder, or as an orphan in the work folder. It is stopped, the run fails (exit 125 when it had exited 0), and a climber attempt that left one is rejected as `escaped_process`.

## Git safety
The runner never resets, checks out or force-moves anything. It works through a private index, writes commits with `commit-tree`, and moves only `refs/heads/hill/<name>`, with compare-and-swap.
- **Byte-exact trees**: the runner hashes and restores file bytes itself, so no git filter, textconv or line-ending conversion ever runs. A work folder that git would transform is refused at the start (and by `brief`): clean/smudge filters, Git LFS, `ident`, `working-tree-encoding`, `core.autocrlf`/`core.eol` CRLF, or sparse checkout. So is a folder whose staged content matches neither `HEAD` nor the file on disk (pointing the index at a tree would lose it): commit or unstage it first. An attempt that changes `.gitattributes` or `.gitmodules` is rejected as `out_of_scope`.
- **Kept** attempts are commits on `hill/<name>`.
- **Rejected** attempts are saved as `refs/hill/<name>/rejected/<n>`. `git checkout refs/hill/<name>/rejected/<n> -- .` brings one back. With the sandbox on, a climber cannot commit (git's admin folders are read-only); with `"sandbox": "off"`, a commit the climber made itself is saved as `rejected/<n>-agent-commit` and its content judged like any other change.
- **Interrupted** attempts (runner killed) are saved as `rejected/interrupted-<n>` (edits) and `rejected/interrupted-<n>-commit` (a stray commit) on the next start.
- **Off-branch**: if an attempt leaves the work folder on another branch, the runner saves `refs/hill/<name>/evidence/<n>-off-branch`, touches nothing and stops for the owner.
- **Git's own files**: `.git/config`, `info/`, `hooks/` and the global git config are snapshotted before each attempt and put back after it; an attempt that edited them is rejected as `tampered_git`. If the runner died before putting them back, the next start stops until the owner inspects them and reruns with `--accept-git-config`.
- **Files git ignores**: new ignored files an attempt writes are moved to `quarantine/<n>/` in the hill folder and the attempt is rejected. Changing or deleting an ignored file that existed before stops the run (it cannot be put back). Folders listed in `scope_ignore` (node_modules, build caches) are exempt.
- **Symlinks and submodules** in a change reject the attempt.
- **Foreign changes**: a moved hill branch or uncommitted edits the runner did not make stop the start with instructions; nothing is reset.
- **Kill and resume**: every outcome is written to `runs/<n>/decision.json` (with an id unique to the attempt) before any git side effect, and the history entry and ledger line carry the same id. The next start stops the leftover climber's process group and finishes a decided outcome from `decision.json`: it completes a keep that was committed but not recorded, recreates a missing rejected ref, and records each outcome exactly once (`recovered_completion` in the ledger), whichever step the kill landed on. Edits with no decision are saved as interrupted refs. Then it continues. `climb.mjs <hill> --recover-only` does the recovery and stops.

## Integrity of the key
- `freeze` hashes `hill.json`, every case, exemplar and scorer file into `lock.json` and makes the hidden cases read-only. The runner rechecks the hashes after every attempt and stops as **tampered** if anything changed.
- A second `freeze` (a **re-freeze**) archives the old run under `generations` in `state.json`, clears the baseline and the approval, and needs a new `brief` and `approve`.
- `ledger.jsonl` is hash-chained: each entry carries the hash of the one before. `hill.mjs verify` reports the first broken line, and the runner refuses to start on a broken chain.
- Diffs that paste a test's input text are rejected as `memorised_test` (visible case) or `leaked_hidden_test` (hidden case).
- A run lock (`run.lock`) stops two runners on one hill; a lock left by a dead process on the same machine is reclaimed.

## Known limits
- The hidden cases sit on the same disk. The sandbox, the leak check, the hash lock and the hidden-score gap guard them; for higher stakes, move the hill folder to another user or machine and score there.
- Scoring and the council stop at the deadline: every command is capped at the time left, and a split or review cut short raises a deadline stop, never a partial score. An attempt cut off this way is recorded as `deadline` (its edits saved as a rejected ref, not counted toward stuck). `stop.min_attempt_sec` (default 300) still stops the runner starting an attempt it cannot finish.
- The Linux `bwrap` path is untested.
- Escape detection runs after every sandboxed child and adds a fraction of a second each; timing-sensitive tests can be flaky on a loaded machine.

## Data the judges see
Each judge gets a private copy of the candidate: every climbable file in `candidate/`, plus `review/diff.patch` (against the baseline commit) and `review/test-results.json`. Agent instruction files in the copy (`CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.mcp.json`, `.cursorrules` and folders like `.claude/` or `.codex/`) are renamed to `.data`, so a judge reads them as content and never loads them as instructions. When the whole review fits in 150,000 characters it is also quoted in the prompt. Otherwise the judge must read every file and answer `"read_all": true`, or its verdict is invalid. When the climbable files pass 4 MB no judge runs and the review fails closed.

The judges are outside models, so the candidate, the diff and the test results leave the machine for each judge's provider. Before the climb, get the owner's ruling on which private material each judge model may read, and keep anything it excludes out of the climbable files, the cases and the exemplars. Secrets, keys and credentials never go into any prompt, case or exemplar: mask them when mining, and check the hill folder for them before `freeze`.

## Product repos
When the work folder is a product repo, its own rules still govern landing. Read that repo's release rules (its `AGENTS.md`, `CLAUDE.md` or contributing guide) before the climb: the hill branch ends as a PR with before/after evidence, any staging merge follows those rules, and production stays off limits.
