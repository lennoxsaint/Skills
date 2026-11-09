# Skills

**AI agent skills I built for my own work. They make your agent finish the job and show receipts.**

Works in Claude Code and Codex. One command to install. By [Lennox Saint](https://github.com/lennoxsaint).

[![Validate skills](https://github.com/lennoxsaint/Skills/actions/workflows/validate.yml/badge.svg)](https://github.com/lennoxsaint/Skills/actions/workflows/validate.yml)

## Pick a skill

| Skill | What it does | Try saying | Version |
|---|---|---|---:|
| [Hill Climb](hill-climb/SKILL.md) | Turns your real data into locked tests, then keeps improving the work until the score and two outside judges say it is done. | "Hill climb this until 90% of the cases pass." | 1.0.0 |
| [Ambitious](ambitious/SKILL.md) | Goes deeper on a big task you flag as important, then has a different AI model score the work instead of grading itself. | "Go above and beyond on this." | 1.2.4 |
| [Goal](goal/SKILL.md) | Turns a plan into one bounded goal an agent can run for hours: a durable Codex goal packet or a compact Claude `/goal` prompt. | "Turn this plan into a goal." | 1.1.0 |
| [Save 10%](save-10-percent/SKILL.md) | Audits recurring costs, verifies actual use, finds 10% in safe net savings, and can execute an exact approved batch. | "Find 10% in safe savings." | 2.0.1 |
| [Email Triage Pro](email-triage-pro/SKILL.md) | Reviews Gmail, surfaces important mail, drafts a few replies, and learns archive and writing preferences. | "Triage my Gmail." | 1.0.0 |

Each skill has a plain guide in [`docs/`](docs), test evidence in [`evaluations/`](evaluations), and a synthetic example in [`examples/`](examples).

## Install in one command

Swap `hill-climb` for any skill name in the table.

**Claude Code**

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git && python3 Skills/scripts/skills.py install hill-climb --host claude
```

**Codex**

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git && python3 Skills/scripts/skills.py install hill-climb --host codex
```

**Both**

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git && python3 Skills/scripts/skills.py install hill-climb --host both
```

Then start a new session and say the "Try saying" line. In Claude Code you can also type `/hill-climb`. In Codex you can type `$hill-climb`.

What the installer does:

- `--host claude` copies the skill to `~/.claude/skills/` (or `$CLAUDE_CONFIG_DIR/skills/`).
- `--host codex` copies it to `~/.codex/skills/` (or `$CODEX_HOME/skills/`).
- It needs only Python 3. It checks the repository first and will not overwrite a skill you already have.
- Install several at once: `python3 Skills/scripts/skills.py install hill-climb goal ambitious --host both`.

To update a skill you already installed:

```bash
git -C Skills pull && python3 Skills/scripts/skills.py install hill-climb --host both --update
```

`--update` moves your old copy to a `skills-backup` folder beside the skills folder, then installs the new one.

## If you are an agent

Read [`AGENTS.md`](AGENTS.md). It has the install steps with a check for each one. [`catalog.json`](catalog.json) lists every skill with a `use_when` line, a `try` prompt and what it `requires`. [`llms.txt`](llms.txt) is the short index.

```bash
python3 scripts/skills.py list              # every skill and when to use it
python3 scripts/skills.py show hill-climb   # one skill as JSON
```

## What every skill ships with

| You get | Where | Why |
|---|---|---|
| The skill | `<skill-name>/SKILL.md` | What the agent reads and follows |
| A plain guide | `docs/<skill-name>.md` | What it does, how to install it, what it needs |
| Test evidence | `evaluations/<skill-name>.md` | What was tested, the numbers, and the known limits |
| A made-up example | `examples/<skill-name>/` | The shape of a run, with no private data |
| Trigger cases | `tests/<skill-name>/trigger-cases.json` | 20 or more prompts that should load the skill and 20 or more that should not |

A skill that can't show this does not get merged. CI checks it on every push.

## Other ways to install

Open [Releases](https://github.com/lennoxsaint/Skills/releases) and download the ZIP for one skill. Unzip it into your skills folder, or upload it through your app's skill upload screen. The folder must hold `SKILL.md` directly, like `~/.claude/skills/<skill-name>/SKILL.md`.

## Safety

No skill here gives an agent new permission. Sending, posting, buying, deleting and deploying still need your yes. No skill may bypass MFA, CAPTCHA, passkeys, permissions, approval gates or irreversible warnings.

Never commit real statements, invoices, credentials, cookies, private screenshots, provider receipts or customer data. Every example in this repository is synthetic.

## Repository layout

```text
AGENTS.md                       Install steps for agents
llms.txt                        Short index for agents
catalog.json                    Every skill as data
CHANGELOG.md                    What changed and when
scripts/skills.py               List, show, validate and install skills
scripts/build_skill_release.py  Build one release ZIP
<skill-name>/                   One self-contained skill
docs/<skill-name>.md            Plain guide
evaluations/<skill-name>.md     Test evidence and known limits
examples/<skill-name>/          Synthetic examples
tests/<skill-name>/             Trigger cases
```

## Development

```bash
python3 scripts/skills.py validate
python3 -m unittest discover -v -s tests -p 'test_*.py'
python3 -m unittest discover -v -s hill-climb/scripts -p 'test_*.py'
python3 scripts/build_skill_release.py hill-climb /tmp/hill-climb.zip
```

Adding a skill means adding one folder, one catalog entry, and the four files in the table above. Validation rejects missing metadata, broken links, syntax errors, weak trigger banks, duplicate names and uncatalogued skill folders. Skill tags use `<skill-name>-v<version>` and publish only that skill's ZIP.

## Who made this

I'm Lennox. I build [Threadify](https://www.threadify.app/home?utm_source=github&utm_medium=readme&utm_campaign=skills_repo&utm_content=who_made_this), and I run these skills on my own work before I put them here.

Licensed under MIT.
