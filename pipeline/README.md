# northsource pipeline

Downloads official Canadian and UN trade data, computes supplier alternatives per HS6 and loads Postgres.

## Sources

| Source | What | URL pattern |
|---|---|---|
| StatCan CIMT | Canadian imports by HS6 x country x month (CAD) | `https://www150.statcan.gc.ca/n1/pub/71-607-x/2021004/zip/CIMT-CICM_Imp_{YYYY}.zip` |
| CBSA Customs Tariff | MFN and preferential rates per HS8, country treatments | `https://www.cbsa-asfc.gc.ca/trade-commerce/tariff-tarif/{YYYY}/html/00/ch{NN}-eng.html` |
| Justice Laws | US surtax orders SOR/2025-95 and SOR/2025-118 | [SOR/2025-95](https://laws-lois.justice.gc.ca/eng/regulations/SOR-2025-95/FullText.html) |
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

## Schema changes

Every new column is added as `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` beside its `CREATE TABLE` in `schema.sql`, never by editing the `CREATE TABLE` statement alone. `load` runs `schema.sql` against every database on every run, including ones that already hold data from a previous version of the schema, so a change that only exists in the `CREATE TABLE` text is a no-op there and the following `COPY` fails with a missing column.

## Ranking

Per HS6, every country with Canadian imports in the last 12 months or a Comtrade export record is a candidate, except the United States. Score = 40 (supplies Canada) + 30 (applied tariff 0%) or 15 (preferential rate below MFN) + up to 30 (log volume relative to the largest candidate). Reasons are stored in `score_reasons`.

## Known Limitations

The volume component of the ranking score pools Canadian import values (CAD) and world export values (USD) on one log scale without currency conversion, so the score is ordinal, not a monetary comparison.

For tariff rate quota goods, chiefly dairy, poultry, eggs and margarine, the HS6 tariff rate is taken from the HS8 line with the lowest MFN rate. For these goods that is the within access commitment line, not the over access line that most commercial imports actually pay. For example HS 0406.10, fresh cheese, is reported at the within access rate even though the over access rate on 0406.10.90 is 245.5% but not less than $4.52/kg. Treat the tariff and preferential rates for these HS6 as the best case within a quota, not the rate a new importer without quota access would pay.
