-- northsource Postgres schema. Idempotent. Loaded by pipeline/load.py and read by api/.
CREATE TABLE IF NOT EXISTS hs_code (
    hs6        char(6) PRIMARY KEY,
    desc_en    text NOT NULL,
    desc_fr    text NOT NULL,
    chapter    char(2) NOT NULL,
    search_en  tsvector GENERATED ALWAYS AS (to_tsvector('english', desc_en)) STORED,
    search_fr  tsvector GENERATED ALWAYS AS (to_tsvector('french', desc_fr)) STORED
);
CREATE INDEX IF NOT EXISTS hs_code_search_en ON hs_code USING gin (search_en);
CREATE INDEX IF NOT EXISTS hs_code_search_fr ON hs_code USING gin (search_fr);
CREATE INDEX IF NOT EXISTS hs_code_chapter ON hs_code (chapter);

CREATE TABLE IF NOT EXISTS country (
    iso        char(3) PRIMARY KEY,
    name_en    text NOT NULL,
    name_fr    text NOT NULL,
    cimt_code  char(2),
    treatments text[] NOT NULL DEFAULT '{}',
    fta        text
);

CREATE TABLE IF NOT EXISTS tariff_line (
    hs8            char(8) PRIMARY KEY,
    hs6            char(6) NOT NULL REFERENCES hs_code (hs6),
    mfn_text       text NOT NULL,
    mfn_pct        numeric,
    pref           jsonb NOT NULL DEFAULT '{}',
    surtax_us_pct  numeric,
    surtax_source  text
);
CREATE INDEX IF NOT EXISTS tariff_line_hs6 ON tariff_line (hs6);

CREATE TABLE IF NOT EXISTS ca_import (
    hs6          char(6) NOT NULL REFERENCES hs_code (hs6),
    partner_iso  char(3) NOT NULL REFERENCES country (iso),
    year         smallint NOT NULL,
    month        smallint NOT NULL,
    value_cad    bigint NOT NULL,
    PRIMARY KEY (hs6, partner_iso, year, month)
);
CREATE INDEX IF NOT EXISTS ca_import_year_month ON ca_import (year DESC, month DESC);

CREATE TABLE IF NOT EXISTS world_export (
    hs6           char(6) NOT NULL REFERENCES hs_code (hs6),
    reporter_iso  char(3) NOT NULL REFERENCES country (iso),
    year          smallint NOT NULL,
    value_usd     numeric NOT NULL,
    PRIMARY KEY (hs6, reporter_iso, year)
);

CREATE TABLE IF NOT EXISTS alternative_rank (
    hs6                      char(6) NOT NULL REFERENCES hs_code (hs6),
    iso                      char(3) NOT NULL REFERENCES country (iso),
    score                    integer NOT NULL,
    score_reasons            text[] NOT NULL DEFAULT '{}',
    already_supplies_canada  boolean NOT NULL,
    ca_import_12m_cad        bigint NOT NULL,
    world_export_usd         numeric,
    tariff_treatment         text NOT NULL,
    rate_applied_text        text NOT NULL,
    rate_applied_pct         numeric,
    rate_mfn_text            text NOT NULL,
    rate_mfn_pct             numeric,
    fta                      text,
    coverage                 text NOT NULL,
    PRIMARY KEY (hs6, iso)
);
CREATE INDEX IF NOT EXISTS alternative_rank_hs6_score ON alternative_rank (hs6, score DESC);

CREATE TABLE IF NOT EXISTS data_version (
    source     text PRIMARY KEY,
    period     text NOT NULL,
    loaded_at  timestamptz NOT NULL DEFAULT now()
);
