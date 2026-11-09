# Agent guide

This repository holds installable agent skills. Each skill is one folder with a `SKILL.md`. `catalog.json` is the index.

## Install a skill for a user

Work from a clone: `git clone --depth 1 https://github.com/lennoxsaint/Skills.git && cd Skills`. The installer needs only Python 3.

1. **Pick the skill.** Run `python3 scripts/skills.py list` and match the user's task to a `USE WHEN` line.
   Done when you can name one skill and quote the line that matched. If no line matches, say so and stop.
2. **Pick the host.** Install for the agent you are running in, unless the user names another.

   | Host | Flag | Installs to |
   |---|---|---|
   | Claude Code | `--host claude` | `$CLAUDE_CONFIG_DIR/skills`, else `~/.claude/skills` |
   | Codex | `--host codex` | `$CODEX_HOME/skills`, else `~/.codex/skills` |
   | Both | `--host both` | both folders |
   | Anything else | `--target-root <dir>` | the skills folder you name |

3. **Install.** Run `python3 scripts/skills.py install <skill-name> --host <host>`. Several names in one command are fine: `python3 scripts/skills.py install hill-climb goal --host both`.
   Done when it prints `Installed <skill-name> <version> to <path> (<host>)` and `<path>/SKILL.md` exists.
   If it prints `Refusing to overwrite`, the user already has that skill. Ask before you rerun with `--update`: it moves their copy to a `skills-backup` folder beside the skills folder, then installs this one.
4. **Check what it needs.** Read the `Needs:` line the installer printed (`python3 scripts/skills.py show <skill-name>` prints it again as `requires`). Check each item on the user's machine with its version command, such as `node --version`. The agent you are running in counts as that agent's CLI.
   Done when every item is present, or you have told the user which one is missing.
5. **Hand over.** Tell the user to start a new session, then give them the `try` prompt the installer printed. Claude Code also takes `/<skill-name>`. Codex also takes `$<skill-name>`. Where the host has a built-in command with the same name, as with `/goal`, give the `try` prompt.
   Done when the user has the prompt and the install path.

Installing a skill copies files. It grants nothing: each skill states its own approval gates, and they still apply.

## Find things

| Need | Where |
|---|---|
| Every skill as data (`use_when`, `try`, `requires`, `hosts`, `version`) | `catalog.json` |
| What a skill does, in plain words | `docs/<skill-name>.md` |
| What was tested and the known limits | `evaluations/<skill-name>.md` |
| A synthetic example run | `examples/<skill-name>/` |
| What changed | `CHANGELOG.md` |

## Change this repository

Every skill ships six things: the skill folder (with `agents/openai.yaml`), a catalog entry, `docs/<name>.md`, `evaluations/<name>.md`, an `examples/<name>/` folder and `tests/<name>/trigger-cases.json` with 20 or more positive and 20 or more negative prompts.

- `SKILL.md` frontmatter holds exactly `name` and `description`.
- A changed skill gets a version bump in `catalog.json`, the README table, its evaluation file and `CHANGELOG.md`.
- Evaluation files report only what was measured. An unmeasured thing is written as a limit.
- Examples are synthetic. Personal paths become an environment variable or a `~/` default so the skill works for a stranger.
- Done when `python3 scripts/skills.py validate` prints `PASS` and `python3 -m unittest discover -s tests -p 'test_*.py'` passes.
