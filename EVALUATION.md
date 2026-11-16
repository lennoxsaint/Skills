# Evaluations

Each public skill has its own evidence and limits report. The level says how strong the proof is, strongest first: **Blind A/B** (tested against no skill, judged blind by a different AI model), **Outside review** (a different AI model reviewed it, plus tests or a cold run), **Tested** (unit tests or one cold run, checked by script or by hand) and **Spec only** (expected results and file checks, with no measured run published).

| Skill | Level | Headline result | Biggest limit | Evaluation |
|---|---|---|---|---|
| Finish Work | Outside review | 72 → 95 (outside review score, 3 rounds) | Two tiny tasks, one model, and no comparison against no skill. | [Finish Work v1.0.0 evaluation](evaluations/finish-work.md) |
| Ambitious | Blind A/B | 7.06 vs 6.00 (blind A/B, older 1.2.3 body) | Small sample, and the shipped 1.3.1 body has no with-vs-without test of its own. | [Ambitious v1.3.1 evaluation](evaluations/ambitious.md) |
| Adversarial Review | Tested | 3/3 (planted faults found) | One run, and a pass was never seen. | [Adversarial Review v1.0.0 evaluation](evaluations/adversarial-review.md) |
| Council | Outside review | 5 → 7.5 (lowest seat score, 5-round self-review) | A self-review of its own text, not a real task; one run; the scores are model judgments. | [Council v1.0.0 evaluation](evaluations/council.md) |
| Ship-ready | Spec only | 10 cases (expected results, no run published) | Never yet run end to end on a real task. | [Ship-ready v1.0.0 evaluation](evaluations/ship-ready.md) |
| Hill Climb | Outside review | 261/261 (runner self-test checks) | Proves the runner, not real-work gains. The Linux sandbox path is untested. | [Hill Climb v1.0.1 evaluation](evaluations/hill-climb.md) |
| T3 Code Conductor | Outside review | 6/6 (right calls in a cold run) | One cold run on made-up threads. | [T3 Code Conductor v1.1.0 evaluation](evaluations/t3-code-conductor.md) |
| Claude Conductor | Outside review | 5/6 (right calls in a cold run) | One cold run on made-up threads; no unit tests of its own. | [Claude Conductor v1.1.0 evaluation](evaluations/claude-conductor.md) |
| Loop | Tested | 26 → 100 (self-scored, one cold run) | A 100 here is a self-score, from one run on one short email. | [Loop v1.0.0 evaluation](evaluations/loop.md) |
| Strategy Prompt | Tested | 6/6 (sections present, math rechecked) | Correct math is not a correct decision; one run on a made-up question. | [Strategy Prompt v1.0.0 evaluation](evaluations/strategy-prompt.md) |
| Save 10% | Tested | 37 tests (plus 40/40 trigger check) | Bank formats, provider sites and live cancellations were not all observed. | [Save 10% v2.0.1 evaluation](evaluations/save-10-percent.md) |
| Goal | Spec only | 12 cases (expected results, no run published) | It cannot prove that native Goal Mode started. | [Goal v1.1.0 evaluation](evaluations/goal.md) |
| Email Triage Pro | Spec only | 10 cases (expected results, no run published) | No measured run is published yet. | [Email Triage Pro v1.0.0 evaluation](evaluations/email-triage-pro.md) |
