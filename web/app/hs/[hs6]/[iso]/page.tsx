import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getLocale, getTranslations } from "next-intl/server";
import ExternalLinks from "@/components/ExternalLinks";
import ImportChart from "@/components/ImportChart";
import TariffCard from "@/components/TariffCard";
import { getCountry } from "@/lib/api";
import { desc, fmtUsd, shortName } from "@/lib/format";
import type { Lang } from "@/lib/types";

type Params = Promise<{ hs6: string; iso: string }>;

function validParams(hs6: string, iso: string): boolean {
  return /^\d{6}$/.test(hs6) && /^[A-Za-z]{3}$/.test(iso);
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { hs6, iso } = await params;
  if (!validParams(hs6, iso)) notFound();
  const lang = (await getLocale()) as Lang;
  const c = await getCountry(hs6, iso.toUpperCase(), lang);
  if (!c) return { title: `HS ${hs6} | northsource`, robots: { index: false } };
  const t = await getTranslations("country");
  return {
    title: t("metaTitle", { country: c.country.name, name: shortName(desc(c, lang)), hs6 }),
    description: desc(c, lang).slice(0, 160),
  };
}

export default async function CountryPage({ params }: { params: Params }) {
  const { hs6, iso } = await params;
  if (!validParams(hs6, iso)) notFound();
  const lang = (await getLocale()) as Lang;
  const t = await getTranslations("country");
  const c = await getCountry(hs6, iso.toUpperCase(), lang);
  if (!c) notFound();

  const total = c.imports.reduce((s, p) => s + p.value_cad, 0);
  return (
    <div>
      <Link href={`/hs/${hs6}`} className="text-sm text-ink-2 hover:text-maple">
        <span aria-hidden="true">{"←"}</span> {t("back", { hs6 })}
      </Link>
      <h1 className="mt-3 font-display text-4xl font-medium leading-tight tracking-tight text-ink sm:text-5xl">
        {c.country.name}
        <span className="ml-3 font-mono text-xl font-normal text-ink-2 sm:text-2xl">{c.hs6}</span>
      </h1>
      <p className="mt-2 max-w-3xl text-lg text-ink-2">{desc(c, lang)}</p>

      <section className="mt-8 border border-rule bg-white p-5">
        <h2 className="kicker mb-3">{t("imports", { name: c.country.name })}</h2>
        {total > 0 ? (
          <ImportChart points={c.imports} lang={lang} />
        ) : (
          <p className="bg-paper px-3 py-6 text-center text-sm text-ink-2" data-testid="import-chart">
            {t("noImports")}
          </p>
        )}
        {c.world_export && c.world_export.value_usd !== null && (
          <p className="mt-3 text-sm text-ink-2">
            {t("worldExport", { year: c.world_export.year })}:{" "}
            <strong className="tabular text-ink">{fmtUsd(c.world_export.value_usd, lang)}</strong>
          </p>
        )}
      </section>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <TariffCard tariff={c.tariff} rank={c.rank} />
        <ExternalLinks links={c.links} name={c.country.name} />
      </div>
    </div>
  );
}
