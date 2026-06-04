---
artifact: CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE_v1_0.md
canonical_id: CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE
version: 1.0
status: READY_FOR_EXECUTION (Sub-A authored; Subs B–E gated on Sub-A findings)
project_codename: Brahma — Residual Legacy Citation Purge (WS-0C)
authored_by: Claude (Cowork) 2026-06-04
authored_for: Claude Code extension running inside Google Antigravity IDE
execution_surface: >
  Claude Code (the extension) in Google Antigravity IDE. CC drives this run from its integrated
  bash terminal + Read/Write/Edit/Grep tools, rooted at `/Users/Dev/Vibe-Coding/Apps/Madhav`. Every
  command paste-ready into CC's bash. Prod DB access via `platform/scripts/start_db_proxy.sh`.
follows: CLAUDECODE_BRIEF_WS0B_CODE_CLUSTER_PURGE_v1_0.md (PR #206; tag `legacy-code-cluster-purge-complete`)
native_approved: true  # native confirmed 2026-06-04 — "Yes"
no_backup: true        # forward-only; commits are the audit trail
context: >
  PR #206 verification (table-existence sweep) confirmed ~509 of 1,202 residual LEGACY_TABLES
  citations in `platform/src` are REAL dead-code references to tables WS-0 dropped — not false
  positives. Largest surfaces: `messages` (433 hits in conversations.ts), `chart_facts` (~475 in
  checkpoints/snapshot/tool_metadata), `predictions` (122), `llm_stack_routing_override/_config_audit/_param_override`
  (29 — the rest of the AIOps admin surface the hot-patch didn't reach), `documents` (19 in build-tools.ts).
  Five sub-streams; audit-first; reverse-citation gate per the durable rule.
acceptance_criteria:
  - "AC-1: Full LEGACY_TABLES grep across platform/src returns ≤ the documented-false-positive count from the over-match analysis (i.e., real SQL citations to dropped tables = 0)"
  - "AC-2: `npm run typecheck` exits with zero NEW errors vs pre-WS-0C baseline"
  - "AC-3: `npm run build` exits 0 OR the failure is the documented pre-existing Turbopack symlink issue"
  - "AC-4: `python -m pytest platform/python-sidecar/tests/ --ignore=platform/python-sidecar/tests/integration` exits 0"
  - "AC-5: For each sub-stream (A-E), an audit doc exists at /tmp/ws0c_sub_<X>_findings.md and a commit-per-sub-stream lands on the branch"
  - "AC-6: Curl smoke on every route under platform/src/app returns 200/3xx/4xx — zero 5xx from import resolution or SQL execution"
  - "AC-7: All sub-streams' destructive ops verified by reverse-citation gate before commit (no orphan importer left behind)"
  - "AC-8: PR opened; six CI gates green (typecheck, unit-tests, secret-scan, naming-lint, governance-gates, planner-regression)"
may_touch:
  - "platform/src/**"  # this is the cleanup scope
  - "platform/scripts/**"  # straggler scripts
  - "platform/package.json"  # if scripts entries reference deleted files
  - "00_ARCHITECTURE/BRAHMA_DEFERRED_FEATURES.md"  # append per disposition
must_not_touch:
  - "platform/python-sidecar/brahmagyan/**"  # Brahma engine
  - "platform/python-sidecar/ganita/**"
  - "platform/python-sidecar/bodha/**"
  - "platform/python-sidecar/kala/**"
  - "platform/python-sidecar/phala/**"
  - "platform/python-sidecar/mimamsa/**"
  - "platform-mcp/**"
  - "platform/supabase/migrations/**"  # frozen history
  - "01_FACTS_LAYER/**"
  - "00_ARCHITECTURE/**"  # except BRAHMA_DEFERRED_FEATURES.md per may_touch
  - ".github/workflows/**"
  - "CAPABILITY_MANIFEST.json"
project_facts:
  gcp_project: madhav-astrology
  region: asia-south1
  prod_url: madhav.marsys.in
  branch: feature/ws0c-residual-purge
  predecessor_tag: legacy-code-cluster-purge-complete
---

# CLAUDECODE_BRIEF — WS-0C Residual Legacy Citation Purge

## §1 Mission

Eliminate the ~509 real dead-code citations to dropped legacy tables that remain in `platform/src` after WS-0B + the hot-patch. The cleanup is partitioned into five sub-streams by table-name surface; each follows an **audit-first** pattern — every destructive action is gated by a verified reverse-citation finding, never by a hand-list assertion. Per the durable rule from WS-0: *source-of-truth kill lists are not evidence; live code grep is.*

**Execution context — Claude Code extension in Google Antigravity IDE.** All commands paste-ready into CC's integrated bash. Repo root `/Users/Dev/Vibe-Coding/Apps/Madhav`.

**Branch:** `feature/ws0c-residual-purge` cut from `main` at tag `legacy-code-cluster-purge-complete`. Per-sub-stream commits so any sub-stream is independently revertable.

---

## §1a Prerequisites

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Confirm WS-0B is merged and tagged
git fetch origin --tags
git tag -l 'legacy-code-cluster-purge-complete'   # expected: present
git log --oneline -3 main

# Cut WS-0C branch from the WS-0B sealing tag
git checkout -b feature/ws0c-residual-purge legacy-code-cluster-purge-complete

# Start the Cloud SQL Auth Proxy in the background (port 5433)
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql "$PROD_DB_URL" -c "SELECT current_database(), now();" || { echo "Proxy failed"; exit 1; }

psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }

# Capture baselines for diffing later
cd platform
npm run typecheck 2>&1 | tee /tmp/ws0c_typecheck_baseline.txt
cd ..

# Reuse the LEGACY_TABLES alternation
export LEGACY_TABLES='audit_job_runs|ayanamsha_registry|build_checkpoints|build_dependencies|build_engine_versions|build_manifests|build_notifications|chart_ayanamsha_reports|chart_dashas|chart_documents|chart_facts|chart_facts_history|chart_facts_staging|chart_facts_supersedence|chat_attachments|classical_attributions|classical_chunks|classical_texts|cluster_register|cluster_register_staging|context_assembly_log|contradiction_register|contradiction_register_staging|convergence_scores|data_source_expected|dasha_periods|divisional_charts|documents|eclipses|eclipses_retrogrades|eclipses_staging|engine_versions|ephemeris_daily|ephemeris_daily_staging|g29_timing_rules|gate_change_log|kp_sublords|l1_bhrigu_bindu_transits|l1_ckn_chakra|l1_graha_aspects_lifetime|l1_kalanala_chakra|l1_kota_chakra|l1_phase_locked_anchors|l1_sapta_shalaka|l1_sarvatobhadra_positions|l1_sarvatobhadra_vedha|l1_tajik_varsha_year_lords|l1_time_synchronicity|l1_varsha_digest|l1_vedha_extended|l25_cdlm_cells|l25_cdlm_cells_staging|l25_cdlm_links|l25_cdlm_links_staging|l25_cgm_edges|l25_cgm_edges_staging|l25_cgm_nodes|l25_cgm_nodes_staging|l25_chart_lattice_snapshots|l25_derivation_graph_edges|l25_derivation_graph_nodes|l25_divergence_ledger|l25_msr_signals|l25_msr_signals_staging|l25_negative_space_map|l25_pattern_catalog|l25_rm_resonances|l25_rm_resonances_staging|l25_ucn_digests|l25_ucn_digests_staging|l25_ucn_sections|l25_ucn_sections_staging|l25_vedha_anchor_interactions|llm_catalog_snapshot|llm_config_audit|llm_model_health|llm_param_override|llm_stack_routing_override|mcp_audit_findings|mcp_bundle_cache|message_feedback|messages|msr_signals|multi_school_stances|notification_views|panchanga_daily|panchanga_daily_staging|pattern_register|pattern_register_staging|prediction_ledger|predictions|pyramid_layers|query_plans|rag_chunks|rag_chunks_staging|rag_embeddings|rag_embeddings_staging|rag_feedback|rag_graph_edges|rag_graph_nodes|rag_queries|rag_reproducibility_failures|rag_retrievals|resonance_register|resonance_register_staging|retrogrades|retrogrades_staging|sade_sati_cycles|sade_sati_phases|sade_sati_phases_staging|sankranti_table|saturn_sign_changes|school_analysis_runs|school_convergence_index|school_disagreements|school_signal_coverage|shadbala|signal_states|tajaka_annual|tool_caveats|varshaphala'

# Closeout (at end of run):
#   kill $PROXY_PID
```

---

## §2 Sub-stream overview

Five sub-streams, in order. **Sub-A is investigation-only** — the chat-layer triage outcome shapes how Subs B-E handle their disposition. Do NOT delete anything in Sub-A.

| Sub | Surface | Hits | Disposition Pattern (provisional, refined by Sub-A) |
|---|---|---|---|
| **A** | `messages` in `conversations.ts` (chat layer) | 433 | Investigation-only. Determine: dead / alive-with-fallback / silently-broken. Output: `/tmp/ws0c_sub_a_findings.md`. |
| **B** | `llm_stack_routing_override`, `llm_config_audit`, `llm_param_override` (AIOps admin) | 29 | Same as Option A from WS-0B hot-patch — delete the rest of the AIOps admin surface; append entry to `BRAHMA_DEFERRED_FEATURES.md`. |
| **C** | `chart_facts` + `divisional_charts`, `varshaphala`, `shadbala`, `dasha_periods`, `chart_dashas`, `l25_*`, `msr_signals`, `pattern_register`, `resonance_register`, `rag_chunks`, `pyramid_layers`, `l1_*` (build / governance / tool_metadata) | ~475 | Per-file disposition: re-point to Brahma equivalent if reachable from a Brahma-active surface; delete if pure dead code. |
| **D** | `predictions` residuals beyond what WS-0B's prediction cluster purged | 122 | Reverse-citation gate, then delete each file. The WS-0B prediction cluster purge missed these. |
| **E** | `documents` in `build-tools.ts` (8 SQL queries) + any other residual | 19 | Reverse-citation gate, then delete or re-point. `documents` is v1 messaging era. |

**Authoring sequence:** Sub-A paste prompt ships with this brief. Subs B-E paste prompts ship after Sub-A's findings doc is reviewed.

---

## §3 Standard sub-stream workflow (Subs B-E template)

Every destructive sub-stream follows this pattern. Sub-A skips Step 3 (it's investigation-only).

### Step 1 — Surface enumeration

```bash
# Grep just THIS sub-stream's tables. Define SUBSTREAM_TABLES per sub-stream.
export SUBSTREAM_TABLES='<sub-stream-specific alternation>'

grep -rEn "(${SUBSTREAM_TABLES})" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null \
  | tee /tmp/ws0c_sub_${SUB}_grep.txt

# Group by file
awk -F: '{print $1}' /tmp/ws0c_sub_${SUB}_grep.txt | sort | uniq -c | sort -rn \
  | tee /tmp/ws0c_sub_${SUB}_files.txt
```

### Step 2 — Per-file reverse-citation audit + disposition

For each file in the enumeration, classify:

| Reachability state | Disposition |
|---|---|
| **No outside importer** AND file is sole-purpose legacy | DELETE_WHOLESALE |
| **Only importers are other already-dead files** | DELETE_WITH_CONSUMERS |
| **Reachable from a Brahma-active route, but legacy table has a Brahma equivalent** | REPOINT |
| **Reachable from a Brahma-active route, table has NO Brahma equivalent** | HALT — report to native; possibly stub + defer to BRAHMA_DEFERRED_FEATURES.md |
| **Reachable from a route that's itself legacy (deletable)** | DELETE_WITH_ROUTE |

Write `/tmp/ws0c_sub_${SUB}_disposition.md` capturing the call per file. **Pause here for any HALT classification.**

### Step 3 — Execute the dispositions

```bash
# DELETE_WHOLESALE / DELETE_WITH_CONSUMERS / DELETE_WITH_ROUTE
# git rm each file (and its test if it has one)

# REPOINT
# Edit each file, swap the SQL query to the Brahma equivalent

# After each disposition group: typecheck
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head && cd ..
```

### Step 4 — Sub-stream commit

```bash
git add -A
git commit -m "chore(ws0c): Sub-${SUB} — <one-line summary>

Surface: <table names>
Hits resolved: <N>
Dispositions: <K wholesale / L with-consumers / M repoint / N halt>
AC-1 contribution: <N citations removed from the legacy grep>

Refs WS-0C"
```

### Step 5 — Mid-stream AC sweep

After each sub-stream commit, run the partial AC sweep to confirm no regression:
```bash
grep -rEn "(${LEGACY_TABLES})" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null | wc -l
# Should decrease by the sub-stream's hit count after each commit
```

---

## §4 Sub-A — `messages` chat-layer triage (investigation only)

The 433 hits sit primarily in `conversations.ts`. The chat surface (R7–R10) is supposedly live. Three possible states need disambiguation BEFORE any deletion or re-point:

- (a) `conversations.ts` is fully dead — the live chat uses different files (`conversation_messages.ts`, etc.). DELETE pattern in a later commit.
- (b) `conversations.ts` is alive with fallback handling that masks the missing `messages` table. INVESTIGATE the fallback path; decide whether to delete fallback or fix forward.
- (c) `conversations.ts` is silently broken — `messages` queries throw at runtime but the consume chat surface compensates with caught exceptions / empty arrays / etc. FIX FORWARD or DELETE depending on consumer.

**Sub-A's output:** `/tmp/ws0c_sub_a_findings.md` documenting which of (a)/(b)/(c) is true, with evidence. The disposition for `conversations.ts` (delete vs re-point vs surgical fix) is decided AFTER Sub-A closes — not during it.

**Sub-A paste prompt:** `ANTIGRAVITY_PASTE_WS0C_SUB_A_CHAT_TRIAGE.md` ships with this brief.

---

## §5 Subs B–E — paste prompts gated on Sub-A

After Sub-A's findings doc lands, Cowork authors:

- `ANTIGRAVITY_PASTE_WS0C_SUB_B_AIOPS_REMAINING.md` — delete the three remaining AIOps admin routes (`/api/admin/aiops/routing`, `/config`, `/params`-like patterns), reuse the WS-0B hot-patch Option A pattern.
- `ANTIGRAVITY_PASTE_WS0C_SUB_C_CHART_FACTS_REPOINT.md` — the largest sub-stream; per-file disposition table likely; reuses `query_chart_facts` re-point pattern from `ganita_*` set.
- `ANTIGRAVITY_PASTE_WS0C_SUB_D_PREDICTIONS_RESIDUAL.md` — predictions-cluster cleanup the WS-0B purge missed; mostly DELETE.
- `ANTIGRAVITY_PASTE_WS0C_SUB_E_DOCUMENTS.md` — `documents` in build-tools.ts; likely DELETE.

If Sub-A reveals the chat layer needs a surgical fix (state c), Cowork inserts a `ANTIGRAVITY_PASTE_WS0C_SUB_A_FIX.md` before Sub-B.

---

## §6 Final WS-0C AC sweep (after all sub-streams commit)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# AC-1: legacy grep — only false-positive substring matches should remain
# (the documented over-match on `messages`/`documents` as English words / property names).
# Compute the expected residual = total over-match count from PR #206 analysis.
grep -rEn "(${LEGACY_TABLES})" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null | tee /tmp/ws0c_final_grep.txt | wc -l

# Word-boundary SQL-context grep — this MUST return zero
grep -rEn "\b(FROM|INTO|UPDATE|DELETE FROM)\s+(${LEGACY_TABLES})\b" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null

# AC-2: typecheck no new errors
cd platform && npm run typecheck 2>&1 | tee /tmp/ws0c_final_typecheck.txt && cd ..
diff /tmp/ws0c_typecheck_baseline.txt /tmp/ws0c_final_typecheck.txt | grep -E "^> .*error TS"

# AC-3: build
cd platform && npm run build 2>&1 | tail -20 && cd ..

# AC-4: pytest
cd platform && python -m pytest python-sidecar/tests/ --ignore=python-sidecar/tests/integration -q 2>&1 | tail -5 && cd ..

# AC-6: route curl smoke (same pattern as WS-0B)
cd platform
npm run start &
SERVER_PID=$!
sleep 5
ROUTES=$(find src/app -type f \( -name 'page.tsx' -o -name 'route.ts' \) \
         | sed 's|src/app||; s|/page\.tsx$||; s|/route\.ts$||' | sort -u)
FAIL=0
for route in $ROUTES; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:3000${route:-/}")
  case "$CODE" in
    200|301|302|307|401|403|404) ;;
    5*) echo "FAIL [$CODE] $route"; FAIL=$((FAIL+1)) ;;
  esac
done
kill $SERVER_PID
cd ..
test "$FAIL" -eq 0 && echo "AC-6 PASS" || echo "AC-6 FAIL — $FAIL routes 5xx'd"
```

---

## §7 Commit discipline + PR

- One commit per sub-stream from §3 Step 4.
- After AC-1 word-boundary grep = 0 AND AC-2/AC-4 green → tag the head: `git tag legacy-residual-purge-complete && git push origin legacy-residual-purge-complete`.
- Open PR `feature/ws0c-residual-purge → main` with the per-sub-stream commit list + final AC scorecard in the description.
- **PR-to-main is human-gated.** CC opens the PR, native reviews + merges.

---

## §8 Out of WS-0C scope

| # | Item | Follow-up |
|---|------|-----------|
| 1 | Documented over-match false positives (e.g., `documents` as a JS property name, `messages` as a chat-export variable) | WS-0D micro-patch to tighten the alternation, OR accept as known residual in `KNOWN_PRE_EXISTING_FAILURES.md` |
| 2 | Turbopack symlink build issue | Bundler tooling ticket; not legacy-related |
| 3 | GCS bucket purge | WS-0E separate brief |
| 4 | `CAPABILITY_MANIFEST.json` legacy entries | M5 governance re-base |
| 5 | Historical migration squash | After WS-2 |

---

## §9 If you find something unexpected

- A sub-stream's enumeration surfaces a table name NOT in any §2 sub-stream (e.g., a citation to `eclipses_retrogrades` showing up in lib code) → add a Sub-F line item; do not extend an existing sub-stream's scope.
- A LIVE route in `app/api/` you didn't expect ends up needing REPOINT and the Brahma equivalent is unclear → HALT for native call; do not stub blindly.
- The chat layer (Sub-A) reveals a third surface beyond `conversations.ts` (e.g., `messages` cited in `chat-export.ts` or similar) → fold into Sub-A's findings, do not delete during Sub-A.

The principle from WS-0B holds: **leave platform/src cleaner than you found it**, not "barely past the AC gate."

---

*End of CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE v1.0. Sub-A paste prompt ships with this brief at `ANTIGRAVITY_PASTE_WS0C_SUB_A_CHAT_TRIAGE.md`. Subs B-E paste prompts authored after Sub-A's findings doc.*
