import { getTranslations } from "next-intl/server";
import FeaturedChips from "@/components/FeaturedChips";
import SearchBox from "@/components/SearchBox";

export default async function Home() {
  const t = await getTranslations("home");
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{t("title")}</h1>
      <p className="mt-3 text-neutral-600">{t("subtitle")}</p>
      <div className="mt-6">
        <SearchBox />
      </div>
      <ol className="mt-6 grid gap-2 text-sm text-neutral-600 sm:grid-cols-3">
        <li>1. {t("how1")}</li>
        <li>2. {t("how2")}</li>
        <li>3. {t("how3")}</li>
      </ol>
      <FeaturedChips />
    </div>
  );
}
