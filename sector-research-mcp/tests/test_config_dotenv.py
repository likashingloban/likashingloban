"""The server auto-loads a project .env so keys work without -e flags."""

import subprocess
import sys
import textwrap
from pathlib import Path

SRC = str(Path(__file__).resolve().parents[1] / "src")


def test_dotenv_is_autoloaded(tmp_path: Path):
    (tmp_path / ".env").write_text(
        "TAVILY_API_KEY=tvly-from-dotenv\nSEC_EDGAR_USER_AGENT=test@example.com\n",
        encoding="utf-8",
    )
    code = textwrap.dedent(
        """
        from sector_research_mcp import config
        assert config.TAVILY_API_KEY == "tvly-from-dotenv", config.TAVILY_API_KEY
        status = config.key_status()
        assert status["tavily"] is True
        assert status["sec_edgar"] is True
        print("ok")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env={"PYTHONPATH": SRC, "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_real_env_overrides_dotenv(tmp_path: Path):
    (tmp_path / ".env").write_text("TAVILY_API_KEY=from-dotenv\n", encoding="utf-8")
    code = "from sector_research_mcp import config; print(config.TAVILY_API_KEY)"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env={"PYTHONPATH": SRC, "PATH": "/usr/bin:/bin", "TAVILY_API_KEY": "from-real-env"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "from-real-env"
