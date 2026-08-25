import type { Lang } from "./types";

const LOCALE: Record<Lang, string> = { en: "en-CA", fr: "fr-CA" };

function compact(n: number, lang: Lang, currency: "CAD" | "USD"): string {
  return new Intl.NumberFormat(LOCALE[lang], {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
    currencyDisplay: "narrowSymbol",
  })
    .format(n)
    .replace(/^\$/, "CA$")
    .replace(/^US\$/, "US$");
}

export function fmtCad(n: number, lang: Lang): string {
  const s = compact(n, lang, "CAD");
  return lang === "en" && !s.startsWith("CA$") ? `CA$${s.replace(/^[^\d]*/, "")}` : s;
}

export function fmtUsd(n: number | null, lang: Lang): string | null {
  if (n === null || n === undefined) return null;
  const s = compact(n, lang, "USD");
  return lang === "en" && !s.startsWith("US$") ? `US$${s.replace(/^[^\d]*/, "")}` : s;
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
