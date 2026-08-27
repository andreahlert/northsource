import { getTranslations } from "next-intl/server";

export default async function SurtaxBadge({ pct, source }: { pct: number; source: string | null }) {
  const t = await getTranslations("result");
  return (
    <div
      className="flex max-w-xl flex-col gap-0.5 border-l-4 border-maple bg-maple-tint px-4 py-3 text-ink"
      data-testid="surtax-badge"
    >
      <span className="font-medium">{t("surtax", { pct })}</span>
      {source && <span className="text-xs text-ink-2">{t("surtaxSource", { source })}</span>}
    </div>
  );
}
