# Skills

Practical, safety-gated AI agent skills from [Lennox Saint](https://github.com/lennoxsaint) and Codex Club.

[![Validate skills](https://github.com/lennoxsaint/Skills/actions/workflows/validate.yml/badge.svg)](https://github.com/lennoxsaint/Skills/actions/workflows/validate.yml)

Every skill is a self-contained folder with instructions, UI metadata, deterministic helpers where needed, and public validation evidence. Install only the skill you want.

## Available skills

| Skill | What it does | Status | Version |
|---|---|---:|---:|
| [Save 10%](save-10-percent/SKILL.md) | Audits recurring costs, verifies actual use, finds 10% in safe net savings, and can execute an exact approved batch. | Stable | 2.0.1 |

See the machine-readable [catalog](catalog.json), the [plain-English guide](docs/save-10-percent.md), or the [evaluation evidence](evaluations/save-10-percent.md).

## Install in under a minute

### Option 1: clone and install one skill

```bash
git clone https://github.com/lennoxsaint/Skills.git
cd Skills
python3 scripts/skills.py list
python3 scripts/skills.py install save-10-percent
```

The installer uses `$CODEX_HOME/skills` when `CODEX_HOME` is set, otherwise `~/.codex/skills`. It validates the repository first and refuses to overwrite an existing skill.

Restart Codex if the new skill does not appear immediately, then try:

```text
Use $save-10-percent to audit my recurring costs and keep working until you find 10% in safe net savings or prove the honest shortfall.
```

### Option 2: download a release

Open [Releases](https://github.com/lennoxsaint/Skills/releases), download the ZIP for the skill you want, and upload or copy that skill folder through your client’s normal Skills interface.

For Codex, the destination is normally:

```text
~/.codex/skills/<skill-name>/
```

The folder must contain `SKILL.md` directly. Avoid accidentally creating `<skill-name>/<skill-name>/SKILL.md`.

## Compatibility

- Codex: supported through the standard local skill-folder format.
- Claude and compatible clients: use the release ZIP or the client’s skill upload flow when supported.
- Python: individual skills declare their own requirements in the catalog and documentation.
- Browser actions: available only when the host proves authenticated controls, live readback, safe interruption, and receipt capture.

No skill may bypass MFA, CAPTCHA, passkeys, permissions, approval gates, or irreversible warnings.

## Browse without installing

```bash
python3 scripts/skills.py list
python3 scripts/skills.py show save-10-percent
python3 scripts/skills.py validate
```

## Repository layout

```text
catalog.json                    Public skill index
scripts/skills.py               List, inspect, validate, and install skills
scripts/build_skill_release.py  Build one deterministic release ZIP
<skill-name>/                   One self-contained installable skill
docs/<skill-name>.md            Human guide
evaluations/<skill-name>.md     Test evidence and known limits
examples/<skill-name>/          Synthetic, non-private examples
tests/<skill-name>/             Trigger and release evidence
```

Adding another skill means adding one folder and one catalog entry. Repository validation rejects missing metadata, broken references, syntax errors, weak trigger banks, duplicate names, and uncatalogued skill folders.

## Privacy

Never commit real statements, invoices, credentials, cookies, private screenshots, provider receipts, or customer data. Examples in this repository are synthetic.

## Development

```bash
python3 scripts/skills.py validate
python3 -m unittest discover -v -s tests -p 'test_*.py'
python3 -m unittest discover -v -s save-10-percent/scripts -p 'test_*.py'
python3 scripts/build_skill_release.py save-10-percent /tmp/save-10-percent.zip
```

Every push validates the full catalog and every registered skill. Skill tags use `<skill-name>-v<version>` and publish only that skill’s deterministic ZIP.

Licensed under MIT.
