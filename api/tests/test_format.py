import pytest

from northsource_api.format import display_rate, month_range, months_back, period_str, ym


@pytest.mark.parametrize(
    "text,pct,expected",
    [
        ("Free", 0.0, "0%"),
        ("6.1%", 6.1, "6.1%"),
        ("6%", 6.0, "6%"),
        ("3.32¢/kg", None, "3.32¢/kg"),
        (None, None, None),
    ],
)
def test_display_rate(text, pct, expected):
    assert display_rate(text, pct) == expected


def test_ym_and_period_str():
    assert ym(2026, 6) == 202606
    assert period_str(2026, 6) == "2026-06"


def test_months_back():
    assert months_back(2026, 6, 0) == (2026, 6)
    assert months_back(2026, 6, 11) == (2025, 7)
    assert months_back(2026, 1, 1) == (2025, 12)
    assert months_back(2026, 6, 23) == (2024, 7)


def test_month_range():
    r = month_range(2026, 6, 12)
    assert r[0] == (2025, 7) and r[-1] == (2026, 6) and len(r) == 12
    assert month_range(2026, 2, 3) == [(2025, 12), (2026, 1), (2026, 2)]
