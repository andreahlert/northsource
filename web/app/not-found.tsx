import Link from "next/link";
import { getTranslations } from "next-intl/server";
import MapleLeaf from "@/components/MapleLeaf";

export default async function NotFound() {
  const t = await getTranslations("notFound");
  return (
    <div className="mx-auto max-w-lg py-20 text-center">
      <MapleLeaf className="mx-auto h-8 w-8 text-maple" />
      <h1 className="mt-4 font-display text-3xl font-medium tracking-tight">{t("title")}</h1>
      <p className="mt-3 text-ink-2">{t("body")}</p>
      <Link href="/" className="mt-8 inline-block font-medium text-maple underline decoration-maple/40 underline-offset-4 hover:text-maple-dark">
        {t("home")}
      </Link>
    </div>
  );
}
