# WS-0B Hot-Patch (Option A — full AIOps surface delete) — Claude Code Prompt

> **Paste this entire block into your Claude Code chat inside Google Antigravity IDE.**
> Branch: `feature/ws0b-code-cluster-purge` (PR #206 — already open, do NOT open a new PR)
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`
> Supersedes the earlier 3-commit hot-patch — Step 1's reverse-citation gate found the dead surface
> reached beyond prober.ts into three live admin route files. Native decision: Option A — delete the
> full AIOps LLM-health observability surface; rebuild under Mīmāṃsā/L5 later.

---

You are Claude Code in Google Antigravity IDE. The Madhav repo is open at `/Users/Dev/Vibe-Coding/Apps/Madhav`. PR #206 (`feature/ws0b-code-cluster-purge → main`) is open. Four small commits land on the SAME branch before merge.

**Context.** The targeted re-grep + reverse-citation gate surfaced that `llm_model_health` is consumed by `prober.ts` (writer) PLUS three admin route files (`/api/admin/aiops/health/route.ts`, `/health/summary/route.ts`, `/state/route.ts`) PLUS likely UI panels. The table was dropped in WS-0; the surface has been silently broken for hours with no observable impact. **Native call: Option A** — delete the full AIOps health surface; defer real LLM observability to a future Mīmāṃsā/L5 work item.

Four commits, one branch. PR-to-main remains human-gated.

## Step 0 — Confirm branch + pull latest

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout feature/ws0b-code-cluster-purge
git pull origin feature/ws0b-code-cluster-purge
git log --oneline -5
```

---

## Step 1 — Full reverse-citation gate on the AIOps health surface

Before deleting, enumerate the entire blast radius so nothing is missed and any deeper hook (scheduler, cron, queue worker) is caught.

```bash
# Already-known consumers (the targeted re-grep already found these):
#   platform/src/lib/aiops/health/prober.ts
#   platform/src/lib/aiops/health/__tests__/prober.test.ts
#   platform/src/app/api/admin/aiops/health/route.ts
#   platform/src/app/api/admin/aiops/health/summary/route.ts
#   platform/src/app/api/admin/aiops/state/route.ts

# Find UI consumers — pages, components, hooks that fetch the AIOps health endpoints
grep -rEln "/api/admin/aiops/(health|state)" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0b_hp_ui_consumers.txt

# Find any importer of the prober beyond the test
grep -rEln "aiops/health/prober" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0b_hp_prober_importers.txt

# Find anything else that references llm_model_health (writer or reader, code or config)
grep -rEn "llm_model_health|LlmModelHealthRow" \
  platform/src platform/scripts platform-mcp/src \
  --include='*.ts' --include='*.tsx' --include='*.py' --include='*.yaml' --include='*.yml' --include='*.sql' 2>/dev/null \
  | grep -v "^platform/supabase/migrations/" \
  | tee /tmp/ws0b_hp_llm_model_health_all.txt

# CRITICAL — find any Cloud Scheduler / cron / queue worker that triggers the prober
grep -rEn "(probeModel|probe-model|aiops.*health.*probe|aiops/health/prober)" \
  platform/scripts .github \
  --include='*.ts' --include='*.py' --include='*.yaml' --include='*.yml' --include='*.sh' 2>/dev/null \
  | tee /tmp/ws0b_hp_scheduler_hooks.txt

# Find Brahma-side admin pages that might link/route to /admin/aiops
grep -rEn "/admin/aiops" platform/src \
  --include='*.ts' --include='*.tsx' --include='*.md' 2>/dev/null \
  | tee /tmp/ws0b_hp_admin_links.txt
```

**Read each output file. Build a complete delete list before any rm:**

- All UI files in `/tmp/ws0b_hp_ui_consumers.txt` → mark for delete (or surgical edit if the file mixes AIOps with non-AIOps code).
- Every prober importer in `/tmp/ws0b_hp_prober_importers.txt` (beyond the known test) → mark for delete.
- Every code/config reference to `llm_model_health` in `/tmp/ws0b_hp_llm_model_health_all.txt` → mark.
- The 5 known route/test/lib files → mark.

**HARD STOP** if `/tmp/ws0b_hp_scheduler_hooks.txt` is non-empty — a Cloud Scheduler / cron / queue trigger is a deeper integration than file deletes resolve; report each hook to native (file + line + what it triggers). Do not proceed to Step 2 until the scheduler hook has a disposition.

**HARD STOP** if `/tmp/ws0b_hp_admin_links.txt` shows a Brahma-active page (cockpit, dashboard, Layer Tower, Asset Inspector) linking to `/admin/aiops` — that means the AIOps surface is referenced by Brahma surfaces, not just standalone. Report links to native.

If both stops are clear, write the consolidated delete list to `/tmp/ws0b_hp_delete_list.txt` and proceed.

---

## Step 2 — Delete the AIOps health surface (Commit 1)

```bash
# Core surface
git rm platform/src/lib/aiops/health/prober.ts
git rm platform/src/lib/aiops/health/__tests__/prober.test.ts
git rm platform/src/app/api/admin/aiops/health/route.ts
git rm platform/src/app/api/admin/aiops/health/summary/route.ts
git rm platform/src/app/api/admin/aiops/state/route.ts

# Clean up the now-empty health/summary route directory (route.ts deleted; if no other files, the dir goes)
if [ -d platform/src/app/api/admin/aiops/health/summary ] \
   && [ -z "$(find platform/src/app/api/admin/aiops/health/summary -type f)" ]; then
  rmdir platform/src/app/api/admin/aiops/health/summary
fi
if [ -d platform/src/app/api/admin/aiops/health ] \
   && [ -z "$(find platform/src/app/api/admin/aiops/health -type f)" ]; then
  rmdir platform/src/app/api/admin/aiops/health
fi
if [ -d platform/src/lib/aiops/health/__tests__ ] \
   && [ -z "$(ls -A platform/src/lib/aiops/health/__tests__)" ]; then
  rmdir platform/src/lib/aiops/health/__tests__
fi
if [ -d platform/src/lib/aiops/health ] \
   && [ -z "$(ls -A platform/src/lib/aiops/health)" ]; then
  rmdir platform/src/lib/aiops/health
fi

# UI consumers (delete each file from /tmp/ws0b_hp_ui_consumers.txt that exclusively
# served the AIOps health surface — admin pages, panels, hooks)
# For each file, look at it: if AIOps health is its sole purpose → git rm; if mixed → Edit out the AIOps block.
while IFS= read -r ui_file; do
  echo "Review: $ui_file"
  # Manually decide per file. Common patterns:
  #   - platform/src/app/admin/aiops/page.tsx → delete the whole admin/aiops route dir
  #   - components/admin/AiopsHealthPanel.tsx → git rm
  #   - hooks/useAiopsHealth.ts → git rm + remove every importer
done < /tmp/ws0b_hp_ui_consumers.txt

# Delete the LlmModelHealthRow type — search for it first
grep -rEln "LlmModelHealthRow|type LlmModelHealth" platform/src --include='*.ts' --include='*.tsx' 2>/dev/null
# For each hit, either git rm the file (if it's a type-only module about model health) or
# Edit it to remove only the LlmModelHealth type definitions.

# Delete any /admin/aiops navigation link in nav components
grep -rEln "/admin/aiops" platform/src --include='*.ts' --include='*.tsx' 2>/dev/null
# Edit each to remove the nav entry (do not git rm a whole nav file for one link)

# Verify zero llm_model_health and zero LlmModelHealthRow remain in the source tree
grep -rEn "llm_model_health|LlmModelHealthRow|aiops/health/prober" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null
# Expected: zero lines

# Local typecheck — catch cascading errors from the removals
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head -20 && cd ..
```

If typecheck surfaces new errors caused by these removals (orphaned barrel exports, dead imports in admin layout files), include the fix in this commit.

**Commit 1:**
```bash
git add -A
git commit -m "chore(ws0b): drop AIOps LLM-health admin surface (Option A)

WS-0 dropped llm_model_health; WS-0B reverse-citation gate found the
surface reached beyond prober.ts into three live admin routes
(/api/admin/aiops/health, /health/summary, /state) plus UI panels.
Table was missing for hours post-WS-0 with no observable failure —
confirming the surface was not on any live path.

Native decision: Option A. Defer LLM-quality observability to a
Mīmāṃsā/L5 work item (see BRAHMA_DEFERRED_FEATURES.md). Cleanly
remove the surface now rather than carry dead admin code against a
dropped table.

Files removed:
- platform/src/lib/aiops/health/prober.ts + test
- platform/src/app/api/admin/aiops/health/route.ts
- platform/src/app/api/admin/aiops/health/summary/route.ts
- platform/src/app/api/admin/aiops/state/route.ts
- UI consumers (admin/aiops pages, AiopsHealthPanel, useAiopsHealth)
- LlmModelHealthRow type + nav entries

Refs PR #206"
```

---

## Step 3 — Fix drift_detector phantom-reference to `rag_router.py` (Commit 2)

```bash
# Locate drift_detector and how it references rag_router.py
grep -rEn "rag_router" platform/scripts/governance platform/python-sidecar \
  --include='*.py' 2>/dev/null

# Look for known_residuals / allowlist config
find . -name "drift_detector*" -o -name "*known_residuals*" -o -name "*drift_config*" 2>/dev/null \
  | grep -v node_modules | grep -v .git
```

**Decision rule (pick the smaller diff):**
- A known_residuals or allowlist config file → add one entry excluding `rag_router.py`.
- drift_detector hardcodes a list of expected modules → remove `rag_router.py` from that list.
- drift_detector scans a stale manifest → update the manifest to remove `rag_router.py`.

Do not refactor drift_detector itself.

```bash
# Confirm quiet after fix
python platform/scripts/governance/drift_detector.py 2>&1 | grep -iE "rag_router|phantom" | head
# Expected: empty
```

**Commit 2:**
```bash
git add -A
git commit -m "fix(drift): drop phantom reference to deleted rag_router.py

drift_detector flagged rag_router.py as expected-but-missing; the file
was deleted in WS-0 Surface 2. Updated the known_residuals / module
list to reflect the deletion.

Unblocks AC-8 governance-gates CI step. Refs PR #206"
```

---

## Step 4 — Fix `retry_wrapper` TypeScript error (Commit 3)

```bash
# Locate retry_wrapper and the error
grep -rEn "retry_wrapper" platform/src --include='*.ts' --include='*.tsx' 2>/dev/null

cd platform && npm run typecheck 2>&1 | grep -B 1 -A 3 "retry_wrapper" && cd ..
```

**Most likely cause:** `retry_wrapper` imports or types something deleted in WS-0/WS-0B/Step 2. The fix is one of:
- Remove a dead import if the type isn't used in `retry_wrapper`'s signature.
- Inline the type if it was a small helper from a deleted module.
- Delete `retry_wrapper` if it was only used by deleted code.

**Reverse-citation gate before deleting `retry_wrapper`:**
```bash
grep -rEln "from ['\"][^'\"]*retry_wrapper" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null
# Zero importers AND `retry_wrapper` only wrapped deleted code → git rm
# One or more LIVE importers → patch the import, don't delete the wrapper
```

```bash
cd platform && npm run typecheck 2>&1 | grep "retry_wrapper" && cd ..
# Expected: empty
```

**Commit 3:**
```bash
git add -A
git commit -m "fix(types): resolve retry_wrapper TS error from deleted-module import

retry_wrapper imported a type from a module deleted in WS-0/WS-0B/AIOps
surface removal. [Describe what you found + how you fixed it.]

Unblocks AC-8 typecheck CI step. Refs PR #206"
```

---

## Step 5 — Record the AIOps deferral (Commit 4)

Create `00_ARCHITECTURE/BRAHMA_DEFERRED_FEATURES.md` (if absent) or append to it (if exists).

If absent, write this file:

```bash
cat > 00_ARCHITECTURE/BRAHMA_DEFERRED_FEATURES.md <<'EOF'
---
artifact: BRAHMA_DEFERRED_FEATURES.md
canonical_id: BRAHMA_DEFERRED_FEATURES
version: 1.0
status: LIVING (rolling list — features intentionally deferred during Brahma cleanup; rebuild plan per item)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-04
purpose: >
  Record of features that existed in the pre-Brahma codebase, were intentionally removed during
  Brahma cleanup (WS-0 / WS-0B / hot-patches), and are scheduled for proper rebuild under a
  Brahma-native layer rather than restoration of the legacy implementation. Distinguishes
  "deferred" from "lost" — the surface is gone, the requirement is not.
---

# Brahma — Deferred Features

## 1. AIOps LLM-quality observability (model health probes + admin surface)

**Removed:** 2026-06-04, WS-0B hot-patch, Option A.

**What it was.** Per-model health probing (`platform/src/lib/aiops/health/prober.ts`) writing latency,
error, last-probe timestamps to `llm_model_health`; three admin routes reading the table
(`/api/admin/aiops/health`, `/health/summary`, `/state`); UI panels surfacing per-stack health
(green/red/amber/dim).

**Why removed.** WS-0 dropped `llm_model_health` as part of the AIOps-stack purge. The admin surface
was silently broken for hours with no observable failure — confirming it wasn't on a daily-driven
path. Restoring the legacy table would re-introduce exactly the dead-code-on-living-table pattern
WS-0/WS-0B were cleaning up. Surface deleted in full instead of stubbed.

**Where it goes.** When Mīmāṃsā/L5 (Learning) is built, the LLM-quality calibration concern is a
natural fit: track per-model behavior against outcomes the same way the corpus-level learning
multiplier tracks rules/signals/techniques. The rebuild lives under `mimamsa_*` tables + Brahma-
native tools, not a port of the legacy admin surface.

**Rebuild trigger.** When Mīmāṃsā work begins (per BRAHMA_COMPLETION_PLAN WS-3 + downstream L5
implementation), spec the LLM-health observability as a Mīmāṃsā sub-asset. Do not rebuild it as a
standalone admin tool.
EOF
```

If file already exists, append the `## 1.` section above as the next numbered section.

**Commit 4:**
```bash
git add -A
git commit -m "docs(brahma): record AIOps observability as deferred under Mīmāṃsā/L5

New artifact 00_ARCHITECTURE/BRAHMA_DEFERRED_FEATURES.md tracks features
intentionally removed during Brahma cleanup, with a rebuild plan per item.
First entry: AIOps LLM-health observability (deleted in this PR; rebuild
target Mīmāṃsā/L5).

Refs PR #206"
```

---

## Step 6 — Full re-verification (the WS-0B AC suite)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# LEGACY_TABLES alternation — note: builds/build_steps/build_events/reports removed (live
# Brahma names); llm_model_health stays (table dropped + surface deleted in this hot-patch).
export LEGACY_TABLES='audit_job_runs|ayanamsha_registry|build_checkpoints|build_dependencies|build_engine_versions|build_manifests|build_notifications|chart_ayanamsha_reports|chart_dashas|chart_documents|chart_facts|chart_facts_history|chart_facts_staging|chart_facts_supersedence|chat_attachments|classical_attributions|classical_chunks|classical_texts|cluster_register|cluster_register_staging|context_assembly_log|contradiction_register|contradiction_register_staging|convergence_scores|data_source_expected|dasha_periods|divisional_charts|documents|eclipses|eclipses_retrogrades|eclipses_staging|engine_versions|ephemeris_daily|ephemeris_daily_staging|g29_timing_rules|gate_change_log|kp_sublords|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_chart_lattice_snapshots|l25_derivation_graph_edges|l25_derivation_graph_nodes|l25_divergence_ledger|l25_msr_signals|l25_msr_signals_staging|l25_negative_space_map|l25_pattern_catalog|l25_rm_resonances|l25_rm_resonances_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_vedha_anchor_interactions|llm_catalog_snapshot|llm_config_audit|llm_model_health|llm_param_override|llm_stack_routing_override|mcp_audit_findings|mcp_bundle_cache|message_feedback|messages|msr_signals|multi_school_stances|notification_views|panchanga_daily|panchanga_daily_staging|pattern_register|pattern_register_staging|prediction_ledger|predictions|pyramid_layers|query_plans|rag_chunks|rag_chunks_staging|rag_embeddings|rag_embeddings_staging|rag_feedback|rag_graph_edges|rag_graph_nodes|rag_queries|rag_reproducibility_failures|rag_retrievals|resonance_register|resonance_register_staging|retrogrades|retrogrades_staging|sade_sati_cycles|sade_sati_phases|sade_sati_phases_staging|sankranti_table|saturn_sign_changes|school_analysis_runs|school_convergence_index|school_disagreements|school_signal_coverage|shadbala|signal_states|tajaka_annual|tool_caveats|varshaphala'

# AC-1: zero legacy citations across platform/src
grep -rEn "(${LEGACY_TABLES})" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git \
  platform/src 2>/dev/null | tee /tmp/ws0b_hp_final_grep.txt
test ! -s /tmp/ws0b_hp_final_grep.txt && echo "AC-1 PASS" || { echo "AC-1 FAIL"; head -20 /tmp/ws0b_hp_final_grep.txt; }

# AC-2: typecheck no new errors
cd platform
npm run typecheck 2>&1 | tee /tmp/ws0b_hp_typecheck.txt
grep -E "Found [0-9]+ error" /tmp/ws0b_hp_typecheck.txt
cd ..
# Expect ≤ 45 errors (the post-WS-0B count). Hot-patch should not raise it.

# AC-3: production build (re-attempt — dead imports gone)
cd platform
npm run build 2>&1 | tee /tmp/ws0b_hp_build.txt | tail -20
grep -E "(Compiled successfully|Failed to compile)" /tmp/ws0b_hp_build.txt
cd ..

# AC-4: pytest sanity
cd platform
python -m pytest python-sidecar/tests/ --ignore=python-sidecar/tests/integration -q 2>&1 | tail -5
cd ..

# AC-8: drift_detector quiet
python platform/scripts/governance/drift_detector.py 2>&1 | tail -20
```

If AC-3 still fails on the Turbopack symlink issue, capture the exact error verbatim and note in the PR comment — that's a pre-existing tooling issue unrelated to legacy purge.

---

## Step 7 — Push + update PR #206

```bash
git push origin feature/ws0b-code-cluster-purge
```

Update PR #206 with this comment template (fill in the AC results):

```
### WS-0B Hot-Patch Applied (4 commits — Option A)

Targeted re-grep + reverse-citation gate found the dead surface reached
beyond `prober.ts` into three live admin route files. Native call: Option A
— delete the full AIOps LLM-health observability surface; defer rebuild
to Mīmāṃsā/L5.

**Commits:**
1. `chore(ws0b): drop AIOps LLM-health admin surface (Option A)` — prober + test + 3 routes + UI panels + types + nav entries
2. `fix(drift): drop phantom reference to deleted rag_router.py`
3. `fix(types): resolve retry_wrapper TS error from deleted-module import`
4. `docs(brahma): record AIOps observability as deferred under Mīmāṃsā/L5` — new BRAHMA_DEFERRED_FEATURES.md

**Updated AC scorecard:**
- AC-1: PASS (zero legacy citations across platform/src)
- AC-2: PASS (typecheck count: NN, baseline 47)
- AC-3: [PASS / pre-existing Turbopack symlink — unrelated, capture verbatim]
- AC-4: PASS
- AC-5: PASS
- AC-6: PASS
- AC-7: [PASS after AC-3 / blocked by pre-existing AC-3]
- AC-8: PASS (drift_detector + retry_wrapper green)

Branch ready for merge. Native to review + merge.
```

**STOP here. Do NOT merge the PR. PR-to-main is human-gated.**

---

## Hard stops (halt immediately, do not attempt fix, report to native)

- Step 1's scheduler-hook grep returns any non-empty result (Cloud Scheduler / cron / queue triggering the prober — that's a deeper hook).
- Step 1's admin-link grep shows a Brahma-active page (cockpit, dashboard, Layer Tower, Asset Inspector) linking to `/admin/aiops`.
- After Step 2 typecheck, a non-AIOps file shows a new compile error not caused by removed AIOps imports.
- AC-1 final grep returns any hits.
- AC-3 fails with errors unrelated to the pre-existing Turbopack symlink.
- More than 3 attempts on any single fix.

Begin with Step 0. Report at each commit and at the final AC scorecard.
