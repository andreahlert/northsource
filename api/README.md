# northsource API

Read-only FastAPI service over the tables loaded by `pipeline/`.

## Run locally

```bash
cd api
uv sync
cp .env.example .env    # set DATABASE_URL
uv run uvicorn northsource_api.main:create_app --factory --reload
```

Open http://localhost:8000/docs for the OpenAPI UI.

## Routes

| Route | Purpose |
|---|---|
| `GET /search?q=&lang=en\|fr` | Up to 20 HS6 by keyword (full text) or code prefix (digits) |
| `GET /hs/{hs6}?lang=` | Description, MFN, US surtax, ranked alternatives (US first, flagged) |
| `GET /hs/{hs6}/country/{iso}?lang=` | 24-month import series, tariff card, rank, external links |
| `GET /featured` | Up to 8 HS6 with a US surtax, by US import volume |
| `GET /sitemap` | Every HS6 with alternatives |
| `GET /meta` | Data versions and row counts |
| `GET /health` | Liveness |

Unknown HS6: `404 {"detail": "HS6 not found", "hs6": "...", "suggestions": [{"hs6", "desc"}]}`.
Every route except `/health` sends `Cache-Control: public, max-age=86400`.

## Tests

```bash
uv run pytest -v      # needs Docker (testcontainers Postgres)
uv run ruff check src tests
```

## Deploy (Railway)

Service root `api/`, Dockerfile build. Variables: `DATABASE_URL` (Railway Postgres reference), `CORS_ORIGINS` (comma separated, e.g. `https://northsource.vercel.app`).
