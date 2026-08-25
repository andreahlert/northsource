import { getTranslations } from "next-intl/server";

export default async function SurtaxBadge({ pct, source }: { pct: number; source: string | null }) {
  const t = await getTranslations("result");
  return (
    <div
      className="inline-flex flex-col gap-0.5 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-red-900"
      data-testid="surtax-badge"
    >
      <span className="font-medium">{t("surtax", { pct })}</span>
      {source && <span className="text-xs text-red-800/80">{t("surtaxSource", { source })}</span>}
    </div>
  );
}
