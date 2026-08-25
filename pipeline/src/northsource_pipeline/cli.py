"""northsource-pipeline CLI: run | fetch | parse | validate | rank | load."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from .cbsa import fetch_cbsa
from .cimt import fetch_cimt, parse_hs6_desc, year_folder
from .comtrade import fetch_comtrade
from .load import load, versions_for
from .paths import DEFAULT_ROOT, Layout, Period
from .rank import write_rank
from .stages import run_parse
from .surtax import fetch_surtax
from .validate import ValidationError, validate

log = logging.getLogger("northsource_pipeline")

# Tests override this to shrink the surtax count windows; None = ORDERS defaults.
SURTAX_RANGES_OVERRIDE: dict[str, tuple[int, int]] | None = None


def active_hs6(layout: Layout) -> list[str]:
    folder = year_folder(layout, layout.period.year)
    if not folder.exists():
        folder = year_folder(layout, layout.period.previous_year)
    text = (folder / "ODPF_3_HS6MDesc.TXT").read_text(encoding="latin-1")
    return parse_hs6_desc(text)["hs6"].tolist()


def run_fetch(
    layout: Layout,
    *,
    tariff_year: int,
    comtrade_year: int,
    comtrade_key: str | None,
    comtrade_sleep: float,
    skip_comtrade: bool,
) -> None:
    fetch_cimt(layout)
    fetch_cbsa(layout, tariff_year=tariff_year)
    fetch_surtax(layout)
    if skip_comtrade:
        log.info("comtrade fetch skipped")
        return
    hs6 = active_hs6(layout)
    log.info("comtrade: %d HS6, key=%s", len(hs6), "yes" if comtrade_key else "no")
    fetch_comtrade(layout, hs6, key=comtrade_key, year=comtrade_year, sleep_s=comtrade_sleep)


def _period(text: str) -> Period:
    try:
        return Period.parse(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="northsource-pipeline")
    p.add_argument("stage", choices=["run", "fetch", "parse", "validate", "rank", "load"])
    p.add_argument("--period", required=True, type=_period, help="YYYY-MM")
    p.add_argument("--data-dir", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--tariff-year", type=int, default=None)
    p.add_argument("--comtrade-year", type=int, default=None)
    p.add_argument("--comtrade-sleep", type=float, default=1.0)
    p.add_argument("--skip-comtrade", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    layout = Layout(args.data_dir, args.period)
    tariff_year = args.tariff_year or args.period.year
    comtrade_year = args.comtrade_year or args.period.previous_year
    stages = ["fetch", "parse", "validate", "rank", "load"] if args.stage == "run" else [args.stage]

    if "load" in stages and not os.environ.get("DATABASE_URL"):
        log.error("DATABASE_URL is not set")
        return 2

    for stage in stages:
        log.info("stage %s period %s data-dir %s", stage, layout.period, layout.root)
        if stage == "fetch":
            run_fetch(
                layout,
                tariff_year=tariff_year,
                comtrade_year=comtrade_year,
                comtrade_key=os.environ.get("COMTRADE_KEY") or None,
                comtrade_sleep=args.comtrade_sleep,
                skip_comtrade=args.skip_comtrade,
            )
        elif stage == "parse":
            run_parse(layout)
        elif stage == "validate":
            try:
                validate(layout, surtax_ranges=SURTAX_RANGES_OVERRIDE)
            except ValidationError as exc:
                log.error("validation failed: %s", exc)
                return 1
        elif stage == "rank":
            write_rank(layout)
        elif stage == "load":
            counts = load(layout, os.environ["DATABASE_URL"], versions_for(layout))
            log.info("load done: %s", counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
