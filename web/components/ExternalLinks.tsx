import { getTranslations } from "next-intl/server";
import type { CountryResponse } from "@/lib/types";

const ORDER = ["tcs", "kompass", "cti", "frasers"] as const;

export default async function ExternalLinks({ links, name }: { links: CountryResponse["links"]; name: string }) {
  const t = await getTranslations("country");
  return (
    <section className="rounded-lg border border-neutral-200 p-4 text-sm">
      <h2 className="mb-2 font-semibold">{t("links", { name })}</h2>
      <ul className="grid gap-2 sm:grid-cols-2">
        {ORDER.map((k) => (
          <li key={k}>
            <a
              href={links[k]}
              target="_blank"
              rel="noopener noreferrer"
              className="block rounded border border-neutral-200 px-3 py-2 hover:bg-neutral-50"
              data-testid="external-link"
            >
              {t(k)} <span aria-hidden="true">&nearr;</span>
            </a>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-neutral-500">{t("notice")}</p>
    </section>
  );
}
