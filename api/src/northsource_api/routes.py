"""HTTP routes. Thin: validate input, call queries, shape output."""

from __future__ import annotations

import logging
import re
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from psycopg import Connection

from . import queries as q
from .db import get_conn
from .format import display_rate, month_range, period_str
from .links import external_links
from .schemas import (
    AlternativeOut,
    CountryOut,
    CountryResponse,
    FeaturedItem,
    FeaturedResponse,
    HsResponse,
    ImportPoint,
    MetaResponse,
    RankOut,
    RateOut,
    SearchItem,
    SearchResponse,
    SitemapResponse,
    SurtaxOut,
    TariffOut,
    WorldExportOut,
)

log = logging.getLogger("northsource_api")

router = APIRouter()

SURTAX_NOTE = "25% surtax on US-origin goods that do not qualify under CUSMA"
USA = "USA"
_HS6_RE = re.compile(r"^\d{6}$")
_ISO_RE = re.compile(r"^[A-Z]{3}$")

Conn = Annotated[Connection, Depends(get_conn)]
Lang = Annotated[Literal["en", "fr"], Query()]


class HsNotFound(Exception):
    def __init__(self, hs6: str, suggestions: list[dict]):
        super().__init__(hs6)
        self.hs6 = hs6
        self.suggestions = suggestions


class CountryNotFound(Exception):
    def __init__(self, iso: str):
        super().__init__(iso)
        self.iso = iso


def _window(conn: Connection, months: int) -> list[tuple[int, int]]:
    latest = q.latest_month(conn)
    if latest is None:
        return []
    return month_range(latest[0], latest[1], months)


def _hs_or_404(conn: Connection, hs6: str) -> dict:
    row = q.get_hs(conn, hs6) if _HS6_RE.match(hs6) else None
    if row is None:
        raise HsNotFound(hs6, q.suggest(conn, hs6))
    return row


def _name(row: dict, lang: str) -> str:
    return row["name_fr"] if lang == "fr" else row["name_en"]


@router.get("/search", response_model=SearchResponse)
def search(
    conn: Conn,
    q_: Annotated[str, Query(alias="q", min_length=1, max_length=100)],
    lang: Lang = "en",
):
    return SearchResponse(
        query=q_, lang=lang, results=[SearchItem(**r) for r in q.search_codes(conn, q_, lang)]
    )


@router.get("/hs/{hs6}", response_model=HsResponse)
def hs_detail(conn: Conn, hs6: str, lang: Lang = "en"):
    hs = _hs_or_404(conn, hs6)
    win = _window(conn, 12)
    start, end = (win[0], win[-1]) if win else ((0, 0), (0, 0))
    mfn = q.hs_mfn(conn, hs6)
    surtax = q.hs_surtax(conn, hs6)
    us_country = q.get_country(conn, USA)
    us = q.us_summary(conn, hs6, start, end)
    alts = [
        AlternativeOut(
            iso=USA,
            name=_name(us_country, lang) if us_country else "United States",
            is_current_us_source=True,
            already_supplies_canada=us["ca_import_12m_cad"] > 0,
            ca_import_12m_cad=us["ca_import_12m_cad"],
            world_export_usd=us["world_export_usd"],
            tariff_treatment=None,
            rate_applied=None,
            rate_applied_pct=None,
            rate_mfn=display_rate(mfn["text"], mfn["pct"]) if mfn else None,
            rate_mfn_pct=mfn["pct"] if mfn else None,
            fta=us_country["fta"] if us_country else None,
            score=None,
            score_reasons=[],
        )
    ]
    for r in q.alternatives(conn, hs6):
        alts.append(
            AlternativeOut(
                iso=r["iso"],
                name=_name(r, lang),
                is_current_us_source=False,
                already_supplies_canada=r["already_supplies_canada"],
                ca_import_12m_cad=r["ca_import_12m_cad"],
                world_export_usd=r["world_export_usd"],
                tariff_treatment=r["tariff_treatment"],
                rate_applied=display_rate(r["rate_applied_text"], r["rate_applied_pct"]),
                rate_applied_pct=r["rate_applied_pct"],
                rate_mfn=display_rate(r["rate_mfn_text"], r["rate_mfn_pct"]),
                rate_mfn_pct=r["rate_mfn_pct"],
                fta=r["fta"],
                score=r["score"],
                score_reasons=list(r["score_reasons"]),
            )
        )
    return HsResponse(
        hs6=hs["hs6"],
        desc_en=hs["desc_en"],
        desc_fr=hs["desc_fr"],
        chapter=hs["chapter"],
        mfn=RateOut(text=mfn["text"], pct=mfn["pct"], display=display_rate(mfn["text"], mfn["pct"]))
        if mfn
        else None,
        surtax_us=SurtaxOut(**surtax, note=SURTAX_NOTE) if surtax else None,
        coverage=q.coverage(conn, hs6, start, end),
        window={"from": period_str(*start), "to": period_str(*end)},
        data_version=q.versions(conn),
        alternatives=alts,
    )


@router.get("/hs/{hs6}/country/{iso}", response_model=CountryResponse)
def country_detail(conn: Conn, hs6: str, iso: str, lang: Lang = "en"):
    hs = _hs_or_404(conn, hs6)
    country = q.get_country(conn, iso) if _ISO_RE.match(iso) else None
    if country is None:
        raise CountryNotFound(iso)
    months = _window(conn, 24)
    rank = q.rank_row(conn, hs6, iso)
    mfn = q.hs_mfn(conn, hs6)
    if rank:
        tariff = TariffOut(
            treatment=rank["tariff_treatment"],
            rate_applied=display_rate(rank["rate_applied_text"], rank["rate_applied_pct"]),
            rate_applied_pct=rank["rate_applied_pct"],
            rate_mfn=display_rate(rank["rate_mfn_text"], rank["rate_mfn_pct"]),
            rate_mfn_pct=rank["rate_mfn_pct"],
            fta=rank["fta"],
        )
    else:
        tariff = TariffOut(
            treatment=None,
            rate_applied=None,
            rate_applied_pct=None,
            rate_mfn=display_rate(mfn["text"], mfn["pct"]) if mfn else None,
            rate_mfn_pct=mfn["pct"] if mfn else None,
            fta=country["fta"],
        )
    world = q.world_export_for(conn, hs6, iso)
    return CountryResponse(
        hs6=hs["hs6"],
        desc_en=hs["desc_en"],
        desc_fr=hs["desc_fr"],
        country=CountryOut(
            iso=iso,
            name=_name(country, lang),
            treatments=list(country["treatments"]),
            fta=country["fta"],
            is_current_us_source=iso == USA,
        ),
        imports=[ImportPoint(**p) for p in q.import_series(conn, hs6, iso, months)],
        world_export=WorldExportOut(**world) if world else None,
        tariff=tariff,
        rank=RankOut(score=rank["score"], score_reasons=list(rank["score_reasons"]))
        if rank
        else None,
        links=external_links(country["name_en"], iso, hs["desc_en"]),
        data_version=q.versions(conn),
    )


@router.get("/meta", response_model=MetaResponse)
def meta(conn: Conn):
    return MetaResponse(
        data_version=q.versions(conn), counts=q.counts(conn), loaded_at=q.loaded_at(conn)
    )


@router.get("/featured", response_model=FeaturedResponse)
def featured(conn: Conn):
    win = _window(conn, 12)
    start, end = (win[0], win[-1]) if win else ((0, 0), (0, 0))
    return FeaturedResponse(items=[FeaturedItem(**r) for r in q.featured(conn, start, end)])


@router.get("/sitemap", response_model=SitemapResponse)
def sitemap(conn: Conn):
    return SitemapResponse(hs6=q.sitemap_ids(conn))


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(request: Request):
    try:
        with request.app.state.pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        log.exception("readiness check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
