import pandas as pd
import pytest

from northsource_pipeline import stages, validate
from northsource_pipeline.paths import Layout

RANGES = {"SOR/2025-95": (1, 10), "SOR/2025-118": (1, 10)}
# Fixture tables are far smaller than the production floors, so shrink them the same
# way surtax_ranges is shrunk, one row is enough to prove a rule other than (f) itself.
MINS = {"hs_code": 1, "tariff_line": 1, "ca_import": 1, "country": 1, "world_export": 1}


@pytest.fixture
def parsed(layout: Layout) -> Layout:
    stages.run_parse(layout)
    return layout


def test_validate_passes_on_fixture(parsed: Layout):
    assert validate.validate(parsed, surtax_ranges=RANGES, minimums=MINS) == []


def test_validate_default_ranges_fail_on_small_fixture(parsed: Layout):
    with pytest.raises(validate.ValidationError) as exc:
        validate.validate(parsed)
    assert "SOR/2025-95" in str(exc.value)


def test_total_mismatch_aborts(parsed: Layout):
    p = parsed.staging() / "cimt_totals.parquet"
    df = pd.read_parquet(p)
    df.loc[0, "hs2_total"] = int(df.loc[0, "hs6_total"] * 1.02)
    df.to_parquet(p, index=False)
    with pytest.raises(validate.ValidationError) as exc:
        validate.validate(parsed, surtax_ranges=RANGES, minimums=MINS)
    assert "HS6/HS2 total mismatch" in str(exc.value)


def test_missing_description_aborts(parsed: Layout):
    p = parsed.staging() / "hs_code.parquet"
    df = pd.read_parquet(p)
    df[df.hs6 != "040610"].to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES, minimums=MINS)
    assert any("040610" in e and "description" in e for e in errors)


def test_unmapped_cimt_country_aborts(parsed: Layout):
    p = parsed.staging() / "cimt_country.parquet"
    df = pd.read_parquet(p)
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [{"cimt_code": "Q9", "iso": None, "name_en": "Nowhere", "name_fr": "Nulle part"}]
            ),
        ]
    )
    df.to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES, minimums=MINS)
    assert any("Q9" in e for e in errors)


def test_unmapped_cbsa_name_aborts(parsed: Layout):
    p = parsed.staging() / "cbsa_country.parquet"
    df = pd.read_parquet(p)
    df = pd.concat([df, pd.DataFrame([{"name": "Atlantis", "treatments": ["GPT"], "iso": []}])])
    df.to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES, minimums=MINS)
    assert any("Atlantis" in e for e in errors)


def test_known_no_iso_names_are_allowed(parsed: Layout):
    p = parsed.staging() / "cbsa_country.parquet"
    df = pd.read_parquet(p)
    df = pd.concat([df, pd.DataFrame([{"name": "Canary Islands", "treatments": [], "iso": []}])])
    df.to_parquet(p, index=False)
    assert validate.checks(parsed, surtax_ranges=RANGES, minimums=MINS) == []


def test_min_row_count_aborts(parsed: Layout):
    # Fixture hs_code has 4 rows, well under a floor of 10: a changed CBSA/CIMT page that
    # degrades to a near-empty parse must not pass validation silently.
    errors = validate.checks(parsed, surtax_ranges=RANGES, minimums={"hs_code": 10})
    assert any("hs_code" in e and "expected at least 10" in e for e in errors)


def test_world_export_multiple_years_aborts(parsed: Layout):
    p = parsed.staging() / "world_export.parquet"
    df = pd.read_parquet(p)
    extra = df.copy()
    extra["year"] = extra["year"] + 1
    df = pd.concat([df, extra], ignore_index=True)
    df.to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES, minimums=MINS)
    assert any("world_export" in e and "year" in e for e in errors)


def test_ca_import_partner_iso_without_country_aborts(parsed: Layout):
    p = parsed.staging() / "ca_import.parquet"
    df = pd.read_parquet(p)
    df.loc[0, "partner_iso"] = "BRA"
    df.to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES, minimums=MINS)
    assert any("BRA" in e for e in errors)
