import Link from "next/link";
import { getTranslations } from "next-intl/server";

export default async function NotFound() {
  const t = await getTranslations("notFound");
  return (
    <div className="mx-auto max-w-lg py-16 text-center">
      <h1 className="text-2xl font-semibold tracking-tight">{t("title")}</h1>
      <p className="mt-3 text-neutral-600">{t("body")}</p>
      <Link href="/" className="mt-6 inline-block underline">
        {t("home")}
      </Link>
    </div>
  );
}
