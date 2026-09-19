# Email Triage Pro

Email Triage Pro reviews one or more Gmail inboxes, surfaces the few messages that matter, drafts a small reply queue, and learns from the user's corrections.

It supports:

- ChatGPT through connected Gmail app accounts
- Claude through its native Gmail connector for one Google account
- multi-account Claude runs through the open-source [`gog` CLI](https://github.com/openclaw/gogcli) on a local-capable Claude surface
- local Codex clients through an available Gmail connection or `gog`

## Install

Clone the repository and install the skill into Codex:

```bash
git clone https://github.com/lennoxsaint/Skills.git
cd Skills
python3 scripts/skills.py install email-triage-pro
```

For ChatGPT, Claude, or another client with skill upload, download the Email Triage Pro release ZIP and use that client's skill or plugin installation flow. The archive contains one top-level `email-triage-pro` folder with `SKILL.md` directly inside it. Restart the client if the skill does not appear immediately.

## What happens after installation

On first use, the skill asks for the inboxes to include, time zone, scan window, draft limit, and voice preferences for each account. It then guides the user through the matching Gmail connection and verifies every account with a narrow read.

After a successful dry run, it asks whether the user wants a daily 8:00 AM schedule. It also asks whether to conserve ChatGPT or Claude usage and recommends the smallest eligible model on the other platform. The user chooses the final model.

## What a run returns

- important mail to handle now
- up to three proposed replies by default
- uncertain or protected mail left untouched
- archive candidates, with proposed and provider-verified states kept separate
- the classification and voice rules applied
- a short feedback prompt

The feedback system learns narrow archive, surface, and protection rules. It also learns tone, length, greeting, sign-off, and phrase preferences for replies. One correction stays attached to one message. A reusable rule requires an explicit general instruction or the same correction on at least two distinct examples.

## Safety

The first run and every scheduled run are read-only. The skill never sends email. Interactive archiving requires exact approval or a user-created reusable rule, adds an undo label first, and requires provider readback. Email content is treated as untrusted input.

Private feedback state stays outside this public repository. It contains compact rules, not message bodies or complete drafts. If a host cannot persist private state, the skill says so and returns a feedback capsule for the user to save.

## Try it

```text
Use $email-triage-pro to connect my Gmail accounts, surface the messages that matter, draft up to three replies, and learn from my feedback.
```
