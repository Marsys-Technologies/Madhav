-- Migration 1091: WP10 step 5 — ka_gochara registry re-pin (plan §6.3 re-pin
--                 list; GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 step 5).
-- Created: 2026-09-24. Author: l3/gochara-autonomous-wp0-7 §7.B tranche 1.
--
-- Numbering: 1091 is the lowest free number by a fresh E-009-discipline scan at
-- tranche-1 start of every origin/* head across both migration directories
-- plus the local head (this family 1080–1084+1086/1087; Saṅgam stage3 carries
-- 1088–1090 in platform/supabase/migrations; 1085 retired per E-010). MIG-1
-- guard run after placement: npm run guard:migration-numbers.
--
-- This file is the numbered form of the preparation artifact
-- platform/python-sidecar/scripts/kala_gochara_cutover/step05_registry_repin.sql
-- (that copy remains as the preparation record, per its header). Applied to
-- production during WP10 tranche 1 under PRODUCTION_TRANCHE_1_AUTHORIZED=true;
-- evidence: kala_gochara_cutover/evidence/step05_evidence.md.
--
-- Reversal: platform/python-sidecar/scripts/kala_gochara_cutover/step05_reversal.sql
-- (restores the pre-step-5 registry rows from the snapshot table written first
-- below).
--
-- TYPE CORRECTION (2026-09-24, tranche-1 run): the two clear_tables literals
-- below use Postgres array syntax '{...}', not the preparation copy's
-- '[...]'. Production asset_registry.clear_tables is text[]; the rehearsal
-- harness (test_wp10_cutover.py) declared it TEXT, so the rehearsal did not
-- catch the malformed '[...]' literal. The first tranche-1 attempt aborted on
-- this error with production unchanged (transaction rolled back). This
-- correction was PREPARED but NOT re-run; tranche halted pending native
-- ruling (E-017). The preparation copy is intentionally left as-is — it is
-- the record of what was attempted.
--
-- step05_registry_repin.sql — WP10 runbook step 5 (plan §9): registry re-pin.
--
-- Tranche 1 (PRODUCTION_TRANCHE_1_AUTHORIZED). Sheet A-2.
--
-- MIGRATION NUMBERING: this file is deliberately UNNUMBERED at preparation
-- time. It receives its number at tranche-1 start, after the E-009 re-scan
-- discipline (highest numeric prefix across every origin/* and local head,
-- both migration directories) — five branches have already collided on
-- 1071–1079; do not guess. Once numbered it moves into platform/migrations/
-- and this copy remains as the preparation record.
--
-- Lifts, per plan §6.3 (registry re-pin list) and PACKET_C1 §4:
--   * count_sql       → kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'
--   * clear_tables    → the three relations, DISPLAY-ONLY (F-24 caveat below)
--   * integrity_check_sql → conjuncts (a)–(k) re-scoped per §6.3
--   * depends_on      → kernel-read assets incl. bg_transit_rules
--   * century row     → declare kala_gochara_windows in its clear_tables
--     (the one surviving item of the WITHDRAWN D-C record, F-30)
--   * target_floor    → deliberately NOT touched (stays 83 until WP10 sets the
--     achieved count, §N.4)
--   * digest spec 1018 → deliberately NOT touched here (retained for the '2.0'
--     residue until N-11; step 10 owns its disposition)
--   * ka_gochara_sweep row, century count_sql/target_table → unchanged (hold)
--
-- F-24 CAVEAT (must accompany this migration — PACKET_C1 §4): clear_tables is
-- DISPLAY ONLY — read by the Atlas display (atlas/schema/route.ts,
-- AtlasView.tsx, atlas/page.tsx), never by the Clear runtime. The actual
-- cleanup is the EXPLICIT_CLEAR_OPS['ka_gochara'] entry in
-- platform/src/lib/cockpit/assetClearSpec.ts (packet C-1, landed on
-- l3/gochara-autonomous-wp0-7). Setting clear_tables without the explicit
-- entry would make the Atlas claim a cleanup the runtime does not perform —
-- the exact v2.0 error F-24 caught.
--
-- N-9 release conditions served here: (iii) conjunct (j) below pins
-- target_table = count_sql relation; (iv) the C-1 EXPLICIT_CLEAR_OPS entry
-- is landed code, not this migration; (v) this re-pin itself.
--
-- EXPECTED AND BENIGN (plan §9 step 5, stated so it is not misread as a
-- regression): between steps 5 and 6 cockpit shows 0 for ka_gochara, because
-- the count now asks about '4.0', which does not exist yet. The order
-- matters: reversed, the integrity conjuncts would still be scoped to '2.0'
-- while '4.0' rows existed, breaking conjunct (f).
--
-- Gate (runbook): count_sql relation = target_table; cockpit stats read the
-- new count; Clear-proof test green (C-1's acceptance test, packet §5).
--
-- Reversal: step05_reversal.sql (restores the pre-step-5 registry row from
-- the snapshot table this script writes first).

BEGIN;

-- Pre-state snapshot for the reversal (preparation-time rehearsal safety; on
-- a real tranche run this row is the rollback record).
CREATE TABLE IF NOT EXISTS kala_gochara_cutover_step05_snapshot (
  snapped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  asset_id TEXT PRIMARY KEY,
  count_sql TEXT, clear_tables TEXT, integrity_check_sql TEXT, depends_on TEXT[]
);
INSERT INTO kala_gochara_cutover_step05_snapshot
  (asset_id, count_sql, clear_tables, integrity_check_sql, depends_on)
SELECT asset_id, count_sql, clear_tables, integrity_check_sql, depends_on
FROM asset_registry
WHERE asset_id IN ('ka_gochara', 'ka_gochara_v3_century_materialize')
ON CONFLICT (asset_id) DO NOTHING;

-- ── ka_gochara: count_sql, clear_tables, depends_on ─────────────────────────

UPDATE asset_registry
   SET count_sql = 'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND generation=''4.0''',
       clear_tables = '{kala_gochara_windows, kala_gochara_contacts, kala_gochara_coverage}',
       depends_on = ARRAY['bg_ephemeris', 'bg_transit_rules', 'ka_gochara_resonance',
                          'ka_vedha_gochara', 'ka_moorti_nirnaya', 'ga_positions',
                          'ga_dashas', 'ga_yoga']::text[]
 WHERE asset_id = 'ka_gochara';

-- ── century (F-30, surviving D-C item): declare the shared windows table ────

UPDATE asset_registry
   SET clear_tables = '{kala_gochara_windows, kala_gochara_windows_v2}'
 WHERE asset_id = 'ka_gochara_v3_century_materialize';

-- ── ka_gochara: integrity conjuncts (a)–(k), re-scoped per plan §6.3 ────────
--
-- Re-scope note: the 670 contract's (a)/(b)/(e) keyed on the '2.0' writer's
-- own bookkeeping table (kala_gochara_v2_build_state), which the '4.0'
-- writer does not use — the ledger (contacts/coverage) and the publication
-- manifest are the '4.0' bookkeeping surfaces. The conjuncts below keep each
-- original's DETECTOR PURPOSE on the '4.0' surfaces; where a 670 conjunct had
-- no '4.0' analogue the comment says so rather than porting a meaningless
-- shape.

UPDATE asset_registry SET integrity_check_sql = $ck$
-- ka_gochara integrity contract (WP10 re-pin, plan §6.3). Scoped to generation '4.0'
-- on kala_gochara_windows plus the two owned relations kala_gochara_contacts /
-- kala_gochara_coverage, with the publication manifest kala_gochara_publication as
-- the generation's bookkeeping surface.
SELECT
  -- (a) §N.3 attribution, re-scoped: every '4.0' window is covered by at least one
  -- '4.0' coverage partition for the same chart — a window with no coverage record is
  -- output without a search manifest behind it (the 670 original detected rows with no
  -- build-state parent; the manifest/coverage pair is the '4.0' parent).
  NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    WHERE w.generation = '4.0'
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_coverage c
        WHERE c.chart_id = w.chart_id AND c.generation = '4.0'
      )
  )
  -- (b) §N.4/§N.8 earned signal, re-scoped: a published manifest's declared row_counts
  -- equal the rows actually present (contacts and coverage) for that (chart,
  -- generation). Candidates carry '{}' until publish() recomputes them, so this
  -- conjunct is scoped to status='published'.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_publication m
    WHERE m.status = 'published'
      AND m.row_counts <> '{}'::jsonb
      AND ((m.row_counts->>'contacts')::int IS DISTINCT FROM
             (SELECT count(*) FROM kala_gochara_contacts c
              WHERE c.chart_id = m.chart_id AND c.generation = m.generation)
        OR (m.row_counts->>'coverage')::int IS DISTINCT FROM
             (SELECT count(*) FROM kala_gochara_coverage c
              WHERE c.chart_id = m.chart_id AND c.generation = m.generation))
  )
  -- (c) §N.5: a '4.0' window may only exist for an event class this chart's resonance
  -- map declares. The targets are the upstream authority — unchanged in kind from 670.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    WHERE w.generation = '4.0'
      AND NOT EXISTS (
        SELECT 1 FROM gochara_resonance_map g
        WHERE g.chart_id = w.chart_id AND g.event_class = w.event_class
      )
  )
  -- (d) window well-formedness, scoped to '4.0' (670's scoping rationale carries: a
  -- whole-family conjunct would pin another writer's defect on this asset).
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    WHERE w.generation = '4.0'
      AND (w.window_end < w.window_start
        OR w.peak_date < w.window_start
        OR w.peak_date > w.window_end)
  )
  -- (e) D-TIME horizon disclosure, re-scoped: every '4.0' window lies inside the
  -- horizon its own manifest discloses (a row outside it is an undisclosed claim
  -- about a span the build never scanned).
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    JOIN kala_gochara_publication m
      ON m.chart_id = w.chart_id AND m.generation = w.generation
     AND m.status IN ('candidate', 'published')
    WHERE w.generation = '4.0'
      AND (w.window_start::timestamptz < lower(m.horizon)
        OR w.window_end::timestamptz > upper(m.horizon))
  )
  -- (f) THE UNTOUCHABLE-DATA RAIL, new form per §6.3: '4.0' rows in any of the three
  -- relations exist only with a candidate/published manifest behind them, AND no
  -- '2.0' row ever appears in the production relation.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    WHERE w.generation = '4.0'
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_publication m
        WHERE m.chart_id = w.chart_id AND m.generation = '4.0'
          AND m.status IN ('candidate', 'published')
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_contacts c
    WHERE c.generation = '4.0'
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_publication m
        WHERE m.chart_id = c.chart_id AND m.generation = '4.0'
          AND m.status IN ('candidate', 'published')
      )
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows p WHERE p.generation = '2.0'
  )
  -- (g) §N.3 generation hygiene, re-scoped: an era-stamped row inside generation '4.0'
  -- came from a different writer sharing the table.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    WHERE w.generation = '4.0' AND w.era_slice_key IS NOT NULL
  )
  -- (h) HARD-FLOOR CORPUS PRESENCE — kept verbatim from 670 per §6.3: for every chart
  -- this writer has materialized, the irreplaceable v1 corpus must still be present
  -- and strictly larger than this writer's layer for that chart.
  AND NOT EXISTS (
    SELECT 1 FROM (SELECT DISTINCT chart_id FROM kala_gochara_windows WHERE generation = '4.0') c
    WHERE (SELECT count(*) FROM kala_gochara_windows p
           WHERE p.chart_id = c.chart_id AND p.generation = 'v1')
          <= (SELECT count(*) FROM kala_gochara_windows w
              WHERE w.chart_id = c.chart_id AND w.generation = '4.0')
  )
  -- (i) sentence-identity resolution: every contact_id named in a '4.0' window's
  -- active_sentences resolves in the contact ledger for the same (chart, generation).
  -- Elements without a contact_id key are not sentence references and are not checked.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w,
         LATERAL jsonb_array_elements(w.active_sentences) s
    WHERE w.generation = '4.0'
      AND s ? 'contact_id'
      AND NOT EXISTS (
        SELECT 1 FROM kala_gochara_contacts c
        WHERE c.chart_id = w.chart_id AND c.generation = '4.0'
          AND c.contact_id = s->>'contact_id'
      )
  )
  -- (j) N-9 (iii): the registry row's target_table IS the relation its count_sql
  -- reads — the mismatch this re-pin exists to close can never silently reopen.
  AND (SELECT r.target_table FROM asset_registry r WHERE r.asset_id = 'ka_gochara')
      = (SELECT substring(r.count_sql from 'FROM ([a-z0-9_]+)')
         FROM asset_registry r WHERE r.asset_id = 'ka_gochara')
  -- (k) the Clear-the-authority / published-over-void detector: for every chart whose
  -- authority row names a '4.x' generation, that generation has at least one window
  -- AND a published manifest. Legacy authorities ('v1'/'3.0') are covered by (h);
  -- an absent authority row reads as 'v1' by the 527 contract and is out of scope.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_authority a
    WHERE a.authoritative_generation LIKE '4.%'
      AND ((SELECT count(*) FROM kala_gochara_windows w
            WHERE w.chart_id = a.chart_id
              AND w.generation = a.authoritative_generation) = 0
        OR NOT EXISTS (
            SELECT 1 FROM kala_gochara_publication m
            WHERE m.chart_id = a.chart_id
              AND m.generation = a.authoritative_generation
              AND m.status = 'published'))
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_gochara';

-- Gate probe (§N.8): the conjunct (j) equality must hold for the row just
-- written, and the new count_sql must mention generation '4.0'.
DO $$
DECLARE
  r RECORD;
BEGIN
  SELECT target_table, count_sql INTO r FROM asset_registry WHERE asset_id = 'ka_gochara';
  IF r.target_table IS DISTINCT FROM substring(r.count_sql from 'FROM ([a-z0-9_]+)') THEN
    RAISE EXCEPTION 'step 5 gate failed: target_table != count_sql relation for ka_gochara';
  END IF;
  IF r.count_sql NOT LIKE '%generation=''4.0''%' THEN
    RAISE EXCEPTION 'step 5 gate failed: count_sql not re-scoped to generation 4.0';
  END IF;
END $$;

COMMIT;
