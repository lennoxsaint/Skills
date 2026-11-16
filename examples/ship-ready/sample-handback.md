# Sample ship-ready hand-backs

Two made-up endings, to show the shape. The project, the PR, the people and the scores are all invented.

## The ask

> Ship-ready: add CSV export to the reports page.

## The contract

```
Outcome: users can download any report as CSV from the reports page
Audience: account admins on the web app
Go: merge PR #87 into main
Bar: 9
```

## Ready

```
READY: CSV export on the reports page — go = merge PR #87 into main
Council: PASS at 9 · 2 rounds · version 3b8f0d1
  | Seat | R1 | R2 |
  | GPT-6.1 Sol | 7.5 / 8 | 9 / 9 |
  | Claude Opus 5.5 | 7 / 7.5 | 9 / 9.5 |
  | Gemini Pro | 8 / 8 | 9.5 / 9 |
Proof: CI green on #87; ~/scratch/proof/export-desktop.png, export-phone.png; tests in ~/scratch/proof/tests.txt
Decided for you: comma delimiter, UTF-8 with BOM so Excel opens it cleanly; button label "Download CSV"
Left out on purpose: scheduled CSV emails (follow-up)
Risks still open: none
```

## Not ready

```
NOT READY: council tapped out at 9 after 3 rounds
Best version: draft PR #87 at 3b8f0d1, CI green
Open dispute:
  Claude Opus says: exports over 50k rows time out in the browser; should stream from the server.
  Author says: the largest report today is 12k rows (query in proof/rows.txt); streaming is a new feature.
Unblock: say whether 50k-row reports are in scope for this change.
```
