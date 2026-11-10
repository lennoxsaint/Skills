---
name: finish-work
description: Close a substantive task with the right checks for its kind of work, an honest outcome summary and a written receipt. Use when a task is about to be called done, at a meaningful checkpoint, when work stops partial or blocked, or when someone says finish this, close this out, wrap this up, or asks whether it is really done.
---

# Finish Work

Finish the requested outcome, verify its proof, and record the actual result. Follow the project's own verification rules and required checks first. Reuse checks already completed in this task.

Read only the relevant closeout guidance:

- Research, advice or document-only work: [research.md](references/research.md).
- Code or executable configuration changes: [code.md](references/code.md).
- User-visible interface changes: also [ui.md](references/ui.md).
- An authorized release or external change: also [release.md](references/release.md).
- Every substantive closeout or checkpoint: [receipt.md](references/receipt.md).

For overlapping work, use the relevant combination. Do not load every reference by default. A research task does not require code tests; a local code task does not imply deployment.

## Proof

- Match the evidence to the change: inspect the text for a copy-only edit; exercise the real workflow for a behavior change.
- Keep proof states apart. Local, visible, staged, scheduled, published and delivered are different claims. For anything outside this machine, use the provider's or runtime's own readback.
- Review the final diff or artifact for regressions and unmet requirements. Investigate relevant warnings and silent failures.
- After two failed attempts at the same fix, stop patching. Write down what you learned, then retry from a clean brief or change approach from fresh evidence.

Continue through routine authorized fixes until the agreed outcome and relevant checks are complete. If essential access, intent or authority is missing, prepare everything independent of it and name the remaining step. Preserve source truth. A passing check, saved configuration or draft is evidence only for that step.

## Close

Close with the outcome, material verification limits, remaining work if any, and the receipt's real state and path. Keep routine tool details in the receipt. Report complete only when the owned scope and its evidence are finished; name remaining work and unavailable verification honestly.
