# Skills

Practical, safety-gated AI agent skills from Lennox Saint and Codex Club.

## Save 10%

`save-10-percent` finds recurring expenses that no longer earn their keep. It checks what is actually being used, exposes hidden dependencies, compares cheaper ways to preserve the same outcome, and keeps working until it finds 10% in evidenced net recurring savings—or proves why the honest result is lower.

It can audit personal subscriptions and small-business SaaS, seats, memberships, cloud services, and automations. When the host has safe authenticated browser controls, it can execute an exact approved batch. It never treats a projected recommendation as money already saved.

### What changed in v2

- Credits, refunds, reimbursements, transfers, and income cannot become spend through absolute-value arithmetic.
- Every audit has a hash-chained local case that survives closed chats, restarts, and partial execution.
- A baseline cannot freeze until declared-account scope, duplicate candidates, source coverage, and transfer reconciliation all pass.
- Three months enables preliminary work; 13 calendar months or equivalent annual evidence earns exhaustive status.
- Each vendor is reviewed for real usage, people and workflows affected, required features, terms, and switching cost.
- The 10% calculation uses net 12-month savings after replacement, exit, setup, bundle, and migration costs.
- Browser execution uses an expiring approval, item identity, idempotency, live-state comparison, and risk-tiered confirmation.

## Install

### Codex

Download the latest release ZIP, unzip it, then copy the skill folder:

```bash
cp -R save-10-percent "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Start with:

```text
Use $save-10-percent to audit my recurring costs. Help me collect the right files first, then keep working until you find 10% in safe net savings or prove the shortfall.
```

### Claude and compatible skill clients

Upload the release ZIP through the client’s normal Skills or Capabilities screen. The analytical workflow uses the open skill-folder format. Browser execution activates only when the host proves the controls listed below.

### Requirements

- Python 3.10 or newer for deterministic local scripts.
- No Python packages for CSV, JSON, OFX/QFX, or QIF.
- Optional local `pdftotext` for text PDFs. Install Poppler on macOS with `brew install poppler` or use your operating system’s package manager. Scanned and ambiguous PDFs fail closed to a machine-readable export.

## Prepare the evidence

The skill will build a checklist, but the fastest start is:

1. Export 90 days from every account that pays subscriptions or recurring business costs.
2. Prefer CSV or OFX/QFX. QIF and structured JSON are also supported.
3. Include current provider bills or admin screenshots for your largest services.
4. Name anything that must remain protected.
5. For an exhaustive audit, provide 13 calendar months or equivalent evidence for annual renewals.

Raw statements are read locally and are not copied into the durable case. Do not commit real statements, invoices, credentials, cookies, screenshots, or provider receipts to this repository.

## What happens

```text
Collect sources
    ↓
Prove account and date coverage
    ↓
Reconcile transfers, card payments, refunds, and duplicates
    ↓
Freeze the recurring-cost baseline and exact 10% target
    ↓
Review the highest-value vendor first
    ↓
Check usage, dependencies, plans, terms, and alternatives
    ↓
Calculate net 12-month savings
    ↓
Freeze one expiring approval batch
    ↓
Live preflight → execute or stop the changed item
    ↓
Provider confirmation → effective bill → statement realization
```

If the evidence only supports 7%, the result is 7% plus the exact remaining blockers. The skill does not weaken the denominator or cancel a protected service to manufacture 10%.

## Browser capability matrix

| Host capability | Analysis | Autonomous execution |
|---|---:|---:|
| Local files and Python | Yes | No |
| Read-only financial/provider connectors | Yes | No |
| Authenticated browser without proof capture | Yes | No |
| Authenticated browser, live readback, screenshots, interruptible MFA, durable receipts | Yes | Yes, after approval |

When execution is unavailable, the skill returns the exact page, action, consequence, and receipt checklist for the user to complete.

## Three examples

### Cancel an unused service

The audit finds a voice tool charged monthly. The user confirms nobody uses it, no assets or automations depend on it, and provider billing shows a reversible monthly cancellation. The row enters the low-risk batch. After live preflight, the skill cancels it, captures confirmation, and waits for the affected statement before calling it realized.

### Replace a tool only when the economics work

A project tool costs $80/month and a suitable alternative costs $25/month. The skill subtracts the replacement subscription, setup fee, lost bundle value, and known migration cost. If the net 12-month saving remains positive and required features are preserved, it may recommend switching. If not, it recommends keeping the current tool.

### Keep a costly but valuable service

A cloud service looks expensive. Usage evidence shows it supports a customer workflow and the cheaper tier would break required storage and access. The skill marks it `verified_used`, records why it is protected from this batch, and continues to the next vendor instead of chasing the headline number.

## Proof states

The result separates:

- `candidate`: evidence supports a proposed reduction;
- `approved`: the exact expiring batch is authorized;
- `scheduled`: the provider will change it later;
- `provider_confirmed`: the provider accepted the action;
- `effective`: the lower plan or cancellation is active;
- `statement_realized`: an affected bill or account statement proves the lower recurring cost.

## Recovery and privacy

- Durable cases live under `~/.save10/cases/` by default.
- `events.jsonl` is append-only and hash-chained; `case.json` is rebuilt from it.
- Common secret-like field names and value patterns are rejected; credentials still never belong in case data.
- The skill reads raw inputs in place and retains source hashes rather than complete rows.
- Use `scripts/redact_and_cleanup.py` only after the redacted ledger and receipts exist.
- Closing the chat does not lose case state. Resume by providing the case directory or asking the skill to show the relevant local case.
- A changed or expired approval stops execution; create a new batch instead of editing the old one.

File deletion is not a claim of forensic erasure on modern filesystems.

## Known limits

- No skill can discover an undeclared account or prove use hidden behind inaccessible provider data.
- Text PDF parsing is deliberately strict; scans and unusual statement layouts may require CSV/OFX.
- Provider websites change. Live differences stop the affected action rather than being guessed through.
- MFA, CAPTCHA, passkeys, purchases, annual commitments, permission changes, and irreversible warnings still require the user.
- Statement-realized savings may take a billing cycle after provider confirmation.

## Deterministic pipeline

```bash
work_dir="$(mktemp -d /tmp/save10-demo.XXXXXX)"
python3 save-10-percent/scripts/normalize_transactions.py examples/sample-transactions.csv "$work_dir/normalized.json" --account-id checking --account-type checking
python3 save-10-percent/scripts/reconcile_transactions.py "$work_dir/normalized.json" "$work_dir/reconciled.json"
python3 save-10-percent/scripts/assess_coverage.py "$work_dir/reconciled.json" examples/sample-scope.json "$work_dir/coverage.json"
python3 save-10-percent/scripts/detect_recurring.py "$work_dir/reconciled.json" "$work_dir/recurring.json"
python3 save-10-percent/scripts/build_baseline.py "$work_dir/recurring.json" "$work_dir/coverage.json" "$work_dir/baseline.json"
cat "$work_dir/baseline.json"
```

The synthetic example produces an exhaustive A$70 monthly baseline and A$7 target.

## Development

```bash
python3 -m unittest discover -v -s save-10-percent/scripts -p 'test_*.py'
python3 -m py_compile save-10-percent/scripts/*.py
python3 /path/to/skill-creator/scripts/quick_validate.py save-10-percent
python3 save-10-percent/scripts/build_release.py save-10-percent /tmp/save-10-percent-v2.0.0.zip
```

See [EVALUATION.md](EVALUATION.md) for the release gates and current receipts.

Licensed under MIT.
