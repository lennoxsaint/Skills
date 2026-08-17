---
name: save-10-percent
description: Audit personal and small-business recurring costs from CSV, JSON, OFX/QFX, QIF, text PDF, invoices, or read-only billing sources; verify actual use and dependencies; compare cheaper alternatives; persist until at least 10% in net recurring savings is evidenced or every safe lane is exhausted; and optionally execute an exact approved cancellation or downgrade batch with live browser preflight and receipts. Use for subscription audits, SaaS or cloud cleanup, inactive seats, memberships, recurring expense reduction, plan downgrades, tool consolidation, or autonomous cancellation requests. Do not use for payroll, tax, debt, investment advice, or one-off budgeting.
---

# Save 10%

Find recurring savings without goal-hacking the denominator. Keep analysis, approval, provider confirmation, effective billing, and statement realization separate.

## Critical rules

- Keep raw financial records and credentials local. Never paste them into hosted model calls, logs, receipts, or public artifacts.
- Treat transaction direction, source coverage, liability identity, usage, dependencies, and net savings as gates—not suggestions.
- Never use absolute-value amount handling. Quarantine ambiguous credits and debits.
- Never call an audit exhaustive without 13 calendar months or equivalent annual-renewal evidence.
- Never manufacture 10%. Finish with the honest shortfall and exact blockers when safe opportunities are exhausted.
- Never execute from conversation memory. Use the durable case, frozen batch, unexpired approval, and live preflight.
- Continue independent lanes when one provider is blocked. Stop only the affected row for missing evidence, login, MFA, CAPTCHA, changed terms, purchase, permission, ambiguity, or data-loss risk.

## 1. Create or resume the case

Read [case-and-coverage.md](references/case-and-coverage.md). Resume the user-named case if one exists; otherwise create one:

```bash
python3 scripts/case_state.py create --currency AUD --protected "Required service"
```

Record every completed phase, user answer, artifact hash, approval, error, and provider result. Do not store passwords, tokens, cookies, raw statements, or raw transaction descriptions in case events.

## 2. Acquire sufficient sources

Read [data-sources.md](references/data-sources.md). Ask only for information that cannot be discovered safely:

1. home currency and accounts included in the recurring-cost audit;
2. protected services or capabilities;
3. whether raw inputs should be deleted after redacted artifacts exist; default to yes.

Use an already authenticated read-only connector when available. Otherwise guide the user to export CSV, OFX/QFX, QIF, JSON, or a text PDF. Do not require one bank or connector.

Normalize each account separately, combine sources, reconcile transfers, and run the coverage gate:

```bash
python3 scripts/normalize_transactions.py INPUT OUTPUT --account-id ID --account-type TYPE --currency AUD --date-order DMY
python3 scripts/combine_sources.py NORMALIZED... --output COMBINED
python3 scripts/reconcile_transactions.py COMBINED RECONCILED
python3 scripts/assess_coverage.py RECONCILED SCOPE_DECLARATION COVERAGE
```

Resolve every missing declared account, duplicate source, ambiguous direction, cross-account transfer, material gap, and unconverted currency before freezing a baseline.

## 3. Freeze the baseline

Run recurring detection and baseline construction only after coverage passes:

```bash
python3 scripts/detect_recurring.py RECONCILED RECURRING
python3 scripts/build_baseline.py RECURRING COVERAGE BASELINE --currency AUD --protected-services CASE_JSON
```

Treat 90 continuous days across every declared account as preliminary coverage. Require 13 distinct calendar months spanning at least a year, or equivalent annual-renewal evidence, for exhaustive coverage. A changed source, protected list, currency conversion, parser, or inclusion set invalidates the baseline hash.

## 4. Interrogate real value in planning state

Read [vendor-review.md](references/vendor-review.md) and [evidence-policy.md](references/evidence-policy.md). Stay read-only through this phase.

Review the highest-value liability first. Present one vendor card at a time with three to five grouped questions covering:

- who uses it, for what outcome, and how recently;
- seats, data, automations, clients, family members, or workflows that depend on it;
- genuinely required features;
- contract, renewal, notice, promotion, bundle, and retention conditions;
- whether cancellation, pause, downgrade, consolidation, negotiation, or replacement preserves the outcome.

Challenge weak “I might need it” answers with evidence, but do not override the user's protection or dependency decisions.

## 5. Research alternatives and keep searching

Use current official provider pricing, plan limits, cancellation terms, data-retention rules, and documented feature differences. Prefer primary sources. Record source, retrieval date, price, term, confidence, and unresolved questions.

Calculate:

`net 12-month saving = gross reduction - replacement cost - exit fees - setup cost - lost bundle value - known migration cost`

Keep migration hours separate unless the user supplies a value of time. Search in this order:

1. unused cancellations;
2. inactive or duplicate seats;
3. adequate cheaper tiers;
4. cloud and usage-based resizing;
5. overlapping-tool consolidation;
6. pauses and billing-cycle changes;
7. renegotiation or retention;
8. workflow redesign or vendor replacement.

Continue until net candidates reach 10% of the frozen baseline or every liability is reviewed and the remaining rows are protected, uneconomic, insufficiently evidenced, or blocked by a named requirement.

## 6. Freeze one approval envelope

Read [execution-safety.md](references/execution-safety.md) and [output-contract.md](references/output-contract.md). Every action row must bind the unique liability, account, provider, exact action, current and target plan, costs, evidence snapshot, consequence, recovery, risk, and execution gate.

Present the whole batch and ask exactly:

**Do you approve this exact batch for execution, subject to live preflight and fresh confirmation for any high-risk or materially changed item?**

After approval, create the immutable 24-hour batch:

```bash
python3 scripts/validate_manifest.py CANDIDATE FROZEN --approval "EXACT USER APPROVAL"
```

Any changed row, source, consequence, risk, price, plan, or baseline requires a new batch.

## 7. Execute only when the host proves capability

Require authenticated browser/computer controls, target-account readback, before/after proof, interruptible security prompts, and receipt capture. Record those booleans and run `scripts/assess_execution_capabilities.py`. If any capability is absent, provide the exact guided checklist instead of claiming autonomous execution.

Immediately before each action, compare live state with the approved row using `scripts/preflight_batch.py`. Low-risk reversible rows may use the batch approval. Require fresh item approval for purchases, annual commitments, deletion, lost access, irreversible actions, ambiguous identity, or material drift.

Never bypass MFA, CAPTCHA, passkeys, permission prompts, retention terms, or data-loss warnings. Never improvise a different plan. Use each idempotency key once.

## 8. Prove and clean up

Track:

`candidate -> approved -> scheduled -> provider_confirmed -> effective -> statement_realized`

Do not call projected savings “saved.” Do not call provider confirmation “statement realized.” After redacted outputs and receipts exist, run `scripts/redact_and_cleanup.py` on the user-approved raw paths and report any deletion failure.

Finish with the baseline, coverage state, vendor decisions, approved and executed rows, projected/provider-confirmed/effective/statement-realized totals, shortfall, blockers, rollbacks, and one obvious next action.
