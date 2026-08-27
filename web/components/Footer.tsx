import { getTranslations } from "next-intl/server";
import { getMeta } from "@/lib/api";
import MapleLeaf from "./MapleLeaf";

const REPO = process.env.NEXT_PUBLIC_REPO_URL ?? "https://github.com/ahlert/northsource";

export default async function Footer() {
  const t = await getTranslations("footer");
  const meta = await getMeta();
  const v = meta?.data_version;
  return (
    <footer className="mt-20 border-t border-rule py-8 text-sm text-ink-2">
      <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 sm:flex-row sm:items-center sm:justify-between">
        <span className="flex items-center gap-2" data-testid="data-version">
          <MapleLeaf className="h-3.5 w-3.5 shrink-0 text-maple" />
          {v?.cimt ? t("data", { cimt: v.cimt, cbsa: v.cbsa ?? "", comtrade: v.comtrade ?? "" }) : t("noData")}
        </span>
        <span>
          {t("license")} <span className="text-rule">·</span>{" "}
          <a
            href={REPO}
            className="text-ink underline decoration-rule underline-offset-4 hover:decoration-maple"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </span>
      </div>
    </footer>
  );
}
