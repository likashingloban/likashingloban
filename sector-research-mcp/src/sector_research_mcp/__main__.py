"""Entry point: run the MCP server over stdio."""

from __future__ import annotations

from .server import get_server


def main() -> None:
    get_server().run()


if __name__ == "__main__":
    main()
