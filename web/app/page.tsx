import Image from "next/image";
import { getTranslations } from "next-intl/server";
import SearchBox from "@/components/SearchBox";
import FeaturedChips from "@/components/FeaturedChips";
import CategoryGrid from "@/components/CategoryGrid";
import StatsBand from "@/components/StatsBand";
import { DoorsBand, ImporterBlock } from "@/components/StorySections";
import unity from "@/public/img/hero-unity.jpg";

export default async function Home() {
  const t = await getTranslations("home");
  const ta = await getTranslations("app");
  const steps = [t("how1"), t("how2"), t("how3")];
  return (
    <div id="top">
      <section className="grid items-center gap-10 md:grid-cols-[1.1fr_1fr] md:gap-12">
        <div>
          <p className="eyebrow">{ta("tagline")}</p>
          <h1 className="mt-4 text-balance font-display text-5xl font-medium leading-[1.05] tracking-tight text-ink sm:text-6xl">
            {t("title")}
          </h1>
          <p className="mt-5 max-w-prose text-lg leading-relaxed text-ink-2">{t("subtitle")}</p>
          <div className="mt-8">
            <SearchBox />
          </div>
          <p className="mt-3 text-sm text-ink-2">{t("trust")}</p>
        </div>
        <div className="relative">
          <Image
            src={unity}
            alt={t("heroAlt")}
            priority
            placeholder="blur"
            sizes="(min-width: 768px) 480px, 100vw"
            className="relative z-10 aspect-[4/3] w-full rounded-md object-cover"
          />
          <span aria-hidden className="absolute -right-3 -top-3 h-full w-full rounded-md bg-maple" />
        </div>
      </section>

      <StatsBand />

      <CategoryGrid />

      <section className="mt-24 border-t border-rule pt-10">
        <ol className="grid gap-8 sm:grid-cols-3">
          {steps.map((s, i) => (
            <li key={i} className="flex flex-col gap-3">
              <span className="font-display text-4xl font-medium leading-none text-maple">{i + 1}</span>
              <span className="text-ink">{s}</span>
            </li>
          ))}
        </ol>
      </section>

      <DoorsBand />

      <div className="mt-20">
        <FeaturedChips />
      </div>

      <ImporterBlock />
    </div>
  );
}
