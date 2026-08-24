import pandas as pd
import pytest

from northsource_pipeline import stages, validate
from northsource_pipeline.paths import Layout

RANGES = {"SOR/2025-95": (1, 10), "SOR/2025-118": (1, 10)}


@pytest.fixture
def parsed(layout: Layout) -> Layout:
    stages.run_parse(layout)
    return layout


def test_validate_passes_on_fixture(parsed: Layout):
    assert validate.validate(parsed, surtax_ranges=RANGES) == []


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
        validate.validate(parsed, surtax_ranges=RANGES)
    assert "HS6/HS2 total mismatch" in str(exc.value)


def test_missing_description_aborts(parsed: Layout):
    p = parsed.staging() / "hs_code.parquet"
    df = pd.read_parquet(p)
    df[df.hs6 != "040610"].to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES)
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
    errors = validate.checks(parsed, surtax_ranges=RANGES)
    assert any("Q9" in e for e in errors)


def test_unmapped_cbsa_name_aborts(parsed: Layout):
    p = parsed.staging() / "cbsa_country.parquet"
    df = pd.read_parquet(p)
    df = pd.concat([df, pd.DataFrame([{"name": "Atlantis", "treatments": ["GPT"], "iso": []}])])
    df.to_parquet(p, index=False)
    errors = validate.checks(parsed, surtax_ranges=RANGES)
    assert any("Atlantis" in e for e in errors)


def test_known_no_iso_names_are_allowed(parsed: Layout):
    p = parsed.staging() / "cbsa_country.parquet"
    df = pd.read_parquet(p)
    df = pd.concat([df, pd.DataFrame([{"name": "Canary Islands", "treatments": [], "iso": []}])])
    df.to_parquet(p, index=False)
    assert validate.checks(parsed, surtax_ranges=RANGES) == []
