# Flight report, review page and taste log

## The chat report
Keep it under 250 words, which is about a minute to read, not counting any sign-off block the person's rules require. Lead with the result and the decision you need from them, not the process. In our tests a 1,000-word handover buried a good plan, and a blind reader marked it down for that.

```markdown
**<Result in one line: what's ready.>** It's at <path or link>. <If the bar wasn't met: "Judge: below the bar on <dimension> (<why>).">

| Target | Measured | Met |
|---|---|---|
| <hook under 2 s> | <1.4 s (ffprobe + frame check)> | ✅ |
| <...> | <UNKNOWN: why> | — |

**Judge:** <Codex gpt-x, final round 2: pass, fit 9 · depth 8 · craft 9 · money 9 · truth 10 · delight 8>
**Instruments run:** <ffmpeg, whisper, headless Chrome at 390/1440, ...>
**Not asked for, but done:** <the unasked-for thing, and why it matters>
**The money move:** <what's prepared> → say **"yes, <exact action>"** and I'll <exactly what happens>.
**Gaps:** <what wasn't verified, and why>
**Bigger version (optional):** <working sketch at path, one line on what it would do>

What delighted you, and what missed?
```

Rules:
- Every number in the report comes from the flight log or a tool output. Unknowns are written as UNKNOWN with the reason.
- Name the judge and its model exactly as `judge.mjs` reported them.
- If the bar wasn't met, say so in the first line, after the result: name the dimension and why. Don't make the process the headline, and don't hide it further down.
- The deliverable carries its own sources note and `evidence/` folder (contract item 10). The report points to them rather than restating them.
- The judge line gives the final verdict only. Earlier rounds, cold-run counts and instrument detail go on the review page.
- If you edited after the last judged round, say which edits the judge didn't see.

## The review page (visual work, decisions, skills)
Make one private page that lets the person review without opening five files:
- the deliverable embedded (the video player, the page in a frame, the decision table);
- before and after, when there was a before;
- the scoreboard and judge verdicts;
- the evidence (contact sheets, screenshots, source links);
- the money move, with the exact yes.

Where the host offers private hosted pages (for example Claude's Artifact tool), publish it there. Otherwise write `review.html` in the run folder and give the path. Never make the page public.

## The taste log
File: `$AMBITIOUS_HOME/taste-log.md` (default `~/.ambitious/taste-log.md`). Create it if missing.

When the person answers "what delighted you, and what missed?", add one line:
```
- 2026-10-20 · <task in 6 words> · delighted: <their words, short> · missed: <their words, short> · run: <run folder>
```
Use their words. Don't polish them into your own.

Every fifth entry, read the last five to ten and propose one to three rule changes for `$AMBITIOUS_HOME/profile.md`, each with the entries that justify it:
```
Proposed taste rule: "<rule>". Evidence: entries <dates>. Add it to your profile?
```
Apply nothing without a yes. Shared skill files never get personal taste.
