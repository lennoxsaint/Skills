# Evidence policy

## Liability and usage

A merchant name is not a subscription identity. Transaction-only merchant groups remain unverified. Bind every execution candidate to an account, currency, recurring transaction set, current plan or contract, and confirmed user or workflow. Two products from the same vendor and account remain separate when a hashed provider liability hint is available; otherwise resolve them in current provider billing before approval.

Use these usage states:

- `protected`: excluded by the user or a verified critical dependency;
- `verified_used`: current activity or workflow evidence exists;
- `owner_confirmed_unused`: the user confirms no required use and no dependency conflicts;
- `underused`: required outcome uses less than the current tier provides;
- `over_tiered`: a cheaper current tier preserves required features;
- `duplicated`: another paid capability already provides the required outcome;
- `replacement_candidate`: a verified alternative can preserve the outcome at lower net cost;
- `research_needed`: identity, usage, terms, or consequence remains unclear;
- `blocked`: the exact missing evidence or access is recorded.

## Evidence tiers

- `high`: current provider billing plus current usage/admin evidence.
- `medium`: settled recurring charge plus user confirmation and verified dependency coverage.
- `low`: cadence, memory, or third-party search without current account proof.

Only high- or medium-confidence rows with confirmed liability identity may enter an execution batch.

Every candidate records:

- evidence source and retrieval date;
- plan, price, currency, renewal, and contract term;
- actual use and dependent people/workflows;
- required features and protected outcomes;
- current and replacement recurring costs;
- exit, setup, bundle, and migration costs;
- consequence, rollback, confidence, and unresolved questions.

Use official provider sources for current pricing and terms. Do not count stale or third-party-only pricing toward the 10% target.

## Proof states

Never collapse:

`candidate -> approved -> scheduled -> provider_confirmed -> effective -> statement_realized`

A provider confirmation is not an affected bill. A bill change is not proof that an unrelated annual renewal has stopped. Keep one-off refunds and credits outside recurring savings.
