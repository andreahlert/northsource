import { getTranslations } from "next-intl/server";
import { reasonLabel } from "@/lib/reasons";
import type { CountryResponse } from "@/lib/types";

export default async function TariffCard({
  tariff,
  rank,
}: {
  tariff: CountryResponse["tariff"];
  rank: CountryResponse["rank"];
}) {
  const t = await getTranslations("country");
  const tr = await getTranslations("reasons");
  const row = (label: string, value: React.ReactNode) =>
    value === null || value === "" ? null : (
      <div className="flex items-center justify-between gap-4 border-b border-rule/70 py-2.5 last:border-0">
        <dt className="text-ink-2">{label}</dt>
        <dd className="tabular font-medium text-ink">{value}</dd>
      </div>
    );
  return (
    <div className="border border-rule bg-white p-5 text-sm" data-testid="tariff-card">
      <h2 className="kicker mb-3">{t("tariff")}</h2>
      <dl>
        {row(t("treatment"), tariff.treatment)}
        {row(t("applied"), tariff.rate_applied)}
        {row(t("mfn"), tariff.rate_mfn)}
        {row(t("fta"), tariff.fta)}
        {rank &&
          row(
            t("score"),
            <span className="inline-flex items-center gap-2">
              <span>{rank.score}</span>
              <span className="h-1.5 w-16 overflow-hidden rounded-sm bg-rule" aria-hidden="true">
                <span className="block h-full bg-maple" style={{ width: `${Math.min(100, Math.max(0, rank.score))}%` }} />
              </span>
            </span>,
          )}
      </dl>
      {rank && rank.score_reasons.length > 0 && (
        <div className="mt-4">
          <p className="text-ink-2">{t("reasons")}</p>
          <ul className="mt-2 flex flex-wrap gap-1.5">
            {rank.score_reasons.map((r) => (
              <li key={r} className="rounded-full bg-paper-2 px-2.5 py-1 text-xs text-ink">
                {reasonLabel(r, tr)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
