"""Single-transaction load of staging Parquet into Postgres."""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import pandas as pd
import psycopg
from psycopg.types.json import Jsonb

from .paths import Layout
from .surtax import ORDERS

log = logging.getLogger(__name__)

SCHEMA_SQL = (Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8")

# table -> (parquet file, columns in COPY order)
TABLES: list[tuple[str, str, list[str]]] = [
    ("hs_code", "hs_code.parquet", ["hs6", "desc_en", "desc_fr", "chapter"]),
    ("country", "country.parquet", ["iso", "name_en", "name_fr", "cimt_code", "treatments", "fta"]),
    (
        "tariff_line",
        "tariff_line.parquet",
        ["hs8", "hs6", "mfn_text", "mfn_pct", "pref", "surtax_us_pct", "surtax_source"],
    ),
    ("ca_import", "ca_import.parquet", ["hs6", "partner_iso", "year", "month", "value_cad"]),
    ("world_export", "world_export.parquet", ["hs6", "reporter_iso", "year", "value_usd"]),
    (
        "alternative_rank",
        "alternative_rank.parquet",
        [
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
        ],
    ),
]
_JSON_COLUMNS = {"pref"}
_LIST_COLUMNS = {"treatments", "score_reasons"}


def _cell(col: str, value):
    if col in _JSON_COLUMNS:
        return Jsonb(json.loads(value))
    if col in _LIST_COLUMNS:
        return list(value)
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):  # numpy scalar -> python
        value = value.item()
        if isinstance(value, float) and math.isnan(value):
            return None
    return value


def versions_for(layout: Layout) -> dict[str, str]:
    st = layout.staging()
    ca = pd.read_parquet(st / "ca_import.parquet")
    last = int((ca["year"] * 100 + ca["month"]).max())
    we = pd.read_parquet(st / "world_export.parquet")
    return {
        "cimt": f"{last // 100}-{last % 100:02d}",
        "cbsa": str(layout.period.year),
        "comtrade": str(int(we["year"].max())) if len(we) else "none",
        "surtax": ";".join(o.source for o in ORDERS),
        "pipeline": str(layout.period),
    }


def load(layout: Layout, database_url: str, versions: dict[str, str]) -> dict[str, int]:
    st = layout.staging()
    counts: dict[str, int] = {}
    # commits on clean exit, rolls back on exception (single transaction)
    with psycopg.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        cur.execute("TRUNCATE " + ", ".join(t for t, _, _ in TABLES))
        for table, filename, cols in TABLES:
            df = pd.read_parquet(st / filename)
            with cur.copy(f"COPY {table} ({', '.join(cols)}) FROM STDIN") as copy:
                for row in df[cols].itertuples(index=False, name=None):
                    copy.write_row(tuple(_cell(c, v) for c, v in zip(cols, row)))
            counts[table] = len(df)
            log.info("loaded %s: %d rows", table, len(df))
        for source, period in versions.items():
            cur.execute(
                "INSERT INTO data_version (source, period, loaded_at) VALUES (%s, %s, now()) "
                "ON CONFLICT (source) DO UPDATE SET period = EXCLUDED.period, loaded_at = now()",
                (source, period),
            )
    return counts
