-- Migration 538: bg_gochara_arcs — the chart-independent monotone-arc substrate
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · wave W2G (GOCHARA-2.0, item 19) · the global half of
-- the 2.0 engine. Rulings this table is built under: ADJUDICATION-3 (W2G is the
-- wave id), -5 (calendar epoch = the ephemeris floor, 1900), -6 (2.0 is built
-- BESIDE v1, generation-stamped, v1 rows never touched), -14 (three-tier
-- materialization). Lane (b) design amendments 1 and 2 (production-scalability
-- keystone SLO; delta-aware invalidation) are both load-bearing here.
--
-- ── WHAT THIS TABLE IS ───────────────────────────────────────────────────────
-- Every graha's motion in ecliptic longitude, over the whole 1900–2150
-- ephemeris epoch, decomposed into MONOTONE ARCS: maximal intervals on which
-- longitude is a strictly monotone function of time AND stays within a single
-- 360° band. Cut points are (a) real stations — roots of the interpolated
-- velocity, sign-change-confirmed — and (b) 360° wrap boundaries.
--
-- The consequence, which is the entire point:
--
--     "when does body B reach degree L?"  becomes a RANGE PREDICATE
--     (lon_lo_deg <= L <= lon_hi_deg) followed by ONE bracketed bisection
--     inside the arc it returns — never a day-stepping scan.
--
-- ── WHY IT IS GLOBAL (the production-scalability keystone) ───────────────────
-- When Saturn reaches 123.45° does not depend on any native's birth data. So
-- the expensive half of a century-long transit computation is CHART-INDEPENDENT
-- and is paid ONCE, here, for every chart that will ever onboard. What remains
-- per chart is a join against these rows plus scoring — a different cost SHAPE,
-- not a faster version of the same shape. W2G's gate criterion (design
-- amendment 1): a new chart's full-century temporal build completes in
-- ≤15 minutes on Nirmāṇa Build.
--
-- ── THE MEASURED PREMISE THIS REPLACES ──────────────────────────────────────
-- v1's dominant cost was measured at ~110–120ms PER contact-primitive call,
-- "regardless of whether it touches the DB at all"
-- (services/gochara_intensity/configuration_activity.py's own documented
-- finding, independently re-confirmed by clean A/B measurement 2026-08-04 —
-- SHAD_DARSHANA_STATE.md lane (a), which also FALSIFIED the earlier premise
-- that ephemeris/kinematics recomputation was the bottleneck). Multiply that
-- floor by (targets × primitives × windows) and it reproduces the measured
-- 550–650s for a THIRTY-DAY window almost exactly. The fix is not a faster
-- call; it is an architecture with no per-primitive call to make. A chart's
-- whole contact computation reads this table in ONE query.
--
-- ── MEASURED ROW COUNTS (live, read-only, against production, 2026-08-05) ────
-- Built over the full stored epoch (1900-01-01 → 2150-12-31, 91,676 knots per
-- body, ayanamsha_id='tropical'):
--
--     Sun         252 arcs   (0 retrograde)
--     Moon      3,357        (0)                    Tier C — lazy
--     Mars        376        (121)
--     Mercury   1,894        (821)
--     Jupiter     494        (236)
--     Venus       580        (164)
--     Saturn      503        (247)
--     Rahu     13,544        (6,870)                see NODE NOTE below
--     Ketu     13,553        (6,875)
--     ────────────────────────────────────────
--     TOTAL    34,553 arcs, whole-epoch build ~48s wall clock, all nine bodies.
--
-- ── THE SLO, MEASURED (live, read-only, production data, 2026-08-05) ────────
-- W2G's gate criterion is "a new chart's full-century temporal build completes
-- in ≤15 minutes on Nirmāṇa Build". Measured end-to-end against chart
-- 482012f1 at its REAL resonance-map size (76 distinct target refs, 6 event
-- classes), over the FULL 1900–2150 epoch (250 years, not one century):
--
--     global arc build, ONCE, shared by every chart .......... 36.8s
--     per-chart contact solve, Tier A only ...... 17,191 contacts in  1.95s
--     per-chart contact solve, Tier A+B ......... 79,949 contacts in  8.69s
--     per-chart contact solve, all nine ........ 334,959 contacts in 37.26s
--
-- ~111 microseconds per contact — against v1's ~110–120 MILLIseconds per
-- contact-primitive call. Same three digits, a thousandfold apart, and that is
-- the whole architectural claim in one line. For scale: v1's per-chart sweep is
-- ~606 substeps at ~255–280s each (tens of hours). This is the contact stream
-- only — scoring, grammar and shape assembly are still to be layered on top,
-- and the SLO is not discharged until they are measured too. Recorded as a
-- real measurement of the substrate half, not as a claim about the whole build.
--
-- ── NODE NOTE (a real, disclosed finding — NOT fixed by this migration) ─────
-- Rahu/Ketu produce ~13.5k arcs each because `brahmagyan.l0_ephemeris` computes
-- them with `swe_id=11`, which in pyswisseph is **SE_TRUE_NODE** (SE_MEAN_NODE
-- is 10) — while that line's own inline comment reads "# Mean North Node". The
-- stored series is therefore the TRUE node, which really does oscillate:
-- measured here as retrograde stretches of median 0.71° over ~9.9 days
-- interleaved with brief direct excursions of median 0.043°. That oscillation
-- is genuine geometry, so the arc decomposition MUST split at it — an arc that
-- silently spanned a direction reversal would no longer be monotone and its
-- unique-crossing invariant (which the bisection depends on) would be false.
--
-- This is deliberately NOT reconciled here. Classical convention treats
-- Rahu/Ketu as always retrograde and assigns no significance to those
-- excursions — a convention `pipeline.transit_search.find_station_events` and
-- `bg_sky_calendar` both already encode by excluding the nodes from STATION
-- events. That is a GRAMMAR decision, frozen at v1 per design §5 ("2.0 changes
-- HOW, never WHAT"); this table is geometry only. The mislabelled comment in
-- l0_ephemeris.py is filed as a finding for the campaign ledger, not patched
-- from inside this lane.
--
-- ── IDEMPOTENCY (§N.3, applied faithfully rather than literally) ────────────
-- §N.3 gives L0 `ON CONFLICT DO UPDATE` because L0 tables are typically FIXED
-- reference constants where an upsert cannot leave anything stale. These rows
-- are DERIVED: a rebuild under a changed engine version can legitimately
-- produce FEWER arcs for a body, and a pure upsert would leave the surplus tail
-- of the previous run behind as orphans — silently corrupting the range join
-- with arcs that no longer exist. So the writer does DELETE-then-INSERT scoped
-- to (substrate_version × body), which is §N.3's actual rule — "a rebuild
-- REPLACES, never accretes" — applied to a derived global asset. The scope is
-- exactly one substep's worth of work, so a crash mid-build cannot half-replace
-- a body.
--
-- ── DELTA-AWARE INVALIDATION (design amendment 2) ───────────────────────────
-- `arc_fingerprint` is PER BODY, never one hash over everything. v1 computes a
-- single build fingerprint that includes the whole event-class list, which is
-- why item 9's one-class addition forced a full ~606-substep replan per chart
-- (SHAD_DARSHANA_STATE.md). Per-body fingerprints mean an invalidation is
-- exactly as wide as the change that caused it: re-deriving Saturn does not
-- touch Jupiter's arcs, and the per-class fingerprints the per-chart layer
-- stores compose these rather than re-hashing the world.
--
-- ── NIRMĀṆA CONTRACT (brief §2.5) ───────────────────────────────────────────
-- Global L0 asset, `scope='global'`, built ONLY via an explicit super-admin L0
-- trigger — never auto-pulled into a per-chart build (§2.5.2). Its
-- asset_registry seed row lands in the same PR as the writer (§2.5.1), with a
-- chart-scoped-by-construction count_sql (a global asset counts globally).
--
-- ── UNTOUCHABLES ────────────────────────────────────────────────────────────
-- This migration does not read, write, alter or reference `kala_gochara_windows`
-- in any way. v1 sweep data is untouched, as the standing rail requires.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS bg_gochara_arcs (
    substrate_version        TEXT             NOT NULL,
    body                     TEXT             NOT NULL,
    arc_index                INTEGER          NOT NULL,

    -- Time bounds (noon-UT Julian day — the abscissa ephemeris_daily rows were
    -- built at; a midnight-knot assumption is wrong by half a day, ~6.6° for
    -- the Moon, as W2G validation V3 measured).
    start_jd                 DOUBLE PRECISION NOT NULL,
    end_jd                   DOUBLE PRECISION NOT NULL,

    -- Longitude bounds on the CONTINUOUS (unwrapped) branch, so arithmetic
    -- across a band boundary stays sane...
    start_lon_unwrapped_deg  DOUBLE PRECISION NOT NULL,
    end_lon_unwrapped_deg    DOUBLE PRECISION NOT NULL,

    -- ...and the WRAPPED bounds the range join actually reads. Because an arc
    -- never spans more than one revolution, "does this arc reach degree L" is
    -- exactly `lon_lo_deg <= L AND L <= lon_hi_deg`. No modular arithmetic, no
    -- special case at 0°/360°.
    lon_lo_deg               DOUBLE PRECISION NOT NULL,
    lon_hi_deg               DOUBLE PRECISION NOT NULL,

    direction                SMALLINT         NOT NULL,
    wrap_index               INTEGER          NOT NULL,

    -- Delta-aware invalidation identity, per body.
    arc_fingerprint          TEXT             NOT NULL,
    engine_version           TEXT             NOT NULL,

    ayanamsha_id             TEXT             NOT NULL DEFAULT 'tropical',
    build_id                 TEXT,
    computed_at              TIMESTAMPTZ      NOT NULL DEFAULT now(),

    CONSTRAINT bg_gochara_arcs_pk
        PRIMARY KEY (substrate_version, body, arc_index),

    CONSTRAINT bg_gochara_arcs_direction_ck
        CHECK (direction IN (-1, 1)),

    CONSTRAINT bg_gochara_arcs_time_ordered_ck
        CHECK (end_jd > start_jd),

    -- The invariant the range-join predicate's exactness rests on. Enforced by
    -- the database, not only by the builder: an arc that spanned more than one
    -- revolution could contain a degree twice, and the join would silently
    -- return one contact where two occurred. 1e-6 tolerance absorbs float
    -- representation only.
    CONSTRAINT bg_gochara_arcs_sub_revolution_ck
        CHECK (lon_hi_deg - lon_lo_deg <= 360.000001),

    CONSTRAINT bg_gochara_arcs_bounds_ordered_ck
        CHECK (lon_hi_deg >= lon_lo_deg),

    CONSTRAINT bg_gochara_arcs_wrapped_bounds_ck
        CHECK (lon_lo_deg >= -0.000001 AND lon_hi_deg <= 360.000001)
);

COMMENT ON TABLE bg_gochara_arcs IS
    'W2G (GOCHARA-2.0) chart-independent monotone-arc substrate: every graha''s '
    'longitude history over the 1900-2150 ephemeris epoch, cut at real stations '
    'and 360-degree wrap boundaries so that longitude is strictly monotone on '
    'each row. Turns "when does body B reach degree L" from a day-stepping scan '
    'into a range predicate plus one bracketed bisection. Chart-INDEPENDENT by '
    'construction, so a century of transit geometry is computed once and shared '
    'by every chart that onboards. Global L0 asset (bg_gochara_arcs), '
    'super-admin-triggered only. Does not touch kala_gochara_windows.';

COMMENT ON COLUMN bg_gochara_arcs.substrate_version IS
    'Zero-padded version tag (arcs_v01). A revision lands as a NEW version''s '
    'row set; the previous version stays queryable so a per-chart layer pinned '
    'to it keeps resolving, exactly as the generation discriminator on '
    'kala_gochara_windows (migration 527) does for served rows.';

COMMENT ON COLUMN bg_gochara_arcs.arc_fingerprint IS
    'Delta-aware invalidation identity for THIS BODY''s arc set: engine version '
    '+ body + epoch bounds + knot count. Per-body, never one hash over '
    'everything -- the defect that made item 9''s one-class addition force a '
    'full 606-substep replan in v1.';

COMMENT ON COLUMN bg_gochara_arcs.direction IS
    '+1 direct, -1 retrograde. For Rahu/Ketu this reflects the TRUE node stored '
    'in ephemeris_daily (swe_id=11 = SE_TRUE_NODE), which genuinely oscillates; '
    'whether such an excursion carries classical significance is a grammar '
    'question, frozen at v1, not this table''s to answer.';

CREATE INDEX IF NOT EXISTS bg_gochara_arcs_degree_join_idx
    ON bg_gochara_arcs (substrate_version, body, lon_lo_deg, lon_hi_deg);

CREATE INDEX IF NOT EXISTS bg_gochara_arcs_time_idx
    ON bg_gochara_arcs (substrate_version, body, start_jd, end_jd);

CREATE INDEX IF NOT EXISTS bg_gochara_arcs_fingerprint_idx
    ON bg_gochara_arcs (substrate_version, body, arc_fingerprint);

-- ── asset_registry seed row (Nirmāṇa contract §2.5.1 — SAME PR as the writer) ─
--
-- target_floor PROVENANCE, stated exactly rather than rounded into a claim it
-- has not earned (§N.4 — floors are aspirational, never fabricated): 34,553 is
-- a REAL derivation, run by this migration's own arc builder against
-- production `ephemeris_daily` READ-ONLY on 2026-08-05 (whole-epoch build ~48s
-- wall clock, all nine bodies). It is NOT a post-INSERT `count_sql` reading --
-- the writer had not yet run in production when this row landed -- and it is
-- not an estimate. Re-verify with count_sql after the first super-admin L0
-- build; a later build reading a different number under a new
-- substrate_version is expected, not a regression.
--
-- has_substeps = true: the writer plans one substep per body (9), so each body
-- is its own savepoint + heartbeat and a crash resumes at the failed body.
-- depends_on = [] deliberately: see the seed-file comment in
-- scripts/seed/asset_registry_seed.ts for why the bg_ephemeris edge is NOT
-- added speculatively.

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind,
    depends_on
) VALUES (
    'bg_gochara_arcs',
    'brahmagyan',
    77,
    'Gocara Cāpa-Vibhāga',
    'Transit Monotone-Arc Substrate',
    'W2G (GOCHARA-2.0, item 19). Chart-independent decomposition of every '
    'graha''s ecliptic-longitude history over the stored 1900-2150 ephemeris '
    'epoch into MONOTONE ARCS: maximal intervals on which longitude is strictly '
    'monotone in time and confined to a single 360-degree band, cut at real '
    'stations (sign-change-confirmed roots of the interpolated velocity) and at '
    '360-degree wrap boundaries. Turns "when does body B reach degree L" from a '
    'day-stepping ephemeris scan into a range predicate plus one bracketed '
    'bisection -- which is what removes the ~110-120ms-per-contact-primitive-call '
    'cost measured in the v1 sweep. Carries a per-body arc_fingerprint so an '
    'invalidation is exactly as wide as the change that caused it. Geometry '
    'only: no grammar, no orbs, no astrology -- those stay frozen at v1 per '
    'GOCHARA_SWEEP_2_0_DESIGN section 5.',
    'postgres_table', 'bg_gochara_arcs',
    'SELECT COUNT(*) FROM bg_gochara_arcs',
    'SELECT pg_total_relation_size(''bg_gochara_arcs'')',
    34553, 'global', true, true, true,
    1800,
    'Brahmagyan', 'L0', 'CURRENT', 'data',
    ARRAY[]::text[]
)
ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    size_sql                = EXCLUDED.size_sql,
    target_table            = EXCLUDED.target_table,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    writer_timeout_seconds  = EXCLUDED.writer_timeout_seconds,
    sort_order              = EXCLUDED.sort_order,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description,
    target_floor            = EXCLUDED.target_floor,
    depends_on              = EXCLUDED.depends_on;

COMMIT;
