import type {
  CountryResponse,
  FeaturedItem,
  HsNotFound,
  HsResponse,
  Lang,
  MetaResponse,
  SearchResponse,
} from "./types";

export const API_URL =
  process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DAILY = { next: { revalidate: 86400 } } as const;

async function get(path: string): Promise<Response> {
  return fetch(`${API_URL}${path}`, DAILY);
}

export async function search(q: string, lang: Lang): Promise<SearchResponse> {
  const r = await fetch(`${PUBLIC_API_URL}/search?q=${encodeURIComponent(q)}&lang=${lang}`);
  if (!r.ok) return { query: q, lang, results: [] };
  return r.json();
}

export type HsResult = { ok: true; data: HsResponse } | { ok: false; notFound: HsNotFound };

export async function getHs(hs6: string, lang: Lang): Promise<HsResult> {
  const r = await get(`/hs/${encodeURIComponent(hs6)}?lang=${lang}`);
  if (r.status === 404) return { ok: false, notFound: await r.json() };
  if (!r.ok) throw new Error(`API ${r.status} on /hs/${hs6}`);
  return { ok: true, data: await r.json() };
}

export async function getCountry(hs6: string, iso: string, lang: Lang): Promise<CountryResponse | null> {
  const r = await get(`/hs/${encodeURIComponent(hs6)}/country/${encodeURIComponent(iso)}?lang=${lang}`);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`API ${r.status} on /hs/${hs6}/country/${iso}`);
  return r.json();
}

export async function getMeta(): Promise<MetaResponse | null> {
  try {
    const r = await get("/meta");
    return r.ok ? r.json() : null;
  } catch {
    return null;
  }
}

export async function getFeatured(): Promise<FeaturedItem[]> {
  try {
    const r = await get("/featured");
    return r.ok ? (await r.json()).items : [];
  } catch {
    return [];
  }
}

export async function getSitemap(): Promise<string[]> {
  try {
    const r = await get("/sitemap");
    return r.ok ? (await r.json()).hs6 : [];
  } catch {
    return [];
  }
}
