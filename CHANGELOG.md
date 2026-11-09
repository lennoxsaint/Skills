# Changelog

What changed in this repository, newest first. Each skill also keeps its own notes in `docs/<skill-name>.md`.

## 10 Nov 2026

**Added**

- **Hill Climb 1.0.0.** New skill. It turns real data into a locked answer key, then climbs to a measured target with fresh agent sessions until the score and two outside judges say it is done. See the [guide](docs/hill-climb.md) and the [evaluation](evaluations/hill-climb.md).
- **Install for Claude Code, Codex or both.** `scripts/skills.py install <name> --host claude|codex|both`. It also takes several skill names at once, and prints what each skill needs and a prompt to try.
- **`--update`.** Replaces a skill you already installed. Your old copy is moved to a `skills-backup` folder first.
- **Installer safety.** An empty `--target-root` is refused. When both hosts share one skills folder, `--host both` installs there once.
- **Agent entry points.** [`AGENTS.md`](AGENTS.md) has install steps with a check for each one. [`llms.txt`](llms.txt) is a short index. `CLAUDE.md` points Claude Code at the agent guide.
- **`llms.txt` is enough on its own.** Each skill line now carries its try prompt and what it needs, and a test keeps it in step with `catalog.json`.
- **Catalog fields.** Every skill in `catalog.json` now has `use_when`, `try` and `hosts`. The catalog also lists the install command for each host.

**Changed**

- **Goal 1.1.0.** Goal now tells apart "create a goal" from "continue the goal that is already running", so a resumed run carries on with the next step and does not rebuild the packet. It also points measurable quality bars at Hill Climb.
- **README.** New front page for Claude Code and Codex users, with one install command per host. The repository is no longer framed around one community.
- **`skills.py list`** now shows when to use each skill.
- **Validation.** A `SKILL.md` may name the word `TODO` inside code formatting. Catalog entries must carry the new fields.

**Unchanged**

- Ambitious 1.2.4, Email Triage Pro 1.0.0 and Save 10% 2.0.1 have the same skill text as before.

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
