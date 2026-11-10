---
name: loop
description: Run a quality loop now. Infer a 100-point rubric, revise a local draft or artifact, score each pass, and stop at 100/100 or blocked_below_100. Use when someone says loop this, make it 100/100, iterate until perfect, improve this draft, thumbnail, video, carousel, post or script, or asks for criteria plus execution in one go.
---

# Loop

Create the criteria, execute the loop now, and report the scorecard.

Use `$hill-climb` instead, when it is installed, for long or high-stakes work that must reach a measured bar: it builds a locked test set from real data and climbs it with fresh sessions and outside judges, where this loop grades itself. When the user only wants a paste-ready prompt to run later, write that prompt and do not run the loop.

## Core Contract

- Infer a task-specific 100-point rubric from the current session, local files, supplied artifacts, and rubrics the project already has.
- Reuse the user's own rubrics when they exist: review checklists, quality gates, style guides and voice rules in the workspace outrank a rubric you invent.
- Literal 100 discipline: success is `100/100`. If that cannot be honestly reached, stop as `blocked_below_100` with exact lost points and why.
- Default cap: 10 loops, or stop earlier after two consecutive no-improvement loops.
- Each loop must produce progress evidence: changed local artifact, new variant, improved score, passing check, clearer blocker, or fresh proof.

## Allowed Work

By default, the agent may inspect and edit local drafts, markdown, specs, scripts, review artifacts, images generated in the current task, captions, thumbnails, video metadata, and local QA packets.

The agent may not send, publish, schedule, deploy, merge, charge, delete, unlock, grant or revoke access, change pricing, mutate production data, or announce anything unless the user explicitly authorized that exact action in the current turn.

Stop on credentials, CAPTCHA, passkey, SMS, OTP, recovery, password, permission, billing, destructive actions, or ambiguous member or customer impact.

## Execution Flow

1. Identify source truth and current artifact.
2. Pick or infer the domain adapter from `references/rubric-adapters.md` in this skill's folder.
3. Create 5-8 weighted criteria totaling exactly 100 points, including hard-veto dimensions.
4. Baseline score the current artifact and name every lost point.
5. Revise the smallest useful surface.
6. Verify with the best available proof: validator, screenshot, rendered preview, transcript, diff, readback, or exact artifact path.
7. Rescore and repeat until `100/100`, 10 loops, two no-improvement loops, or a hard blocker.
8. Clean up failed temporary attempts unless they are useful evidence.

## Scoring Rules

- A hard veto is a criterion that must pass in full. While one fails, the status stays below `score_100`, whatever the other points add up to.
- Do not award points without visible evidence.
- If the task is subjective, convert taste into observable criteria before scoring.
- If a criterion cannot be evaluated from available context, mark its points lost and explain the missing evidence.
- If the same weakness appears twice, change strategy before another iteration.

## Final Output

Always return a scorecard:

- Status: `score_100`, `blocked_below_100`, `needs_approval`, `missing_source`, `unsafe_live_action`, or `credential_blocked`.
- Rubric with weights totaling 100.
- Starting score, per-loop scores, and final score.
- Lost points and exact blockers if below 100.
- Files and artifacts changed.
- Verification run and proof captured.
- Live actions not taken.
- Who scored. This loop is self-scored: the agent that revised the work also graded it. Say so, and name an outside check when the stakes call for one.
