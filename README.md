# northsource

Open data tool for Canadian importers: for any product (HS6 code), which countries other than the United States can supply it, ranked by whether they already sell to Canada, the tariff Canada applies under its trade agreements, and export volume.

Monorepo:

- `pipeline/` Python: StatCan CIMT, CBSA Customs Tariff, surtax orders, UN Comtrade to Postgres. See `pipeline/README.md`.
- `api/` FastAPI read-only API (see api/README.md when present).
- `web/` Next.js frontend (see web/README.md when present).

Data sources are official and public: Statistics Canada, Canada Border Services Agency, Justice Laws Canada, UN Comtrade. MIT licensed.
