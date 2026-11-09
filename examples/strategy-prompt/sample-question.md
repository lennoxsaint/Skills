# Sample question

A made-up decision for a made-up notes app. Every number is invented for this example.

```text
Acme Notes has 400 paying customers at $12 a month and about 6,000 free users.
Monthly churn on paid is 4%. We have one developer and three months of runway
for one growth bet. Our goal is the most paying customers six months from now.

Option A: add an annual plan at $96 a year (two months free).
Option B: cut the free tier from unlimited notes to 100 notes.
Option C: build a team plan at $30 a month for up to five people.

Which one should we do first?
```

Try it with:

```text
Use $strategy-prompt on the question in examples/strategy-prompt/sample-question.md.
```

What to expect, under six headings:

1. **Options** - the three options, restated plainly.
2. **Steelman** - the best honest case for each one.
3. **Scoring Algorithm** - 5 to 8 criteria with weights that add up to 100%, a 1-10 score for each option on each criterion, and the weighted totals with the sums shown.
4. **Initial Recommendation** - the option the matrix picks.
5. **Double-Check** - bias, edge cases, missing criteria, a math check, and "what would make me wrong about this?"
6. **Final Recommendation** - a clear answer, the reasons tied to the six-month goal, a confidence level, the key assumptions and what to do next.

The scores are the model's judgement, not measurements. The skill says so when the numbers are directional.
