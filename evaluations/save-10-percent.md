# Save 10% v2.0.1 evaluation

## Status

The v2.0.1 release candidate passes 37 skill tests, five repository tests, Python compilation, skill-folder validation, deterministic ZIP construction, and a 40-case advisory trigger evaluation.

This supports the local workflow and release package. It does not claim that every bank format, provider website, host router, or live cancellation flow has been observed.

## Design review

The skill follows the public skill-building guidance:

- one trigger-rich description containing what the skill does and when to use it;
- a concise imperative workflow in `SKILL.md`;
- one-level progressive-disclosure references;
- deterministic scripts for fragile financial and approval logic;
- explicit dependencies, validation, stopping rules, recovery, and error handling;
- trigger, functional, integration, safety, persistence, and packaging tests;
- no user documentation inside the installable skill folder.

A redacted advisory review identified the release gates that now protect transaction direction, account coverage, transfer reconciliation, durable state, liability identity, live preflight, net savings, and honest shortfall reporting. No raw financial records or credentials were sent.

The trigger description was classified against 20 intended triggers and 20 nearby non-triggers. The result was 40/40 expected decisions. See [`tests/save-10-percent/trigger-eval-receipt.json`](../tests/save-10-percent/trigger-eval-receipt.json). This is advisory evidence, not proof of routing in every host.

## Deterministic coverage

Passing scenarios include:

- signed debits, credits, refunds, reimbursements, reversals, and ambiguous direction;
- DMY/MDY handling, OFX identifiers, duplicate files, duplicate candidates, and separate liabilities;
- cross-account card-payment reconciliation without hiding underlying spend;
- fortnightly, monthly, and annual cadence arithmetic;
- foreign-currency exclusion and switching-cost netting;
- preliminary and exhaustive coverage boundaries;
- missing or undeclared accounts and material date gaps;
- append-only case replay, tamper detection, and secret-like field rejection;
- baseline-bound batch hashes, 24-hour expiry, live drift, high-risk confirmation, and idempotency;
- safe denial of autonomous execution when required host capabilities are missing;
- text-PDF confidence gates and deterministic release ZIP contents.

Run:

```bash
python3 scripts/skills.py validate
python3 -m unittest discover -v -s tests -p 'test_*.py'
python3 -m unittest discover -v -s save-10-percent/scripts -p 'test_*.py'
python3 scripts/build_skill_release.py save-10-percent /tmp/save-10-percent.zip
```

## Known limits

- Automatic skill routing varies by host.
- Text PDF support depends on local `pdftotext`; scans may require CSV or OFX.
- Browser execution depends on host capabilities and current provider UI.
- No live vendor account was changed during repository evaluation.
- Statement realization requires a future affected bill or account ledger.
- Users must declare all relevant accounts and answer dependency questions honestly.
