# Ship-ready

Ship-ready is for work you want handed back ready to go, so you only have to press one button.

Your agent does the work, proves it the way its audience will meet it, runs [Council](council.md) on that exact version, and stages the go: a ready PR, an email draft, a saved post or a deploy command. Then it sends you one message and stops. You hear back once, when it is ready or when it is truly stuck.

## When it runs

- "ship-ready: add CSV export to the reports page"
- "full stop on the password reset bug"
- "don't come back until the launch email is ready to send"
- "bring this landing page back ready to publish, council 9.5"

## How it works

1. **Contract.** Four lines: the outcome, the audience, the go action, and the bar (9 unless you name one).
2. **Build.** It does the work and settles reversible choices itself, logging each one for you. It asks you only for a secret, a spend, new access or a change of goal.
3. **Prove.** Tests and the real flow for code, every fact and link for an email, screenshots at phone and desktop width for a page. The proof is saved to disk.
4. **Council.** Three labs must pass the exact proven version. A two-lab result comes back as NOT READY unless you waived the third lab.
5. **Stage the go.** The PR is green with the council scores in its description, the email is a draft, the post is saved. It reads the live state back. If what is staged differs from what council passed, it runs a confirm round.
6. **Hand back.** One message: READY with the one go action, or NOT READY with the best version, each open dispute and the one thing that would unblock it.

## What it may do

| You said | It may |
|---|---|
| "ship-ready" or "full stop" | Edit, test, build and draft, commit to a task branch, push it, and open a draft PR in your own repos |
| anything else that loaded it | The same work, locally only. It asks once before the first push or PR. |

## What it will not do

- It will not send, publish, schedule, merge, deploy or charge. The go is your tap.
- It will not change repo settings. If a push could trigger the go on its own, through a merge queue or deploy-on-push, it stops and reports BLOCKED.
- It will not mark a PR ready if that would set off auto-merge. Every PR starts as a draft.
- It will not report READY on a tap out, a block or a two-lab result.

## Install

Ship-ready runs Council, so install both:

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install ship-ready council --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away. [Finish Work](finish-work.md) is optional: when it is installed, ship-ready logs the run with it.

Then try:

```text
Ship-ready: fix this bug, prove it, pass council 9, and stop before the merge.
```

## What you need

The Council skill and what it needs: reviewers from three AI labs your agent can reach. For code, git and a GitHub CLI or connector to open the PR.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The grant, the six steps, and the hand-back message |

A synthetic example lives in [`examples/ship-ready/`](../examples/ship-ready/sample-handback.md). The test evidence is in the [evaluation](../evaluations/ship-ready.md).

## Changelog

**1.0.0** (16 Nov 2026) - first public release. This is the hand-off I use, with my private paths, tools and one product-specific release rule replaced by general ones. Its text went through the same five-round council as Council. It has not yet run end to end on a real task.
