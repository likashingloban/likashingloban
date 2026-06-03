from sector_research_mcp import rubrics as r


def test_funding_intensity_bands():
    assert r.funding_intensity_band(50_000_000) == 1
    assert r.funding_intensity_band(100_000_000) == 2
    assert r.funding_intensity_band(499_000_000) == 2
    assert r.funding_intensity_band(500_000_000) == 3
    assert r.funding_intensity_band(1_000_000_000) == 4
    assert r.funding_intensity_band(2_000_000_000) == 5


def test_market_size_bands():
    assert r.market_size_band(900_000_000) == 1
    assert r.market_size_band(1_000_000_000) == 2
    assert r.market_size_band(3_000_000_000) == 3
    assert r.market_size_band(10_000_000_000) == 4
    assert r.market_size_band(50_000_000_000) == 5


def test_profitability_bands():
    assert r.profitability_band(19) == 1
    assert r.profitability_band(20) == 2
    assert r.profitability_band(40) == 3
    assert r.profitability_band(60) == 4
    assert r.profitability_band(75) == 5


def test_growth_bands():
    assert r.growth_band(4) == 1
    assert r.growth_band(5) == 2
    assert r.growth_band(10) == 3
    assert r.growth_band(20) == 4
    assert r.growth_band(35) == 5


def test_exit_intensity_combines_channels():
    assert r.exit_intensity_band(0, 0) == 1
    assert r.exit_intensity_band(150_000_000, 0) == 2  # limited M&A, no IPO
    assert r.exit_intensity_band(300_000_000, 0) == 3  # emerging M&A
    assert r.exit_intensity_band(0, 2_000_000_000) == 3  # $1-3B IPO
    assert r.exit_intensity_band(600_000_000, 4_000_000_000) == 4
    assert r.exit_intensity_band(1_500_000_000, 12_000_000_000) == 5
    # stronger channel wins
    assert r.exit_intensity_band(150_000_000, 12_000_000_000) == 5


def test_market_opportunity_composite():
    mo = r.MarketOpportunity(4, 5, 3)
    assert mo.composite == 4.0


def test_average_ignores_none():
    assert r.average([2, None, 4]) == 3.0
    assert r.average([None]) is None


def test_scorecard_summary_lines():
    card = r.ScoreCard(
        funding_intensity=3.33,
        competitive_intensity=2,
        market_opportunity=r.MarketOpportunity(4, 5, 3),
        exit_intensity=2.5,
    )
    lines = card.summary_lines()
    assert "Funding Intensity Score: 3.33 / 5" in lines
    assert "Competitive Intensity Score: 2 / 5" in lines
    assert "Market Opportunity Score = 4.0 / 5" in lines
    assert "Exit Intensity Score = 2.5 / 5" in lines
