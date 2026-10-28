# Worked example: a signup page that leaks

This example is invented to show the shape of a run. The business, the numbers and the judge scores are made up for illustration. They are not results.

## The ask

```text
Go above and beyond: our free trial page gets traffic but hardly anyone signs up. Fix it.
```

"Go above and beyond" is an explicit ask for big effort, so the skill loads. Tier: Standard.

## 1. Climb to the goal behind the goal

The ask says "fix the page". The goal behind it is "more visitors start a trial, and those trials are real people who might pay". That changes the target: a page that gets more junk signups is not a win.

Verbs, not nouns: *make a busy visitor understand the product in five seconds, make starting the trial feel safe, get them to click the button.*

## 2. Find the money moment

The money moment is the "Start free trial" button. The skill checks that the button goes to the live signup form, and that the form loads. It does not build a new form.

## 3. Sweep and build from raw material

It reads what nobody pointed at:

- the raw analytics export, not the dashboard summary;
- the page as a phone user sees it, in a real browser at 390 px wide;
- the last 30 support emails, to find the words customers use.

Made-up findings for this example:

- on a phone, the button sits below two screens of text;
- the page says "streamline your workflow" and customers say "stop copying invoices by hand";
- the form asks for a credit card, and the page never says so.

Stretch targets, all measurable in the same run:

| Target | Bar |
|---|---|
| Button visible without scrolling on a 390 px phone | yes |
| Headline uses the customer's own words | yes |
| Page fully loads on a slow phone connection | under 2.5 s |
| Card requirement stated before the click | yes |

## 4. Red-team it

A hostile first reader goes through the new page: "Why should I trust this? What happens to my card? Where's the catch?" Two of those questions had no answer on the page. Both get one plain line.

## 5. Outside judge

First the tools: a real browser screenshot at phone and desktop width, a page speed test, and a click test on the button.

Then a different model sees only the brief, the screenshots and the page source. It scores fit, depth, craft, money moment, truth and delight, and names one top fault: "the trial length is only in the footer". That gets fixed and the page is judged again.

## 6. Report against stretch targets

```text
Ready: the new trial page is in the branch, live button checked.

Targets
- button above the fold on a phone: met (390 px screenshot)
- customer words in headline: met (from 30 support emails)
- load under 2.5 s: met (speed test, slow phone profile)
- card requirement stated before click: met

Judge: round 1 fail (trial length hidden), round 2 pass.
Not asked for: the support emails showed people ask about refunds, so the page now answers it.
Money move: the page is ready to ship. One yes merges it.
Unknown: whether signups go up. Check in 14 days against last month.
```

The real signup rate is not a target in the run, because it can only be measured after real visitors arrive. It goes in a follow-up with a date.
