# Instruments by task type

Use this at step 5 (depth brief). For each kind of work it lists what the top professional does, the rawest material they start from, the instruments they reach for, what counts as outside proof, and where the money moment usually sits. These are starting points, not a checklist. Pick what changes the result. If the person's profile (`$AMBITIOUS_HOME/profile.md`) lists local instruments, those come first.

A note on "instruments": the test is whether the tool changes what you can *see* or *prove*. A markdown table doesn't. A query re-run against the raw rows does.

## Contents
- Video and motion
- Sales pages, landing pages and web design
- Writing: articles, posts, emails, scripts
- Money hunts: growth, revenue, pricing, retention
- Data analysis and decisions
- Code and product features
- Skills, prompts, agents and pipelines (reusable automation)
- Decks and presentations
- Strategy and research

---

## Video and motion
**Verbs:** stop the scroll, make a claim believable, hold attention, make the ask feel earned.
**Top-pro move:** cut from the raw footage and a word-level transcript. Build the story around the one strongest proof moment. Design the last 5 seconds (the CTA) first, then make every earlier beat earn it. Watch the result frame by frame, with sound and without.
**Rawest material:** original camera files and audio (not proxies or prior cuts), the word-level transcript, the product's live page or app for the real offer, past videos' retention graphs if any exist.
**Instruments:** `ffprobe` (streams, duration, fps), `ffmpeg` (frame-accurate cuts, `loudnorm` to −14 LUFS for social, burned captions), whisper word timestamps, a contact sheet (`ffmpeg ... tile`), Remotion or HyperFrames for designed motion, frame exports at each cut for checking.
**Outside proof:** the script or storyboard judged before rendering (concept faults are the costly ones), then a contact sheet + transcript + loudness and duration report judged blind by a different model. Every on-screen proof must come from the workflow the video claims; if it doesn't, change the claim or get the right footage. The hook at 0–2 s and the CTA in the last 5 s are checked as frames. Played start to finish once (watching, not skimming).
**Money moment:** the CTA. The viewer should know exactly what to do, why now, and that the claim was proven earlier in the video.
**Red team:** the swipe-away test, which marks the first second a cold viewer would leave and why.

## Sales pages, landing pages and web design
**Verbs:** make a stranger understand in five seconds, make them believe, remove every reason to hesitate, make buying feel obvious.
**Top-pro move:** start from the buyer's own words (reviews, support tickets, recorded calls, DMs). Write the offer and the objection list before any layout. Show the product doing the job (real screenshots or a live demo loop) instead of describing it. Design the buy section first.
**Rawest material:** the real product (run it, screenshot it), real pricing and its rules, customer language, competitors' live pages, analytics for the current page if one exists.
**Instruments:** a real browser render at 390 px and 1440 px (Playwright or headless Chrome screenshots), Lighthouse for performance and accessibility, axe for contrast, a type scale and spacing system rather than ad hoc values, real assets over stock.
**Outside proof:** screenshots at both widths judged blind, a five-second test (the judge sees the first screen only and states what the product is and who it's for), the Lighthouse scores, every claim traced to the product or a source.
**Money moment:** the buy button and the price beside it, including what makes now the right time (scarcity only if it's real).
**Red team:** the skeptical buyer, who lists every objection they would raise and checks the page answers each one.

## Writing: articles, posts, emails, scripts
**Verbs:** earn the first line, make one idea land, prove it with a receipt, make the reader act.
**Top-pro move:** report before writing. Find the primary sources, the exact numbers and dates, and the one story that carries the idea. Write long, then cut by a third. Read it aloud.
**Rawest material:** primary sources (transcripts, logs, receipts, the raw data), the author's own past writing that worked, the audience's words.
**Instruments:** a fact sheet with a source for every claim, the author's voice guide and best past examples, a humanizer pass for AI patterns, a readability check, a channel-specific checker (length, link rules).
**Outside proof:** a blind judge who reads the piece as the target reader and marks where attention drops and which claims feel unproven, plus a fact check against the fact sheet.
**Money moment:** the one action the reader takes at the end. It is specific, costs them little, and the piece made it feel natural.
**Red team:** the hostile reader, who hunts for the weakest claim, the cliché and the line that sounds like AI.

## Money hunts: growth, revenue, pricing, retention
**Verbs:** find money that is already nearly ours, find the leak, make the yes easy.
**Top-pro move:** sweep wide before going deep. List every lever first, across *recover* (failed payments, billing or coupon bugs, money owed either way), *expand* (upgrades, users at a plan limit, annual prepay offered on every paid tier), *convert* (trials about to end, near-converters, unanswered buyer questions) and *win back* (churn signals, lapsed payers). Then go deep on the few with the best size × speed × confidence, and the biggest leak in the funnel. Prepare each chosen move to one yes: drafted, targeted, quantified, and runnable by an agent after the yes, not handed back as a to-do.
**Rawest material:** billing records (failed charges, plan limits, cancellations with reasons), product usage events, funnel steps from raw rows, support and sales conversations, pricing pages.
**Instruments:** read-only queries against the billing and analytics sources, cohort and funnel computations in code (never sums done in your head), a small table of candidate moves with size, confidence and effort, drafts written for each named move.
**Outside proof:** every number re-derived from the raw query by a script or a second query; a different model checks the ranking against the evidence and disputes anything thin.
**Money moment:** the person's single "yes" that releases each prepared move (send these 12 drafts, apply this coupon, change this price), with the expected value and its uncertainty spelled out.
**Red team:** the short seller, who asks why each number might be wrong or smaller than it looks, and who gets hurt if the move backfires (customer trust, spam flags).
**Note:** a recovered payment is recovered revenue, not new revenue. Label them apart, and label projections as projections.

## Data analysis and decisions
**Verbs:** find out what changed and why, decide under uncertainty.
**Top-pro move:** load raw events into a real database, reproduce the official number first (if you can't, that's a finding), then test the team's beliefs against the data, then look for the signal no one has noticed yet and check it holds on data it wasn't fitted to.
**Rawest material:** raw event logs and exports, not dashboards.
**Instruments:** SQLite or DuckDB, Python (pandas, statsmodels, scipy), charts rendered to files, a held-out period for any predictive claim.
**Outside proof:** the official number reproduced, a held-out test, a different model checking the inference chain.
**Money moment:** the decision the analysis unlocks, with options and for/against for each.
**Red team:** the forensic accountant, who ties every number back to its source and looks for double counting, survivorship and mismatched time windows.

## Code and product features
**Verbs:** make the user's job faster, never break what works.
**Top-pro move:** reproduce the problem first, write the failing test, then the fix. Read the surrounding code and match its idiom. Ship the smallest change that solves it completely, and observe it working in the real product.
**Rawest material:** the real bug (reproduction steps, logs, crash reports), the codebase, the user's actual workflow.
**Instruments:** the project's own test suite, type checker and linter, a real run of the app (browser automation and screenshots for UI), profiling for performance claims.
**Outside proof:** tests failing before and passing after, the app exercised end to end, a code review by a different model (`codex review` or similar).
**Money moment:** the user-visible behaviour that makes someone stay, upgrade or recommend it.
**Red team:** the QA breaker, who tries empty states, huge inputs, slow networks, double clicks and the back button.

## Skills, prompts, agents and pipelines (reusable automation)
**Verbs:** make the right behaviour happen every time, for inputs nobody has seen yet.
**Top-pro move:** treat it like a product with tests. Write realistic test prompts, run them with and without the change, have them judged blind, and read the transcripts, not just the outputs. Explain the *why* behind each instruction rather than shouting MUSTs. Bundle a script anything repeats.
**Rawest material:** real past transcripts and outputs, the failures that prompted the work, the user's corrections.
**Instruments:** an eval set (with and without, several runs each), a blind judge, trigger tests for when it should and shouldn't activate, validators for the file format.
**Outside proof:** the blind with/without win rate, the trigger accuracy on held-out prompts, a fresh instance following the instructions cold.
**Money moment:** the hours saved per use × uses, or the outcome it automates. Show the first real use.
**Red team:** the adversarial user, who sends inputs designed to make it misfire, over-trigger or take an action it shouldn't.

## Decks and presentations
**Verbs:** get busy people to believe a story about cause and effect and decide in 30 minutes.
**Top-pro move:** write the decision and the three-sentence argument first, then build each slide as evidence for one sentence. Every chart answers one question in its title.
**Rawest material:** the underlying data and the history of past decisions, not last quarter's deck.
**Instruments:** charts generated from the data by code, a slide renderer to check every slide visually, speaker notes timed.
**Outside proof:** a blind judge reads the deck only and states the decision being asked for. If they can't, it isn't working.
**Money moment:** the decision slide, with options, for and against, and the recommendation.
**Red team:** the skeptical executive, who asks "so what?" of every slide.

## Strategy and research
**Verbs:** find what's true, find what matters, choose.
**Top-pro move:** go to primary sources and to people's revealed behaviour (what they paid for, what they did), not opinions. State the assumptions that would change the answer and test the cheapest one.
**Rawest material:** primary documents, raw data, transcripts, filings, the competitor's actual product.
**Instruments:** source-linked notes, a claim/evidence table, small experiments or pre-mortems.
**Outside proof:** another model attacks the reasoning blind; every claim has a source link.
**Money moment:** the choice and the first step, prepared.
**Red team:** the short seller writing the bear case.
