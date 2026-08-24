import pandas as pd
import psycopg
import pytest

from northsource_pipeline import load, rank, stages
from northsource_pipeline.paths import Layout

pytest.importorskip("testcontainers.postgres")
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="module")
def database_url():
    try:
        with PostgresContainer("postgres:16-alpine") as pg:
            url = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
            yield url
    except Exception as exc:  # noqa: BLE001 - docker/testcontainers unavailable, skip cleanly
        pytest.skip(f"Docker/testcontainers unavailable: {exc}")


@pytest.fixture
def staged(layout: Layout) -> Layout:
    stages.run_parse(layout)
    rank.write_rank(layout)
    return layout


def _count(url, table):
    with psycopg.connect(url) as conn:
        return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_versions_for(staged: Layout):
    v = load.versions_for(staged)
    assert v == {
        "cimt": "2026-06",
        "cbsa": "2026",
        "comtrade": "2025",
        "surtax": "SOR/2025-95;SOR/2025-118",
        "pipeline": "2026-08",
    }


def test_load_all_tables(staged: Layout, database_url):
    counts = load.load(staged, database_url, load.versions_for(staged))
    assert counts["hs_code"] == 4
    assert counts["country"] == 8
    assert counts["tariff_line"] == 5
    # partners per hs6 after CIMT_DROP filters "ZX": 040610=4 (US,FR,DE,CN),
    # 720610=4 (US,DE,MX,CN), 870322=3 (US,DE,MX); matches
    # test_cimt.py::test_parse_cimt_writes_staging.
    assert counts["ca_import"] == 12 * (4 + 4 + 3)
    assert counts["alternative_rank"] > 0
    with psycopg.connect(database_url) as conn:
        row = conn.execute(
            "SELECT mfn_pct, pref->'CEUT'->>'pct', surtax_us_pct FROM tariff_line "
            "WHERE hs8 = '87032200'"
        ).fetchone()
        assert float(row[0]) == 6.1 and row[1] == "0.0" and float(row[2]) == 25.0
        row = conn.execute("SELECT mfn_pct FROM tariff_line WHERE hs8 = '04061010'").fetchone()
        assert row[0] is None
        row = conn.execute("SELECT treatments, fta FROM country WHERE iso = 'MEX'").fetchone()
        assert row == (["MXT", "CPTPT"], "CUSMA")
        row = conn.execute(
            "SELECT score_reasons FROM alternative_rank WHERE hs6 = '040610' AND iso = 'FRA'"
        ).fetchone()
        assert row[0] == ["supplies Canada", "FTA 0%", "top-10 world exporter"]
        row = conn.execute("SELECT period FROM data_version WHERE source = 'cimt'").fetchone()
        assert row[0] == "2026-06"
        n = conn.execute(
            "SELECT count(*) FROM hs_code WHERE search_en @@ plainto_tsquery('english', 'cheese')"
        ).fetchone()[0]
        assert n == 1


def test_load_is_idempotent(staged: Layout, database_url):
    load.load(staged, database_url, load.versions_for(staged))
    load.load(staged, database_url, load.versions_for(staged))
    assert _count(database_url, "hs_code") == 4


def test_failed_load_leaves_previous_data(staged: Layout, database_url):
    load.load(staged, database_url, {"pipeline": "2026-07"})
    before = _count(database_url, "ca_import")
    p = staged.staging() / "alternative_rank.parquet"
    df = pd.read_parquet(p)
    df.loc[0, "iso"] = "QQQ"  # violates FK to country
    df.to_parquet(p, index=False)
    with pytest.raises(psycopg.Error):
        load.load(staged, database_url, {"pipeline": "2026-08"})
    assert _count(database_url, "ca_import") == before
    with psycopg.connect(database_url) as conn:
        assert (
            conn.execute("SELECT period FROM data_version WHERE source = 'pipeline'").fetchone()[0]
            == "2026-07"
        )
