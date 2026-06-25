---
artifact: L1_REGEN_B5_OPTIONB_EXECUTION_v1_0.md
canonical_id: L1_REGEN_B5_OPTIONB_EXECUTION
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: L0_L1_SYNC_FREEZE_THEN_GENERATE_BRIEF_v1_0.md
purpose: >
  Phase F decision is made. Fix B5 (the last instance of the NATIVE_BIRTH-contamination class, in the
  ga_sensitive writer) IN the freeze, re-sync the job image, then regenerate per Option B (only what the
  data proves is wrong/stale), behind the FORENSIC 7/7 gate. Stop for the native L2–L5 cascade decision
  after native L1 is verified.
audience: Claude Code (Antigravity)
---

# Native decisions (2026-06-25)
- **B5: FIX NOW**, before any data generation (honors "fix the gaps before generating").
- **Regen depth: OPTION B** — rebuild only what the audit proved wrong/stale. ga_positions + the other
  ga_ assets are CONFIRMED CLEAN (731661e0 live before both builds; native Sun 291.96° Cap correct,
  Abhinandan Sun 317.89° Aqu correct) — do NOT rebuild them.
- **Native cascade (L2–L5): DECIDE AFTER native L1 verified** — keep this session scoped to L0/L1.

The audit established: only 4 charts exist; 2 have data (native 482012f1, Abhinandan 1c826d5a); 2 are
unbuilt (cb73cd3d, acdf0d66 — no action). Only **ga_sensitive** is wrong/stale; its downstream needs a
refresh on Abhinandan. Native ga_sensitive may be CORRUPTED (built on `{}` not NATIVE_BIRTH).

---

## PHASE F.1 — Fix B5 (ga_sensitive writer-level chart_id guard)
File `ga_writers/ga_sensitive_writer.py`, `build_ga_sensitive_for_ayanamsha` (~L2390):
- L2428: `chart_id: str = CANONICAL_CHART_ID` — REMOVE the native default (make chart_id required),
  same footgun fixed in ga_positions.
- L2453-2454: replace the unguarded
  ```
  if birth_params is None:
      birth_params = NATIVE_BIRTH
  ```
  with the 3-way guard (mirrors 731661e0):
  ```
  if birth_params is None:
      if chart_id == CANONICAL_CHART_ID:
          birth_params = NATIVE_BIRTH
      else:
          raise RuntimeError(
              f"Non-native chart {chart_id} has no birth_params — refusing NATIVE_BIRTH fallback "
              f"(would contaminate with the native's chart)."
          )
  ```
- ALSO audit the adapter path: the B1 fix made the native pass `None` (not `{}`) so this guard fires
  correctly. Confirm the orchestrator/adapter passes `None` for the native and a real dict for
  non-native (it should, post-B1) — quote the adapter line.
- Check any OTHER caller of `build_ga_sensitive_for_ayanamsha` that relied on the removed chart_id
  default; fix to pass chart_id explicitly.
- TESTS: non-native chart_id + birth_params=None ⇒ raises; native chart_id + None ⇒ uses NATIVE_BIRTH;
  non-native + real params ⇒ uses them. pytest ga_sensitive green.
- COMMIT: `fix(ga_sensitive): writer-level chart_id guard — refuse NATIVE_BIRTH for non-native (close B5, last NATIVE_BIRTH contamination instance)`

## PHASE F.2 — Re-sync the job image (carry B5)
B5 changes the code that runs in the Cloud Run job. Merge to main, FULL GREEN CI, then rebuild + push
the `brahma-build-pipeline-job` image from the new main HEAD. PROVE the deployed job image commit ==
new main HEAD (gcloud run jobs describe … template.template.containers[0].image → digest → commit ==
HEAD). Record the new HEAD SHA + image digest. Update build_runs.job_image_tag population if not yet
added. GATE: no generation until the job image carries B5 and parity is re-proven.

---

## PHASE G — FORENSIC 7/7 gate on the native (snapshot FIRST)
Before touching native data: snapshot the native's current chart_facts (so a regression is reversible).
The native's ga_positions is CLEAN (confirmed) and is NOT being rebuilt — but ga_sensitive consumes
positions, so re-affirm the 7 anchors hold on the data ga_sensitive will read:
Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries (all 5 ayanāṁśas), Tithi=Shukla Tritiya,
Vara=Ravivara, Yoga=Shiva, Karana=Garaja. 7/7 PASS required before rebuilding native ga_sensitive.
HALT on any anchor failure.

---

## PHASE H — Regenerate per OPTION B (via execute_run, on the B5 job image)
Do NOT rebuild ga_positions or any confirmed-clean ga_ asset. Only:

H.1 — NATIVE 482012f1 ga_sensitive: wipe its ga_sensitive rows (delete-then-insert per build) and
  rebuild via execute_run (5 ayanāṁśa sub-steps). This fixes B1 (was built on `{}` — potential
  corruption), B2 (adds KN Rao esoteric-AK school), and includes cf38e029 (Rāhu reverse-degree).
  VERIFY: 8,610-ish rows; BOTH schools present (parashari_rahu_excluded + kn_rao_rahu_included) for
  karaka + esoteric rows; KN Rao AK correctly ranked (Rāhu reversed); FORENSIC-consistent.

H.2 — ABHINANDAN 1c826d5a ga_sensitive: rebuild via execute_run. Fixes B2 (KN Rao school). VERIFY both
  schools present; KN Rao AK == Mercury (per the earlier reckoning proof), no [GA5] false-divergence
  warning.

H.3 — ABHINANDAN stale downstream sweep: rebuild the 7 stale assets (ga_condition, ga_medical,
  ga_sade_sati, ga_structural, ga_tajaka, ga_vastu, ga_yoga) via execute_run in DAG order — they were
  built on correct positions but flagged stale after the ga_sensitive refresh. VERIFY each returns to
  lit with stable counts (no accretion).

H.4 — Degenerate-distribution sanity on a couple of rebuilt assets (no single-value collapse).

H.5 — STOP. Do NOT cascade native L2–L5 yet. Report native L1 verified state + the current native
  L2(bo_)/L3(ka_)/L4(ph_)/L5(mi_) staleness/error states so the native decides the cascade scope as a
  separate call.

---

## §X — Deliverables + guardrails
DELIVER: B5 diff + tests + commit (F.1); new main HEAD + green CI + job-image==HEAD parity (F.2);
native snapshot + FORENSIC 7/7 result (G); per-asset rebuild verification with both-schools proof for
ga_sensitive on both charts + Abhinandan downstream counts (H.1–H.4); and the native L2–L5 state report
for the cascade decision (H.5).
GUARDRAILS: B5 fixed + job image re-synced BEFORE any generation. Do NOT rebuild confirmed-clean assets
(ga_positions etc.) — the data proves them correct; rebuilding them is the wasted compute we're
avoiding. Native 482012f1 only behind FORENSIC 7/7 + snapshot. cb73cd3d + acdf0d66 untouched (unbuilt).
All rebuilds via execute_run on the B5 job image. STOP at H.5 for the cascade decision.

## §Y — Note on the build metadata anomaly (non-blocking)
Abhinandan ga_positions has `built_against_upstream_hash = e3b0c44298fc1c14` (SHA-256 of empty bytes) —
a build-metadata recording bug, NOT a data bug (positions verified correct). File it as a separate
hygiene item (the upstream-hash recorder is writing the empty-input hash); do not let it block this
regen.
