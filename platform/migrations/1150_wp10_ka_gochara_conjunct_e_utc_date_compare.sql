-- Migration 1150: WP10 — ka_gochara conjunct (e) UTC date-compare CORRECTNESS fix
--                 (E-020 disposition, ADK-0026; native-authorized:
--                 PRODUCTION_MIGRATION_AUTHORIZED for THIS migration only,
--                 conditional on dual-timezone disposable rehearsal GREEN and
--                 PRAMĀṆIN's pass; apply through migrate.ts, NEVER
--                 apply_migration.sh).
-- Created: 2026-09-28. Author: l3/gochara-autonomous-wp0-7 (E-020 execution).
--
-- Numbering: 1150 is the first number of this lane's granted block
-- (1150–1159 per ADK-0026 §4). Verified free by a fresh scan of every
-- origin/* ref (1087 refs) across BOTH platform/migrations/ and
-- platform/supabase/migrations/ — no 1126–1159 file exists anywhere.
--
-- What this fixes: migration 1091's conjunct (e) compared
--   w.window_start::timestamptz < lower(m.horizon)
-- The `date::timestamptz` cast evaluates at the SESSION TimeZone, while the
-- manifest horizon is a UTC tzrange — the detector's verdict therefore
-- depended on which timezone the evaluating session ran in (an Asia/Kolkata
-- session reads 2020-01-01 as 2019-12-31T18:30Z). The detector now compares
-- dates as dates in UTC:
--   w.window_start < (lower(m.horizon) AT TIME ZONE 'UTC')::date
--   w.window_end   > (upper(m.horizon) AT TIME ZONE 'UTC')::date
-- Semantics preserved: the horizon range is half-open [lower, upper), so a
-- window dated date(lower) is inside and a window dated date(upper) is the
-- boundary day (the component was clipped AT the scanned boundary) — the
-- strict `>` on the upper comparison is the timezone-correct form of the
-- original semantics, NOT a relaxation. Every other conjunct byte-identical
-- to 1091.
--
-- Context (disclosed, per ADK-0026 §6 and the E-020 evidence): conjunct (e)
-- AS WRITTEN IN 1091 correctly caught 39 genuinely-wrong horizon-edge rows
-- (window_start = 2019-12-31 vs horizon 2020-01-01T00:00Z; chart 482012f1:
-- 12 era; chart 1c826d5a: 13 era + 7 month + 7 day) produced by the '4.0'
-- writer's noon-UTC JD-day flooring defect (00:00–11:59 UTC instants dated
-- one day early). The DATA was fixed (E-020 path (i): true-inverse
-- midnight-UTC convention in step06b_windows_projection.py and
-- legacy_semantics.py:1331,1342; projections regenerated). This migration
-- fixes the detector's residual timezone dependence found while rehearsing
-- that fix. Detector text before: migration 1091 (sha recorded in
-- _migrations_applied); after: this file.
--
-- Rehearsal (disposable copy of the production dump + corrected '4.0'
-- projection): full (a)–(k) GREEN under BOTH SET TimeZone='UTC' AND
-- SET TimeZone='Asia/Kolkata'. Evidence:
-- kala_gochara_cutover/evidence/link3_conditioning_evidence.md (E-020 section).
--
-- Deferred: production apply is NOT performed at authoring time — it awaits
-- PRAMĀṆIN's pass, then runs through migrate.ts (ledger row in the same
-- transaction, migrate.ts-computed sha256/sql_identity, --dry-run
-- verification after).

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
  -- about a span the build never scanned). Migration 1150 (E-020/ADK-0026)
  -- CORRECTNESS fix: the comparison is now date-vs-date in UTC — the manifest
  -- horizon is a UTC tzrange, and the prior `window_start::timestamptz` cast
  -- evaluated at the SESSION TimeZone (Asia/Kolkata sessions shifted the window
  -- date's midnight by -05:30), so the detector's verdict depended on the
  -- session timezone. The horizon range is half-open [lower, upper): a window
  -- dated date(lower) is inside; a window dated date(upper) is the boundary
  -- day itself (the component was clipped AT the scanned boundary) and is not
  -- an undisclosed claim — hence strict `>` on the upper comparison, the
  -- timezone-correct form of the original semantics. Nothing else tolerated.
  AND NOT EXISTS (
    SELECT 1 FROM kala_gochara_windows w
    JOIN kala_gochara_publication m
      ON m.chart_id = w.chart_id AND m.generation = w.generation
     AND m.status IN ('candidate', 'published')
    WHERE w.generation = '4.0'
      AND (w.window_start < (lower(m.horizon) AT TIME ZONE 'UTC')::date
        OR w.window_end > (upper(m.horizon) AT TIME ZONE 'UTC')::date)
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

-- Gate probe (§N.8): the amended conjunct (e) must be present in UTC
-- date-compare form, and no other conjunct may have drifted from 1091's text
-- (guarded here by the two anchor substrings that flank conjunct (e)).
DO $$
DECLARE
  t TEXT;
  code TEXT;
BEGIN
  SELECT integrity_check_sql INTO t FROM asset_registry WHERE asset_id = 'ka_gochara';
  IF t IS NULL OR position('(lower(m.horizon) AT TIME ZONE ''UTC'')::date' IN t) = 0
     OR position('(upper(m.horizon) AT TIME ZONE ''UTC'')::date' IN t) = 0 THEN
    RAISE EXCEPTION 'migration 1150: conjunct (e) UTC date-compare not present after apply';
  END IF;
  -- The amended conjunct's own comment names the old `::timestamptz` cast
  -- (as prose, in backticks) to document what was removed; the survival check
  -- must therefore run against the SQL with -- comments stripped.
  code := regexp_replace(t, '--[^\n]*', '', 'g');
  IF position('window_start::timestamptz' IN code) > 0
     OR position('window_end::timestamptz' IN code) > 0 THEN
    RAISE EXCEPTION 'migration 1150: session-tz timestamptz cast survived the apply';
  END IF;
  IF position('(k) the Clear-the-authority / published-over-void detector' IN t) = 0
     OR position('(a) §N.3 attribution, re-scoped' IN t) = 0 THEN
    RAISE EXCEPTION 'migration 1150: neighbouring conjunct text drifted';
  END IF;
END $$;
