---
name: goal
description: Generate durable Codex goal packets or optimized Claude /goal prompts from user-provided plans, specs, or task lists. Use when someone asks to turn a plan into a /goal prompt, create a steerable autonomous execution goal, optimize a goal prompt, or write a goal contract for implementation.
---

# Goal

Turn a user-provided plan into one bounded, verifiable goal.

- For Codex, create a durable goal packet and return its paste-ready `/goal` launcher.
- For Claude, return one paste-ready `/goal` prompt no longer than 4,000 characters.
- Return notes only when the user explicitly asks for rationale, alternatives, or critique.

## Core contract

- Preserve the user's strategy, requirements, constraints, names, paths, dates, prices, gates, and stop rules.
- Do not redesign the plan or reopen decisions unless a requirement is impossible or dangerously unclear.
- If no plan, spec, or task list is provided, ask the user to paste the plan. Ask only that.
- If a plan is provided, do not interview unless a critical blocker would make the goal unsafe or impossible.
- Keep one goal to one bounded outcome. Route recurring or time-triggered routines to a scheduling or loop skill when one is available.
- Resolve Codex versus Claude from the request or destination. Ask only when the platform is genuinely ambiguous and changes the result.
- Prefer the shortest contract that preserves every execution-relevant fact.
- Reference accessible source files by exact path and reading order instead of duplicating them. Inline anything the executor cannot retrieve.

## Codex goal packet

For Codex, treat native Goal Mode as the lifecycle authority. The packet is the durable contract and progress surface; it does not replace `/goal` status, pause, resume, or clear controls.

Store each packet at `.codex/goals/<goal-slug>/` inside the resolved workspace root.
Treat packets as local runtime artifacts. Do not edit `.gitignore`, stage, or commit them unless the user explicitly asks.

### Create the packet

1. Resolve the workspace root to the Git root when one exists; otherwise use the current working directory.
2. Write a short goal title with no more than eight meaningful words.
3. Reserve a unique packet directory with:

   ```bash
   python3 "<skill-root>/scripts/goal_slug.py" --workspace-root "<workspace-root>" --title "<goal-title>" --reserve
   ```

4. Use the exact `packet_dir`, `goal_path`, `progress_path`, and `goal_slug` returned as JSON. The helper normalizes lowercase ASCII slugs, keeps the final suffixed slug within 64 characters, and reserves collisions without overwriting an existing packet.
5. Read `assets/goal.md.template`, fill every token, and save the final `goal.md`.
6. Compute the SHA-256 of that saved file.
7. Read `assets/progress.md.template`, fill every token including the saved goal hash, and save `progress.md`.
8. Confirm neither saved file contains a `{{...}}` template token.
9. Use absolute paths in the launcher. Quote paths containing spaces.

### Ownership and steering

- `goal.md` is owner-editable source truth for the outcome, constraints, permissions, exit criteria, and steering notes.
- `progress.md` is Codex-owned runtime state. Codex updates it after every meaningful checkpoint and before stopping.
- Never rewrite owner-controlled sections of `goal.md` while executing. If a user gives steering in the active thread, follow it immediately and record the accepted decision in `progress.md`.
- Use this authority order:
  1. latest explicit instruction in the active thread
  2. current `goal.md`
  3. `progress.md`
- Re-read `goal.md` before each checkpoint, after resume or compaction, and before every live, irreversible, or externally visible action.
- Record the SHA-256 of the last-read `goal.md` in `progress.md`. When it changes, summarize the steering absorbed and adjust the next checkpoint before continuing.
- Do not claim that editing the file interrupts a tool call already in flight. File steering takes effect at the next re-read.

### Return the launcher

After creating the packet, return:

1. A clickable link to `goal.md`.
2. A copyable launcher in this shape:

```text
/goal Execute the goal contract at "<absolute-path>/goal.md". Treat native /goal as the lifecycle authority. Re-read goal.md before every checkpoint, after resume or compaction, and before live or irreversible actions. Maintain "<absolute-path>/progress.md" after every meaningful checkpoint, including the current checkpoint, verified evidence, remaining work, blockers, accepted steering, and the SHA-256 of the last-read goal.md. Continue until the contract's exit criteria are proven or a hard blocker requires the owner.
```

Do not start the goal unless the user explicitly asks to start it. Creating the packet and launcher does not itself prove Goal Mode is active.

## Goal contract standard

Write `goal.md` as a concise operational brief:

1. Outcome
2. Workspace and source truth
3. Success and loop criteria
4. Autonomy
5. Hard stop rules
6. Required work
7. Verification
8. Steering notes
9. Final report

Apply these rules:

- Define verifiable success criteria that Codex can evaluate after any turn.
- Prefer numbers, thresholds, parity targets, checklists, named artifacts, or pass/fail checks when supported by the source plan.
- Include known starting points, suspect areas, allowed tools, and acceptable limitations.
- Define what Codex must inspect, change, verify, and decide at each checkpoint.
- Require fresh progress evidence before continuing claims: changed files, passing checks, improved metrics, captured proof, or exact blocker text.
- After the same symptom or error repeats three times, inspect fresh state and change strategy. Stop with the exact blocker if the changed strategy still cannot progress.
- For indefinite-seeming work, include a turn, time, or checkpoint cap.
- For visual work, use feature checks, specs, design-system adherence, screenshots, or visual diffs instead of "pixel perfect" alone.
- Before completion, require cleanup and review of failed attempts, temporary tools, dead code, reduced coverage, and leftover artifacts.
- Keep proof evaluator-visible. Separate draft, local, staged, runtime-verified, delivered, and live/public states.

## Live-action gates

When the plan touches live systems, member data, payments, publishing, messages, calendar events, GitHub, production apps, or public copy:

- Codex may inspect, draft, stage, screenshot, validate, and prepare.
- Codex may submit, send, publish, delete, charge, change access or pricing, deploy, merge, announce, or write production data only when the plan explicitly authorizes that exact action.
- If authorization is unclear, stop with the exact prepared output and ask for approval.
- If credentials, CAPTCHA, passkey, SMS, OTP, recovery, password, or security prompts appear, stop and report the blocker.

## Claude mode

For Claude, keep the prompt-only behavior:

- Begin with `/goal`.
- Use the user's plan as source truth.
- Include outcome, sources, success and loop criteria, autonomy, hard stops, required work, verification, and final report.
- Preserve live-action gates and proof-state distinctions.
- Keep the complete prompt at 4,000 characters or fewer, including headings and whitespace.
- Return only the prompt unless the user asks for notes.

## Quality check

Before returning:

- Confirm the goal is bounded and its stopping condition is objectively testable.
- Confirm every source requirement, permission boundary, blocker, and proof obligation survives.
- Confirm looped work says when to continue, change strategy, or stop.
- Confirm the goal packet contains no unresolved template tokens.
- Confirm `goal.md` and `progress.md` are in the same uniquely reserved packet directory.
- Confirm the launcher uses the exact absolute paths and does not imply Goal Mode is already active.
- Confirm `progress.md` is agent-owned and `goal.md` remains owner-editable.
- Confirm Claude output stays within 4,000 characters.
- Confirm no live action is authorized by implication.
