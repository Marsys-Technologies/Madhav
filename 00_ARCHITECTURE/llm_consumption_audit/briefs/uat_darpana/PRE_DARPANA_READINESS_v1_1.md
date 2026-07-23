---
artifact: PRE_DARPANA_READINESS
type: READINESS CHECKLIST (residual fixes + verifications before UAT-DARPANA opens)
version: 1.1
status: OPEN — exit condition NOT met. UAT-DARPANA remains HELD. Tier A is 3/6 CLOSED, 1/6
  OPEN (CR-131, honest blocker), 2/6 HALTED for native decision (A-5, A-6). Tier B is 2/5
  PASS, 1/5 PASS-with-caveat, 1/5 PARTIAL (new silent-empty finding), 1/5 FAIL-as-specified.
  This v1.1 reports the swarm's actual findings — not a stretched pass. v1.0's exit condition
  ("Tier A all CLOSED + Tier B all VERIFIED") is not satisfied; two decisions are reserved for
  the native per v1.0's own gate design.
context: PRE-DARPANA READINESS swarm executed 2026-07-23/24 (Coordinator: Sonnet, Opus
  step-ups on judgment-heavy investigate/decide/verify lanes per native directive). PR #728
  (VIDHI-PŪRṆATĀ) confirmed deployed live with image-SHA parity (A-2). PR #729 (governance
  close) merged (A-1, commit 64318a2f). PR #730 (A-4 D7 writer fix) opened this session.
changelog:
  - v1.1 (2026-07-24, PRE-DARPANA READINESS swarm close): per-item closure evidence added
    for all Tier A/B items below. A-1, A-2, A-4 CLOSED. A-3 (CR-131) confirmed OPEN with two
    independent, stacked blockers (sweep incompletion + a separate serving-path DATABASE_URL
    gap) — the brief's "~600x faster resume" premise was checked and found unsupported (actual
    ~6x). A-5 and A-6 HALTED for native decision per the brief's own reserved-gate design — no
    bounded, fabrication-free repair found for either; accept-as-dark recommended for both,
    disclosure mechanism verified live and working. Lane B independently reproduced one of
    A-6's findings (a silent empty in `phala_predictive_anchors_get`) and surfaced a new B-2
    FAIL: the Sat–Jupiter Apr–Aug 2027 standing-prediction claim could not be located on any
    live surface. Full per-item evidence below.
  - v1.0 (2026-07-23, native-commissioned via Cowork, Fable-compiled): original checklist.
---

# PRE-DARPANA READINESS — full-coverage checklist (v1.1, evidenced)

## Tier A — MUST FIX before Darpana

**A-1. PR #729 governance close — CLOSED.**
Root cause confirmed by reading `schema_validator.py`: `_SESSION_LOG_HEADING_RE` is an
ASCII-only regex (`^##\s+([A-Za-z0-9_.\-]+)\s+—`); PR #729's new heading
`## VIDHI-PŪRṆATĀ — ...` contains diacritics (Ū/Ṛ/Ṇ/Ā) that don't match the character class,
so the entry-splitter never recognized the heading as a boundary and bled the prior entry's
`session_close.session_id` into the wrong block. Fixed by leading the heading with the ASCII
`session_id` token (`## VIDHI-PURNATA-2026-07-23 — VIDHI-PŪRṆATĀ: ...`) and adding the missing
`session_open` block the same bug had masked. `schema_validator.py` went 44→43 violations, 0
CRITICAL/HIGH (exit=3, accepted by CI's policy); `drift_detector.py`, `msr_referential_
integrity.py --self-test`, `assert_no_native_literal.sh`, `edge_security_smoke.sh --ci-only`
all passed. Merged squash commit **64318a2f** on `main`. Branch deleted post-merge.

**A-2. Deploy merged planner to LIVE serving surface — CLOSED.**
CI auto-deploys on merge to `main` via `.github/workflows/deploy.yml` (`workflow_run` trigger).
For commit 350d8455 (#728): migrations 462/463 confirmed applied live
(`_migrations_applied` rows 348/349, timestamps 2026-07-23T18:46:01-02Z). Image-SHA parity
confirmed via `gcloud run services describe`: `amjis-web` revision `amjis-web-01118-6cs` and
`amjis-mcp` revision `amjis-mcp-00455-9h6` both running image tag `350d84552cfd4bd9a600
c4eeef056443ef5983c8` = main HEAD at merge time. All 4 live-verify probes passed via the
`marsys-jis-direct` connector, actual tool output quoted: (a) spirituality question →
`spirituality_deepdive` 13-item floor; (b) keyword-free "tell me about my money" → full
`wealth_deepdive` incl. E-3/E-7 elevation-band machinery; (c) unclassifiable question →
`general_synthesis` w/ `chart_digest_read` hard-floored (E-0 foundational floor); (d)
migrations 462/463 live. Non-blocking note: `amjis-sidecar` runs an older image — expected,
#728 didn't touch sidecar paths.

**A-3. CR-131 Gochara temporal serving — OPEN (honest, unresolved).**
Confirmed live: `ka_gochara_sweep` for 482012f1 is at exactly **165/300 substeps,
state='error'**, `last_error: "BLOCKED: upstream dependency(ies) timeout:21600s did not
complete in this run"`. The brief's own **"~600x faster post-memoization" premise was tested
against real timestamps and found unsupported** — measured speedup is **~6x** (30 min/substep
pre-memoization → ~4.9 min/substep post), meaning the remaining 135 substeps need **~11+ more
hours** across multiple 6-hour Cloud Run executions, not a quick resume. Also corrected: the
brief's "forward span 2026–2055" is overstated — live `kala_gochara_windows` actually spans
1949-12-31→2037-09-30. Re-dispatch was not possible from this session: the orchestrator
entrypoint requires a `build_runs` row created only by the authenticated cockpit web API, and
the only DB access available (`mcp__postgres__query`) is read-only (confirmed by a rejected
probe INSERT). **Independently of sweep completeness**, all three live serving tools
(`gochara_activation_get`, `gochara_forecast_get`, `gochara_election_avoidance_get`) currently
return empty with `backing_data_reachable:false, empty_reason:"...DATABASE_URL not set..."` —
a second, separate gap in the tools' execution environment (confirmed not a general MCP outage
via a working `ganita_chart_facts_get` control call). **Verdict: CR-131 remains OPEN.** No
fabricated windows or completion state reported.

**A-4. D7 `spouse_karya`→`progeny_karya` writer mislabel — CLOSED.**
Root cause confirmed by reading source: `VARGA_KARYA[7]` in
`platform/python-sidecar/ga_writers/ga_vargas_writer.py` read `"spouse_karya"`; D7 (Saptāṃśa)
is the classical progeny significator. One-line fix (dict-value only, FROZEN WriterBase
contract untouched) + regression test `test_d7_karya_is_progeny_not_spouse` (full suite
131/131 pass). Chart-scoped delete-then-insert rebuild actually executed for both
**482012f1** and **1c826d5a** via the writer's own `replace_prior_chart_divisionals`
idempotency path. Verified live, before/after: `spouse_karya`→`progeny_karya` on D7 for both
charts, **zero** `spouse_karya` rows remain DB-wide, per-chart `chart_divisionals` row counts
unchanged (22,092 both before/after), all other 144 karya labels per chart confirmed
unchanged. Landed as **PR #730** (fix not committed by the working lane; caught and corrected
during close — see Session Notes).

**A-5. Remedy-engine cluster (CR-67 + CR-69) — HALTED for native decision.**
Investigated (Opus), not implemented. Three independent root causes found, none a bounded
serving fix: (1) CR-67/`remedy_scan` — `bodha_rm_resonances.associated_cdlm_cells_array` is
**100% NULL DB-wide, across every built chart**; the `bo_upaya` writer has no code path that
populates it (an unimplemented L2 derivation, not a query bug). (2) CR-69/
`intervention_synthesis` — `query_remedies.ts` never reads the `leverage_ranked` arg and has no
leverage_index field; the intended data lives in a different, never-yet-populated table
(`bodha_rm_dasha_windowed_prescriptions`, builder landed 2026-07-22, this chart's `bo_upaya`
last built 2026-07-17 — plausibly just stale, not proven dead: the join was checked and found
satisfiable off L1 `chart_vichara` leverage_index rows). Fixing CR-69 alone would still need
both a first-ever production exercise of an unverified builder AND a serving-layer rewrite —
not a single bounded change. **Disclosure verified live and correct**: `health_deepdive` and
`wealth_deepdive` completeness receipts cite CR-67/CR-69 in the `dark` bucket with citable
`OPEN_CRS` entries, not silent empties. **Recommendation to native: accept-as-dark now
(disclosure is safe to ship); if closure is wanted later, CR-69 has a plausible bounded-ish
path (rebuild `bo_upaya` + rewire `query_remedies.ts`, no new astrology) but CR-67 requires
genuinely new derivation work and should not be bundled with CR-69.**

**A-6. Timing-anchor cluster (CR-66 + CR-37) — HALTED for native decision.**
Investigated (Opus), not implemented. Corrects the brief's own framing on two points: (1)
**A-3 did NOT resolve** (Gochara windows are not reachable — see A-3), but this does **not**
darken A-6 as the brief feared, because `taranga_curve`'s actual live_tool is `kala_bundle_get`
(avadhi + convergence + kala_activation), which is **live and Gochara-independent** — verified
returning real dasha-avadhi rows and 1,685 overlapping convergence windows. (2) The genuine
residuals are narrower than framed: `phala_anchors` synthesis is degenerate (8 rows total,
wealth=0, mostly build-date+90 artifacts collapsing onto one dasha window) and yoga-activation
dating is 16% (`kala_yoga_activation_get`: 15 rows, 13 undated) — but most of that 16% is
**correctly** undated: 12 of the 13 are always-on natal yogas (Anapha, Gola, Kedara, etc.) with
no discrete activation window by nature; dating them would be fabrication. No bounded,
fabrication-free repair exists for either data core (both require FROZEN-writer rebuilds +
external computation). **Two live disclosure bugs found and left unfixed pending native
sign-off** (both bounded, fabrication-free, ready to implement): (a)
`phala_predictive_anchors_get`'s empty response has **no `empty_reason` and no `known_gap`** —
a genuine silent empty, independently reproduced by Lane B (see B-1); (b) `yoga_activation_scan`
is defined but **wired into no floor** in `registry_data.ts`, so CR-37 never reaches any
completeness receipt regardless of the tool's own honest `undated_activation_count` field.
Also flagged: the defect register's CR-37/R-45 disposition ("0/13,364 dated") is **stale** — a
prior rebuild moved `kala_activation` to 97% dated; only the YOGA class (16%, mostly
structural) and DOSHA (48%) lag. **Recommendation to native: accept-as-dark for the data cores;
decide on shipping the two disclosure fixes (a) and (b) above — both are surgical and
fabrication-free.**

## Tier B — VERIFY before Darpana

**B-1. End-to-end plan→execute smoke, one question per floor — PARTIAL.**
All 8 floors (spirituality, education, progeny, marriage-with-timing, health-with-ayurdaya,
foundational-fallback, multi-domain union, pointed single-fact) compiled with honest
completeness receipts at plan-issuance — zero silent empties at that stage; every `dark`
item cites an OPEN CR. Execution-time spot checks served real rows (`ganita_ayurdaya_get` 26
rows, `bodha_chart_digest_get` 9,946 MSR signals, `phala_anchors_get` 5 rows, etc.). **One
silent-empty finding, independent of A-6's investigation but the same root**:
`phala_predictive_anchors_get(domain=wealth)` returns `{"anchors":[],"anchor_count":0}` with
**no `empty_reason`, `known_gap:null`** — and this tool is the `standing_predictions_read`
machine-band primitive present in **every** deepdive plan. Not waved through; folded into
A-6's native decision (disclosure fix (a) above addresses exactly this).

**B-2. Standing-predictions surface (E-2) — FAIL as specified.**
Exact, unapproximated result: Ketu-MD shape and Venus-MD 2034 are both **present**, but only
via `kala_bundle_get`/`ganita_dasha_lord_capability_get` timeline surfaces, not the named
standing-predictions primitive. **The Sat–Jupiter Apr–Aug 2027 claim was not found on any
live surface queried** (`kala_bundle_get` timeline, `phala_anchors_get`, `phala_outlook_get`,
`phala_predictive_anchors_get` — the last is empty per B-1). This is a genuine finding, not a
near-miss — folded into A-6's native decision alongside B-1.

**B-3. CR-130 dark-flag — PASS.**
`spirituality_deepdive`'s `spiritual_yoga_scan` floor item carries `known_gap:"CR-130"`;
completeness receipt's `dark` array cites `{"floor_item_id":"spiritual_yoga_scan",
"cr_row":"CR-130", ...}` — visible, not silent. Confirmed independently by Lane B.

**B-4. Connector environment — PASS, with one disclosed caveat.**
Lane B independently reached the live `marsys-jis-direct` connector (not localhost) and
confirmed the deployed planner resolves post-#728 intents (`spirituality_deepdive`,
`progeny_deepdive`, `education_deepdive`, elevation-band union) that did not exist pre-#728 —
corroborating A-2 independently, not merely trusting its report. Entitlement clean: exactly 4
charts entitled, `catalog_chart_select(482012f1)` succeeds with valid provenance, no
cross-chart leakage across any probe. **Caveat**: the fresh-context verifier could confirm the
connector serves post-#728 *behavior* but could not independently re-derive the exact image
digest from within this sandbox — that specific fact rests on A-2's `gcloud` check, not
re-proven by B-4.

**B-5. Sealed split + §11 governance untouched — PASS.**
The only Tier-A code diff across the whole swarm is A-4's: 1 line in `ga_vargas_writer.py` +
9-line regression test. A full keyword scan of that diff for
`calibrat|sealed|train|test_split|2020-01-01|split` returned zero hits. No calibration table,
`mimamsa_*` surface, or `sealed_split_guard.ts` boundary touched; FROZEN WriterBase
`run`/`plan_substeps`/commit-discipline untouched. Assertion holds.

## Tier C — ACCEPT-AS-DARK (unchanged from v1.0; native disclosure targets confirmed
reachable this session for CR-130, CR-67, CR-69 — see B-3, A-5)

- **CR-130** Jaimini spiritual yoga family — disclosure confirmed live and correct (B-3).
- **CR-61, CR-16, CR-24, CR-64, CR-68, CR-73, CR-30** — unchanged from v1.0; not
  independently re-verified by this swarm (out of this pass's scope).

## Exit condition — NOT MET

v1.0's exit condition ("Tier A all CLOSED + Tier B all VERIFIED") does not hold: A-3 is OPEN,
A-5 and A-6 are HALTED pending native decision, and B-1/B-2 carry real findings (not passes).
**UAT-DARPANA remains HELD.** Per the governing directive: "If any lane cannot close
honestly, report it OPEN with the exact blocker — do not stretch a partial into a pass." This
v1.1 does exactly that. Native decision needed on A-5 and A-6 (see above) before this checklist
can move toward a genuine v1.2 close; A-3 needs either a longer-running re-dispatch session
with write-DB/cockpit access and the `DATABASE_URL` serving-path gap closed, or an honest
re-scope of CR-131's timeline.

## Session notes (swarm process, for the record)
- Two background workers (A-2, A-4) dropped mid-response to a transient API error and were
  resumed from their transcripts rather than restarted — both completed correctly on resume.
- A-4's fix was applied and live-verified by its worker but **left uncommitted** in the working
  tree at lane-close; caught during the Coordinator's own close pass and landed properly as
  PR #730 (own branch, its own commit, CI-gated) rather than merged silently — consistent with
  the "each lane its own worktree/PR" hard constraint.
