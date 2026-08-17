# Output contract

Keep the durable case local. Produce the artifacts reached by the case. Core scripts deterministically emit source, coverage, baseline, approval, preflight, and case-state files; the host agent assembles vendor-review, execution, and realization artifacts from verified evidence rather than inventing unavailable fields:

- `events.jsonl`: append-only hash-chained case events.
- `case.json`: current state reconstructed from the event log.
- `source-manifest.json`: declared accounts, hashes, formats, periods, parser versions, and row counts.
- `coverage-report.json`: preliminary/exhaustive state, source content hashes, reconciliation hash, periods, gaps, ambiguous directions, duplicates, transfers, currencies, and blockers.
- `baseline.json`: currency, included liabilities, monthly controllable spend, exact 10% target, coverage hash, and baseline hash.
- `vendor-review.json`: liability identity, usage, dependencies, required features, terms, alternatives, switching costs, and decisions.
- `opportunity-ledger.json`: gross and net 12-month savings, risk, consequence, recovery, confidence, and eligibility.
- `frozen-batch.json`: exact actions, evidence and baseline hashes, approval, expiry, idempotency keys, and batch hash.
- `execution-receipts.json`: preflight, before/after proof references, provider confirmation, effective date, failures, and skipped rows.
- `realization-report.md`: projected, provider-confirmed, effective, and statement-realized totals and percentages.
- `data-deletion-receipt.json`: hashes of raw paths removed, failures, and retained redacted artifacts.

Do not include account numbers, tokens, cookies, passwords, private content, raw transaction descriptions, unredacted screenshots, or complete raw rows in shareable artifacts.

The final user summary states:

1. baseline and coverage state;
2. what was kept and why;
3. approved and executed reductions;
4. every savings proof state;
5. remaining shortfall and exact blockers;
6. rollback windows and one obvious next action.
