"""All SQL. Functions take a psycopg connection with dict_row and return plain data."""

from __future__ import annotations

from datetime import datetime

from psycopg import Connection

from .format import ym

DATA_TABLES = ["hs_code", "country", "tariff_line", "ca_import", "world_export", "alternative_rank"]


def _num(v):
    return None if v is None else float(v)


def latest_month(conn: Connection) -> tuple[int, int] | None:
    row = conn.execute(
        "SELECT year, month FROM ca_import ORDER BY year DESC, month DESC LIMIT 1"
    ).fetchone()
    return (row["year"], row["month"]) if row else None


def search_codes(conn: Connection, q: str, lang: str, limit: int = 20) -> list[dict]:
    desc = "desc_fr" if lang == "fr" else "desc_en"
    q = q.strip()
    if q.isdigit():
        rows = conn.execute(
            f"SELECT hs6, {desc} AS desc, chapter FROM hs_code WHERE hs6 LIKE %s ORDER BY hs6 LIMIT %s",
            (q + "%", limit),
        ).fetchall()
    else:
        vec, cfg = ("search_fr", "french") if lang == "fr" else ("search_en", "english")
        rows = conn.execute(
            f"SELECT hs6, {desc} AS desc, chapter, ts_rank({vec}, plainto_tsquery(%s, %s)) AS r "
            f"FROM hs_code WHERE {vec} @@ plainto_tsquery(%s, %s) ORDER BY r DESC, hs6 LIMIT %s",
            (cfg, q, cfg, q, limit),
        ).fetchall()
    return [{"hs6": r["hs6"], "desc": r["desc"], "chapter": r["chapter"]} for r in rows]


def get_hs(conn: Connection, hs6: str) -> dict | None:
    return conn.execute(
        "SELECT hs6, desc_en, desc_fr, chapter FROM hs_code WHERE hs6 = %s", (hs6,)
    ).fetchone()


def suggest(conn: Connection, hs6: str, n: int = 5) -> list[dict]:
    digits = "".join(ch for ch in hs6 if ch.isdigit())
    for length in range(min(len(digits), 5), 1, -1):
        rows = conn.execute(
            "SELECT hs6, desc_en AS desc FROM hs_code WHERE hs6 LIKE %s ORDER BY hs6 LIMIT %s",
            (digits[:length] + "%", n),
        ).fetchall()
        if rows:
            return [dict(r) for r in rows]
    return []


def hs_mfn(conn: Connection, hs6: str) -> dict | None:
    row = conn.execute(
        "SELECT mfn_text, mfn_pct FROM tariff_line WHERE hs6 = %s ORDER BY mfn_pct NULLS LAST, hs8 LIMIT 1",
        (hs6,),
    ).fetchone()
    return {"text": row["mfn_text"], "pct": _num(row["mfn_pct"])} if row else None


def hs_surtax(conn: Connection, hs6: str) -> dict | None:
    rows = conn.execute(
        "SELECT hs8, surtax_us_pct, surtax_source FROM tariff_line "
        "WHERE hs6 = %s AND surtax_us_pct IS NOT NULL ORDER BY hs8",
        (hs6,),
    ).fetchall()
    if not rows:
        return None
    return {
        "pct": _num(rows[0]["surtax_us_pct"]),
        "source": rows[0]["surtax_source"],
        "hs8": [r["hs8"] for r in rows],
    }


def alternatives(conn: Connection, hs6: str) -> list[dict]:
    rows = conn.execute(
        "SELECT r.*, c.name_en, c.name_fr FROM alternative_rank r JOIN country c ON c.iso = r.iso "
        "WHERE r.hs6 = %s ORDER BY r.score DESC, r.iso",
        (hs6,),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        for k in ("world_export_usd", "rate_applied_pct", "rate_mfn_pct"):
            d[k] = _num(d[k])
        out.append(d)
    return out


def us_summary(conn: Connection, hs6: str, start: tuple[int, int], end: tuple[int, int]) -> dict:
    cad = conn.execute(
        "SELECT COALESCE(SUM(value_cad), 0) AS v FROM ca_import WHERE hs6 = %s AND partner_iso = 'USA' "
        "AND year * 100 + month BETWEEN %s AND %s",
        (hs6, ym(*start), ym(*end)),
    ).fetchone()["v"]
    usd = conn.execute(
        "SELECT value_usd FROM world_export WHERE hs6 = %s AND reporter_iso = 'USA' ORDER BY year DESC LIMIT 1",
        (hs6,),
    ).fetchone()
    return {
        "ca_import_12m_cad": int(cad),
        "world_export_usd": _num(usd["value_usd"]) if usd else None,
    }


def coverage(conn: Connection, hs6: str, start: tuple[int, int], end: tuple[int, int]) -> str:
    row = conn.execute(
        "SELECT 1 FROM ca_import WHERE hs6 = %s AND year * 100 + month BETWEEN %s AND %s LIMIT 1",
        (hs6, ym(*start), ym(*end)),
    ).fetchone()
    return "canada" if row else "world_only"


def get_country(conn: Connection, iso: str) -> dict | None:
    return conn.execute(
        "SELECT iso, name_en, name_fr, cimt_code, treatments, fta FROM country WHERE iso = %s",
        (iso,),
    ).fetchone()


def import_series(
    conn: Connection, hs6: str, iso: str, months: list[tuple[int, int]]
) -> list[dict]:
    if not months:
        return []
    rows = conn.execute(
        "SELECT year, month, value_cad FROM ca_import WHERE hs6 = %s AND partner_iso = %s "
        "AND year * 100 + month BETWEEN %s AND %s",
        (hs6, iso, ym(*months[0]), ym(*months[-1])),
    ).fetchall()
    have = {(r["year"], r["month"]): int(r["value_cad"]) for r in rows}
    return [{"year": y, "month": m, "value_cad": have.get((y, m), 0)} for y, m in months]


def world_export_for(conn: Connection, hs6: str, iso: str) -> dict | None:
    row = conn.execute(
        "SELECT year, value_usd FROM world_export WHERE hs6 = %s AND reporter_iso = %s ORDER BY year DESC LIMIT 1",
        (hs6, iso),
    ).fetchone()
    return {"year": row["year"], "value_usd": _num(row["value_usd"])} if row else None


def rank_row(conn: Connection, hs6: str, iso: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM alternative_rank WHERE hs6 = %s AND iso = %s", (hs6, iso)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    for k in ("world_export_usd", "rate_applied_pct", "rate_mfn_pct"):
        d[k] = _num(d[k])
    return d


def versions(conn: Connection) -> dict[str, str]:
    return {
        r["source"]: r["period"]
        for r in conn.execute("SELECT source, period FROM data_version").fetchall()
    }


def loaded_at(conn: Connection) -> datetime | None:
    return conn.execute("SELECT max(loaded_at) AS t FROM data_version").fetchone()["t"]


def counts(conn: Connection) -> dict[str, int]:
    return {t: conn.execute(f"SELECT count(*) AS n FROM {t}").fetchone()["n"] for t in DATA_TABLES}


def featured(
    conn: Connection, start: tuple[int, int], end: tuple[int, int], n: int = 8
) -> list[dict]:
    rows = conn.execute(
        """
        SELECT h.hs6, h.desc_en AS desc, MIN(t.surtax_us_pct) AS surtax_us_pct,
               COALESCE((SELECT SUM(value_cad) FROM ca_import i WHERE i.hs6 = h.hs6 AND i.partner_iso = 'USA'
                         AND i.year * 100 + i.month BETWEEN %s AND %s), 0) AS ca_import_12m_cad
        FROM hs_code h JOIN tariff_line t ON t.hs6 = h.hs6
        WHERE t.surtax_us_pct IS NOT NULL
        GROUP BY h.hs6, h.desc_en
        ORDER BY ca_import_12m_cad DESC, h.hs6
        LIMIT %s
        """,
        (ym(*start), ym(*end), n),
    ).fetchall()
    return [
        {
            "hs6": r["hs6"],
            "desc": r["desc"],
            "surtax_us_pct": _num(r["surtax_us_pct"]),
            "ca_import_12m_cad": int(r["ca_import_12m_cad"]),
        }
        for r in rows
    ]


def sitemap_ids(conn: Connection) -> list[str]:
    return [
        r["hs6"]
        for r in conn.execute("SELECT DISTINCT hs6 FROM alternative_rank ORDER BY hs6").fetchall()
    ]
