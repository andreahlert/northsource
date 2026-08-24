"""Generated raw-file fixtures: 4 HS6, 9 CIMT country codes, no network."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from northsource_pipeline.paths import Layout, Period

PERIOD = Period(2026, 8)

HS6_DESC = {
    "040610": ("KGM", "Cheese, fresh, unripened or uncured, including whey cheese and curd",
               "Fromage, frais, non affinés, le fromage de lactosérum et caillebotte"),
    "720610": ("KGM", "Iron and non-alloy steel in ingots", "Fer et aciers non alliés en lingots"),
    "870322": ("NMB", "Motor cars, spark-ignition engine, cylinder capacity 1,000 to 1,500 cc",
               "Voitures de tourisme, moteur à allumage par étincelles, 1 000 à 1 500 cm3"),
    "847130": ("NMB", "Portable digital automatic data processing machines, weight <= 10 kg",
               "Machines automatiques de traitement de l'information portatives, <= 10 kg"),
}

CTY = [  # code, num, name_en, name_fr
    ("US", "009", "United States of America", "États-Unis d'Amérique"),
    ("FR", "150", "France", "France"),
    ("DE", "155", "Germany", "Allemagne"),
    ("MX", "030", "Mexico", "Mexique"),
    ("CN", "580", "China", "Chine"),
    ("NL", "160", "Netherlands", "Pays-Bas"),
    ("JP", "560", "Japan", "Japon"),
    ("MM", "540", "Myanmar (Burma)", "Myanmar (Birmanie)"),
    ("ZX", "005", "Unknown or unspecified", "Inconnu ou non-precisé"),
]

# hs6 -> country -> list of (province, state, value) rows per month
CIMT_ROWS = {
    "040610": {
        "US": [("ON", "NY", 2_000_000), ("QC", "WI", 1_000_000)],
        "FR": [("QC", "", 900_000)],
        "DE": [("ON", "", 400_000)],
        "CN": [("BC", "", 1_500_000)],
        "ZX": [("ON", "", 10_000)],
    },
    "720610": {
        "US": [("ON", "PA", 5_000_000)],
        "DE": [("ON", "", 700_000)],
        "MX": [("ON", "", 2_000_000)],
        "CN": [("BC", "", 4_000_000)],
    },
    "870322": {
        "US": [("ON", "MI", 8_000_000)],
        "DE": [("ON", "", 6_000_000)],
        "MX": [("ON", "", 3_000_000)],
    },
}

MONTHS_2025 = [f"2025{m:02d}" for m in range(7, 13)]
MONTHS_2026 = [f"2026{m:02d}" for m in range(1, 7)]

COMTRADE = {  # hs6 -> list of (reporterISO, primaryValue USD)
    "040610": [("DEU", 2_400_000_000), ("FRA", 1_500_000_000), ("NLD", 1_200_000_000),
               ("USA", 1_000_000_000), ("S19", 5_000_000)],
    "720610": [("CHN", 500_000_000), ("DEU", 300_000_000)],
    "870322": [("JPN", 10_000_000_000), ("MEX", 3_000_000_000), ("DEU", 9_000_000_000)],
    "847130": [("CHN", 90_000_000_000), ("MEX", 8_000_000_000), ("USA", 4_000_000_000)],
}

CBSA_CHAPTERS = {
    "04": [
        ("04.06", "", "Cheese and curd.", "", "", ""),
        ("0406.10", "", "Fresh cheese", "", "", ""),
        ("0406.10.10", "00", "Within access commitment", "KGM", "3.32¢/kg",
         "CCCT, LDCT, UST, MXT, CIAT, CT, CRT, IT, NT, SLT, PT, COLT, JT, PAT, HNT, KRT, CEUT, UAT, CPTPT, UKT: Free GPT 3.32¢/kg"),
        ("0406.10.90", "00", "Over access commitment", "KGM", "245.5% but not less than $4.52/kg", ""),
    ],
    "72": [
        ("72.06", "", "Iron and non-alloy steel in ingots.", "", "", ""),
        ("7206.10", "", "Ingots", "", "", ""),
        ("7206.10.00", "00", "Ingots", "KGM", "Free", ""),
    ],
    "84": [
        ("8471.30", "", "Portable machines", "", "", ""),
        ("8471.30.00", "00", "Portable machines", "NMB", "Free", ""),
    ],
    "87": [
        ("8703.22", "", "Of a cylinder capacity exceeding 1,000 cc but not exceeding 1,500 cc", "", "", ""),
        ("8703.22.00", "00", "Of a cylinder capacity exceeding 1,000 cc but not exceeding 1,500 cc", "NMB", "6.1%",
         "CCCT, LDCT, UST, MXT, CIAT, CT, CRT, IT, NT, SLT, PT, COLT, JT, PAT, HNT, KRT, CEUT, UAT, CPTPT, UKT: Free AUT 6%,\nNZT 6%,\nGPT 6%"),
    ],
    "98": [
        ("9801.10.10", "00", "Conveyances", "", "Free", ""),
    ],
}

CBSA_COUNTRIES = [  # name, mfn, gpt, ldct, other
    ("Burma", "yes", "yes", "yes", ""),
    ("China", "yes", "no", "no", ""),
    ("France", "yes", "no", "no", "CEUT"),
    ("Germany", "yes", "no", "no", "CEUT"),
    ("Japan", "yes", "no", "no", "CPTPT"),
    ("Mexico", "yes", "no", "no", "MXT, CPTPT"),
    ("Netherlands", "yes", "no", "no", "CEUT"),
    ("United States of America", "yes", "no", "no", "UST"),
]

SURTAX_95_CODES = ["7206.10.00", "7601.10.00", "9801.10.10"]
SURTAX_118_CODES = ["8703.22.00", "9801.10.10"]


def hs6_desc_line(code: str, start: str, end: str, uom: str, en: str, fr: str) -> str:
    return f"{code:<6}     {start} {end} {uom:<3} {en:<83}{fr:<83}ODPFN"


def cty_desc_line(code: str, num: str, start: str, end: str, en: str, fr: str) -> str:
    return f"{code} {num:<3}     {start} {end} {en:<83}{fr:<83}ODPFN023_6  202606"


def _write_cimt_year(folder: Path, months: list[str]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    last = months[-1]
    hs6_lines = ["YearMonth/AnnéeMois,HS6,Country/Pays,Province,State/État,Value/Valeur,Quantity/Quantité,Unit of Measure/Unité de Mesure"]
    hs2: dict[tuple[str, str, str], int] = {}
    for ym in months:
        for hs6, per_country in CIMT_ROWS.items():
            for country, rows in per_country.items():
                for prov, state, value in rows:
                    hs6_lines.append(f'"{ym}","{hs6}","{country}","{prov}","{state}",{value},1,"KGM"')
                    key = (ym, hs6[:2], country)
                    hs2[key] = hs2.get(key, 0) + value
    (folder / f"ODPFN015_{last}N.csv").write_text("\n".join(hs6_lines) + "\n", encoding="utf-8")
    hs2_lines = ["YearMonth/AnnéeMois,HS2,Country/Pays,Province,State/État,Value/Valeur"]
    for (ym, ch, country), value in sorted(hs2.items()):
        hs2_lines.append(f'"{ym}","{ch}","{country}","ON","",{value}')
    (folder / f"ODPFN022_{last}N.csv").write_text("\n".join(hs2_lines) + "\n", encoding="utf-8")
    desc = [hs6_desc_line("040610", "198801", "199112", "KGM", "Cheese, fresh (old text)", "Fromage (ancien)")]
    for code, (uom, en, fr) in HS6_DESC.items():
        desc.append(hs6_desc_line(code, "199201", "999912", uom, en, fr))
    (folder / "ODPF_3_HS6MDesc.TXT").write_text("\r\n".join(desc) + "\r\n", encoding="latin-1")
    cty = [cty_desc_line("DE", "155", "197001", "199009", "West Germany", "Allemagne de l'Ouest")]
    for code, num, en, fr in CTY:
        cty.append(cty_desc_line(code, num, "196601", "999912", en, fr))
    (folder / "ODPF_6_CtyDesc.TXT").write_text("\r\n".join(cty) + "\r\n", encoding="latin-1")


def _chapter_html(rows: list[tuple[str, ...]]) -> str:
    head = "<tr><th>Tariff Item</th><th>SS</th><th>Description of Goods</th><th>Unit of Meas.</th><th>MFN Tariff</th><th>Applicable Preferential Tariffs</th></tr>"
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<html><body><h1>Chapter</h1><table>{head}{body}</table></body></html>"


def _countries_html() -> str:
    head = "<tr><th>Country Name</th><th>MFN</th><th>GPT</th><th>LDCT</th><th>Other</th></tr>"
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in CBSA_COUNTRIES)
    return f"<html><body><table>{head}{body}</table></body></html>"


def _surtax_html(title: str, codes: list[str]) -> str:
    items = "".join(f"<p class='TariffItem'>{c}</p>" for c in codes)
    return f"<html><body><h1>{title}</h1><p>Section 2 applies a surtax of 25%.</p>{items}</body></html>"


def build_raw_tree(root: Path) -> Layout:
    layout = Layout(root, PERIOD)
    cimt = layout.raw("cimt")
    _write_cimt_year(cimt / "2025" / "CIMT-CICM_Imp_2025", MONTHS_2025)
    _write_cimt_year(cimt / "2026" / "CIMT-CICM_Imp_2026", MONTHS_2026)
    cbsa = layout.raw("cbsa")
    for nn in range(1, 100):
        rows = CBSA_CHAPTERS.get(f"{nn:02d}")
        html = _chapter_html(rows) if rows else "<html><body><p>Reserved</p></body></html>"
        (cbsa / f"ch{nn:02d}-eng.html").write_text(html, encoding="utf-8")
    (cbsa / "countries-pays-eng.html").write_text(_countries_html(), encoding="utf-8")
    surtax = layout.raw("surtax")
    (surtax / "SOR-2025-95.html").write_text(_surtax_html("Steel and Aluminum", SURTAX_95_CODES), encoding="utf-8")
    (surtax / "SOR-2025-118.html").write_text(_surtax_html("Motor Vehicles", SURTAX_118_CODES), encoding="utf-8")
    comtrade = layout.raw("comtrade")
    for hs6, rows in COMTRADE.items():
        records = [
            {"reporterISO": iso, "reporterDesc": iso, "cmdCode": hs6, "refYear": 2025,
             "flowCode": "X", "partnerISO": "W00", "primaryValue": value}
            for iso, value in rows
        ]
        (comtrade / f"{hs6}.json").write_text(json.dumps(records), encoding="utf-8")
    return layout


@pytest.fixture
def layout(tmp_path: Path) -> Layout:
    return build_raw_tree(tmp_path)
