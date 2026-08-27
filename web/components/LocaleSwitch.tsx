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
    `px-1.5 py-1 text-sm font-medium tracking-wide underline-offset-[6px] decoration-2 ${
      locale === l ? "text-ink underline decoration-maple" : "text-ink-2 hover:text-ink"
    }`;

  return (
    <div className="flex items-center gap-1" aria-label="Language" role="group">
      <button type="button" className={cls("en")} onClick={() => set("en")} aria-pressed={locale === "en"} data-testid="lang-en">EN</button>
      <span className="text-rule" aria-hidden="true">|</span>
      <button type="button" className={cls("fr")} onClick={() => set("fr")} aria-pressed={locale === "fr"} data-testid="lang-fr">FR</button>
    </div>
  );
}
