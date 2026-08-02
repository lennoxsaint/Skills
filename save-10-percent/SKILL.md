---
name: save-10-percent
description: Audit bank transactions, invoices, SaaS seats, cloud bills, memberships, and verified product usage; normalize controllable recurring expenses; continue researching until at least 10% can be safely saved or the evidence is exhausted; freeze one exact approval batch; and optionally cancel, downgrade, consolidate, renegotiate, or replace only that approved batch with receipts. Use for subscription audits, recurring-cost reduction, duplicate-seat reviews, SaaS or cloud cleanup, monthly expense optimization, and autonomous cancellation requests.
license: MIT
metadata:
  author: Lennox Saint
  version: 1.0.2
  category: finance-operations
  tags:
    - subscriptions
    - cost-optimization
    - automation
---

# Save 10%

Find consequential recurring savings by comparing what is paid with what is actually used. Keep projected, provider-confirmed, and realized savings separate.

## Start with three questions

Ask only what cannot be discovered:

1. Which currency and accounts define the audit?
2. Which services or capabilities are protected?
3. Should raw working data be deleted after the audit? Default to yes.

Then connect available read-only financial, billing, and usage sources. If connectors are unavailable, accept CSV, JSON, OFX/QFX, or QIF exports. Never require a specific bank.

## Contract

- Default scope to controllable recurring expenses: subscriptions, SaaS, cloud, memberships, seats, and recurring services.
- Exclude payroll, tax, transfers, debt, personal purchases, and core cost of goods unless the user opts in.
- Continue until verified projected savings reach 10% or every safe lane is exhausted.
- Never manufacture the missing percentage. Return the honest shortfall and smallest evidence repair.
- Never expose credentials or raw transaction data. Prefer Keychain, environment-secret stores, or authenticated connectors.
- Never cancel, downgrade, purchase, accept an annual contract, or delete data without an exact approved action envelope.

## Workflow

### 1. Normalize spend

Read [data-sources.md](references/data-sources.md). Run `scripts/normalize_transactions.py`, then `scripts/detect_recurring.py` and `scripts/build_baseline.py`. Prefer settled account-currency values. Treat unconverted currencies as a coverage gap, not zero.

Produce a baseline with inclusions, exclusions, coverage, monthly controllable spend, and the exact 10% target. Re-freeze the baseline when a new recurring expense is found.

### 2. Verify usage and consequences

Read [evidence-policy.md](references/evidence-policy.md). Cross-reference provider activity, workspace seats, integrations, invoices, recent workflows, exports, and user confirmation. Ask for browser-history or content access only when necessary and consented.

Classify every item as `verified_used`, `owner_confirmed_unused`, `probable_unused`, `unverified`, or `protected`. Use `scripts/score_usage.py` to merge the evidence.

### 3. Keep searching in this order

1. Cancel unused services.
2. Remove duplicate or inactive seats.
3. Downgrade overpowered tiers or resize usage-based infrastructure.
4. Consolidate overlapping tools.
5. Renegotiate material contracts.
6. Replace a vendor or redesign a workflow when the migration cost and risk are lower than the verified saving.

Use `scripts/optimize_batch.py` to select the lowest-risk batch that clears 10%. Calculate migration time, one-off fees, lost credits, and contract lock-in separately; never disguise them as monthly savings.

### 4. Freeze one action envelope

Read [execution-safety.md](references/execution-safety.md) and [output-contract.md](references/output-contract.md). Every row must state the provider, exact action, current and future monthly cost, verified saving, consequence, recovery path, effective date, and execution gate.

Present the entire batch and ask: **Do you want me to cancel or downgrade the subscriptions in this approved batch?**

If approved, run `scripts/validate_manifest.py --approval ...`. The resulting SHA-256 hash is immutable. Any changed price, warning, consequence, contract, or action requires a new batch and approval.

### 5. Execute safely

Use official APIs or authenticated provider UIs. Pause for login, MFA, CAPTCHA, permission changes, unapproved purchases, materially changed terms, or irreversible data-loss warnings.

Use the nearest cheaper tier only when it is reversible, adequate, month-to-month, and preserves required data. Transfer assets before removing seats. Prove restores before cloud deletion. Shadow replacement workflows before switching writes.

Track `candidate -> approved -> scheduled -> provider_confirmed -> realized`. Count a saving toward the public 10% result only after a provider confirmation and affected billing evidence.

### 6. Delete raw inputs

After redacted ledgers and receipts exist, run `scripts/redact_and_cleanup.py`. Report deletion failures. File deletion is not a claim of forensic erasure on modern filesystems.

## Finish

Return the baseline, approved and executed actions, projected/provider-confirmed/realized savings, remaining shortfall, rollbacks, skipped rows, and a raw-data deletion receipt. Make the next action obvious to a non-technical user.
