-- Migration 251: ga_condition_composite — unified planetary condition table
-- One row per (chart_id, ayanamsha_id, graha) = 9 grahas × 5 ayanamshas = 45 rows/chart.
-- Populated by the ga_condition writer (heavy, plan_substeps per ayanamsha).
--
-- Stores:
--   • Dignity composite (D1 label + score, varga spread as JSONB, composite score)
--   • Avasthas (baladi, jagradadi, deeptaadi, lajjitaadi, sayanadi)
--   • Motion & combustion state
--   • Friendship (naisargika, tatkalika, panchadha)
--   • Graha yuddha (planetary war) metadata
--   • Unified condition score (0–1 numeric, formula v1)
--   • Dasha trajectory references (peak / weak periods)

BEGIN;

CREATE TABLE IF NOT EXISTS ga_condition_composite (
    id                          SERIAL PRIMARY KEY,
    chart_id                    UUID        NOT NULL,
    build_id                    UUID,
    ayanamsha_id                TEXT        NOT NULL,
    graha                       TEXT        NOT NULL,

    -- ── Dignity (D1 + varga spread) ───────────────────────────────────────────
    dignity_d1                  TEXT,       -- 'exalted','moolatrikona','own','great_friend_sign',
                                            -- 'friend_sign','neutral_sign','enemy_sign',
                                            -- 'great_enemy_sign','debilitated'
    dignity_score_d1            NUMERIC,    -- 0.0–1.0 per DIGNITY_SCORES table
    varga_dignity_spread        JSONB,      -- {varga: dignity_label, …} for cross-varga view
    varga_dignity_composite     NUMERIC,    -- weighted average dignity score across vargas

    -- ── Avasthas ──────────────────────────────────────────────────────────────
    avastha_baladi              TEXT,       -- 'bala','kumara','yuva','vriddha','mrita'
    avastha_jagradadi           TEXT,       -- 'jagrata','svapna','sushupti'
    avastha_deeptaadi           TEXT,       -- 'deepta','swastha','mudita','shanta','shakta',
                                            -- 'dina','peedit','khala','vikala'
    avastha_lajjitaadi          TEXT,       -- 'lajjita','garvita','kshudhita','trishita',
                                            -- 'mudita','kshobhita'
    avastha_sayanadi            TEXT,       -- one of 12 posture states

    -- ── Motion & combustion ───────────────────────────────────────────────────
    motion_state                TEXT,       -- 'vakra','anuvakra','manda','sama','atichara'
    speed_degrees_per_day       NUMERIC,    -- daily motion in degrees (negative = retrograde)
    is_retrograde               BOOLEAN,
    combustion_arc_from_sun     NUMERIC,    -- angular arc from Sun in degrees (0–180)
    is_combust                  BOOLEAN,
    is_deeply_combust           BOOLEAN,

    -- ── Friendship relations ──────────────────────────────────────────────────
    -- naisargika: permanent natural friendship per BPHS Ch.27
    -- tatkalika:  temporary friendship based on chart position
    -- panchadha:  5-fold (naisargika + tatkalika combined)
    -- Note: these store relation of the graha's lord (sign lord) to the graha,
    -- or the graha's relation to its dispositor — set by the writer.
    naisargika_relation         TEXT,       -- relation to sign lord (friend/neutral/enemy)
    tatkalika_relation          TEXT,       -- temporary relation
    panchadha_relation          TEXT,       -- 'great_friend','friend','neutral','enemy','great_enemy'

    -- ── Graha yuddha (planetary war) ─────────────────────────────────────────
    graha_yuddha_with           TEXT,       -- name of planet in war (NULL if none)
    graha_yuddha_result         TEXT,       -- 'winner','loser','none'

    -- ── Unified condition score ───────────────────────────────────────────────
    condition_score             NUMERIC,    -- 0.0–1.0 composite; NULL when inputs incomplete
    condition_formula_version   TEXT        NOT NULL DEFAULT 'condition_formula_v1',
    condition_score_breakdown   JSONB,      -- {dignity:0.8, baladi:1.0, deeptaadi:0.85, …}

    -- ── Dasha trajectory ─────────────────────────────────────────────────────
    peak_dasha_periods          JSONB,      -- [{dasha_label, start_date, end_date, reason}, …]
    weak_dasha_periods          JSONB,      -- same schema; low-condition periods

    -- ── Audit ─────────────────────────────────────────────────────────────────
    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ga_condition_composite_unique
        UNIQUE (chart_id, ayanamsha_id, graha)
);

-- Primary access pattern: fetch all grahas for a chart+ayanamsha
CREATE INDEX IF NOT EXISTS idx_ga_condition_chart_ay
    ON ga_condition_composite (chart_id, ayanamsha_id);

-- Secondary: single-graha lookup across ayanamshas
CREATE INDEX IF NOT EXISTS idx_ga_condition_chart_graha
    ON ga_condition_composite (chart_id, graha);

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DROP TABLE IF EXISTS ga_condition_composite;
--   COMMIT;
-- =============================================================================
