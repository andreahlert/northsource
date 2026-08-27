import { getTranslations } from "next-intl/server";
import type { CountryResponse } from "@/lib/types";

const ORDER = ["tcs", "kompass", "cti", "frasers"] as const;

export default async function ExternalLinks({ links, name }: { links: CountryResponse["links"]; name: string }) {
  const t = await getTranslations("country");
  return (
    <section className="border border-rule bg-white p-5 text-sm">
      <h2 className="kicker mb-3">{t("links", { name })}</h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {ORDER.filter((k) => links[k].startsWith("https://")).map((k) => (
          <li key={k}>
            <a
              href={links[k]}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between gap-2 border border-rule bg-paper px-3 py-2.5 font-medium text-ink transition-colors hover:border-maple hover:text-maple"
              data-testid="external-link"
            >
              <span>{t(k)}</span>
              <span aria-hidden="true" className="text-ink-2">{"↗"}</span>
            </a>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-ink-2">{t("notice")}</p>
    </section>
  );
}
