# Work Receipt

Write a receipt for substantive tasks and meaningful checkpoints, including partial and blocked outcomes. Routine chat and unchanged polling need none.

## Where it goes

The first match wins:

1. The work log the project's own instructions name, when they name one. Follow that log's format and skip the helper below.
2. The folder in the `FINISH_WORK_LOG_DIR` environment variable.
3. `~/.finish-work/log/`.

## Write it

Use the helper in this skill's folder, so every entry has the same shape:

```text
python3 <skill-dir>/scripts/log_receipt.py \
  --task-id "<stable id for this task>" \
  --status completed \
  --objective "<what was asked>" \
  --outcome "<what is true now, in plain words>" \
  --scope "<what was in and out of scope>" \
  --file "<changed file>" --file "<another>" \
  --check "<command or inspection>: <result>" \
  --decision "<choice made and why>" \
  --error "<failure and its fix>" \
  --next "<remaining step>"
```

`--status` is one of `completed`, `in_progress`, `waiting`, `blocked`, `cancelled` or `unknown`. `--file`, `--check`, `--decision`, `--error` and `--next` repeat. Only `--status`, `--objective` and `--outcome` are required. Read `--help` if an argument is unfamiliar.

The helper appends one entry to `YYYY-MM-DD.md` in the log folder and prints one line of JSON: `status` (`written`, `skipped` or `failed`), `path` and `entry_id`. It never edits or removes an earlier entry.

## Rules

- Record what happened, not what was planned. A value you do not know is written as `UNKNOWN`.
- Use the actual status, measured against what was asked. Work that stopped early is `blocked`, `waiting` or `in_progress`, never `completed`. A local fix that nobody asked to release is `completed`; say "not released" in the outcome.
- `--error` holds a failure met along the way and what fixed it. A blocker that still stands goes in `--outcome` and `--next`.
- For a release or other outside action, put the target, the tool, the before and after proof and the way back in `--check` lines.
- Never include secrets or raw private source text.
- Read back the printed `path` and `status`. `failed` is an outstanding closeout obligation, not a receipt. Retry a recoverable failure with the same arguments: the helper skips an entry it has already written, so a retry cannot duplicate it.
