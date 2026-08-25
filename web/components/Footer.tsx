import { getTranslations } from "next-intl/server";
import { getMeta } from "@/lib/api";

const REPO = process.env.NEXT_PUBLIC_REPO_URL ?? "https://github.com/ahlert/northsource";

export default async function Footer() {
  const t = await getTranslations("footer");
  const meta = await getMeta();
  const v = meta?.data_version;
  return (
    <footer className="mt-16 border-t border-neutral-200 py-6 text-sm text-neutral-500">
      <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 sm:flex-row sm:justify-between">
        <span data-testid="data-version">
          {v?.cimt ? t("data", { cimt: v.cimt, cbsa: v.cbsa ?? "", comtrade: v.comtrade ?? "" }) : t("noData")}
        </span>
        <span>
          {t("license")} ·{" "}
          <a href={REPO} className="underline" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
        </span>
      </div>
    </footer>
  );
}
