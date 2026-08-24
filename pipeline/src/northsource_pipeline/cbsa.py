"""CBSA Customs Tariff: HS8 lines with MFN and preferential rates, country treatments."""

from __future__ import annotations

import logging
import re

import pandas as pd
from bs4 import BeautifulSoup

from .countries import cbsa_name_to_iso3
from .http import download
from .paths import Layout
from .rates import parse_pref, parse_rate, pref_to_json

log = logging.getLogger(__name__)

CHAPTER_URL = "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/{year}/html/00/ch{nn:02d}-eng.html"
COUNTRIES_URL = "https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/{year}/html/countries-pays-eng.html"
_HS8_RE = re.compile(r"\d{4}\.\d{2}\.\d{2}")
_TARIFF_COLUMNS = ["hs8", "hs6", "mfn_text", "mfn_pct", "pref"]


def fetch_cbsa(layout: Layout, tariff_year: int) -> None:
    raw = layout.raw("cbsa")
    for nn in range(1, 100):
        download(CHAPTER_URL.format(year=tariff_year, nn=nn), raw / f"ch{nn:02d}-eng.html")
    download(COUNTRIES_URL.format(year=tariff_year), raw / "countries-pays-eng.html")


def _rows(html: str) -> list[list[str]]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return []
    out = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if cells:
            out.append(cells)
    return out


def parse_chapter(html: str) -> pd.DataFrame:
    rows = []
    for cells in _rows(html):
        if len(cells) != 6 or not _HS8_RE.fullmatch(cells[0]):
            continue
        hs8 = cells[0].replace(".", "")
        mfn = parse_rate(cells[4])
        rows.append({
            "hs8": hs8,
            "hs6": hs8[:6],
            "mfn_text": mfn.text,
            "mfn_pct": mfn.pct,
            "pref": pref_to_json(parse_pref(cells[5])),
        })
    df = pd.DataFrame(rows, columns=_TARIFF_COLUMNS)
    df["mfn_pct"] = df["mfn_pct"].astype("float64")
    return df


def parse_countries_page(html: str) -> pd.DataFrame:
    rows = []
    for cells in _rows(html):
        if len(cells) != 5 or cells[0] == "Country Name":
            continue
        name, _mfn, gpt, ldct, other = cells
        treatments = []
        if gpt.strip().lower() == "yes":
            treatments.append("GPT")
        if ldct.strip().lower() == "yes":
            treatments.append("LDCT")
        treatments += [c.strip() for c in other.split(",") if c.strip()]
        rows.append({"name": name, "treatments": treatments, "iso": cbsa_name_to_iso3(name)})
    return pd.DataFrame(rows, columns=["name", "treatments", "iso"])


def parse_cbsa(layout: Layout) -> None:
    raw = layout.raw("cbsa")
    st = layout.staging()
    frames = []
    for nn in range(1, 100):
        page = raw / f"ch{nn:02d}-eng.html"
        if not page.exists():
            log.warning("missing chapter page %s", page.name)
            continue
        frames.append(parse_chapter(page.read_text(encoding="utf-8")))
    tariff = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_TARIFF_COLUMNS)
    tariff = tariff.drop_duplicates("hs8").sort_values("hs8").reset_index(drop=True)
    tariff.to_parquet(st / "tariff_line_raw.parquet", index=False)
    log.info("tariff_line_raw: %d HS8 lines", len(tariff))

    countries = parse_countries_page((raw / "countries-pays-eng.html").read_text(encoding="utf-8"))
    countries.to_parquet(st / "cbsa_country.parquet", index=False)
