# Changelog

What changed in this repository, newest first. Each skill also keeps its own notes in `docs/<skill-name>.md`.

## 10 Nov 2026

**Added**

- **Hill Climb 1.0.0.** New skill. It turns real data into a locked answer key, then climbs to a measured target with fresh agent sessions until the score and two outside judges say it is done. See the [guide](docs/hill-climb.md) and the [evaluation](evaluations/hill-climb.md).
- **Loop 1.0.0.** New skill. It writes a 100-point rubric for one draft, revises and rescores it, and stops at 100/100 or says which points are missing. See the [guide](docs/loop.md) and the [evaluation](evaluations/loop.md).
- **Adversarial Review 1.0.0.** New skill. An independent reviewer critiques a frozen draft against a fixed rubric, each finding is checked, and the loop stops at the bar or the budget. See the [guide](docs/adversarial-review.md) and the [evaluation](evaluations/adversarial-review.md).
- **Strategy Prompt 1.0.0.** New skill. It steelmans every option, scores them in a weighted matrix, checks its own pick, then gives a final recommendation. See the [guide](docs/strategy-prompt.md) and the [evaluation](evaluations/strategy-prompt.md).
- **Finish Work 1.0.0.** New skill. Before an agent says "done" it runs the right checks for the kind of work, keeps "local" apart from "live", and writes a receipt to a file you choose. See the [guide](docs/finish-work.md) and the [evaluation](evaluations/finish-work.md).
- **Install for Claude Code, Codex or both.** `scripts/skills.py install <name> --host claude|codex|both`. It also takes several skill names at once, and prints what each skill needs and a prompt to try.
- **`--update`.** Replaces a skill you already installed. Your old copy is moved to a `skills-backup` folder first.
- **Installer safety.** An empty `--target-root` is refused. When both hosts share one skills folder, `--host both` installs there once.
- **Agent entry points.** [`AGENTS.md`](AGENTS.md) has install steps with a check for each one. [`llms.txt`](llms.txt) is a short index. `CLAUDE.md` points Claude Code at the agent guide.
- **`llms.txt` is enough on its own.** Each skill line now carries its try prompt and what it needs, and a test keeps it in step with `catalog.json`.
- **Catalog fields.** Every skill in `catalog.json` now has `use_when`, `try` and `hosts`. The catalog also lists the install command for each host.

**Changed**

- **Ambitious 1.3.1.** The leaner body the author runs every day: five moves per run, and the extras (more crew fields, the working sketch, the review page, the taste log) only when they fix a named audience problem. In a blind head-to-head on 27 Oct 2026 this body was about even with the 1.2.3 body and about 12% faster, and it missed the adoption rule set before that test by 0.03 on one task. It is published anyway as the owner's choice. The [evaluation](evaluations/ambitious.md) has the numbers, and the `ambitious-v1.2.4` release keeps the earlier body.
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
