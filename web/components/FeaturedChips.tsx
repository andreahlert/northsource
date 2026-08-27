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
    <section className="mt-14">
      <h2 className="kicker mb-4 flex items-center gap-3">
        <span className="h-px w-6 bg-maple" aria-hidden="true" />
        {t("featured")}
      </h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {items.slice(0, 8).map((f) => (
          <li key={f.hs6}>
            <Link
              href={`/hs/${f.hs6}`}
              className="flex items-baseline gap-3 border-l-[3px] border-maple bg-white/70 px-4 py-3 transition-colors hover:bg-white"
              data-testid="featured-chip"
              title={f.desc}
            >
              <span className="font-mono text-xs text-ink-2">{f.hs6}</span>
              <span className="min-w-0 flex-1 truncate font-medium text-ink">{shortName(f.desc)}</span>
              <span className="tabular shrink-0 text-sm text-ink-2">{fmtCad(f.ca_import_12m_cad, lang)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
