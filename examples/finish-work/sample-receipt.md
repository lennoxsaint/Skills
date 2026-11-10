# Sample receipts

What the receipt file looks like after the two tasks in [`sample-task.md`](sample-task.md). The times, entry ids and folder names are made up. The shape is what `scripts/log_receipt.py` writes.

The file is `~/.finish-work/log/2026-11-10.md`:

```markdown
# Work receipts 2026-11-10

## 09:04:08 +0000 - completed - Fix slugify leaving a trailing dash

- Entry: `3f9a1c07b2d4`
- Task: slugify-trailing-dash
- Status: completed
- Objective: Fix slugify leaving a trailing dash
- Outcome: slugify now strips dashes from both ends; local fix only, not deployed
- Scope: slugify.py only; deploy.sh not run
- Workspace: ~/projects/acme-blog-tools
- Files changed:
  - slugify.py
- Checks and outcomes:
  - python3 -m unittest: 2 of 4 failed before the fix, 4 of 4 pass after
- Decisions:
  - lstrip -> strip on the slug; the existing tests already covered the case
- Errors and fixes: none recorded
- Next steps:
  - Run ./deploy.sh when ready to ship

<!-- receipt-end 3f9a1c07b2d4 -->

## 09:12:41 +0000 - blocked - Update pricing.md and publish it with ./publish.sh

- Entry: `c81e5d2a9b60`
- Task: acme-pricing-2026-11-10
- Status: blocked
- Objective: Update pricing.md and publish it with ./publish.sh
- Outcome: pricing.md updated locally. Not published: publish.sh exited 1 because ACME_PUBLISH_TOKEN is not set. Nothing is live.
- Scope: In: edit pricing.md, run publish.sh. Out: getting the token.
- Workspace: ~/projects/acme-help-centre
- Files changed:
  - pricing.md
- Checks and outcomes:
  - inspected pricing.md: Solo $9, Team $24, Studio $45
  - ./publish.sh: exit 1, ACME_PUBLISH_TOKEN not set; no PUBLISHED.marker created
- Decisions: none recorded
- Errors and fixes: none recorded
- Next steps:
  - Site owner supplies ACME_PUBLISH_TOKEN, then run ./publish.sh

<!-- receipt-end c81e5d2a9b60 -->
```

Each entry ends with a `receipt-end` line. The helper counts a receipt as written only when the whole entry is there, from the `Entry` line to that last line.

The first entry is `completed` because the fix was the whole request. It still says "not deployed", so nobody reads it as shipped.

The second entry is `blocked`. The edit worked, but the request was "update and publish", and the publish did not happen.
