# Execution safety

Before every provider action:

1. Reopen the live billing surface.
2. Confirm account, plan, price, currency, renewal date, and target.
3. Capture the current state without secrets.
4. Verify exports, ownership transfers, integrations, and recovery paths.
5. Compare the live action with the approved manifest hash.

Stop and re-freeze when the provider changes the price, effective date, data-retention consequence, contract length, or required action.

Never bypass MFA, CAPTCHA, security challenges, cancellation retention offers that materially change the terms, or irreversible deletion warnings. Never buy a replacement or accept an annual commitment without separate approval.

For seat removal, transfer owned assets and test access first. For cloud shutdown, prove a restore before deletion. For workflow replacement, shadow traffic before switching writes, then run a live canary before cancelling the old service.

