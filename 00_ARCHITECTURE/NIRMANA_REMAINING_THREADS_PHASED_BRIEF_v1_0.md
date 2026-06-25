---
artifact: NIRMANA_REMAINING_THREADS_PHASED_BRIEF_v1_0.md
canonical_id: NIRMANA_REMAINING_THREADS_PHASED_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Single self-contained, phased Claude Code execution brief for the REMAINING open threads after the
  Gaṇita integrity fix closed (GANITA_INTEGRITY_FIX_PHASED_BRIEF — DONE, all 6 phases DB-verified). In
  order: (1) tracker Clear/Build/Rebuild proofs on the now-correct 1c826d5a; (2) Nirmāṇa + Nava-Jātaka
  access investigation and decision; (3) esoteric-AK both-schools cleanup; (4) orphan recreation
  (waits for native-supplied birth data).
audience: Claude Code (Antigravity)
---

# Nirmāṇa — remaining threads, phased

## §0 — Context + rules (read once)
The Gaṇita integrity fix is COMPLETE and verified: chart **Abhinandan Mohanty
`1c826d5a-41cb-4450-b4dc-59d440e5f75a`** now holds its OWN correct positions (Sun ~318° Aquarius, Moon
~73° Gemini, Lagna ~23.5° Aries), the false AK divergence is gone, and the Cloud Run job image
`c47d67531dc5a31c56a7e535749277938df515ab` carries both fixes. This brief is the leftover hardening +
two product questions.

Rules (unchanged): destructive ops ONLY on `1c826d5a`, NEVER on native
`482012f1-710e-4a25-994a-93821f5871aa`. Data plane = prod via Cloud SQL proxy `:5433`. Builds run on
the Cloud Run job (confirm `job_image_tag`); rebuilds via `execute_run`. Chrome is read-tier → use
`mcp__Claude_in_Chrome__*` for any UI driving. FROZEN orchestrator contract — conforming
writers/adapters only. Truth bar: tracker display == DB reality; full success or explicit failure list,
never silent partial success. Each phase ends in a GATE — on failure STOP and report at that phase.

---

## PHASE 1 — Tracker operation proofs on the corrected chart (Clear / Build / Rebuild)
Now that 1c826d5a is correct, prove the three tracker operations DB-truthfully on it. All via the
cockpit UI (Chrome MCP) with DB reads (:5433) as the arbiter.

1A — CLEAR completeness + no over-delete:
  Pick 3 ga_ assets covering all resolution paths: ga_condition (EXPLICIT_CLEAR_OPS), a chart_facts
  category asset (derived-from-count_sql), ga_dashas (dedicated table). For each: PRE DB count → UI
  asset-scope clear → capture /api/cockpit/clear/execute response (failed_tables MUST be empty) → POST
  DB count == 0 for that asset ONLY. Snapshot `SELECT fact_category, count(*) FROM chart_facts WHERE
  chart_id='1c826d5a-...' GROUP BY 1` before/after the chart_facts clear: ONLY that asset's category
  drops; every L0/other category byte-identical (over-delete guard). Then a LAYER-scope ganita clear:
  every ga_ category → 0, zero failed_tables; confirm L0/brahmagyan categories untouched.

1B — BUILD lights the whole layer honestly:
  Starting from the layer-cleared state in 1A, press the Gaṇita LAYER Build in the UI. Capture
  /api/cockpit/runs response (run_id, plan, job_image_tag — confirm it is the c47d6753 image). Watch to
  completion; every in-scope ga_ data asset → lit with DB rows > 0; tracker count == DB count per asset.
  HONESTY CHECK: if any asset errors, the layer header shows a non-zero error badge and is NOT painted
  fully green despite build_runs.state='completed'. ga_prashna correctly shows 0 (no horary) — that is
  lit-with-zero, not an error.

1C — REBUILD: no accretion:
  Pick ga_dashas (deterministic, ~538k rows — the asset most likely to expose accretion). PRE DB count
  = N. UI asset-scope Rebuild. Confirm the runs plan includes the target (skip-if-lit bypassed) + its
  transitive downstream. Watch to completion. POST DB count == N EXACTLY (delete-then-insert; not 2N).
  Confirm asset_throughput last_built_at advanced, state='lit'. Confirm the target's downstream went
  'stale' then rebuilt to 'lit' in DAG order. Any count drift = a writer idempotency bug → name the
  asset + writer module and STOP.

DELIVER (Phase 1): the 3-asset clear table + category over-delete snapshot; the layer-build runs
response + per-asset lit proof + honesty-check result; the rebuild N==N proof + downstream-stale list.
GATE: all three operations DB-proven before Phase 2.

---

## PHASE 2 — Nirmāṇa + Nava-Jātaka access (investigate, then decide)
OBSERVED: logged in as a NON-super-admin chart owner (Abhinandan), clicking Nirmāṇa redirects to the
Consult view instead of the build tracker, and the "Nava Jātaka" (new chart) button is absent. Both
work as super_admin. This MAY be intended (build = super-admin-only) or a bug (owner should reach it).

2A — DIAGNOSE (read-only):
  - Code is already mapped: `platform/src/app/clients/[id]/nirmana/page.tsx` redirects when
    `!access.canBuild`; `lib/auth/chart-page-guard.ts` sets `canBuild = (permission === 'all')`;
    `lib/auth/authorizeChartAccess.ts` grants 'all' to super_admin OR `charts.owner_id == uid`, else
    'view'/'deny'. Dashboard `dashboard/page.tsx` gates the Nava-Jātaka button on
    `role === 'super_admin'`.
  - The deciding DATA fact (prod :5433): `SELECT id, owner_id, client_id, subject_name FROM charts
    WHERE id='1c826d5a-...';` AND the profile of the logged-in non-super-admin:
    `SELECT id, role FROM profiles WHERE id=<that uid>;`
  - Classify: if owner_id == the non-admin's uid → the guard SHOULD grant 'all' and the redirect is a
    BUG (e.g. owner_id NULL or set to the super-admin who created the chart). If owner_id is the
    super-admin / NULL → the redirect is correct-by-design (non-owner viewer), and the "fix" is a
    product decision, not a code bug.

2B — DECIDE + ACT (this is the product call — implement the chosen branch only):
  Present the diagnosis to the native with the two coherent end-states and let them pick:
    (i) BUILD IS OWNER+ADMIN: a non-admin who OWNS a chart should reach its build tracker. Then: ensure
        owner_id is correctly populated on chart creation (data fix for existing rows + a creation-path
        fix so new charts set owner_id = creator). Nava-Jātaka button: decide separately whether owners
        may create charts (if yes, relax the dashboard `role==='super_admin'` gate to also allow chart
        creation for the intended role; if no, leave it admin-only).
    (ii) BUILD IS ADMIN-ONLY: the current behavior is correct. Then the only change is UX: the Nirmāṇa
        link/redirect should not look broken — e.g. hide/disable the Nirmāṇa affordance for non-owners
        or show a "view-only — build restricted" state instead of a silent bounce to Consult.
  Do NOT implement both. Implement the native's choice with a test (guard unit test for the access
  matrix: super_admin→all, owner→all, grantee→view, other→deny; and the UI affordance reflecting it).

DELIVER (Phase 2): the owner_id/role data + classification (bug vs intended), the native's decision,
and the implemented change + test. GATE: native must rule before any code change here.

---

## PHASE 3 — Esoteric-AK both-schools cleanup (native decided: BOTH schools)
File `ga_writers/ga_sensitive_writer.py`. `_build_karaka_rows` (~L1025-1029) already emits both schools
via the loop `[("parashari_rahu_excluded", parashari_sorted[:8], …), ("kn_rao_rahu_included",
knrao_sorted[:8], …)]` and (post-fix) ranks Rāhu by reversed degree in the KN Rao set.
`_build_esoteric_rows` (~L860-899) currently derives Brahma/Vishnu/Shiva from a Parāśarī-only AK
(`max(grahas_7, key=…)`, Rāhu excluded).

DO:
1. Refactor `_build_esoteric_rows` to emit the esoteric points for BOTH schools — Parāśarī AK (7-graha,
   Rāhu excluded) AND KN Rao AK (8-graha, Rāhu ranked by the reversed `30 − (long % 30)` key, identical
   to the corrected `_build_karaka_rows`). Tag each emitted row with the school
   (`parashari_rahu_excluded` / `kn_rao_rahu_included`), mirroring the karaka rows so downstream can
   distinguish them. Do NOT change the Parāśarī derivation's values — only ADD the KN Rao variant.
   Reuse the same AK-selection helper the karaka function uses (factor it out if needed) so the two
   functions cannot drift again.
2. Update the docstring (it says "Simplified derivation from AK position") to note dual-school output.
3. Tests: assert _build_esoteric_rows now emits both schools; for the 1c826d5a fixture, the KN Rao
   esoteric points derive from Mercury (the corrected KN Rao AK), the Parāśarī ones unchanged. pytest
   ga_sensitive green.
4. COMMIT: `feat(ga_sensitive): esoteric points (Brahma/Vishnu/Shiva) emit both Parāśarī + KN Rao AK schools`
5. After Phases 1–3 commits land, rebuild the job image if needed (confirm job_image_tag), then rebuild
   ga_sensitive (and its esoteric-consuming downstream) for 1c826d5a via execute_run; verify both-school
   esoteric rows now exist for this chart.
GATE: dual-school esoteric rows DB-confirmed for 1c826d5a.

---

## PHASE 4 — Orphan recreation (WAITS for native birth data — do not fabricate)
The two orphan charts `1789595b` and `b35046d8` were already DELETED (1,060 rows). Recreation needs
real birth data which only the native can supply.
DO:
1. STOP and request from the native, for EACH orphan to recreate: name/subject, birth_date, birth_time,
   birth_place, birth_lat, birth_lng, IANA timezone_id. Do NOT invent any of these.
2. On receipt: INSERT proper `public.charts` rows (new uuids), then build each via execute_run like any
   chart (the ga_positions fix means they build their OWN correct positions). Verify each new chart's
   Sun matches its supplied birth date (sanity vs contamination).
3. If the native declines recreation (they were pure test artifacts), record "orphans deleted, not
   recreated — closed" and skip.
GATE: do not create any chart row without native-supplied birth data.

---

## §5 — Deliverables + guardrails
One report per phase (the tables/proofs named in each). Any GATE failure → STOP and report at that
phase. Guardrails: destructive ops on 1c826d5a + named orphans ONLY, never native 482012f1; rebuilds
via execute_run on the job image carrying all fix commits (confirm job_image_tag); Chrome MCP for UI;
FROZEN orchestrator contract; never fabricate birth data, a citation, or a product decision that is the
native's to make (Phase 2 access end-state, Phase 4 birth data).
