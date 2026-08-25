# northsource pipeline

Downloads official Canadian and UN trade data, computes supplier alternatives per HS6 and loads Postgres.

## Sources

| Source | What | URL pattern |
|---|---|---|
| StatCan CIMT | Canadian imports by HS6 x country x month (CAD) | `https://www150.statcan.gc.ca/n1/pub/71-607-x/2021004/zip/CIMT-CICM_Imp_{YYYY}.zip` |
| CBSA Customs Tariff | MFN and preferential rates per HS8, country treatments | `https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/{YYYY}/html/00/ch{NN}-eng.html` |
| Justice Laws | US surtax orders SOR/2025-95 and SOR/2025-118 | `https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-95/FullText.html` |
| UN Comtrade | World exports by HS6 x reporter, annual (USD) | `comtradeapicall` package |

## Usage

```bash
cd pipeline
uv sync
export DATABASE_URL=postgresql://user:pass@host:5432/northsource
export COMTRADE_KEY=...          # optional; without it Comtrade is fetched one HS6 per call
uv run northsource-pipeline run --period 2026-08
```

Stages can run alone: `fetch`, `parse`, `validate`, `rank`, `load`. Raw files land in `data/raw/{source}/{period}/` and are never re-downloaded. Staging Parquet lands in `data/staging/{period}/`.

Options: `--data-dir`, `--tariff-year` (default: period year), `--comtrade-year` (default: period year minus 1), `--comtrade-sleep` (seconds between keyless calls, default 1.0), `--skip-comtrade`.

## Tests

```bash
uv run pytest -v        # load tests need Docker (testcontainers)
uv run ruff check src tests
```

## Ranking

Per HS6, every country with Canadian imports in the last 12 months or a Comtrade export record is a candidate, except the United States. Score = 40 (supplies Canada) + 30 (applied tariff 0%) or 15 (preferential rate below MFN) + up to 30 (log volume relative to the largest candidate). Reasons are stored in `score_reasons`.

## Known Limitations

The volume component of the ranking score pools Canadian import values (CAD) and world export values (USD) on one log scale without currency conversion, so the score is ordinal, not a monetary comparison.
