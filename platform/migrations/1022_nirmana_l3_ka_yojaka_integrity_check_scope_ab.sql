-- 1022_nirmana_l3_ka_yojaka_integrity_check_scope_ab.sql
--
-- NIRMĀṆA L3 Kāla — CONDUCTOR follow-up ruling on #2542 (2026-09-10T15:19:15Z), correcting the
-- 06:36:56Z ruling on the same issue. Extends migration 1019's Option-B canonical-only scoping
-- from conjunct (c) to conjuncts (a) and (b) of ka_yojaka's integrity_check_sql.
--
-- Two canonical-scoped `ka_yojaka` redispatch attempts (runs f6b1699e-9bfe-4b40-a433-e03c6b685733
-- and 5146ed9d-848a-4135-b404-ed2984b2ac86) both failed identically on conjuncts (a)/(b), which
-- migration 1019 left table-wide on the stated premise ("(a), (b) ... already pass table-wide
-- today") — that premise was wrong. Live-verified this cycle, matching the ruling exactly:
--
--   chart_id    total   violates_(a)   violates_(b)
--   1c826d5a    50171   0              0
--   482012f1    50104   50104          50678 (of 50678 signals)
--   cb73cd3d    49875   49730          49730
--
-- Root cause: NOT cross-chart contamination. Canonical's (482012f1) own kala_activation_predicates
-- rows are stale relative to the current bodha_msr_signals signal_id scheme (built against the old
-- non-deterministic v4 ids before the L2 determinism fix moved bodha_msr_signals to deterministic
-- v5 ids) — zero overlap between the two id sets for canonical today. Conjunct (a) is working
-- exactly as designed (its own header: "detects a bo_laksana rebuild that re-issues signal_ids,
-- leaving the whole predicate set pointing at dead rows") — it caught a real staleness condition.
--
-- cb73cd3d's violation is separately real, pre-existing, and independent of canonical's staleness
-- (migration 1019's own inline comment for conjunct (a) already documented "cb73cd3d violates this
-- on 49,730 of its 49,875 rows" at authoring time). Because dispatch_nirmana_campaign_wave.py can
-- only ever rebuild the canonical chart (the same restriction that justified scoping conjunct (c)
-- in migration 1019), cb73cd3d's table-wide contribution to (a)/(b) can never be cleared by
-- anything this campaign's dispatch does — the check is structurally unpassable regardless of how
-- correct a canonical rebuild is, for the identical reason conjunct (c) was scoped.
--
-- RULED: scope conjuncts (a) and (b) to canonical-only, mirroring (c)'s existing migration-1019
-- scope exactly (same disclosed-tradeoff precedent: migrations 882/884/902/1019-c). Abhinandan
-- (1c826d5a) currently passes both conjuncts at 0 violations, so this trades away no live coverage
-- anywhere it currently holds. cb73cd3d's real, pre-existing violations remain tracked separately,
-- out of this campaign's canonical-only certification scope — not declared fixed by this migration.
-- Conjuncts (d), (e), (f) remain byte-identical to migration 1019's text (unaffected, already pass).
--
-- Routing note (per the ruling): this is the mechanical extension of the already-ratified (c)
-- pattern to (a)/(b), not a new class of decision — L3 has standing authority for kala_* asset
-- integrity-check fixes of this shape (same precedent as #2556/migration 1020's conjunct-(d) fix),
-- no further Conductor sign-off required for this specific change.
--
-- Numbered 1022 (not 1021): this cycle's own `ka_avadhi` PR #2556 was found mid-cycle to have a
-- stale duplicate number (1020, collided with the independently-merged bo_anveshana migration
-- 1020) and was renumbered to 1021 as a separate PR-hygiene fix -- see that file's own header.
-- This migration claims the next free slot after that rename, verified via `git ls-tree -r
-- origin/main --name-only -- platform/migrations/` immediately before authoring.
--
-- Verified against live production BEFORE this migration (read-only, non-mutating, this cycle):
-- canonical-scoped (a)/(b) violation counts are 50104/50104 and 50678/50678 respectively —
-- identical to the ruling's own numbers. This migration is a genuine no-op against CURRENT data
-- (conjuncts (a)/(b) still read FALSE for canonical immediately after, same as table-wide today,
-- because canonical's own rows are the violation, not a chart being excluded) — it only changes
-- behavior once a fresh canonical ka_yojaka rebuild lands v5-consistent signal_ids. Overall
-- integrity_passed for ka_yojaka remains FALSE before and immediately after this migration.
--
-- Post-apply verification (N.4/N.8 — never trust a silent no-op): expect UPDATE 1, then
-- re-running the check_sql verbatim against live kala_activation_predicates should still return
-- integrity_passed=f (conjuncts (a)/(b) still red on stale canonical data, as expected), and the
-- new text should contain the literal string "chart_id = '482012f1-710e-4a25-994a-93821f5871aa'"
-- inside BOTH conjunct (a) and conjunct (b) (grep-verify each independently — cheap positive
-- signal both scopes actually landed, not just one).

BEGIN;

UPDATE asset_registry SET integrity_check_sql = $ck$
SELECT
  -- ka_yojaka integrity contract (D-CND-03: chart-partitioned, attribution-preserving)
  -- Target table kala_activation_predicates.
  -- NO distinctness conjunct appears here: (chart_id, signal_id, ayanamsha_id) is ALREADY a DB
  -- UNIQUE index (idx_kap_chart_signal_ayan), so asserting it again could never fail and would
  -- breach C12's rewrite floor. Conjuncts (a) and (b) instead assert the two-way cardinality
  -- agreement with the L2 signal inventory, which no index can enforce.
  -- (a) §N.5 upstream authority. Every predicate must name a signal that still exists, for the
  -- SAME chart and the SAME ayanamsha. The table carries no foreign key, so a bo_laksana
  -- rebuild that re-issues signal_ids leaves the whole predicate set pointing at dead rows and
  -- nothing notices. SCOPED to the canonical chart (this migration, ruling #2542 15:19:15Z
  -- follow-up, mirroring (c)'s migration-1019 scope): dispatch_nirmana_campaign_wave.py can only
  -- ever rebuild canonical, so cb73cd3d's independent, pre-existing 49,730/49,875-row violation
  -- (documented in migration 1019's own comment) can never be cleared by this campaign's dispatch
  -- and must not permanently block canonical's own certification.
  NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    WHERE p.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s
      WHERE s.signal_id    = p.signal_id
        AND s.chart_id     = p.chart_id
        AND s.ayanamsha_id = p.ayanamsha_id)
  )
  -- (b) §N.5 coverage, the other direction. ka_yojaka's contract is one predicate per MSR
  -- signal, so for every chart it has built, every L2 signal must have a predicate. Detects a
  -- partial bind pass or a build that ran against a smaller signal set than the live one.
  -- SCOPED to the canonical chart (this migration, same rationale as (a) above).
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals s
    WHERE s.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND EXISTS (SELECT 1 FROM kala_activation_predicates q WHERE q.chart_id = s.chart_id)
      AND NOT EXISTS (
        SELECT 1 FROM kala_activation_predicates p
        WHERE p.chart_id     = s.chart_id
          AND p.signal_id    = s.signal_id
          AND p.ayanamsha_id = s.ayanamsha_id)
  )
  -- (c) §N.6 item 3 / §N.7 item 6: an honest UNDATED must be REPORTED, not merely be empty.
  -- A predicate with no constituent_lords cannot ever be dated by any downstream engine, so it
  -- must carry the CR-37 always_on_reason saying why. SCOPED to the canonical chart (migration
  -- 1019, ruling #2542 Option B): campaign dispatch can only ever rebuild canonical
  -- (dispatch_nirmana_campaign_wave.py restricts to DEFAULT_CHART_ID), so this conjunct
  -- measures what this campaign can actually certify. Abhinandan and cb73cd3d retain pre-fix
  -- violations (9,300 / 9,054 at ruling time) tracked separately, not silently declared clean.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
      AND jsonb_array_length(
            COALESCE(dasha_eligibility_rule_jsonb->'constituent_lords','[]'::jsonb)) = 0
      AND (dasha_eligibility_rule_jsonb->>'always_on_reason') IS NULL
  )
  -- (d) §N.5 provenance: a predicate that DID resolve lords must say where they came from.
  -- A lord list with no constituent_lords_source is an unattributable claim (B.3).
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE jsonb_array_length(
            COALESCE(dasha_eligibility_rule_jsonb->'constituent_lords','[]'::jsonb)) > 0
      AND (dasha_eligibility_rule_jsonb->>'constituent_lords_source') IS NULL
  )
  -- (e) B.3 derivation ledger must resolve and must not drift from the row it sits on.
  -- Every bg_transit_rules id the ledger cites must be a real L0 rule row -- the ledger must
  -- carry its ratified_by and template_version -- and that template_version must equal the
  -- row's own column (a wrapper-local copy that can drift from its source is §N.7 item 3).
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    CROSS JOIN LATERAL jsonb_array_elements_text(
      COALESCE(p.derivation_ledger_jsonb->'bg_transit_rules_ids','[]'::jsonb)) AS r
    WHERE NOT EXISTS (SELECT 1 FROM bg_transit_rules b WHERE b.id::text = r)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE (derivation_ledger_jsonb->>'ratified_by') IS NULL
       OR (derivation_ledger_jsonb->>'template_version') IS DISTINCT FROM template_version
  )
  -- (f) payload presence guard: all four jsonb payloads are NOT NULL at the schema level but
  -- nothing stops an empty object, which serves as a populated-looking hollow envelope
  -- (§N.6 item 3). Every predicate must actually carry its four declarations.
  AND NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates
    WHERE dasha_eligibility_rule_jsonb   = '{}'::jsonb
       OR transit_trigger_jsonb          = '{}'::jsonb
       OR strength_affliction_hook_jsonb = '{}'::jsonb
       OR derivation_ledger_jsonb        = '{}'::jsonb
  )
  AS integrity_passed
$ck$
 WHERE asset_id = 'ka_yojaka';

COMMIT;
