"""Spawn the sector-research MCP server over stdio and exercise it as a client.

This is a live end-to-end smoke run: it launches the actual server process,
lists its tools/prompts, then calls a keyless data tool, the deterministic
scorer, and the renderer — printing what comes back.
"""

import asyncio
import json
import os
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _text(result):
    """Pull the JSON/text payload out of a CallToolResult."""
    for block in result.content:
        if getattr(block, "type", None) == "text":
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                return block.text
    return None


async def main():
    out_dir = tempfile.mkdtemp(prefix="sector-demo-")
    params = StdioServerParameters(
        command="sector-research-mcp",
        args=[],
        env={**os.environ, "SECTOR_RESEARCH_OUTPUT_DIR": out_dir},
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"== connected to {init.serverInfo.name} v{init.serverInfo.version}\n")

            tools = await session.list_tools()
            prompts = await session.list_prompts()
            print(f"tools: {len(tools.tools)} | prompts: {[p.name for p in prompts.prompts]}\n")

            status = _text(await session.call_tool("server_status", {}))
            print("server_status ->", json.dumps(status, indent=2), "\n")

            # Live keyless data pull (no API key needed).
            sc = _text(await session.call_tool("defillama_stablecoins", {"top": 5}))
            print("defillama_stablecoins (live):")
            print(f"  top-5 circulating total: ${sc['top_circulating_total_usd']/1e9:,.1f}B")
            for s in sc["stablecoins"]:
                print(f"  {s['symbol']:<6} {s['name']:<24} ${s['circulating_usd']/1e9:,.1f}B")
            print()

            # Deterministic scoring.
            scores = _text(
                await session.call_tool(
                    "compute_scores",
                    {
                        "funding_by_year_usd": [3.0e8, 1.2e9, 2.5e9],
                        "competitive_intensity_band": 3,
                        "market_size_annual_revenue_usd": 1.2e10,
                        "avg_gross_margin_pct": 68,
                        "growth_cagr_pct": 28,
                        "exit_12m_max_ma_usd": 1.5e8,
                        "exit_3y_max_ma_usd": 1.5e9,
                        "exit_3y_max_ipo_usd": 1.2e10,
                    },
                )
            )
            print("compute_scores ->")
            for line in scores["score_lines"]:
                print("  " + line)
            print()

            # Render a real deliverable from the skeleton.
            skel = _text(await session.call_tool("get_report_skeleton", {"sector": "stablecoin"}))
            rendered = _text(
                await session.call_tool(
                    "render_report",
                    {"sector": "stablecoin", "markdown_body": skel["skeleton_markdown"]},
                )
            )
            print("render_report ->", json.dumps(rendered["outputs"], indent=2))

    print("\n== output files ==")
    for fn in sorted(os.listdir(out_dir)):
        full = os.path.join(out_dir, fn)
        print(f"  {full}  ({os.path.getsize(full):,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
