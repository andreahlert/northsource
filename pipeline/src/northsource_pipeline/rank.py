"""alternative_rank: deterministic scoring of candidate supplier countries per HS6."""

from __future__ import annotations

import logging
import math

import pandas as pd

from .countries import TREATMENT_FTA, USA
from .paths import Layout
from .rates import Rate, pref_from_json

log = logging.getLogger(__name__)

COLUMNS = [
    "hs6",
    "iso",
    "score",
    "score_reasons",
    "already_supplies_canada",
    "ca_import_12m_cad",
    "world_export_usd",
    "tariff_treatment",
    "rate_applied_text",
    "rate_applied_pct",
    "rate_mfn_text",
    "rate_mfn_pct",
    "fta",
    "coverage",
]


def window(ca_import: pd.DataFrame, months: int) -> list[tuple[int, int]]:
    if ca_import.empty:
        return []
    last = int((ca_import["year"] * 100 + ca_import["month"]).max())
    year, month = last // 100, last % 100
    out = []
    for _ in range(months):
        out.append((year, month))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return list(reversed(out))


def _num(x) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def hs6_tariff(tariff_line: pd.DataFrame) -> dict[str, dict]:
    out: dict[str, dict] = {}
    df = tariff_line.sort_values("hs8")
    for hs6, group in df.groupby("hs6", sort=False):
        numeric = group[group["mfn_pct"].notna()]
        row = numeric.sort_values("mfn_pct").iloc[0] if len(numeric) else group.iloc[0]
        out[hs6] = {
            "mfn_text": row["mfn_text"],
            "mfn_pct": _num(row["mfn_pct"]),
            "pref": pref_from_json(row["pref"]),
        }
    return out


def applied_rate(
    treatments, mfn_text: str, mfn_pct: float | None, pref: dict[str, Rate]
) -> tuple[str, str, float | None]:
    """Lowest numeric preferential rate among the country's treatments, else MFN."""
    best: tuple[str, str, float | None] | None = None
    for code in treatments:
        rate = pref.get(code)
        if rate is None:
            continue
        if (
            rate.pct is not None and (best is None or best[2] is None or rate.pct < best[2])
        ) or best is None:
            best = (code, rate.text, rate.pct)
    if best is None:
        return ("MFN", mfn_text, mfn_pct)
    if best[2] is None and mfn_pct is not None:
        return ("MFN", mfn_text, mfn_pct)
    if best[2] is not None and mfn_pct is not None and best[2] > mfn_pct:
        return ("MFN", mfn_text, mfn_pct)
    return best


def rank(
    hs_code: pd.DataFrame,
    ca_import: pd.DataFrame,
    world_export: pd.DataFrame,
    tariff_line: pd.DataFrame,
    country: pd.DataFrame,
    *,
    months: int = 12,
) -> pd.DataFrame:
    known = set(hs_code["hs6"])
    win = set(window(ca_import, months))
    in_win = ca_import[[(y, m) in win for y, m in zip(ca_import["year"], ca_import["month"])]]
    ca12 = in_win.groupby(["hs6", "partner_iso"], as_index=False)["value_cad"].sum()
    ca12 = ca12.rename(columns={"partner_iso": "iso", "value_cad": "ca_import_12m_cad"})
    canada_hs6 = set(ca12["hs6"])

    we = world_export.rename(columns={"reporter_iso": "iso", "value_usd": "world_export_usd"})
    if len(we):
        we = we[we["year"] == we["year"].max()]
    we = we[["hs6", "iso", "world_export_usd"]]
    top10: set[tuple[str, str]] = set()
    for hs6, g in we.groupby("hs6"):
        for iso in g.sort_values("world_export_usd", ascending=False)["iso"].head(10):
            top10.add((hs6, iso))

    cand = ca12.merge(we, on=["hs6", "iso"], how="outer")
    cand = cand[cand["hs6"].isin(known) & (cand["iso"] != USA)].copy()
    cand["ca_import_12m_cad"] = cand["ca_import_12m_cad"].fillna(0).astype("int64")

    treatments = {r["iso"]: list(r["treatments"]) for _, r in country.iterrows()}
    tariffs = hs6_tariff(tariff_line)

    rows = []
    for hs6, group in cand.groupby("hs6"):
        vols = {}
        for _, r in group.iterrows():
            v = (
                r["ca_import_12m_cad"]
                if r["ca_import_12m_cad"] > 0
                else _num(r["world_export_usd"]) or 0.0
            )
            vols[r["iso"]] = float(v)
        vmax = max(vols.values(), default=0.0)
        t = tariffs.get(hs6, {"mfn_text": "", "mfn_pct": None, "pref": {}})
        coverage = "canada" if hs6 in canada_hs6 else "world_only"
        for _, r in group.iterrows():
            iso = r["iso"]
            reasons: list[str] = []
            score = 0
            supplies = r["ca_import_12m_cad"] > 0
            if supplies:
                score += 40
                reasons.append("supplies Canada")
            code, text, pct = applied_rate(
                treatments.get(iso, []), t["mfn_text"], t["mfn_pct"], t["pref"]
            )
            fta = TREATMENT_FTA.get(code)
            if pct == 0.0:
                score += 30
                reasons.append("FTA 0%" if fta else "duty free")
            elif pct is not None and t["mfn_pct"] is not None and 0 < pct < t["mfn_pct"]:
                score += 15
                reasons.append("preferential rate")
            v = vols[iso]
            if vmax > 0 and v > 0:
                score += round(30 * math.log1p(v) / math.log1p(vmax))
            if (hs6, iso) in top10:
                reasons.append("top-10 world exporter")
            rows.append(
                {
                    "hs6": hs6,
                    "iso": iso,
                    "score": int(score),
                    "score_reasons": reasons,
                    "already_supplies_canada": bool(supplies),
                    "ca_import_12m_cad": int(r["ca_import_12m_cad"]),
                    "world_export_usd": _num(r["world_export_usd"]),
                    "tariff_treatment": code,
                    "rate_applied_text": text,
                    "rate_applied_pct": pct,
                    "rate_mfn_text": t["mfn_text"],
                    "rate_mfn_pct": t["mfn_pct"],
                    "fta": fta,
                    "coverage": coverage,
                }
            )
    df = pd.DataFrame(rows, columns=COLUMNS)
    df = df.sort_values(["hs6", "score", "iso"], ascending=[True, False, True]).reset_index(
        drop=True
    )
    for col in ("world_export_usd", "rate_applied_pct", "rate_mfn_pct"):
        df[col] = df[col].astype("float64")
    df["fta"] = df["fta"].astype(object).where(df["fta"].notna(), None)
    return df


def write_rank(layout: Layout) -> None:
    st = layout.staging()
    df = rank(
        pd.read_parquet(st / "hs_code.parquet"),
        pd.read_parquet(st / "ca_import.parquet"),
        pd.read_parquet(st / "world_export.parquet"),
        pd.read_parquet(st / "tariff_line.parquet"),
        pd.read_parquet(st / "country.parquet"),
    )
    df.to_parquet(st / "alternative_rank.parquet", index=False)
    log.info("alternative_rank: %d rows, %d HS6", len(df), df["hs6"].nunique())
