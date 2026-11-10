---
name: strategy-prompt
description: Make a rigorous recommendation on a business, strategy, research or decision question. Steelman every option, score them in a weighted matrix, give a first recommendation, check it for bias and blind spots, ask what would make it wrong, then give a final recommendation tied to the user's goals. Use when someone says strategy prompt, steelman both sides, score the options, compare these strategic choices, or asks for a rigorous business recommendation.
---

# Strategy Prompt

Use this skill when the user asks to apply the Strategy Prompt, steelman both sides, score options, compare strategic choices, or make a rigorous business recommendation.

## Workflow

1. Gather the user's own context first when a retrieval tool is available: their notes, saved reading, past decisions and numbers on the topic. Open the Options section with one line on what you found and what you could not reach.
2. Define the options being compared. If the user gives only one option, create the strongest realistic alternatives.
3. Steelman every option in good faith.
4. Create 5-8 decision criteria relevant to the user's stated objective.
5. Weight criteria so the total is exactly 100%.
6. Score each option from 1-10 on every criterion. 10 is always best for the user, so low effort and low risk score high.
7. Show the weighted scoring matrix and calculations.
8. Provide the initial recommendation based on the matrix.
9. Double-check the analysis:
   - bias or blind spots
   - edge cases
   - missing criteria
   - math check
   - "What would make me wrong about this?"
10. Present the final recommendation:
   - clear answer
   - rationale tied to the user's business goals
   - strategic implications
   - confidence level
   - key assumptions
   - follow-up actions or contingencies

## Rules

- Do not invent precision. If numbers are directional, say so.
- The final recommendation may differ from the initial one. When the double-check changes a weight or a score, show the new totals beside the old ones and say what changed your mind.
- Keep the matrix readable; prefer fewer, sharper criteria over a fake spreadsheet epic.
- If the decision is high-stakes or the evidence is contested, recommend a second opinion from a different model after this pass, and say which scores are most open to dispute.
- If current facts matter, look them up from live sources after reading the user's own context.

## Output Headings

- Options
- Steelman
- Scoring Algorithm
- Initial Recommendation
- Double-Check
- Final Recommendation
