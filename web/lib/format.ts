import type { Lang } from "./types";

const LOCALE: Record<Lang, string> = { en: "en-CA", fr: "fr-CA" };

function compact(n: number, lang: Lang, currency: "CAD" | "USD"): string {
  return new Intl.NumberFormat(LOCALE[lang], {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
    // en keeps the narrow "$" symbol (disambiguated below with an explicit CA$/US$
    // prefix); fr uses the ISO code so CAD and USD never render as the same "$".
    currencyDisplay: lang === "en" ? "narrowSymbol" : "code",
  })
    .format(n)
    .replace(/[\u00a0\u202f]/g, " ");
}

// Rewrites en-CA's bare "$n" (or "-$n") into an explicit "CA$n" / "US$n",
// preserving a leading minus sign instead of discarding it.
function withPrefix(s: string, prefix: string): string {
  const negative = s.startsWith("-");
  const rest = s.replace(/^-?\$?/, "");
  return `${negative ? "-" : ""}${prefix}${rest}`;
}

export function fmtCad(n: number, lang: Lang): string {
  const s = compact(n, lang, "CAD");
  return lang === "en" ? withPrefix(s, "CA$") : s;
}

export function fmtUsd(n: number | null, lang: Lang): string | null {
  if (n === null || n === undefined) return null;
  const s = compact(n, lang, "USD");
  return lang === "en" ? withPrefix(s, "US$") : s;
}

export function monthLabel(year: number, month: number, lang: Lang): string {
  return new Intl.DateTimeFormat(LOCALE[lang], { month: "short", year: "numeric", timeZone: "UTC" }).format(
    new Date(Date.UTC(year, month - 1, 1)),
  );
}

export function periodLabel(period: string, lang: Lang): string {
  const [y, m] = period.split("-").map(Number);
  return monthLabel(y, m, lang);
}

export function shortName(d: string): string {
  const cut = d.split(/,|;| of /)[0].trim().toLowerCase();
  return cut.slice(0, 40);
}

export function desc(hs: { desc_en: string; desc_fr: string }, lang: Lang): string {
  return lang === "fr" && hs.desc_fr ? hs.desc_fr : hs.desc_en;
}
