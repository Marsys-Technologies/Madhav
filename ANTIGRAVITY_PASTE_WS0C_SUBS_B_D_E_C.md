# WS-0C Sub-B → Sub-D → Sub-E → Sub-C (sequential) — CC Prompt

> **Paste this entire block into your Claude Code chat inside Google Antigravity IDE.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE_v1_0.md`
> Branch: `feature/ws0c-residual-purge` (Sub-A-EXEC commit `f05d2be6` pushed)
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`

---

You are Claude Code in Google Antigravity IDE. Sub-A-EXEC closed (commit `f05d2be6`). This paste executes the four remaining sub-streams **sequentially in a single run** — risk-ordered so the small / well-understood ones land first, and the largest / riskiest one (Sub-C `chart_facts` repoint) lands last. Each sub-stream produces one commit on `feature/ws0c-residual-purge`. After all four close, you open the WS-0C PR and stop at the human-gate.

**Sequence (intentional risk ordering):**

1. **Sub-B** — rest of AIOps admin (smallest, same Option-A pattern as the hot-patch + Sub-A's familiar territory)
2. **Sub-D** — `predictions` residuals (small, mostly delete)
3. **Sub-E** — `documents` in `build-tools.ts` (small, likely delete)
4. **Sub-C** — `chart_facts` + L1/L2.5 layer-table residuals (largest, per-file disposition; most likely to hit a HALT)

If Sub-C halts on an UNCLASSIFIED / REPOINT-with-no-Brahma-equivalent finding, **Sub-B/D/E are already committed** — Sub-C halting only blocks the PR; the rest of the cleanup stands.

## Operating rails (applies to all four sub-streams)

- No backup. Forward-only. Commits are the audit trail.
- `MAX_SPEND_PER_ASSET`: $300 per sub-stream — halt if exceeded.
- `verify-before-promote`: ON — each sub-stream's commit gated on its typecheck + partial AC sweep.
- `bounded-retries`: 3 per failing step. Beyond → halt and report.
- **PR-to-main is human-gated.** You open the PR at the end; native reviews + merges.
- Per the durable rule: every destructive action requires a reverse-citation gate before commit. No file goes away without verified-dead evidence.

## Step 0 — Branch + proxy + baselines

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout feature/ws0c-residual-purge
git pull origin feature/ws0c-residual-purge
git log --oneline -3   # confirm f05d2be6 is at the top after main; pull may rebase

# Start Cloud SQL proxy
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
psql_prod -c "SELECT 1;" >/dev/null && echo "Proxy up" || { echo "Proxy fail"; exit 1; }

# Capture pre-Sub-B baselines
cd platform
npm run typecheck 2>&1 | tee /tmp/ws0c_subB_baseline_typecheck.txt
cd ..

# Reuse the LEGACY_TABLES alternation (same as the WS-0C brief)
export LEGACY_TABLES='audit_job_runs|ayanamsha_registry|build_checkpoints|build_dependencies|build_engine_versions|build_manifests|build_notifications|chart_ayanamsha_reports|chart_dashas|chart_documents|chart_facts|chart_facts_history|chart_facts_staging|chart_facts_supersedence|chat_attachments|classical_attributions|classical_chunks|classical_texts|cluster_register|cluster_register_staging|context_assembly_log|contradiction_register|contradiction_register_staging|convergence_scores|data_source_expected|dasha_periods|divisional_charts|documents|eclipses|eclipses_retrogrades|eclipses_staging|engine_versions|ephemeris_daily|ephemeris_daily_staging|g29_timing_rules|gate_change_log|kp_sublords|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_chart_lattice_snapshots|l25_derivation_graph_edges|l25_derivation_graph_nodes|l25_divergence_ledger|l25_msr_signals|l25_msr_signals_staging|l25_negative_space_map|l25_pattern_catalog|l25_rm_resonances|l25_rm_resonances_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_vedha_anchor_interactions|llm_catalog_snapshot|llm_config_audit|llm_model_health|llm_param_override|llm_stack_routing_override|mcp_audit_findings|mcp_bundle_cache|message_feedback|messages|msr_signals|multi_school_stances|notification_views|panchanga_daily|panchanga_daily_staging|pattern_register|pattern_register_staging|prediction_ledger|predictions|pyramid_layers|query_plans|rag_chunks|rag_chunks_staging|rag_embeddings|rag_embeddings_staging|rag_feedback|rag_graph_edges|rag_graph_nodes|rag_queries|rag_reproducibility_failures|rag_retrievals|resonance_register|resonance_register_staging|retrogrades|retrogrades_staging|sade_sati_cycles|sade_sati_phases|sade_sati_phases_staging|sankranti_table|saturn_sign_changes|school_analysis_runs|school_convergence_index|school_disagreements|school_signal_coverage|shadbala|signal_states|tajaka_annual|tool_caveats|varshaphala'
```

---

# === SUB-B: Rest of AIOps admin surface ===

**Surface:** `llm_stack_routing_override`, `llm_config_audit`, `llm_param_override`.
**Pattern:** Option A — delete the surface; append a new entry to `BRAHMA_DEFERRED_FEATURES.md`.

## B.1 — Surface enumeration

```bash
export SUBB_TABLES='llm_stack_routing_override|llm_config_audit|llm_param_override'

# SQL-context grep + casual citations
grep -rEn "(${SUBB_TABLES})" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0c_subB_grep.txt
awk -F: '{print $1}' /tmp/ws0c_subB_grep.txt | sort | uniq -c | sort -rn | tee /tmp/ws0c_subB_files.txt
cat /tmp/ws0c_subB_files.txt

# Look for admin routes + UI components
grep -rEln "/api/admin/aiops/(routing|config|params|stack|override)" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0c_subB_routes.txt

# Reverse-citation gate: scheduler / cron / queue triggers (same pattern as Sub-A's prober)
grep -rEn "(routingOverride|configAudit|paramOverride|llm_stack_routing|llm_config_audit|llm_param_override)" \
  platform/scripts .github \
  --include='*.ts' --include='*.py' --include='*.yaml' --include='*.yml' --include='*.sh' 2>/dev/null \
  | tee /tmp/ws0c_subB_scheduler_hooks.txt

# Brahma-link check
grep -rEn "/admin/aiops" platform/src --include='*.ts' --include='*.tsx' 2>/dev/null \
  | tee /tmp/ws0c_subB_admin_links.txt
```

**HALT** if `/tmp/ws0c_subB_scheduler_hooks.txt` is non-empty AND the hooks reference a Cloud Scheduler / Cloud Run Job / cron trigger (not just an npm-script handle like Sub-A's case). Report to native.

**HALT** if Brahma-active surfaces (cockpit, dashboard, Layer Tower, Asset Inspector) link to `/admin/aiops` — that means the surface isn't standalone.

Belt-and-suspenders gcloud check:
```bash
gcloud scheduler jobs list --location=asia-south1 2>&1 | grep -iE 'aiops|routing|config|param|override' \
  || echo "GCLOUD_SCHEDULER: clear for Sub-B targets"
gcloud run jobs list --region=asia-south1 2>&1 | grep -iE 'aiops|routing|config|param|override' \
  || echo "GCLOUD_RUN_JOBS: clear for Sub-B targets"
```

## B.2 — Build the delete list

Combine: 5 known surface files + everything from `/tmp/ws0c_subB_files.txt` and `/tmp/ws0c_subB_routes.txt` not already covered. Anticipated targets:

- Three admin route files: `app/api/admin/aiops/routing/route.ts`, `.../config/route.ts`, `.../params/route.ts` (or similar names; let the grep tell you).
- Any related UI components in `platform/src/lib/components/aiops/` or `platform/src/app/admin/aiops/`.
- Type defs in `platform/src/lib/db/schema/aiops.ts` for these tables — surgical edit (not full delete) since Sub-A-EXEC's predecessor hot-patch already touched this file.
- Any npm scripts in `package.json` (per Sub-A's bulk-cron precedent).

## B.3 — Execute

```bash
# Delete admin route files
# (concrete commands depend on what B.1 found; write them based on the actual paths)
git rm <route files>
git rm <UI components>

# Empty-dir cleanup
for d in <directories that should now be empty>; do
  [ -d "$d" ] && [ -z "$(find "$d" -type f)" ] && rmdir "$d"
done

# Surgical edit on schema/aiops.ts: remove only the types for the three dropped tables
# (keep types for any KEPT tables — llm_pricing_versions, llm_usage_events, llm_call_log, etc.)

# Remove any npm script entries
grep -E '"(aiops:routing|aiops:config|aiops:params)"' platform/package.json

# Verify zero residuals
grep -rEn "(${SUBB_TABLES})" platform/src --include='*.ts' --include='*.tsx' 2>/dev/null
# Expected: zero

# Typecheck
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head && cd ..
```

## B.4 — Append to BRAHMA_DEFERRED_FEATURES.md

Add a new numbered section (section 2 — section 1 is the AIOps health surface from the WS-0B hot-patch):

```markdown
## 2. AIOps LLM stack-routing override + config audit + param override admin surface

**Removed:** 2026-06-04, WS-0C Sub-B.

**What it was.** Three admin routes (`/api/admin/aiops/routing|config|params`) reading
`llm_stack_routing_override`, `llm_config_audit`, `llm_param_override` — the rest of the
AIOps observability stack the WS-0B hot-patch did not reach.

**Why removed.** Same reasoning as section 1. WS-0 dropped these tables; the admin surface was
silently broken with no observable impact for days. Same Option-A disposition: delete rather
than restore-and-stub.

**Where it goes.** Rebuild alongside section 1's AIOps health under Mīmāṃsā/L5 as the LLM-quality
calibration concern. Single rebuild for both AIOps surfaces; do not resurrect either piecemeal.

**Rebuild trigger.** When Mīmāṃsā/L5 work begins.
```

## B.5 — Sub-B commit

```bash
git add -A
git commit -m "chore(ws0c): drop rest of AIOps admin surface (Sub-B)

WS-0 dropped llm_stack_routing_override / llm_config_audit /
llm_param_override; WS-0C Sub-B reverse-citation gate found three
admin routes (/api/admin/aiops/routing|config|params) + UI panels still
on those tables — the rest of the AIOps observability stack the WS-0B
hot-patch addressed only the health slice of.

Tables missing from prod for days with no observable failure (same
silent-broken signature as the health surface). Native dispostion:
Option A — delete; append to BRAHMA_DEFERRED_FEATURES.md as section 2.

Refs WS-0C"

# Mid-stream AC sweep — partial grep should shrink by Sub-B's hit count (~29)
grep -rEn "(${LEGACY_TABLES})" --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null | wc -l
```

If typecheck reports new errors not caused by Sub-B's edits → halt; do not commit; do not start Sub-D.

---

# === SUB-D: predictions residuals ===

**Surface:** files citing `predictions` table that WS-0B's prediction cluster purge missed.
**Pattern:** delete each (`predictions` rows were already migrated to `mcp_predictions` in WS-0).

## D.1 — Surface enumeration

```bash
export SUBD_TABLES='predictions'

# SQL-context grep (avoid substring false positives — "predictions" is a common identifier)
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+predictions\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0c_subD_grep.txt
awk -F: '{print $1}' /tmp/ws0c_subD_grep.txt | sort | uniq -c | sort -rn | tee /tmp/ws0c_subD_files.txt
cat /tmp/ws0c_subD_files.txt

# Also catch ORM/query-builder style calls
grep -rEn "from\(['\"]predictions['\"]|table\(['\"]predictions['\"]" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0c_subD_orm.txt
```

## D.2 — Per-file disposition

For each file in the union of D.1 outputs:

- **Reverse-citation gate** — does any LIVE route reach this file? Grep `from ['"][^'"]*<file_path_stem>['"]` across platform/src.
- If `predictions` is the file's primary purpose AND no live importer (or only dead-cluster importers) → **DELETE**.
- If a live route uses other functions from the file AND the `predictions` SQL is a side path → **SURGICAL EDIT** removing only the predictions SQL block.
- If a live route uses the predictions SQL → **HALT**; this means there's still a live prediction-write code path on the dropped `predictions` table that should have gone to `mcp_predictions`. Report to native.

Record dispositions in `/tmp/ws0c_subD_disposition.md`.

## D.3 — Execute + commit

```bash
# Per-file rm / Edit per D.2 disposition
# After edits, verify zero residuals
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+predictions\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null
# Expected: zero

cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head && cd ..

git add -A
git commit -m "chore(ws0c): drop predictions table residuals (Sub-D)

WS-0B's prediction cluster purge missed ~122 SQL citations to the
dropped 'predictions' table. WS-0 already migrated the rows to
mcp_predictions (the canonical Brahma prediction log). Sub-D removes
the orphan code that still cited the dropped table.

Dispositions: <K wholesale / L surgical / 0 halt>

Refs WS-0C"
```

Mid-stream partial grep wc -l should drop by ~122.

---

# === SUB-E: documents in build-tools.ts ===

**Surface:** `documents` (mostly in `build-tools.ts`, 19 hits, 8 SQL queries).
**Pattern:** likely delete; possibly surgical-edit `build-tools.ts` if other code paths in the file are live.

## E.1 — Surface enumeration

```bash
export SUBE_TABLES='documents'

# SQL-context grep with word-boundary (avoid `documents` as a JS property name)
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+documents\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0c_subE_grep.txt
awk -F: '{print $1}' /tmp/ws0c_subE_grep.txt | sort | uniq -c | sort -rn | tee /tmp/ws0c_subE_files.txt
cat /tmp/ws0c_subE_files.txt

# Find build-tools.ts specifically
find platform/src -name 'build-tools.ts' -not -path '*/node_modules/*'
```

## E.2 — Per-file disposition (focus on build-tools.ts)

Open `build-tools.ts`. Inspect:
- Exports of the file.
- Which exports touch the `documents` SQL.
- Reverse-import graph: who calls each export.

Decision tree:
- All exports touch dropped `documents` AND no live consumer → **DELETE the whole file**.
- Mixed: some exports live, some touch `documents` → **SURGICAL EDIT**: remove the `documents`-touching functions + remove their callers from any consumer files (which may cascade to a small delete list).
- Surprise: a live route still depends on `documents` SQL with no obvious Brahma equivalent → **HALT**.

Same pattern for any other file in `/tmp/ws0c_subE_files.txt`.

Record in `/tmp/ws0c_subE_disposition.md`.

## E.3 — Execute + commit

```bash
# Per disposition: git rm or Edit
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+documents\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null
# Expected: zero

cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head && cd ..

git add -A
git commit -m "chore(ws0c): drop documents-table residuals (Sub-E)

build-tools.ts contained 8 SQL queries to the dropped 'documents' table
(v1 messaging era). Sub-E [deletes / surgically removes] the dead paths.

Dispositions: <K wholesale / L surgical / 0 halt>

Refs WS-0C"
```

---

# === SUB-C: chart_facts + L1/L2.5 layer-table residuals (largest) ===

**Surface:** `chart_facts`, `divisional_charts`, `varshaphala`, `shadbala`, `dasha_periods`, `chart_dashas`, `l25_*`, `msr_signals`, `pattern_register`, `resonance_register`, `rag_chunks`, `pyramid_layers`, `l1_*`. ~475 hits.
**Pattern:** per-file disposition — REPOINT to Brahma equivalent if reachable from active surface; DELETE if pure dead code.

This is the largest and riskiest sub-stream. Plan time and halt readiness. If a file falls into UNCLASSIFIED or no-Brahma-equivalent, halt cleanly — Sub-B/D/E are already committed and Sub-C halting only blocks the PR; their cleanup is preserved.

## C.1 — Surface enumeration with hotspot grouping

```bash
export SUBC_TABLES='chart_facts|divisional_charts|varshaphala|shadbala|dasha_periods|chart_dashas|msr_signals|pattern_register|pattern_register_staging|resonance_register|resonance_register_staging|rag_chunks|rag_chunks_staging|pyramid_layers|l25_msr_signals|l25_msr_signals_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_rm_resonances|l25_rm_resonances_staging|l25_chart_lattice_snapshots|l25_vedha_anchor_interactions|l25_derivation_graph_nodes|l25_derivation_graph_edges|l25_pattern_catalog|l25_divergence_ledger|l25_negative_space_map|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended'

# SQL-context grep
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+(${SUBC_TABLES})\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | tee /tmp/ws0c_subC_grep.txt

awk -F: '{print $1}' /tmp/ws0c_subC_grep.txt | sort | uniq -c | sort -rn | tee /tmp/ws0c_subC_files.txt
cat /tmp/ws0c_subC_files.txt | head -40

# Group by table — which tables are the worst offenders?
grep -oE "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+(${SUBC_TABLES})\b" /tmp/ws0c_subC_grep.txt \
  | awk '{print $NF}' | sort | uniq -c | sort -rn | tee /tmp/ws0c_subC_tables.txt
cat /tmp/ws0c_subC_tables.txt

# Hotspot dirs
awk -F: '{print $1}' /tmp/ws0c_subC_grep.txt | xargs -I {} dirname {} | sort | uniq -c | sort -rn \
  | head -20 | tee /tmp/ws0c_subC_dirs.txt
```

## C.2 — Disposition table

Build `/tmp/ws0c_subC_disposition.md` — one row per file:

```
| File | Table(s) cited | Reverse-import: live consumers | Disposition | Notes |
|---|---|---|---|---|
| ... | chart_facts | route X, Y | REPOINT → ganita_positions | shape map below |
| ... | l25_msr_signals | none (dead) | DELETE_WHOLESALE | |
| ... | shadbala | route Z | HALT | no Brahma equivalent for shadbala yet |
```

**REPOINT mapping (Brahma equivalents):**
- `chart_facts` (positions slice) → `ganita_positions`
- `chart_facts` (dasha slice) → `ganita_dashas`
- `chart_facts` (varga slice) → `ganita_divisionals` (verify table name with `psql_prod -c "\dt ganita_*"`)
- `chart_facts` (panchanga slice) → `ganita_panchanga`
- `chart_facts` (sensitive points) → `ganita_sensitive_points`
- `chart_facts` (strength: shadbala/ashtakavarga) → `ganita_strength` if it exists, else **HALT** (no equivalent yet)
- `l25_msr_signals` / `msr_signals` → `bodha_signals`
- `l25_cgm_nodes` / `l25_cgm_edges` → `bodha_graph`
- `l25_cdlm_*` → `bodha_domain_links`
- `l25_rm_resonances` → `bodha_resonance`
- `dasha_periods` / `chart_dashas` → `ganita_dashas`
- `pyramid_layers` → kept (recreated by runtime-guardian; live)
- `pattern_register` / `resonance_register` / `rag_chunks` → DELETE (no current Brahma equivalent — these were Discovery Layer + RAG corpus, fully retired)
- `l1_*` chakra tables (`sarvatobhadra`, `sapta_shalaka`, `kalanala`, `kota`, `ckn`, `vedha_extended`, etc.) → DELETE (no current Brahma equivalent; would rebuild in WS-2 if needed)
- `varshaphala` → DELETE or HALT (Tajaka/varsha is a Kāla concern; verify Brahma equivalent before delete)

**HALT decision rule:** If a LIVE route depends on `shadbala` / `varshaphala` / any other table without a clear Brahma equivalent — report to native; do not stub blindly. Sub-B/D/E commits stand; PR opens after the HALT is resolved.

Verify the Brahma table names before any REPOINT edit:
```bash
psql_prod -c "\dt ganita_*"
psql_prod -c "\dt bodha_*"
```

## C.3 — Execute (per-cluster, smallest first)

Order: pure deletes first (lowest risk) → REPOINTs second. Group by directory cluster to minimize cascading typecheck errors.

```bash
# Pure deletes (cluster 1)
git rm <files marked DELETE_WHOLESALE>

# Typecheck after cluster 1
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head -10 && cd ..

# REPOINTs (cluster 2) — use Edit tool per file; swap SQL + import
# After each cluster of REPOINTs, re-run typecheck

# Final residual check
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+(${SUBC_TABLES})\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null | head -5
# Expected: zero, or only the HALTed files if any
```

## C.4 — Commit

```bash
git add -A
git commit -m "chore(ws0c): chart_facts + L1/L2.5 layer-table residuals (Sub-C)

Largest cleanup sub-stream. ~475 SQL citations across checkpoints,
snapshot, tool_metadata, and other paths.

Dispositions:
- chart_facts → repointed to ganita_positions/dashas/divisionals/panchanga
- msr_signals / l25_* synthesis → repointed to bodha_signals/graph/links/resonance
- dasha_periods / chart_dashas → repointed to ganita_dashas
- pattern_register / resonance_register / rag_chunks / l1_chakras → deleted (no Brahma equivalent — Discovery Layer + RAG retired)
- pyramid_layers → kept (live, runtime-guardian recreated)
- [list any HALTed files separately]

K wholesale / L surgical / M repoint / N halt files.

Refs WS-0C"
```

---

# === Final WS-0C AC sweep ===

After Sub-C commit:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# AC-1 (WS-0C definition): SQL-context grep must return zero (or only HALTed files)
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+(${LEGACY_TABLES})\b" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null | tee /tmp/ws0c_final_grep.txt | wc -l

# AC-2: typecheck delta vs Step 0 baseline
cd platform && npm run typecheck 2>&1 | tee /tmp/ws0c_final_typecheck.txt && cd ..
diff /tmp/ws0c_subB_baseline_typecheck.txt /tmp/ws0c_final_typecheck.txt | grep -E "^> .*error TS"
# Expected: empty (no NEW errors)

# AC-3: build (re-attempt — chat-layer fix may have unblocked it)
cd platform && npm run build 2>&1 | tail -20 | tee /tmp/ws0c_final_build.txt && cd ..

# AC-4: pytest
cd platform && python -m pytest python-sidecar/tests/ --ignore=python-sidecar/tests/integration -q 2>&1 | tail -5 && cd ..

# AC-6: route curl smoke (only if AC-3 succeeded)
if grep -q "Compiled successfully" /tmp/ws0c_final_build.txt; then
  cd platform
  npm run start &
  SERVER_PID=$!
  sleep 8
  ROUTES=$(find src/app -type f \( -name 'page.tsx' -o -name 'route.ts' \) \
           | sed 's|src/app||; s|/page\.tsx$||; s|/route\.ts$||' | sort -u)
  FAIL=0
  for route in $ROUTES; do
    CODE=$(curl -s -o /tmp/ws0c_resp.txt -w '%{http_code}' -m 8 "http://localhost:3000${route:-/}")
    case "$CODE" in
      200|301|302|307|401|403|404) ;;
      5*)
        BODY=$(head -c 200 /tmp/ws0c_resp.txt)
        if echo "$BODY" | grep -qE 'relation .* does not exist'; then
          echo "FAIL [$CODE] $route: $BODY"; FAIL=$((FAIL+1))
        fi
        ;;
    esac
  done
  kill $SERVER_PID
  cd ..
  test "$FAIL" -eq 0 && echo "AC-6 PASS" || echo "AC-6 FAIL — $FAIL routes 5xx'd on dropped-table"
fi
```

# === Open the WS-0C PR ===

```bash
git push origin feature/ws0c-residual-purge

gh pr create \
  --base main \
  --head feature/ws0c-residual-purge \
  --title "WS-0C: Residual legacy citation purge (Subs A-EXEC + B + D + E + C)" \
  --body "$(cat <<'EOF'
WS-0C closes the residual legacy citation cleanup that WS-0 + WS-0B + the
hot-patch left in platform/src. Five sub-streams, five commits.

## Commits
- f05d2be6 — Sub-A-EXEC: chat layer fix-forward (8 files)
- <sub-B SHA> — Sub-B: rest of AIOps admin surface (Option A — defer to Mīmāṃsā/L5)
- <sub-D SHA> — Sub-D: predictions table residuals
- <sub-E SHA> — Sub-E: documents table residuals (build-tools.ts)
- <sub-C SHA> — Sub-C: chart_facts + L1/L2.5 layer-table residuals (largest; repoint + delete)

## AC scorecard
| AC | Status |
|---|---|
| AC-1 SQL-context legacy grep | [PASS / N HALTed files] |
| AC-2 typecheck NEW errors | 0 |
| AC-3 production build | [PASS / pre-existing Turbopack symlink — unrelated] |
| AC-4 pytest | PASS |
| AC-5 per-sub-stream commits + findings docs | PASS |
| AC-6 curl smoke | [PASS / blocked by AC-3] |
| AC-7 reverse-citation gates verified per sub-stream | PASS |
| AC-8 CI gates | [pending CI run] |

## Sub-stream details + findings docs in /tmp/ws0c_sub_*_findings.md
EOF
)"
```

**STOP. Do NOT merge. PR-to-main is human-gated.** Native reviews + merges.

```bash
kill $PROXY_PID 2>/dev/null
```

Report back with:
- Each sub-stream's commit SHA.
- The final AC scorecard.
- Any HALT decisions native needs to resolve (most likely in Sub-C).
- PR URL.

---

## Hard stops across all sub-streams

- Any sub-stream's typecheck cascades into new errors outside its target files — halt that sub-stream; do not commit; do not start the next.
- Any reverse-citation gate finds a live route that needs HALT — halt that sub-stream; do not commit; report.
- Sub-C's scheduler-hook check finds a Cloud Run Job, Cloud Scheduler entry, or GitHub Action triggering any of the AIOps endpoints — halt Sub-B; report.
- Any HALT during Sub-C does NOT roll back Sub-B/D/E — those commits stand. Open the PR with their commits and document the Sub-C HALTs in the PR body as `Open` items.
- More than 3 attempts on any single fix.

Begin with Step 0. Report at every commit.
