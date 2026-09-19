# Email Triage Pro evaluation

Version: 1.0.0

## Review scope

The release was checked for cross-client routing, onboarding, conservative mailbox behavior, feedback learning, scheduling guidance, and public-data safety.

## Acceptance cases

| Case | Expected result |
|---|---|
| ChatGPT with two Gmail accounts | Guides separate Gmail app connections, verifies both accounts, and never substitutes `gog` |
| Claude with one Gmail account | Uses the native Google Workspace connector |
| Claude with several Gmail accounts | Uses explicit-account `gog` routing on a local-capable Claude surface |
| First triage run | Reads narrowly, surfaces priority mail, proposes at most three replies, and makes no mailbox changes |
| Classification correction | Applies one-off feedback now and promotes only explicit or repeated general rules |
| Voice correction | Revises the current draft and stores only distilled reusable style preferences |
| Conflict with archive learning | Protection and surface rules win; uncertainty remains visible |
| Scheduled setup | Asks about 8:00 AM, time zone, usage pool, and model before creating anything |
| Scheduled run | Produces a review-only report and performs no unattended Gmail writes |
| Provider draft | Reports success only after a provider draft ID and readback |

## Evidence

- Repository validator covers catalog registration, frontmatter, references, trigger-bank size, README registration, and local links.
- The skill validator checks the standalone package structure.
- The release builder produces a deterministic ZIP containing only the skill folder.
- The public tree is scanned for credential patterns, private inbox addresses, local user paths, and local state artifacts before publication.

## Limits

Connector availability and write actions vary by plan, workspace, region, model, and administrator policy. OpenAI documents multiple connected accounts as app-dependent; the skill verifies each account rather than assuming Gmail exposes that option. Anthropic documents a single connected Google account, so multi-account Claude runs need local `gog` access. Hosted clients without private persistent state can learn only within the current conversation or a user-approved scheduled-task profile.
