import Link from "next/link";
import { getTranslations } from "next-intl/server";
import LocaleSwitch from "./LocaleSwitch";

export default async function Header() {
  const t = await getTranslations("app");
  return (
    <header className="border-b border-neutral-200">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-lg font-semibold tracking-tight">{t("name")}</span>
          <span className="hidden text-sm text-neutral-500 sm:inline">{t("tagline")}</span>
        </Link>
        <LocaleSwitch />
      </div>
    </header>
  );
}
