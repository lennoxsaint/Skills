# Loop

loop is for one draft you want right, now.

you hand it a draft. it writes a 100-point rubric for that draft, scores it, fixes the weakest part and scores again. it stops at 100/100. if it can't get there honestly, it stops and tells you which points are missing and why.

## when it runs

it runs when you ask for it:

- "loop this"
- "make it 100/100"
- "iterate until it's perfect"
- "improve this draft"
- "give me the criteria and run them"

it works on local things: a post, an email, a script, a thumbnail, a carousel, a spec.

it is not for long jobs that need a number you can prove. the loop grades its own work. for a locked test set and outside judges, use [Hill Climb](hill-climb.md).

## how a loop works

1. **find the truth.** the draft, and the facts it is allowed to use.
2. **write the rubric.** 5 to 8 criteria that add up to exactly 100. your own checklists and style rules come first when you have them.
3. **score the start.** every lost point gets a name.
4. **fix the smallest thing that helps.**
5. **check it.** a validator, a screenshot, a diff, a readback. no points without something you can see.
6. **score again.** repeat until 100/100, 10 loops, or two loops with no gain.

some criteria are **hard vetoes**: a wrong fact, fake proof, text you can't read on a phone. while one of those fails, the loop can't call the work done, whatever the other points add up to.

## what you get back

a scorecard:

| part | what it says |
|---|---|
| status | `score_100`, `blocked_below_100`, or the reason it had to stop |
| rubric | the criteria and their weights |
| scores | start, each loop, final |
| lost points | what is missing and why, when it stops below 100 |
| files | what changed |
| proof | which checks ran |
| live actions | what it did not send, post or publish |
| who scored | the same agent that did the work, said plainly |

## what it will not do

it will not send, publish, schedule, deploy, merge, charge or delete anything unless you said yes to that exact action in the same message. it stops at logins, codes, CAPTCHAs and payment screens.

## install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install loop --host claude
```

use `--host codex` for Codex, or `--host both` for both. start a new session if the skill does not show up right away.

then try:

```text
Loop this draft: make it 100/100 or tell me exactly what blocks it.
```

## what you need

nothing to install. the agent needs to be able to read and edit the draft.

## files in the skill

| file | what it is |
|---|---|
| `SKILL.md` | the contract, the eight steps, the scoring rules |
| `references/rubric-adapters.md` | starting rubrics for thumbnails, video, writing, social posts and pipelines |

a synthetic example lives in [`examples/loop/`](../examples/loop/sample-draft.md). the test evidence is in the [evaluation](../evaluations/loop.md).

## changelog

**1.0.0** (10 Nov 2026) - first public release. this is the loop i run, with my private rubric names and product notes replaced by general ones. three lines were made clearer after a test with an agent that had never seen the skill: what a hard veto does, where the adapter file lives, and that the scorecard must say the loop scored itself.
