# Ledger and receipt

## Ledger

Keep the ledger in a file outside the artifact paths, for example `council-ledger.md` in a scratch folder, so it survives compaction and never gets committed with the work. Add one row per finding:

```
| id | seat | sev | outcome | evidence |
| G1 | GPT (OpenAI) | blocker | fixed | test_guest_share fails before, passes after |
| N2 | Gemini (Google) | nit | declined | outside intent: retry UI -> follow-up |
| C3 | Claude Opus (Anthropic) | should | not reproduced | ran `npm test auth` 3x, green |
```

Id prefixes: one letter per seat, for example G = GPT, C = Claude, N = Gemini, X = Grok, and A for your own concerns as the author.

Record usage only if the tool returned it. Never guess usage.

## Receipt

This is the receipt the user reads. Keep it to one screen.

```
COUNCIL <PASS|SINGLE-SEAT PASS|TAP OUT|BLOCKED> at <bar> after <n> rounds · version <short sha, or each file's short SHA256>   [waived: <lab>, if the user waived one]

| Seat | R1 | R2 | R3 |
| <GPT model> (high) | 7 / 6 | 9 / 9.5 | |
| <Claude model> (high) | 7.5 / 7 | 9 / 9 | |
| <third-lab model> (high) | 6.5 / 7 | 9.5 / 9 | |
(one column per round; cells: Quality / Owner axis; "no score" when a seat gave none)

Fixed: <n> (<n> blockers, <n> should)   Declined: <n> nits -> follow-ups
Size: <before> -> <after>
Proof: <paths or links: tests, screenshots, rendered files>
Decided for you: <each reversible choice you settled, one line each>
Go: <the one action left for the user, e.g. "merge PR #42", "send the draft to X">
Open: <disputes, 2-3 lines per side, only on TAP OUT>
```

Write each seat's actual model as the provider reported it, not the alias you requested. Write `no score` for a missing score. Never invent one.

## In a PR

Put this section in the PR description:

```markdown
## Council review

Bar 9.5 · PASS after 2 rounds

| Seat | Round 1 | Round 2 |
| --- | --- | --- |
| <GPT model> | 7 / 6 | 9.5 / 9.5 |
| <Claude model> | 7.5 / 7 | 9.5 / 9.5 |
| <third-lab model> | 6.5 / 7 | 9.5 / 9.5 |
```

Edit the PR description. Do not post the receipt as a comment. When there is no PR, the receipt goes in the final reply.
