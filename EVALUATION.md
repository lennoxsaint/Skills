# Save 10% evaluation

## What was tested

### Trigger coverage

`tests/trigger-cases.json` contains six prompts that should trigger the skill and six nearby prompts that should not. It covers direct savings requests, bank-file audits, cloud and seat cleanup, approved cancellation, invoice-only work, payroll tax, one-off travel, and unrelated product work.

This is a review bank for agent-level trigger evaluation, not a claim that a JSON file can prove automatic model routing by itself.

### Deterministic functions

Seven standard-library tests cover:

- monthly and annual recurrence detection;
- transfer exclusion and exact 10% target arithmetic;
- duplicate merchant normalization;
- protected-expense enforcement and honest shortfall reporting;
- stable immutable batch hashes;
- rejection of broken arithmetic and hidden annual commitments; and
- safe handling of unconverted currencies.

Run them with:

```bash
python3 -m unittest -v save-10-percent/scripts/test_save10.py
```

### Synthetic end to end

The included sample transaction file passes through normalize, recurrence detection, and baseline construction without external dependencies. Its expected monthly controllable baseline is A$70 and its exact target is A$7.

### Real-workflow dogfood

The private Lennox version was used to freeze a real recurring-expense action manifest. That run caught two important failure modes before cancellation:

- a community downgrade would have disabled a Pro-only membership automation; and
- a service believed to be unused still had live flows sending customer messages.

No bank records, credentials, provider cookies, private receipts, or account identifiers are included in this repository.

## Baseline comparison

Without the skill, a subscription audit can easily mix guesses with evidence, count projected savings as cash already saved, and let a later execution drift beyond what the user approved.

With the skill, the same workflow has a normalized baseline, explicit coverage gaps, protected capabilities, consequence and recovery fields, a deterministic 10% target, one immutable approval hash, provider receipts, and separate projected, provider-confirmed, and realized totals.

## Known limits

- Provider login, MFA, CAPTCHA, contract, and data-loss gates still require the user.
- A 10% result is impossible when safe opportunities do not add up to 10%; the skill reports the shortfall instead.
- Trigger routing must be evaluated in each host agent because hosts discover and rank skills differently.
- Cancellation is only complete after provider confirmation; realization still requires an affected billing readback.

