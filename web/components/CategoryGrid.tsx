import Image from "next/image";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { CATEGORIES } from "@/lib/categories";

export default async function CategoryGrid() {
  const t = await getTranslations("home");
  const tc = await getTranslations("categories");
  return (
    <section className="mt-20" aria-labelledby="categories">
      <h2 id="categories" className="font-display text-3xl font-medium tracking-tight text-ink sm:text-4xl">
        {t("categoriesTitle")}
      </h2>
      <p className="mt-2 max-w-2xl text-ink-2">{t("categoriesSub")}</p>
      <ul className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {CATEGORIES.map((c) => (
          <li key={c.key}>
            <Link
              href={`/hs/${c.hs6}`}
              className="group flex h-full flex-col border border-rule bg-white p-4 transition-colors hover:border-maple"
              data-testid="category-tile"
            >
              <Image
                src={`/icons/${c.key}.png`}
                alt=""
                width={96}
                height={96}
                className="h-16 w-16 rounded-md bg-paper transition-transform group-hover:scale-105 sm:h-20 sm:w-20"
              />
              <span className="mt-4 font-medium leading-snug text-ink group-hover:text-maple">{tc(c.key)}</span>
              <span className="mt-1 font-mono text-xs text-ink-2">
                {t("example")} {c.hs6}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
