---
artifact: CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE
version: 1.0
status: READY_FOR_EXECUTION
project_codename: Brahma — Legacy Code Cluster Purge (WS-0B follow-on)
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code extension running inside Google Antigravity IDE
execution_surface: >
  Claude Code (the extension) hosted in Google Antigravity IDE. CC drives this entire run from its
  integrated bash terminal + Read/Write/Edit/Grep tools, rooted at `/Users/Dev/Vibe-Coding/Apps/Madhav`.
  Every command paste-ready into CC's bash; no IDE switch.
follows: CLAUDECODE_BRIEF_WS0_LEGACY_PURGE_v1_0.md (v1.2, executed 2026-06-04, tag `legacy-purge-v2-complete`)
native_approved: true  # native confirmed 2026-06-04 — "Yes go ahead"
no_backup: true        # forward-only commitment; commits are the audit trail
context: >
  WS-0 closed with AC-3 partial: ~1,877 SQL citations to dropped legacy tables remained in four
  dead-code clusters under platform/src (build/ A1–A14 DAG orchestration, aiops/ never-deployed
  stack, prediction/ pre-Mīmāṃsā ledger, reports/ v1 messaging era). They are runtime-bombs: tables
  don't exist, so any route reaching these paths throws at SQL execution; TypeScript can't catch it.
  WS-0B exists to eliminate the runtime risk before WS-1 (portal drivability) touches the same
  surfaces.
acceptance_criteria:
  - "AC-1: Full LEGACY_TABLES grep (the WS-0 v1.2 alternation) across platform/src returns zero hits"
  - "AC-2: `npm run typecheck` exits 0 new errors (pre-existing in KNOWN_PRE_EXISTING_FAILURES.md OK)"
  - "AC-3: `npm run build` exits 0 (catches import-resolution runtime-bombs typecheck misses)"
  - "AC-4: `python -m pytest platform/python-sidecar/tests/ --ignore=platform/python-sidecar/tests/integration` exits 0 (sanity — no Python changes expected, but verify)"
  - "AC-5: `madge --orphans --extensions ts,tsx platform/src` shows no NEW orphan files vs the pre-WS-0B baseline captured in Step 0"
  - "AC-6: All four named clusters (build/, aiops/, prediction/, reports/) fully removed; each surviving file under those dirs has an explicit kept-because note in the commit message"
  - "AC-7: A curl smoke against every Next.js route file under platform/src/app returns 200, 302/307 redirect, or a documented 401/403 (no 500s from import resolution)"
  - "AC-8: CI green on the WS-0B branch — typecheck, unit-tests, secret-scan, naming-lint, governance-gates, planner-regression all pass"
may_touch:
  - "platform/src/lib/build/**"
  - "platform/src/lib/aiops/**"
  - "platform/src/lib/prediction/**"
  - "platform/src/lib/reports/**"
  - "platform/src/build/**"
  - "platform/src/aiops/**"
  - "platform/src/prediction/**"
  - "platform/src/reports/**"
  - "platform/src/app/api/**"  # may need to delete legacy route handlers consuming the above
  - "platform/src/components/**"  # may need to delete dead UI components consuming the above
  - "platform/src/hooks/**"
  - "platform/src/lib/clients/**"  # may need to delete legacy DB clients
  - "platform/src/lib/types/**"  # may need to delete legacy type defs
  - "platform/src/__tests__/**"  # delete tests of deleted code
  - "platform/src/lib/**/**.test.ts"
  - "platform/scripts/**"  # any straggler scripts the WS-0 step 2c missed
  - "platform/package.json"  # if scripts entries reference deleted files
must_not_touch:
  - "platform/python-sidecar/**"          # Brahma engine; WS-0 v1.2 audit.ts re-point is done
  - "platform-mcp/**"                     # MCP sidecar; WS-0 already cleaned
  - "platform/src/app/api/build/start/**" # the NEW Brahma build trigger (RUNTIME-GUARDIAN fixed)
  - "platform/src/app/api/build/events/**" # Brahma SSE live rail
  - "platform/src/app/api/build/active/**" # may still be polling shim; preserve
  - "platform/supabase/migrations/**"     # frozen history
  - "01_FACTS_LAYER/**"
  - "00_ARCHITECTURE/**"
  - ".github/workflows/**"                # WS-0 surface 3 already done
  - "CAPABILITY_MANIFEST.json"
project_facts:
  gcp_project: madhav-astrology
  region: asia-south1
  prod_url: madhav.marsys.in
  branch: feature/ws0b-code-cluster-purge
  predecessor_tag: legacy-purge-v2-complete
---

# CLAUDECODE_BRIEF — WS-0B Legacy Code Cluster Purge

## §1 Mission

Four dead-code clusters in `platform/src` — `build/`, `aiops/`, `prediction/`, `reports/` — still contain ~1,877 SQL citations to tables WS-0 dropped. They are imported deeply enough that simple deletion breaks the TypeScript graph; that's why WS-0 left them as a follow-on. **WS-0B's job: discover the full blast radius of each cluster, delete or re-point every file in it, and prove the result with build + curl-smoke gates that catch the runtime-bomb cases TypeScript misses.**

**Execution context — Claude Code extension in Google Antigravity IDE.** All commands paste-ready into CC's integrated bash. Repo root `/Users/Dev/Vibe-Coding/Apps/Madhav`.

**Branch:** `feature/ws0b-code-cluster-purge` cut from `main` at tag `legacy-purge-v2-complete`. Per-cluster commits so any cluster's delete is revertable in isolation.

---

## §1a Prerequisites

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Cut the branch from the WS-0 sealing tag
git fetch origin --tags
git checkout -b feature/ws0b-code-cluster-purge legacy-purge-v2-complete

# Install audit tooling (madge for import-graph, ts-prune for unused exports)
# Use npx so we don't pollute package.json
npx --yes madge --version
npx --yes ts-prune --version

# Reuse the LEGACY_TABLES alternation from WS-0 v1.2 Step 2-PRE
# (Update this if the source-of-truth list ever changes)
export LEGACY_TABLES='audit_job_runs|ayanamsha_registry|build_checkpoints|build_dependencies|build_engine_versions|build_events|build_manifests|build_notifications|build_steps|builds|builds_staging|chart_ayanamsha_reports|chart_dashas|chart_documents|chart_facts|chart_facts_history|chart_facts_staging|chart_facts_supersedence|chat_attachments|classical_attributions|classical_chunks|classical_texts|cluster_register|cluster_register_staging|context_assembly_log|contradiction_register|contradiction_register_staging|convergence_scores|data_source_expected|dasha_periods|divisional_charts|documents|eclipses|eclipses_retrogrades|eclipses_staging|engine_versions|ephemeris_daily|ephemeris_daily_staging|g29_timing_rules|gate_change_log|kp_sublords|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_chart_lattice_snapshots|l25_derivation_graph_edges|l25_derivation_graph_nodes|l25_divergence_ledger|l25_msr_signals|l25_msr_signals_staging|l25_negative_space_map|l25_pattern_catalog|l25_rm_resonances|l25_rm_resonances_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_vedha_anchor_interactions|llm_catalog_snapshot|llm_config_audit|llm_model_health|llm_param_override|llm_stack_routing_override|mcp_audit_findings|mcp_bundle_cache|message_feedback|messages|msr_signals|multi_school_stances|notification_views|panchanga_daily|panchanga_daily_staging|pattern_register|pattern_register_staging|prediction_ledger|predictions|pyramid_layers|query_plans|rag_chunks|rag_chunks_staging|rag_embeddings|rag_embeddings_staging|rag_feedback|rag_graph_edges|rag_graph_nodes|rag_queries|rag_reproducibility_failures|rag_retrievals|reports|resonance_register|resonance_register_staging|retrogrades|retrogrades_staging|sade_sati_cycles|sade_sati_phases|sade_sati_phases_staging|sankranti_table|saturn_sign_changes|school_analysis_runs|school_convergence_index|school_disagreements|school_signal_coverage|shadbala|signal_states|tajaka_annual|tool_caveats|varshaphala'

# Baseline gates (so we can prove "no new errors" later)
cd platform
npm run typecheck 2>&1 | tee /tmp/ws0b_typecheck_baseline.txt
npx --yes madge --orphans --extensions ts,tsx src 2>&1 | tee /tmp/ws0b_orphans_baseline.txt
cd ..
```

---

## §2 Step 0 — Cluster discovery (import-graph audit)

Goal: produce a per-cluster disposition table — every file in each cluster classified as `ORPHAN` (no live consumer reachable from a route/page), `CONSUMED BY DEAD` (only consumed by other legacy files), or `CONSUMED BY LIVE` (a live route/page imports it, needs re-point or consumer-also-deletes).

### 2.0 Locate the actual cluster directories

```bash
# The four named clusters MAY live at platform/src/lib/<cluster>/ or platform/src/<cluster>/
# Find them programmatically — do not assume a path.
find platform/src -maxdepth 4 -type d \( \
       -name 'build' -o -name 'aiops' -o -name 'prediction' -o -name 'reports' \
     \) -not -path '*/node_modules/*' \
     | tee /tmp/ws0b_cluster_dirs.txt
cat /tmp/ws0b_cluster_dirs.txt

# Sanity: there should be one or two paths per named cluster. If the result is empty for
# any named cluster → confirm WS-0 didn't already delete it (git log --diff-filter=D
# --name-only legacy-purge-v2-complete~..legacy-purge-v2-complete | grep -E 'build|aiops|prediction|reports')
# and skip that cluster.

# Also enumerate any OTHER dir under platform/src that contains a heavy citation count to LEGACY_TABLES
grep -rEln "(${LEGACY_TABLES})" platform/src \
  --include="*.ts" --include="*.tsx" 2>/dev/null \
  | xargs -I {} dirname {} | sort | uniq -c | sort -rn \
  | tee /tmp/ws0b_citation_hotspots.txt
head -30 /tmp/ws0b_citation_hotspots.txt
```

The hotspots table reveals any cluster the four named ones don't capture. **Read this output before proceeding** — if a non-named hotspot has >50 citations, add it to the cluster list for §3.

### 2.1 Per-cluster import-graph audit

For each cluster path in `/tmp/ws0b_cluster_dirs.txt`, run the audit:

```bash
audit_cluster() {
  local CLUSTER_DIR="$1"
  local CLUSTER_NAME=$(basename "$CLUSTER_DIR")
  echo "=== Auditing cluster: $CLUSTER_DIR ==="

  # All files in the cluster
  find "$CLUSTER_DIR" -type f \( -name '*.ts' -o -name '*.tsx' \) \
    | sort > /tmp/ws0b_${CLUSTER_NAME}_files.txt
  local FILE_COUNT=$(wc -l < /tmp/ws0b_${CLUSTER_NAME}_files.txt)
  echo "Files in cluster: $FILE_COUNT"

  # Citation count to legacy tables (sanity: the cluster IS legacy)
  local CITE_COUNT=$(grep -rEc "(${LEGACY_TABLES})" "$CLUSTER_DIR" \
    --include="*.ts" --include="*.tsx" 2>/dev/null \
    | awk -F: '{s+=$2}END{print s+0}')
  echo "Legacy-table citations in cluster: $CITE_COUNT"

  # Reverse dependency — who outside the cluster imports anything from the cluster?
  # Pattern: any import path containing "/<CLUSTER_NAME>/" or "/<cluster_subpath>/"
  local CLUSTER_REL=$(echo "$CLUSTER_DIR" | sed 's|platform/src/||; s|^lib/||')
  echo "Reverse imports (consumers outside the cluster):"
  grep -rEln "from ['\"][^'\"]*/${CLUSTER_NAME}/" platform/src \
    --include="*.ts" --include="*.tsx" 2>/dev/null \
    | grep -v "^${CLUSTER_DIR}/" \
    | tee /tmp/ws0b_${CLUSTER_NAME}_consumers.txt

  local CONSUMER_COUNT=$(wc -l < /tmp/ws0b_${CLUSTER_NAME}_consumers.txt)
  echo "Outside consumers: $CONSUMER_COUNT"

  # If 0 outside consumers → cluster is ORPHAN-AT-ROOT → wholesale delete is safe.
  # If >0 → walk each consumer; classify by whether the consumer is itself a route/page,
  # another legacy file, or a live shared lib.
  if [ "$CONSUMER_COUNT" -gt 0 ]; then
    echo "Classifying each consumer:"
    while IFS= read -r consumer; do
      # Is the consumer a Next.js route/page?
      if echo "$consumer" | grep -qE 'app/.*/(page|route)\.(ts|tsx)$'; then
        echo "  LIVE-ROUTE: $consumer"
      # Is the consumer in another known legacy cluster?
      elif echo "$consumer" | grep -qE '/(build|aiops|prediction|reports)/'; then
        echo "  DEAD-CONSUMER: $consumer"
      else
        echo "  UNCLASSIFIED: $consumer"  # MANUALLY DECIDE
      fi
    done < /tmp/ws0b_${CLUSTER_NAME}_consumers.txt
  fi

  # Orphans within the cluster (per madge)
  echo "Madge orphans within $CLUSTER_DIR:"
  npx --yes madge --orphans --extensions ts,tsx "$CLUSTER_DIR" 2>/dev/null \
    | tee /tmp/ws0b_${CLUSTER_NAME}_orphans.txt

  echo "=== End audit: $CLUSTER_NAME ==="
}

# Run the audit for each cluster
while IFS= read -r dir; do
  audit_cluster "$dir"
done < /tmp/ws0b_cluster_dirs.txt
```

### 2.2 Disposition table

Output of the audit produces a per-cluster disposition. CC writes this to `/tmp/ws0b_disposition.md`:

```
| Cluster | Dir | Files | Citations | Outside consumers | Disposition |
|---|---|---|---|---|---|
| build | platform/src/lib/build/ | N | C | k LIVE-ROUTE / m DEAD / 0 UNCLASSIFIED | DELETE_WHOLESALE \| DELETE_WITH_CONSUMERS \| REPOINT |
| aiops | ... | ... | ... | ... | ... |
| prediction | ... | ... | ... | ... | ... |
| reports | ... | ... | ... | ... | ... |
```

**Decision rules:**
- All outside consumers are DEAD-CONSUMER or LIVE-ROUTE that no longer exists in Brahma → **DELETE_WHOLESALE.** Delete cluster + all consumers in one commit.
- One or more LIVE-ROUTE consumers map to a Brahma-active surface (e.g., the chart-build cockpit) → **REPOINT.** Re-point the consumer to the Brahma equivalent (likely `platform-mcp/` tool or `platform/python-sidecar/brahmagyan/`). Note the re-point details inline.
- One or more UNCLASSIFIED → **HALT.** Report each unclassified consumer to native for a manual call. Do not guess.

---

## §3 Per-cluster execution

Execute clusters in this order: aiops (smallest, never deployed — proves the pattern) → reports → prediction → build (largest, most coupled). For each cluster:

```bash
purge_cluster() {
  local CLUSTER_DIR="$1"
  local CLUSTER_NAME=$(basename "$CLUSTER_DIR")
  local DISPOSITION="$2"  # DELETE_WHOLESALE | DELETE_WITH_CONSUMERS | REPOINT

  echo "=== Purging cluster: $CLUSTER_NAME ($DISPOSITION) ==="

  case "$DISPOSITION" in
    DELETE_WHOLESALE)
      git rm -r "$CLUSTER_DIR"
      ;;
    DELETE_WITH_CONSUMERS)
      git rm -r "$CLUSTER_DIR"
      # Delete every DEAD-CONSUMER from /tmp/ws0b_${CLUSTER_NAME}_consumers.txt
      grep "^  DEAD-CONSUMER: " /tmp/ws0b_${CLUSTER_NAME}_consumers.txt \
        | awk '{print $2}' \
        | xargs -I {} git rm {}
      # Then delete any LIVE-ROUTE consumers whose route is no longer reachable in Brahma
      # (native sign-off required per LIVE-ROUTE entry; see disposition table for the call)
      ;;
    REPOINT)
      # Per-consumer re-point: edit each LIVE-ROUTE file to use the Brahma equivalent
      # The specific re-point is documented in the disposition table for this cluster
      echo "REPOINT: edit each LIVE-ROUTE consumer per the disposition table; do not git rm the cluster blindly."
      ;;
  esac

  # Verification gates AFTER the cluster delete
  echo "Running per-cluster gates:"
  cd platform
  npm run typecheck 2>&1 | tee /tmp/ws0b_${CLUSTER_NAME}_typecheck.txt
  if grep -E "error TS" /tmp/ws0b_${CLUSTER_NAME}_typecheck.txt; then
    echo "TYPECHECK FAILED for cluster $CLUSTER_NAME — review errors, decide:"
    echo "  (a) Add the failing file to the delete list (it consumed the cluster), or"
    echo "  (b) Re-point the failing file to a Brahma equivalent"
    echo "Then re-run gates. Do NOT commit until typecheck is green."
    cd ..
    return 1
  fi
  cd ..

  # Per-cluster commit
  git add -A
  git commit -m "chore(ws0b): purge legacy cluster ${CLUSTER_NAME}

  Disposition: ${DISPOSITION}
  Files deleted: see commit stat
  Consumers handled: see /tmp/ws0b_${CLUSTER_NAME}_consumers.txt
  AC verified: typecheck green post-delete

  Part of WS-0B (follows tag legacy-purge-v2-complete)"

  echo "=== Done: $CLUSTER_NAME committed ==="
}

# Manually invoke per cluster, in order, after reviewing /tmp/ws0b_disposition.md:
# purge_cluster platform/src/lib/aiops DELETE_WHOLESALE
# purge_cluster platform/src/lib/reports DELETE_WHOLESALE
# purge_cluster platform/src/lib/prediction DELETE_WITH_CONSUMERS
# purge_cluster platform/src/lib/build DELETE_WITH_CONSUMERS
```

**Stop-and-report on any cluster where the gates fail after 3 attempts** — do not loop unbounded.

---

## §4 Step 4 — Final verification suite

After all clusters are committed, run the full WS-0 v1.2 Step-4 grep across `platform/src` plus the additional WS-0B gates.

### 4.1 LEGACY_TABLES grep — must return zero

```bash
# Same alternation as §1a. Must return 0 hits across all of platform/src.
grep -rEn "(${LEGACY_TABLES})" \
  --include="*.ts" --include="*.tsx" \
  --exclude-dir=node_modules --exclude-dir=.next --exclude-dir=.git \
  platform/src \
  2>/dev/null | tee /tmp/ws0b_final_grep.txt

# AC-1: file must be empty (zero lines)
test ! -s /tmp/ws0b_final_grep.txt && echo "AC-1 PASS" || { echo "AC-1 FAIL — citations remain"; head -20 /tmp/ws0b_final_grep.txt; exit 1; }
```

### 4.2 Typecheck + build (catches runtime-bombs typecheck alone misses)

```bash
cd platform
npm run typecheck 2>&1 | tee /tmp/ws0b_final_typecheck.txt
# AC-2: zero NEW errors vs /tmp/ws0b_typecheck_baseline.txt
diff /tmp/ws0b_typecheck_baseline.txt /tmp/ws0b_final_typecheck.txt | grep -E "^> .*error TS" \
  && { echo "AC-2 FAIL — new typecheck errors"; exit 1; } || echo "AC-2 PASS"

# AC-3: production build succeeds
npm run build 2>&1 | tee /tmp/ws0b_build.txt
grep -E "(Compiled successfully|Failed to compile)" /tmp/ws0b_build.txt
# AC-3 PASS if "Compiled successfully" appears
cd ..
```

### 4.3 Python pytest (sanity — no Python changes expected)

```bash
cd platform
python -m pytest python-sidecar/tests/ \
  --ignore=python-sidecar/tests/integration \
  -q 2>&1 | tail -10
# AC-4: all green
cd ..
```

### 4.4 Madge orphan delta — no NEW orphans

```bash
cd platform
npx --yes madge --orphans --extensions ts,tsx src 2>&1 | tee /tmp/ws0b_orphans_post.txt
cd ..

# AC-5: no NEW orphans vs baseline (orphans we created by deleting consumers without deleting their imports)
diff /tmp/ws0b_orphans_baseline.txt /tmp/ws0b_orphans_post.txt | grep '^>' \
  && { echo "AC-5 FAIL — new orphans"; exit 1; } || echo "AC-5 PASS"
```

### 4.5 Cluster-residue check

```bash
# AC-6: each named cluster either fully gone, or surviving files documented
for cluster in build aiops prediction reports; do
  remaining=$(find platform/src -type d -name "$cluster" -not -path '*/node_modules/*' 2>/dev/null)
  if [ -n "$remaining" ]; then
    file_count=$(find "$remaining" -type f \( -name '*.ts' -o -name '*.tsx' \) | wc -l)
    if [ "$file_count" -gt 0 ]; then
      echo "Cluster $cluster has $file_count surviving files at $remaining — REPOINT disposition expected:"
      ls "$remaining"
    fi
  fi
done
```

### 4.6 Route curl smoke (catches the runtime-bomb at the HTTP layer)

The deploy-build above proves the bundle compiles. This step proves every route loads its handler module without throwing. Run against a locally-served build (Next.js standalone or `npm run start` after the build).

```bash
cd platform
# Start the production build in the background
npm run start &
SERVER_PID=$!
sleep 5  # wait for boot

# Enumerate every public route (api routes + pages)
ROUTES=$(find src/app -type f \( -name 'page.tsx' -o -name 'route.ts' \) \
         | sed 's|src/app||; s|/page\.tsx$||; s|/route\.ts$||' \
         | sort -u)

echo "=== Curl smoke against $(echo "$ROUTES" | wc -l) routes ==="
FAIL=0
for route in $ROUTES; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:3000${route:-/}")
  case "$CODE" in
    200|301|302|307|401|403)
      echo "OK   [$CODE] $route" ;;
    500|502|503)
      echo "FAIL [$CODE] $route"; FAIL=$((FAIL+1)) ;;
    *)
      echo "UNKN [$CODE] $route" ;;  # 404 is fine (dynamic routes need params)
  esac
done

kill $SERVER_PID
cd ..

# AC-7: zero 500s from import resolution
test "$FAIL" -eq 0 && echo "AC-7 PASS" || { echo "AC-7 FAIL — $FAIL routes 5xx'd"; exit 1; }
```

A 5xx here means a route's handler module still imports something that hits a dropped table at module-init time. Fix the import or delete the route.

### 4.7 CI green check (after push)

```bash
# AC-8: push the branch and verify CI passes
git push -u origin feature/ws0b-code-cluster-purge

# Then watch CI — typecheck, unit-tests, secret-scan, naming-lint, governance-gates,
# planner-regression must all pass. Use gh CLI:
gh run watch --branch feature/ws0b-code-cluster-purge
# Or via web: https://github.com/<org>/Madhav/actions
```

---

## §5 Commit discipline + tag

- One commit per cluster from `purge_cluster()`. Plus one final commit if §4 verification surfaces a fix (e.g., a stray orphan that needs deletion).
- After AC-1 through AC-8 all green, tag the head: `git tag legacy-code-cluster-purge-complete && git push origin legacy-code-cluster-purge-complete`.
- Open PR `feature/ws0b-code-cluster-purge → main` with the AC report in the description. **The PR-to-main is a human gate** (per durable preference: "PR-to-main is human-gated"). Native reviews + merges.

---

## §6 Out of WS-0B scope

| # | Item | Why deferred | Follow-up |
|---|------|--------------|-----------|
| 1 | UI dead-state in cockpit / dashboard / consult | WS-1 (drivable portal) is the natural home — those surfaces are rebuilt there | WS-1 brief |
| 2 | Brahma writer depth (thin data) | WS-2 (honest volume floors + full builds) | WS-2 brief |
| 3 | Rule Base rework (BG-0-6) | WS-3 (native-led) | WS-3 brief |
| 4 | GCS bucket contents | Same as WS-0 §8 #1 | WS-0C / pre-WS-2 brief |
| 5 | `CAPABILITY_MANIFEST.json` legacy entries | Same as WS-0 §8 #2 | M5 governance re-base |
| 6 | Historical SQL migration squash | Same as WS-0 §8 #3 | After WS-2 |

---

## §7 If you find something unexpected

This audit is concrete but the codebase is real — there will be surprises. Decision rules:

- A cluster the audit reveals you didn't expect → add to the §3 list, audit it the same way, halt for native sign-off only if disposition is REPOINT or UNCLASSIFIED.
- A live route that needs REPOINT but the Brahma equivalent doesn't exist yet → HALT. Report to native. Do not stub.
- Tests of deleted code that are now broken → delete the tests in the same commit as their subject.
- A type definition (`types/*.ts`) only used by deleted code → delete it.
- A package.json script entry pointing to a deleted file → remove it.
- A pre-existing typecheck error that surfaces louder after a delete (cascade) → fix or document in `KNOWN_PRE_EXISTING_FAILURES.md` (rare; baseline diff in 4.2 should catch this honestly).

The principle: **leave platform/src cleaner than you found it**, not "minimally cleaner to pass the grep."

---

*End of CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE v1.0. Authored for Claude Code in Antigravity IDE. Follows WS-0 v1.2 (tag `legacy-purge-v2-complete`). Branch `feature/ws0b-code-cluster-purge`. Eight ACs; per-cluster commits; PR-to-main human-gated.*
