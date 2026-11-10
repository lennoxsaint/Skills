# Sample plan

A made-up migration plan for a made-up notes app. Three faults are planted in it on purpose. They are listed at the bottom so you can check what the review catches.

```text
Plan: move Acme Notes from the old database to the new one

1. On Friday at 6 pm, switch the app to read from the new database.
2. Over the weekend, copy the old data across with the export script.
3. On Monday, delete the old database to save hosting cost.
4. Tell customers about the move in the next monthly newsletter.

Success: the app works on Monday morning.
```

Try it with:

```text
Use $adversarial-review on the plan in examples/adversarial-review/sample-plan.md. Use an independent reviewer and a 90/100 bar. Review only. Do not carry the plan out.
```

What to expect:

- A frozen brief and a rubric with weights that add up to 100, set before the first review.
- A saved snapshot of the plan with a SHA-256 manifest, so each verdict is tied to an exact version.
- An independent reviewer in a fresh context, with its real model named and its independence labelled (`different_family` or `same_family_fresh_context`).
- Findings with severity, evidence and a specific fix. Each one is checked, then accepted, rejected with a reason, or marked unresolved.
- A revised plan, a fresh review of the whole new version, and a score history.
- A final report that says what was checked and what was not. A passing score means the plan was reviewed. It does not mean the migration works.

The planted faults:

1. The app reads from the new database before the data is copied there (steps 1 and 2 are in the wrong order).
2. The old database is deleted with no check that the copy is complete and no way back (step 3).
3. "The app works" cannot be tested: there is no count check, no sample check and no rollback trigger.
