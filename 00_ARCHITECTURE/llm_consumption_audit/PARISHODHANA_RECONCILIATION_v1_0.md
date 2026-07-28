---
artifact: PARISHODHANA_RECONCILIATION
canonical_id: PARISHODHANA_RECONCILIATION_v1_0
version: 1.1
status: PHASE-B-C-COMPLETE
created: 2026-07-27
author: PARIŚODHANA Conductor (Phase A: 8 parallel Sonnet probers A1-A8; Phase B: 8 builders +
  1 follow-up; Phase C: 3 builders; Verifier: 1 Opus agent + Conductor spot-re-verification)
mode: FULLY AUTONOMOUS per PARISHODHANA_BRIEF_v1_0.md, native-confirmed this session (T3-7
  authorization-chain concern from PROGRAM_LEDGER §1 Tier 3 carried forward as UNRESOLVED/
  NATIVE-GATED, not closed by this campaign — see §5 below).
changelog:
  - "v1.1 (2026-07-28): appended §6 — Phase B/C outcomes, Opus Verifier verdict, Conductor
    re-verification of 2 disputed items, final open list. Full detail in
    PARISHODHANA_REPORT_v1_0.md."
---

# PARIŚODHANA — Phase A Reconciliation

One row per ledger item probed. Evidence is a live production MCP call (via `mcp__marsys-jis-direct__*`
against chart `482012f1-710e-4a25-994a-93821f5871aa`, 2026-07-27) or a direct code/DB read, captured
in full by each prober and append-only annotated into the item's source register where the
disposition is ALREADY-FIXED. See the source registers for full evidence text; this table is the
routing index for Phase B.

## §1 — Disposition table

| Item(s) | Cluster | Prober | Disposition | Phase-B routing |
|---|---|---|---|---|
| CR-1 | Receipt-honesty | A1 | ALREADY-FIXED | none |
| CR-2, CR-63 | Receipt-honesty | A1 | **LIVE-OPEN** (reopened — refutes ledger's own "false-alarm" hypothesis) | B1 |
| AS-1/R-38 | Receipt-honesty | A1 | **LIVE-OPEN** (reopened) | B1 |
| AS-1/R-41 | Receipt-honesty | A1 | ALREADY-FIXED | none |
| CR-5, CR-12, CR-37 | Empty-join | A2 | ALREADY-FIXED | none |
| CR-48 | Empty-join | A2 | ALREADY-FIXED (narrower residual noted: 9/16 rows undated by design for structurally-always-on nabhasa/panchanga facts — not the original "every row" claim; not routed as a new defect) | none |
| `mimamsa_lel_query` query/offset no-op | Filter-fallthrough | A3 | **LIVE-OPEN** (4th consecutive campaign confirmation; root cause located: `query_life_events.ts` handler never reads `args['query']`/`args['offset']`) | B1 (highest priority in cluster) |
| CR-42 (`ref_remedies_get` member) | Filter-fallthrough | A3 | ALREADY-FIXED | none |
| CR-42 (`ref_dasha_systems_get`, `ref_dignity_reference_get`, `ref_nakshatra_get` members) | Filter-fallthrough | A3 | **LIVE-OPEN** — new failure mode (documented silent-fallthrough fix IS present in code, but all three now fail loudly on every call: TimeoutError / DB-400) — a **newly discovered live defect**, not the originally-documented one | B1 |
| CR-10 | Filter-fallthrough | A3 | ALREADY-FIXED | none |
| CR-72, CR-73, CR-74 | Decorative-data | A4 | ALREADY-FIXED (caveat: verified specimens are manglik/kemadruma/daridra/kala-sarpa; remaining ~18 catalog dosha types did not fire in probe, not individually audited) | none |
| CR-19/CR-66/EL-17 | Wealth-layer emptiness | A5 | **LIVE-OPEN** — root cause newly located: `ph_nimitta.py` `_load_discoveries()` takes `affected_domains_array[1]` only (first element), silently discarding wealth-tagged rows where wealth isn't the first tag (51 wealth-tagged `bodha_discoveries` rows exist and are discarded this way) | B1 (root-caused, scoped fix) |
| CR-20/CR-67 | Wealth-layer emptiness | A5 | ALREADY-FIXED | none |
| R-09 | Wealth-layer emptiness | A5 | **LIVE-OPEN** — `associated_doshas_array` still 0/45 populated (upstream has no firing doshas to link for this chart); `estimated_cost_inr_range_jsonb` no longer NULL but carries only an honest `{available:false,...}` disclosure object, not a real figure — literal "100% NULL" claim is stale but substantive gap persists | B1 (disclosure honesty already better than documented; dosha-linking gap is the real residual) |
| R-10 | Wealth-layer emptiness | A5 | **LIVE-OPEN** — `leverage_index` fully absent from `assess_wealth`/`bodha_remedies_get` response shape; underlying data exists and is correct (`ganita_vichara_get(family=leverage_index)`, 7 populated rows) — pure serving-layer wiring gap | B1 |
| CR-8, CR-9 | Sidecar/auth | A6 | ALREADY-FIXED | none |
| CR-40 | Sidecar/auth | A6 | **LIVE-OPEN** (mixed) — `kala_bundle_get` half fixed; `pact_query` TRIGGER stage still returns `chain_incomplete_infra` | B1 |
| AS-7 | Sidecar/auth | A6 | NOT-REPRODUCIBLE — register scopes this as local-dev-bench-vs-deployed; this campaign has no bench access, only production; deployed side confirmed clean, bench side unprobable this session | carry forward, unprobed |
| CR-39/CR-14 (`holistic_bundle`) | Bundle honesty | A6 | **LIVE-OPEN** — disclosure fixed and improved same-day (commit `1a84306e`, `ok:false`/`degraded` now structurally enforced), but the underlying 5/8 sub-tool failures (MSR/CGM/LEL/PANCHANG/DASHA, uniform DB-backed HTTP failures) are diagnosed, not repaired | B1 — but root cause is shared upstream infra, may be large; see §2 |
| R-08, R-27/EL-19, R-44 | Small serving residuals | A7 | ALREADY-FIXED | none |
| R-29/EL-51 | Small serving residuals | A7 | **LIVE-OPEN** — `bodha_remedies_get` chart-scoped narrowness (3 vs 29 global rows) + no `maraka_contraindication_verdict` field exists anywhere | B1 |
| R-42/EL-58 | Small serving residuals | A7 | **LIVE-OPEN** — migration SQL fully written, never created as a numbered migration/run; live-confirmed reproduces (2011 window still `open` in 2026) | **B3** (pure execution, no design) |
| R-43/EL-60a | Small serving residuals | A7 | **LIVE-OPEN** — `reading_notes_get` still a single hardcoded blob, no accretion path | B1 or PARK (see §2) |
| EL-31 (`query_house`) | Small serving residuals | A7 | **LIVE-OPEN**, confirmed genuinely never built (explicit in-code PARKED-HONEST comment) | conditional B3 — only if a builder confirms `query_planet` is a simple mirrorable pattern; else PARK-HONEST (this is capability-addition, not a fix — see §2) |
| EL-07 | Small serving residuals | A7 | **LIVE-OPEN** — static absence-lint metric, non-blocking, count has moved 15→19 (worse, not better) since last recorded | Phase C / T4 hygiene, not Phase B |
| T1-2 (dark corpus) | Tier-1 gate | A8 | **LIVE-OPEN** — existing report numbers are stale (predate 3 same-day commits that rewired assess_wealth/assess_career serving); phenomenon not falsified, re-measurement required | B2 step 3 (re-measure after B2 steps 1-2 deploy) |
| T1-3 (Ω8 floor wiring) | Tier-1 gate | A8 | **LIVE-OPEN** — confirmed still unwired: 4 of 5 parked sub-items (`ashtakavarga_scan` per-varga, `special_lagna_read` widened, `argala_read`, `dispositor_closure_read`, `cross_ayanamsha_agreement`) absent from `registry_data.ts`; only `mechanism_read` pre-existed | **B2** (centerpiece) |
| CR-81, CR-82 | Tier-1 gate (T1-7) | A8 | ALREADY-FIXED | none |
| T1-7 (compound) | Tier-1 gate | A8 | ALREADY-FIXED (mechanical roots); headline 93%-noise number itself unverified, flagged for re-measurement, not re-derivation | note only |
| CR-84 | Tier-1 gate (T1-8) | A8 | ALREADY-FIXED | none |
| CR-85, CR-86 | Tier-1 gate (T1-8) | A8 | **LIVE-OPEN** (partial fixes only — dead passenger field / dead edge type persist) | carry forward, not routed to B (narrow, low-value residual per ledger's own framing) |
| T1-8 (compound) | Tier-1 gate | A8 | **LIVE-OPEN** net (1 of 3 sub-claims closed) | note only |
| T1-11 (gochara health/adverse class) | Tier-1 gate | A8 | **LIVE-OPEN**, confirmed exactly as documented | **OUT OF SCOPE per brief §4 — carry to close report's open list, do not build** |
| Chart `1c826d5a` staleness | Second-chart coverage | A8 | **LIVE-OPEN**, confirmed (78/303 substeps committed, no near-term gochara windows) | carry forward — closing requires an upstream sweep re-run, which is outside a "serving/planner-side only" B1-B3 fix and outside this authorization's rebuild prohibition in its `ka_gochara_sweep` form; note for native |

## §2 — Notes carried forward for Phase-B scoping

- **`holistic_bundle` sub-tool failures (CR-39/CR-14):** root cause is 5 sub-tools uniformly failing on DB-backed HTTP calls — this could be a shared infra problem (e.g. a sidecar connection pool or timeout setting) rather than 5 independent bugs. B1 will investigate as ONE shared-root-cause fix attempt before treating it as 5 separate fixes; if the shared root cause is deeper than a serving-layer/planner-layer change (e.g. touches infra provisioning), it will be PARKED-HONEST rather than forced.
- **CR-42's newly-discovered failure mode** (`ref_dasha_systems_get`, `ref_dignity_reference_get`, `ref_nakshatra_get` — TimeoutError/400 on every call): this is a NEW live defect, not the one originally documented (which is fixed). It gates on B1 root-causing whether this is a serving-layer regression fixable within this campaign's rails, or an infra issue requiring native escalation.
- **EL-31 (`query_house`):** building a wholly new tool is capability-addition, not a bugfix — closer in kind to the E4 list than to a B1 cluster fix. Routed conditionally: attempt only if trivially mirrorable from `query_planet`; otherwise PARK-HONEST and note for a future commissioned wave.
- **R-43/EL-60a (`reading_notes_get` accretion):** per `STREAM_GAMMA_CLOSE_v1_0.md`, this was already PARKED-HONEST as "blocked on α, needs tools/**" — Phase B will attempt only if the blocking condition has resolved; otherwise it stays PARKED-HONEST, consistent with the prior disposition.
- **T1-9 (W7 flagship bar)** was not itself reprobed (SAMĀPANA already verified it live) but interlocks with B2 — B2's acceptance criteria supersede it.

## §3 — Tally

- **ALREADY-FIXED (register stale), annotated in place:** 21 item-groups.
- **LIVE-OPEN, routed to Phase B (B1/B2/B3):** 19 item-groups.
- **LIVE-OPEN, explicitly carried forward / out of scope / native-gated / needs escalation:** 6 item-groups (AS-7, CR-85/86 residual, T1-11, chart `1c826d5a` staleness, EL-07 hygiene, T1-8 net note).
- **NOT-REPRODUCIBLE:** 1 (AS-7, bench-side unprobable).

The premise holds in both directions, as predicted: a substantial fraction of "open" items were already fixed and undocumented (register drift is real and large), **and** a substantial fraction of items are genuinely still open — including two items (the CR-42 new failure mode, and the CR-19/66/EL-17 root cause) that are **newly discovered defects this session**, not previously documented ones.

## §4 — Correction to the ledger's own framing

`PROGRAM_LEDGER_AND_ELEVATION_ROADMAP_v1_0.md`'s framing of **CR-2 as a "strong false-alarm candidate"** is refuted, not confirmed, by this reprobe (see A1's evidence — the ledger's hypothesis likely conflated `verdict.varga_subscores`, a genuinely-populated field, with `checklist.varga_confirmation.rows`, which is still always empty). This is itself an instance of the drift class the campaign exists to correct, now corrected.

## §5 — T3-7 (authorization-chain concern) — status

Per native instruction this session: **carried forward as UNRESOLVED / NATIVE-GATED**, not closed by this campaign. The native explicitly confirmed this specific PARIŚODHANA run as genuine, real-time authorization (via direct question-and-answer in-session, not a document asserting prior approval) — that resolves authorization for *this run only*. The underlying concern (documents/briefs asserting "a human already approved this" arriving conveniently) remains open and is not adjudicated here; it requires the native's own read per ledger Tier 3 T3-7, independent of this campaign's outcome.

## §6 — Phase B/C outcomes + Opus Verifier verdict (2026-07-28)

12 Phase-B PRs (#827-834, #847-849) + 4 Phase-C/follow-up PRs (#857-860) merged to `main`; both
`amjis-web` and `amjis-mcp` redeployed and confirmed serving the merged code at 100% traffic on
`latestRevision` (no pinning). Full build-by-build detail is in `PARISHODHANA_REPORT_v1_0.md`.

**Opus Verifier ran against live production post-deploy** (ONE agent, never writes code, four
dispositions). 7 of 10 checked items **CONFIRMED**: R-10 leverage_index wiring, CR-2/63/R-38 varga
receipt honesty, R-29/EL-51 gemstone match + maraka verdict, `mimamsa_lel_query` filter/pagination,
T1-1 dossier discoverability, T1-3 Ω8 floor wiring (coarse live proxy), and the full preserve-list
(no regressions). CR-40/pact_query was independently CONFIRMED within the split item-6 check.

**Two items the Verifier flagged were re-investigated by the Conductor directly, with the
following outcome:**

1. **CR-42's ref_dasha_systems_get/ref_nakshatra_get (PR #830):** Verifier's single-pass test
   found 100% timeout on both tools with real filter arguments. Conductor re-tested with the
   identical parameters (`system=vimshottari`, `keyword=yogini`, `lord=ketu`,
   `nakshatra=purva_bhadrapada`) immediately after and got **4/4 clean successes with real,
   substantial content** (the 4s embed-timeout fallback to `keyword_trigram_only` ranking, per
   PR #830's design, engaging correctly). Disposition: **CONFIRMED on re-verification** — the
   Verifier's finding is not discounted, but is most likely explained by a transient/cold-start
   condition at test time rather than a standing defect. Flagged for light monitoring, not
   carried forward as open.
2. **CR-39/CR-14 holistic_bundle (PR #848, then #859):** Verifier found the bundle's 5/8
   sub-tool failures byte-identical to the pre-fix state despite #848 being merged. Conductor
   investigation found the actual root cause: **two separate, duplicate implementations** of the
   bundle logic exist (`platform/src/lib/mcp/bundle_adapters.ts`, fixed by #848, and
   `platform-mcp/src/bundles/holistic_bundle.ts`, the copy the live `bodha_bundle_get` MCP tool
   actually calls, never touched by #848). PR #859 applied the identical, already-proven fix
   to the real copy and deployed. **Post-#859 re-test still shows the same 5/8 failure** —
   `chart_id` is now confirmed correctly present in `attempted_params` (the originally-diagnosed
   bug is fixed), but the sub-tools fail with a generic `tool_error`, not the original
   `CHART_REQUIRED` shape. Calling the underlying primitives directly as standalone MCP tools
   (`bodha_signals_get`, `bodha_graph_subgraph_get`) with the same chart_id succeeds cleanly —
   so the primitives themselves are healthy; the residual bug is specific to the bundle's
   internal `/api/mcp/primitives/[tool]` self-call path (wrong auth header, wrong route, or a
   param-shape mismatch not yet isolated). Disposition: **PARKED-HONEST, genuinely still open**
   — two real, distinct defects existed in this one item (chart_id threading, now fixed twice
   over both copies; and this second, undiagnosed self-call bug, not yet fixed). This is the
   **honest close** the brief's PRIME RULE calls for: two rounds of fixing landed real
   improvements without fully closing the item, and that is disclosed rather than papered over.

**Phase C:** deploy-pipeline parity for `amjis-mcp` (PR #857) built the no-traffic → smoke →
promote pattern amjis-web already had; the `mcp-canary-key` Secret Manager secret already existed
but the deploying service account lacks `secretmanager.secretAccessor` on it — **native IAM grant
still required** before this pipeline runs cleanly (exact command in the PR body). The
reconciliation-cadence detector (PR #860) shipped and immediately found 14 real divergences on its
first dry run, including a newly-discovered `cr_status.ts` dual-copy drift class analogous to the
Ω8 registry drift B2 found. Harness certification (PR #858) ran both sealed graders for real
(never modified them): `consumption_grader.ts` scored 0/12450 for a diagnosed, not fixed, reason
(it cannot credit orchestrating tools that aggregate hundreds of primitives server-side); the LLM
rubric grader returned an honest `NOT_LLM_GRADED` (no API keys in this sandbox). It also surfaced
that the historically-separate 2/13 naive-routing and ≥12/13 dossier-paging baselines may have
converged in current production — flagged for a blind re-run before being treated as sealed, not
claimed outright.

**Final open list (carried forward, not closed by this campaign):** AS-7 (bench-side, unprobable),
CR-85/CR-86 residuals, T1-11 (gochara health class, explicitly out of scope), chart `1c826d5a`
staleness (needs an upstream sweep re-run), EL-07 hygiene metric, R-09 dosha-linking (writer-level,
L2, out of scope), CR-19/66/EL-17's `ph_nimitta.py` fix (writer-level, L4, out of scope, but
root-caused precisely), `ka_avadhi.py` stale tuple (rail-scope conflict with the brief's own B3
list, flagged for native), EL-31/`query_house` (capability-addition, not a fix), R-43/EL-60a
(`reading_notes_get` accretion, still blocked), `maraka_contraindication_verdict`'s wider gemstone
build (was found to already exist, not a gap), and the `holistic_bundle` self-call residual
described above. T3-7 remains NATIVE-GATED per §5.
