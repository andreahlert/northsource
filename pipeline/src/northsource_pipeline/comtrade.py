"""UN Comtrade: world exports by HS6 x reporter, annual, partner = World."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from itertools import groupby
from pathlib import Path

import pandas as pd

from .paths import Layout

log = logging.getLogger(__name__)

FetchFn = Callable[[str], "pd.DataFrame | None"]
_ISO3_RE = re.compile(r"^[A-Z]{3}$")
_COMMON = {
    "typeCode": "C",
    "freqCode": "A",
    "clCode": "HS",
    "reporterCode": None,
    "flowCode": "X",
    "partnerCode": "0",
    "partner2Code": None,
    "customsCode": None,
    "motCode": None,
    "format_output": "JSON",
    "aggregateBy": None,
    "breakdownMode": "classic",
    "countOnly": None,
    "includeDesc": True,
}


def default_fetch_fn(key: str | None, year: int) -> FetchFn:
    import comtradeapicall  # imported lazily: needs network-facing deps, never in tests

    def fn(cmd_code: str):
        if key:
            return comtradeapicall.getFinalData(
                key, period=str(year), cmdCode=cmd_code, maxRecords=100_000, **_COMMON
            )
        return comtradeapicall.previewFinalData(
            period=str(year), cmdCode=cmd_code, maxRecords=500, **_COMMON
        )

    return fn


def _call_with_retry(fn: FetchFn, cmd_code: str, attempts: int = 3, wait_s: float = 30.0):
    for i in range(attempts):
        try:
            return fn(cmd_code)
        except Exception as exc:  # noqa: BLE001 - network/API error, retry then give up
            log.warning("comtrade %s attempt %d failed: %s", cmd_code, i + 1, exc)
            if i + 1 < attempts:
                time.sleep(wait_s)
    return None


def _write(dest: Path, df) -> None:
    records = [] if df is None or len(df) == 0 else json.loads(df.to_json(orient="records"))
    dest.write_text(json.dumps(records), encoding="utf-8")


def fetch_comtrade(
    layout: Layout,
    hs6_list: list[str],
    *,
    key: str | None,
    year: int,
    sleep_s: float = 1.0,
    fetch_fn: FetchFn | None = None,
) -> None:
    raw = layout.raw("comtrade")
    fn = fetch_fn or default_fetch_fn(key, year)
    codes = sorted(set(hs6_list))
    if key:
        batches = [
            (f"chapter_{ch}.json", ",".join(group))
            for ch, group in groupby(codes, key=lambda c: c[:2])
        ]
    else:
        batches = [(f"{c}.json", c) for c in codes]
    for name, cmd_code in batches:
        dest = raw / name
        if dest.exists():
            continue
        _write(dest, _call_with_retry(fn, cmd_code))
        if sleep_s:
            time.sleep(sleep_s)


def parse_comtrade(layout: Layout) -> None:
    raw = layout.raw("comtrade")
    rows = []
    for path in sorted(raw.glob("*.json")):
        for rec in json.loads(path.read_text(encoding="utf-8")):
            iso = str(rec.get("reporterISO", ""))
            if not _ISO3_RE.match(iso):
                continue
            rows.append(
                {
                    "hs6": str(rec["cmdCode"]).zfill(6),
                    "reporter_iso": iso,
                    "year": int(rec["refYear"]),
                    "value_usd": float(rec["primaryValue"] or 0.0),
                }
            )
    df = pd.DataFrame(rows, columns=["hs6", "reporter_iso", "year", "value_usd"])
    df = df.groupby(["hs6", "reporter_iso", "year"], as_index=False)["value_usd"].sum()
    df.to_parquet(layout.staging() / "world_export_raw.parquet", index=False)
    log.info("world_export_raw: %d rows", len(df))
