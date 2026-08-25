const FALLBACK_SITE_URL = "http://localhost:3000";

// Both robots.ts and sitemap.ts are prerendered at build time, so a missing
// NEXT_PUBLIC_SITE_URL in production silently ships localhost URLs unless we
// warn here.
export function siteUrl(): string {
  const url = process.env.NEXT_PUBLIC_SITE_URL;
  if (url) return url;
  if (process.env.NODE_ENV === "production") {
    console.warn(`northsource: NEXT_PUBLIC_SITE_URL unset, falling back to ${FALLBACK_SITE_URL}`);
  }
  return FALLBACK_SITE_URL;
}
