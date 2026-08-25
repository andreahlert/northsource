export type Lang = "en" | "fr";

export interface SearchItem {
  hs6: string;
  desc: string;
  chapter: string;
}

export interface SearchResponse {
  query: string;
  lang: Lang;
  results: SearchItem[];
}

export interface Alternative {
  iso: string;
  name: string;
  is_current_us_source: boolean;
  already_supplies_canada: boolean;
  ca_import_12m_cad: number;
  world_export_usd: number | null;
  tariff_treatment: string | null;
  rate_applied: string | null;
  rate_applied_pct: number | null;
  rate_mfn: string | null;
  rate_mfn_pct: number | null;
  fta: string | null;
  score: number | null;
  score_reasons: string[];
}

export interface HsResponse {
  hs6: string;
  desc_en: string;
  desc_fr: string;
  chapter: string;
  mfn: { text: string; pct: number | null; display: string } | null;
  surtax_us: { pct: number; source: string | null; hs8: string[]; note: string } | null;
  coverage: "canada" | "world_only";
  window: { from: string; to: string };
  data_version: Record<string, string>;
  alternatives: Alternative[];
}

export interface HsNotFound {
  detail: string;
  hs6: string;
  suggestions: { hs6: string; desc: string }[];
}

export interface CountryResponse {
  hs6: string;
  desc_en: string;
  desc_fr: string;
  country: { iso: string; name: string; treatments: string[]; fta: string | null; is_current_us_source: boolean };
  imports: { year: number; month: number; value_cad: number }[];
  world_export: { year: number; value_usd: number | null } | null;
  tariff: {
    treatment: string | null;
    rate_applied: string | null;
    rate_applied_pct: number | null;
    rate_mfn: string | null;
    rate_mfn_pct: number | null;
    fta: string | null;
  };
  rank: { score: number; score_reasons: string[] } | null;
  links: { tcs: string; kompass: string; cti: string; frasers: string };
  data_version: Record<string, string>;
}

export interface MetaResponse {
  data_version: Record<string, string>;
  counts: Record<string, number>;
  loaded_at: string | null;
}

export interface FeaturedItem {
  hs6: string;
  desc: string;
  surtax_us_pct: number | null;
  ca_import_12m_cad: number;
}
