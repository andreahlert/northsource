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
      const r = await search(term, lang);
      if (id === seq.current) {
        setResults(r.results);
        setBusy(false);
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
      <input
        type="search"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder={t("placeholder")}
        autoComplete="off"
        className="w-full rounded-lg border border-neutral-300 px-4 py-3 text-lg shadow-sm focus:border-neutral-900 focus:outline-none"
        data-testid="search-input"
      />
      {q.trim() && (
        <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-lg">
          {busy && results.length === 0 && <li className="px-4 py-2 text-sm text-neutral-500">{ts("searching")}</li>}
          {!busy && results.length === 0 && <li className="px-4 py-2 text-sm text-neutral-500">{ts("noResults")}</li>}
          {results.map((r) => (
            <li key={r.hs6}>
              <Link
                href={`/hs/${r.hs6}`}
                className="flex gap-3 px-4 py-2 hover:bg-neutral-50"
                data-testid="search-result"
              >
                <span className="font-mono text-neutral-500">{r.hs6}</span>
                <span className="truncate">{r.desc}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </form>
  );
}
