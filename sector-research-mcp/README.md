# Sector Research MCP

An [MCP](https://modelcontextprotocol.io) server that generates **standardized,
directly comparable sector market-map memos**. It ships the analytical
methodology, the fixed memo structure, the scoring rubrics, the source
connectors, and the Markdown→PDF renderer — so a calling model (Claude Code,
Claude Desktop, or any MCP client) can produce a complete, source-traceable
memo and emit both deliverables.

Supported sectors:

| Key | Title short-name (`*`) |
|---|---|
| `stablecoin-payments` | Stablecoins & Payment Rails |
| `ai-infrastructure` | AI Infrastructure |
| `ai-consumer` | AI Consumer |
| `market-infrastructure` | Market Infrastructure |

Every memo is titled exactly **`Standardized Sector Market Map <short-name>`**
and written to both `.md` and `.pdf`.

## Design

The work is split deliberately:

- **The server** supplies the methodology + skeleton, gathers source-traceable
  data (Tavily, Messari, Amberdata, SEC EDGAR, DefiLlama, CoinGecko), does the
  **deterministic rubric math**, and renders the final files.
- **The calling model** does the synthesis — running the Data Sources step,
  filling the skeleton, and citing every material number.

This keeps scoring reproducible (it's plain Python with unit tests, not
free-form arithmetic) while leaving judgment to the model.

## Install

```bash
cd sector-research-mcp
python -m venv .venv && . .venv/bin/activate
pip install -e .          # or: pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env` and fill in what you have. **All keys are
optional** — a tool whose key is missing returns a structured error instead of
crashing, and the keyless sources (SEC EDGAR, DefiLlama, CoinGecko public tier)
work with no configuration.

| Variable | Used by | Required? |
|---|---|---|
| `TAVILY_API_KEY` | `web_search`, `extract_url` | for discovery/scraping |
| `MESSARI_API_KEY` | `messari_asset` | optional |
| `AMBERDATA_API_KEY` | `amberdata_*` | optional |
| `SEC_EDGAR_USER_AGENT` | `sec_*` | recommended (SEC asks for contact) |
| `COINGECKO_API_KEY` | `coingecko_markets` | optional (keyless tier works) |
| `SECTOR_RESEARCH_OUTPUT_DIR` | `render_report` | optional (defaults to `./reports`) |

## Run

```bash
python -m sector_research_mcp        # stdio transport
```

### Register with Claude Code

```bash
claude mcp add sector-research -- python -m sector_research_mcp
```

### Register with Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "sector-research": {
      "command": "python",
      "args": ["-m", "sector_research_mcp"],
      "env": { "TAVILY_API_KEY": "...", "SEC_EDGAR_USER_AGENT": "you@example.com" }
    }
  }
}
```

## Usage

The fastest path is the bundled prompt **`sector_market_map`**, which returns a
ready-to-run brief (methodology + skeleton) for a sector. A typical loop:

1. `get_research_instructions("stablecoin-payments")` — the full methodology.
2. `get_sector_profile(...)` — scope guardrails, seed companies, tickers, sources.
3. `web_search(...)` / `extract_url(...)` — discover the company universe and
   funding/exit activity within the stated windows.
4. `sec_recent_filings`, `sec_company_concept`, `messari_asset`,
   `defillama_stablecoins`, `coingecko_markets`, `amberdata_*` — pull
   source-traceable numbers.
5. `compute_scores(...)` — deterministic rubric bands and final score lines.
6. `render_report(sector, markdown_body)` — writes the `.md` + `.pdf`.

### Tools

| Tool | Purpose |
|---|---|
| `list_sectors` | Sectors with definitions + scope + key status |
| `get_sector_profile` | Scope, seed companies, tickers, curated sources |
| `get_research_instructions` | Full standardized methodology for a sector |
| `get_report_skeleton` | Fixed-order Markdown skeleton with score lines |
| `get_rubrics` | All scoring rubrics verbatim |
| `compute_scores` | Deterministic Funding / Competitive / Market Opportunity / Exit scores |
| `web_search` / `extract_url` | Tavily discovery + content extraction |
| `sec_recent_filings` / `sec_company_concept` / `sec_full_text_search` | SEC EDGAR (free) |
| `messari_asset` | Messari fundamentals/market data |
| `amberdata_request` / `amberdata_spot_price` | Amberdata on-chain/market data |
| `defillama_stablecoins` / `defillama_stablecoin_detail` | DefiLlama (free) |
| `coingecko_markets` | CoinGecko (free) token market data |
| `render_report` | Emit the Markdown + PDF deliverables |
| `server_status` | Credential availability + output dir |

### Methodology coverage

The standardized memo always produces, in order:

1. **Funding** — 12- and 24-month windows; headline aggregate + YoY,
   primary/secondary and geographic splits, a per-round table with per-row
   source URLs; **Funding Intensity Score** (3-yr average band).
2. **Competitive Landscape** — clusters as company-per-column tables (Overview,
   Product & Services, Moat, Target Clients, Client Key Metrics, Key Risks,
   References) plus product×geography sub-segmentation with aggregate funding;
   **Competitive Intensity Score**.
3. **Market Opportunity** — current annual revenue, gross margin, CAGR, each
   with source + tier; **Market Size / Profitability / Growth Scores** and the
   composite **Market Opportunity Score**.
4. **Exit Opportunities** — 12-month and 3-year M&A + IPO tables, public
   comparables across NYSE/NASDAQ/LSEG/ADX/HKEX/SSE; **Exit Intensity Score**
   (average of both windows).
5. **Legal & Regulatory** — US/EMEA/SEA matrix (frameworks, developments,
   lawsuits, patents) + favored use-cases by jurisdiction.
6. **Tech Stack** — open vs closed source, dominant stablecoins/protocols/
   open-source projects, recent innovations.
7. **References** — every URL and document filename used.

## Data sources & free-API suggestions

Built-in connectors: **Tavily** (search/extract over the curated source
hierarchy), **Messari**, **Amberdata**, **SEC EDGAR** (free), **DefiLlama**
(free), **CoinGecko** (free public tier).

Additional **free** APIs worth wiring in next (surfaced in the methodology so
the model knows they exist):

- **FRED** (St. Louis Fed) — macro series, keyless-ish with a free key.
- **Frankfurter / ECB SDW** — FX reference rates, fully keyless.
- **Financial Modeling Prep** & **Alpha Vantage** — equity fundamentals/quotes
  for public comparables (free tiers).
- **rwa.xyz** — tokenized real-world-asset and stablecoin metrics.
- **GLEIF LEI** — keyless entity resolution for clean company identity.

## Development

```bash
. .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

The rubric math and the memo structure are covered by `tests/` so scoring and
section ordering can't silently drift.
