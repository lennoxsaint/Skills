# Assembling the crew

Use this at step 6. Felix's heist-movie point is that the best results come from bringing in fields the task doesn't obviously need. His warning matters as much: role-play makes the transcript weirder without improving anything. A crew member is a **method you will actually run**, not a voice you put on.

## How to pick
1. Write the work as verbs (from step 2). "A quarterly review" becomes "getting busy people to believe a story about cause and effect, and to decide under uncertainty, in 30 minutes."
2. For each verb, ask which field does that verb for a living, and what *method* they use.
3. Keep the 2–4 that would change the result. Drop any you can't name a concrete method for.
4. Add one red team (always).
5. Record each one in `flight.json` → `crew`: `{ "field", "method", "changed" }`. Fill in `changed` after the build. If a crew member changed nothing, say so. That's useful to know.

## Verb → field → method
| Verb | Field | Method you actually run |
|---|---|---|
| Hold attention | Film editor | Cut on action and on breath. Remove every frame that doesn't move the story. Check pacing as a timeline of beats per second. |
| Make the payoff land | Motion designer | Time animation to the beat, ease in and out, one focal point per frame. Check legibility at phone size. |
| Make people act | Direct-response copywriter | One reader, one promise, one action. Specificity over adjectives. Reason to act now. Write 10 headlines, keep 1. |
| Be understood in 5 s | Information designer | One message per screen. Hierarchy by size and contrast. Run a 5-second test. |
| Prove a claim | Investigative journalist | Find the primary source, get two independent confirmations, quote exactly, date everything. |
| Find what changed | Statistician / data scientist | Reproduce the official number, segment, test against a held-out period, report effect sizes with uncertainty. |
| Decide under uncertainty | Decision analyst | Options × outcomes × probabilities. Ask what would change the decision. Find the cheapest test. |
| Price it | Pricing strategist | Value metric, willingness-to-pay evidence, anchor and decoy, a price ladder with real triggers. |
| Make it feel premium | Brand designer | Restrained palette, a real type scale, generous space, one distinctive move. Remove decoration that doesn't carry meaning. |
| Make it usable | UX researcher | Watch the task done (or simulate it step by step). Count clicks and hesitations. Fix the first point of confusion. |
| Make it sound right | Audio engineer | Loudness to target (−14 LUFS social, −16 podcast), remove noise and clipping, music ducked under voice. |
| Make it fast | Performance engineer | Profile before optimising, measure p50 and p95, fix the biggest cost first. |
| Make it reliable | SRE / QA | Failure modes, retries, timeouts, idempotency, test the unhappy path. |
| Teach it | Instructional designer | State the outcome, show a worked example, then have the learner try it, with feedback. |
| Grow it | Growth marketer | Map the funnel from raw events, find the step with the biggest absolute loss, run one test there. |
| Retain them | Customer success | Read the last conversations of churned users. Find the moment value was missing. |

## Red team methods (pick at least one)
| Red team | Method |
|---|---|
| Short seller | Write the bear case: why the numbers are smaller than they look, what's hidden, who loses if this goes wrong. Research it; don't just imagine it. |
| Forensic accountant | Tie every number to its source. Look for double counting, mixed time windows, survivorship and currency mixing. |
| Hostile first reader | Read as someone who wants to leave. Mark the first moment you would, the weakest claim and the line that sounds generated. |
| Swipe-away viewer | Watch as a cold viewer and mark the exact second you'd scroll on, and why. |
| Skeptical buyer | List every objection to paying. Check that the work answers each one, in order of how likely it is. |
| QA breaker | Empty states, huge inputs, slow network, double submit, back button, mobile width, screen reader. |
| Adversarial user | Inputs designed to make a skill or agent misfire, over-trigger or exceed its authority. |
| Competitor | Look at the work as the best competitor would and find what they'd copy, and what they'd mock. |

## Helper agents
When parallel work helps (one helper researching raw material while another builds a variant), use helper agents within the person's cap (default at most 2 at once). Give each helper a method, its inputs, its output file and a stop condition. Never give it a persona. Use a cheaper model for read-only or mechanical work. If helpers aren't available, run the methods yourself in sequence.
