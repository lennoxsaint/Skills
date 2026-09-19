# ChatGPT setup

Use ChatGPT's Gmail app or the plugin that contains Gmail. Do not route ChatGPT users through `gog`.

## Connect the accounts

1. Ask the user to open **Settings > Apps** or **Plugins**, whichever their ChatGPT account shows.
2. Open Gmail and select **Connect**.
3. Complete Google's sign-in and authorization flow for the intended account.
4. Return to the Gmail connection page and add each additional Gmail account when the interface offers another account connection.
5. Give each connection a clear account label when the interface supports labels.
6. In managed workspaces, explain that an administrator may need to enable Gmail or approve the required Google scopes.

App availability depends on the user's plan, region, workspace settings, role, and model. OpenAI documents that some apps support multiple connected accounts. If the Gmail connection shown to this user does not offer another account, state that limitation and process only the provider-verified account. Do not imply coverage of the missing inbox.

## Verify the connection

For every requested account, select or address that connection explicitly and run a narrow read such as the newest unread message from the last day. Confirm the returned account identity when the tool exposes it. A successful read from one Gmail connection does not verify the others.

If Calendar or Drive context is wanted, connect the matching Google Calendar and Google Drive accounts separately and verify each one with a narrow read.

## Permissions

Start with read access. Enable write actions only when the user wants Gmail draft creation or verified archiving. Keep approval prompts enabled. Never ask the user to paste an OAuth token or password into chat.

Official references, checked 2026-09-19:

- [Connected apps in ChatGPT](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt)
- [Google app data controls FAQ](https://help.openai.com/en/articles/10408842-google-app-for-chatgpt-data-controls-faq)
- [Scheduled tasks in ChatGPT](https://help.openai.com/en/articles/10291617-chatgpt-tasks)
