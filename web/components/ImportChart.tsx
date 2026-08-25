"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtCad, monthLabel } from "@/lib/format";
import type { Lang } from "@/lib/types";

interface Point {
  year: number;
  month: number;
  value_cad: number;
}

export default function ImportChart({ points, lang }: { points: Point[]; lang: Lang }) {
  const data = points.map((p) => ({ label: monthLabel(p.year, p.month, lang), value: p.value_cad }));
  return (
    <div className="h-64 w-full" data-testid="import-chart">
      <ResponsiveContainer width="100%" height="100%" minWidth={300} minHeight={200}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} interval={3} />
          <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => fmtCad(v, lang)} width={72} />
          <Tooltip formatter={(v) => fmtCad(Number(v), lang)} />
          <Line type="monotone" dataKey="value" stroke="#171717" strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
