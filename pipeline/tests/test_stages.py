import json

import pandas as pd

from northsource_pipeline import stages
from northsource_pipeline.paths import Layout


def test_run_parse_then_assemble(layout: Layout):
    stages.run_parse(layout)
    st = layout.staging()

    country = pd.read_parquet(st / "country.parquet").set_index("iso")
    assert sorted(country.index) == ["CHN", "DEU", "FRA", "JPN", "MEX", "MMR", "NLD", "USA"]
    assert list(country.loc["MEX", "treatments"]) == ["MXT", "CPTPT"]
    assert country.loc["MEX", "fta"] == "CUSMA"
    assert list(country.loc["CHN", "treatments"]) == []
    assert country.loc["CHN", "fta"] is None
    assert list(country.loc["MMR", "treatments"]) == ["GPT", "LDCT"]
    assert country.loc["MMR", "name_en"] == "Myanmar (Burma)"
    assert country.loc["DEU", "cimt_code"] == "DE"

    tl = pd.read_parquet(st / "tariff_line.parquet").set_index("hs8")
    assert sorted(tl.index) == ["04061010", "04061090", "72061000", "84713000", "87032200"]
    assert tl.loc["72061000", "surtax_us_pct"] == 25.0
    assert tl.loc["72061000", "surtax_source"] == "SOR/2025-95"
    assert pd.isna(tl.loc["04061010", "surtax_us_pct"])
    assert tl.loc["04061010", "surtax_source"] is None
    assert json.loads(tl.loc["87032200", "pref"])["CEUT"] == {"text": "Free", "pct": 0.0}

    we = pd.read_parquet(st / "world_export.parquet")
    assert "S19" not in set(we.reporter_iso)
    assert set(we[we.hs6 == "847130"].reporter_iso) == {"CHN", "MEX", "USA"}
    assert len(we[we.hs6 == "040610"]) == 4
