"""Parse stage: run every parser, then assemble the final staging tables."""

from __future__ import annotations

import logging

import pandas as pd

from .cbsa import parse_cbsa
from .cimt import parse_cimt
from .comtrade import parse_comtrade
from .countries import fta_for
from .paths import Layout
from .surtax import parse_surtax

log = logging.getLogger(__name__)


def assemble(layout: Layout) -> None:
    st = layout.staging()
    hs_code = pd.read_parquet(st / "hs_code.parquet")
    cimt_country = pd.read_parquet(st / "cimt_country.parquet")
    cbsa_country = pd.read_parquet(st / "cbsa_country.parquet")
    tariff_raw = pd.read_parquet(st / "tariff_line_raw.parquet")
    surtax = pd.read_parquet(st / "surtax.parquet")
    world_raw = pd.read_parquet(st / "world_export_raw.parquet")

    # country: CIMT list (names) + CBSA treatments. One CBSA row may map to several ISO3.
    treatments: dict[str, list[str]] = {}
    for _, row in cbsa_country.iterrows():
        for iso in list(row["iso"]):
            treatments.setdefault(iso, list(row["treatments"]))
    country = cimt_country.dropna(subset=["iso"]).drop_duplicates("iso").copy()
    country["treatments"] = country["iso"].map(lambda iso: treatments.get(iso, []))
    country["fta"] = country["treatments"].map(fta_for)
    country["fta"] = country["fta"].astype(object).where(country["fta"].notna(), None)
    country = country[["iso", "name_en", "name_fr", "cimt_code", "treatments", "fta"]].sort_values(
        "iso"
    )
    country.to_parquet(st / "country.parquet", index=False)

    # tariff_line: only HS6 known to CIMT (drops chapters 98/99 and retired codes), plus surtax.
    known = set(hs_code["hs6"])
    tariff = tariff_raw[tariff_raw["hs6"].isin(known)].merge(surtax, on="hs8", how="left")
    tariff["surtax_source"] = (
        tariff["surtax_source"].astype(object).where(tariff["surtax_source"].notna(), None)
    )
    log.info("tariff_line: kept %d of %d HS8 lines", len(tariff), len(tariff_raw))
    tariff.sort_values("hs8").to_parquet(st / "tariff_line.parquet", index=False)

    # world_export: only known HS6 and known reporters.
    isos = set(country["iso"])
    world = world_raw[world_raw["hs6"].isin(known) & world_raw["reporter_iso"].isin(isos)]
    log.info("world_export: kept %d of %d rows", len(world), len(world_raw))
    world.sort_values(["hs6", "reporter_iso"]).to_parquet(st / "world_export.parquet", index=False)


def run_parse(layout: Layout) -> None:
    parse_cimt(layout)
    parse_cbsa(layout)
    parse_surtax(layout)
    parse_comtrade(layout)
    assemble(layout)
