# Sample council run

A made-up run, to show the shape. The project, the commits, the findings and the scores are all invented. The model names stand in for whatever is newest when you run it.

## The ask

> Council 9 on PR #42: the fix for guest share links that 404 after login.

## The ledger

Kept in `~/scratch/council-ledger.md`, outside the repo, never committed.

```
| id | seat | sev | outcome | evidence |
| G1 | GPT (OpenAI) | should | fixed | test_guest_share_after_login fails before, passes after |
| C1 | Claude Opus (Anthropic) | should | fixed (merged w/ G1) | same root cause: redirect drops ?share= |
| N1 | Gemini (Google) | nit | declined | retry button styling predates the PR -> follow-up |
| C2 | Claude Opus (Anthropic) | blocker | not reproduced | claimed token leak in logs; ran `npm test auth` 3x and grep'd logs, no token |
| A1 | author | should | fixed | my own concern: no test for an expired share link; added one |
```

## The receipt

```
COUNCIL PASS at 9 after 2 rounds · version 7c1e9a2

| Seat | R1 | R2 |
| GPT-6.1 Sol (high) | 7 / 7.5 | 9 / 9 |
| Claude Opus 5.5 (high) | 6.5 / 7 | 9.5 / 9 |
| Gemini Pro (high) | 8 / 8 | 9 / 9.5 |
(cells: Quality / Owner axis)

Fixed: 2 (0 blockers, 2 should)   Declined: 1 nit -> follow-ups
Size: 64 lines -> 81 lines
Proof: test output in ~/scratch/proof/tests.txt, screen recording ~/scratch/proof/share-link.mov
Decided for you: kept the ?share= param name rather than renaming it to ?s=
Go: merge PR #42
```

## In the PR description

```markdown
## Council review

Bar 9 · PASS after 2 rounds

| Seat | Round 1 | Round 2 |
| --- | --- | --- |
| GPT-6.1 Sol | 7 / 7.5 | 9 / 9 |
| Claude Opus 5.5 | 6.5 / 7 | 9.5 / 9 |
| Gemini Pro | 8 / 8 | 9 / 9.5 |
```
