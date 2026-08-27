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

const TH = "px-3 py-3 font-semibold";
const TD = "px-3 py-3 align-middle";

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
  const filter = (on: boolean) =>
    `flex cursor-pointer select-none items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors ${
      on ? "border-maple bg-maple-tint text-ink" : "border-rule bg-white text-ink-2 hover:border-ink-2"
    }`;

  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        <label className={filter(ftaOnly)}>
          <input
            type="checkbox"
            checked={ftaOnly}
            onChange={(e) => setFtaOnly(e.target.checked)}
            className="accent-maple"
            data-testid="filter-fta"
          />
          {t("ftaOnly")}
        </label>
        <label className={filter(suppliesOnly)}>
          <input
            type="checkbox"
            checked={suppliesOnly}
            onChange={(e) => setSuppliesOnly(e.target.checked)}
            className="accent-maple"
            data-testid="filter-supplies"
          />
          {t("suppliesOnly")}
        </label>
      </div>
      <div className="overflow-x-auto border border-rule bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-rule text-left text-[11px] uppercase tracking-[0.14em] text-ink-2">
            <tr>
              <th className={TH} scope="col">{t("rank")}</th>
              <th className={TH} scope="col">{t("country")}</th>
              <th className={`${TH} text-right`} scope="col">{t("score")}</th>
              <th className={`${TH} text-right`} scope="col">{t("imports")}</th>
              <th className={`${TH} text-right`} scope="col">{t("exports")}</th>
              <th className={TH} scope="col">{t("applied")}</th>
              <th className={TH} scope="col">{t("mfn")}</th>
              <th className={TH} scope="col">{t("fta")}</th>
              <th className={TH} scope="col">
                <span className="sr-only">{t("action")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {us && (
              <tr className="bg-maple-tint text-ink" data-testid="us-row">
                <td className={TD}>
                  <span className="block h-2 w-2 rounded-full bg-maple" aria-hidden="true" />
                </td>
                <td className={TD}>
                  <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <span className="font-medium">{us.name}</span>
                    <span className="whitespace-nowrap rounded-sm bg-maple px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white">
                      {t("currentSource")}
                    </span>
                  </span>
                </td>
                <td className={`${TD} text-right`}></td>
                <td className={`${TD} text-right`}>{money(us.ca_import_12m_cad)}</td>
                <td className={`${TD} text-right text-ink-2`}>{usd(us.world_export_usd)}</td>
                <td className={TD}></td>
                <td className={TD}>{us.rate_mfn ?? ""}</td>
                <td className={TD}>{us.fta ?? ""}</td>
                <td className={`${TD} text-right`}>
                  <Link href={`/hs/${hs6}/${us.iso}`} className="whitespace-nowrap text-ink-2 underline decoration-rule underline-offset-4 hover:text-maple hover:decoration-maple">
                    {t("find")}
                  </Link>
                </td>
              </tr>
            )}
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-ink-2">
                  {t("none")}
                </td>
              </tr>
            )}
            {rows.map((a, i) => (
              <tr key={a.iso} className="border-t border-rule/70 transition-colors hover:bg-paper" data-testid="alt-row">
                <td className={`${TD} text-ink-2`}>{i + 1}</td>
                <td className={`${TD} font-medium text-ink`}>{a.name}</td>
                <td className={`${TD} text-right`} title={a.score_reasons.map((r) => reasonLabel(r, tr)).join(", ")}>
                  {a.score !== null && (
                    <span className="inline-flex items-center justify-end gap-2">
                      <span className="font-medium">{a.score}</span>
                      <span className="h-1.5 w-14 overflow-hidden rounded-sm bg-rule" aria-hidden="true">
                        <span className="block h-full bg-maple" style={{ width: `${Math.min(100, Math.max(0, a.score))}%` }} />
                      </span>
                    </span>
                  )}
                </td>
                <td className={`${TD} text-right`}>{a.already_supplies_canada ? money(a.ca_import_12m_cad) : ""}</td>
                <td className={`${TD} text-right ${a.world_export_usd === null ? "text-ink-2" : ""}`}>{usd(a.world_export_usd)}</td>
                <td className={`${TD} whitespace-nowrap`}>
                  <span className={a.rate_applied_pct === 0 ? "font-medium text-pine" : ""}>{a.rate_applied ?? ""}</span>
                  {a.tariff_treatment && a.tariff_treatment !== "MFN" && (
                    <span className="ml-1 text-xs text-ink-2">({a.tariff_treatment})</span>
                  )}
                </td>
                <td className={TD}>{a.rate_mfn ?? ""}</td>
                <td className={TD}>{a.fta ?? ""}</td>
                <td className={`${TD} text-right`}>
                  <Link
                    href={`/hs/${hs6}/${a.iso}`}
                    className="whitespace-nowrap font-medium text-maple hover:text-maple-dark"
                    data-testid="find-suppliers"
                  >
                    {t("find")} <span aria-hidden="true">{"→"}</span>
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
