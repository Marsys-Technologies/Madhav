---
artifact: GANITA_INTEGRITY_FIX_PHASED_BRIEF_v1_0.md
canonical_id: GANITA_INTEGRITY_FIX_PHASED_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Single self-contained, phased Claude Code execution brief that resolves the two Gaṇita integrity
  bugs found on Abhinandan Mohanty 1c826d5a (ga_positions chart-identity contamination + ga_sensitive
  KN-Rao Ātmakāraka reckoning), cleans up the orphan charts, rebuilds the chart cleanly, and proves the
  build tracker shows DB truth — in dependency-correct order so nothing is rebuilt twice.
audience: Claude Code (Antigravity)
consolidates:
  - GA_POSITIONS_CONTAMINATION_BRIEF_v1_0.md
  - GA_POSITIONS_FIX_EXECUTION_v1_0.md
  - GA_SENSITIVE_AK_RECKONING_FIX_BRIEF_v1_0.md
  - BUILD_TRACKER_WRITER_FIXES_PERSIST_BRIEF_v1_0.md
  - BUILD_TRACKER_REFRESH_BRIEF_v1_0.md
---

# Gaṇita Integrity Fix — single phased brief

## §0 — Context (read once)
Two integrity bugs surfaced on non-native test chart **Abhinandan Mohanty
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`** (SAFE — destructive ops allowed here; the native
**`482012f1-710e-4a25-994a-93821f5871aa`** is ground-truth and must NEVER be touched destructively):

- **BUG A — ga_positions chart-identity contamination.** `ga_positions` stored the NATIVE's planetary
  positions under non-native chart_ids (Abhinandan's Sun read 291.96° Capricorn = the native's, not his
  real ~318° Aquarius). Root cause: the orchestrator adapter dropped `birth_params`, so the writer fell
  back to a hard-coded `NATIVE_BIRTH`. All 14 non-root ga_ assets for 1c826d5a are downstream-suspect.
- **BUG B — ga_sensitive KN-Rao Ātmakāraka reckoning.** The KN Rao 8-graha AK ranking sorts Rāhu on
  raw `degree % 30` instead of the school's reverse `30 − (degree % 30)`. With Rāhu in late Aries this
  spuriously makes Rāhu the AK over Mercury in 4 of 5 ayanāṁśas → a FALSE "AK divergence" warning.

Operating rules: data plane = prod via Cloud SQL proxy **:5433**; builds run on **Cloud Run job
`brahma-build-pipeline-job`** (a web deploy does NOT rebuild the job image — confirm `job_image_tag`);
rebuilds go through **`execute_run`** (never the local one-off script, never a hand-built run). FROZEN
orchestrator contract — fix via conforming writers/adapters, never by changing the orchestrator.

**The BUG A code fix is ALREADY in the working tree (Cowork-authored)** — Phase 1 verifies it, does not
re-derive it. The BUG B code change is authored in Phase 2.

---

## PHASE 1 — Verify + commit the ga_positions fix (BUG A code, already applied)
Cowork already edited 3 files. Confirm via `git diff`, do not rewrite:
- `pipeline/orchestrator/writers/ga_positions.py` — adapter now passes
  `birth_params=ctx.config.get('birth_params')` (it previously dropped it — THE bug; every peer ga_
  adapter already passes it).
- `ga_writers/ga_positions_writer.py` — `build_ga_positions` `chart_id` is now REQUIRED (removed the
  `=CANONICAL_CHART_ID` footgun); birth-param resolution replaced `bp = birth_params or NATIVE_BIRTH`
  with: explicit params win; `NATIVE_BIRTH` allowed ONLY when `chart_id==CANONICAL_CHART_ID`; a
  non-native chart with no birth_params RAISES (refuses to contaminate). FORENSIC gate is already
  native-scoped — no change needed.
- `tests/test_ga_orchestrator_conformance.py` — two ownership tests now pass `_DUMMY_BIRTH`; added
  `test_non_native_without_birth_params_refuses_native_fallback` and
  `test_native_without_birth_params_uses_native_default`.

DO:
1. `git diff` — confirm exactly those 3 files changed, nothing else. If anything else differs, list it
   and STOP.
2. `pytest` the sidecar: ga_positions tests + `test_ga_orchestrator_conformance` +
   `test_ga_writer_generalization`. All green; the two new regression tests must pass.
3. Grep for any other `build_ga_positions(` caller relying on the removed `chart_id` default (a bare
   call with no chart_id). Known callers (ga_prashna_cast, build_runner, the adapter, tests) all pass
   it — confirm none break.
4. COMMIT: `fix(ga_positions): pass per-chart birth_params; refuse NATIVE_BIRTH fallback for non-native charts`
   Report the SHA.
GATE: do not advance to Phase 2 until Phase 1 tests are green and committed.

---

## PHASE 2 — ga_sensitive KN-Rao AK reckoning fix (BUG B code)
File: `ga_writers/ga_sensitive_writer.py`, `_build_karaka_rows` (~L968-1018).

2.1 — CITATION GATE (read-only, BEFORE the edit; canonical-or-floor rule — do not encode a convention
uncited). Confirm the rule "KN Rao reckons Rāhu's degree-in-sign in reverse (`30 − (long mod 30)`) for
chara-kāraka ranking." Search the project's own classical layer first (bg_texts / brahma_yoga_catalog /
bg_rules and 08_CLASSICAL_CROSS_REFERENCE) and quote the reference. If the corpus has it, cite the id.
If it does NOT, STOP and ask the native for a source — do not invent one and do not proceed to 2.2.

2.2 — THE FIX (after 2.1 yields a citation):
- In the KN Rao 8-graha ranking, compute Rāhu's effective sort degree as `30 − (rahu_long % 30)`; all 7
  classical grahas keep `long % 30`. Do NOT alter the Parāśarī 7-graha set. Keep the STORED
  longitude/degree facts truthful (reversal affects RANKING only — store raw, rank by reversed). Add a
  one-line comment citing the 2.1 source.
- Keep the `ak_divergent` warning path intact (it is correct when a divergence is REAL — e.g. Rāhu
  genuinely highest under reversed reckoning); we are fixing the comparison input, not removing the
  guard.
2.3 — CLEANUPS (same commit):
- Docstring ~L976 still says "AK divergence → halt build" — update to warning-not-halt + reverse
  reckoning.
- `_build_esoteric_rows` (~L1073) computes AK Parāśarī-only while `_build_karaka_rows` runs both
  schools. This is a NATIVE DECISION (both-schools vs Parāśarī-only) — do NOT change unilaterally; add
  `# NOTE: Parāśarī-only by current design — native decision pending (AK reckoning fix §2.3)` and leave
  as-is unless the native has ruled.
2.4 — TESTS: fixture matching 1c826d5a (Rāhu ~28° raw late Aries, Mercury ~27.5°) ⇒ assert KN Rao AK ==
Mercury and `ak_divergent == False`. Second fixture where Rāhu IS highest under reversed reckoning ⇒
assert the warning still fires. `pytest` ga_sensitive green.
2.5 — COMMIT: `fix(ga_sensitive): KN Rao Ātmakāraka reckons Rāhu reverse-degree (removes false AK divergence)`
Report the SHA.
GATE: Phases 1 + 2 both committed before Phase 3.

---

## PHASE 3 — Rebuild the Cloud Run job image (carry BOTH commits)
A web deploy does NOT rebuild the job image; a stale image silently runs old orchestrator code.
3.1 — Rebuild + push `brahma-build-pipeline-job` (image
`asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:latest`) from a SHA that contains
BOTH the Phase 1 and Phase 2 commits — ONE image build, so ga_sensitive is later rebuilt once on
correct positions AND correct reckoning. Report the image tag/digest.
3.2 — Trigger a single no-op/already-lit asset on 1c826d5a (action != rebuild, skips cleanly) just to
read the runs-response `job_image_tag`; confirm it matches the pushed digest. If it doesn't match, the
cloud is still on old code — STOP and report.
GATE: job image proven current before any rebuild.

---

## PHASE 4 — Orphan charts: delete (+ recreate) — NATIVE APPROVED
Two orphans `1789595b` and `b35046d8` have graha_position rows but NO `public.charts` row (identical
63.23° Gemini under two build_ids — phantom/test artifacts). Native approved delete + recreate.
4.1 — pre-delete safety (read-only): confirm BOTH chart_ids have ZERO row in `public.charts` AND are
not referenced by `asset_throughput`/`build_runs` for any REAL chart. If either is referenced or
appears in charts, STOP and report.
4.2 — DELETE all rows for these two orphan chart_ids ONLY, across `chart_facts`, `chart_dashas`,
`chart_divisionals`, `ga_condition_composite`, `asset_throughput`. Record per-table deletion counts.
Never touch 482012f1 or 1c826d5a here.
4.3 — RECREATE: recreation needs real birth data, which these orphans lack. ASK THE NATIVE for each
orphan's intended details (name, date, time, place, lat/lng, IANA timezone_id) — do NOT invent them.
On receipt, INSERT proper `public.charts` rows, then build each via `execute_run` like any chart. If
the native declines recreation, STOP after the delete and report (recreation optional).
GATE: orphans deleted (recreation may proceed in parallel with Phase 5 once birth data is supplied).

---

## PHASE 5 — Rebuild 1c826d5a cleanly (sequenced) + WHOLE-CHART proof
SAFE chart; never native 482012f1. Via `execute_run` on the Phase-3 job image.
5.1 — confirm `job_image_tag` carries both fixes (Phase 3.2).
5.2 — rebuild `ga_positions` for 1c826d5a via execute_run.
5.3 — rebuild ALL 14 downstream ga_ assets in DAG order via execute_run (this single pass rebuilds
ga_sensitive ONCE, now on correct positions + correct Rāhu reckoning — do not rebuild it separately).
5.4 — re-verify Gaṇita layer counts (expect a full lit layer again, counts now reflecting Abhinandan's
real chart).
5.5 — WHOLE-CHART verification (acceptance bar — NOT Sun alone): query `chart_facts` graha_position for
1c826d5a and confirm ALL THREE anchors moved OFF the native's values:
  - SUN  → ~318° Aquarius (was 291.96° Capricorn)
  - MOON → OFF Purva Bhadrapada (was the native's 327° PB)
  - LAGNA→ OFF 12.4° Aries (was the native's lagna)
If any of the three still shows the native's value, the rebuild did not take — STOP and report.
5.6 — also confirm the BUG B warning is GONE: no `[GA5] AK divergence` log for 1c826d5a, and the stored
KN Rao AK == Mercury in the 4 affected ayanāṁśas (Mars in Surya-Siddhanta).
5.7 — degenerate-distribution sanity: confirm a couple of downstream assets (e.g. ga_dashas,
ga_strength) didn't collapse to a single repeated value (degenerate-distribution-guard).
GATE: whole-chart proof passes before Phase 6.

---

## PHASE 6 — Tracker truth-check (stale-display class — does the cockpit now show DB reality?)
Independent of the above bugs but proven on this freshly-correct chart. Root cause:
`/api/cockpit/stats` uses `asset_throughput.rows_written` as the primary count and only falls back to
live `count_sql` when rows_written IS NULL; clears reset state but not rows_written → the tracker can
lie. (If the REFRESH fix from BUILD_TRACKER_REFRESH_BRIEF is not yet applied, apply it here: clear nulls
rows_written; stats ignores the rows_written shortcut unless state ∈ {lit,building}.)
6.1 — open the Nirmāṇa tracker for 1c826d5a (Chrome read-tier → use mcp__Claude_in_Chrome__*). For each
lit ga_ asset, assert the displayed count == the live DB count (per-asset count_sql vs the tracker
number). They must match with no manual cache-bust.
6.2 — asset-scope clear ONE asset, then confirm the tracker shows it as NOT BUILT / 0 and the DB shows 0
AND asset_throughput.rows_written IS NULL. Rebuild it; confirm the count returns and matches DB.
6.3 — if display ≠ DB anywhere, that is the stale-display bug — report it distinctly (it is NOT a
clear/build failure).

---

## §7 — Deliverables (one report at the end, per phase)
Per phase: the git diff/SHA (1,2), job image digest + job_image_tag parity (3), orphan pre-delete
safety + per-table deletion counts + recreate status (4), per-asset rebuild result + Gaṇita counts +
SUN/MOON/LAGNA BEFORE/AFTER + AK-warning-gone proof (5), and the tracker-vs-DB match table (6). Any
GATE failure = STOP and report at that phase, do not proceed.

## §8 — Hard guardrails
- Destructive ops ONLY on 1c826d5a and the two named orphans; NEVER native 482012f1.
- Rebuilds via execute_run on the job image carrying both fix commits; confirm job_image_tag.
- Whole-chart verification (Sun+Moon+Lagna) is the acceptance bar, not Sun alone.
- Orphan recreation + the KN Rao citation + the esoteric-AK both-schools choice all require
  native-supplied input — never fabricate birth data, a citation, or that design decision.
- FROZEN orchestrator contract — conforming writers/adapters only.
- Hygiene: `run_abhinandan_sensitive_nakshatra.py` hard-codes the DB password in plaintext; move it to
  an env var before committing/reusing that script (non-blocking).
