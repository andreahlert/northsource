"use client";

import { useTranslations } from "next-intl";
import { useEffect } from "react";

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations("error");

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="mx-auto max-w-lg py-20 text-center">
      <h1 className="font-display text-3xl font-medium tracking-tight">{t("title")}</h1>
      <p className="mt-3 text-ink-2">{t("body")}</p>
      <button
        type="button"
        onClick={reset}
        className="mt-8 rounded-md bg-maple px-5 py-2.5 text-sm font-medium text-white hover:bg-maple-dark"
      >
        {t("retry")}
      </button>
    </div>
  );
}
