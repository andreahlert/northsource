import psycopg
import pytest
from psycopg.rows import dict_row

from northsource_api import queries as q


@pytest.fixture
def conn(database_url):
    with psycopg.connect(database_url, row_factory=dict_row) as c:
        yield c


def test_latest_month(conn):
    assert q.latest_month(conn) == (2026, 6)


def test_search_text_and_prefix(conn):
    en = q.search_codes(conn, "cheese", "en")
    assert [r["hs6"] for r in en] == ["040610", "040620"] or sorted(r["hs6"] for r in en) == [
        "040610",
        "040620",
    ]
    assert set(en[0]) == {"hs6", "desc", "chapter"}
    fr = q.search_codes(conn, "fromage", "fr")
    assert sorted(r["hs6"] for r in fr) == ["040610", "040620"]
    assert fr[0]["desc"].startswith("Fromage")
    assert [r["hs6"] for r in q.search_codes(conn, "0406", "en")] == ["040610", "040620"]
    assert q.search_codes(conn, "xyzzy", "en") == []
    assert [r["hs6"] for r in q.search_codes(conn, "ingots", "en")] == ["720610"]


def test_get_hs_and_suggest(conn):
    assert q.get_hs(conn, "040610")["chapter"] == "04"
    assert q.get_hs(conn, "999999") is None
    assert [r["hs6"] for r in q.suggest(conn, "040699")] == ["040610", "040620"]
    assert [r["hs6"] for r in q.suggest(conn, "04")] == ["040610", "040620"]
    assert q.suggest(conn, "999999") == []
    assert set(q.suggest(conn, "0406")[0]) == {"hs6", "desc"}


def test_hs_mfn_and_surtax(conn):
    assert q.hs_mfn(conn, "040610") == {"text": "3.32¢/kg", "pct": None}
    assert q.hs_mfn(conn, "720610") == {"text": "Free", "pct": 0.0}
    assert q.hs_mfn(conn, "999999") is None
    assert q.hs_surtax(conn, "720610") == {
        "pct": 25.0,
        "source": "SOR/2025-95",
        "hs8": ["72061000"],
    }
    assert q.hs_surtax(conn, "040610") is None


def test_alternatives_and_us(conn):
    alts = q.alternatives(conn, "040610")
    assert [a["iso"] for a in alts] == ["FRA", "CHN", "DEU", "NLD"]
    assert alts[0]["name_en"] == "France" and alts[0]["name_fr"] == "France"
    assert alts[0]["score_reasons"] == ["supplies Canada", "FTA 0%", "top-10 world exporter"]
    us = q.us_summary(conn, "040610", (2025, 7), (2026, 6))
    assert us == {"ca_import_12m_cad": 36_000_000, "world_export_usd": 1.0e9}
    assert q.us_summary(conn, "847130", (2025, 7), (2026, 6)) == {
        "ca_import_12m_cad": 0,
        "world_export_usd": 4.0e9,
    }
    assert q.coverage(conn, "040610", (2025, 7), (2026, 6)) == "canada"
    assert q.coverage(conn, "847130", (2025, 7), (2026, 6)) == "world_only"


def test_country_series_and_rank(conn):
    assert q.get_country(conn, "FRA")["treatments"] == ["CEUT"]
    assert q.get_country(conn, "ZZZ") is None
    months = [(2024, 7), (2024, 8), (2026, 6)]
    s = q.import_series(conn, "040610", "FRA", months)
    assert s == [
        {"year": 2024, "month": 7, "value_cad": 900_000},
        {"year": 2024, "month": 8, "value_cad": 900_000},
        {"year": 2026, "month": 6, "value_cad": 900_000},
    ]
    assert q.import_series(conn, "040610", "DEU", months) == [
        {"year": 2024, "month": 7, "value_cad": 0},
        {"year": 2024, "month": 8, "value_cad": 0},
        {"year": 2026, "month": 6, "value_cad": 0},
    ]
    assert q.world_export_for(conn, "040610", "FRA") == {"year": 2025, "value_usd": 1.5e9}
    assert q.world_export_for(conn, "040610", "CHN") is None
    assert q.rank_row(conn, "040610", "FRA")["score"] == 95
    assert q.rank_row(conn, "040610", "USA") is None


def test_meta_queries(conn):
    assert q.versions(conn)["cimt"] == "2026-06"
    assert q.loaded_at(conn).year == 2026
    assert q.counts(conn) == {
        "hs_code": 4,
        "country": 6,
        "tariff_line": 5,
        "ca_import": 84,
        "world_export": 8,
        "alternative_rank": 7,
    }
    f = q.featured(conn, (2025, 7), (2026, 6))
    assert f == [
        {
            "hs6": "720610",
            "desc": "Iron and non-alloy steel in ingots",
            "surtax_us_pct": 25.0,
            "ca_import_12m_cad": 60_000_000,
        }
    ]
    assert q.sitemap_ids(conn) == ["040610", "720610", "847130"]
