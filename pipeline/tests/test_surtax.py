import pandas as pd

from northsource_pipeline import surtax
from northsource_pipeline.paths import Layout


def test_parse_surtax_html_extracts_hs8_and_skips_ch98_99():
    html = "<p>7206.10.00</p><p>7206.10.00</p><p>9801.10.10</p><p>9999.00.00</p><p>section 2.1</p><p>8703.22.00</p>"
    assert surtax.parse_surtax_html(html) == ["72061000", "87032200"]


def test_orders_are_the_two_known_regulations():
    assert [o.source for o in surtax.ORDERS] == ["SOR/2025-95", "SOR/2025-118"]
    assert (
        surtax.ORDERS[0].url
        == "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-95/FullText.html"
    )
    assert (
        surtax.ORDERS[1].url
        == "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-118/FullText.html"
    )
    assert all(o.pct == 25.0 for o in surtax.ORDERS)


def test_parse_surtax_writes_staging(layout: Layout):
    surtax.parse_surtax(layout)
    df = pd.read_parquet(layout.staging() / "surtax.parquet").set_index("hs8")
    assert sorted(df.index) == ["72061000", "76011000", "87032200"]
    assert df.loc["72061000", "surtax_source"] == "SOR/2025-95"
    assert df.loc["87032200", "surtax_source"] == "SOR/2025-118"
    assert df.loc["87032200", "surtax_us_pct"] == 25.0


def test_fetch_surtax(layout: Layout, monkeypatch, tmp_path):
    urls = []

    def fake_download(url, dest, **kw):
        urls.append((url, dest.name))
        dest.write_text("<html></html>")
        return dest

    monkeypatch.setattr(surtax, "download", fake_download)
    surtax.fetch_surtax(Layout(tmp_path / "fresh", layout.period))
    assert urls == [
        (
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-95/FullText.html",
            "SOR-2025-95.html",
        ),
        (
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-118/FullText.html",
            "SOR-2025-118.html",
        ),
    ]
