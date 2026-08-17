# Data sources and adapters

Use the narrowest local or read-only source that can prove the decision.

## Acquisition order

1. Reuse an authenticated read-only connector or official API exposed by the host.
2. Request CSV or OFX/QFX for transaction history.
3. Accept QIF or structured JSON when those are the available exports.
4. Accept a text-based PDF only through the local confidence gate.
5. Request current invoices, admin billing, and usage exports for candidate providers.

Never require a particular bank. Never ask the user to paste a token, password, cookie, account number, or complete statement into chat. Store connector credentials in the host credential vault and keep them out of case artifacts.

## Adapter contract

Every source follows:

`detect -> extract -> normalize -> coverage report`

Record the content hash, parser version, account alias, date order, period, row counts, quarantined rows, and confidence. Do not copy raw source data into the durable case. Ask for `DMY` or `MDY` when slash-formatted dates are ambiguous; never infer silently from one ambiguous row.

Preserve a provider transaction ID such as OFX `FITID` when available, but store only its hash. Auto-deduplicate only matching stable provider IDs or whole duplicate source files. Retain identical-looking rows without IDs as unresolved duplicate candidates; never delete them merely because date, merchant, and amount match.

When an export contains a provider subscription, contract, plan, or liability identifier, store only its hash and use it to separate recurring liabilities. Otherwise mark the merchant/account group `merchant_group_unverified`; provider billing or equivalent evidence must confirm the exact subscription before execution.

Supported deterministic transaction formats:

- CSV with a signed amount, explicit type, or separate debit/credit columns;
- JSON containing transaction objects;
- OFX/QFX with transaction type and signed amount;
- QIF with signed amounts;
- text PDF when local `pdftotext` extraction produces at least 95% confidence.

Scanned PDFs, password-protected PDFs, ambiguous columns, positive unsigned amounts, and low-confidence extraction fail closed. Explain how to obtain CSV/OFX/QIF/JSON instead.

## Coverage

Declare every personal or business account that can pay recurring costs. Treat settlement currency as authoritative. Record foreign currency as a coverage gap until a timestamped conversion is supplied.

Start preliminary analysis after 90 continuous days for every declared account. Require 13 distinct calendar months spanning at least a year, or equivalent annual-provider evidence, before declaring the audit exhaustive. Unexpected undeclared accounts and unresolved duplicate candidates block the baseline just like missing accounts do.
