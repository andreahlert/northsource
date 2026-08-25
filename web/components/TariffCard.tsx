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
  const row = (label: string, value: string | number | null) =>
    value === null || value === "" ? null : (
      <div className="flex justify-between gap-4 py-1">
        <dt className="text-neutral-500">{label}</dt>
        <dd className="font-medium">{value}</dd>
      </div>
    );
  return (
    <div className="rounded-lg border border-neutral-200 p-4 text-sm" data-testid="tariff-card">
      <h2 className="mb-2 font-semibold">{t("tariff")}</h2>
      <dl>
        {row(t("treatment"), tariff.treatment)}
        {row(t("applied"), tariff.rate_applied)}
        {row(t("mfn"), tariff.rate_mfn)}
        {row(t("fta"), tariff.fta)}
        {rank && row(t("score"), rank.score)}
      </dl>
      {rank && rank.score_reasons.length > 0 && (
        <div className="mt-3">
          <p className="text-neutral-500">{t("reasons")}</p>
          <ul className="mt-1 list-disc pl-5">
            {rank.score_reasons.map((r) => (
              <li key={r}>{reasonLabel(r, tr)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
