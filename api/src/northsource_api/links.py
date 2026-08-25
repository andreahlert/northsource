"""Links to external supplier directories, pre-filtered by HS6 keyword and country."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]*")


def keyword_for(desc_en: str) -> str:
    words = _WORD_RE.findall(desc_en)
    return " ".join(w.lower() for w in words[:3])


def external_links(country_name: str, iso: str, desc_en: str) -> dict[str, str]:
    kw = quote_plus(keyword_for(desc_en))
    name = quote_plus(country_name)
    return {
        "tcs": f"https://www.tradecommissioner.gc.ca/search-recherche.aspx?lang=eng&q={name}",
        "kompass": f"https://www.kompass.com/en/searchCompanies?text={kw}&country={iso}",
        "cti": f"https://www.ctidirectory.com/search/?keyword={kw}",
        "frasers": f"https://www.frasers.com/search?q={kw}",
    }
