# Loop

Loop is for one draft you want right, now.

You hand it a draft. It writes a 100-point rubric for that draft, scores it, fixes the weakest part and scores again. It stops at 100/100. If it can't get there honestly, it stops and tells you which points are missing and why.

## When it runs

It runs when you ask for it:

- "loop this"
- "make it 100/100"
- "iterate until it's perfect"
- "improve this draft"
- "give me the criteria and run them"

It works on local things: a post, an email, a script, a thumbnail, a carousel, a spec.

It is not for long jobs that need a number you can prove. The loop grades its own work. For a locked test set and outside judges, use [Hill Climb](hill-climb.md).

See also [Council](council.md): reviewers from three AI labs score the work instead of the agent grading itself.

## How a loop works

1. **Find the truth.** The draft, and the facts it is allowed to use.
2. **Write the rubric.** 5 to 8 criteria that add up to exactly 100. Your own checklists and style rules come first when you have them.
3. **Score the start.** Every lost point gets a name.
4. **Fix the smallest thing that helps.**
5. **Check it.** A validator, a screenshot, a diff, a readback. No points without something you can see.
6. **Score again.** Repeat until 100/100, 10 loops, or two loops with no gain.

Some criteria are **hard vetoes**: a wrong fact, fake proof, text you can't read on a phone. While one of those fails, the loop can't call the work done, whatever the other points add up to.

## What you get back

A scorecard:

| Part | What it says |
|---|---|
| Status | `score_100`, `blocked_below_100`, or the reason it had to stop |
| Rubric | The criteria and their weights |
| Scores | Start, each loop, final |
| Lost points | What is missing and why, when it stops below 100 |
| Files | What changed |
| Proof | Which checks ran |
| Live actions | What it did not send, post or publish |
| Who scored | The same agent that did the work. The scorecard says so. |

## What it will not do

It will not send, publish, schedule, deploy, merge, charge or delete anything unless you said yes to that exact action in the same message. It stops at logins, codes, CAPTCHAs and payment screens.

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install loop --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Loop this draft: make it 100/100 or tell me exactly what blocks it.
```

## What you need

Nothing to install. The agent needs to be able to read and edit the draft.

## Files in the skill

| File | What it is |
|---|---|
| `SKILL.md` | The contract, the eight steps, the scoring rules |
| `references/rubric-adapters.md` | Starting rubrics for thumbnails, video, writing, social posts and pipelines |

A synthetic example lives in [`examples/loop/`](../examples/loop/sample-draft.md). The test evidence is in the [evaluation](../evaluations/loop.md).

## Changelog

**1.0.0** (10 Nov 2026) - first public release. This is the loop I run, with my private rubric names and product notes replaced by general ones. Three lines were made clearer after a test with an agent that had never seen the skill: what a hard veto does, where the adapter file lives, and that the scorecard must say the loop scored itself.
