# Changelog

What changed in this repository, newest first. Each skill also keeps its own notes in `docs/<skill-name>.md`.

## 24 Nov 2026

**Changed**

- **Council 1.1.0: Gemini Neon seat.** The third lab's ladder is now the latest Gemini Neon, through a harness such as Antigravity or Cursor, then the latest Gemini Pro, then the latest Grok, then another lab's top model. Wording only: no code changed.

## 21 Nov 2026

**Added**

- **T3 Code Conductor 1.3.0: the settle gate.** `scripts/settle_check.py` reads a top-level thread's last message, last run and linked pull requests before it is settled, and prints `ALLOW` or `BLOCK` with the reason. Run as a hook on T3's organize tool, it refuses to settle a thread that still looks open until a proof line is recorded, and logs every top-level settle. An audit of one live fleet found 45 of 165 top-level threads settled over three days were still open (27%), most settled in bulk without their last message being read. Replayed on the 151 of those threads that had not changed, the public script blocks 28 of 34 open ones and asks for a proof line on 30 of 117 closed ones. That replay uses the threads the gate was tuned on, so real results will be lower. 17 new unit tests.

**Changed**

- **Claude Conductor 1.2.1: read before you resolve.** The same audit, as a rule: resolve a top-level thread one at a time after reading its last message, let helpers bulk-resolve children only, and never ask for a "resolve all". Wording only; not measured.
- **T3 Code Conductor 1.2.1 and Council 1.0.1: launch in full access.** Every thread, delegate and council seat starts with `runtimeMode: "full-access"` unless the owner asks for a supervised one. In a live fleet over 14 days, 208 of 226 supervised threads on one machine came from launches on a linked machine: a cross-machine launch does not inherit the caller's mode, so it lands supervised and waits on approval prompts no one is watching. Same-machine launches already inherited full access. Wording only: no code changed.

## 18 Nov 2026

**Changed**

- **T3 Code Conductor 1.2.0 and Claude Conductor 1.2.0: sweep on the clock.** The sweep of ended threads now runs at the start of any turn when the last `SWEEP` ledger line is more than 45 minutes old, before the conductor handles the message. In a live fleet the 1.1.0 trigger ("sweep whenever no reply needs you") never fired: replies reached the conductor every 1.5 minutes (median over 27 hours), context compaction dropped the duty from its summary within a few hours, and sweeps ran only when the owner asked. Each ended thread gets one of four moves: settle, progress, desk or snooze. Helpers and children are settled in the turn their result is read, and an idle thread is woken only with work. A host hook that checks the age of the last sweep is recommended so the rule survives compaction. Wording only: `desk.py` and its 12 tests are unchanged. See the [T3 guide](docs/t3-code-conductor.md) and the [Claude guide](docs/claude-conductor.md).

## 17 Nov 2026

**Changed**

- **T3 Code Conductor 1.1.0 and Claude Conductor 1.1.0: settle on the goal, not the run.** A thread whose run ended is judged against the goal it was first given. A finished one is settled, one with work left gets its next step at once, and one that needs the owner goes to the review page with the goal, a dated summary of what was achieved with proof, and what is left. In T3 Code Conductor that is an outcomes card: an ordinary desk card whose `why` holds the goal, the outcomes and what is left, whose links hold the proof, and whose `yes` is the next step. An unfinished thread the owner started gets one too, and nothing is sent into it. Wording only: no code changed, and `desk.py` and its 12 tests are as they were. See the [T3 guide](docs/t3-code-conductor.md) and the [Claude guide](docs/claude-conductor.md).

## 16 Nov 2026

**Added**

- **Council 1.0.0.** New skill. Reviewers from three AI labs score the exact same version, the agent fixes what they prove, and the loop repeats until every reviewer would ship it, the loop stalls, or it is blocked. It keeps a fingerprint of each version, a scope guard on growth, and a round budget, and it stops one step before anything goes out. Its text went through five rounds of its own council before release. See the [guide](docs/council.md) and the [evaluation](evaluations/council.md).
- **Ship-ready 1.0.0.** New skill. It takes a task to ready-to-go: does the work, proves it, passes Council, stages the send, publish or merge, and hands back one message. It has not yet run end to end on a real task. See the [guide](docs/ship-ready.md) and the [evaluation](evaluations/ship-ready.md).

**Changed**

- **Skill count to 13** in the README, `AGENTS.md` and `llms.txt`. The guides for Loop and Adversarial Review now point to Council. Neither skill's own text changed, so their versions stay at 1.0.0.

## 15 Nov 2026

**Changed**

- **Front page rebuilt for two readers.** The README now opens with a diagram of what a skill changes, a plain "What this is", and "Start here": the four skills to try first, each with what it does, its proof and what it needs. The original "Try saying" prompts are kept. The full table shows every skill's proof level and headline result with a link to its evidence. No skill's behaviour or version changed.
- **Proof in the catalog.** Every entry in `catalog.json` now has `best_for` and a `proof` block (`level`, `headline`, `caption`, `summary`, `limit`) quoted from its evaluation file, plus top-level `start_here`, `proof_levels` and `cold_run`. `llms.txt` and `EVALUATION.md` carry the same proof, and a test keeps `llms.txt` in step with the catalog.
- **Diagrams drawn from the data.** `scripts/build_readme_art.py` draws the README diagrams in light and dark from `catalog.json`. CI fails if they are out of date.
- **Answer path for visiting agents.** `AGENTS.md` and the README's "For agents" section say how to answer "what's good here?" from the repository, with the proof quoted at its real level.
- **Hill Climb needs, corrected.** Its default judges use both Claude Code and Codex. `catalog.json` said either one was enough.
- **Stars and results, asked for plainly.** A live star badge sits at the top of the README, and two short asks invite a star from people a skill helped. Visiting agents offer the star once and star only after their user says yes (`catalog.json` `star`). A new issue form, "Share a result", collects real results; the README shows no user quotes until there are real ones.
- **Eddy Studio in "Who made this".** One short block on Lennox's Mac video app, beside the Threadify link.
- **Guides in sentence case.** The guides in `docs/` now use normal sentence case, and a few phrases that read as filler were rewritten. Facts, numbers and commands are unchanged.

## 12 Nov 2026

**Added**

- **Claude Conductor 1.0.0.** New skill. It runs the Claude Code threads you already have as you: one run contract, a count of every open thread, a ranked ledger, whole outcomes for each owner, proof before "done", and one private review page. See the [guide](docs/claude-conductor.md) and the [evaluation](evaluations/claude-conductor.md).
- **T3 Code Conductor 1.0.0.** New skill. One T3 Code thread conducts all the others: census, roster, append-only ledger, outside review on a different model at the exact commit, answers from standing decisions, and one phone review page of only the decisions that need you. It ships `desk.py`, a tested helper that keeps the cards and renders the page. See the [guide](docs/t3-code-conductor.md) and the [evaluation](evaluations/t3-code-conductor.md).

## 10 Nov 2026

**Added**

- **Hill Climb 1.0.0.** New skill. It turns real data into a locked answer key, then climbs to a measured target with fresh agent sessions until the score and two outside judges say it is done. See the [guide](docs/hill-climb.md) and the [evaluation](evaluations/hill-climb.md).
- **Loop 1.0.0.** New skill. It writes a 100-point rubric for one draft, revises and rescores it, and stops at 100/100 or says which points are missing. See the [guide](docs/loop.md) and the [evaluation](evaluations/loop.md).
- **Adversarial Review 1.0.0.** New skill. An independent reviewer critiques a frozen draft against a fixed rubric, each finding is checked, and the loop stops at the bar or the budget. See the [guide](docs/adversarial-review.md) and the [evaluation](evaluations/adversarial-review.md).
- **Strategy Prompt 1.0.0.** New skill. It steelmans every option, scores them in a weighted matrix, checks its own pick, then gives a final recommendation. See the [guide](docs/strategy-prompt.md) and the [evaluation](evaluations/strategy-prompt.md).
- **Finish Work 1.0.0.** New skill. Before an agent says "done" it runs the right checks for the kind of work, keeps "local" apart from "live", and writes a receipt to a file you choose. A different model reviewed the receipt helper before release. The faults it found, and what was done about each, are in the evaluation. See the [guide](docs/finish-work.md) and the [evaluation](evaluations/finish-work.md).
- **Install for Claude Code, Codex or both.** `scripts/skills.py install <name> --host claude|codex|both`. It also takes several skill names at once, and prints what each skill needs and a prompt to try.
- **`--update`.** Replaces a skill you already installed. Your old copy is moved to a `skills-backup` folder first.
- **Installer safety.** An empty `--target-root` is refused. When both hosts share one skills folder, `--host both` installs there once.
- **Agent entry points.** [`AGENTS.md`](AGENTS.md) has install steps with a check for each one. [`llms.txt`](llms.txt) is a short index. `CLAUDE.md` points Claude Code at the agent guide.
- **`llms.txt` is enough on its own.** Each skill line now carries its try prompt and what it needs, and a test keeps it in step with `catalog.json`.
- **Catalog fields.** Every skill in `catalog.json` now has `use_when`, `try` and `hosts`. The catalog also lists the install command for each host.

**Changed**

- **Ambitious 1.3.1.** The leaner body the author runs every day: five moves per run, and the extras (more crew fields, the working sketch, the review page, the taste log) only when they fix a named audience problem. In a blind head-to-head on 27 Oct 2026 this body was about even with the 1.2.3 body and about 12% faster, and it missed the adoption rule set before that test by 0.03 on one task. It is published anyway as the owner's choice. The [evaluation](evaluations/ambitious.md) has the numbers, and the [`ambitious-v1.2.4` release](https://github.com/lennoxsaint/Skills/releases/tag/ambitious-v1.2.4) keeps the earlier body.
- **Hill Climb 1.0.1.** One line changed after the first release earlier the same day: the description now sends quick polish of one draft to Loop. The method and the scripts are the same.
- **Goal 1.1.0.** Goal now tells apart "create a goal" from "continue the goal that is already running", so a resumed run carries on with the next step and does not rebuild the packet. It also points measurable quality bars at Hill Climb.
- **README.** New front page for Claude Code and Codex users, with one install command per host. The repository is no longer framed around one community.
- **`skills.py list`** now shows when to use each skill.
- **Validation.** A `SKILL.md` may name the word `TODO` inside code formatting. Catalog entries must carry the new fields.

**Unchanged**

- Email Triage Pro 1.0.0 and Save 10% 2.0.1 have the same skill text as before.

## 29 Oct 2026

- **Ambitious 1.2.4.** Label only. The version number now follows the private history.

## 28 Oct 2026

- **Ambitious 1.0.0.** First public release.

## 20 Sep 2026

- **Goal 1.0.0.** First public release, with runtime tests.

## 19 Sep 2026

- **Email Triage Pro 1.0.0.** First public release.

## 17 Aug 2026

- **Save 10% 2.0.0.** New workflow. The repository became a catalog that can hold many skills.

## 2 Aug 2026

- **Save 10% 1.0.0.** First skill in the repository.
