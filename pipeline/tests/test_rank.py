import math

import pandas as pd
import pytest

from northsource_pipeline import rank, stages
from northsource_pipeline.paths import Layout
from northsource_pipeline.rates import Rate


def test_window_last_12_months():
    ca = pd.DataFrame({"year": [2025, 2025, 2026, 2026], "month": [5, 12, 1, 6]})
    w = rank.window(ca, 12)
    assert w[0] == (2025, 7) and w[-1] == (2026, 6) and len(w) == 12


def test_hs6_tariff_picks_lowest_numeric_mfn():
    tl = pd.DataFrame(
        [
            {"hs8": "01010010", "hs6": "010100", "mfn_text": "6.5%", "mfn_pct": 6.5, "pref": "{}"},
            {
                "hs8": "01010020",
                "hs6": "010100",
                "mfn_text": "Free",
                "mfn_pct": 0.0,
                "pref": '{"GPT": {"text": "Free", "pct": 0.0}}',
            },
            {
                "hs8": "02020010",
                "hs6": "020200",
                "mfn_text": "3.32¢/kg",
                "mfn_pct": float("nan"),
                "pref": "{}",
            },
            {
                "hs8": "02020020",
                "hs6": "020200",
                "mfn_text": "9¢/kg",
                "mfn_pct": float("nan"),
                "pref": "{}",
            },
        ]
    )
    t = rank.hs6_tariff(tl)
    assert t["010100"]["mfn_text"] == "Free" and t["010100"]["mfn_pct"] == 0.0
    assert t["010100"]["pref"]["GPT"] == Rate("Free", 0.0)
    assert t["020200"]["mfn_text"] == "3.32¢/kg" and t["020200"]["mfn_pct"] is None


@pytest.mark.parametrize(
    "treatments,mfn_text,mfn_pct,pref,expected",
    [
        (
            ["CEUT"],
            "6.1%",
            6.1,
            {"CEUT": Rate("Free", 0.0), "GPT": Rate("6%", 6.0)},
            ("CEUT", "Free", 0.0),
        ),
        (
            ["MXT", "CPTPT"],
            "6.1%",
            6.1,
            {"MXT": Rate("2%", 2.0), "CPTPT": Rate("Free", 0.0)},
            ("CPTPT", "Free", 0.0),
        ),
        ([], "6.1%", 6.1, {"CEUT": Rate("Free", 0.0)}, ("MFN", "6.1%", 6.1)),
        (["GPT"], "3.32¢/kg", None, {"GPT": Rate("3.32¢/kg", None)}, ("GPT", "3.32¢/kg", None)),
        (["GPT"], "Free", 0.0, {}, ("MFN", "Free", 0.0)),
        (["GPT"], "8%", 8.0, {"GPT": Rate("8%", 8.0)}, ("GPT", "8%", 8.0)),
    ],
)
def test_applied_rate(treatments, mfn_text, mfn_pct, pref, expected):
    assert rank.applied_rate(treatments, mfn_text, mfn_pct, pref) == expected


def test_rank_keeps_only_latest_world_export_year():
    hs_code = pd.DataFrame({"hs6": ["040610"]})
    # An unrelated hs6, outside `known`, keeps ca_import non-empty so window() and the
    # boolean row filter behave normally; it is filtered out before scoring.
    ca_import = pd.DataFrame(
        [{"hs6": "999999", "partner_iso": "USA", "year": 2000, "month": 1, "value_cad": 1}]
    )
    world_export = pd.DataFrame(
        [
            {"hs6": "040610", "reporter_iso": "FRA", "year": 2024, "value_usd": 100.0},
            {"hs6": "040610", "reporter_iso": "FRA", "year": 2025, "value_usd": 200.0},
        ]
    )
    tariff_line = pd.DataFrame(
        [{"hs8": "04061010", "hs6": "040610", "mfn_text": "Free", "mfn_pct": 0.0, "pref": "{}"}]
    )
    country = pd.DataFrame([{"iso": "FRA", "treatments": []}])
    df = rank.rank(hs_code, ca_import, world_export, tariff_line, country)
    fra = df[(df.hs6 == "040610") & (df.iso == "FRA")]
    assert len(fra) == 1
    assert fra.world_export_usd.iloc[0] == 200.0


@pytest.fixture
def ranked(layout: Layout) -> pd.DataFrame:
    stages.run_parse(layout)
    rank.write_rank(layout)
    return pd.read_parquet(layout.staging() / "alternative_rank.parquet")


def test_us_never_in_alternatives(ranked):
    assert "USA" not in set(ranked.iso)


def test_columns_and_order(ranked):
    assert list(ranked.columns) == [
        "hs6",
        "iso",
        "score",
        "score_reasons",
        "already_supplies_canada",
        "ca_import_12m_cad",
        "world_export_usd",
        "tariff_treatment",
        "rate_applied_text",
        "rate_applied_pct",
        "rate_mfn_text",
        "rate_mfn_pct",
        "fta",
        "coverage",
    ]
    cheese = ranked[ranked.hs6 == "040610"]
    assert cheese.score.is_monotonic_decreasing


def test_fta_zero_supplier_outranks_mfn_supplier_with_more_volume(ranked):
    cheese = ranked[ranked.hs6 == "040610"].set_index("iso")
    fr, cn = cheese.loc["FRA"], cheese.loc["CHN"]
    assert cn.ca_import_12m_cad > fr.ca_import_12m_cad
    assert fr.score > cn.score
    assert list(fr.score_reasons) == ["supplies Canada", "FTA 0%", "top-10 world exporter"]
    assert fr.tariff_treatment == "CEUT" and fr.rate_applied_pct == 0.0 and fr.fta == "CETA"
    assert fr.rate_mfn_text == "3.32¢/kg" and pd.isna(fr.rate_mfn_pct)
    assert cn.tariff_treatment == "MFN" and pd.isna(cn.rate_applied_pct)
    assert list(cn.score_reasons) == ["supplies Canada"]
    assert fr.coverage == "canada"


def test_comtrade_only_country_has_no_canada_flag(ranked):
    nl = ranked[(ranked.hs6 == "040610") & (ranked.iso == "NLD")].iloc[0]
    assert not nl.already_supplies_canada
    assert nl.ca_import_12m_cad == 0
    assert nl.world_export_usd == 1_200_000_000.0
    assert "supplies Canada" not in list(nl.score_reasons)
    assert "FTA 0%" in list(nl.score_reasons)


def test_duty_free_mfn_reason(ranked):
    steel = ranked[ranked.hs6 == "720610"].set_index("iso")
    assert steel.loc["CHN", "tariff_treatment"] == "MFN"
    assert "duty free" in list(steel.loc["CHN", "score_reasons"])
    assert pd.isna(steel.loc["CHN", "fta"])


def test_world_only_coverage(ranked):
    laptops = ranked[ranked.hs6 == "847130"]
    assert set(laptops.coverage) == {"world_only"}
    assert sorted(laptops.iso) == ["CHN", "MEX"]
    assert (laptops.ca_import_12m_cad == 0).all()


def test_ca_import_12m_uses_window(ranked):
    fr = ranked[(ranked.hs6 == "040610") & (ranked.iso == "FRA")].iloc[0]
    assert fr.ca_import_12m_cad == 12 * 900_000


def test_volume_points_bounded(ranked):
    assert ranked.score.max() <= 100
    top = ranked[(ranked.hs6 == "870322") & (ranked.iso == "DEU")].iloc[0]
    expected = 40 + 30 + round(30 * math.log1p(72_000_000) / math.log1p(10_000_000_000))
    assert top.score == expected
    assert math.isclose(top.world_export_usd, 9_000_000_000.0)
