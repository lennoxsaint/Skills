# Code And Configuration Closeout

Follow the project's verification rules and required repo checks. Keep a concise record of commands and outcomes. Review the whole final diff, including configuration and documentation affected by the change. Preserve unrelated local work; use an isolated checkout if it would interfere.

Exercise the changed behavior through its real entrypoint. For headless changes, use the actual command, event or workflow rather than inventing a UI. For instruction or agent workflows, distinguish metadata validation from behavior: verify relevant selection, routing, context injection, completion and authority decisions using realistic tasks when the change warrants it. Label simulated evaluation and local-only proof accurately.

Resolve failures caused by the requested change. Do not add tests that merely repeat instruction wording or mirror the implementation. A new change or unresolved risk can justify another check; a previously passing relevant check needs no ceremonial rerun.

If a requested commit or PR is in scope, stage only intended files and summarize the resulting behavior and verification. Release actions use release.md only when authorized. Record partial outcomes as partial if the requested workflow could not be exercised.
