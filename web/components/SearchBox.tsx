"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { search } from "@/lib/api";
import type { Lang, SearchItem } from "@/lib/types";

export default function SearchBox() {
  const t = useTranslations("home");
  const ts = useTranslations("search");
  const lang = useLocale() as Lang;
  const router = useRouter();
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchItem[]>([]);
  const [busy, setBusy] = useState(false);
  const seq = useRef(0);

  useEffect(() => {
    const term = q.trim();
    if (!term) {
      setResults([]);
      return;
    }
    const id = ++seq.current;
    const timer = setTimeout(async () => {
      setBusy(true);
      try {
        const r = await search(term, lang);
        if (id === seq.current) setResults(r.results);
      } finally {
        if (id === seq.current) setBusy(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [q, lang]);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const term = q.trim();
    if (/^\d{6}$/.test(term)) router.push(`/hs/${term}`);
    else if (results[0]) router.push(`/hs/${results[0].hs6}`);
  }

  return (
    <form onSubmit={onSubmit} className="relative w-full" role="search">
      <svg
        viewBox="0 0 24 24"
        className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-ink-2"
        aria-hidden="true"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("placeholder")}
        aria-label={t("placeholder")}
        autoComplete="off"
        className="h-14 w-full rounded-md border-2 border-ink bg-white pl-12 pr-4 text-lg text-ink placeholder:text-ink-2/70 focus:border-maple focus:outline-none focus:ring-4 focus:ring-maple/15"
        data-testid="search-input"
      />
      {q.trim() && (
        <ul className="absolute z-10 mt-2 w-full overflow-hidden rounded-md border border-rule bg-paper shadow-[0_16px_40px_-16px_rgba(27,27,27,0.35)]">
          {busy && results.length === 0 && <li className="px-4 py-3 text-sm text-ink-2">{ts("searching")}</li>}
          {!busy && results.length === 0 && <li className="px-4 py-3 text-sm text-ink-2">{ts("noResults")}</li>}
          {results.map((r) => (
            <li key={r.hs6} className="border-t border-rule/60 first:border-0">
              <Link
                href={`/hs/${r.hs6}`}
                className="flex items-baseline gap-3 px-4 py-2.5 hover:bg-white"
                data-testid="search-result"
              >
                <span className="font-mono text-sm font-medium text-maple">{r.hs6}</span>
                <span className="truncate text-ink">{r.desc}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}
