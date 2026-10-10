# Personal plugin release

This demo deliberately uses no authentication. Keep the local MCP server and
HTTPS tunnel running for the entire demo. The OpenAI API key stays in the
server's `.env`; it is never included in the plugin archive.

## Start and package

Run these in separate terminals from the project root:

```sh
.venv/bin/python -m shopping_assistant.server --transport http --port 8000
ngrok http 8000
```

Use the HTTPS URL printed by ngrok:

```sh
.venv/bin/python scripts/package_plugin.py --url https://YOUR-TUNNEL/mcp
```

This creates `dist/shopping-assistant.zip` with the manifest, no-auth remote MCP
configuration, and shopping skill. Source `plugins/shopping-assistant/mcp.json`
retains localhost for local development. Rebuild when the tunnel URL changes.

## Register in ChatGPT

You can also use Plugin Creator to save the generated package as a private
plugin, including its skill and remote MCP configuration. To update an existing
plugin, use its exact backend ID and preserve its current connection settings.
A `plugins_…` package ID is not an `asdk_app_…` connection ID; do not pass it to
`--app-id`. That option is only for the registered-connection workflow below.


1. Sign in at https://chatgpt.com/plugins.
2. Choose **+ → Add custom MCP server**.
3. Name: **Shopping Assistant**. Server URL: your HTTPS `/mcp` URL.
4. Authentication: **No authentication**. Review the notice and create the plugin.
5. Install the personal connection. Copy its `plugin_asdk_app_…` ID from the URL.

A custom MCP connection by itself does not install a local skill. Build the
registered-connection version of the package:

```sh
.venv/bin/python scripts/package_plugin.py --url https://YOUR-TUNNEL/mcp --app-id plugin_asdk_app_YOUR_ID
```

This version includes `.app.json` and declares it in the manifest; it avoids a
duplicate raw MCP connection. In desktop Work, use the built-in plugin creator
to add `dist/shopping-assistant` to a personal marketplace, preserving its skill,
then install from that marketplace. Local marketplace availability varies by
surface. A ZIP is a distribution artifact, not proof of installation.

## Acceptance check

In a fresh chat with the installed plugin selected, request demo laptops under
$400. Confirm the interpreted filter. Check that results include product links,
USD prices, and checked/found coverage. Then try a semantic requirement such as
at least 4GB RAM. Missing battery-life evidence should remain unknown.

Public-directory publication is separate and requires the submission/review
flow and a stable deployed endpoint. This tunnel setup is for personal testing.

Official workflow: https://developers.openai.com/plugins/build/plugins
