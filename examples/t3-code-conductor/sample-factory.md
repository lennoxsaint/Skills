# Sample factory: a made-up owner's T3 Code threads

Everything here is synthetic. The company, people, repositories, machines and threads are made up.

## STANDING.md (the owner's standing decisions)

```markdown
## Priorities, in order
1. Mobile app sign-up works on the beta build - done means a beta build where a new account can sign up, proven by a screen recording
2. Weekly newsletter ready by Friday - done means a reviewed draft on the desk
3. Everything else: keep moving

## The conductor may do alone
- run tests, open PRs, merge to the `staging` branch after an outside review PASS at the exact head
- answer lanes from earlier decisions in the ledger
- pick the recommended option on any choice that can be undone before anything goes out

## Always needs the owner
- publish, send email to subscribers, spend, delete, merge to `main`, taste calls on design

## Limits
- wind down at 85% usage, stop new dispatch at 90%; time box 6 hours

## The owner's own threads (read, never steer)
- "Sketchbook" on the laptop
```

## What the census finds

Two machines are connected: a laptop and a desktop.

| Thread | Machine | State | Latest request | Latest reply |
|---|---|---|---|---|
| A "signup bug" | laptop | waiting | "fix sign-up on the beta build" | "Fixed in PR 12. Tests pass on my branch. Merge to main?" No outside review yet. |
| B "newsletter" | desktop | waiting | "draft this week's newsletter" | "Draft ready. Which subject line: 'What we shipped' or 'Three new things'?" |
| C "icons" | laptop | completed | "redraw the app icons" | "Done." The icon files are not in the repo. |
| D "Sketchbook" | laptop | running | the owner's own notes | — |
| E "analytics" | desktop | idle | "add sign-up analytics" | Created yesterday, no lane in the roster. |
| F (unnamed) | desktop | — | — | Listed but cannot be read. |

The ledger already holds this line from last week: `- 2026-11-02 owner: newsletter subject lines should say what shipped, not count things.`

## What a good first cycle does

| Thread | Outcome |
|---|---|
| A | Not merged to `main`: that needs the owner. The conductor orders an outside review on a different model at PR 12's exact head commit. On PASS it may merge to `staging`. The `main` merge becomes a desk card with the review verdict and the recording. |
| B | Answered from the ledger: "What we shipped". One ledger line names the earlier decision. No desk card. |
| C | Reopened. "Done" with no files is a claim, not proof. The lane is told the finish line: icon files committed and visible in the beta build. |
| D | The owner's own thread. Read, not steered. |
| E | Gets a lane: a roster row and a ledger line. |
| F | A named gap in the census. Open threads with no lane: 0, with F listed as unreadable. |

## The desk after the cycle

```bash
D=<skill-dir>/scripts/desk.py
export CONDUCTOR_HOME=~/conductor
python3 $D add c-main-merge --title "Merge the sign-up fix to main?" \
  --why "PR 12 passed outside review at commit 9b1e4d2. Staging sign-up works: recording below." \
  --yes "Merge to main" --no "Keep it on staging" --lane signup-bug --priority 1 \
  --link https://example.com/recordings/signup-staging
python3 $D lint && python3 $D render
```

The page headline reads "1 decision needs you". The owner sends `answer c-main-merge yes` to the conductor thread. The conductor records it, tells the lane, marks the card routed and adds one ledger line.
