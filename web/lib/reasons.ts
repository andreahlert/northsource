// The pipeline emits a closed, small set of literal score-reason strings
// (pipeline/src/northsource_pipeline/rank.py). Map each to a translation key;
// anything unmapped falls through to the raw string so a new pipeline literal
// still renders instead of disappearing.
const REASON_KEYS: Record<string, string> = {
  "supplies Canada": "suppliesCanada",
  "FTA 0%": "fta0",
  "duty free": "dutyFree",
  "preferential rate": "preferentialRate",
  "top-10 world exporter": "top10Exporter",
};

export function reasonLabel(reason: string, t: (key: string) => string): string {
  const key = REASON_KEYS[reason];
  return key ? t(key) : reason;
}
