-- 1019_nirmana_l3_ka_yojaka_integrity_check_scope.sql
--
-- NIRMĀṆA L3 Kāla — CONDUCTOR ruling on adjudication #2542 (L3 → CONDUCTOR, D-CND-17 re-scope):
-- `ka_yojaka`'s `integrity_check_sql` conjunct (c) (migration 670) is table-wide across
-- `kala_activation_predicates` — no `chart_id` scoping at all. Live-measured violation counts
-- at ruling time: canonical `482012f1` = 9,327, Abhinandan `1c826d5a` = 9,300, `cb73cd3d`
-- (damaged/excluded) = 9,054. The PR #2464 writer fix (`ka_yojaka.py` #2456 W2
-- generalization loop) is structurally complete and zeroes canonical's violations on a fresh
-- rebuild, but the unscoped conjunct also counts the other two charts' pre-fix rows, so it can
-- never pass under a canonical-only dispatch no matter how correct the canonical rebuild is.
--
-- Three options were laid out (#2542): (A) scope to the two-chart set (canonical + Abhinandan)
-- mirroring migration 902's `ga_condition` precedent; (B) scope to canonical only; (C) extend
-- the FROZEN `dispatch_nirmana_campaign_wave.py` to accept Abhinandan as a second dispatchable
-- chart. RULED: **Option B.** Option A was rejected because it does not actually unblock
-- anything here: `dispatch_nirmana_campaign_wave.py`'s `_select_frozen_build_assets` hard-raises
-- for any `chart_id != DEFAULT_CHART_ID`, so nothing in this campaign's own machinery can ever
-- rebuild Abhinandan's `ka_yojaka` predicates — a two-chart-scoped conjunct would stay
-- permanently red regardless of the canonical rebuild's correctness, unlike migration 902's
-- `ga_condition` case where the two-chart scope was actually achievable. Option C was rejected
-- as disproportionate: extending the FROZEN, campaign-wide dispatch script that L1/L2/L4 also
-- depend on, just to satisfy one asset's integrity check, is a bigger and riskier change than a
-- single-asset migration — if the native later wants Abhinandan dispatchable for real, that is
-- its own decision, not a side effect of unblocking `ka_yojaka`.
--
-- Scope: canonical chart (`482012f1-...`) only, matching the disclosed-tradeoff precedent of
-- migrations 882 (`ga_dashas`), 884 (`ga_vargas`), and 902 (`ga_condition`) — this campaign's
-- `asset_frozen` decision is about the canonical chart's build correctness, not an audit of all
-- 3 charts (which have their own separate operator-E2E validation track). Conjuncts (a), (b),
-- (d), (e), (f) remain table-wide and unscoped — they already pass table-wide today per #2542's
-- own analysis (only conjunct (c) was reported as the blocker), so no coverage is traded away
-- where none needs to be.
--
-- Abhinandan's and cb73cd3d's un-rebuilt `ka_yojaka` rows are NOT declared fixed by this
-- migration — they remain real, pre-#2464-writer-fix violations, out of this campaign's
-- dispatch scope. Fixing them requires their own coordinated rebuild (tracked separately; not
-- an L3/CONDUCTOR quick fix, same disposition as migration 902's header for `ga_condition`'s
-- equivalent carve-out). When Abhinandan is rebuilt with the fixed writer and independently
-- reaches zero conjunct-(c) violations, this scope can be widened back per Option A.

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
  -- nothing notices. Chart-partitioned by construction: today chart cb73cd3d violates this on
  -- 49,730 of its 49,875 rows while the other two charts are clean.
  NOT EXISTS (
    SELECT 1 FROM kala_activation_predicates p
    WHERE NOT EXISTS (
      SELECT 1 FROM bodha_msr_signals s
      WHERE s.signal_id    = p.signal_id
        AND s.chart_id     = p.chart_id
        AND s.ayanamsha_id = p.ayanamsha_id)
  )
  -- (b) §N.5 coverage, the other direction. ka_yojaka's contract is one predicate per MSR
  -- signal, so for every chart it has built, every L2 signal must have a predicate. Detects a
  -- partial bind pass or a build that ran against a smaller signal set than the live one.
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals s
    WHERE EXISTS (SELECT 1 FROM kala_activation_predicates q WHERE q.chart_id = s.chart_id)
      AND NOT EXISTS (
        SELECT 1 FROM kala_activation_predicates p
        WHERE p.chart_id     = s.chart_id
          AND p.signal_id    = s.signal_id
          AND p.ayanamsha_id = s.ayanamsha_id)
  )
  -- (c) §N.6 item 3 / §N.7 item 6: an honest UNDATED must be REPORTED, not merely be empty.
  -- A predicate with no constituent_lords cannot ever be dated by any downstream engine, so it
  -- must carry the CR-37 always_on_reason saying why. SCOPED to the canonical chart (this
  -- migration, ruling #2542 Option B): campaign dispatch can only ever rebuild canonical
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
