# Output contract

Produce these redacted artifacts:

- `baseline.json`: currency, monthly controllable spend, 10% target, inclusions, exclusions, and coverage state.
- `opportunity-ledger.json`: merchant, usage state, confidence, evidence references, current/future monthly cost, saving, consequence, recovery path, and eligibility.
- `frozen-batch.json`: exact approved rows, totals, owner approval text, timestamp, and SHA-256 batch hash.
- `execution-receipts.json`: action timestamps, before/after proof, provider confirmation, effective date, and failures.
- `realization-report.md`: projected, provider-confirmed, and realized totals and percentage.
- `data-deletion-receipt.json`: raw paths deleted, failures, and retained redacted artifacts.

Never include raw transaction descriptions, account numbers, tokens, cookies, private content, or unredacted screenshots.

