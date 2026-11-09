# Reviewer packet and receipt

The caller remains the only writer unless an existing host workflow explicitly assigns another owner. Prefer the installed provider connector or CLI; inspect its current help and verify the destination account, supported model and effort. Use a tool-free fresh review where sufficient. Do not require a particular vendor or CLI on every host.

When the reviewer is a command-line tool, read its current help before each use instead of trusting remembered flags. Ask for a fresh session with no saved history, no tools the review does not need, and structured output. Use subprocess argument arrays and a prompt argument or supported stdin; never interpolate source text into shell code. Some wrappers consume stdin, so confirm the prompt arrived by checking the reply against the packet. Check the model named in the returned usage metadata or the tool's own run header, not the alias you asked for. Use the authentication the user already has; do not read credentials into prompts or enable a separately paid fallback. Stop on unknown billing, an unknown account or a provider denial.

A model named for one review is that review's choice, not a permanent default. Do not substitute if the user specifies a model.

Give the judge:

- User goal and deliverable, audience, scope, fixed rubric and constraints.
- Exact artifact plus minimal raw evidence/fact sheet, with provenance and limitations.
- A file manifest and package digest. Omit author verdict, rationale and previous scores to reduce anchoring. Supply earlier findings only when needed to adjudicate a specific disputed repair; identify this limitation.
- A request for integer category scores within fixed maxima, their sum, severity-rated findings with concrete evidence/fixes, the top fault and `accepted: true|false`.
- For agreement, explicit acceptance means “I endorse this exact workflow/version within the stated proof limits; no material disagreement remains.” The judge must be free to decline.

Store each round privately:

```json
{
  "round": 1,
  "artifact_digest": "sha256 of manifest JSON",
  "manifest": {"artifact.md": "sha256 of file bytes"},
  "requested_model": "exact requested identifier, or default when none was named",
  "actual_model": "provider verified identifier or UNKNOWN",
  "requested_effort": "explicit effort",
  "independence": "different_family or same_family_fresh_context or unknown",
  "prompt_path": "versioned prompt",
  "raw_reply_path": "versioned raw reply",
  "score": 0,
  "dimensions": {},
  "findings": [],
  "accepted": false,
  "author_response": "checked findings, changes retained/reverted, unresolved disputes",
  "proof_limit": "what was actually inspected"
}
```

The zero score above is a schema example, never a verdict. Reject malformed sums, out-of-range categories, missing critical fields, wrong/unknown actual model, truncated output or digest mismatch as invalid reviews. Keep the reply and diagnose; never fill gaps with an author score. A valid review can score below target. Only current matching-digest reviews apply; historical reviews retain their original artifact hashes.
