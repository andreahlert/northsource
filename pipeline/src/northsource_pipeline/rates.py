"""Parsing of CBSA Customs Tariff rate strings."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

TREATMENT_CODES: frozenset[str] = frozenset(
    {
        "AUT", "CCCT", "CEUT", "CIAT", "COLT", "CPTPT", "CRT", "CT", "GPT", "HNT", "IT", "JT",
        "KRT", "LDCT", "MXT", "NT", "NZT", "PAT", "PT", "SLT", "UAT", "UKT", "UST",
    }
)

_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)%")
# Longest codes first so CPTPT is not split into CT + ...; \b keeps IT/NT/CT from matching inside words.
_CODE_RE = re.compile(r"\b(" + "|".join(sorted(TREATMENT_CODES, key=len, reverse=True)) + r")\b")


@dataclass(frozen=True)
class Rate:
    text: str
    pct: float | None


def parse_rate(text: str) -> Rate:
    t = " ".join(text.split())
    if t == "Free":
        return Rate(t, 0.0)
    m = _PCT_RE.fullmatch(t)
    if m:
        return Rate(t, float(m.group(1)))
    return Rate(t, None)


def parse_pref(text: str) -> dict[str, Rate]:
    """Parse the 'Applicable Preferential Tariffs' cell.

    Grammar: a sequence of treatment codes, each group of codes followed by one rate.
    'CCCT, LDCT, UST: Free GPT 7.5%' -> CCCT/LDCT/UST = Free, GPT = 7.5%.
    """
    t = " ".join(text.split())
    result: dict[str, Rate] = {}
    pending: list[str] = []
    for token in _CODE_RE.split(t):
        if token in TREATMENT_CODES:
            pending.append(token)
            continue
        rate_text = token.strip(" ,:;")
        if not rate_text:
            continue
        rate = parse_rate(rate_text)
        for code in pending:
            result[code] = rate
        pending = []
    return result


def pref_to_json(pref: dict[str, Rate]) -> str:
    return json.dumps({k: {"text": v.text, "pct": v.pct} for k, v in pref.items()}, ensure_ascii=False)


def pref_from_json(text: str) -> dict[str, Rate]:
    return {k: Rate(v["text"], v["pct"]) for k, v in json.loads(text).items()}
