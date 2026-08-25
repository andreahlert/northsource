import pandas as pd
import pytest

from northsource_pipeline import cli
from northsource_pipeline.paths import Layout


def test_parse_validate_rank_via_cli(layout: Layout, monkeypatch):
    root = str(layout.root)
    assert cli.main(["parse", "--period", "2026-08", "--data-dir", root]) == 0
    # fixture surtax counts are below the real expected ranges: validation must fail with exit 1
    assert cli.main(["validate", "--period", "2026-08", "--data-dir", root]) == 1
    monkeypatch.setattr(
        cli, "SURTAX_RANGES_OVERRIDE", {"SOR/2025-95": (1, 10), "SOR/2025-118": (1, 10)}
    )
    assert cli.main(["validate", "--period", "2026-08", "--data-dir", root]) == 0
    assert cli.main(["rank", "--period", "2026-08", "--data-dir", root]) == 0
    df = pd.read_parquet(layout.staging() / "alternative_rank.parquet")
    assert len(df) > 0


def test_load_without_database_url_is_usage_error(layout: Layout, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert cli.main(["load", "--period", "2026-08", "--data-dir", str(layout.root)]) == 2


def test_fetch_calls_each_source(layout: Layout, monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(cli, "fetch_cimt", lambda l: called.append("cimt") or [])
    monkeypatch.setattr(
        cli, "fetch_cbsa", lambda l, tariff_year: called.append(("cbsa", tariff_year))
    )
    monkeypatch.setattr(cli, "fetch_surtax", lambda l: called.append("surtax"))
    monkeypatch.setattr(cli, "active_hs6", lambda l: ["040610"])
    monkeypatch.setattr(
        cli,
        "fetch_comtrade",
        lambda l, hs6, **kw: called.append(("comtrade", hs6, kw["year"], kw["key"])),
    )
    monkeypatch.setenv("COMTRADE_KEY", "abc")
    assert cli.main(["fetch", "--period", "2026-08", "--data-dir", str(tmp_path)]) == 0
    assert called == ["cimt", ("cbsa", 2026), "surtax", ("comtrade", ["040610"], 2025, "abc")]


def test_fetch_skip_comtrade(layout: Layout, monkeypatch, tmp_path):
    called = []
    monkeypatch.setattr(cli, "fetch_cimt", lambda l: called.append("cimt") or [])
    monkeypatch.setattr(cli, "fetch_cbsa", lambda l, tariff_year: called.append("cbsa"))
    monkeypatch.setattr(cli, "fetch_surtax", lambda l: called.append("surtax"))
    monkeypatch.setattr(cli, "fetch_comtrade", lambda *a, **kw: called.append("comtrade"))
    assert (
        cli.main(["fetch", "--period", "2026-08", "--data-dir", str(tmp_path), "--skip-comtrade"])
        == 0
    )
    assert "comtrade" not in called


def test_bad_period_is_usage_error():
    with pytest.raises(SystemExit):
        cli.main(["parse", "--period", "2026-8"])
