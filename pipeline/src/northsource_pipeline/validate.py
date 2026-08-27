"""Validation rules (a)..(h) from the spec plus review follow-ups. Any failure aborts before load."""

from __future__ import annotations

import logging

import pandas as pd

from .countries import CBSA_ALIASES, cimt_unmapped
from .paths import Layout
from .surtax import ORDERS

log = logging.getLogger(__name__)

TOTAL_TOLERANCE = 0.001  # 0.1%

# Production floors per staging table. Overridable so fixture-based tests can shrink them,
# the same way surtax_ranges already is.
MINIMUMS: dict[str, int] = {
    "hs_code": 4000,
    "tariff_line": 5000,
    "ca_import": 500_000,
    "country": 150,
    "world_export": 10_000,
}


def minimums_for(*, skip_comtrade: bool) -> dict[str, int]:
    """Production floors, with the world_export floor lifted when Comtrade was skipped on
    purpose (rank then works from Canadian imports only)."""
    mins = dict(MINIMUMS)
    if skip_comtrade:
        mins["world_export"] = 0
    return mins


class ValidationError(Exception):
    pass


def checks(
    layout: Layout,
    *,
    surtax_ranges: dict[str, tuple[int, int]] | None = None,
    minimums: dict[str, int] | None = None,
) -> list[str]:
    st = layout.staging()
    ranges = surtax_ranges or {o.source: o.expected_range for o in ORDERS}
    mins = MINIMUMS if minimums is None else minimums
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

    hs_code = pd.read_parquet(st / "hs_code.parquet")
    ca_import = pd.read_parquet(st / "ca_import.parquet")
    country = pd.read_parquet(st / "country.parquet")
    tariff_line = pd.read_parquet(st / "tariff_line.parquet")
    world_export = pd.read_parquet(st / "world_export.parquet")

    # (b) every HS6 in ca_import has a description
    hs_code_set = set(hs_code["hs6"])
    ca_hs6 = set(ca_import["hs6"])
    for hs6 in sorted(ca_hs6 - hs_code_set):
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

    # (f) minimum row counts per staging table, guards against a changed page or an outage
    # producing a coherent but near-empty parse that would otherwise load silently.
    tables = {
        "hs_code": hs_code,
        "tariff_line": tariff_line,
        "ca_import": ca_import,
        "country": country,
        "world_export": world_export,
    }
    for table, floor in mins.items():
        n = len(tables.get(table, pd.DataFrame()))
        if n < floor:
            errors.append(f"{table}: {n} rows, expected at least {floor}")

    # (g) world_export holds exactly one year (rank keeps only the latest year, a second
    # year present here means a retry with a different comtrade year was never cleaned up).
    years = sorted(set(world_export["year"])) if len(world_export) else []
    if len(years) > 1:
        errors.append(f"world_export: multiple years present {years}, expected exactly one")

    # (h) every ca_import.partner_iso resolves to a known country, otherwise the load
    # aborts late on the country foreign key instead of failing here with a named code.
    missing_iso = sorted(set(ca_import["partner_iso"]) - set(country["iso"]))
    for iso in missing_iso:
        errors.append(f"partner_iso {iso} in ca_import has no country row")

    return errors


def validate(
    layout: Layout,
    *,
    surtax_ranges: dict[str, tuple[int, int]] | None = None,
    minimums: dict[str, int] | None = None,
) -> list[str]:
    errors = checks(layout, surtax_ranges=surtax_ranges, minimums=minimums)
    for e in errors:
        log.error("validation: %s", e)
    if errors:
        raise ValidationError("; ".join(errors))
    log.info("validation passed")
    return errors
