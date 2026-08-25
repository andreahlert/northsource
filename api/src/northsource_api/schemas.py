"""Response models. Field names are the public contract used by the web app."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SearchItem(BaseModel):
    hs6: str
    desc: str
    chapter: str


class SearchResponse(BaseModel):
    query: str
    lang: str
    results: list[SearchItem]


class RateOut(BaseModel):
    text: str
    pct: float | None
    display: str


class SurtaxOut(BaseModel):
    pct: float
    source: str
    hs8: list[str]
    note: str


class AlternativeOut(BaseModel):
    iso: str
    name: str
    is_current_us_source: bool
    already_supplies_canada: bool
    ca_import_12m_cad: int
    world_export_usd: float | None
    tariff_treatment: str | None
    rate_applied: str | None
    rate_applied_pct: float | None
    rate_mfn: str | None
    rate_mfn_pct: float | None
    fta: str | None
    score: int | None
    score_reasons: list[str]


class HsResponse(BaseModel):
    hs6: str
    desc_en: str
    desc_fr: str
    chapter: str
    mfn: RateOut | None
    surtax_us: SurtaxOut | None
    coverage: str
    window: dict[str, str]
    data_version: dict[str, str]
    alternatives: list[AlternativeOut]


class CountryOut(BaseModel):
    iso: str
    name: str
    treatments: list[str]
    fta: str | None
    is_current_us_source: bool


class ImportPoint(BaseModel):
    year: int
    month: int
    value_cad: int


class WorldExportOut(BaseModel):
    year: int
    value_usd: float | None


class TariffOut(BaseModel):
    treatment: str | None
    rate_applied: str | None
    rate_applied_pct: float | None
    rate_mfn: str | None
    rate_mfn_pct: float | None
    fta: str | None


class RankOut(BaseModel):
    score: int
    score_reasons: list[str]


class CountryResponse(BaseModel):
    hs6: str
    desc_en: str
    desc_fr: str
    country: CountryOut
    imports: list[ImportPoint]
    world_export: WorldExportOut | None
    tariff: TariffOut
    rank: RankOut | None
    links: dict[str, str]
    data_version: dict[str, str]


class MetaResponse(BaseModel):
    data_version: dict[str, str]
    counts: dict[str, int]
    loaded_at: datetime | None


class FeaturedItem(BaseModel):
    hs6: str
    desc: str
    surtax_us_pct: float | None
    ca_import_12m_cad: int


class FeaturedResponse(BaseModel):
    items: list[FeaturedItem]


class SitemapResponse(BaseModel):
    hs6: list[str]
