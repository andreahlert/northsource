"""Statistics Canada CIMT: Canadian imports by HS6 x partner x month."""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

import duckdb
import pandas as pd

from .countries import cimt_to_iso3
from .http import download
from .paths import Layout

log = logging.getLogger(__name__)

ZIP_URL = "https://www150.statcan.gc.ca/n1/pub/71-607-x/2021004/zip/CIMT-CICM_Imp_{year}.zip"
ACTIVE = "999912"
_CTY_RE = re.compile(r"^(\S+)\s+(\d+)\s+(\d{6})\s+(\d{6})\s+(.*?)\s{2,}(.*?)\s{2,}ODPF")


def year_folder(layout: Layout, year: int) -> Path:
    return layout.raw("cimt") / str(year) / f"CIMT-CICM_Imp_{year}"


def fetch_cimt(layout: Layout) -> list[Path]:
    folders = []
    for year in (layout.period.previous_year, layout.period.year):
        zip_path = layout.raw("cimt") / f"CIMT-CICM_Imp_{year}.zip"
        download(ZIP_URL.format(year=year), zip_path, timeout=600)
        folder = year_folder(layout, year)
        if not folder.exists():
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(folder.parent)
        folders.append(folder)
    return folders


def parse_hs6_desc(text: str) -> pd.DataFrame:
    rows = []
    for line in text.splitlines():
        if len(line) < 112 or line[18:24] != ACTIVE:
            continue
        code = line[0:6]
        rows.append(
            {
                "hs6": code,
                "desc_en": line[29:112].strip(),
                "desc_fr": line[112:195].strip(),
                "chapter": code[:2],
            }
        )
    df = pd.DataFrame(rows, columns=["hs6", "desc_en", "desc_fr", "chapter"])
    return df.drop_duplicates("hs6", keep="last").sort_values("hs6").reset_index(drop=True)


def parse_cty_desc(text: str) -> pd.DataFrame:
    rows = []
    for line in text.splitlines():
        m = _CTY_RE.match(line)
        if not m or m.group(4) != ACTIVE:
            continue
        code = m.group(1)
        rows.append(
            {
                "cimt_code": code,
                "iso": cimt_to_iso3(code),
                "name_en": m.group(5).strip(),
                "name_fr": m.group(6).strip(),
            }
        )
    # dtype=object keeps unmapped codes as Python None instead of pandas 3.0's
    # default string dtype, which would coerce None to NaN.
    df = pd.DataFrame(rows, columns=["cimt_code", "iso", "name_en", "name_fr"], dtype=object)
    return df.drop_duplicates("cimt_code", keep="last").reset_index(drop=True)


def _csv_list(paths: list[Path]) -> str:
    return "[" + ", ".join(f"'{p.as_posix()}'" for p in paths) + "]"


def aggregate_imports(hs6_csvs: list[Path]) -> pd.DataFrame:
    """Sum province/state rows to national level per month x HS6 x CIMT country code."""
    q = f"""
        SELECT hs6,
               country AS cimt_code,
               CAST(ym // 100 AS INTEGER) AS year,
               CAST(ym % 100 AS INTEGER) AS month,
               CAST(SUM(value) AS BIGINT) AS value_cad
        FROM read_csv({_csv_list(hs6_csvs)}, header=true,
                      names=['ym','hs6','country','province','state','value','quantity','uom'],
                      types={{'ym':'BIGINT','hs6':'VARCHAR','country':'VARCHAR','province':'VARCHAR',
                             'state':'VARCHAR','value':'BIGINT','quantity':'BIGINT','uom':'VARCHAR'}},
                      union_by_name=false)
        GROUP BY 1, 2, 3, 4
        ORDER BY 1, 2, 3, 4
    """
    return duckdb.sql(q).df()


def monthly_totals(hs6_csvs: list[Path], hs2_csvs: list[Path]) -> pd.DataFrame:
    q = f"""
        WITH h6 AS (
            SELECT ym, SUM(value) AS hs6_total
            FROM read_csv({_csv_list(hs6_csvs)}, header=true,
                          names=['ym','hs6','country','province','state','value','quantity','uom'],
                          types={{'ym':'BIGINT','hs6':'VARCHAR','country':'VARCHAR','province':'VARCHAR',
                                 'state':'VARCHAR','value':'BIGINT','quantity':'BIGINT','uom':'VARCHAR'}})
            GROUP BY ym),
        h2 AS (
            SELECT ym, SUM(value) AS hs2_total
            FROM read_csv({_csv_list(hs2_csvs)}, header=true,
                          names=['ym','hs2','country','province','state','value'],
                          types={{'ym':'BIGINT','hs2':'VARCHAR','country':'VARCHAR','province':'VARCHAR',
                                 'state':'VARCHAR','value':'BIGINT'}})
            GROUP BY ym)
        SELECT CAST(h6.ym // 100 AS INTEGER) AS year, CAST(h6.ym % 100 AS INTEGER) AS month,
               CAST(h6.hs6_total AS BIGINT) AS hs6_total, CAST(h2.hs2_total AS BIGINT) AS hs2_total
        FROM h6 FULL OUTER JOIN h2 USING (ym)
        ORDER BY 1, 2
    """
    return duckdb.sql(q).df()


def parse_cimt(layout: Layout) -> None:
    folders = [
        year_folder(layout, layout.period.previous_year),
        year_folder(layout, layout.period.year),
    ]
    folders = [f for f in folders if f.exists()]
    if not folders:
        raise FileNotFoundError("no CIMT year folder found, run fetch first")
    hs6_csvs = [next(f.glob("ODPFN015_*N.csv")) for f in folders]
    hs2_csvs = [next(f.glob("ODPFN022_*N.csv")) for f in folders]
    latest = folders[-1]
    st = layout.staging()

    hs_code = parse_hs6_desc((latest / "ODPF_3_HS6MDesc.TXT").read_text(encoding="latin-1"))
    hs_code.to_parquet(st / "hs_code.parquet", index=False)

    country = parse_cty_desc((latest / "ODPF_6_CtyDesc.TXT").read_text(encoding="latin-1"))
    country.to_parquet(st / "cimt_country.parquet", index=False)

    imports = aggregate_imports(hs6_csvs)
    imports["partner_iso"] = imports["cimt_code"].map(cimt_to_iso3)
    dropped = imports["partner_iso"].isna().sum()
    log.info("ca_import: %d rows, %d dropped (no ISO3)", len(imports), dropped)
    ca_import = imports.dropna(subset=["partner_iso"])[
        ["hs6", "partner_iso", "year", "month", "value_cad"]
    ]
    ca_import.to_parquet(st / "ca_import.parquet", index=False)

    monthly_totals(hs6_csvs, hs2_csvs).to_parquet(st / "cimt_totals.parquet", index=False)
