from pathlib import Path

import pandas as pd
import pytest
import requests

from northsource_pipeline import cimt
from northsource_pipeline.paths import Layout
from tests.conftest import cty_desc_line, hs6_desc_line


def _http_error(status_code: int) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = status_code
    return requests.HTTPError(f"{status_code} error", response=resp)


def test_parse_hs6_desc_keeps_active_only_and_latest_text():
    text = "\r\n".join(
        [
            hs6_desc_line("040610", "198801", "199112", "KGM", "Cheese old", "Fromage vieux"),
            hs6_desc_line("040610", "199201", "999912", "KGM", "Cheese, fresh", "Fromage, frais"),
            hs6_desc_line("010111", "198801", "200112", "NMB", "Horses, dead code", "Chevaux"),
        ]
    )
    df = cimt.parse_hs6_desc(text)
    assert df.to_dict("records") == [
        {"hs6": "040610", "desc_en": "Cheese, fresh", "desc_fr": "Fromage, frais", "chapter": "04"}
    ]


def test_parse_cty_desc_maps_iso3_and_keeps_unmappable_with_none():
    text = "\r\n".join(
        [
            cty_desc_line("DE", "155", "197001", "199009", "West Germany", "Allemagne de l'Ouest"),
            cty_desc_line("DE", "155", "199010", "999912", "Germany", "Allemagne"),
            cty_desc_line("XK", "273", "201701", "999912", "Kosovo", "Kosovo"),
            cty_desc_line(
                "ZX", "005", "198801", "999912", "Unknown or unspecified", "Inconnu ou non-precisé"
            ),
        ]
    )
    df = cimt.parse_cty_desc(text)
    assert df.to_dict("records") == [
        {"cimt_code": "DE", "iso": "DEU", "name_en": "Germany", "name_fr": "Allemagne"},
        {"cimt_code": "XK", "iso": "XKX", "name_en": "Kosovo", "name_fr": "Kosovo"},
        {
            "cimt_code": "ZX",
            "iso": None,
            "name_en": "Unknown or unspecified",
            "name_fr": "Inconnu ou non-precisé",
        },
    ]


def test_aggregate_imports_sums_provinces(layout: Layout):
    folders = [cimt.year_folder(layout, 2025), cimt.year_folder(layout, 2026)]
    csvs = [next(f.glob("ODPFN015_*N.csv")) for f in folders]
    df = cimt.aggregate_imports(csvs)
    us = df[(df.hs6 == "040610") & (df.cimt_code == "US") & (df.year == 2026) & (df.month == 3)]
    assert us.value_cad.tolist() == [3_000_000]
    assert set(df.year.unique()) == {2025, 2026}
    assert len(df[(df.hs6 == "040610") & (df.cimt_code == "US")]) == 12
    assert list(df.columns) == ["hs6", "cimt_code", "year", "month", "value_cad"]


def test_monthly_totals_match(layout: Layout):
    folders = [cimt.year_folder(layout, 2025), cimt.year_folder(layout, 2026)]
    hs6 = [next(f.glob("ODPFN015_*N.csv")) for f in folders]
    hs2 = [next(f.glob("ODPFN022_*N.csv")) for f in folders]
    df = cimt.monthly_totals(hs6, hs2)
    assert len(df) == 12
    assert (df.hs6_total == df.hs2_total).all()
    assert (
        df.hs6_total.iloc[0]
        == 3_000_000
        + 900_000
        + 400_000
        + 1_500_000
        + 10_000
        + 5_000_000
        + 700_000
        + 2_000_000
        + 4_000_000
        + 8_000_000
        + 6_000_000
        + 3_000_000
    )


def test_parse_cimt_writes_staging(layout: Layout):
    cimt.parse_cimt(layout)
    st = layout.staging()
    hs = pd.read_parquet(st / "hs_code.parquet")
    assert sorted(hs.hs6) == ["040610", "720610", "847130", "870322"]
    ca = pd.read_parquet(st / "ca_import.parquet")
    assert list(ca.columns) == ["hs6", "partner_iso", "year", "month", "value_cad"]
    assert "ZX" not in set(ca.partner_iso) and None not in set(ca.partner_iso)
    assert set(ca.partner_iso) == {"USA", "FRA", "DEU", "MEX", "CHN"}
    country = pd.read_parquet(st / "cimt_country.parquet")
    assert len(country) == 9
    totals = pd.read_parquet(st / "cimt_totals.parquet")
    assert list(totals.columns) == ["year", "month", "hs6_total", "hs2_total"]


def test_fetch_cimt_downloads_and_extracts(layout: Layout, monkeypatch, tmp_path: Path):
    import io
    import zipfile

    from northsource_pipeline import cimt as mod

    def fake_download(url, dest, **kw):
        assert url == mod.ZIP_URL.format(year=int(dest.stem.split("_")[-1]))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"{dest.stem}/ODPFN015_202612N.csv", "x")
        dest.write_bytes(buf.getvalue())
        return dest

    monkeypatch.setattr(mod, "download", fake_download)
    fresh = Layout(tmp_path / "fresh", layout.period)
    folders = mod.fetch_cimt(fresh)
    assert [f.name for f in folders] == ["CIMT-CICM_Imp_2025", "CIMT-CICM_Imp_2026"]
    assert (folders[1] / "ODPFN015_202612N.csv").exists()


def test_fetch_cimt_tolerates_missing_current_year_zip(layout: Layout, monkeypatch, tmp_path: Path):
    import io
    import zipfile

    from northsource_pipeline import cimt as mod

    def fake_download(url, dest, **kw):
        year = int(dest.stem.split("_")[-1])
        if year == layout.period.year:  # 2026, not yet published
            raise _http_error(404)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"{dest.stem}/ODPFN015_202512N.csv", "x")
        dest.write_bytes(buf.getvalue())
        return dest

    monkeypatch.setattr(mod, "download", fake_download)
    fresh = Layout(tmp_path / "fresh", layout.period)
    folders = mod.fetch_cimt(fresh)
    assert [f.name for f in folders] == ["CIMT-CICM_Imp_2025"]


def test_fetch_cimt_previous_year_404_still_raises(layout: Layout, monkeypatch, tmp_path: Path):
    from northsource_pipeline import cimt as mod

    def fake_download(url, dest, **kw):
        raise _http_error(404)

    monkeypatch.setattr(mod, "download", fake_download)
    fresh = Layout(tmp_path / "fresh", layout.period)
    with pytest.raises(requests.HTTPError):
        mod.fetch_cimt(fresh)


def test_fetch_cimt_non_404_error_always_raises(layout: Layout, monkeypatch, tmp_path: Path):
    import io
    import zipfile

    from northsource_pipeline import cimt as mod

    def fake_download(url, dest, **kw):
        year = int(dest.stem.split("_")[-1])
        if year == layout.period.year:
            raise _http_error(500)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr(f"{dest.stem}/ODPFN015_202512N.csv", "x")
        dest.write_bytes(buf.getvalue())
        return dest

    monkeypatch.setattr(mod, "download", fake_download)
    fresh = Layout(tmp_path / "fresh", layout.period)
    with pytest.raises(requests.HTTPError):
        mod.fetch_cimt(fresh)
