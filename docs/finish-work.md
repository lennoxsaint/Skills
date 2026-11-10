# Finish Work

finish-work is what your agent runs before it says "done".

most agents stop when the code compiles or the draft exists. this skill makes the agent prove the thing it changed, say plainly what is proven and what is not, and leave a receipt you can read next week.

## when it runs

- a real task is about to be called done
- the work hits a checkpoint worth writing down
- the work stops early: partial, waiting or blocked
- you say "finish this", "close this out", "wrap this up" or "is it really done?"

it is not for a quick answer or routine chat.

## what it does

1. **picks the right checks.** it reads only the closeout guide that fits the work.

   | kind of work | what the agent checks |
   |---|---|
   | research, advice, documents | the answer against the request and its sources. no test suite needed. |
   | code and config | the project's own checks, the whole final diff, and the changed behavior through its real entry point |
   | anything you can see | the running app at desktop and phone sizes, plus console errors |
   | a release or outside action | only what you said yes to. then it reads back the real result from the provider. |

2. **keeps proof states apart.** local, visible, staged, scheduled, published and delivered are six different claims. a passing test proves the test passed. it does not prove the thing is live.
3. **stops patching after two failed fixes.** it writes down what it learned and starts again from fresh evidence.
4. **writes a receipt.** one entry in a dated file: what was asked, what is true now, the checks and their results, the decisions, what is left.
5. **closes in a few lines.** the outcome, what could not be verified, what is left, and where the receipt is.

## the receipt

a small helper writes it, so every entry has the same shape:

```bash
python3 <skill-dir>/scripts/log_receipt.py \
  --status blocked \
  --objective "update the prices and publish them" \
  --outcome "prices saved locally. not published: the publish token is missing." \
  --check "./publish.sh: exit 1, token not set" \
  --next "get the token, then run ./publish.sh"
```

where it goes, first match wins:

1. the work log your project's own instructions name
2. the folder in `FINISH_WORK_LOG_DIR`
3. `~/.finish-work/log/`

the status is one of `completed`, `in_progress`, `waiting`, `blocked`, `cancelled` or `unknown`. the helper only adds entries and never edits an old one. run the same command again from the same folder, today or tomorrow, and it skips the receipt it already wrote. if a write was cut off halfway, the retry writes the whole entry. it uses only what ships with Python and sends nothing anywhere.

## what it will not do

it gives the agent no new permission. a fix on your machine does not mean "deploy it". if a release needs a yes, the agent gets everything ready and names the one step that is left.

it will not call blocked work complete.

## install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install finish-work --host claude
```

use `--host codex` for Codex, or `--host both` for both. start a new session if the skill does not show up right away.

then try:

```text
Use finish-work to close this out: run the right checks, tell me what is proven, and write the receipt.
```

## what you need

Python 3.9 or newer for the receipt helper. nothing else to install.

## files in the skill

| file | what it is |
|---|---|
| `SKILL.md` | the proof rules and how to close |
| `references/research.md` | closeout for research, advice and documents |
| `references/code.md` | closeout for code and config |
| `references/ui.md` | closeout for anything you can see |
| `references/release.md` | closeout for a release or outside action |
| `references/receipt.md` | where the receipt goes and how to write it |
| `scripts/log_receipt.py` | the receipt helper |

two synthetic tasks live in [`examples/finish-work/`](../examples/finish-work/sample-task.md), with the receipts they should leave. the test evidence is in the [evaluation](../evaluations/finish-work.md).

## changelog

**1.0.0** (10 Nov 2026) - first public release. this is the closeout i run on every real task, cleaned up for anyone to use. my private work log became a receipt file you choose, and one product's release rules were left out. four lines were made clearer after two tests with agents that had never seen the skill. a different model then reviewed the receipt helper twice and found ways it could skip or double a receipt. the [evaluation](../evaluations/finish-work.md) lists each one and what was done.
