---
artifact: L0_L1_SYNC_FREEZE_THEN_GENERATE_BRIEF_v1_0.md
canonical_id: L0_L1_SYNC_FREEZE_THEN_GENERATE_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
severity: HIGH — governs the clean L0+L1 data regeneration
purpose: >
  Native-directed workflow: prove that EVERY L0 (Brahmagyan) + L1 (Gaṇita) correctness fix is
  committed → merged → deployed to BOTH the web app and the Cloud Run job image, so localhost and prod
  are in complete sync, BEFORE generating any fresh L0/L1 data. The currently-stale data (from an
  up-voted build on possibly-mixed code) is to be DISCARDED, not salvaged. Data generation is GATED
  behind a proven prod==main==all-fixes-in state. The exact wipe+regenerate baseline is decided AFTER
  the audit (Phase F), not before.
audience: Claude Code (Antigravity)
---

# L0+L1 — Sync, Freeze, THEN Generate

## §0 — Native intent (the governing principle)
"Identify the gaps, fix the gaps, push everything to prod so localhost and prod are in complete sync,
THEN generate the data." No incremental resume of half-built runs. The stale data is wrong by
definition — abandon it. Only after prod is provably identical to main AND main contains every L0/L1
fix do we regenerate clean L0+L1. This brief is an AUDIT-AND-SYNC gate; data generation is the LAST
step and is gated.

CONTEXT (changes that must ALL be accounted for): natal_engine → PyJHora swap; the contaminated ga_
asset fixes; ga_positions chart-independence / native-leakage fix (no native details bleeding into
non-native charts); ga_sensitive KN-Rao AK reckoning; ga_nakshatra dict_row; ga_sensitive
ValueError→warning; any L0 (Brahmagyan) equivalents.

ENVIRONMENT CAVEAT (important): the Cowork mount shows local `main` AHEAD of `origin/main` by ≥4
commits (incl. the Nirmāṇa access fix c026167b) AND an untracked working tree. Prior execution reports
referenced commits (731661e0 ga_positions, cf38e029 ga_sensitive) NOT visible in the Cowork mount —
meaning work happened in a DIFFERENT clone/worktree (Antigravity). So: run this audit in the
EXECUTOR's authoritative repo; treat any single vantage point as possibly-stale; reconcile ALL clones/
worktrees. "Where is each fix committed?" is the first thing to establish, not assume.

## PHASE A — INVENTORY: enumerate every L0/L1 fix and where it currently lives
Build a table: each fix → its commit SHA(s) → which branch → merged to main? → in origin/main? Cover:
1. PyJHora swap (natal_engine retired, pyjhora_adapter live) — confirm the merged PR (#332 per memory).
2. ga_positions chart-independence fix (adapter passes birth_params; writer refuses NATIVE_BIRTH for
   non-native; chart_id default removed) — the reported SHA was 731661e0.
3. ga_sensitive KN-Rao AK reckoning (Rāhu reverse-degree) — reported cf38e029.
4. ga_sensitive ValueError→warning (AK-divergence non-fatal).
5. ga_nakshatra dict_row KeyError fix.
6. esoteric-AK both-schools (if that work landed — Phase 3 of the remaining-threads brief).
7. Any other of the 16 ga_ assets touched during the contamination work.
8. L0 (Brahmagyan) equivalents — see Phase B (native-leakage sweep) for what to look for.
For EACH: is it on origin/main? If only on a feature branch or a stray worktree, that's a GAP.

## PHASE B — NATIVE-LEAKAGE SWEEP (the chart-independence guarantee, L0 + L1 + shared compute)
The ga_positions bug was `bp = birth_params or NATIVE_BIRTH` (silent native fallback) + a native-
defaulting chart_id. AUDIT every writer/compute path for the SAME class so no native detail can bleed
into a non-native chart. Grep targets already found in the tree (audit each, fix any that can run for a
non-native chart): `ga_writers/*`, `pipeline/orchestrator/writers/ga_positions.py`,
`brahmagyan/ganita/engine.py`, `pyjhora_adapter/compute.py`, `pipeline/writers/panchanga_writer.py`,
`brahmagyan/l0_ephemeris.py`, `ka_*` writers, `ph_rectification`. For each: does it have a hard-coded
NATIVE_BIRTH / 1984-02-05 / CANONICAL_CHART_ID default that a non-native build could hit? L0 ephemeris
is chart-INDEPENDENT (date-range, not birth) so it's likely fine — CONFIRM that, don't assume. Any
writer that can build a non-native chart from native defaults = a GAP to fix like ga_positions
(require birth_params; refuse native fallback for non-native; loud halt). Add/confirm a regression test
per fix (non-native chart_id with different birth ⇒ different output than native).

## PHASE C — CLOSE THE GAPS
For every GAP from A and B: finish the fix, add its regression test, commit. Also resolve the
working-tree strays seen in the Cowork mount: `run_abhinandan_sensitive_nakshatra.py` (hardcoded DB
password — move secret to env or do NOT commit; it's a one-off, prefer scripts/ or delete),
`cleanup_orphaned_firebase_users.ts` (commit under scripts/ if keeping), and any other untracked code.
The many `?? 00_ARCHITECTURE/*.md` briefs are docs — commit the ones worth keeping. Goal at end of C:
a clean `git status` and every L0/L1 fix on a branch ready to merge.

## PHASE D — MERGE TO MAIN + GREEN CI
Merge all fix branches/worktrees into ONE main HEAD. Run FULL CI on that HEAD — it must be GREEN
(all jobs). Record the main HEAD SHA. No data generation until CI is green on the SHA that contains
every Phase-A/B fix. (Per native: "full green CI + both deploys" is the sync bar.)

## PHASE E — DEPLOY BOTH PLANES + PROVE PARITY (localhost == prod)
The web app and the Cloud Run JOB image are SEPARATE deploys — both must be at main HEAD.
1. WEB: confirm the deployed web app is at main HEAD (Cloud Run web revision → commit).
2. JOB IMAGE: rebuild + push `brahma-build-pipeline-job`
   (`asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline`) from main HEAD. Read the
   deployed image: `gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1
   --project=madhav-astrology --format='value(template.template.containers[0].image)'`; resolve its
   digest → commit; assert that commit == main HEAD (so EVERY Phase-A/B fix is an ancestor).
3. PARITY VERDICT: web commit == job-image commit == main HEAD == contains-all-fixes. Only a triple
   match passes. ALSO add the process improvement: a `job_image_tag` column on `build_runs` populated
   from getJobImageTag() at run creation, so each future run records its image commit (audit without
   gcloud).
GATE: do not proceed to F until parity is PROVEN.

## PHASE F — DECIDE THE CLEAN-DATA BASELINE (report first, native decides)
Only now — with prod proven synced — report and let the native choose the wipe+regenerate scope:
- Non-native charts (1c826d5a + any others with stale L0/L1): full discard + regenerate on the synced
  image. (Default expectation, but confirm the chart list.)
- Native 482012f1: regenerate ONLY behind a passing FORENSIC 7/7 gate (Phase G), snapshot-before, since
  it is ground truth. The PyJHora swap means its anchors are UNPROVEN on a fresh rebuild (open trust
  gate) — do not blindly rebuild the native.
- L0 (Brahmagyan): is L0 regenerated too, or is it chart-independent reference data that only needs
  regen if a Phase-B fix touched an L0 writer? Report what actually changed in L0 and recommend.
Present the baseline options + row-count expectations; the native picks before any wipe.

## PHASE G — FORENSIC 7/7 GATE (before trusting ANY regenerated native data)
On a fresh native build under the synced PyJHora image, assert the 7 birth anchors:
Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries (all 5 ayanāṁśas), Tithi=Shukla Tritiya,
Vara=Ravivara, Yoga=Shiva, Karana=Garaja. 7/7 PASS is REQUIRED before the native's regenerated L0/L1 is
trusted. A FORENSIC failure HALTS — the PyJHora swap would have regressed the foundation.

## PHASE H — GENERATE CLEAN DATA (only after A–G pass + native picks baseline in F)
Per the F decision, on the synced image via execute_run: wipe the agreed stale data, regenerate L0/L1
for the agreed charts in DAG order. Verify per-chart whole-chart correctness (e.g. 1c826d5a Sun ~318°
Aquarius, Moon Gemini/Ardra, Lagna Aries — its OWN chart) and the native FORENSIC 7/7. Degenerate-
distribution sanity on a few assets. Record the image commit each run ran on (the new build_runs.
job_image_tag column).

## §9 — Deliverables + guardrails
DELIVER per phase: the fix-inventory table with merge/origin status (A); the native-leakage audit +
fixes (B); clean git status (C); main HEAD SHA + green CI (D); the web==job==main parity proof (E);
the baseline-decision report (F); FORENSIC 7/7 result (G); regenerated-data verification (H).
GUARDRAILS: NO data generation until E parity is proven AND (for the native) G passes. Reconcile ALL
clones/worktrees — do not trust a single vantage. Native 482012f1 regenerated only behind FORENSIC +
snapshot. Never fabricate birth data or skip a gate. Each phase GATE failure = STOP and report.

## §10 — Why this order (the point)
Generating data before prod==main is the exact trap that produced the stale up-voted build: localhost
triggered, but the cloud job ran whatever image it had. Freezing + proving the sync first means the
clean data is generated once, correctly, on code we KNOW is live — no second wasted pass.
