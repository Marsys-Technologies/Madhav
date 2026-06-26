---
artifact: PRE_REGEN_FIX_PLAN_v1_0.md
canonical_id: PRE_REGEN_FIX_PLAN
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
parent: PRE_REGEN_FULL_AUDIT_CAMPAIGN_v1_0.md
purpose: >
  The fix plan that closes the L0–L4 audit campaign: apply the 6 open MAJOR findings (priority-ordered),
  each with a concrete fix AND a test that proves it against the ACTUAL offending data (not the pattern
  the author imagined — this campaign has had three "fixed≠complete" misses). Then full suite green →
  rebuild job image → re-prove main==prod → regenerate L0–L4 all charts → post-regen B7 isolation
  spot-check. Branch audit/pre-regen-wave0 → merges GREEN at the end.
audience: Claude Code (Antigravity)
---

# Pre-Regeneration Fix Plan (6 majors → regenerate)

## §0 — State
Branch `audit/pre-regen-wave0` (HEAD c79f85a8; main untouched; guard 6/6 GREEN). Audit W0–W5 complete:
11 contamination sites already fixed; 6 open MAJORS remain (below). Minors + cosmetics + L5 are out of
scope (deferred). Apply fixes on the branch; main stays untouched until the final green merge.

**GOVERNING RULE (from 3 "fixed≠complete" misses this campaign — LEL strip twice, 7-vs-9 sites,
green-guard-missed-2): every fix in this plan ships with a test that asserts against the ACTUAL
offending data/value, not just the author's assumed pattern.** A fix without such a test is not done.

## §1 — Priority order (by real urgency, not finding number)
1. **F-W5-001 — l4_anchors chart_id guard (LIVE PUBLIC EXPOSURE — do FIRST, independent of regen).**
2. **F-W4-005 — ka_dasha_kala psycopg3 crash + chart_id isolation (RUNTIME CRASH / build-breaking).**
3. **F-W5-003 — ph_muhurta native 10th-lord hardcoded (contamination — derived-native-fact class).**
4. **F-W5-002 — l4_anchors LEL EVT.* leak (2nd incomplete LEL fix — public exposure).**
5. **F-W4-002 — ka_sangam EnrichmentContext dead → convergence bias all charts.**
6. **F-W4-004 — ka_vighnakara gandanta/papakartari stubs → kala_obstruction under-populated.**

## §2 — The fixes (each: change + the mandatory proof-test)

### FIX 1 — F-W5-001 l4_anchors chart_id guard (live cross-chart exposure)
`brahmagyan/phala/l4_anchors.py` `query_phala_anchors()`. The docstring promises non-native →
empty, but the guard was never written; any chart_id gets the full native ANCHOR_CATALOG via the public
endpoint. FIX: at the top of the function body:
```
if chart_id != NATIVE_CHART_ID:
    return {"ok": True, "chart_id": chart_id, "anchors": [], "anchor_count": 0}
```
PROOF-TEST: call query_phala_anchors with a NON-native chart_id → assert empty anchors; with the native
chart_id → assert the full catalog still returns. (Don't just assert the guard exists — assert the
non-native call returns empty.) This is live exposure — verify it on the deployed endpoint after fix.

### FIX 2 — F-W4-005 ka_dasha_kala psycopg3 crash + isolation
`pipeline/orchestrator/writers/ka_dasha_kala.py`. (a) `_update_registry_health()` calls
`conn.execute(...)` — psycopg3 connections have no `.execute()`; replace with
`with conn.cursor() as cur: cur.execute(...)`. (b) `run(ctx)` ignores `ctx.config['chart_id']` — add
`chart_id = ctx.config['chart_id']` at the top of run() and scope ALL its queries by it.
PROOF-TEST: a unit/integration test that actually RUNS the writer's registry-health path (would raise
AttributeError today) and asserts no exception; and a test that the writer's queries carry the passed
chart_id (not a default). Run on 1c826d5a end-to-end to confirm it builds without the crash.

### FIX 3 — F-W5-003 ph_muhurta native 10th-lord hardcoded (derived-native-fact contamination)
`services/ph_muhurta/engine.py` `ACTION_GRAHA_MAP`. The map hardcodes career/business →
Saturn because the NATIVE's Capricorn 10th house makes Saturn the 10th-lord (the comment admits it).
For any non-native chart this injects the native's house-lord. FIX: keep ACTION_GRAHA_MAP as a domain→
archetype mapping ONLY; remove native-specific house-lord encoding. At write time, look up the relevant
house lord(s) for the TARGET chart from `ga_condition_composite` (or a lagna-lord lookup) keyed by
chart_id, and derive personalization_graha from THAT.
PROOF-TEST: build the muhurta personalization for a NON-native chart with a different lagna and assert
the career/business personalization_graha ≠ the native's Saturn (i.e. reflects the target chart's
10th-lord). This is a NEW contamination shape (a derived native fact baked as a constant, grep-invisible)
— note it in the findings register so future audits look for derived-native-fact constants, not just
NATIVE_BIRTH.

### FIX 4 — F-W5-002 l4_anchors LEL EVT.* leak (2nd incomplete LEL fix)
`brahmagyan/phala/l4_anchors.py` `strip_lel_citations()`. The current regex
`r'\bper LEL\b.*?(?:\.|$)'` misses `LEL EVT.2019` fragments (e.g. in ANC.CAREER.2027.01 notes). FIX:
broaden to cover both forms, e.g. `r'\b(?:per LEL|LEL EVT\.\S+)\b[^.]*\.?'` (or a cleaner equivalent
that strips the whole parenthetical when LEL-derived).
PROOF-TEST (this is the lesson — do NOT skip): iterate EVERY notes string in ANCHOR_CATALOG, run the
strip, and assert ZERO `LEL` substring remains in ANY of them. Not "the regex matches my example" —
a sweep over the real catalog. (C2-002 shipped narrow once already; this closes it for good.)

### FIX 5 — F-W4-002 ka_sangam EnrichmentContext never populated
`pipeline/orchestrator/writers/ka_sangam.py` + `services/ka_sangam/`. EnrichmentContext is empty, so
currents C7 (ashtakavarga), C11 (vedha), C12 (tajika), C13 (school_consensus) score 0.0 for EVERY chart
→ convergence scores systematically biased. FIX: pre-fetch vedha rules, ashtakavarga bindus, tajika
year lords, and school-consensus weights from the DB into EnrichmentContext BEFORE mode_a_search() /
mode_b_sweep().
PROOF-TEST: after the fix, on a real chart, assert C7/C11/C12/C13 are NON-zero (and plausibly varied)
for at least one convergence row — proving the enrichment now flows. A distribution check that those
currents aren't uniformly 0.0.

### FIX 6 — F-W4-004 ka_vighnakara gandanta + papakartari stubs
`pipeline/orchestrator/writers/ka_vighnakara.py` (~L180-201). Two of four obstruction checks always
return None; Saturn window is a placeholder (2030-2032). FIX (native chooses A or B — default A):
- (A) IMPLEMENT: gandanta = Moon longitude (from ka_graha_sancara) in last 3°20' of Cancer/Scorpio/
  Pisces; papakartari = lagna hemmed between malefics (from chart_facts). Real logic, cited rules.
- (B) If not implementing now: explicitly mark them `stub=True` (or NOT_IMPLEMENTED) in the DB row so
  downstream consumers KNOW coverage is partial — no silent None masquerading as "no obstruction."
PROOF-TEST: (A) a chart with a known gandanta Moon yields a gandanta obstruction row; (B) the rows
carry the stub flag and a consumer can distinguish "checked, none" from "not checked." Either way, no
silent None.

## §3 — Close-out sequence — CODE ONLY (this brief STOPS at step 5; NO data generation)
**SCOPE BOUNDARY (native directive):** this brief is the CODE fix + merge + deploy-readiness ONLY. It
does NOT regenerate any data. The native will generate the data themselves, at runtime, by pressing the
global Build button in the **Nirmāṇa build tracker** — that act is also the live validation of the
hardened global-build path. Do NOT call execute_run for a regeneration, do NOT auto-build any chart.
1. FULL sidecar test suite GREEN on the branch (incl. all 6 new proof-tests + the contamination guard
   6/6). No skips.
2. Fold the deferred MINORS into the findings register as KNOWN-NON-BLOCKING (don't lose them — they're
   future cleanup): L2 ×5, L3 ×5, F-W5-004 (logger elevation), F-W5-005 (cosmetic).
3. MERGE `audit/pre-regen-wave0` → main (GREEN — all guard tests pass). Push.
4. REBUILD the Cloud Run job image from the new main HEAD (so the writer fixes are in the image the
   build tracker will invoke). Confirm deployed job-image commit == new main HEAD (the standing
   pre-build gate).
5. RE-PROVE main==prod across planes (web/sidecar/mcp/job-image ancestor-correct; migrations current) —
   the LOCALHOST_PROD_FULL_SYNC_CHECK.
   **← THIS BRIEF ENDS HERE.** Deliver: 6 fixes + proof-tests green, merged main SHA, job-image digest
   == main HEAD, main==prod parity table. STOP and report. The system is now CODE-READY for the native
   to generate data via the build tracker.
   EXCEPTION: F-W5-001 (live public exposure of native anchors) may be deployed AHEAD of the others —
   it's leaking now; don't wait for the full merge to ship just that guard if it can go safely alone.

## §4 — SEPARATE PHASE (native-triggered, NOT part of this brief): generate + verify
Done BY THE NATIVE through the Nirmāṇa build tracker after §3 reports code-ready:
- The native presses global Build (and per-layer/per-asset as desired) in the tracker UI to regenerate
  L0–L4 for the charts they choose — exercising + validating the hardened global-build/DAG path.
- POST-REGEN B7 isolation spot-check (the sole post-regen backstop) is run AFTER that generation: for
  ≥1 asset per layer confirm a NON-native chart's regenerated rows carry ITS OWN values, not the
  native's (Abhinandan Sun ~318° Aquarius), and specifically re-verify the three exposure/contamination
  fixes — F-W5-001 non-native anchors empty, F-W5-003 non-native muhurta graha ≠ native Saturn,
  F-W5-002 no LEL leak in served notes. A failure = a missed vulnerable site → halt, fix, rebuild image,
  re-generate the affected asset. (This check can be authored as its own short verification prompt when
  the native is ready to run it.)
- THEN the campaign closes; L5 Mīmāṃsā audit is the next separate effort (gated on L4 close).

## §4 — Guardrails
- Branch only until step-3 green merge; never merge while any guard/proof-test is red.
- Every fix ships its proof-test (§0 governing rule) — assert against actual data, not assumed pattern.
- F-W5-001 (live public exposure) should land + deploy ASAP, even ahead of the full regen sequence —
  it's leaking native data on a public endpoint right now.
- Native 482012f1 read-only/FORENSIC-gated in regen; destructive checks on 1c826d5a only.
- FROZEN orchestrator contract — conforming writers only (F-W4-005's cursor fix conforms).
- The two contamination fixes here (F-W5-003 derived-native-fact, and any new shape) → widen the grep
  guard / document the shape so the structural guard keeps pace.
