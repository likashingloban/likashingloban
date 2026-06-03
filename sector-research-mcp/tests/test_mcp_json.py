"""The committed project-scoped .mcp.json stays valid and path-independent."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mcp_json_references_console_script():
    config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = config["mcpServers"]["sector-research"]
    # Must use the PATH-resolved console script, not a machine-specific path.
    assert server["command"] == "sector-research-mcp"
    assert "/" not in server["command"]

    # That console script must actually be declared by the package.
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    assert "sector-research-mcp" in scripts
