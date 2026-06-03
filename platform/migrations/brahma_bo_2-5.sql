-- brahma_bo_2-5.sql — Brahma L2 Bodha — bodha.lenses (BO-2-5)
-- Asset:   bodha.lenses
-- Owns:    Computed lens views over bodha_signals + bodha_graph
-- Depends: bodha_signals (BO-2-1), bodha_graph (BO-2-2)
-- Tables:  NONE — pure views / stored functions over existing bodha_* tables
--
-- CONTRACT (from BRAHMA_L1_L5_REGISTRY_SEED §C — bodha.lenses):
--   concordance lens  : groups signals by school agreement / disagreement
--   contradiction lens: surfaces signal pairs with contradicting valence
--   negative_space    : computes what is NOT signalled (absent expected signals)
--   salience          : ranks signals by confidence × reinforcement_count × domain_weight
--
-- ROLLBACK:
--   DROP FUNCTION IF EXISTS bodha_concordance_lens(TEXT, NUMERIC);
--   DROP FUNCTION IF EXISTS bodha_contradiction_lens(TEXT, NUMERIC);
--   DROP FUNCTION IF EXISTS bodha_negative_space(TEXT);
--   DROP FUNCTION IF EXISTS bodha_salience_lens(TEXT, NUMERIC, NUMERIC, INT);
--   DROP FUNCTION IF EXISTS bodha_query_signals_with_lens(TEXT, TEXT, TEXT, TEXT, NUMERIC, TEXT, INT, INT);
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── §1 — Concordance Lens ─────────────────────────────────────────────────────
--
-- Groups signals by domain + valence, computes per-group school agreement score.
-- "Agreement" is proxied by averaging confidence × salience across signals in a group.
-- High score = many signals pointing the same direction with high confidence.
-- Low score  = signals exist but are weak or contradicted.

CREATE OR REPLACE FUNCTION bodha_concordance_lens(
    p_chart_id  TEXT,
    p_min_conf  NUMERIC DEFAULT 0.0
)
RETURNS TABLE (
    domain          TEXT,
    valence         TEXT,
    signal_count    BIGINT,
    avg_confidence  NUMERIC,
    avg_salience    NUMERIC,
    agreement_score NUMERIC,
    signal_ids      TEXT[],
    signal_names    TEXT[]
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        s.domain,
        s.valence,
        COUNT(*)                                                    AS signal_count,
        ROUND(AVG(s.confidence)::NUMERIC, 4)                       AS avg_confidence,
        ROUND(AVG(s.salience)::NUMERIC, 4)                         AS avg_salience,
        -- agreement_score = avg(confidence x salience) — higher when signals agree strongly
        ROUND(AVG(s.confidence * s.salience)::NUMERIC, 4)          AS agreement_score,
        ARRAY_AGG(s.signal_id ORDER BY s.salience DESC, s.confidence DESC) AS signal_ids,
        ARRAY_AGG(s.signal_name ORDER BY s.salience DESC, s.confidence DESC) AS signal_names
    FROM public.bodha_signals s
    WHERE s.chart_id = p_chart_id
      AND s.confidence >= p_min_conf
    GROUP BY s.domain, s.valence
    ORDER BY s.domain, agreement_score DESC
$$;

COMMENT ON FUNCTION bodha_concordance_lens(TEXT, NUMERIC) IS
'BO-2-5 concordance lens: groups bodha_signals by domain+valence, ranks by agreement_score = avg(confidence x salience). High score = school consensus; low score = weak or split signals. Native chart (Abhisek Mohanty 1984-02-05): expect Saturn-career signals to cluster near top.';


-- ── §2 — Contradiction Lens ───────────────────────────────────────────────────
--
-- Surfaces signal PAIRS within the same domain where one is benefic and the other
-- malefic (or context-dependent vs. malefic), indicating genuine interpretive tension.
-- Each pair carries both signal IDs, the domain, the edge via bodha_graph if it
-- exists (CONTRADICTS edge), and a tension_score = product of confidences.

CREATE OR REPLACE FUNCTION bodha_contradiction_lens(
    p_chart_id  TEXT,
    p_min_conf  NUMERIC DEFAULT 0.3
)
RETURNS TABLE (
    domain          TEXT,
    signal_id_a     TEXT,
    signal_name_a   TEXT,
    valence_a       TEXT,
    confidence_a    NUMERIC,
    signal_id_b     TEXT,
    signal_name_b   TEXT,
    valence_b       TEXT,
    confidence_b    NUMERIC,
    tension_score   NUMERIC,
    graph_edge_id   TEXT,
    has_graph_edge  BOOLEAN
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        a.domain,
        a.signal_id                     AS signal_id_a,
        a.signal_name                   AS signal_name_a,
        a.valence                       AS valence_a,
        a.confidence                    AS confidence_a,
        b.signal_id                     AS signal_id_b,
        b.signal_name                   AS signal_name_b,
        b.valence                       AS valence_b,
        b.confidence                    AS confidence_b,
        ROUND((a.confidence * b.confidence * a.salience * b.salience)::NUMERIC, 4) AS tension_score,
        g.edge_id                       AS graph_edge_id,
        (g.edge_id IS NOT NULL)         AS has_graph_edge
    FROM public.bodha_signals a
    JOIN public.bodha_signals b
        ON  a.chart_id = b.chart_id
        AND a.domain   = b.domain
        AND a.signal_id < b.signal_id
        AND (
              (a.valence = 'benefic'           AND b.valence = 'malefic')
           OR (a.valence = 'malefic'           AND b.valence = 'benefic')
           OR (a.valence = 'context-dependent' AND b.valence = 'malefic')
           OR (a.valence = 'malefic'           AND b.valence = 'context-dependent')
        )
    LEFT JOIN public.bodha_graph g
        ON  g.chart_id       = a.chart_id
        AND g.edge_type      = 'CONTRADICTS'
        AND (
              (g.from_signal_id = a.signal_id AND g.to_signal_id = b.signal_id)
           OR (g.from_signal_id = b.signal_id AND g.to_signal_id = a.signal_id)
        )
    WHERE a.chart_id    = p_chart_id
      AND a.confidence >= p_min_conf
      AND b.confidence >= p_min_conf
    ORDER BY tension_score DESC
$$;

COMMENT ON FUNCTION bodha_contradiction_lens(TEXT, NUMERIC) IS
'BO-2-5 contradiction lens: surfaces same-domain signal pairs with opposing valence (benefic vs malefic). tension_score = product of confidences x saliencies. Links to bodha_graph CONTRADICTS edges when present. Native chart test: must return >=1 row (at least one contradiction-hub).';


-- ── §3 — Negative Space Lens ──────────────────────────────────────────────────
--
-- Computes what is NOT signalled: domains and grahas where the chart has no
-- signals at all, or only low-confidence signals (< 0.4).

CREATE OR REPLACE FUNCTION bodha_negative_space(
    p_chart_id  TEXT
)
RETURNS TABLE (
    check_type          TEXT,
    label               TEXT,
    signal_count        BIGINT,
    max_confidence      NUMERIC,
    interpretation_hint TEXT
)
LANGUAGE sql
STABLE
AS $$
    WITH expected_domains(domain) AS (
        SELECT unnest(ARRAY[
            'career', 'wealth', 'relationships', 'health', 'spirit',
            'mind', 'travel', 'parents', 'dasha', 'nadi_bnn',
            'yogini_tajaka', 'house_domain'
        ])
    ),
    expected_grahas(graha) AS (
        SELECT unnest(ARRAY[
            'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
            'Venus', 'Saturn', 'Rahu', 'Ketu'
        ])
    ),
    actual_domains AS (
        SELECT
            s.domain,
            COUNT(*)        AS signal_count,
            MAX(s.confidence) AS max_confidence
        FROM public.bodha_signals s
        WHERE s.chart_id = p_chart_id
        GROUP BY s.domain
    ),
    actual_grahas AS (
        SELECT
            s.graha,
            COUNT(*)        AS signal_count,
            MAX(s.confidence) AS max_confidence
        FROM public.bodha_signals s
        WHERE s.chart_id = p_chart_id
          AND s.graha IS NOT NULL
        GROUP BY s.graha
    )

    SELECT
        'domain_absent'::TEXT                                   AS check_type,
        ed.domain                                               AS label,
        0::BIGINT                                               AS signal_count,
        0::NUMERIC                                              AS max_confidence,
        'Domain ' || ed.domain || ' has NO signals — potential blank in the reading'
                                                                AS interpretation_hint
    FROM expected_domains ed
    LEFT JOIN actual_domains ad ON ad.domain = ed.domain
    WHERE ad.domain IS NULL

    UNION ALL

    SELECT
        'domain_weak'::TEXT                                     AS check_type,
        ad.domain                                               AS label,
        ad.signal_count,
        ROUND(ad.max_confidence::NUMERIC, 4)                   AS max_confidence,
        'Domain ' || ad.domain || ' exists (' || ad.signal_count ||
            ' signals) but max confidence=' ||
            ROUND(ad.max_confidence::NUMERIC, 2) ||
            ' — weak coverage, consider deepening'             AS interpretation_hint
    FROM actual_domains ad
    WHERE ad.max_confidence < 0.4

    UNION ALL

    SELECT
        'graha_absent'::TEXT                                    AS check_type,
        eg.graha                                                AS label,
        0::BIGINT                                               AS signal_count,
        0::NUMERIC                                              AS max_confidence,
        'Graha ' || eg.graha || ' has NO signals — potential blind spot or quiet planet'
                                                                AS interpretation_hint
    FROM expected_grahas eg
    LEFT JOIN actual_grahas ag ON ag.graha = eg.graha
    WHERE ag.graha IS NULL

    ORDER BY check_type, label
$$;

COMMENT ON FUNCTION bodha_negative_space(TEXT) IS
'BO-2-5 negative_space: computes what is NOT signalled — absent domains, weak domains (max_conf<0.4), absent grahas. The silence is itself informative. Returns domain_absent / domain_weak / graha_absent rows with interpretation hints.';


-- ── §4 — Salience Lens ────────────────────────────────────────────────────────
--
-- Ranks signals by composite_salience:
--   = confidence x salience x (1 + reinforcement_count/10) x domain_weight
--
-- Domain weights: career=1.0, wealth=0.9, relationships=0.85, health=0.8,
--                 spirit=0.75, mind=0.75, travel=0.70, parents=0.70,
--                 dasha=0.80, nadi_bnn=0.75, yogini_tajaka=0.70, house_domain=0.65

CREATE OR REPLACE FUNCTION bodha_salience_lens(
    p_chart_id      TEXT,
    p_min_conf      NUMERIC DEFAULT 0.0,
    p_min_salience  NUMERIC DEFAULT 0.0,
    p_limit         INT     DEFAULT 50
)
RETURNS TABLE (
    rank                INT,
    signal_id           TEXT,
    signal_name         TEXT,
    domain              TEXT,
    valence             TEXT,
    confidence          NUMERIC,
    base_salience       NUMERIC,
    reinforcement_count BIGINT,
    domain_weight       NUMERIC,
    composite_salience  NUMERIC,
    claim_text          TEXT,
    source_citation     TEXT,
    grounding_status    TEXT
)
LANGUAGE sql
STABLE
AS $$
    WITH domain_weights(domain, weight) AS (
        SELECT d, w FROM (VALUES
            ('career',        1.00::NUMERIC),
            ('wealth',        0.90::NUMERIC),
            ('relationships', 0.85::NUMERIC),
            ('health',        0.80::NUMERIC),
            ('spirit',        0.75::NUMERIC),
            ('mind',          0.75::NUMERIC),
            ('travel',        0.70::NUMERIC),
            ('parents',       0.70::NUMERIC),
            ('dasha',         0.80::NUMERIC),
            ('nadi_bnn',      0.75::NUMERIC),
            ('yogini_tajaka', 0.70::NUMERIC),
            ('house_domain',  0.65::NUMERIC)
        ) AS t(d, w)
    ),
    reinforcement_counts AS (
        SELECT
            g.from_signal_id AS signal_id,
            COUNT(*)          AS reinforce_count
        FROM public.bodha_graph g
        WHERE g.chart_id  = p_chart_id
          AND g.edge_type = 'REINFORCES'
        GROUP BY g.from_signal_id
    )
    SELECT
        ROW_NUMBER() OVER (ORDER BY
            (s.confidence
             * s.salience
             * (1.0 + COALESCE(rc.reinforce_count, 0)::NUMERIC / 10.0)
             * COALESCE(dw.weight, 0.70)
            ) DESC
        )::INT                                              AS rank,
        s.signal_id,
        s.signal_name,
        s.domain,
        s.valence,
        s.confidence,
        s.salience                                          AS base_salience,
        COALESCE(rc.reinforce_count, 0)                    AS reinforcement_count,
        COALESCE(dw.weight, 0.70)                          AS domain_weight,
        ROUND(
            (s.confidence
             * s.salience
             * (1.0 + COALESCE(rc.reinforce_count, 0)::NUMERIC / 10.0)
             * COALESCE(dw.weight, 0.70)
            )::NUMERIC, 6
        )                                                   AS composite_salience,
        s.claim_text,
        s.source_citation,
        s.grounding_status
    FROM public.bodha_signals s
    LEFT JOIN domain_weights dw ON dw.domain = s.domain
    LEFT JOIN reinforcement_counts rc ON rc.signal_id = s.signal_id
    WHERE s.chart_id    = p_chart_id
      AND s.confidence >= p_min_conf
      AND s.salience   >= p_min_salience
    ORDER BY composite_salience DESC
    LIMIT p_limit
$$;

COMMENT ON FUNCTION bodha_salience_lens(TEXT, NUMERIC, NUMERIC, INT) IS
'BO-2-5 salience lens: ranks signals by composite_salience = confidence x base_salience x (1+reinforcement_count/10) x domain_weight. Domain weights: career=1.0, wealth=0.9, ..., house_domain=0.65. Signals reinforced by bodha_graph REINFORCES edges rank higher.';


-- ── §5 — Unified entry point: query_signals with lens parameter ───────────────
--
-- Extends BO-2-1 query_signals with a lens= parameter. When lens is NULL,
-- behaves identically to the BO-2-1 plain signal list.

CREATE OR REPLACE FUNCTION bodha_query_signals_with_lens(
    p_chart_id      TEXT,
    p_lens          TEXT    DEFAULT NULL,
    p_domain        TEXT    DEFAULT NULL,
    p_valence       TEXT    DEFAULT NULL,
    p_min_conf      NUMERIC DEFAULT 0.0,
    p_grounding     TEXT    DEFAULT NULL,
    p_limit         INT     DEFAULT 100,
    p_offset        INT     DEFAULT 0
)
RETURNS JSONB
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_result JSONB;
BEGIN
    CASE LOWER(COALESCE(p_lens, 'default'))

        WHEN 'concordance' THEN
            SELECT jsonb_agg(row_to_json(r))
            INTO   v_result
            FROM   bodha_concordance_lens(p_chart_id, p_min_conf) AS r
            WHERE  (p_domain  IS NULL OR r.domain  = p_domain)
              AND  (p_valence IS NULL OR r.valence = p_valence);

        WHEN 'contradiction' THEN
            SELECT jsonb_agg(row_to_json(r))
            INTO   v_result
            FROM   bodha_contradiction_lens(p_chart_id, GREATEST(p_min_conf, 0.3)) AS r
            WHERE  (p_domain IS NULL OR r.domain = p_domain);

        WHEN 'negative_space' THEN
            SELECT jsonb_agg(row_to_json(r))
            INTO   v_result
            FROM   bodha_negative_space(p_chart_id) AS r;

        WHEN 'salience' THEN
            SELECT jsonb_agg(row_to_json(r))
            INTO   v_result
            FROM   bodha_salience_lens(p_chart_id, p_min_conf, 0.0, p_limit) AS r
            WHERE  (p_domain  IS NULL OR r.domain  = p_domain)
              AND  (p_valence IS NULL OR r.valence = p_valence);

        ELSE
            SELECT jsonb_agg(row_to_json(s) ORDER BY s.salience DESC, s.confidence DESC)
            INTO   v_result
            FROM   public.bodha_signals s
            WHERE  s.chart_id   = p_chart_id
              AND  (p_domain    IS NULL OR s.domain           = p_domain)
              AND  (p_valence   IS NULL OR s.valence          = p_valence)
              AND  s.confidence >= p_min_conf
              AND  (p_grounding IS NULL OR s.grounding_status = p_grounding)
            LIMIT  p_limit OFFSET p_offset;

    END CASE;

    RETURN COALESCE(v_result, '[]'::JSONB);
END;
$$;

COMMENT ON FUNCTION bodha_query_signals_with_lens(TEXT, TEXT, TEXT, TEXT, NUMERIC, TEXT, INT, INT) IS
'BO-2-5 unified entry point: bodha_query_signals_with_lens(chart_id, lens, ...). lens=concordance|contradiction|salience|negative_space|NULL. NULL = plain BO-2-1 signal list. All lens functions are computed over bodha_signals + bodha_graph; no new tables required.';

COMMIT;

-- ── Notes ─────────────────────────────────────────────────────────────────────
--
-- Population: no bootstrap needed — all functions are computed views over existing data.
--   bodha_signals (BO-2-1) must be seeded first.
--   bodha_graph (BO-2-2) must be seeded for REINFORCES/CONTRADICTS edges to be used
--   in salience and contradiction lenses respectively.
--
-- MCP tool: platform-mcp/src/tools/bo_2-5.ts
--
-- Python engine: platform/python-sidecar/brahmagyan/bodha/bo_2-5.py
--
-- Acceptance gate (BO-2-5):
--   contradiction_lens: SELECT * FROM bodha_contradiction_lens('<native_chart_id>', 0.3)
--     must return >= 1 row (at least one contradiction-hub in the native chart)
--   negative_space: SELECT * FROM bodha_negative_space('<native_chart_id>')
--     non-error execution; result set is informational
--   salience_lens: SELECT * FROM bodha_salience_lens('<native_chart_id>', 0, 0, 5)
--     must return 5 rows ordered by composite_salience DESC
