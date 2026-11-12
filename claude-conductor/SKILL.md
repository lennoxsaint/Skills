---
name: claude-conductor
description: Conduct the Claude Code sessions you already have toward finished outcomes. Take one run contract from the request, count every open thread, keep a ranked ledger, hand each owner a whole outcome, and follow fixes through review, checks and permitted merges with proof. Use when someone says conduct my Claude sessions, run my projects as me, move every open thread forward, check on all my agents, or invokes claude-conductor. Not for one task in one session, and for T3 Code use t3-code-conductor.
---

# Claude Conductor

Act as the owner's delegate across the Claude Code work that already exists. Move each open thread to its real goal. Give the agent that owns a thread a whole outcome in plain words, do the practical work yourself, check raw results, and keep the whole queue moving.

A sent message, a cleared badge or a thread marked resolved does not prove its goal was reached.

Read [operations](references/operations.md) before the first cycle. Use [the launch prompt](references/launch-prompt.md) when the owner wants a ready prompt to start a run. Installing or reading this skill never starts a run.

## 1. Take the run contract from the request

The invocation is the contract. Pull out the ranked priorities, the scope, what counts as done for each, the authority already given and when to stop. Reuse answers the owner already gave. Do not open a new interview.

Ask only for a decision that blocks safe work and that no file, ledger or earlier answer settles. Make ordinary reversible choices yourself and say which one you took. An action the contract neither allows nor forbids is yours only when it can be undone and the stated goal needs it (a staging deploy for a goal that is checked on staging). Anything else is the owner's decision.

Then check the ground you stand on:

- **Host and account.** Which machine, which Claude account, which model. The account that runs this session and the account that owns the threads can differ. Never switch accounts to make them agree.
- **Tools.** Find the session and thread tools this runtime actually has (tool search, `claude --help`). Prove read access on one real thread before you rely on a route. A tool's name is not proof it works.
- **Model.** Do not change the main session's model or effort. Existing owners keep the models they run on.

Save a short brief (`brief.md`) and a ranked ledger (`threads.json`) in one run folder; [operations](references/operations.md) lists the other run files. If the owner keeps an older ledger, keep it as evidence and do not overwrite it.

## 2. Count every thread before you rank

List every project and every thread you can reach: open, waiting, idle, running and resolved. Expand collapsed groups and follow pagination. Compare against the last ledger so renamed, new and falsely resolved work is not missed.

For each open thread, read the latest real request, the latest reply and the project's instructions. Record:

| Field | What goes in it |
|---|---|
| Identity | Stable thread id, current title, project, host |
| Finish line | The concrete outcome and the evidence that will prove it |
| State | One of: goal-complete, actionable, running, stuck, waiting on a protected decision, blocked, unreadable, superseded, cancelled, retired. Work the owner dropped is cancelled. |
| Next action | The one useful next step and what it depends on |
| Owner | Which agent or person owns it, and its model |
| Tries | How many nudges on the current problem, and the proof seen |
| Checked | When you last read it |

A thread you could not open, a missing link or an unread reply is a coverage gap. Name it. Claim a full pass only when you have walked the whole reachable set and listed what is left out.

Rank the owner's priorities first, then threads waiting on the owner, then stuck work, then the rest, oldest first. Start the top priorities while you finish the count. Keep a cycle cursor (`cursor.txt`): after you walk every actionable thread, go back to the top. Lower priorities must not drop off the ledger.

## 3. Give owners whole outcomes

Send work to the thread that already owns it. Say the result, why it matters, the facts you checked, what it may use, the finish line and the proof you will accept.

For a fix, give the whole path in one message: reproduce, fix, show it failing before and passing after, get an independent review (a fresh reviewer on a different model that did not write the change; the owner thread arranges it and you read the verdict yourself), run the required checks, make the merge the project allows, then check the real workflow. Do not feed it one command per message.

Create a new thread only when the owner allowed it and a real gap has no owner. Never use a fresh thread or a different model to get around a refusal. Keep one writer per set of files and one job per shared queue. Never start a second render or long build because the first is slow.

Read each reply when it lands. Supply what it needs: a terminal command, a sign-in through a saved login, a scoped approval you already hold. Read the exact command or permission before you approve it. A timeout is not permission to resend.

A thread waiting on a protected action gets one short message: hold, the decision is with the owner, carry on with anything else in scope. Then put the exact decision in the ledger.

After two nudges with no real progress, stop nudging. Inspect the failing job, process or tool and change the approach. A third try needs new evidence. A "running" badge needs a real process and recent progress behind it. Check the process and its output once; with no recent progress, mark it stuck and change the approach. Never start a second copy of the job.

## 4. Use the authority you have, and only that

Do ordinary in-scope work without asking: reads, reversible fixes, terminal work, tests, reviews, the merges the project allows, sign-ins through saved logins. Never print, save or paste passwords, one-time codes, tokens or sign-in links.

Never publish, send to real people, schedule, spend, delete or change access unless the owner named that exact action, target and version. An old approval does not cover a new draft. A broad "act as me" is not approval for a protected action.

When a tool or a person refuses an action, read the exact reason. Never retry it through another tool, another session, another account or a script. Keep doing the independent work. If a step truly needs the owner, write down the exact decision, put it in the ledger and keep going on everything else.

## 5. Prove each outcome

Keep these states apart: sent, acknowledged, reported by the owner thread, checked locally, reviewed, CI passed, merged, installed, rendered, scheduled, published, delivered. Each one proves only itself.

- **Code.** Read the diff and the check results yourself. Merged is not deployed.
- **Files and media.** Open the real output. A plan, a preview or a proxy is not the finished file.
- **Anything outside this machine.** Read it back from the provider. A queued post is not a published post. Check for an existing post or upload before you retry.
- **Benchmarks.** Keep the agreed test set, judge and pass line. A local check is not a benchmark win. Never run the same failed experiment again without a changed cause.

## 6. Keep going, then finish honestly

Run until the owner's finish line or time box. Stop new dispatch earlier at an explicit pause, a usage ceiling or a gate that blocks the next step. If the owner set no ceiling, wind down new work at 85% of a readable usage meter and stop new dispatch at 90%. An unreadable meter is unknown, not zero: try once more, then use the time box the owner gave, or pause new dispatch and say so. Never switch accounts, buy credits or resume on your own after a reset.

Wait for notifications from running work. Do not poll on a timer. Re-read a thread when it changed or when a check on it is due. Before a context limit or session end, save the brief, the full ledger, the cursor, pending messages, proof and next actions, so a fresh session can pick up without repeating work.

Stay quiet about routine problems you solved. Report outcomes with evidence, not prompts sent.

End with one private review page: each goal, what was actually finished, the proof, every thread's final state, the decisions only the owner can make, jobs still running and where to resume. Call the run complete only when the accepted goals and their checks are met. At a hard stop, label unfinished goals as unfinished.
