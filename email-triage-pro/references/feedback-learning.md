# Feedback learning

The skill learns two different profiles: classification and writing voice. Keep both private, minimal, reversible, and scoped to the relevant account.

## Classification profile

Supported decisions:

- `archive`: place matching low-risk mail in the archive candidate lane
- `surface`: show matching mail in the main report
- `protect`: never archive matching mail automatically
- `one_off`: apply only to the named thread

Each reusable rule records only:

- a generated rule ID
- account scope or `all accounts`
- decision
- a narrow match such as sender, sender domain, exact list address, or subject phrase
- whether the rule was explicit or inferred
- distinct-example count
- created and last-used timestamps
- active or undone status

Do not store message bodies or private attachment text. Prefer the narrowest reliable match. Do not create a domain-wide archive rule from one sender when the user mentioned only that sender.

## Promotion rules

- A correction about one item becomes a one-off decision.
- `Always archive these`, `never show this sender`, `protect invoices from this address`, and equivalent statements create explicit reusable rules immediately.
- An inferred rule needs the same correction on at least two distinct threads.
- A user can undo or narrow any rule. Preserve a short rule history so the last feedback update can be reversed.
- Protected categories and `protect` rules always override `archive` rules.
- If two active rules conflict at the same precedence, surface the item and ask.

## Voice profile

Store distilled preferences, not complete drafts or private correspondence. Useful fields are:

- account scope
- formality and warmth
- normal length
- greeting and sign-off
- paragraph and list preference
- directness, humor, and apology preference
- phrases to use or avoid
- formatting constraints

Voice feedback such as `shorter`, `less formal`, `do not say just checking in`, or `sign off with Sam` applies to the revised draft now. Make it reusable only when the user says it is a general preference or repeats the correction on two distinct drafts.

Never learn factual claims, promises, prices, dates, availability, or legal positions as voice rules. Those require fresh source context.

## Persistence adapters

Use the best private state available:

1. **Local skill client:** store a private JSON profile outside the public skill folder, preferably under the user's project state directory. Set restrictive file permissions when supported.
2. **Scheduled task:** keep a compact profile inside the private task instructions. Update it only after the user confirms the proposed rule change.
3. **Hosted chat without persistent task state:** keep rules in the current conversation and return a compact feedback capsule for the user to save. Say `feedback persistence unavailable`.

Never use public memory, a shared chat, a repository, or a connected document as the default feedback store.

## End-of-run prompt

Use numbered items so the user can answer quickly:

```text
Inbox feedback: reply with items to archive, always surface, or protect.
Draft feedback: reply with the draft number and the change, such as shorter, warmer, or keep this voice.
```

Before saving reusable rules, show the proposed rule changes in one short list. Apply exact one-off choices immediately. If a user says `undo that rule`, deactivate the most recent matching rule and confirm what changed.
