"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useMemo, useState } from "react";
import { fmtCad, fmtUsd } from "@/lib/format";
import { reasonLabel } from "@/lib/reasons";
import type { Alternative, Lang } from "@/lib/types";

interface Props {
  hs6: string;
  alternatives: Alternative[];
  lang: Lang;
}

export default function AlternativesTable({ hs6, alternatives, lang }: Props) {
  const t = useTranslations("table");
  const tr = useTranslations("reasons");
  const [ftaOnly, setFtaOnly] = useState(false);
  const [suppliesOnly, setSuppliesOnly] = useState(false);

  const us = alternatives.find((a) => a.is_current_us_source) ?? null;
  const rows = useMemo(
    () =>
      alternatives
        .filter((a) => !a.is_current_us_source)
        .filter((a) => !ftaOnly || a.fta !== null)
        .filter((a) => !suppliesOnly || a.already_supplies_canada),
    [alternatives, ftaOnly, suppliesOnly],
  );

  const money = (n: number) => fmtCad(n, lang);
  const usd = (n: number | null) => fmtUsd(n, lang) ?? t("noData");

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-4 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={ftaOnly} onChange={(e) => setFtaOnly(e.target.checked)} data-testid="filter-fta" />
          {t("ftaOnly")}
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={suppliesOnly}
            onChange={(e) => setSuppliesOnly(e.target.checked)}
            data-testid="filter-supplies"
          />
          {t("suppliesOnly")}
        </label>
      </div>
      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left text-xs uppercase tracking-wide text-neutral-500">
            <tr>
              <th className="px-3 py-2" scope="col">{t("rank")}</th>
              <th className="px-3 py-2" scope="col">{t("country")}</th>
              <th className="px-3 py-2 text-right" scope="col">{t("score")}</th>
              <th className="px-3 py-2 text-right" scope="col">{t("imports")}</th>
              <th className="px-3 py-2 text-right" scope="col">{t("exports")}</th>
              <th className="px-3 py-2" scope="col">{t("applied")}</th>
              <th className="px-3 py-2" scope="col">{t("mfn")}</th>
              <th className="px-3 py-2" scope="col">{t("fta")}</th>
              <th className="px-3 py-2" scope="col">
                <span className="sr-only">{t("action")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {us && (
              <tr className="bg-neutral-100 text-neutral-500" data-testid="us-row">
                <td className="px-3 py-2"></td>
                <td className="px-3 py-2">
                  {us.name}{" "}
                  <span className="ml-1 rounded bg-neutral-200 px-1.5 py-0.5 text-xs">{t("currentSource")}</span>
                </td>
                <td className="px-3 py-2 text-right"></td>
                <td className="px-3 py-2 text-right">{money(us.ca_import_12m_cad)}</td>
                <td className="px-3 py-2 text-right">{usd(us.world_export_usd)}</td>
                <td className="px-3 py-2"></td>
                <td className="px-3 py-2">{us.rate_mfn ?? ""}</td>
                <td className="px-3 py-2">{us.fta ?? ""}</td>
                <td className="px-3 py-2">
                  <Link href={`/hs/${hs6}/${us.iso}`} className="underline">
                    {t("find")}
                  </Link>
                </td>
              </tr>
            )}
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-6 text-center text-neutral-500">
                  {t("none")}
                </td>
              </tr>
            )}
            {rows.map((a, i) => (
              <tr key={a.iso} className="border-t border-neutral-100" data-testid="alt-row">
                <td className="px-3 py-2 text-neutral-500">{i + 1}</td>
                <td className="px-3 py-2 font-medium">{a.name}</td>
                <td className="px-3 py-2 text-right" title={a.score_reasons.map((r) => reasonLabel(r, tr)).join(", ")}>
                  {a.score ?? ""}
                </td>
                <td className="px-3 py-2 text-right">{a.already_supplies_canada ? money(a.ca_import_12m_cad) : ""}</td>
                <td className="px-3 py-2 text-right">{usd(a.world_export_usd)}</td>
                <td className="px-3 py-2">
                  {a.rate_applied ?? ""}
                  {a.tariff_treatment && a.tariff_treatment !== "MFN" && (
                    <span className="ml-1 text-xs text-neutral-500">({a.tariff_treatment})</span>
                  )}
                </td>
                <td className="px-3 py-2">{a.rate_mfn ?? ""}</td>
                <td className="px-3 py-2">{a.fta ?? ""}</td>
                <td className="px-3 py-2">
                  <Link
                    href={`/hs/${hs6}/${a.iso}`}
                    className="whitespace-nowrap rounded bg-neutral-900 px-2 py-1 text-xs text-white hover:bg-neutral-700"
                    data-testid="find-suppliers"
                  >
                    {t("find")}
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
