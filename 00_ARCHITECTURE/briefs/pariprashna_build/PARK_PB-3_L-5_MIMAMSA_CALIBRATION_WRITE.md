---
artifact: PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE
type: PARK-WITH-COSTED-SPEC + PRATINIDHI MEMO ASK (BRIEF_PB-3 §F1 Lane L-5 acceptance branch b)
campaign: PB — Paripraśna Build
wave: PB-3 SAMĪKṢĀ
version: 1.0
status: OPEN — parked, awaiting a Pratinidhi MEMO on the conversational-calibration write target
date: 2026-07-28
authored_by: Claude Code (PB-3 L-5 autonomous execution session)
governing: BRIEF_PB-3.md §F1 Lane L-5 ("parks with costed spec + MEMO. Both valid; silence is not."),
           §5 W-4, MEMO_PB-3_0 "What this ruling is NOT", LEDGER_MAP_PB-3.md
---

# PARK — the conversational `mimamsa_calibration` write needs its own Pratinidhi MEMO

## §0 — What this is (and is not)

This is the **park-with-costed-spec** half of Lane L-5's acceptance, taken deliberately and
with evidence — not silence, and not a quiet drop. The lane's other half (the Brier
computation + the ledger-side outcome recording) **was built and round-trips for real** against
a migrated throwaway Postgres; see the L-5 report and `l5_roundtrip_harness.sh`. Only the final
seam — **persisting a conversational calibration row into `mimamsa_calibration`** — is parked,
because doing it correctly requires a schema change this lane cannot self-authorize.

## §1 — The finding that forces the park (verified against the deployed DB)

BRIEF_PB-3 §F1 Lane L-5 says: "upsert into `mimamsa_calibration`, with `source_citation` = the
ledger row id." **That instruction describes a table schema that no longer exists.**

- The brief's assumed shape — `mimamsa_calibration(chart_id, technique, ayanamsha_id,
  brier_score, sample_size, source_citation, computed_at)` — is the **retired MI-5-3 prototype**
  (defined by the legacy `0001_brahma_baseline.sql`). It is the SAME phantom schema the
  `outcome.py` / `update_calibration()` retirement (PR #725 / migration 464, CR-115/CR-128)
  was closed against.
- The **LIVE** `mimamsa_calibration` (verified against the deployed DB at PB-3 L-5 BIND) is the
  **mi_pramana per-match analytical scoring** schema created by migration 348:

  ```
  PRIMARY KEY (chart_id, match_id)
  columns: chart_id, match_id, prediction_id, event_id,
           score_timing, score_magnitude, score_domain, score_falsifier, score_manifestation,
           manifestation_channel, composite_verdict, composite_score, base_rate_adjusted_skill,
           evidence_admissibility, n_for_stratum, leakage_status, scoring_formula_version,
           scored_at, base_rate, brier_vs_null
  ```

  It carries **no `source_citation` column, no `brier_score` column, and no scalar `confidence`
  column.** Its natural key is `(chart_id, match_id)` — a `match_id` being a
  `mimamsa_predictions ↔ mimamsa_event_provenance` (LEL) match, a concept a conversational
  prediction does not have.

**Writing an INSERT against `source_citation` / `brier_score` on this table would recreate the
exact `outcome.py` phantom-column defect Lane L-5 was chartered to diagnose.** That is the one
thing this lane must not do.

## §2 — Why it cannot be fixed inside L-5's authority

1. **It needs a migration.** Adding columns (or a new table) is a schema change. L-5's
   `may_touch` grants **no** `platform/migrations/**` or `supabase/migrations/**` path.
2. **The table is mi_pramana-owned.** `mimamsa_calibration` is written by `mi_pramana.py`, an
   `mi_*.py` L5 writer that is on BRIEF_PB-3 §F2's **`must_not_touch`** list. Changing its
   schema or write semantics risks the deterministic analytical pipeline, the §7.4 NO-LEAKAGE
   single-physical-table role, and the cockpit count — X-5's exact "Option-A risk
   concentration."
3. **It is a design-authority decision, not a lane call.** Whether conversational calibration
   shares mi_pramana's physical table or gets its own is precisely the kind of choice
   MEMO_PB-3_0 reserved: "Any `phala_anchors` schema change requires its own, separate
   Pratinidhi MEMO per W-4 — this memo does not authorize one." The same logic binds
   `mimamsa_calibration`.

## §3 — What WAS delivered (so the park is bounded, not open-ended)

`platform/src/lib/pariprashna/samiksha/outcome_calibration.ts` (pure) +
`outcome_recorder.ts` (orchestrator) already produce, for every resolved conversational claim:

- the deterministic **Brier score** `(confidence − outcome)²` from the ledger row's numrange
  confidence + the observed outcome (honest-null when confidence is absent or the outcome is
  `unverifiable` / Brier-excluded);
- the **real ledger-side write** (window_closed → outcome_recorded / unverifiable, co-located
  outcome columns persisted) via L-1's DAL — proven round-tripping against a real DB row;
- a fully-formed **`CalibrationWriteIntent`** whose `source_citation` **is the ledger row id**
  ("the ledger is the citation", §14.5) — the exact payload the parked persistence consumes.

So when the MEMO lands, the remaining work is *only* the persistence sink, not any of the
computation or provenance.

## §4 — Costed spec (what the MEMO must choose between)

### Option A — extend `mimamsa_calibration` in place (shared physical table)
Additive migration:
- `ALTER TABLE mimamsa_calibration ADD COLUMN calibration_source text NOT NULL DEFAULT
  'analytical'` (discriminator: `'analytical'` = mi_pramana; `'conversational'` = this loop),
  plus nullable `source_citation text`, `brier numeric`, `confidence_point numeric`,
  `outcome text`.
- Relax/extend the PK: conversational rows have no `match_id`; use
  `match_id = 'PB3.LEDGER.' || <ledger_row_id>` as a synthetic, namespaced key so the
  `(chart_id, match_id)` PK still holds without collision.
- **Cost:** touches an `mi_*`-owned table + `mi_pramana`'s `CAL_SQL` mental model; the cockpit
  `count_sql`, `query_calibration`, and the §7.4 NO-LEAKAGE role all now read a table with two
  provenance classes and must filter by `calibration_source`. Risk concentration exactly as
  X-5 warned. **What breaks if done wrong:** the `mimamsa_calibration` consumers
  (`query_calibration`, `mimamsa_calibration_get`, `mi_gunanaka` multiplier read) begin to see
  conversational rows they were never written to expect.

### Option B — a new `mimamsa_conversational_calibration` table (separate sink) — RECOMMENDED
Additive migration, new table:
```
mimamsa_conversational_calibration (
  id uuid PK default gen_random_uuid(),
  chart_id uuid NOT NULL,
  source_citation uuid NOT NULL,        -- = brahma_mimamsa_prediction_ledger.id (the ledger IS the citation)
  prediction_ledger_row_id uuid NOT NULL REFERENCES brahma_mimamsa_prediction_ledger(id),
  domain text, confidence_point numeric, outcome text, outcome_value numeric,
  brier numeric, brier_excluded boolean NOT NULL,
  scored_at timestamptz NOT NULL default now(),
  UNIQUE (prediction_ledger_row_id)     -- one calibration row per resolved claim (upsert key)
)
```
- **Cost:** one new additive table + a ~15-line writer in `samiksha/`; the parked
  `recordConversationalOutcome` flips `calibration_persisted` to a real UPSERT.
- **Why recommended:** it never touches the mi_pramana table, honors §14.1's provenance
  distinction (analytical vs conversational calibration) cleanly, keeps the §7.4 NO-LEAKAGE
  role naming ONE physical table per class, and matches the `CalibrationWriteIntent` shape
  1:1 (no synthetic-key gymnastics). It is fully within COLLECT-ONLY (§14.6 C1): nothing reads
  it into a serving path.

## §5 — What the Pratinidhi MEMO must rule
1. **Option A vs B** (recommendation: B — separate additive table, no mi_pramana contact).
2. The **exact target name + column set** (if B) or the discriminator design (if A).
3. Confirmation that the write stays **COLLECT-ONLY** (W-3): no priors bump, no serving
   annotation reads this row — a grep/runtime guard, per Lane L-6.
4. That `mimamsa_predictions`, `brahma_prospective_ledger`, and `phala_anchors` remain
   **untouched** (this park proposes zero change to any of them).

## §6 — Migration-guard note
Both options are **additive-only** (new columns with defaults / a new table); neither drops or
rewrites existing data, and neither touches `phala_anchors` (which stays a read-only anchor
reference — its genuinely-missing outcome columns are moot now that outcome state lives in the
L-1 ledger). No migration is executed by this lane; this doc IS the park.

*End PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE v1.0.*
