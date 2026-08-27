import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getLocale, getTranslations } from "next-intl/server";
import AlternativesTable from "@/components/AlternativesTable";
import SurtaxBadge from "@/components/SurtaxBadge";
import { getHs } from "@/lib/api";
import { desc, periodLabel, shortName } from "@/lib/format";
import type { Lang } from "@/lib/types";

type Params = Promise<{ hs6: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { hs6 } = await params;
  if (!/^\d{6}$/.test(hs6)) notFound();
  const lang = (await getLocale()) as Lang;
  const r = await getHs(hs6, lang);
  if (!r.ok) return { title: `HS ${hs6} | northsource`, robots: { index: false } };
  const t = await getTranslations("result");
  const name = shortName(desc(r.data, lang));
  return {
    title: t("metaTitle", { name, hs6 }),
    description: desc(r.data, lang).slice(0, 160),
  };
}

export default async function HsPage({ params }: { params: Params }) {
  const { hs6 } = await params;
  if (!/^\d{6}$/.test(hs6)) notFound();
  const lang = (await getLocale()) as Lang;
  const t = await getTranslations("result");
  const r = await getHs(hs6, lang);

  if (!r.ok) {
    return (
      <div className="mx-auto max-w-3xl">
        <h1 className="font-display text-3xl font-medium tracking-tight sm:text-4xl">{t("notFoundTitle", { hs6 })}</h1>
        {r.notFound.suggestions.length > 0 && (
          <>
            <p className="mt-4 text-ink-2">{t("notFoundHint")}</p>
            <ul className="mt-3 divide-y divide-rule border-y border-rule">
              {r.notFound.suggestions.map((s) => (
                <li key={s.hs6}>
                  <Link href={`/hs/${s.hs6}`} className="flex items-baseline gap-3 py-2.5 hover:text-maple" data-testid="suggestion">
                    <span className="font-mono text-sm text-maple">{s.hs6}</span> {s.desc}
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    );
  }

  const d = r.data;
  return (
    <div>
      <p className="eyebrow">{t("chapter", { chapter: d.chapter })}</p>
      <h1 className="mt-2 max-w-4xl font-display text-3xl font-medium leading-tight tracking-tight text-ink sm:text-4xl">
        <span className="font-mono text-2xl font-normal text-ink-2 sm:text-3xl">{d.hs6}</span>{" "}
        {desc(d, lang)}
      </h1>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        {d.surtax_us && <SurtaxBadge pct={d.surtax_us.pct} source={d.surtax_us.source} />}
        {d.mfn && (
          <div className="rounded-full border border-rule bg-white px-3.5 py-1.5 text-sm">
            <span className="text-ink-2">{t("mfn")}: </span>
            <span className="font-medium">{d.mfn.display}</span>
          </div>
        )}
      </div>
      {d.coverage === "world_only" && (
        <p className="mt-4 max-w-xl border-l-4 border-amber-500 bg-amber-50 px-4 py-3 text-sm text-amber-950" data-testid="world-only">
          {t("worldOnly")}
        </p>
      )}
      <p className="mt-10 text-xs text-ink-2">
        {t("window", { from: periodLabel(d.window.from, lang), to: periodLabel(d.window.to, lang) })}
      </p>
      <div className="mt-3">
        <AlternativesTable hs6={d.hs6} alternatives={d.alternatives} lang={lang} />
      </div>
    </div>
  );
}
