# Save 10% v2.0 evaluation

## Release-candidate status

The v2.0 local release candidate passes 37 deterministic and command-line tests, Python compilation, skill-folder validation, a deterministic ZIP build, and a 40-case advisory trigger evaluation.

This evidence supports the local workflow and release package. It does not claim that every bank format, provider website, host router, or live cancellation flow has been observed.

## Anthropic guide cross-check

The package follows the public guidance in *The Complete Guide to Building Skills for Claude*:

- one trigger-rich description with what and when;
- concise imperative workflow in `SKILL.md`;
- one-level progressive-disclosure references;
- explicit ordering, dependencies, validation, stopping rules, recovery, and error handling;
- deterministic scripts for fragile financial and approval logic;
- trigger, functional, integration, safety, persistence, and packaging tests;
- repository-level installation, examples, limitations, and release documentation;
- no README inside the skill folder.

## OpenRouter review and routing receipt

A redacted council using Claude Opus 5, Grok 4.6, Gemini 3.7 Flash, and GPT-5.6 reviewed the v1 design. No raw financial records, credentials, transactions, or private member data were sent. The strongest shared findings became v2 release gates:

- signed transaction direction;
- declared-source coverage before baseline freeze;
- cross-account transfer and card-payment reconciliation;
- durable local state rather than chat memory;
- unique liability identity and live execution preflight;
- net 12-month savings after switching costs;
- honest shortfall instead of a manufactured 10%.

The current description was then classified against 20 intended triggers and 20 nearby non-triggers by `openai/gpt-5.6-luna` through authenticated OpenRouter MCP. It returned 40/40 expected decisions. The aggregate receipt is `tests/trigger-eval-receipt.json`. This is advisory description evidence, not proof of automatic routing in every compatible host.

## Deterministic suite

Run:

```bash
python3 -m unittest discover -v -s save-10-percent/scripts -p 'test_*.py'
```

### Financial correctness

Passing scenarios cover:

- income, refunds, reimbursements, reversals, and ambiguous positive amounts;
- separate debit and credit columns;
- explicit DMY/MDY handling for slash-formatted dates;
- cross-account credit-card payment reconciliation without hiding underlying card spend;
- duplicate rows and duplicate source files;
- same-day legitimate charges with distinct provider IDs remaining intact;
- unresolved duplicate candidates without provider IDs failing closed;
- same merchant on different accounts remaining distinct liabilities;
- same merchant and account remaining separate when provider liability hints differ;
- long all-letter vendor names not being erased as identifiers;
- fortnightly, monthly, and annual cadence arithmetic;
- unconverted currency exclusion;
- replacement, exit, setup, bundle, and migration cost netting;
- protected rows and honest target shortfall.

### Coverage and persistence

Passing scenarios cover:

- missing declared accounts;
- undeclared accounts present in the combined source set;
- ambiguous direction;
- less than 90 days of history and the 13-calendar-month exhaustive boundary;
- material activity gaps;
- preliminary and exhaustive coverage states;
- baseline refusal before coverage passes;
- append-only case replay;
- invalid state transitions;
- tamper detection in the event hash chain;
- rejection of common secret-like case fields and value patterns;
- command-line resume from disk.

### Approval and execution

Passing scenarios cover:

- exact baseline-bound batch hashes;
- 24-hour approval expiry;
- high-risk item confirmation;
- annual-commitment rejection;
- changed price detection during live preflight;
- autonomous-browser denial when any required host capability is missing;
- guided-checklist fallback.

### PDF and packaging

Passing scenarios cover:

- confident text-statement parsing;
- fail-closed ambiguous PDF extraction;
- complete synthetic command-line workflow;
- reproducible A$70 baseline and A$7 target;
- deterministic release ZIP hashes;
- exclusion of caches and files outside the skill folder.

## Baseline comparison

The v1 workflow could interpret a positive amount as spend, delete legitimate long vendor names during normalization, collapse same-day charges, merge distinct vendor liabilities, proceed without a durable case, calculate a baseline without a coverage artifact or protected-list binding, and freeze approval without expiry or live drift comparison.

The v2 workflow fails closed on those paths. It also provides an exact next evidence request instead of lowering confidence invisibly.

## CI gates

Every push and pull request must pass:

1. the complete test suite;
2. Python compilation;
3. frontmatter key validation;
4. all linked-reference checks;
5. at least 20 positive and 20 negative trigger cases;
6. repository secret scanning;
7. deterministic release archive construction.

Tags matching `save-10-percent-v*` rerun tests and compilation before GitHub release creation.

## Known limits and watch-outs

- Actual automatic skill routing varies by host; the JSON bank and OpenRouter classification do not replace host-specific routing tests.
- Text PDF support depends on local `pdftotext`; scans and unusual layouts may fail correctly to CSV/OFX rather than parse.
- Generic browser execution is governed by the host. The skill provides deterministic capability and preflight gates but cannot guarantee a provider has not redesigned its website.
- No live vendor account was changed during repository evaluation.
- Statement realization still requires a future affected bill or account ledger.
- Users must declare all relevant accounts and answer dependency questions honestly; the skill cannot discover inaccessible sources.

These limits must remain visible in the README and final audit output.
