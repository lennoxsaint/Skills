# Evidence policy

## Confidence

- `high`: current provider billing plus current usage/admin evidence.
- `medium`: settled recurring charge plus owner confirmation or indirect usage evidence.
- `low`: merchant cadence or search evidence without current account proof.

Only high- or medium-confidence rows may enter an execution batch. Low-confidence rows remain research leads.

## Usage states

- `verified_used`: recent provider, workflow, seat, or local-use proof exists.
- `owner_confirmed_unused`: Lennox explicitly says it is unused and no current dependency is found.
- `probable_unused`: no recent activity is visible, but dependency coverage is incomplete.
- `unverified`: evidence conflicts or is missing.
- `protected`: excluded by owner instruction or business-critical dependency.

## Proof states

Never collapse these states:

`candidate -> approved -> scheduled -> provider_confirmed -> realized`

Use `realized` only after a bill, account statement, or provider ledger demonstrates the lower recurring charge. Keep one-off refunds and credits out of recurring savings.

