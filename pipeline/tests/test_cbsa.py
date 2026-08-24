import math

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from northsource_pipeline import cbsa
from northsource_pipeline.paths import Layout
from northsource_pipeline.rates import Rate, pref_from_json


def test_parse_chapter_keeps_hs8_rows_only(layout: Layout):
    html = (layout.raw("cbsa") / "ch04-eng.html").read_text(encoding="utf-8")
    df = cbsa.parse_chapter(html)
    assert df.hs8.tolist() == ["04061010", "04061090"]
    assert df.hs6.tolist() == ["040610", "040610"]
    assert df.mfn_text.tolist() == ["3.32¢/kg", "245.5% but not less than $4.52/kg"]
    assert all(math.isnan(v) for v in df.mfn_pct)
    pref = pref_from_json(df.pref.iloc[0])
    assert pref["CEUT"] == Rate("Free", 0.0)
    assert pref["GPT"] == Rate("3.32¢/kg", None)
    assert pref_from_json(df.pref.iloc[1]) == {}


def test_parse_chapter_numeric_mfn(layout: Layout):
    html = (layout.raw("cbsa") / "ch87-eng.html").read_text(encoding="utf-8")
    df = cbsa.parse_chapter(html)
    assert df.hs8.tolist() == ["87032200"]
    assert df.mfn_pct.tolist() == [6.1]
    assert pref_from_json(df.pref.iloc[0])["NZT"] == Rate("6%", 6.0)


def test_parse_chapter_without_table_is_empty():
    df = cbsa.parse_chapter("<html><body><p>Reserved</p></body></html>")
    assert len(df) == 0
    assert list(df.columns) == ["hs8", "hs6", "mfn_text", "mfn_pct", "pref"]


def test_parse_countries_page(layout: Layout):
    html = (layout.raw("cbsa") / "countries-pays-eng.html").read_text(encoding="utf-8")
    df = cbsa.parse_countries_page(html).set_index("name")
    assert df.loc["Mexico", "treatments"] == ["MXT", "CPTPT"]
    assert df.loc["Mexico", "iso"] == ["MEX"]
    assert df.loc["Burma", "treatments"] == ["GPT", "LDCT"]
    assert df.loc["Burma", "iso"] == ["MMR"]
    assert df.loc["China", "treatments"] == []
    assert df.loc["United States of America", "treatments"] == ["UST"]


def test_parse_cbsa_writes_staging(layout: Layout):
    cbsa.parse_cbsa(layout)
    st = layout.staging()
    tl = pd.read_parquet(st / "tariff_line_raw.parquet")
    assert sorted(tl.hs8) == [
        "04061010",
        "04061090",
        "72061000",
        "84713000",
        "87032200",
        "98011010",
    ]
    cc = pd.read_parquet(st / "cbsa_country.parquet")
    assert len(cc) == 8
    assert list(cc.columns) == ["name", "treatments", "iso"]
    cc = cc.set_index("name")
    assert list(cc.loc["Mexico", "treatments"]) == ["MXT", "CPTPT"]
    assert list(cc.loc["Burma", "iso"]) == ["MMR"]
    schema = pq.read_schema(st / "cbsa_country.parquet")
    assert pa.types.is_list(schema.field("treatments").type)
    assert pa.types.is_list(schema.field("iso").type)


def test_fetch_cbsa_requests_all_pages(layout: Layout, monkeypatch, tmp_path):
    urls = []

    def fake_download(url, dest, **kw):
        urls.append(url)
        dest.write_text("<html></html>")
        return dest

    monkeypatch.setattr(cbsa, "download", fake_download)
    fresh = Layout(tmp_path / "fresh", layout.period)
    cbsa.fetch_cbsa(fresh, tariff_year=2026)
    assert len(urls) == 100
    assert (
        urls[0]
        == "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/html/00/ch01-eng.html"
    )
    assert (
        urls[-1]
        == "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/2026/html/countries-pays-eng.html"
    )
