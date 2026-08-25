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
      <Link href={`/hs/${hs6}`} className="text-sm text-neutral-500 underline">
        {t("back", { hs6 })}
      </Link>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
        {c.country.name}
        <span className="ml-2 font-mono text-lg font-normal text-neutral-500">{c.hs6}</span>
      </h1>
      <p className="mt-1 text-neutral-600">{desc(c, lang)}</p>

      <section className="mt-6">
        <h2 className="mb-2 text-sm font-medium text-neutral-600">{t("imports", { name: c.country.name })}</h2>
        {total > 0 ? (
          <ImportChart points={c.imports} lang={lang} />
        ) : (
          <p className="rounded-md bg-neutral-50 px-3 py-4 text-sm text-neutral-500" data-testid="import-chart">
            {t("noImports")}
          </p>
        )}
        {c.world_export && c.world_export.value_usd !== null && (
          <p className="mt-2 text-sm text-neutral-600">
            {t("worldExport", { year: c.world_export.year })}: <strong>{fmtUsd(c.world_export.value_usd, lang)}</strong>
          </p>
        )}
      </section>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <TariffCard tariff={c.tariff} rank={c.rank} />
        <ExternalLinks links={c.links} name={c.country.name} />
      </div>
    </div>
  );
}
