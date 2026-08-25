"""Small pure helpers: rate display strings and month arithmetic."""

from __future__ import annotations


def display_rate(text: str | None, pct: float | None) -> str | None:
    if pct is not None:
        return f"{float(pct):g}%"
    return text


def ym(year: int, month: int) -> int:
    return year * 100 + month


def period_str(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def months_back(year: int, month: int, n: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) - n
    return idx // 12, idx % 12 + 1


def month_range(end_year: int, end_month: int, n: int) -> list[tuple[int, int]]:
    return [months_back(end_year, end_month, n - 1 - i) for i in range(n)]
