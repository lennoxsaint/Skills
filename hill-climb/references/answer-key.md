# Building the answer key

The answer key is the hill. A climber will find every hole in it, so build it from what really happened, test it against labelled exemplars before trusting it, and lock it before the climb. Keep scratch work (mining output, builder scripts, trial scores) in `<hill>/build/`: it is not frozen and the climber never sees it.

## Mining recipes

Start from data that already exists. Save every real example with its source (file and line, URL or row id) so a reviewer can trace it. Private material (the owner's drafts, DMs, transcripts) is fine in cases and exemplars; secrets are not.

| work | where the truth lives | good / bad signal |
| --- | --- | --- |
| Agent or MCP guidance (which tool, in what order) | Claude Code `~/.claude/projects/**/*.jsonl`, Codex `~/.codex/sessions/**/*.jsonl(.zst)`, incident notes in run logs | the turn finished without tool errors or user correction / the next user message corrects it, a tool errored, a required first call was skipped |
| Content generation (posts, emails, scripts) | the drafts the system produced next to what the owner actually published or rewrote; post performance | owner kept it untouched, or it beat the owner's own median / owner rewrote it, deleted it, or it underperformed |
| App or UX polish | bug tickets, beta tester feedback, crash logs, analytics funnels, screenshots of broken states | the flow completes on a real input / a reported bug, a stuck state, a failing visual check |
| Prompts and agents in general | eval runs, past corrections, review comments | the owner approved / the owner said "no, because ..." |

Real data goes stale. A real post that broke a rule the owner has since adopted is a `fail` exemplar, labelled with the reason ("uses a phrase the owner has since banned"), not a `pass` because it was published.

For tool-choice work, `scripts/mine_tools.mjs` turns transcripts into one row per user turn:

```bash
node $HC/mine_tools.mjs --server <mcp-server-name> --out ~/.hill-climb/mining/<mcp-server-name>-turns.jsonl [--since 2026-10-01]
```

Each row has the user's words, the ordered tools called, the first call's input, which calls errored, the error text, the next user message and the source line. It masks obvious secrets. It reads Claude `tool_use` blocks and Codex `McpToolCall` items and direct function calls, whether named `mcp__<server>__<tool>` or split into `namespace: "mcp__<server>"` plus `name: "<tool>"` (counting a call logged both ways once), including zstd-compressed Codex sessions (these need `zstdcat` on the PATH; without it the miner prints `INCOMPLETE` with the number of files it could not read). One Codex turn often fans out into dozens of calls, so Codex yields fewer turns with richer chains.

## Exemplars

Exemplars are the calibration set: real outputs already marked good or bad, ideally in the owner's own words ("this one sounds like me", "never do this"). Pick 3-10 that span the failure types. Each file in `exemplars/` holds:

```json
{ "id": "ex-rewrite-1", "input": "<the case input>", "output": "<the real output, exactly as the producer would print it>",
  "label": "fail", "why": "owner rewrote the hook", "source": "path#L120", "checks": [ ...the checks its case would carry... ] }
```

A good exemplar (`pass`) must pass every check; a bad one (`fail`) must fail at least one. `validate --run`, `discriminate` and `freeze` run the checks on them and report each exemplar's failed checks; the key must pass at least 80% of the good ones (TPR) and fail at least 80% of the bad ones (TNR). This holds for every hill, a custom `scorer.command` included: every case and exemplar carries checks, and the key must have at least one good and one bad exemplar to be tested at all. When the key misses, the checks are wrong: rewrite them, keep the labels.

## From exemplar to cases

1. Write down what separates each good exemplar from each bad one, as yes/no questions.
2. Turn each real example into a case: its input, plus the checks from step 1 that apply.
3. Synthesise around the edges the real cases reveal: rephrasings, missing information, ambiguous asks, adversarial asks, the same ask for a different account or format. An agent that can read the mined data is good at this; read every synthetic case and delete the ones a real user would never send.
4. Add **negative** cases, where the right output is to do nothing, ask a question or refuse, and mark the few cases that must never fail (`must_pass`), e.g. "never publishes without a confirm". `split` keeps must-pass cases visible.
5. `validate` requires 20 visible and 8 hidden cases, 3 real cases and 3 exemplars. Aim for about 50 or more cases with at least a third real. `split` holds out ~30% as hidden tests, stratified by origin and negative; `split --reset` moves everything back and splits again.

## Check types

How a check finds its value: with no `path`, it reads the parsed JSON when the whole output is a JSON object or array, else the raw text. With `path` (e.g. `tools[0]`, `post.text`), it reads that field, parsing the output strictly and, failing that, from a ```json fence or the outermost `{...}` or `[...]` in it.

`equals`, `not_equals`, `in`, `not_in`, `any_of`, `none_of` and array membership in `contains` compare JSON values with their types: `5` is not `"5"`, `true` is not `"true"`, `null` is not `""`, and objects and arrays compare by content. A field that is missing matches nothing, not even `null` or `""` (so `not_in` passes and `in` fails on it). With no `path`, a string `value` is compared with the raw text and a number, boolean or `null` value with the parsed output (`3` equals output `3`, not `"3"`). `ci: true` compares the values' text case-insensitively instead. Text checks (`contains` on text, `regex`, the length checks) read the value as text, a missing field as empty.

| type | passes when | fields |
| --- | --- | --- |
| `equals` / `not_equals` | value matches / differs | `value` |
| `in` / `not_in` | value is / is not one of a list | `values` |
| `contains` / `not_contains` | text contains the string, or an array contains the item | `value` |
| `any_of` / `none_of` | an array shares at least one / none of the items | `values` |
| `regex` / `not_regex` | pattern matches / does not | `pattern`, `flags` |
| `max_len`, `min_len`, `max_words` | length bounds | `value` |
| `json_valid` | the whole output parses as JSON | |
| `command` | a shell command exits 0 | `run`, `timeout_sec`, `pass_env` |
| `judge` | an LLM answers YES to a yes/no question | `question`, optional `judge` spec, optional `image_path` |

Order of preference: code checks, then `command`, then `judge`.

**Command checks** run in the work folder inside the produce sandbox, with the output on stdin and env `HILL_CASE` (`{"id","input"}`), `HILL_WORKDIR`, `HILL_SCORER_DIR` and `HILL_CACHE_DIR`. Point at scorer files through `$HILL_SCORER_DIR`, never a relative path. A check every case shares (a test suite) can live in one `__contract__` case.

**Judge checks** ask one binary question, phrased so **YES means good**: "Does every number in the post appear in the input?", not "Does the post invent a number?". The judge sees the case input and the output in full (as untrusted data blocks) and must answer exactly YES or NO; anything else is retried once, then counted as a judge error. It reads at most 6,000 characters of input and 12,000 of output: a longer one is never judged and the check fails ("not judged ... a partial read never passes"), and `validate` refuses a judge check on a case input or exemplar output over the limit. Check long outputs with code, or have the producer print the part the judge needs. Answers are cached by question, input and output, so an unchanged output costs nothing on later attempts. Use a different model from the producer (`validate` warns when they match). Before adding a judge question, try it on the exemplars:

```bash
node $HC/hill.mjs judge-test <hill> --question "Does the post open with a concrete claim?" [--model claude-sonnet-5-5]
```

It prints the TPR, TNR and each exemplar's verdict. Below 0.8, sharpen the question (one property, observable in the text, no taste words like "engaging") or move it to code.

**Image judge checks** (UI, charts, thumbnails): have the producer save a screenshot under `$HILL_CACHE_DIR` and print JSON that names it, e.g. `{"shot": "c014.png", ...}`, then add `"image_path": "shot"` to the judge check. The judge gets the image (a Claude judge reads the file; a Codex judge gets it with `-i`) and still answers YES or NO. The file must be a real png, jpeg or webp of at most 5 MB inside the producer cache (an exemplar's sits inside `exemplars/`); anything else is never judged and the check fails. The image's hash is part of the cache key, so a changed screenshot is judged again. Ask about one thing you can see ("Is every label in the screenshot fully visible, with none cut off?"), never "is it beautiful": overall taste belongs to the council (stage 2).

**Proxies** (length, readability, hashtag counts) are calibrated on the owner's real outputs: set the bound at a percentile of their good examples (e.g. the 90th percentile length), not a round number.

A case passes only when every check passes (`repeats` and `pass_rule` handle flaky producers).

## The producer

`scorer/produce.mjs` is the bridge from a case to the output under test. It reads `{id, input}` on stdin, runs the current work folder's version of the system and prints the output. **Offline** means: no production writes, no messages sent, no paid side effects, and the same input gives a comparable output tomorrow. A model call is fine; a call to the live product's API is not. Replay recorded responses, stub the tool layer, or ask a model to act on the current instructions against a stub.

It runs in the produce sandbox (see [safety.md](safety.md)): the work folder is read-only, `$HILL_CACHE_DIR` is its only writable folder, and `$HILL_MODEL` carries `produce.model`. Anything else from the environment, such as a model login token, must be listed in `produce.pass_env`.

A tool-choice recipe that worked on a pilot with a production MCP server: a stub MCP server (`scorer/stub-server.mjs`) serves the work folder's real tool list and server instructions with canned answers from `scorer/fixtures.json`; `produce.mjs` runs `claude -p --model "$HILL_MODEL" --strict-mcp-config --mcp-config <stub> --tools ''` with only the stub's tools allowed and the user's words on stdin, then prints `{"first_move", "tools", "args", "reply"}` from the stub's call log. Checks then read `first_move` and `tools`.

Run one case through the real producer before writing many. `try` uses the same env, `pass_env` and sandbox as scoring (a custom `scorer.command` gets a one-case batch) and prints the output and each check's result:

```bash
node $HC/hill.mjs try <hill> --case c014                 # a pool or visible case (--split pool|optimise to pick one)
node $HC/hill.mjs try <hill> --input '"show my drafts"'  # an ad hoc input (JSON, or plain text), no checks
```

Hidden cases need `--split holdout --allow-hidden`; keep what you see out of the climbable files.

## Before brief
Commit the starting files on the hill branch first. `brief` needs a clean, committed work folder because the baseline score and the council's diff are both measured from that commit. It also refuses what the runner refuses: a repo that transforms files through git (filters, LFS, ident, encodings, CRLF conversion, sparse checkout), and staged changes that exist only in git's index (commit, unstage or stash them).

## Saturation and refresh

A case every attempt passes teaches nothing; a case nothing can pass may be wrong. After a climb, prune saturated cases, add new ones from fresh production misses, and `freeze` again for the next climb rather than editing a frozen key.
