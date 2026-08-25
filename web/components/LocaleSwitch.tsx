"use client";

import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";

export default function LocaleSwitch() {
  const locale = useLocale();
  const router = useRouter();

  function set(lang: "en" | "fr") {
    document.cookie = `NEXT_LOCALE=${lang}; path=/; max-age=31536000; samesite=lax`;
    router.refresh();
  }

  const cls = (l: string) =>
    `px-2 py-1 text-sm rounded ${locale === l ? "bg-neutral-900 text-white" : "text-neutral-600 hover:bg-neutral-100"}`;

  return (
    <div className="flex gap-1" aria-label="Language">
      <button type="button" className={cls("en")} onClick={() => set("en")} data-testid="lang-en">EN</button>
      <button type="button" className={cls("fr")} onClick={() => set("fr")} data-testid="lang-fr">FR</button>
    </div>
  );
}
