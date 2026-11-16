# Routes to each seat

Use the first route that works.

## 1. T3 Code `delegate_task`

When T3 Code's `delegate_task` is present, use it. Each seat then runs in its own lab's harness on the user's own sign-in, so it can run the code. Settings are in step 3 of `SKILL.md`.

## 2. Lab CLIs on the user's sign-ins

Read the CLI's `--help` before each use, because flags change. Pass the brief as an argument array or on stdin. Never put the brief inside a shell string.

| Seat | CLI shape (verify with --help) |
|---|---|
| OpenAI GPT | `codex exec -m <gpt-id> -c model_reasoning_effort=high --sandbox read-only -` |
| Anthropic Claude | `claude -p --model <opus-id> --effort high --permission-mode plan --no-session-persistence --output-format json` |
| Google Gemini | `gemini -m <gemini-id> -p <brief>` |
| Grok, Gemini or Opus through Cursor | `cursor-agent -p --model <id>` (`agent` in newer installs), or the lab's own CLI |

Where no read-only flag is verified, run the seat in a scratch copy of the fingerprint, never the author's checkout.

Read the real model name from the run header or usage metadata. The alias you asked for is not proof of the model that ran. If the real model is unknown, record `UNKNOWN` and do not count that seat toward a pass.

## 3. Native subagents (one lab only)

The Claude Code `Agent` tool or Codex `spawn_agent` gives a fresh context, but only from the author's own lab. Label the receipt `same-lab review`. It never counts as a council pass. Report it as a single-seat review.

## 4. OpenRouter (paid, last resort)

OpenRouter reaches many labs through one paid API, billed per token, and sends the work to outside providers. Use it only when the user explicitly approves the spend for this run. Send redacted content only: the task, the constraints, public links and your own conclusions, never secrets, private code or personal data unless the user approves that content. OpenRouter seats are text-only and cannot run your code. Say so in the receipt.
