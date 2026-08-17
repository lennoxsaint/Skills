# Browser execution safety

Browser autonomy is capability-gated, action-specific, and fail-closed.

## Required host capabilities

Before offering execution, prove:

- authenticated browser or computer controls;
- visible target account, provider, current plan, price, currency, and renewal;
- before/after screenshots or equivalent provider readback;
- safe interruption for login, MFA, CAPTCHA, passkey, and owner prompts;
- durable case and receipt writes;
- no credential values in prompts, commands, screenshots, or artifacts.

Otherwise produce a guided checklist and record execution as `not_performed`.

## Approval

Freeze one batch for 24 hours. Each row binds the liability, account, provider, current and target plan, action, costs, evidence snapshot, baseline hash, risk, consequence, rollback, and idempotency key.

One batch approval covers only reversible low- or medium-risk actions whose live terms still match. Require fresh item approval for:

- purchases or annual commitments;
- permanent deletion or unrecoverable data loss;
- lost member, family, staff, or customer access;
- high-risk or irreversible actions;
- ambiguous account or liability identity;
- materially changed plan, price, term, consequence, or warning.

Record a fresh high-risk confirmation separately from the immutable batch. It must name the liability, bind the exact `batch_hash`, contain the confirmation text and timestamp, and fall between batch approval and expiry. Pass the resulting secret-free JSON map to `scripts/preflight_batch.py --item-confirmations FILE`; a missing, stale, future-dated, or mismatched confirmation stops that row.

## Live preflight

Immediately before each action:

1. Reopen live billing.
2. Verify provider, account, liability, plan, price, currency, renewal, seats, and dependencies.
3. Compare live state with the approved hash.
4. Capture pre-action proof without secrets.
5. Confirm the idempotency key has not completed.

Stop only the affected row on drift. Never substitute a different tier, accept a retention offer, buy a replacement, or widen scope without new approval.

## Execution

Never bypass MFA, CAPTCHA, passkeys, security challenges, permission prompts, or data-loss warnings. Do not remove a seat until assets and ownership are transferred. Do not delete cloud resources until a tested recovery path exists. Shadow replacement workflows and run a live canary before disabling the original.

After acting, capture the provider confirmation and next-bill preview. Record failures and continue independent approved rows.
