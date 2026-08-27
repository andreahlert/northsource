"use client";

import { useTranslations } from "next-intl";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtCad, monthLabel } from "@/lib/format";
import type { Lang } from "@/lib/types";

interface Point {
  year: number;
  month: number;
  value_cad: number;
}

const MAPLE = "#d52b1e";
const RULE = "#e6dfd5";
const INK2 = "#6b6560";

export default function ImportChart({ points, lang }: { points: Point[]; lang: Lang }) {
  const t = useTranslations("chart");
  const data = points.map((p) => ({ label: monthLabel(p.year, p.month, lang), value: p.value_cad }));
  return (
    <div className="h-64 w-full" data-testid="import-chart" role="img" aria-label={t("aria")}>
      <ResponsiveContainer width="100%" height="100%" minWidth={300} minHeight={200}>
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
          <defs>
            <linearGradient id="mapleFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={MAPLE} stopOpacity={0.18} />
              <stop offset="100%" stopColor={MAPLE} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="2 4" stroke={RULE} vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: INK2 }} interval={3} axisLine={{ stroke: RULE }} tickLine={false} />
          <YAxis
            tick={{ fontSize: 11, fill: INK2 }}
            tickFormatter={(v: number) => fmtCad(v, lang)}
            width={72}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(v) => fmtCad(Number(v), lang)}
            contentStyle={{ background: "#faf7f2", border: `1px solid ${RULE}`, borderRadius: 4, fontSize: 12 }}
            labelStyle={{ color: INK2, marginBottom: 4 }}
            itemStyle={{ color: "#1b1b1b", fontWeight: 500 }}
            cursor={{ stroke: INK2, strokeDasharray: "2 4" }}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={MAPLE}
            strokeWidth={2}
            fill="url(#mapleFill)"
            dot={false}
            activeDot={{ r: 4, fill: MAPLE, stroke: "#faf7f2", strokeWidth: 2 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
