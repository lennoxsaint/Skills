# One cycle

A cycle is one supervisory pass. Start one when a lane finished or replied, when an owner answer arrived, when a check is due, or when the scheduled refresh fires. Not on a fixed short timer.

## The pass

1. **Read the state.** The end of `LEDGER.md`, `ROSTER.md`, open cards (`desk.py show`).
2. **Read only what changed.** Lanes whose last run finished or that replied since the last ledger line. Skip quiet lanes that are not due.
3. **For each changed lane, judge the proof, not the claim.** Open the diff, the check output, the file, the readback. Decide: done, needs another step, needs review, blocked, or needs the owner.
4. **Answer what you can.** Check `STANDING.md` and the ledger. Answer the lane, log the decision you used.
5. **Send the next whole outcome** to each lane that needs one (template below).
6. **Order outside reviews** for anything that claims done (review stack below).
7. **Update the desk.** Add a card only for a decision that is truly the owner's. Close cards whose answer was delivered. `desk.py lint`, then `desk.py render`.
8. **One ledger line** with what changed, then wait for notifications.

Walk the roster in order and keep your place in `cursor.txt` in the run folder, so a low-priority lane still gets its turn after the top ones.

## Brief template

```text
<lane name>: <the result>, because <why it matters>.
facts i checked: <short list, with where each came from>.
you may: <tools, repos, branches, accounts>.
you may not: <protected actions for this lane>.
done means: <finish line> proven by <evidence i will check>.
path: reproduce, fix, show it failing then passing, outside review at the exact head,
the checks this project requires, <the merge you may make>, then check the real result.
tell me only when it is done or truly blocked, with the proof.
```

For work that is not code, swap the `path` line for the real steps: `path: draft, outside review of the draft, <the change you may make>, then show me the real result.` Leave out what does not apply; keep the finish line and the proof.

## Review stack

| Role | Who | Gets | Never gets |
|---|---|---|---|
| Builder | The lane thread | The brief | — |
| Independent reviewer | A fresh `delegate_task` on a different model or provider, read-only | The diff or artifact, the acceptance criteria, the exact commit | The builder's summary, scores or reasoning |
| Blind reviewer | A fresh `delegate_task`, read-only | Only the artifact and the rubric | Anything else |
| Judge | The project's sealed test set or judge, if it has one | What its contract says | A changed pass line |

The reviewer reports defects with a plain verdict (PASS or FAIL) at one exact commit. The builder fixes. A fix means a new review at the new head. Reviews are advice unless the project's own rules say otherwise; they never fill the owner's ratings.

## Stuck lanes

- **Two nudges, no progress:** stop nudging. Read the job, process or tool output yourself. Change the approach.
- **"Running" for a long time:** check for a real process and recent output before you believe the badge.
- **A refusal:** read the exact reason. Never retry it through another lane, another model, another account or a script.
- **Never interrupt a lane mid-render.** Wait for it to finish, then steer.

## Handover

When the conductor's context is filling up, or the owner asks:

1. Finish the current step and write the ledger.
2. Create the new conductor thread with the launch prompt from `setup.md`.
3. Update `CONDUCTOR.md` and the conductor row in `ROSTER.md`. Keep a dated backup of each.
4. One ledger line naming the old and new thread.
5. Tell the old thread it is retired. Lanes and timers keep working because they read `CONDUCTOR.md`.
