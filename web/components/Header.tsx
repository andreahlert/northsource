import Link from "next/link";
import { getTranslations } from "next-intl/server";
import LocaleSwitch from "./LocaleSwitch";
import MapleLeaf from "./MapleLeaf";

export default async function Header() {
  const t = await getTranslations("app");
  return (
    <header className="bg-paper">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <Link href="/" className="group flex items-center gap-2.5">
          <MapleLeaf className="h-6 w-6 text-maple transition-transform group-hover:-rotate-6" />
          <span className="font-display text-2xl font-semibold tracking-tight text-ink">{t("name")}</span>
          <span className="ml-1 hidden border-l border-rule pl-3 text-sm text-ink-2 sm:inline">{t("tagline")}</span>
        </Link>
        <LocaleSwitch />
      </div>
      <div className="h-[3px] bg-maple" />
    </header>
  );
}
