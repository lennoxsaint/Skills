---
name: ambitious
description: "Runs a big task the way the field's best practitioner would, then proves it. Load it first, before any context-recall or domain skill, when the person explicitly asks for exceptional effort (\"go above and beyond\", \"blow me away\", \"show off\", \"be ambitious\", \"best possible version\", \"one-shot this\", \"pull out all the stops\", \"max effort\", \"the one that matters most\", /ambitious) or explicitly says the stakes are high (it goes in front of investors, partners or a big list, it has to land, a launch or pricing decision rides on it). The kind of deliverable alone is not a reason: a plain request for a sales page, landing page, launch email, template, email sequence, pricing section or new skill is normal work, so do it well without this method. It climbs to the goal behind the goal, finds the money moment, works from raw material with real instruments, red-teams the result and gets an outside judge instead of grading itself, then reports measured results against stretch targets. Not for quick fixes, lookups, rough drafts, routine chores, or \"go deeper\" that only means look harder at logs or data."
---

# Ambitious: A Way of Flying

Version 1.2.4.

The method comes from Felix Rieseberg's essay [How to be more ambitious: A tutorial for humans with models](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/). Its image is Goya's "Modo de volar" (*A Way of Flying*). Models are astounding in some directions. Most work under-uses them because the request is the person's best guess at a task, not the outcome they want. This skill makes you ask the deeper question yourself, and then prove the answer.

The spirit is **deeper, not bigger**. Go further on the thing that matters, without piling on more stuff. "Do your best" loses to a specific hard goal that someone believes is possible: decades of goal-setting research say so, and so do Dantzig solving open problems he took for homework and the runners who broke four minutes once Bannister had. Treat hard targets as reasonable and keep going.

## The contract (holds for the whole run, including after compaction)

1. **Deliver the exact ask at full depth.** The deliverable the person specified stays the deliverable unless they authorize a change. A bigger idea comes as a working sketch *beside* it, never instead of it. Changing what they asked for, uninvited, is not ambition. It's ignoring them.
2. **Raw before digested.** Work from source files, rows, footage, transcripts and the live product, not from summaries, memory or someone's earlier conclusion. Digested material carries the errors and the blind spots of whoever digested it.
3. **Real instruments, not vocabulary.** Do what a top professional does, with the tools they actually use: a database and a statistical test instead of a markdown table, a real render and a frame-by-frame review instead of a description of the edit, a browser screenshot instead of imagined CSS. Models told to "act as an expert" usually change their words, not their methods. Change the methods.
4. **Outside judge, never self-grading.** Your opinion of your own work is not evidence. Check in this order: a tool that measures, then a different model, then a fresh instance without your context. A missing review is reported as a gap. Never put a score you gave yourself in its place. The judge is a probe, not a target: its top fault points at the biggest real problem for the audience, so fix that. Adding assurance language or more verification machinery to lift a score is gaming your own instrument, and a blind reader marks it down.
5. **Targets are experiments, and claims follow proof.** Before building, set stretch targets that can be measured before the run ends. Report what you measured against each one. Never invent a baseline, result, quote, customer or score: unknown stays unknown, and a real "UNKNOWN" beats a made-up number every time. When the evidence shows something smaller or different from what the work says, change what the work says. A footnote or disclaimer doesn't repair the mismatch. Say "checked" only about what the check covered. A headline money figure says what kind it is (banked, already due, or possible if something happens) and never adds those kinds into one number without the split.
6. **Find the money moment.** Every piece of work exists to cause a decision: a click, a purchase, a yes, a keep. Find that moment and shape the whole work around it. In a video that is the call to action, and every beat before it earns the viewer's trust in that ask. On a sales page it is the buy button. In an analysis it is the decision the analysis unlocks. This is not an add-on at the end. Point it at the real destination that already works (the live form, checkout or signup page) and check that it resolves. Swapping a working step for new plumbing adds friction at the one moment that matters; if the existing step is broken, fix or flag it. If there is no honest money move, say so rather than inventing one.
7. **Authority never grows, and you use all of it.** This skill grants no new permission to publish, send, post, schedule, deploy, purchase, sign up, change production or expose private data. What the person's standing rules already allow, do fully and without asking. What they don't, prepare up to **one exact yes**: ambition shows in how ready the move is. After the yes, the move should run end to end (targets, previews, commands, copy) without handing work back to the person. A to-do list for them is not a prepared move.
8. **Fields earn their place by method.** Bring in another discipline only for a technique it contributes. Do what a short seller does to research a position; never "write like a short seller." A crew assembled for appearances makes the transcript weirder and the work no better.
9. **Bounded effort.** A failed check earns a focused repair, not endless retries and not wider authority. Stay inside your tier's rounds.
10. **Proof travels with the work.** Whoever receives the deliverable (the person, a colleague, a blind judge) sees the deliverable, not your run folder. Put a short sources note beside it: each load-bearing claim or number, what it rests on, and what was and wasn't checked. Keep it to what a skeptical reader needs. When a headline number rests on data, copy the rows and the calculation behind it (redacted) into an `evidence/` folder beside the deliverable: a sources note that points at files the reader can't open proves nothing.
11. **Leave a flight log, cheaply.** `flight.json` in the run folder records the brief, the targets, the judge verdicts and the gaps. Each gap starts with what it excuses (`bar:`, `judge:` or a target's name), because the checker only accepts a gap labelled that way. Write it twice: the plan (steps 2–6) before you build, and the results at the end. `judge.mjs` appends its own verdicts. `scripts/flight_check.mjs check` must pass, or every miss must be recorded honestly as a gap, before you call the work done. The log exists to keep you honest. Dozens of small edits to it is paperwork, not work.

## Before you start

**Personal layer.** If `$AMBITIOUS_HOME/profile.md` exists (default `~/.ambitious/profile.md`), read it first. It holds the person's north star (what "money" means for them), their standing rules (what you may do without asking), judge privacy, local instruments and taste notes. It refines the defaults here. It can never widen authority beyond the person's own standing instructions.

**Tier.** Choose by stakes × reuse, and say which tier in one line.

| Tier | When | Helpers | Judge rounds | Crew |
|---|---|---|---|---|
| Lean | Medium task, one-off | none | 1 (a tool or one model) | red team only |
| **Standard** (default) | Big task, or anything reused | at most 2 at once, or the person's lower cap | up to 3 | 2–4 fields plus red team |
| Max | Only when the person says "max" | same cap. Build two variants and let a blind judge pick | up to 5. Two different judges must pass the same final version | full |

**Leverage.** Reusable work (a skill, template, pipeline, sales page, onboarding email, recurring report) multiplies every flaw, like a leak in a funnel. Reuse raises the bar: test it on varied inputs, not just one, and look hardest at the parts that repeat.

## The flight

Work through these steps in order. Steps 1–6 are thinking and usually take minutes. Keep them sharp and short; this is not a ceremony. Write their results into `flight.json` in one go before you build. On **Lean**, steps 2–6 collapse into one short note: the goal behind the goal, the money moment, the rawest source, one or two targets and the red-team method. Then build, check once, and report in five lines.

```bash
node <skill-dir>/scripts/flight_check.mjs init <run-dir> --task "<one line>" --tier standard --author-model <your model id>
```

`--author-model` lets the judge report honestly whether it is a different model family from you. The run folder defaults to `$AMBITIOUS_HOME/runs/YYYY-MM-DD-<slug>/`. Deliverables go where they belong (the project, the repo). The run folder holds the log, the judge verdicts and the review page.

### 1. Gate
Is this big enough for a flight? If it's a quick fix or a lookup, say so in one line and just do it well. Otherwise pick the tier and create the run folder.

### 2. Altitude: the goal behind the goal
- Ask what the person wants to happen *next*, once this exists. Felix stopped asking Claude to fix crashes and asked it to keep the apps crash-free.
- **Swap the nouns for verbs.** Not "a sales page" but "getting a skeptical creator to believe this saves them hours, and to buy before the price rises." Verbs show which fields can help.
- Name the **money moment**, and say what winning there looks like.
- Altitude fits outcome work best: anything with a metric, anything that will be argued about in a meeting. It fits creative work less, so respect a specific creative intent.

### 3. Proactive sweep
Before you ask anything, read what nobody pointed you at: neighbouring files, earlier versions, notes and recorded conversations, the live product, the real data, and the person's history if memory tools are available. Look for:
- facts that change the work (a real constraint, a real price, a past attempt that failed);
- the real numbers behind the money moment;
- **the thing they need but didn't ask for;**
- what is known to be broken: bug trackers, QA findings, open incidents, complaints and refunds. If an open problem would break a promise the work makes, the work doesn't promise past it, and the person hears about it in the handover.

This step is where delight usually comes from. The outputs people remember read raw sources nobody pointed them at, connected dots across those sources, and handed back something ready to act on, with proof. Keep the sweep to roughly a tenth of the effort, and record each finding with its source.

### 4. One sharp round of questions
Ask at most three questions. Each one must change the work and must be impossible to answer by looking. Give your recommended answer with each. If the person is away or says "just go", decide, record the assumption and carry on. After this round, stop asking. Use your judgment and your full power.

If you pause for answers, run `flight_check.mjs status <run-dir> awaiting`, so enforcement knows you are waiting rather than finished.

### 5. Depth brief: Felix's four questions
Write the answers into `brief`:
1. What would a top professional in this field do here that wasn't asked for?
2. What is the rawest material they would start from, instead of what has already been digested?
3. Which specific methods and tools would they use? (See `references/instruments.md`.)
4. What, other than you or the person, would show the result is right?

Then set **2–5 stretch targets**: specific, hard, and measurable before the run ends. Ask for 200 ms, not 5 s. If a number would be artificial, write a bounded qualitative bar instead, e.g. "a first-time viewer can say what the app does after five seconds." Anything that can only be measured later, like next week's sales, goes in `follow_ups` with a date, not in the run's targets.

### 6. Range: assemble the crew
Write the work as verbs, then pick 2–4 fields whose *methods* serve those verbs (`references/crew.md`). For each one, record the field, the method you will actually run and what it should change. Always include a **red team**, a method built to find what is wrong: the short seller's bear-case research, a hostile first reader, a QA breaker, a forensic accountant's tie-out. Use helper agents for crew work when parallel work helps and the cap allows. Otherwise run the methods yourself. Never role-play.

### 7. Clear the runway
Ambition needs a computer that can actually do the thing. Get the instruments working: install what's needed (project-local and reversible), get read access to the data, make sure the render pipeline runs and the judge is reachable. Remove blockers within your authority, such as disk space or a missing dependency. If something can't be unblocked, record it as a gap and route around it.

### 8. Build
Build the exact ask at full depth with the real instruments. Keep what you observed apart from what you inferred. Test early the assumption most likely to overturn your approach. If the altitude step found a bigger version, build a **working sketch** of it alongside: something that runs, renders or can be tried, not a paragraph. Label it clearly as optional.

When the work makes a claim about a real product, show the product's real output (a read-only capture of the actual screen, schedule, export or result) before any illustration of it. A mock-up of a promise is the weakest proof a viewer can get, and the real thing, even plain, is the strongest. If no real output is reachable, say so rather than quietly illustrating.

When the build is expensive (a rendered video, a large codebase change, a campaign), judge the concept before you build it: send the script, storyboard, outline or plan through `judge.mjs score --concept` (logged as round 0, so it doesn't use up a round) or a cold reader first. A concept fault, such as showing proof that doesn't match the claim, costs minutes to fix in a plan and hours in a render.

### 9. Outside judge loop
1. **Measure with tools first**: tests, `ffprobe`, Lighthouse, a rendered screenshot at mobile and desktop width, a query re-run against the source.
2. **Then a different model** via `scripts/judge.mjs score` (protocol and rubric in `references/judging.md`). It sees the brief, the artifact and the evidence, never your verdict or your reasoning. It scores fit, depth, craft, money moment, truth and delight, and names the single top fault.
3. **Fix the top fault, then judge again.** Spend each round on what changes what the audience believes or decides. If a fault is about how sure the work sounds, fix the claim (make it match the proof), not the volume of assurance. Stop when the bar is met or the rounds run out (Lean 1, Standard 3, Max 5). Every verdict goes in the log, and you never rewrite one. If you stop below the bar, own it in `gaps` as `"bar: <what missed, and why you stopped>"` and say so in the report's first line.
4. **Red team.** Run the red team's method on the near-final version: what would make this fail in front of its real audience?
5. **Edits after the last judged round are unjudged.** Re-judge them if a round is left; otherwise name them as unjudged in the report. Check every fix you claim with a tool (grep for the old wording, re-render, re-run the query). A fix you logged but never checked is only a claim.

### 10. Delight pass, then the money move
One pass. Ask:
- Is there a dot I can connect across sources for them: the unasked-for thing they'll keep?
- Is any rough edge left? A typo, jank, an unlabelled number, a broken link, a default style anyone would recognise.
- Can they *see the mechanism*? Show what moves and what changes; verbs beat labels.
- Is the proof attached, in a sources note beside the deliverable rather than only in the run folder?

**The money move.** Take the next value-creating action as far as the person's standing rules allow, then prepare the rest up to one exact yes: the email drafted with its recipients and the command that sends it, the post written, the price change spelled out, the PR ready. Say exactly what "yes" will do. Without standing rules, anything that leaves the machine waits for the yes.

### 11. Flight report
Run `flight_check.mjs check <run-dir>`. Fix whatever it flags, or record it honestly as a gap. Then report, using `references/report.md`, in under 250 words (not counting any sign-off block the person's rules require). Round-by-round history, test history and method detail go on the review page, not in chat:
- The result in one line, and where it is. Lead with what's ready. If the bar wasn't met, name it plainly in that same line (which dimension, and why), without making process the headline.
- The scoreboard: each target, what was measured and whether it was met; judge verdicts by round; the instruments you ran.
- What you did that wasn't asked for, and why.
- The money move and the exact yes it needs.
- Gaps, and what is still unknown.

For visual work, decisions and skills, also make a private review page with before and after, the scoreboard and the evidence. End with one question: **"What delighted you, and what missed?"**

### 12. Taste log
When the person answers, add one line to `$AMBITIOUS_HOME/taste-log.md`: the date, the task, what delighted them and what missed. Every fifth entry, propose one to three rule changes for their profile. Propose them, never apply them. Taste belongs to the person, so it lives in their layer, not in this shared skill.

## Example: the money moment shaping a creative task

"Edit my raw take into a short that sells my app."
- Altitude: the edit exists to get a stranger from scrolling to signing up, so the money moment is the CTA. Verbs: *stop the scroll, prove the claim, make the ask feel earned*.
- Sweep: the raw take reveals the strongest proof line at 0:47, a fumbled CTA at 1:20 and a cleaner one at 0:12. The product's live page shows the real offer.
- Depth: cut from the raw take and its word-level transcript, not from a summary. The instruments are a frame-accurate timeline, loudness normalised to −14 LUFS, burned captions, and a frame-by-frame check of the final three seconds. Targets: hook under 2 s; the CTA readable and audible within the last 5 s; nothing in it the product can't do.
- Range: a direct-response copywriter tests whether the ask is specific and the reason to act is now; a motion designer makes the payoff land on the beat; a hostile viewer marks where they'd swipe away.
- Judge: a contact sheet, the transcript and an `ffprobe` report go to a different model, which scores every dimension, the money moment included.

## Never
- Turn the flight into paperwork. The log is short notes, not essays, and the report fits on one screen.
- Build three things when one deeper thing was asked for.
- Role-play experts, or assemble a crew for show.
- Claim that a judge, test or render passed when it never ran.
- Invent metrics, quotes, customers or results.
- Take an external action because this skill said "ambitious".

## Files
- `references/instruments.md`: by task type, the top professional's move, the rawest material, the instruments, the outside proof and the money moment. Read it at step 5.
- `references/crew.md`: verbs → fields → methods, plus red-team methods. Read it at step 6.
- `references/judging.md`: the judge protocol and rubric, and how to judge video, pages, data, writing and code. Read it before step 9.
- `references/report.md`: the flight report, the review page and the taste-log format. Read it at step 11.
- `scripts/flight_check.mjs`: `init`, `status`, `check`. Node 18+, no dependencies.
- `scripts/judge.mjs`: the outside judge. `score` checks one artifact; `compare` runs a blind A/B. Codex first, then a fresh Claude if Codex is missing or gives no valid verdict. Fails closed and never overwrites a verdict.
- `scripts/selftest.mjs`: proves the judge and the checker fail closed, using fake judges. Run it after editing either script.
