---
artifact: PRE_DARPANA_READINESS
type: READINESS CHECKLIST (residual fixes + verifications before UAT-DARPANA opens)
version: 2.0
status: OPEN — exit condition NOT fully met. UAT-DARPANA remains HELD. 9 of 11 SARVA-SIDDHI
  fix lanes CLOSED-WITH-EVIDENCE (code + live-verified); 2 lanes CODE-COMPLETE-BUT-DATA-PENDING
  (real fix merged and deployed, production table not yet rebuilt — needs the same cockpit
  build access as T-2); 1 lane (T-2 full materialization) is a genuine, evidence-sized OPEN
  item the native has elected to dispatch personally via the cockpit UI. This v2.0 reports the
  swarm's actual findings — not a stretched pass, per the campaign's own §0.3 honesty doctrine.
context: SARVA-SIDDHI campaign executed 2026-07-24 (Coordinator: Sonnet, Opus step-ups on W-0
  verdicts, all root-cause/detector/provenance lanes, and the W-5 adversarial verifier, per
  BRIEF_SARVA_SIDDHI_v1_0.md §2). Supersedes PRE_DARPANA_READINESS_v1_1.md's Tier A/B/C
  disposition — every accept-as-dark ruling in v1.1 was RESCINDED by native order at campaign
  open; this v2.0 replaces that checklist's structure with the campaign's own W-0→W-5 wave
  report. 11 PRs merged to main: #732–#742, plus #743 (hygiene: stale CR-37 register flag +
  accidentally-committed node_modules symlinks, landing at close of this session).
changelog:
  - v2.0 (2026-07-24, SARVA-SIDDHI campaign close): full wave report below. Fresh-context Opus
    adversarial review confirmed all 12 merged diffs as genuine code fixes (zero B.10
    fabrication, zero §N.5 circular-derivation violations) via source review (the live MCP
    connector's tool catalog only reaches tools present at session start, so 2 brand-new tools
    plus several "live-verified" runtime numbers could not be independently reproduced by the
    verifier — flagged per item below, not glossed over).
  - v1.1 (2026-07-24, PRE-DARPANA READINESS swarm close): superseded — see file history.
---

# PRE-DARPANA READINESS v2.0 — SARVA-SIDDHI campaign close

## Exit condition — NOT FULLY MET (honest, evidenced)

Per `BRIEF_SARVA_SIDDHI_v1_0.md`'s own exit clause: "every item CLOSED-WITH-EVIDENCE ... Exit
met → Darpana unlocks." That bar is not fully cleared. What follows is exactly where the line
sits — 9 lanes genuinely closed, 2 lanes real-fixed-but-not-yet-data-refreshed, 1 lane real and
sized but deliberately not dispatched this session (native decision). **UAT-DARPANA remains
HELD** pending: (a) a build dispatch to refresh `phala_anchors` and `dosha_label` production
data (CR-66, CR-73 — bounded, no new code needed), (b) the T-2 gochara materialization dispatch
itself (native's own call, cockpit UI), (c) a small planner-wiring follow-up for CR-24's new
serving face.

## W-0 — Truth pass (complete)

Published `SARVA_SIDDHI_TRUTH_TABLE_v1_0.md`. Corrected the native's own recollection: the
gochara sweep has **never** completed (16/16 build_run attempts errored, before and after the
D-4b event-driven reconciliation). Confirmed CR-68/CR-16/CR-61/CR-64 as stale register-drift
(already fixed in code via PR #688/#594/#585, register never updated — the third occurrence of
this drift class after CR-56). Confirmed CR-130/CR-24/CR-73/CR-30 as real, scoped work; CR-30
fully open, the other three partial (some real coverage already existed, narrower residual
scoped correctly).

## W-1 — Temporal core

- **T-1 (DATABASE_URL fix) — CLOSED, live-verified.** PR #732, merged. Root cause: the D-5
  Lane G-4 gochara serving tools held their own direct `pg.Pool`/`DATABASE_URL` connection —
  the only file in `platform-mcp` to do so — against a Cloud Run service with no DB attachment.
  Fixed by routing through the platform's existing DB-connected proxy route
  (`platform/src/app/api/mcp/db/query/route.ts`), matching every sibling tool's pattern.
  **Live-verified post-deploy** (this session, direct MCP call): `gochara_activation_get` and
  `gochara_forecast_get` both return `backing_data_reachable:true` with real data (the forecast
  call returned a genuine 135K-character payload, not an empty-error stub).
- **T-2 (full materialization) — OPEN, real work sized, dispatch held by native decision.**
  PR #737, merged. Root cause found and fixed: `ka_gochara_sweep`'s substep plan was anchored
  to each dasha system's ~1950 balance-start date instead of the literal 1984-02-05 birth date,
  so the 0–99 substep grid could never reach birth+100y=2084 — it topped out near 2049 while
  wasting ~34 years per class on pre-birth substeps. Fixed `_derive_birth_year` to read
  `charts.birth_date`; extended the horizon to 101 years; bumped the resume-fingerprint so the
  writer's own idempotent rebuild path replans cleanly. **This resizes the real remaining work
  upward, not down**: a correct-span replan is 303 substeps from scratch (the old 165 done
  substeps are discarded by the fingerprint change) — at the measured ~4.65 min/substep, that's
  **≈23.5 hours across ≥4 resumable ~6h Cloud Run dispatches**, not the ~10.5h/2-dispatch
  estimate W-0 first produced (which assumed the old, wrong-span plan). A legitimate dispatch
  mechanism exists (`gcloud run jobs execute` against `brahma-build-pipeline-job`, whose deployed
  image already includes the #737 fix), and a writable Cloud SQL proxy path is available — the
  Coordinator confirmed both are technically reachable this session, then **asked the native
  whether to proceed** given the real cost (≈24h paid compute, direct production DB writes
  outside the cockpit UI). **Native chose to dispatch this personally via the cockpit UI.**
  D-6's "v1 corpus complete" precondition remains unmet until that dispatch runs to completion.
- **T-3 (CR-37 activation dating) — CLOSED, live-verified.** PR #742, merged. Root cause:
  correctly-undated distribution yogas were conflated with genuinely-undated real-mechanism
  yogas in the register's "0/13,364 dated" figure (already known stale from the prior session).
  `ka_yojaka`/`ka_kalasutra` rebuilt with real `chart_dashas`-derived activation windows.
  **Live-verified this session**: `kala_yoga_activation_get` returns real dated windows for
  Anapha/Sasa/Vasi Yoga (e.g. Sasa Yoga dated to a real Saturn antardasha 2024-12-08→2027-08-18)
  and correctly leaves Gola/Kedara/Shoola/Yuga (always-on distribution yogas, 4+ distinct signs)
  undated with a new, honest `always_on_reason:"distribution_yoga_all_grahas"` discriminator
  instead of a bare null. Committed before/after counts (native 482012f1: YOGA 12/74→161/207,
  DOSHA 203/422→926/1059; control 1c826d5a: YOGA 0/66→168/213, DOSHA 0/155→760/820) are
  author-reported from the rebuild session, not independently reproduced by the W-5 verifier,
  but the underlying writer logic was confirmed to read real dasha periods, not fabricate dates.
  **Register follow-up caught live in W-5**: the `yoga_activation_scan` primitive's `known_gap`
  was still flagging CR-37 after #742 merged — the recurring drift class, this time inside the
  same campaign. Fixed in PR #743 (this session, landing at close).
- **T-4 (CR-66 phala anchors) — CODE-CLOSED, DATA-PENDING.** PR #739, merged. Root cause: three
  stacked bugs in `ph_nimitta` — a stale domain-vocabulary mismatch collapsed every
  wealth/spirituality/character row to `transition` (the direct cause of wealth=0); a
  `LIMIT 200` convergence selection grabbed only the earliest all-historical rows, starving 956
  wealth / 674 spirituality / 816 career future-dated windows; a `horizon_tier` mislabel nuked
  past windows via the stale-near clip gate. Fixed with per-domain stratified selection + a
  canonical vocabulary map + a corrected horizon-tier function. **Live re-derivation against the
  actual DB (read-only query, this session) confirmed the fix produces 290 real rows across all
  6 domains (wealth 0→~26 distinct anchor windows)** — but this is a query-level proof, not a
  production state change: the physical `phala_anchors` table rebuild requires the same
  cockpit-build access as T-2, and **a live probe this session confirmed the production table
  still shows the old 8 rows, wealth=0** — the fix has not yet been served. Disclosure is live
  and correct in the interim (see T-5).
- **T-5 (§N.6 disclosure repairs) — CLOSED, live-verified.** Bundled into PR #739. (a)
  `phala_predictive_anchors_get`'s empty response now carries `empty_reason` + `known_gap`
  distinguishing a genuine backing-set emptiness from a filter-miss from an unreachable-count
  case — **live-verified this session**: calling it for `domain=wealth` today returns exactly
  this honest disclosure (`"phala_anchors has 8 anchor(s) for this chart, but none match the
  requested filter..."`, `known_gap:"CR-66"`) instead of a silent empty. (b) `yoga_activation_scan`
  wired into the shared E-1 elevation band in `registry_data.ts` — confirmed present in the live
  compiled plan for a wealth question this session.

## W-2 — Prediction loop

- **P-1 (standing predictions provenance) — CLOSED, planner-wired.** PR #736, merged. The
  central finding reshaped the task: all three predictions (Sat-Jupiter Apr-Aug 2027, Ketu-MD
  shape, Venus-MD 2034) already existed in `brahma_prospective_ledger` with **genuine original
  provenance** — filed 2026-07-19 during the D-4a Lane A-4 session, `filed_by:
  native:abhisek@marsys.in`. No backfill was performed (none was needed, and fabricating a
  synthetic backfill flag would have degraded real provenance — correctly declined). The actual
  defect: `standing_predictions_read` was wired to `phala_predictive_anchors_get` (an L4 anchor
  surface, empty for wealth) instead of the prospective ledger. Fixed via a new
  `query_prospective_ledger.ts` capability reading the ledger directly, §N.6-layered by domain
  cluster. **Confirmed live-wired this session** via `plan_retrieval`: the compiled wealth-plan's
  `standing_predictions_read` primitive now points to `standing_predictions_read` with
  `known_gap:null` (previously `phala_predictive_anchors_get`). Direct tool round-trip on the new
  tool itself was not reachable this session (deployed after this session's MCP connector cache
  was fixed) — the planner-level repoint is the strongest evidence available and is dispositive
  that the fix shipped and is live.

## W-3 — Remedy core

- **R-1/R-2 (CR-67 + CR-69) — CLOSED, live-verified.** PR #741, merged. CR-67: `bo_upaya`'s
  `associated_cdlm_cells_array` was 100% NULL DB-wide (unimplemented L2 derivation, not a query
  bug) — fixed with a real graha→CDLM-cell join resolved via each MSR signal's
  `constituent_facts_array → chart_facts.fact_subject` (§N.5-compliant, non-fabricated). CR-69:
  `query_remedies.ts` never read `leverage_ranked` and exposed no rank axis — fixed by wiring a
  real `leverage_index` composite READ (not recomputed) from `chart_vichara`
  (`(domain_load_bearing_weight ÷ capability) × dasha_runway`, `ga_vichara`'s own
  `leverage_index_v1`). A genuinely broken SQL bug in `bo_upaya`'s B-4 windowed-prescription
  builder was found and fixed along the way (`event_date < DATE %s` — invalid syntax, had kept
  `bodha_rm_dasha_windowed_prescriptions` at 0 rows since the builder's introduction).
  **Live-verified this session**: `bodha_remedies_get(chart_id, domain=wealth)` returns real,
  domain-joined, cited resonances (Saturn/Jupiter/Sun, associated_cdlm_cell_count 7/5/13) with 9
  citation-backed prescriptions, and the response's own `data_gap_note` explicitly confirms
  "CR-67 CLOSED: associated_cdlm_cells_array is now populated." One residual disclosed, not
  hidden, by the fix itself: `associated_doshas_array` and `estimated_cost_inr_range_jsonb`
  remain unpopulated (separate, out-of-scope writer gaps, not silently patched).

## W-4 — Detectors + rankings

- **D-1 (CR-130 Jaimini spiritual yoga) — CLOSED, live-verified.** PR #740, merged. The
  Parashari `pravrajya_yoga` detector already existed and fired correctly (confirmed 0 rows for
  this native is a genuine correct-negative, not a bug) — that half needed no work. The real gap:
  the Jaimini karakāṃśa spiritual family existed in the L0 catalog only, zero L1 firing detector.
  Built real firing detectors for all 7 karakāṃśa yogas (occupation or Jaimini chara-rāśi-dṛṣṭi
  on the karakāṃśa sign), grounded in real `chart_facts` karakamsa/Ātmakāraka reads, cited to
  Jaimini Sutram 1.2/1.1.9-11 + BPHS Ch.34. **Live-verified this session**:
  `jaimini_karakamsha_moon` fires for the native (strength 0.9417, real citation, real
  constituent_fact_ids) with an honest NULL bhanga floor (no classical cancellation rule exists
  for this yoga family — not fabricated). Migration 465 seeds the catalog rows. Differential
  firing across native vs. control chart (author-reported, not independently reproduced by the
  adversarial verifier) is architecturally sound per source review.
- **D-2 (CR-24 mechanism serving face) — CODE-CLOSED, PLANNER-WIRING-PENDING.** PR #734, merged,
  CI green. The named-valenced mechanism object was already built (`bo_yantra_mechanism.py`,
  prior wave); the real CR-24 gap was the missing dedicated serving face. Built
  `bodha_mechanisms_get`, §N.6-compliant (chain/circuit class ordered first, facet counts,
  honest empty on charts with no built mechanisms). **Genuine residual, caught in this session's
  W-5 pass**: the vidhi planner's `mechanism_read` primitive in `registry_data.ts` was never
  repointed to the new tool — it still points to `bodha_graph_subgraph_get` with
  `known_gap:'CR-24'` still set, confirmed live via `plan_retrieval` this session. The new tool
  exists and is reachable directly, but a caller going through the compiled floor still hits the
  old raw-subgraph path. Small, bounded follow-up: repoint the primitive.
- **D-3 (CR-73 dosha cancellation) — CODE-CLOSED, DATA-PENDING.** PR #735, merged. Found the
  brief's premise was partly stale: bespoke cancellation already existed for kemadruma, daridra,
  kala_sarpa (+12 variants), and manglik from an earlier commit — not reimplemented. The real,
  citable gap closed: `_cancel_kemadruma` was missing the kendra-support bhaṅga ground
  (BPHS-cited, already used by the firing-authoritative detector) — a genuine
  detector/dosha-label contradiction. Fixed with real geometry (kendra-from-Moon,
  kendra-from-lagna over the 5 tara-grahas), verified deterministically on both charts.
  **Confirmed by this session's live probe: production `kemadruma` still shows
  `fire_reason:"requires_pass"`** — same class of residual as CR-66, needs a rebuild dispatch,
  code fix not yet served.
- **D-4 (CR-30 KP face) — CLOSED, planner-wired.** PR #738, merged, CI green. No dedicated KP
  tool existed (`kp_query`/`query_kp_ruling_planets` were phantom-dropped, no engine ever backed
  them — correctly not restored as-is). Built `ganita_kp_cusps_get` fresh over already-stored L1
  KP data (cusp/star/sub/sub-sub lord chains), cross-checked 8/8 fields against raw
  `chart_facts` by hand (no transcription bug). **Confirmed live-wired this session** via
  `plan_retrieval`: the compiled floor's `kp_cusp_sublord_read` primitive now points to
  `ganita_kp_cusps_get` with `known_gap:null`. Direct tool round-trip not reachable this session
  (same new-tool connector-cache limitation as P-1).

## Register reconciliation (W-0 cluster 2 + cluster 3 stale items)

**PR #733, merged.** CR-68, CR-16, CR-61, CR-64 flipped from OPEN to CLOSED across
`registry_data.ts` + `cr_status.ts` (both packages, codegen-mirror-regenerated, not hand-edited)
+ a new surgical migration. CR-132 minted for CR-64's narrower orphan-ref residual rather than
re-opening CR-64. A standing note was added to `POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md`
flagging this as the third confirmed register-drift occurrence (after CR-56) — and this campaign
itself produced a **fourth** occurrence mid-campaign (CR-37's dark-flag surviving its own fix's
merge, caught and fixed in PR #743). The drift class is real and recurring; every wave that
touches `registry_data.ts` should re-verify its own dark-flags are cleared post-merge as a
standard step, not an afterthought.

## W-5 — Full re-verification (this session)

- **Targeted live probe per fixed item**: 9 of 11 lanes independently live-verified this session
  via direct MCP tool access (not delegated — subagents in this campaign hit an OAuth wall on
  this connector in non-interactive sessions; the Coordinator had direct access and used it).
  2 lanes (CR-24's new tool, CR-30's new tool) could not be round-tripped directly because they
  were deployed mid-session, after this session's MCP tool catalog was cached — confirmed
  instead via planner-level wiring (`plan_retrieval` showing the correct `live_tool`/`known_gap`
  for their primitives), which is dispositive evidence of deployment even without a raw tool call.
- **Fresh-context Opus adversarial verification**: dispatched against all 12 merged diffs. Same
  connector limitation applied to the verifier — it corroborated every fix via direct source
  review (reading the actual diffs, not trusting summaries) rather than reproducing live calls.
  **Verdict: all 12 CONFIRMED at the code level** — zero fabricated computation (§N B.10), zero
  circular/non-grounded derivations (§N.5) found in any diff. The verifier explicitly flagged
  that runtime numeric claims (before/after counts, differential firings, `backing_data_reachable`
  values) are author-reported and could not be independently reproduced by it — this is disclosed
  here, not glossed over. It also caught that this report's PR #743 was still open (not yet
  merged) at the time it reviewed — corrected below.
- **PR #743 (hygiene, this session)**: two accidentally-committed `node_modules` symlinks
  (self-referencing, introduced via a `git add -A` during PR #738's conflict resolution) removed
  from git tracking; the stale CR-37 dark-flag cleared. Both changes validated
  (`schema_validator.py` baseline unchanged at 43 violations, `tsc --noEmit` clean both packages)
  and opened as its own PR per the "each lane its own worktree/PR" constraint.

## Standing note on the recurring register-drift class

Four confirmed occurrences now: CR-56 (VIDHI-PŪRṆATĀ), CR-54/CR-59 (D-2), and CR-68/CR-16/CR-61/
CR-64 (this campaign's W-0) — plus a same-campaign recurrence on CR-37 (fixed mid-campaign, not a
prior-session artifact). The pattern: a fix lands, but the vidhi registry's `known_gap` flag on
the affected primitive is not part of the same PR's acceptance criteria, so it silently survives
the merge. **Recommendation for the native**: make "clear this primitive's `known_gap` if your
fix closes it" an explicit, checked step in every future fix-lane's PR template, not an implicit
expectation — W-5's own re-probe is what caught CR-37's recurrence, and that re-probe should not
be the only backstop.

## Exit — what unlocks it

Three concrete, bounded items stand between this report and Darpana unlocking:
1. **A build dispatch** to rebuild `phala_anchors` (CR-66) and the `dosha_label` rows (CR-73) —
   both are pure data-refresh, zero new code, blocked only on the same cockpit/write-DB access
   T-2 needs.
2. **T-2's own materialization dispatch** (≈23.5h, ≥4 resumable Cloud Run runs) — native has
   elected to run this personally via the cockpit UI.
3. **A small planner-wiring fix** repointing `mechanism_read` to `bodha_mechanisms_get` (CR-24) —
   bounded, no new computation, a registry-file change plus live re-verification.

No fabrication anywhere in the 12-PR diff set (adversarially confirmed). No accept-as-dark
recommendation is made for any of these three — all three are real, bounded, fabrication-free
paths to full closure; none requires new astrology or new derivation work. When they land, this
checklist should re-verify each live and move to a genuine v2.1/exit-met close.
