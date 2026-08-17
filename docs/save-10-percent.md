# Save 10%

`save-10-percent` finds recurring expenses that no longer earn their keep. It checks actual use and dependencies, compares safer or cheaper ways to preserve the outcome, and keeps working until it finds 10% in evidenced net recurring savings or proves why the honest result is lower.

It is designed for personal subscriptions and small-business SaaS, seats, memberships, cloud services, and automations. It is not for payroll, tax, debt, investment advice, or one-off budgeting.

## Start here

Install the skill, then say:

```text
Use $save-10-percent to audit my recurring costs. Help me collect the right files first, then keep working until you find 10% in safe net savings or prove the shortfall.
```

The skill accepts CSV, JSON, OFX/QFX, QIF, text PDFs, invoices, and read-only billing sources. Python 3.10 or newer is required for the deterministic local scripts. Text PDF support also requires local `pdftotext`; scanned or ambiguous PDFs correctly fall back to a machine-readable export.

## What happens

```text
Collect sources
    ↓
Prove account and date coverage
    ↓
Reconcile transfers, card payments, refunds, and duplicates
    ↓
Freeze the recurring-cost baseline and exact 10% target
    ↓
Review the highest-value vendor first
    ↓
Check usage, dependencies, plans, terms, and alternatives
    ↓
Calculate net 12-month savings
    ↓
Show one exact, expiring approval batch
    ↓
Live preflight → execute or stop the changed item
    ↓
Provider confirmation → effective bill → statement realization
```

If the evidence supports only 7%, the result is 7% plus the exact remaining blockers. The skill does not weaken the denominator or cancel protected services to manufacture 10%.

## Evidence to prepare

1. Export at least 90 continuous days from every account that pays controllable recurring costs.
2. Prefer CSV or OFX/QFX. QIF and structured JSON are also supported.
3. Include current provider bills or admin evidence for the largest services.
4. Name every service or capability that must remain protected.
5. Provide 13 calendar months or equivalent annual-renewal evidence before calling the audit exhaustive.

Raw statements stay local and are not copied into the durable case. Never paste passwords, tokens, cookies, account numbers, or complete statements into chat.

## Execution boundary

Analysis does not authorize cancellation. The skill freezes one exact batch and asks:

> Do you approve this exact batch for execution, subject to live preflight and fresh confirmation for any high-risk or materially changed item?

Autonomous execution requires an authenticated browser, exact account and plan readback, before-and-after proof, interruptible security prompts, and durable receipts. Without those capabilities, the skill produces a guided checklist and reports `not_performed`.

Purchases, annual commitments, deletion, lost access, high-risk actions, ambiguous identity, and material live changes always require fresh item approval.

## Proof states

- `candidate`: evidence supports a proposed reduction.
- `approved`: the exact expiring batch is authorized.
- `scheduled`: the provider will change it later.
- `provider_confirmed`: the provider accepted the action.
- `effective`: the lower plan or cancellation is active.
- `statement_realized`: an affected bill or statement proves the lower recurring cost.

A recommendation is not money saved. A provider confirmation is not yet an affected statement.

## Privacy and recovery

- Durable cases live under `~/.save10/cases/` by default.
- Case events are append-only, hash-chained, and secret-rejecting.
- Raw inputs are read in place; durable artifacts store hashes and redacted evidence.
- Changed or expired approval stops execution rather than silently widening authority.
- A blocked provider does not stop independent approved rows.
- File deletion is not a claim of forensic erasure on modern filesystems.

## Synthetic demo

From the repository root:

```bash
work_dir="$(mktemp -d /tmp/save10-demo.XXXXXX)"
python3 save-10-percent/scripts/normalize_transactions.py examples/save-10-percent/sample-transactions.csv "$work_dir/normalized.json" --account-id checking --account-type checking
python3 save-10-percent/scripts/reconcile_transactions.py "$work_dir/normalized.json" "$work_dir/reconciled.json"
python3 save-10-percent/scripts/assess_coverage.py "$work_dir/reconciled.json" examples/save-10-percent/sample-scope.json "$work_dir/coverage.json"
python3 save-10-percent/scripts/detect_recurring.py "$work_dir/reconciled.json" "$work_dir/recurring.json"
python3 save-10-percent/scripts/build_baseline.py "$work_dir/recurring.json" "$work_dir/coverage.json" "$work_dir/baseline.json"
cat "$work_dir/baseline.json"
```

The synthetic data produces an exhaustive A$70 monthly baseline and an A$7 target.

## Known limits

- No skill can discover an undeclared account or inaccessible usage source.
- Provider websites change; material differences stop the affected action.
- MFA, CAPTCHA, passkeys, purchases, permissions, and irreversible warnings still require the user.
- Statement-realized savings may take a billing cycle after provider confirmation.

Read the installable [SKILL.md](../save-10-percent/SKILL.md) for the exact agent workflow and the [evaluation](../evaluations/save-10-percent.md) for test coverage.
