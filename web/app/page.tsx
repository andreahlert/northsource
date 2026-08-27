import { getTranslations } from "next-intl/server";
import FeaturedChips from "@/components/FeaturedChips";
import SearchBox from "@/components/SearchBox";

export default async function Home() {
  const t = await getTranslations("home");
  const ta = await getTranslations("app");
  return (
    <div className="mx-auto max-w-3xl pt-4 sm:pt-12">
      <p className="eyebrow">{ta("tagline")}</p>
      <h1 className="mt-3 text-balance font-display text-5xl font-medium leading-[1.02] tracking-tight text-ink sm:text-6xl">
        {t("title")}
      </h1>
      <p className="mt-5 max-w-2xl text-lg leading-relaxed text-ink-2">{t("subtitle")}</p>
      <div className="mt-8">
        <SearchBox />
      </div>
      <ol className="mt-8 grid gap-4 text-sm text-ink-2 sm:grid-cols-3">
        {(["how1", "how2", "how3"] as const).map((k, i) => (
          <li key={k} className="flex gap-3 border-t border-rule pt-3">
            <span className="font-display text-2xl leading-none text-maple">{i + 1}</span>
            <span>{t(k)}</span>
          </li>
        ))}
      </ol>
      <FeaturedChips />
    </div>
  );
}
