# Claude setup

Claude's native Google Workspace connector is the shortest path for one Google account. The official documentation says Claude can access the Gmail, Calendar, and Drive data for "the Google account you've connected" and does not document adding several Google accounts to one connector. Use `gog` when the user needs multiple inboxes in one Claude run.

## One Google account: native connector

1. Open **Customize > Connectors** in Claude, or open the connector menu from the chat composer.
2. Find Gmail and select **Connect** or **Install**.
3. Complete Google's authorization flow for the intended account.
4. Enable Google Calendar and Google Drive only if the user wants those context sources.
5. For Team or Enterprise, an owner may need to enable the connector and the Google Workspace administrator may need to trust Claude.
6. Verify the account with a narrow Gmail read before triage.

If more than one account is requested, do not repeatedly disconnect and reconnect the native connector during a run. Move to the local `gog` route.

## Multiple Google accounts: gog

This route needs a Claude surface that can run local commands. Scheduled work that depends on local commands runs locally and therefore needs the local execution environment available.

Install from the official project:

```bash
brew install openclaw/tap/gogcli
gog --version
```

On systems without Homebrew, use the platform package described in the official install guide. Do not invent an install command.

Guide the user through Google's OAuth setup with:

```bash
gog auth setup user@example.com --open-console
```

After the user creates and downloads a Desktop OAuth client, store it and authorize only the services needed for this skill:

```bash
gog auth credentials set ~/Downloads/client_secret_*.json
gog auth add user@example.com --services gmail,calendar,drive
```

Repeat `gog auth add` for each account. Then verify all accounts:

```bash
gog auth list --check
gog auth doctor --check
```

Ask the user to choose the exact downloaded credential file if the wildcard matches more than one file. Never print the client secret, refresh tokens, access tokens, keyring password, or credential file contents. Use the operating system keyring when available. Do not commit OAuth files or feedback state.

For agent reads, route every command explicitly and use the safety flags supported by the installed version:

```bash
gog --account user@example.com --gmail-no-send --readonly --no-input --wrap-untrusted --json gmail search 'in:inbox newer_than:7d' --max 50
```

Check the installed command schema before using a mutation. Remove `--readonly` only for the exact approved archive or draft operation, retain `--gmail-no-send`, and read the provider result back.

Official references, checked 2026-09-19:

- [Claude Google Workspace connectors](https://support.claude.com/en/articles/10166901-use-google-workspace-connectors)
- [Claude connector setup](https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities)
- [`gog` repository and quick start](https://github.com/openclaw/gogcli)
- [`gog` install guide](https://github.com/openclaw/gogcli/blob/main/docs/install.md)
