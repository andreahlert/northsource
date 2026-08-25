import Link from "next/link";
import { getLocale, getTranslations } from "next-intl/server";
import { getFeatured } from "@/lib/api";
import { fmtCad, shortName } from "@/lib/format";
import type { Lang } from "@/lib/types";

export default async function FeaturedChips() {
  const t = await getTranslations("home");
  const lang = (await getLocale()) as Lang;
  const items = await getFeatured();
  if (items.length === 0) return null;
  return (
    <section className="mt-10">
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-neutral-500">{t("featured")}</h2>
      <ul className="flex flex-wrap gap-2">
        {items.slice(0, 8).map((f) => (
          <li key={f.hs6}>
            <Link
              href={`/hs/${f.hs6}`}
              className="inline-flex items-center gap-2 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-sm text-red-900 hover:bg-red-100"
              data-testid="featured-chip"
              title={f.desc}
            >
              <span className="font-mono">{f.hs6}</span>
              <span>{shortName(f.desc)}</span>
              <span className="text-red-700/70">{fmtCad(f.ca_import_12m_cad, lang)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
