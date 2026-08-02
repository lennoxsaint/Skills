# Skills

Practical, safety-gated AI agent skills from Lennox Saint and Codex Club.

## Save 10%

`save-10-percent` audits recurring expenses, cross-references them with real usage, keeps researching until it finds at least 10% in verified projected savings or proves the shortfall, and can execute one exact user-approved cancellation or downgrade batch.

It does **not** upload your bank data, guess that an unfamiliar merchant is waste, or count a cancellation as realized before the bill changes.

### Five-minute start

1. Download the latest `save-10-percent-*.zip` from [Releases](https://github.com/lennoxsaint/Skills/releases).
2. Claude users: upload the ZIP in **Settings > Capabilities > Skills**. Codex users: unzip it into the skills directory shown below.
3. Say: `Use $save-10-percent to audit my recurring expenses and find 10% I can safely save.`
4. Connect supported read-only sources or provide a local CSV, JSON, OFX/QFX, or QIF transaction export.
5. Name anything that must be protected. Review the frozen batch; nothing changes until you approve that exact batch.

For Codex:

```bash
cp -R save-10-percent "${CODEX_HOME:-$HOME/.codex}/skills/"
```

For Claude-compatible skill clients, install the same `save-10-percent` directory using that client's normal skill/plugin workflow. The core instructions and scripts use the open skill folder format and Python's standard library.

### What the result looks like

The skill returns one plain-language savings packet:

- your verified monthly recurring-cost baseline and exact 10% target;
- safe recommendations ranked by consequence, confidence, and recovery path;
- one immutable approval batch, so later execution cannot quietly expand scope;
- separate projected, provider-confirmed, and realized savings totals; and
- receipts, rollback instructions, evidence gaps, and a raw-data cleanup receipt.

If a browser login, MFA prompt, CAPTCHA, changed contract, purchase, or data-loss warning appears, the skill stops at that provider and keeps working on the rest.

### Try the deterministic pipeline

```bash
python3 save-10-percent/scripts/normalize_transactions.py examples/sample-transactions.csv /tmp/save10-normalized.json
python3 save-10-percent/scripts/detect_recurring.py /tmp/save10-normalized.json /tmp/save10-recurring.json
python3 save-10-percent/scripts/build_baseline.py /tmp/save10-recurring.json /tmp/save10-baseline.json
cat /tmp/save10-baseline.json
```

The sample data is synthetic. Do not commit real bank exports, credentials, screenshots, cookies, or provider receipts.

### Safety model

- Discovery is read-only by default.
- Raw inputs are ephemeral by default.
- The agent produces a redacted ledger and one immutable batch hash.
- Execution requires approval of that exact batch.
- Login, MFA, CAPTCHA, purchases, permission changes, and destructive warnings still stop for the user.
- If safe opportunities total only 7%, the result is 7% plus an evidence gap—not an invented 10%.

### Development

```bash
python3 -m unittest -v save-10-percent/scripts/test_save10.py
python3 /path/to/skill-creator/scripts/quick_validate.py save-10-percent
```

Licensed under MIT.
