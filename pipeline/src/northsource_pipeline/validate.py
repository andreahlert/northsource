"""Validation rules (a)..(e) from the spec. Any failure aborts before load."""

from __future__ import annotations

import logging

import pandas as pd

from .countries import CBSA_ALIASES, cimt_unmapped
from .paths import Layout
from .surtax import ORDERS

log = logging.getLogger(__name__)

TOTAL_TOLERANCE = 0.001  # 0.1%


class ValidationError(Exception):
    pass


def checks(layout: Layout, *, surtax_ranges: dict[str, tuple[int, int]] | None = None) -> list[str]:
    st = layout.staging()
    ranges = surtax_ranges or {o.source: o.expected_range for o in ORDERS}
    errors: list[str] = []

    # (a) HS6 vs HS2 monthly totals
    totals = pd.read_parquet(st / "cimt_totals.parquet")
    for _, r in totals.iterrows():
        if pd.isna(r["hs6_total"]) or pd.isna(r["hs2_total"]):
            errors.append(
                f"HS6/HS2 total mismatch {int(r['year'])}-{int(r['month']):02d}: missing side"
            )
            continue
        diff = abs(r["hs6_total"] - r["hs2_total"]) / max(r["hs2_total"], 1)
        if diff > TOTAL_TOLERANCE:
            errors.append(
                f"HS6/HS2 total mismatch {int(r['year'])}-{int(r['month']):02d}: {diff:.4%}"
            )

    # (b) every HS6 in ca_import has a description
    hs_code = set(pd.read_parquet(st / "hs_code.parquet")["hs6"])
    ca_hs6 = set(pd.read_parquet(st / "ca_import.parquet")["hs6"])
    for hs6 in sorted(ca_hs6 - hs_code):
        errors.append(f"HS6 {hs6} in ca_import has no description")

    # (c) every CIMT country code maps to ISO3 or is in the drop list
    cimt_codes = pd.read_parquet(st / "cimt_country.parquet")["cimt_code"]
    for code in cimt_unmapped(cimt_codes):
        errors.append(f"CIMT country code {code} has no ISO3 mapping")

    # (d) every CBSA country name maps to ISO3 (names known to have none are allowed)
    cbsa = pd.read_parquet(st / "cbsa_country.parquet")
    for _, r in cbsa.iterrows():
        if len(list(r["iso"])) == 0 and r["name"] not in CBSA_ALIASES:
            errors.append(f"CBSA country name {r['name']!r} has no ISO3 mapping")

    # (e) surtax line counts within the expected range per order
    surtax = pd.read_parquet(st / "surtax.parquet")
    counts = surtax.groupby("surtax_source").size().to_dict()
    for source, (lo, hi) in ranges.items():
        n = int(counts.get(source, 0))
        if not lo <= n <= hi:
            errors.append(f"surtax {source}: {n} HS8 lines, expected {lo}..{hi}")

    return errors


def validate(
    layout: Layout, *, surtax_ranges: dict[str, tuple[int, int]] | None = None
) -> list[str]:
    errors = checks(layout, surtax_ranges=surtax_ranges)
    for e in errors:
        log.error("validation: %s", e)
    if errors:
        raise ValidationError("; ".join(errors))
    log.info("validation passed")
    return errors
