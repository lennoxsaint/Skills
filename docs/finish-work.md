# Finish Work

Finish Work is what your agent runs before it says "done".

This skill makes the agent prove the thing it changed, say plainly what is proven and what is not, and leave a receipt you can read next week.

## When it runs

- A real task is about to be called done
- The work hits a checkpoint worth writing down
- The work stops early: partial, waiting or blocked
- You say "finish this", "close this out", "wrap this up" or "is it really done?"

It is not for a quick answer or routine chat.

## What it does

1. **Picks the right checks.** It reads only the closeout guide that fits the work.

   | Kind of work | What the agent checks |
   |---|---|
   | Research, advice, documents | The answer against the request and its sources. No test suite needed. |
   | Code and config | The project's own checks, the whole final diff, and the changed behavior through its real entry point |
   | Anything you can see | The running app at desktop and phone sizes, plus console errors |
   | A release or outside action | Only what you said yes to. Then it reads back the real result from the provider. |

2. **Keeps proof states apart.** Local, visible, staged, scheduled, published and delivered are six different claims. A passing test proves the test passed. It does not prove the thing is live.
3. **Stops patching after two failed fixes.** It writes down what it learned and starts again from fresh evidence.
4. **Writes a receipt.** One entry in a dated file: what was asked, what is true now, the checks and their results, the decisions, what is left.
5. **Closes in a few lines.** The outcome, what could not be verified, what is left, and where the receipt is.

## The receipt

A small helper writes it, so every entry has the same shape:

```bash
python3 <skill-dir>/scripts/log_receipt.py \
  --status blocked \
  --objective "update the prices and publish them" \
  --outcome "prices saved locally. not published: the publish token is missing." \
  --check "./publish.sh: exit 1, token not set" \
  --next "get the token, then run ./publish.sh"
```

Where it goes, first match wins:

1. The work log your project's own instructions name
2. The folder in `FINISH_WORK_LOG_DIR`
3. `~/.finish-work/log/`

The status is one of `completed`, `in_progress`, `waiting`, `blocked`, `cancelled` or `unknown`. The helper only adds entries and never edits an old one. Run the same command again from the same folder, today or tomorrow, and it skips the receipt it already wrote. If a write was cut off halfway, the retry writes the whole entry. It uses only what ships with Python and sends nothing anywhere.

## What it will not do

It gives the agent no new permission. A fix on your machine does not mean "deploy it". If a release needs a yes, the agent gets everything ready and names the one step that is left.

It will not call blocked work complete.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install finish-work --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Use finish-work to close this out: run the right checks, tell me what is proven, and write the receipt.
```

## What you need

Python 3.9 or newer for the receipt helper. Nothing else to install.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The proof rules and how to close |
| `references/research.md` | Closeout for research, advice and documents |
| `references/code.md` | Closeout for code and config |
| `references/ui.md` | Closeout for anything you can see |
| `references/release.md` | Closeout for a release or outside action |
| `references/receipt.md` | Where the receipt goes and how to write it |
| `scripts/log_receipt.py` | The receipt helper |

Two synthetic tasks live in [`examples/finish-work/`](../examples/finish-work/sample-task.md), with the receipts they should leave. The test evidence is in the [evaluation](../evaluations/finish-work.md).

## Changelog

**1.0.0** (10 Nov 2026) - first public release. This is the closeout I run on every real task, cleaned up for anyone to use. My private work log became a receipt file you choose, and one product's release rules were left out. Four lines were made clearer after two tests with agents that had never seen the skill. A different model then reviewed the receipt helper twice and found ways it could skip or double a receipt. The [evaluation](../evaluations/finish-work.md) lists each one and what was done.
