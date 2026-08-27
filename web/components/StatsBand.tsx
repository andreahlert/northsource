import { getLocale, getTranslations } from "next-intl/server";
import { getMeta } from "@/lib/api";
import { periodLabel } from "@/lib/format";
import type { Lang } from "@/lib/types";

export default async function StatsBand() {
  const t = await getTranslations("home");
  const lang = (await getLocale()) as Lang;
  const meta = await getMeta();
  if (!meta || !meta.data_version.cimt) return null;
  const n = (v: number) => new Intl.NumberFormat(lang === "fr" ? "fr-CA" : "en-CA", { notation: "compact", maximumFractionDigits: 2 }).format(v);
  const stats = [
    { value: n(meta.counts.hs_code ?? 0), label: t("statsCodes") },
    { value: n(meta.counts.country ?? 0), label: t("statsCountries") },
    { value: n(meta.counts.ca_import ?? 0), label: t("statsRecords") },
  ];
  return (
    <section className="mt-16 border-y border-rule py-6" aria-label="Coverage">
      <dl className="grid gap-6 sm:grid-cols-3">
        {stats.map((s) => (
          <div key={s.label} className="flex items-baseline gap-3 sm:block">
            <dd className="tabular font-display text-3xl font-medium text-ink sm:text-4xl">{s.value}</dd>
            <dt className="text-sm text-ink-2">{s.label}</dt>
          </div>
        ))}
      </dl>
      <p className="mt-4 text-xs text-ink-2">{t("statsUpdated", { period: periodLabel(meta.data_version.cimt, lang) })}</p>
    </section>
  );
}
