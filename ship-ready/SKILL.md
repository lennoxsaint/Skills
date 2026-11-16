---
name: ship-ready
description: Take a task all the way to ready-to-go and stop one tap before it goes out. Do the work, prove it as its audience would meet it, pass council, stage the send, publish or merge, then hand back a one-screen receipt. Use when the user says "ship-ready", "full stop", "bring it back ready to send", "don't come back until it's ready", or hands off work with a public consequence that they do not want to review.
---

# Ship-ready

The user hands off a task so they can stop thinking about it. They hear back once: when the work is ready for a single **go**, or when it is truly stuck. The work counts as ready only when two things are true:

- it has been **proven** the way its audience will meet it
- **council** has passed that exact version at the bar

This skill needs `council` installed beside it.

## What you may do

The grant depends on the words the user used.

- **They said "ship-ready" or "full stop":** you may edit, test, build, preview, render and draft. You may also commit to a task branch, push that branch and open a draft PR in the user's own repos.
- **The skill loaded from any other wording:** you may do the same work, but only locally. Ask once before your first push or PR.

The go stays the user's tap in every case except a staging merge the user has pre-authorized for this project (step 5). That covers send, publish, schedule, merge, deploy, charge, delete, and any change to access or pricing.

## 1. Contract

Write the contract in four lines:

- the **outcome**
- the **audience**
- the **go action**: for example "merge PR #12 into main", "send the email draft to the client" or "schedule the saved post"
- the **bar**: the council score the user named, or 9 if they named none

Before your first push, check whether that push could trigger the go on its own, for example through a merge queue or a deploy-on-push branch. Never change repo settings to prevent it: if it could, stop and report BLOCKED. Open every PR as a draft, so nothing merges before council.

Done when someone with no context could tell from the contract what "ready" means and what the go is.

## 2. Build

Do the work. Settle reversible choices yourself and log each one for the receipt. Ask the user only for things only they can give: a secret, a spend, new access or a change of goal. Keep to the scope of the contract. Anything the work uncovers that falls outside it goes on a follow-up list.

## 3. Prove

Meet the work the way its audience will. Save the proof to disk.

| Work | Proof |
|---|---|
| Code | Covering tests pass. Run the real flow, and capture a screenshot or recording of any UI. Open the draft PR and get CI green now, before council. |
| Email or DM | Read it as the recipient will. Check every fact against its source, click every link, and cut AI-writing tells. |
| Post | Apply the brand and voice files the user named. Run the platform's own validator or preview, if it has one. |
| Page or design | Screenshots at phone and desktop width, in light and dark themes, with a clean console. |
| Doc or plan | Check every number and claim against its source. |

Done when each part of the outcome has a proof file or a command output behind it.

## 4. Council

Run `council` at the bar on the proven version. A pass needs all three labs. A two-lab result goes back to the user as NOT READY, unless they waived the missing lab. A SINGLE-SEAT PASS is READY only when they asked for one reviewer.

A TAP OUT or BLOCKED result goes to step 6 under that name. It never comes back as READY.

## 5. Stage the go

Set things up so the go is one action:

- **PR**: green and mergeable, with the council section in its description. Check auto-merge and the merge queue again; if marking it ready would merge it, report BLOCKED. Otherwise mark it ready for review.
- **Email**: a draft in the user's mail app, to the right recipient.
- **Post**: a saved draft in the user's scheduler.
- **Deploy**: the exact command.

Read the live state back. Compare what is staged with the version council passed. If the content differs, run a confirm round (council step 6). Unless it passes, hand back NOT READY and send nothing.

**Pre-authorized staging merge.** Some projects let the agent squash-merge to a staging branch before the real go, which is then a production release by the user or someone they name. Follow that order: council passes the PR head first; then the squash merge; then compare the squash patch `git diff <squash-sha>^ <squash-sha>` with the reviewed `git diff <base> <pr-head>`, and run a confirm round if they differ; then the staging retest. Any fix after the merge needs a confirm round before it merges. Only when council has passed the exact staged content and the retest is green, send the one message that asks for the release.

## 6. Hand back

Send the one message the user reads:

```
READY: <outcome> — go = <the one action>
Council: <PASS at bar · rounds · version · scores table>
Proof: <paths/links>
Decided for you: <each reversible choice you settled>
Left out on purpose: <follow-ups>
Risks still open: <none, or each in one line>
```

If the work is not ready, open the message with `NOT READY: <why>`. Then give:

- the best staged version
- each open dispute, 2-3 lines per side
- the one thing that would unblock it

Stop and wait for the user's go. Log the run with `finish-work` if it is installed.
