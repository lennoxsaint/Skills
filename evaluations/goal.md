# Goal evaluation

Version: 1.0.0

## Review scope

The release was checked for Codex packet creation, collision-safe paths, owner and agent file ownership, steering precedence, native Goal Mode boundaries, Claude prompt mode, live-action gates, and deterministic packaging.

## Acceptance cases

| Case | Expected result |
|---|---|
| Codex plan in a Git repository | Resolves the Git root and creates one unique packet under `.codex/goals/` |
| Workspace path with spaces | Returns correctly quoted absolute paths in the launcher |
| Repeated goal title | Reserves a new suffixed packet without overwriting the first |
| Missing plan | Asks only for the plan, specification, or task list |
| Owner steering during execution | Active thread wins; accepted steering is recorded in `progress.md` |
| Edited `goal.md` | Re-reads the contract, records its new SHA-256, and adjusts the next checkpoint |
| Three repeated failures | Inspects fresh state and changes strategy before stopping with the exact blocker |
| Live publishing in the plan | Prepares safely and acts only when the plan authorizes the exact public action |
| Claude destination | Returns one `/goal` prompt no longer than 4,000 characters and creates no Codex packet |
| Packet quality check | Leaves no unresolved template tokens and keeps goal and progress files together |

## Evidence

- `scripts/validate_goal_skill.py` checks the contract language, both templates, slug behavior, collision handling, and the 64-character cap.
- Repository validation checks catalog registration, frontmatter, UI metadata, public links, trigger-bank coverage, and Python syntax.
- Repository tests install the skill into a temporary directory and run its standalone validator from the installed copy.
- The release builder creates a deterministic ZIP containing only the `goal` skill folder.

## Limits

The skill can define and package a goal, but it cannot prove that native Goal Mode started. Host support for Goal Mode, pause, resume, and status controls varies. The executor must still verify live outcomes through the real provider or runtime; a local checkpoint is not delivery proof.
