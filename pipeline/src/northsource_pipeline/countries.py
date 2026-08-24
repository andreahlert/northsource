"""ISO 3166 mapping for CIMT codes and CBSA country names, and treatment -> FTA names."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pycountry

USA = "USA"

# CIMT partner codes that have no ISO3 or are not real countries.
CIMT_DROP: frozenset[str] = frozenset({"EA", "ZX", "ZZ"})
_CIMT_OVERRIDE: dict[str, str] = {"XK": "XKX"}

# CBSA country names that pycountry.countries.lookup() cannot resolve (verified 2026-08-24).
# Empty list = no ISO3 of its own (part of another entry), the row is ignored.
CBSA_ALIASES: dict[str, list[str]] = {
    "Ascension Island": ["SHN"],
    "Brunei": ["BRN"],
    "Burma": ["MMR"],
    "Canary Islands": [],
    "Cape Verde": ["CPV"],
    "Ceuta and Melilla": [],
    "Channel Islands": ["JEY", "GGY"],
    "Democratic Republic of Congo": ["COD"],
    "Falkland Islands": ["FLK"],
    "French Southern and Antartic Territories": ["ATF"],
    "Kosovo": ["XKX"],
    "Macedonia": ["MKD"],
    "Mariana Islands": ["MNP"],
    "Micronesia": ["FSM"],
    "New Caledonia and Dependencies": ["NCL"],
    "Russia": ["RUS"],
    "Saint Helena and Dependencies": ["SHN"],
    "Saint Martin": ["MAF"],
    "Sint Maarten": ["SXM"],
    "Swaziland": ["SWZ"],
    "Tokelau Islands": ["TKL"],
    "Tristan Da Cunha": ["SHN"],
    "Turkey": ["TUR"],
    "Vatican (Holy See)": ["VAT"],
    "Virgin Islands, U.S.A.": ["VIR"],
}

# Tariff treatment code -> agreement name shown to users. Unilateral preferences have no entry.
TREATMENT_FTA: dict[str, str] = {
    "UST": "CUSMA",
    "MXT": "CUSMA",
    "CEUT": "CETA",
    "CPTPT": "CPTPP",
    "UKT": "Canada-UK TCA",
    "KRT": "CKFTA",
    "CT": "CCFTA",
    "COLT": "CCoFTA",
    "PT": "CPFTA",
    "PAT": "CPaFTA",
    "HNT": "CHFTA",
    "JT": "CJFTA",
    "CIAT": "CIFTA",
    "UAT": "CUFTA",
    "CRT": "CCRFTA",
    "IT": "CEFTA",
    "NT": "CEFTA",
    "SLT": "CEFTA",
}


def cimt_to_iso3(code: str) -> str | None:
    if code in CIMT_DROP:
        return None
    if code in _CIMT_OVERRIDE:
        return _CIMT_OVERRIDE[code]
    c = pycountry.countries.get(alpha_2=code)
    return c.alpha_3 if c else None


def cimt_unmapped(codes: Iterable[str]) -> list[str]:
    return sorted({c for c in codes if c not in CIMT_DROP and cimt_to_iso3(c) is None})


def cbsa_name_to_iso3(name: str) -> list[str]:
    name = " ".join(name.split())
    if name in CBSA_ALIASES:
        return list(CBSA_ALIASES[name])
    try:
        return [pycountry.countries.lookup(name).alpha_3]
    except LookupError:
        return []


def fta_for(treatments: Sequence[str]) -> str | None:
    for code in treatments:
        if code in TREATMENT_FTA:
            return TREATMENT_FTA[code]
    return None
