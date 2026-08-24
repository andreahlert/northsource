from pathlib import Path

import pytest

from northsource_pipeline.paths import Layout, Period


def test_period_parse_and_str():
    p = Period.parse("2026-08")
    assert (p.year, p.month) == (2026, 8)
    assert str(p) == "2026-08"
    assert p.previous_year == 2025


@pytest.mark.parametrize("bad", ["2026-8", "202608", "2026-13", "abcd-01"])
def test_period_parse_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        Period.parse(bad)


def test_layout_creates_dirs(tmp_path: Path):
    layout = Layout(tmp_path, Period(2026, 8))
    raw = layout.raw("cimt")
    staging = layout.staging()
    assert raw == tmp_path / "raw" / "cimt" / "2026-08"
    assert staging == tmp_path / "staging" / "2026-08"
    assert raw.is_dir() and staging.is_dir()
