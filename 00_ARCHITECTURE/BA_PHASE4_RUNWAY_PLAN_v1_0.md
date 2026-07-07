---
canonical_id: BA_PHASE4_RUNWAY_PLAN
version: 1.0
status: CURRENT — governs the sequence from now to native-rebuild-closed
created: 2026-07-07
author: Cowork (Beyond-Acharya program) — native-directed consolidation, sitting 2026-07-07
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — the runway to Phase-4 (native 482012f1 rebuild)
supersedes: the standalone Phase-4 GO prompt issued 2026-07-07 (its content is absorbed into R4 below);
  and re-sequences CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING (v1.1) from post-rebuild to pre-rebuild.
rationale: >
  Native decision 2026-07-07 — land ALL pending code churn (LEL re-architecture + JL-026 dual-write
  audit) BEFORE the native rebuild, so the native chart is built ONCE on the final architecture with its
  57 LEL events already chart-keyed (no post-rebuild recalibration pass). The validated-config claim
  from runs d6ebca1e/d7cddc38 expires with the churn; it is re-earned by one clean Abhinandan
  revalidation run (R3) before the native chart is touched. Rifle re-zeroed, then the one shot.
---

# BA PHASE-4 RUNWAY — phased implementation to the native rebuild

**Chart ids:** native = `482012f1-710e-4a25-994a-93821f5871aa` · Abhinandan (proving ground) =
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`. Two-chart rule throughout: Abhinandan proves everything first.

**Standing guardrails (all phases):** native chart never built/written until R4 · single writer stream
(no parallel sessions, merges, deploys, cockpit clicks outside the active phase) · every phase closes
with ledger + CURRENT_STATE entries before the next opens · HALT-and-report on any FORENSIC miss,
contamination hit, or LEL row loss.

---

## R1 — NATIVE INPUTS (human; ~30 min; no code)

| # | Activity | Owner | Detail |
|---|---|---|---|
| R1.1 | **JL-009 glance** | Native | Conductor surfaces the age-banded event base-rate table from `brahma_event_ontology` (22 classes). Native confirms/edits. Conductor applies edits (ontology upsert, version bump) + closes JL-009 in BA_JUDGMENT_LEDGER. Required before ANY L4 anchor generation for the native chart. |
| R1.2 | **Retrospective veto sweep** | Native | Confirm (or veto) JL-021…026 dispositions as upheld by Ācārya-Pratinidhi (mig-416 edge kept; WORKER_LIMIT=2). Silence past R1 close = confirmed. |
| R1.3 | **Environment quiesce** | Native | No other Claude Code/Antigravity session, no manual cockpit builds, no pending PRs, no open DB sessions. Declare the single stream. |

**Exit:** JL-009 CLOSED in ledger `[verify-against: ledger]`; quiesce declared in SESSION_LOG.

## R2 — CODE CHURN, ALL OF IT (conductor; the only phase that changes the system)

| # | Activity | Brief / scope |
|---|---|---|
| R2.1 | **JL-026 dual-write audit → mig-416 edge disposition** | Full ga_structural↔ga_condition dual-write map (incl. graha_yuddha); if audit proves independence, apply drafted migration 419; if not, edge stays with documented reason. JL-026 closes either way. |
| R2.2 | **LEL re-architecture** | `CLAUDECODE_BRIEF_BA_LEL_CHART_SCOPING_v1_0.md` (v1.1, root) Steps 0–7 in full: chart-scoped schema + 57-row backfill, source-of-truth flip, presence-branching in L4/L5, calibration state machine, debounced save→recalibration trigger, recorded_at leakage discipline, gated pool capture, retrieval + governance close-out. All its exit gates verified on Abhinandan + native DATA (native chart still not rebuilt — schema/backfill only). |

**Exit:** both workstreams' exit gates green; all PRs merged CI-gated; migrations applied prod;
native life_events = 57 rows @ 482012f1, Abhinandan = 0, `[verify-against: prod db]`.

## R3 — RE-ZERO THE RIFLE (conductor; revalidation on the proving ground)

One clean **Abhinandan full rebuild** on the new HEAD, parallel mode (WORKER_LIMIT=2): expect 66/66
(or the new asset count if R2 registered lel_events — record the new canonical count), 0 errors,
`build_runs.state=completed`. Then:
- FORENSIC-equivalents: Abhinandan Sun=Aquarius, Lagna=Aries 23°32′ Bharani-4 `[verify-against: prod db]`
- Contamination: zero native values under 1c826d5a; zero Abhinandan values under 482012f1.
- LEL presence-branching live: Abhinandan calibration_state='structural', rectification_basis=
  'structural_no_lel', lel_query(1c826d5a) = empty-with-reason `[verify-against: prod]`
- Degeneracy sweep on all L2–L5 scored columns (salience_v2, posteriors, convergence) non-degenerate.
- Retrieval smoke: bodha_signals_get + one apex tool within caps, ranking_basis present.

**Exit:** clean run id recorded; this HEAD+config becomes the NEW validated configuration. FREEZE it —
from R3 close to R4 close: no merges, no migrations, no env changes, nothing.

## R4 — PHASE-4: THE NATIVE REBUILD (conductor; the one shot)

1. **Fresh snapshot** of native 482012f1 L1–L5 rows (all chart-scoped tables incl. life_events);
   snapshot id + restore path recorded in RUN_LEDGER. (LEL rows are additionally protected by the R2
   clear-safety allowlist — belt and braces.)
2. **Rebuild native L1→L5** via the standard cockpit path, full fresh rebuild (JL-024), WORKER_LIMIT=2,
   on the R3-frozen configuration.
3. **Post-rebuild gates** `[verify-against: prod db]`:
   - FORENSIC 7/7: Sun Cap · Moon Purva Bhadrapada · Lagna Aries ×5 ayanamshas · Shukla Tritiya ·
     Ravivara · Shiva yoga · Garaja karana.
   - Contamination cross-check: Abhinandan values unchanged and ≠ native.
   - bhava_arudha 12 × 5 ayanamshas present (closes the P3A deferred gate; flip P3A brief → COMPLETE).
   - LEL integrity: 57 rows intact; calibration_state='calibrated'; rectification LEL-fit ran and
     STILL validates 10:43; ph_pramana attestations reference chart-scoped LEL rows.
   - JL-009 values in effect: native L4 anchors' base_rate factors trace to the R1.1-confirmed ontology
     values (spot 5 lift_vectors).
   - Degeneracy: min(posterior) < 0.2, signature_tier chart_defining > 0, contradictions > 0 w/ domains.
   - Retrieval smoke: bodha_signals_get(482012f1, career, 10) ranking-clean; one apex tool within cap;
     judgment_flags show calibration='calibrated' on an L5 surface.
4. **HALT conditions:** any FORENSIC miss · contamination hit · LEL row loss/mutation ·
   build_runs.state ≠ completed → STOP, restore from snapshot, report. No iteration on the native chart.

**Exit:** all gates green → ledger (JL-⟦next⟧: Phase-4 executed, native-ratified sequence), CURRENT_STATE,
SESSION_LOG close. The instrument is live on both charts under the full Beyond-Acharya architecture.

## R5 — POST-CLOSE (next sittings; not part of this runway)

Live-testing punch-list (topic_relevance tuning, stale provenance notes, digest aggregation, the
ganita_chart_facts_get 404, basic rashi-chart surface) · Retrieval 3.0 faceted-instruments design ·
optional WORKER_LIMIT raise with fresh CPU data · JL-022 Option B · cross-chart pool opening decision.

---

*Sequencing rationale in one line: churn → re-zero → one shot. R1 is the only phase needing the native's
personal time; R2–R4 are conductor-autonomous under the standing guardrails.*
