# Operating mechanics

How a conductor run works in practice. The rules in `SKILL.md` win if this file and that one ever disagree.

## Where the threads are

Claude Code work can live in several places. Check each one the owner uses, and say which ones you could not reach:

| Surface | How to see it |
|---|---|
| Local Claude Code sessions on this machine | The session tools this runtime exposes, or the CLI commands `claude --help` lists |
| Cloud project threads on claude.ai/code | A browser tool the owner has approved, or a native project tool if this runtime has one |
| Background agents and subagents this session started | Their task notifications |
| T3 Code threads running Claude | Use the `t3-code-conductor` skill instead |

A list of local sessions is not a census of cloud projects. If no tool shows a surface's history, record that exact gap and only advance work you can really see.

Do not edit another app's database, state files or stored conversations to read or steer them.

## The run folder

One folder per run. A plain layout is enough:

```text
run-<date>/
  brief.md        the run contract: priorities, finish lines, authority, stop rules
  threads.json    the ledger: one entry per thread (fields in SKILL.md, section 2)
  cursor.txt      where the current cycle is
  pending.md      messages queued and jobs in flight, each with a stable id
  evidence/       copies or links of proof: diffs, check output, readbacks
  review.html     the final private review page
```

Count separately: all known threads, open threads, threads read fresh this cycle, threads you could not open. Reconcile additions, renames and retired scopes instead of starting the ledger over.

If other agents share the machine, use whatever claim or lock system the owner already runs before you edit shared files or take an outside action. Reading needs no claim. Never invent a new lock name to get around someone else's.

## Cycles

A new cycle starts when a reply changes what can be done, when another thread can move, or when a check is due. It does not start because five minutes passed.

No identical "continue" messages. If a queued message never arrived, look at that one session. Do not start a second owner for the same work.

## Recovering a stuck thread

For a badge that says running but shows no progress, check in this order: the job's real state, its last progress line or receipt, the process, the expected output file. Tell apart prepared, started, progressing, stopped and delivered. Recover only the stuck session, through its supported route, and keep its history and pending actions. Do not restart shared apps or other people's workers.

Before a long render or build, check that every input it needs exists and is the agreed version. Do not delete a failing field just to make a validator pass.

## Sign-ins

Use only a login the owner already saved, through an approved password manager integration or a secure entry path. Never dump vault items, clipboard contents, environment variables or tokens. If a secret shows up in output by accident, stop, do not copy it, and report that it happened without the value.

## Usage

Read usage from the provider's own meter, with its labels and reset times. Do not work out a percentage from token counts or a plan name. A meter for one product does not describe another.

## The review page

One private HTML file. Escape all text. No remote scripts, fonts or trackers. Relative links to evidence. For each goal: what was asked, what is true now, the proof state, what is left and who owns it. Include a searchable list of every thread and its final state. Keep private material on the machine; do not upload whole transcripts to an outside judge.

## Closing

Use the owner's closeout routine if they have one (the `finish-work` skill in this repository is one). Release claims on finished work. Hand off unfinished work with its claims and a plain note. A finished review window is not the same as finished products.
