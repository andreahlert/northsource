# northsource web

Next.js front end for northsource. Talks to the API in `../api`.

## Run locally

```bash
cd web
npm install
cp .env.example .env.local   # point API_URL / NEXT_PUBLIC_API_URL at a running API
npm run dev
```

Pages: `/` (search + featured chips), `/hs/{hs6}` (ranked alternatives, US row pinned), `/hs/{hs6}/{iso}` (24-month imports, tariff, supplier links). Language switch sets the `NEXT_LOCALE` cookie (`en` or `fr`).

## Tests

```bash
npm test        # vitest, lib/format
npm run e2e     # Playwright smoke tests against tests/mock-api.mjs (no Postgres or Python needed)
npm run lint
```

## Deploy (Vercel)

Root directory `web`. Environment variables: `API_URL` and `NEXT_PUBLIC_API_URL` (the Railway API URL), `NEXT_PUBLIC_SITE_URL` (the public site URL, used by `sitemap.xml` and `robots.txt`), `NEXT_PUBLIC_REPO_URL`. Add the Vercel domain to the API's `CORS_ORIGINS`.

Every API fetch uses `next: { revalidate: 86400 }`, so pages refresh their data daily without a redeploy.
