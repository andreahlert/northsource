"""Postgres container seeded with a small, fully known dataset."""

from __future__ import annotations

import os
from pathlib import Path

import docker.errors
import psycopg
import pytest
from psycopg.types.json import Jsonb

pytest.importorskip("testcontainers.postgres")
from testcontainers.postgres import PostgresContainer

SCHEMA = (
    Path(__file__).resolve().parents[2] / "pipeline" / "src" / "northsource_pipeline" / "schema.sql"
)

NOTE = "25% surtax on US-origin goods that do not qualify under CUSMA"

HS = [
    (
        "040610",
        "Cheese, fresh, unripened or uncured, including whey cheese and curd",
        "Fromage, frais, non affinés, le fromage de lactosérum et caillebotte",
        "04",
    ),
    (
        "040620",
        "Cheese, grated or powdered, of all kinds",
        "Fromage râpé ou en poudre, de tous types",
        "04",
    ),
    ("720610", "Iron and non-alloy steel in ingots", "Fer et aciers non alliés en lingots", "72"),
    (
        "847130",
        "Portable digital automatic data processing machines, weight <= 10 kg",
        "Machines automatiques de traitement de l'information portatives, <= 10 kg",
        "84",
    ),
]
COUNTRIES = [
    ("USA", "United States of America", "États-Unis d'Amérique", "US", ["UST"], "CUSMA"),
    ("FRA", "France", "France", "FR", ["CEUT"], "CETA"),
    ("DEU", "Germany", "Allemagne", "DE", ["CEUT"], "CETA"),
    ("CHN", "China", "Chine", "CN", [], None),
    ("MEX", "Mexico", "Mexique", "MX", ["MXT", "CPTPT"], "CUSMA"),
    ("NLD", "Netherlands", "Pays-Bas", "NL", ["CEUT"], "CETA"),
]
PREF_CHEESE = {"CEUT": {"text": "Free", "pct": 0.0}, "GPT": {"text": "3.32¢/kg", "pct": None}}
TARIFF = [
    ("04061010", "040610", "3.32¢/kg", None, PREF_CHEESE, None, None),
    ("04061090", "040610", "245.5% but not less than $4.52/kg", None, {}, None, None),
    ("04062000", "040620", "3.32¢/kg", None, PREF_CHEESE, None, None),
    ("72061000", "720610", "Free", 0.0, {}, 25.0, "SOR/2025-95"),
    ("84713000", "847130", "Free", 0.0, {}, None, None),
]
MONTHS_24 = (
    [(2024, m) for m in range(7, 13)]
    + [(2025, m) for m in range(1, 13)]
    + [(2026, m) for m in range(1, 7)]
)
MONTHS_12 = MONTHS_24[-12:]
IMPORTS = (
    [("040610", "FRA", y, m, 900_000) for y, m in MONTHS_24]
    + [("040610", "USA", y, m, 3_000_000) for y, m in MONTHS_24]
    + [("040610", "CHN", y, m, 1_500_000) for y, m in MONTHS_12]
    + [("720610", "USA", y, m, 5_000_000) for y, m in MONTHS_12]
    + [("720610", "CHN", y, m, 4_000_000) for y, m in MONTHS_12]
)
WORLD = [
    ("040610", "DEU", 2025, 2.4e9),
    ("040610", "FRA", 2025, 1.5e9),
    ("040610", "NLD", 2025, 1.2e9),
    ("040610", "USA", 2025, 1.0e9),
    ("720610", "CHN", 2025, 5e8),
    ("847130", "CHN", 2025, 9e10),
    ("847130", "MEX", 2025, 8e9),
    ("847130", "USA", 2025, 4e9),
]
RANK = [
    # hs6, iso, score, reasons, supplies, ca12, world, treatment, applied_text, applied_pct, mfn_text, mfn_pct, fta, coverage
    (
        "040610",
        "FRA",
        95,
        ["supplies Canada", "FTA 0%", "top-10 world exporter"],
        True,
        10_800_000,
        1.5e9,
        "CEUT",
        "Free",
        0.0,
        "3.32¢/kg",
        None,
        "CETA",
        "canada",
    ),
    (
        "040610",
        "CHN",
        70,
        ["supplies Canada"],
        True,
        18_000_000,
        None,
        "MFN",
        "3.32¢/kg",
        None,
        "3.32¢/kg",
        None,
        None,
        "canada",
    ),
    (
        "040610",
        "DEU",
        62,
        ["FTA 0%", "top-10 world exporter"],
        False,
        0,
        2.4e9,
        "CEUT",
        "Free",
        0.0,
        "3.32¢/kg",
        None,
        "CETA",
        "canada",
    ),
    (
        "040610",
        "NLD",
        55,
        ["FTA 0%", "top-10 world exporter"],
        False,
        0,
        1.2e9,
        "CEUT",
        "Free",
        0.0,
        "3.32¢/kg",
        None,
        "CETA",
        "canada",
    ),
    (
        "720610",
        "CHN",
        100,
        ["supplies Canada", "duty free", "top-10 world exporter"],
        True,
        48_000_000,
        5e8,
        "MFN",
        "Free",
        0.0,
        "Free",
        0.0,
        None,
        "canada",
    ),
    (
        "847130",
        "CHN",
        60,
        ["duty free", "top-10 world exporter"],
        False,
        0,
        9e10,
        "MFN",
        "Free",
        0.0,
        "Free",
        0.0,
        None,
        "world_only",
    ),
    (
        "847130",
        "MEX",
        50,
        ["duty free", "top-10 world exporter"],
        False,
        0,
        8e9,
        "MFN",
        "Free",
        0.0,
        "Free",
        0.0,
        "CUSMA",
        "world_only",
    ),
]
VERSIONS = [
    ("cimt", "2026-06"),
    ("cbsa", "2026"),
    ("comtrade", "2025"),
    ("surtax", "SOR/2025-95;SOR/2025-118"),
    ("pipeline", "2026-08"),
]


def seed(url: str) -> None:
    with psycopg.connect(url) as conn:
        conn.execute(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "TRUNCATE hs_code, country, tariff_line, ca_import, world_export, alternative_rank, data_version"
        )
        conn.cursor().executemany(
            "INSERT INTO hs_code (hs6, desc_en, desc_fr, chapter) VALUES (%s, %s, %s, %s)", HS
        )
        conn.cursor().executemany(
            "INSERT INTO country (iso, name_en, name_fr, cimt_code, treatments, fta) VALUES (%s, %s, %s, %s, %s, %s)",
            COUNTRIES,
        )
        conn.cursor().executemany(
            "INSERT INTO tariff_line (hs8, hs6, mfn_text, mfn_pct, pref, surtax_us_pct, surtax_source) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(a, b, c, d, Jsonb(e), f, g) for a, b, c, d, e, f, g in TARIFF],
        )
        conn.cursor().executemany(
            "INSERT INTO ca_import (hs6, partner_iso, year, month, value_cad) VALUES (%s, %s, %s, %s, %s)",
            IMPORTS,
        )
        conn.cursor().executemany(
            "INSERT INTO world_export (hs6, reporter_iso, year, value_usd) VALUES (%s, %s, %s, %s)",
            WORLD,
        )
        conn.cursor().executemany(
            "INSERT INTO alternative_rank (hs6, iso, score, score_reasons, already_supplies_canada, ca_import_12m_cad, "
            "world_export_usd, tariff_treatment, rate_applied_text, rate_applied_pct, rate_mfn_text, rate_mfn_pct, fta, coverage) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            RANK,
        )
        conn.cursor().executemany(
            "INSERT INTO data_version (source, period, loaded_at) VALUES (%s, %s, '2026-08-24T12:00:00+00:00')",
            VERSIONS,
        )
        conn.commit()


@pytest.fixture(scope="module")
def database_url():
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
    except (OSError, RuntimeError, docker.errors.DockerException) as exc:
        if os.environ.get("REQUIRE_DOCKER"):
            raise
        pytest.skip(f"Docker unavailable: {exc}")
    url = container.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
    seed(url)
    yield url
    container.stop()


@pytest.fixture(scope="module")
def app(database_url):
    from northsource_api.main import create_app

    from northsource_api.config import Settings

    return create_app(Settings(database_url=database_url, cors_origins="http://localhost:3000"))


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
