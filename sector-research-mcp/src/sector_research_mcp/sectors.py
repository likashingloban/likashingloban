"""Sector definitions for the standardized market map.

Each sector carries:
  - a short_name used to fill the report title's "*" slot,
  - a precise definition and explicit scope boundaries (to prevent
    double-counting adjacent verticals, per the methodology),
  - seed company lists (public + private) as *starting points only* — the
    actual company universe is discovered live via the Data Sources step,
  - relevant public tickers for SEC/comparables work,
  - sector-tuned source domains for Tavily and any specialized free APIs.

Seed lists are deliberately conservative and clearly labeled; they are not a
substitute for live discovery and must be expanded during analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Sector:
    key: str
    short_name: str  # fills the title "Standardized Sector Market Map — <short_name>"
    name: str
    definition: str
    in_scope: list[str]
    out_of_scope: list[str]
    seed_public: list[str] = field(default_factory=list)
    seed_private: list[str] = field(default_factory=list)
    tickers: list[str] = field(default_factory=list)
    source_domains: list[str] = field(default_factory=list)
    specialized_apis: list[str] = field(default_factory=list)
    sample_queries: list[str] = field(default_factory=list)


# Source domains shared across every sector (the Data Sources hierarchy).
COMMON_SOURCE_DOMAINS = [
    "thebusinessresearchcompany.com",
    "grandviewresearch.com",
    "alliedmarketresearch.com",
    "bcg.com",
    "mckinsey.com",
    "oliverwyman.com",
    "sec.gov",
    "gartner.com",
    "forrester.com",
    "accenture.com",
    "bain.com",
    "prnewswire.com",
    "businesswire.com",
    "techcrunch.com",
    "theinformation.com",
    "wsj.com",
    "nytimes.com",
    "economist.com",
    "bloomberg.com",
    "reuters.com",
    "pymnts.com",
    "cbinsights.com",
    "pitchbook.com",
    "crunchbase.com",
    "messari.io",
    "ycombinator.com",
    "techstars.com",
]


SECTORS: dict[str, Sector] = {
    "stablecoin-payments": Sector(
        key="stablecoin-payments",
        short_name="Stablecoins & Payment Rails",
        name="Stablecoins & Payment Rails",
        definition=(
            "Issuers of fiat-referenced stablecoins and the on/off-ramp, "
            "settlement, orchestration, and card/acquiring infrastructure that "
            "moves value between fiat and stablecoins or settles stablecoins "
            "between businesses."
        ),
        in_scope=[
            "Fiat-backed stablecoin issuers (USD, EUR and others)",
            "Stablecoin orchestration / payments APIs and PSPs",
            "On/off-ramps and treasury/settlement rails",
            "Card issuing/acquiring built on stablecoin settlement",
            "Cross-border B2B settlement on stablecoin rails",
        ],
        out_of_scope=[
            "General L1/L2 blockchains (counted under AI/market infra only via tooling)",
            "Pure DeFi lending/DEX protocols not used as a payment rail",
            "Algorithmic / non-fiat-collateralized tokens",
            "Generic fintech neobanks without stablecoin settlement",
        ],
        seed_public=["Coinbase", "Block", "PayPal", "Mastercard", "Visa", "Robinhood"],
        seed_private=[
            "Circle",
            "Tether",
            "Bridge (Stripe)",
            "BVNK",
            "Conduit",
            "Zero Hash",
            "Paxos",
            "Brale",
            "Sphere",
        ],
        tickers=["COIN", "HOOD", "PYPL", "MA", "V", "XYZ"],
        source_domains=COMMON_SOURCE_DOMAINS
        + ["defillama.com", "rwa.xyz", "circle.com", "tether.to", "paxos.com"],
        specialized_apis=["defillama", "messari", "amberdata", "coingecko"],
        sample_queries=[
            "stablecoin payments funding round Series 2025",
            "stablecoin issuer circulating supply revenue reserves",
            "GENIUS Act stablecoin license MiCA EMT",
            "cross-border B2B stablecoin settlement volume",
        ],
    ),
    "ai-infrastructure": Sector(
        key="ai-infrastructure",
        short_name="AI Infrastructure",
        name="AI Infrastructure",
        definition=(
            "The compute, model, and developer layer that produces and serves AI: "
            "accelerator silicon, GPU/cloud capacity, foundation-model labs, "
            "inference/serving, vector and data infra, MLOps, and orchestration."
        ),
        in_scope=[
            "AI accelerators / silicon",
            "GPU cloud and neoclouds",
            "Foundation model labs (sold as API/platform)",
            "Inference, serving, and model gateways",
            "Vector DBs, data and feature infra, MLOps/orchestration",
        ],
        out_of_scope=[
            "End-user AI applications (counted under AI Consumer)",
            "Generic enterprise SaaS adding an AI feature",
            "Semiconductor end-markets unrelated to AI (e.g. auto MCUs)",
        ],
        seed_public=["NVIDIA", "AMD", "Microsoft", "Google", "Amazon", "Broadcom", "Arm"],
        seed_private=[
            "OpenAI",
            "Anthropic",
            "CoreWeave",
            "Lambda",
            "Together AI",
            "Fireworks AI",
            "Mistral",
            "Databricks",
            "Cerebras",
            "Groq",
        ],
        tickers=["NVDA", "AMD", "MSFT", "GOOGL", "AMZN", "AVGO", "ARM", "ORCL", "SMCI"],
        source_domains=COMMON_SOURCE_DOMAINS
        + ["runtime.news", "stateof.ai", "semianalysis.com"],
        specialized_apis=["sec_edgar"],
        sample_queries=[
            "AI infrastructure startup funding round 2025 GPU cloud",
            "foundation model lab revenue annualized run rate",
            "AI inference serving company Series funding valuation",
            "GPU cloud capacity datacenter capex commitment",
        ],
    ),
    "ai-consumer": Sector(
        key="ai-consumer",
        short_name="AI Consumer",
        name="AI Consumer",
        definition=(
            "Consumer-facing AI products monetized via subscriptions or usage by "
            "individuals: assistants/chat, companions, search, creative tools "
            "(image/video/audio), and consumer AI hardware."
        ),
        in_scope=[
            "Consumer AI assistants and chat",
            "AI companions and entertainment",
            "Consumer creative tools (image/video/audio/writing)",
            "AI-native consumer search",
            "Consumer AI hardware/devices",
        ],
        out_of_scope=[
            "B2B / enterprise AI software (separate vertical)",
            "Model labs sold primarily as developer APIs (AI Infrastructure)",
            "Ad networks and legacy consumer apps adding an AI feature",
        ],
        seed_public=["Meta", "Alphabet", "Microsoft", "Apple", "Adobe", "Duolingo"],
        seed_private=[
            "OpenAI (ChatGPT)",
            "Perplexity",
            "Character.AI",
            "Midjourney",
            "ElevenLabs",
            "Suno",
            "Runway",
            "Luma AI",
        ],
        tickers=["META", "GOOGL", "MSFT", "AAPL", "ADBE", "DUOL"],
        source_domains=COMMON_SOURCE_DOMAINS + ["sensortower.com", "data.ai", "stateof.ai"],
        specialized_apis=["sec_edgar"],
        sample_queries=[
            "consumer AI app subscription revenue ARR 2025",
            "AI companion app funding round valuation",
            "consumer AI hardware device launch sales",
            "generative AI creative tool MAU paying subscribers",
        ],
    ),
    "market-infrastructure": Sector(
        key="market-infrastructure",
        short_name="Market Infrastructure",
        name="Market Infrastructure",
        definition=(
            "The regulated plumbing of capital markets: exchanges, clearing and "
            "settlement (CCP/CSD), custody, tokenization platforms, market data, "
            "and trading/post-trade technology, including digital-asset variants."
        ),
        in_scope=[
            "Exchanges and trading venues (incl. digital-asset exchanges)",
            "Clearing, settlement, custody (CCP/CSD/qualified custodians)",
            "Tokenization / RWA platforms and transfer agents",
            "Market data and index providers",
            "Post-trade and trading infrastructure technology",
        ],
        out_of_scope=[
            "Retail brokerage apps without venue/clearing infrastructure",
            "Stablecoin issuers (separate vertical)",
            "Buy-side asset managers and funds",
        ],
        seed_public=["ICE", "CME", "Nasdaq", "LSEG", "Deutsche Boerse", "DTCC", "Coinbase"],
        seed_private=[
            "Securitize",
            "Fnality",
            "Ondo Finance",
            "Fireblocks",
            "Anchorage Digital",
            "Clear Street",
            "Proof",
            "Digital Asset (Canton)",
        ],
        tickers=["ICE", "CME", "NDAQ", "CBOE", "MKTX", "TW", "LSEG.L", "DB1.DE"],
        source_domains=COMMON_SOURCE_DOMAINS
        + ["rwa.xyz", "dtcc.com", "swift.com", "bis.org"],
        specialized_apis=["sec_edgar", "messari"],
        sample_queries=[
            "tokenization platform funding round 2025 RWA",
            "digital asset custody clearing settlement license",
            "market infrastructure exchange revenue growth 2025",
            "central bank tokenized settlement pilot wholesale",
        ],
    ),
}


def get_sector(key: str) -> Sector:
    norm = key.strip().lower().replace(" ", "-").replace("_", "-")
    aliases = {
        "stablecoin": "stablecoin-payments",
        "stablecoins": "stablecoin-payments",
        "payments": "stablecoin-payments",
        "payment-rail": "stablecoin-payments",
        "payment-rails": "stablecoin-payments",
        "stablecoin-and-payment-rail": "stablecoin-payments",
        "ai-infra": "ai-infrastructure",
        "infrastructure": "ai-infrastructure",
        "ai-consumer-app": "ai-consumer",
        "consumer": "ai-consumer",
        "market-infra": "market-infrastructure",
        "market-infrastructures": "market-infrastructure",
    }
    norm = aliases.get(norm, norm)
    if norm not in SECTORS:
        valid = ", ".join(SECTORS)
        raise KeyError(f"Unknown sector '{key}'. Valid keys: {valid}")
    return SECTORS[norm]


def list_sector_keys() -> list[str]:
    return list(SECTORS)
