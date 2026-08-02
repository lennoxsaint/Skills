# Data sources

Use the narrowest available source that can prove the decision.

1. Settled bank or card transactions for merchant, amount, currency, and cadence.
2. Current provider billing for price, tier, renewal, and cancellation terms.
3. Admin consoles for seats, usage, integrations, owned assets, and export paths.
4. Local application history or logs when they prove actual use without exposing private content.
5. Owner confirmation for intent and protected services; do not use it to fabricate pricing or provider state.

Store tokens in the operating system's credential vault with a provider-specific service name. Retrieve them only inside the command that calls the provider. Never print the token. Prefer read-only API scopes for discovery.

Accepted transaction inputs are CSV, JSON, OFX, and QIF. If a PDF statement is the only source, extract it to a temporary local table, inspect the extraction, and delete both raw and intermediate files after the ledger is complete.

Prefer the bank's settled AUD amount. If only a foreign-currency price exists, record the exchange-rate source and timestamp and mark the result estimated.
