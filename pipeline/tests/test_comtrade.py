import json

import pandas as pd

from northsource_pipeline import comtrade
from northsource_pipeline.paths import Layout


def _fake_fetch(calls):
    def fn(cmd_code: str):
        calls.append(cmd_code)
        codes = cmd_code.split(",")
        return pd.DataFrame(
            [
                {
                    "reporterISO": "DEU",
                    "reporterDesc": "Germany",
                    "cmdCode": c,
                    "refYear": 2025,
                    "flowCode": "X",
                    "partnerISO": "W00",
                    "primaryValue": 10.0,
                }
                for c in codes
            ]
        )

    return fn


def test_fetch_keyless_one_file_per_hs6(layout: Layout, tmp_path):
    fresh = Layout(tmp_path / "fresh", layout.period)
    calls = []
    comtrade.fetch_comtrade(
        fresh, ["040610", "720610"], key=None, year=2025, sleep_s=0, fetch_fn=_fake_fetch(calls)
    )
    assert calls == ["040610", "720610"]
    files = sorted(p.name for p in fresh.raw("comtrade").glob("*.json"))
    assert files == ["040610.json", "720610.json"]
    assert (
        json.loads((fresh.raw("comtrade") / "040610.json").read_text())[0]["reporterISO"] == "DEU"
    )


def test_fetch_keyed_batches_by_chapter(layout: Layout, tmp_path):
    fresh = Layout(tmp_path / "fresh", layout.period)
    calls = []
    comtrade.fetch_comtrade(
        fresh,
        ["040610", "040620", "720610"],
        key="k",
        year=2025,
        sleep_s=0,
        fetch_fn=_fake_fetch(calls),
    )
    assert calls == ["040610,040620", "720610"]
    files = sorted(p.name for p in fresh.raw("comtrade").glob("*.json"))
    assert files == ["chapter_04.json", "chapter_72.json"]


def test_fetch_skips_existing_and_writes_empty_list_for_none(layout: Layout, tmp_path):
    fresh = Layout(tmp_path / "fresh", layout.period)
    (fresh.raw("comtrade") / "040610.json").write_text("[]")
    calls = []

    def fn(cmd_code):
        calls.append(cmd_code)

    comtrade.fetch_comtrade(
        fresh, ["040610", "720610"], key=None, year=2025, sleep_s=0, fetch_fn=fn
    )
    assert calls == ["720610"]
    assert (fresh.raw("comtrade") / "720610.json").read_text() == "[]"


def test_parse_comtrade_filters_non_iso_reporters(layout: Layout):
    comtrade.parse_comtrade(layout)
    df = pd.read_parquet(layout.staging() / "world_export_raw.parquet")
    assert list(df.columns) == ["hs6", "reporter_iso", "year", "value_usd"]
    cheese = df[df.hs6 == "040610"]
    assert sorted(cheese.reporter_iso) == ["DEU", "FRA", "NLD", "USA"]
    assert "S19" not in set(df.reporter_iso)
    assert set(df.year) == {2025}
    assert (
        df[(df.hs6 == "040610") & (df.reporter_iso == "DEU")].value_usd.iloc[0] == 2_400_000_000.0
    )
