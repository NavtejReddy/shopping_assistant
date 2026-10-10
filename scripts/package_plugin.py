"""Build a secret-free plugin archive for a public HTTPS MCP endpoint."""
import argparse
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--app-id", help="Registered ChatGPT ID, with or without plugin_ prefix")
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment or url.path != "/mcp":
        parser.error("Use an HTTPS endpoint ending in /mcp, without credentials or query parameters.")
    app_id = args.app_id.removeprefix("plugin_") if args.app_id else None
    if app_id and not re.fullmatch(r"asdk_app_[A-Za-z0-9_-]+", app_id):
        parser.error("Expected the registered asdk_app_ ID from ChatGPT.")
    source = ROOT / "plugins/shopping-assistant"
    target = ROOT / "dist/shopping-assistant"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    manifest = json.loads((source / "plugin.json").read_text())
    shutil.copytree(source / "skills", target / "skills")
    if app_id:
        manifest["extensions"]["com.openai"]["apps"] = "./.app.json"
        (target / ".app.json").write_text(json.dumps({"apps": {"shopping-assistant": {"id": app_id, "required": True}}}, indent=2) + "\n")
    else:
        config = json.loads((source / "mcp.json").read_text())
        server = config["mcpServers"]["shopping-assistant"]
        server.update(url=args.url, extensions={"com.openai": {"auth": {"type": "none"}}})
        (target / "mcp.json").write_text(json.dumps(config, indent=2) + "\n")
    (target / "plugin.json").write_text(json.dumps(manifest, indent=2) + "\n")
    archive = ROOT / "dist/shopping-assistant.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in sorted(target.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(target))
    print(archive)
    print("Registered ChatGPT mapping" if app_id else "Portable remote MCP package")


if __name__ == "__main__":
    main()
