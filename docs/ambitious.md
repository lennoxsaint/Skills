# Ambitious

Ambitious is a skill for the big jobs. You ask for something that matters, and it tries to work the way the best person in that field would. Then it has to show proof - a test, a measurement, a different model's score - instead of telling you the work is good.

## Where it comes from

The idea comes from Felix Rieseberg's article [How to be more ambitious: A tutorial for humans with models](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/) (13 Oct 2026).

He argues that models can do a lot more than we ask. Most of the time we ask for our best guess at a task and not for the thing we actually want, so the model does the small thing well and stops.

This skill makes the model ask the bigger question for you. Then it has to show proof.

## When it runs

It runs when you ask for it out loud:

- "Go above and beyond"
- "Blow me away"
- "Pull out all the stops"
- "Max effort"
- "One-shot this"
- "Be ambitious" or `/ambitious`

It also runs when you say the stakes are high. For example, the deck goes in front of investors, the email goes to your whole list, or a launch rides on it.

It does not run just because of what you asked for. "Write a sales page" is normal work. The model should do it well, without this method. It also skips quick fixes, lookups, rough drafts and "go deeper on these logs".

## How a run works

```mermaid
flowchart LR
  A[Climb to the goal behind the goal] --> B[Find the money moment]
  B --> C[Build from raw material]
  C --> D[Red-team it]
  D --> E[Outside judge]
  E -->|Top fault| C
  E --> F[Report against stretch targets]
```

**1. Climb to the goal behind the goal.** Before it starts, it asks what you want to happen once this thing exists. Not "a sales page" but "a doubtful buyer believes this saves them hours, and buys". That changes what good looks like.

**2. Find the money moment.** Every piece of work is there to cause one decision. Think of a click, a buy or a yes. It finds that moment and builds everything around it. It points the ask at the real page that already works, and checks the link.

**3. Build from raw material, with real tools.** It works from the real files, rows, footage and live product - not from summaries. And it uses the tools a pro would use. It runs a real query, makes a real render and takes a real screenshot, so nothing is a guess about how the page looks.

**4. Red-team it.** "Red-team" means attack your own work on purpose. It tries to break the work before anyone else sees it. A reader who wants it to fail. A doubter who lists every reason it won't work. A tester who clicks everything.

**5. Get an outside judge.** It does not grade itself. First a tool that measures. Then a different model that sees only the brief and the work. It fixes the biggest fault the judge names, then asks again. If no judge was possible, it says so.

**6. Report against stretch targets.** Before it builds, it sets 2-5 hard targets it can measure in the same run. At the end it shows each target, what it measured and whether it hit. Unknown stays unknown. It never makes up a number.

One rule never bends. The skill gives no new permission. It will not post, send, buy or deploy because you said "be ambitious". It gets the move ready, then waits for one clear yes.

## What it does to Claude

We tested the instructions the first public release shipped (the v1.2.3 body), before the 28 Oct trigger fix (that fix only changes when the skill loads, not what it does). There were three tasks. Each task ran three times with the skill and three times without it. A different model scored every output blind, on a 1-10 scale. It never knew which one used the skill.

| Test | With the skill | Without |
|---|---:|---:|
| All three tasks (average score) | 7.06 | 6.00 |
| Revenue-leak task | 7.22 | 6.11 |
| Coach landing page | 7.89 | 6.44 |
| Reel edit | 6.06 | 5.44 |

- Across all three tasks it scored about 17% better.
- The reel edit counts as a tie. Its three runs didn't agree, so we don't claim a win there.
- It costs more. A run took about 1.3-2x the time and tool calls.
- Does it turn on at the right time? When people asked for big effort, it turned on in 12 out of 12 runs. When people asked for something close but normal (like "write a sales page"), it wrongly turned on 67% of the time before the 28 Oct fix and 18% after.
- The built-in self test passes 58 out of 58 checks.

These are three tasks, not a big study. Treat them as an early sign.

**The version you get now (1.3.1) is leaner than the one in that table.** I ran the two head to head on the same three tasks:

| Task | 1.3 body | 1.2.3 body |
|---|---:|---:|
| Revenue-leak task | 6.50 | 6.61 |
| Coach landing page | 7.28 | 7.61 |
| Reel edit | 5.94 | 5.44 |

- About even on two tasks, better on the reel edit, and about 12% faster with 11% fewer tool calls.
- It missed the bar I set before the test. The rule said "not more than 0.3 lower on any task" and the landing page came in 0.33 lower.
- I publish it anyway because it is the one I run every day. It has not been tested against "no skill" on its own.
- Want the version that passed the rule? Download the [`ambitious-v1.2.4` release](https://github.com/lennoxsaint/Skills/releases/tag/ambitious-v1.2.4) and unzip it into your skills folder.

More detail is in the [evaluation](../evaluations/ambitious.md).

## Install

```bash
git clone --depth 1 https://github.com/lennoxsaint/Skills.git
python3 Skills/scripts/skills.py install ambitious --host claude
```

Use `--host codex` for Codex, or `--host both` for both. Start a new session if the skill does not show up right away.

Then try:

```text
Go above and beyond: find where my signup page loses people and fix the biggest leak.
```

## What you need

- Node 18 or newer, for the flight log and the judge scripts. No packages to install.
- For the outside judge: Codex or Claude Code installed on your computer, so the script can ask a fresh model from the command line. If neither is there, the run says the judge is missing instead of faking it.
- Optional: `ffmpeg` and whisper for judging video, and Playwright or headless Chrome for judging web pages.

## Your own settings

You can keep a private file at `~/.ambitious/profile.md` (or wherever `AMBITIOUS_HOME` points). Put your north star, what the model may do without asking, and your taste notes in it. It can tighten the defaults. It can never give the model more permission than your own standing rules do.

## Safety

- No new authority. Sending, posting, buying, deploying and changing live data still need your yes.
- No self-grading. A score the model gave itself never counts as proof.
- No made-up numbers, quotes, customers or results.
- The judge sees only the brief and the work, with secret-looking strings blanked out.

## Changelog

**1.3.1** (10 Nov 2026) - the leaner body I run every day, plus the same 28 Oct trigger fix. Every run is now five moves: brief, raw evidence, build, outside check, prepared next action. Extra crew fields, the working sketch, the review page and the taste log only run when they fix a problem you can name for the real audience. The flight check now warns about a missing crew only on the max tier. In a blind head-to-head this body missed the bar I set before the test, by 0.03 on one task (see above). I chose to publish it anyway.

**1.2.4** (29 Oct 2026) - label only. The version number now follows the private history (v1.2.3 plus the trigger fix). The skill text is unchanged.

**1.0.0** (28 Oct 2026) - first public release. This is the private v1.2.3 body plus the 28 Oct trigger fix. A later private version tried to replace v1.2.3 in a blind test. It did not beat v1.2.3 by the rule we wrote before the test, so v1.2.3 stayed. The fix narrows when the skill fires. It now fires only on an explicit ask for big effort, or explicitly high stakes. A plain request for a sales page or a template is now normal work. Private paths and owner-only rules were removed. The method is the same.
