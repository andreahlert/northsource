"""Canadian surtax orders on US-origin goods (Justice Laws consolidated text)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import pandas as pd
from bs4 import BeautifulSoup

from .http import download
from .paths import Layout

log = logging.getLogger(__name__)

_HS8_RE = re.compile(r"\b(\d{4})\.(\d{2})\.(\d{2})\b")


@dataclass(frozen=True)
class Order:
    source: str
    url: str
    pct: float
    expected_range: tuple[int, int]
    filename: str


ORDERS: list[Order] = [
    Order(
        "SOR/2025-95",
        "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-95/FullText.html",
        25.0,
        (250, 400),
        "SOR-2025-95.html",
    ),
    Order(
        "SOR/2025-118",
        "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-118/FullText.html",
        25.0,
        (10, 40),
        "SOR-2025-118.html",
    ),
]


def fetch_surtax(layout: Layout) -> None:
    raw = layout.raw("surtax")
    for order in ORDERS:
        download(order.url, raw / order.filename)


def parse_surtax_html(html: str) -> list[str]:
    text = BeautifulSoup(html, "lxml").get_text(" ")
    codes = {a + b + c for a, b, c in _HS8_RE.findall(text) if a[:2] not in ("98", "99")}
    return sorted(codes)


def parse_surtax(layout: Layout) -> None:
    raw = layout.raw("surtax")
    rows: dict[str, dict] = {}
    for order in ORDERS:
        codes = parse_surtax_html((raw / order.filename).read_text(encoding="utf-8"))
        log.info("%s: %d HS8 lines", order.source, len(codes))
        for hs8 in codes:
            rows.setdefault(
                hs8, {"hs8": hs8, "surtax_us_pct": order.pct, "surtax_source": order.source}
            )
    df = pd.DataFrame(list(rows.values()), columns=["hs8", "surtax_us_pct", "surtax_source"])
    df.sort_values("hs8").to_parquet(layout.staging() / "surtax.parquet", index=False)
