# Durable case and coverage

The case is the execution authority. Chat history is not.

## State

`intake -> scope -> acquire_sources -> coverage -> normalize -> reconcile -> recurring -> vendor_review -> alternative_research -> net_candidates -> freeze_or_shortfall -> approval -> preflight -> execute -> provider_confirmed -> effective -> statement_realized -> cleanup`

Exception states are `blocked`, `failed`, `stopped_material_change`, `expired_approval`, `insufficient_coverage`, and `user_aborted`.

Use `scripts/case_state.py` to create, show, advance, and record the case. Events are append-only, hash-chained, permission-restricted, and replayed into `case.json`. Common secret-like field names and value patterns are rejected; this is a guardrail, not a substitute for never passing sensitive values to the command.

Record:

- phase transitions and exact blocker;
- user protection, usage, dependency, and approval answers;
- artifact paths and hashes;
- provider preflight and proof states;
- failures, retries, and next action.

Do not store raw statements, raw transaction descriptions, credentials, browser cookies, or private screenshots in event payloads.

## Coverage gates

The source declaration lists every account that can pay controllable recurring costs. The coverage report blocks baseline freezing when:

- scope is not confirmed;
- a declared account is absent;
- an account has less than 90 continuous days;
- a material activity gap remains;
- an undeclared account is present;
- an identical-looking transaction without a stable provider ID remains unresolved;
- any transaction direction is ambiguous;
- a cross-account transfer remains unresolved.

`preliminary_pass` supports a qualified working audit. `exhaustive_pass` requires 13 distinct calendar months spanning at least a year, or equivalent annual-renewal evidence.

Changing a source, declaration, parser, currency conversion, protected item, or inclusion decision invalidates the baseline and downstream approval.
