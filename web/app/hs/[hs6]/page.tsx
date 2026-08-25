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
      <div>
        <h1 className="text-2xl font-semibold">{t("notFoundTitle", { hs6 })}</h1>
        {r.notFound.suggestions.length > 0 && (
          <>
            <p className="mt-4 text-neutral-600">{t("notFoundHint")}</p>
            <ul className="mt-2 space-y-1">
              {r.notFound.suggestions.map((s) => (
                <li key={s.hs6}>
                  <Link href={`/hs/${s.hs6}`} className="underline" data-testid="suggestion">
                    <span className="font-mono">{s.hs6}</span> {s.desc}
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
      <p className="text-sm text-neutral-500">{t("chapter", { chapter: d.chapter })}</p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
        <span className="font-mono">{d.hs6}</span> <span className="font-normal">{desc(d, lang)}</span>
      </h1>
      <div className="mt-4 flex flex-wrap items-start gap-4">
        {d.surtax_us && <SurtaxBadge pct={d.surtax_us.pct} source={d.surtax_us.source} />}
        {d.mfn && (
          <div className="rounded-md border border-neutral-200 px-3 py-2 text-sm">
            <span className="text-neutral-500">{t("mfn")}: </span>
            <span className="font-medium">{d.mfn.display}</span>
          </div>
        )}
      </div>
      {d.coverage === "world_only" && (
        <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-900" data-testid="world-only">
          {t("worldOnly")}
        </p>
      )}
      <p className="mt-6 text-xs text-neutral-500">
        {t("window", { from: periodLabel(d.window.from, lang), to: periodLabel(d.window.to, lang) })}
      </p>
      <div className="mt-2">
        <AlternativesTable hs6={d.hs6} alternatives={d.alternatives} lang={lang} />
      </div>
    </div>
  );
}
