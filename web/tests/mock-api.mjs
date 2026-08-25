// Minimal stand-in for the northsource API, serving fixture JSON for Playwright.
import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const load = (name) => JSON.parse(readFileSync(join(here, "fixtures", name), "utf8"));

const search = load("search.json");
const routes = {
  "/hs/040610": load("hs-040610.json"),
  "/hs/040610/country/FRA": load("country-040610-FRA.json"),
  "/hs/040610/country/USA": load("country-040610-USA.json"),
  "/meta": load("meta.json"),
  "/featured": load("featured.json"),
  "/sitemap": load("sitemap.json"),
  "/health": { status: "ok" },
};

const PORT = Number(process.env.MOCK_API_PORT ?? 8001);

createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const send = (status, body) => {
    res.writeHead(status, {
      "content-type": "application/json",
      "access-control-allow-origin": "*",
      "cache-control": "no-store",
    });
    res.end(JSON.stringify(body));
  };
  if (req.method === "OPTIONS") return send(204, {});
  if (url.pathname === "/search") {
    const q = (url.searchParams.get("q") ?? "").trim().toLowerCase();
    const lang = url.searchParams.get("lang") ?? "en";
    const results = /^\d+$/.test(q)
      ? search.filter((r) => r.hs6.startsWith(q))
      : search.filter((r) => r.desc.toLowerCase().includes(q));
    return send(200, { query: q, lang, results });
  }
  if (url.pathname in routes) return send(200, routes[url.pathname]);
  if (url.pathname.startsWith("/hs/")) {
    const hs6 = url.pathname.split("/")[2];
    if (url.pathname.includes("/country/")) return send(404, { detail: "country not found" });
    return send(404, { detail: "HS6 not found", hs6, suggestions: [{ hs6: "040610", desc: search[0].desc }] });
  }
  send(404, { detail: "not found" });
}).listen(PORT, () => console.log(`mock api on http://localhost:${PORT}`));
