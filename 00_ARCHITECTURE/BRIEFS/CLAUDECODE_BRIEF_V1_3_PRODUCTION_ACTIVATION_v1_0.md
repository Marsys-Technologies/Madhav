---
artifact: CLAUDECODE_BRIEF_V1_3_PRODUCTION_ACTIVATION_v1_0.md
canonical_id: CLAUDECODE_BRIEF_V1_3_PRODUCTION_ACTIVATION
version: 1.0
status: READY_FOR_EXECUTION
project_codename: Brahma — V1.3 Production Activation (gap closure between worktree-complete and prod-complete)
authored_by: Claude (Cowork) 2026-06-05
authored_for: Claude Code in Antigravity — Conductor mode (5 streams; Stream 1 sequential gate, 2-5 parallel)
governs_under: BUILD_GUARANTOR_SWARM_CHARTER + AUTONOMOUS_MODE + AUTONOMY_RESILIENCE_PATTERN
predecessor: BRAHMA_V1_3_COMPLETE.md (Cowork close-out; NOT tagged on main yet)
worktrees: MadhavProd1, MadhavProd2, MadhavProd3, MadhavProd4, MadhavProd5
no_backup: true
human_gates: NONE (per AUTONOMY_RESILIENCE_PATTERN — Tier-3 catastrophic-runaway cap only)
binding_discipline: see §2 (every AC verifies against prod)
context: >
  V1.3 wave seals (BRAHMA_FOUR_WAVE_COMPLETE + POSTDEPLOY_FIVE_STREAM_COMPLETE) reported "instrument
  built" with rich per-layer counts. Native diagnostic 2026-06-05 surfaced massive divergence: the
  waves built + tested in worktrees but never deployed application-layer schema or seed data to
  production. Portal broken on missing pyramid_layers. This arc closes the gap, then tags
  brahma-v1-3-production-live (NOT brahma-v1-3-complete — the prior tag idea is retired per
  native directive 2026-06-05 evening).
---

# CLAUDECODE_BRIEF — V1.3 Production Activation

The autonomous wave seals reported "built" against worktree state; prod state diverged. This arc deploys what was built, verifies against prod (not worktree), and only tags V1.3 when production actually matches the claimed instrument state.

**Execution context — Claude Code extension in Google Antigravity IDE.** Repo root `/Users/Dev/Vibe-Coding/Apps/Madhav`. Single-paste master launch; 5 streams (Stream 1 sequential gate, Streams 2-5 parallel after Stream 1 closes).

## §1 Mission — close the seal-vs-prod gap

The prior arc's failure mode: ACs verified the swarm's worktree DB, not prod. This arc inverts that — every AC verifies prod explicitly via `psql "$PROD_DB_URL"`, `curl https://madhav.marsys.in/...`, `gh api`, or `gcloud`. The wave-close discipline: **no tag without a final prod gate that re-runs the native's diagnostic and confirms zero divergence vs the claimed instrument state.**

The instrument target (what prod must show before V1.3 ships):
- L0: 7 assets, full ephemeris 1900-2100 × 9 bodies (~8M rows), remedy corpus ≥50, classical text chunks present, reference/ontology/almanac populated
- L1: 9 assets per chart (5 ayanamshas × 9 grahas = 45 positions per chart minimum; full divisionals/dashas/strength/sensitive_points/panchanga)
- L2: 569 grounded signals, 110 CGM edges, 81 CDLM cells, 569 multipliers
- L3: 893 timeline rows, 23 convergence windows, 17 obstructions per chart
- L4: 25 anchors with falsifiers + mitigation + muhurta surfaces
- L5: 56 LEL events ingested (per native diagnostic; not 57 — the trailing-dot artefact), event_chart_state_index populated, calibration substrate live
- Portal: dashboard + cockpit + admin/foundation all return 200 (or 4xx with valid auth/notfound); no 5xx

## §2 The verify-against-prod discipline (binding)

Every AC in this brief is written in the form:

> `<measurable thing>` **[verify-against: prod]** **[via: psql_prod | curl_prod | gh api | gcloud | docker]**

The swarm's session can pass internal worktree tests, but the AC is only satisfied when the verify-against:prod check returns the expected result. Streams that complete their internal work but fail their prod gate **do not tag** — they spawn a delta-deploy session under AUTONOMY_RESILIENCE_PATTERN §B.1 (deep-fix escalation) to close the prod gap, then re-run the prod gate.

Vimarśaka role amended in this brief: audits run against prod, not worktree. If Vimarśaka can't reach prod (e.g., proxy down), it surfaces "cannot-verify" as a Tier-2 Smṛti entry rather than silent-passing.

## §3 The five streams

Stream 1 is the sequential gate — its output (the PR-disposition register + the migration inventory) feeds the other four. Streams 2-5 are fully parallel after Stream 1 closes.

| Stream | Scope | Worktree | Branch | Budget cap |
|---|---|---|---|---|
| **1 — PR Triage + Migration Inventory** | Classify 22 open PRs (MERGE_NOW / MERGE_WITH_REBASE / CLOSE_STALE / KEEP_OPEN); inventory every `CREATE TABLE` in main + open branches; build topological migration apply order | `MadhavProd1` | `feature/v13-prod-triage` | $400 |
| **2 — Migration Apply** | Apply every application-layer migration from Stream 1's inventory to prod (single-transaction, post-apply verify per migration) | `MadhavProd2` | `feature/v13-prod-migrations` | $400 |
| **3 — Data Writer Execution** | Run every writer + seeder against prod for the native's chart (482012f1-…); verify each layer's volume against floor | `MadhavProd3` | `feature/v13-prod-data` | $800 |
| **4 — Portal Fix + Verify** | Diagnose every 5xx route via curl; fix at source; verify zero 5xx across all routes under app/ | `MadhavProd4` | `feature/v13-prod-portal` | $500 |
| **5 — LEL Ingest** | Parse `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`; ingest into `mimamsa_lel_events`; verify count = 56 unique EVT IDs; build event_chart_state_index | `MadhavProd5` | `feature/v13-prod-lel` | $200 |

Total wave ceiling: $2.3k (sum of stream caps); $5k absolute per AUTONOMY_RESILIENCE_PATTERN.

## §4 Per-stream specifications

### §4.1 Stream 1 — PR Triage + Migration Inventory (sequential gate)

This stream must close before 2-5 launch. Its outputs are inputs to 2-5.

**Substream 1.A — PR triage**

For each of the 22 open PRs (run `gh pr list --base main --state open --limit 30`):

```bash
classify_pr() {
  local pr_num=$1
  # Fetch PR metadata, diff stats, last commit date, CI status, branch name
  gh pr view $pr_num --json title,body,headRefName,additions,deletions,changedFiles,statusCheckRollup,updatedAt

  # Decision rules:
  #   MERGE_NOW       — diff is in scope of V1.3 (fixes a known prod gap), CI green or fixable, no conflicts with main
  #   MERGE_WITH_REBASE — diff is in scope, but needs rebase against current main first
  #   CLOSE_STALE     — diff is superseded by later work OR last update >14 days OR explicitly abandoned in PR body
  #   KEEP_OPEN       — work-in-progress that should continue in its own arc post-V1.3
}
```

The classifier (LLM-driven per AUTONOMY_RESILIENCE_PATTERN §B.2 autonomous disposition classifier) outputs `/tmp/v13_pr_triage.md` with one row per PR + reasoning. Confidence < 0.6 defaults to KEEP_OPEN (preserves work, doesn't risk wrong closes). Each decision logs to Smṛti.

**Per-classification action (autonomous per native authorization):**
- MERGE_NOW → `gh pr merge <num> --squash --auto`
- MERGE_WITH_REBASE → spawn a delta session that rebases the branch + re-runs CI + auto-merges
- CLOSE_STALE → `gh pr close <num> --comment "Closed during V1.3 production activation triage. Reason: <classifier rationale>. Reopenable."`
- KEEP_OPEN → no action; logged for native review

**AC 1.A:** `gh pr list --base main --state open` returns ≤ 5 PRs after Stream 1 closes (the KEEP_OPEN set; size depends on real classifications). **[verify-against: prod]** **[via: gh api]**

**Substream 1.B — Migration inventory**

```bash
# Find every CREATE TABLE statement across main + every open branch
git fetch origin --all --tags --prune
for branch in main $(git branch -r | grep origin/feature | sed 's|origin/||'); do
  git ls-tree -r "$branch" --name-only \
    | grep -E '\.(sql|py)$' \
    | xargs -I {} git show "$branch:{}" 2>/dev/null \
    | grep -B 1 -i "CREATE TABLE" \
    > "/tmp/v13_migrations_${branch//\//_}.txt"
done

# Inventory: which tables exist in which branch, which dependencies (FK + sequencing)
# Output: /tmp/v13_migration_apply_order.md with topologically sorted list
```

**AC 1.B:** `/tmp/v13_migration_apply_order.md` exists with every Brahma-era migration listed in apply order, dependencies marked. **[verify-against: prod]** **[via: file existence]**

Stream 1 tag: `v13-prod-triage-complete`.

---

### §4.2 Stream 2 — Migration Apply (parallel after Stream 1)

Consumes `/tmp/v13_migration_apply_order.md`. For each migration in apply order:

```bash
apply_v13_migration() {
  local mig_path=$1
  local mig_id=$(basename "$mig_path" .sql)

  # Pre-check: already applied?
  local applied=$(psql_prod -At -c "SELECT count(*) FROM supabase_migrations.schema_migrations WHERE version = '$mig_id'")
  if [ "$applied" -gt 0 ]; then
    echo "SKIP $mig_id — already applied"
    return 0
  fi

  # Apply single-transaction
  psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 --single-transaction -f "$mig_path"

  # Record in tracker if not auto-recorded
  psql_prod -c "INSERT INTO supabase_migrations.schema_migrations (version) VALUES ('$mig_id') ON CONFLICT DO NOTHING"

  # Post-apply verify: each promised table exists
  # (parse the migration for CREATE TABLE statements; verify each via \dt)
}
```

**AC 2:** every migration in `/tmp/v13_migration_apply_order.md` is recorded in `supabase_migrations.schema_migrations` AND every `CREATE TABLE` target appears in `information_schema.tables`. **[verify-against: prod]** **[via: psql_prod]**

Stream 2 tag: `v13-prod-migrations-applied`.

---

### §4.3 Stream 3 — Data Writer Execution (parallel)

Depends on Stream 2 partial — each writer only runs after its target tables exist (Stream 3 polls per-table existence; runs writers as their dependencies clear).

```bash
# Per-layer writer execution against the native's chart
CHART_ID="482012f1-..."  # native's chart id (full from diagnostic)

# L0 writers
python -m brahmagyan.ephemeris.build_ephemeris --start 1900-01-01 --end 2100-12-31
python -m brahmagyan.remedy_corpus.seed
python -m brahmagyan.text_index.build  # populates classical_text_chunks
python -m brahmagyan.reference.seed
python -m brahmagyan.ontology.seed
python -m brahmagyan.almanac.build

# L1 writers (run against the native's chart)
python -m brahmagyan.ganita.run --chart-id $CHART_ID --all-ayanamshas

# L2 writers
python -m brahmagyan.bodha.signals --chart-id $CHART_ID
python -m brahmagyan.bodha.graph --chart-id $CHART_ID
python -m brahmagyan.bodha.domain_links --chart-id $CHART_ID
python -m brahmagyan.bodha.resonance --chart-id $CHART_ID

# L3 writers
python -m brahmagyan.kala.timeline --chart-id $CHART_ID
python -m brahmagyan.kala.convergence --chart-id $CHART_ID

# L4 writers
python -m brahmagyan.phala.anchors --chart-id $CHART_ID
python -m brahmagyan.phala.mitigation --chart-id $CHART_ID
python -m brahmagyan.phala.muhurta --chart-id $CHART_ID

# L5 — coordinated with Stream 5 LEL ingest
python -m brahmagyan.mimamsa.event_chart_state_index --chart-id $CHART_ID
python -m brahmagyan.mimamsa.calibration_substrate
```

Per-writer prod verification (each writes a Smṛti entry with actual vs expected count):

| Asset | Target floor | Verify SQL |
|---|---|---|
| ephemeris_daily | 8M+ rows (1900-2100 × 9 bodies × ~365 days) | `SELECT count(*) FROM ephemeris_daily` |
| brahma_remedy_corpus | ≥50 | `SELECT count(*) FROM brahma_remedy_corpus` |
| classical_text_chunks | ≥1000 (BPHS chapters alone) | `SELECT count(*) FROM classical_text_chunks` |
| ganita_positions (chart) | 45 (5 ayanamshas × 9 grahas) | `SELECT count(*) FROM ganita_positions WHERE chart_id = $1` |
| ganita_divisionals (chart) | 60 (D1-D60) | `SELECT count(*) FROM ganita_divisionals WHERE chart_id = $1` |
| ganita_dashas (chart) | 819 (Vimshottari L1+L2+L3 Sukshma depth) | `SELECT count(*) FROM ganita_dashas WHERE chart_id = $1` |
| bodha_signals (chart) | 569 | `SELECT count(*) FROM bodha_signals WHERE chart_id = $1` |
| bodha_graph (chart) | 110 edges | `SELECT count(*) FROM bodha_graph WHERE chart_id = $1` |
| bodha_domain_links (chart) | 81 | `SELECT count(*) FROM bodha_domain_links WHERE chart_id = $1` |
| kala_timeline (chart) | 893 | `SELECT count(*) FROM kala_timeline WHERE chart_id = $1` |
| kala_convergence (chart) | 23 | `SELECT count(*) FROM kala_convergence WHERE chart_id = $1` |
| phala_anchors (chart) | 25 | `SELECT count(*) FROM phala_anchors WHERE chart_id = $1` |
| event_chart_state_index | 56 (after Stream 5) | `SELECT count(*) FROM event_chart_state_index` |

Where actual < floor → AMBER, log to Smṛti, run delta session to close gap, re-verify. Where the floor genuinely can't be reached (e.g., a writer is missing for a table), park + escalate per AUTONOMY_RESILIENCE_PATTERN §B.1.

**AC 3:** every floor in the table above met or AMBER+documented in Smṛti. **[verify-against: prod]** **[via: psql_prod]**

Stream 3 tag: `v13-prod-data-populated`.

---

### §4.4 Stream 4 — Portal Fix + Verify (parallel)

Depends on Stream 2 (migrations) for `pyramid_layers` and friends.

```bash
# 1. Enumerate every route in app/
ROUTES=$(find platform/src/app -type f \( -name 'page.tsx' -o -name 'route.ts' \) \
  | sed 's|platform/src/app||; s|/page\.tsx$||; s|/route\.ts$||' | sort -u)

# 2. For each, curl against prod with a valid session cookie
SESSION_COOKIE="<paste your __session value or have Stream 4 mint one>"

declare -a FIVE_HUNDRED=()
for r in $ROUTES; do
  # Substitute stub IDs for [id] / [slug] segments
  REAL=$(echo "$r" | sed 's|\[id\]|482012f1-95a5-490b-a5a7-027d3e0efda0|; s|\[slug\]|test|; s|\[conversationId\]|test-conv|')
  CODE=$(curl -s -o /tmp/v13_resp.html -w "%{http_code}" \
    -H "Cookie: __session=$SESSION_COOKIE" \
    "https://madhav.marsys.in${REAL}")
  case "$CODE" in
    200|301|302|307|401|403|404) ;;  # acceptable
    5*)
      ERROR=$(head -c 500 /tmp/v13_resp.html | tr '\n' ' ')
      echo "FAIL [$CODE] $REAL : $ERROR"
      FIVE_HUNDRED+=("$REAL")
      ;;
  esac
done

# 3. For each FIVE_HUNDRED, pull Cloud Run logs to capture the actual error
for r in "${FIVE_HUNDRED[@]}"; do
  echo "=== Logs for $r ==="
  gcloud run services logs read amjis-web --region=asia-south1 --limit=10 \
    --format="value(textPayload)" | grep -iE "error|exception|fail" | head -5
done

# 4. Fix at source: pyramid_layers gap likely accounts for most. Other 5xx → triage individually.
# 5. Re-curl after each fix; iterate until FIVE_HUNDRED is empty.
```

**AC 4:** every route under `app/` returns 200/3xx/4xx (no 5xx) when curled with a valid session cookie. **[verify-against: prod]** **[via: curl_prod]**

Stream 4 tag: `v13-prod-portal-verified`.

---

### §4.5 Stream 5 — LEL Ingest (parallel)

Depends on Stream 2 (mimamsa_lel_events schema) but otherwise independent.

```bash
# 1. Parse the LEL markdown source-of-truth
# 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md
# Use the existing intake script if present; else author + run inline.
python -m brahmagyan.mimamsa.lel_ingest \
  --source 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md \
  --target-table mimamsa_lel_events \
  --strict-evt-id-uniqueness

# 2. Verify count
psql_prod -c "SELECT count(*) FROM mimamsa_lel_events;"
# Expected: 56 (per native diagnostic; one trailing-dot variant gets canonicalized)

# 3. Verify event IDs match the file
psql_prod -c "SELECT event_id FROM mimamsa_lel_events ORDER BY event_date;" > /tmp/v13_db_evt.txt
grep -oE "EVT\.[A-Z0-9._]+" 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md | sort -u > /tmp/v13_file_evt.txt
diff /tmp/v13_db_evt.txt /tmp/v13_file_evt.txt
# Expected: no diff
```

**AC 5:** `mimamsa_lel_events` row count = 56 AND every event_id in DB matches an EVT.* token in the source file. **[verify-against: prod]** **[via: psql_prod + file diff]**

Stream 5 tag: `v13-prod-lel-ingested`.

---

## §5 Final V1.3 production-live gate (wave-close session, sequential after Streams 2-5)

A single session that re-runs the native's full diagnostic and refuses to tag unless every line matches the claimed instrument state.

```bash
# Re-execute the native's 2026-06-05 diagnostic queries verbatim.
# Compare each line against the V1.3 instrument target from §1 of this brief.
# Tag only on full match.

python platform/scripts/governance/v13_production_gate.py \
  --target-spec 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_V1_3_PRODUCTION_ACTIVATION_v1_0.md \
  --gate-section "§1 instrument target" \
  --output /tmp/v13_final_gate.md

# If /tmp/v13_final_gate.md reports zero divergences → tag.
if grep -q "^PROD GATE: PASS$" /tmp/v13_final_gate.md; then
  git tag -a brahma-v1-3-production-live-2026-06-XX \
    -m "Brahma V1.3 — production-live (prod state matches claimed instrument state per BRAHMA_V1_3_PRODUCTION_ACTIVATION final gate)"
  git push origin brahma-v1-3-production-live-2026-06-XX
else
  echo "GATE FAIL — divergences:"
  cat /tmp/v13_final_gate.md
  # Spawn delta-deploy session per the divergences; re-run gate; iterate.
fi
```

**AC FINAL:** `brahma-v1-3-production-live-*` tag exists on main AND `/tmp/v13_final_gate.md` reports `PROD GATE: PASS`. **[verify-against: prod]** **[via: git tag list + file existence]**

## §6 Hard stops — none synchronous

Per `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`. Only Tier-3 (catastrophic-runaway $5k absolute ceiling — but per-stream caps in §3 are smaller) emits async notification. Every other event auto-resolves or routes through Tier-2 with Smṛti logging.

The wave-close prod gate is **not** a hard stop — it's a wave-completion criterion. If it fails, a delta-deploy session spawns automatically per AUTONOMY_RESILIENCE_PATTERN §B.1 deep-fix escalation; only the absolute spend ceiling can stop the loop.

## §7 must_not_touch (per-stream)

Standard Brahma protection set + per-stream additions:

- All streams: must_not_touch `01_FACTS_LAYER/**`, `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md`, this brief, the prior seal artifacts
- Stream 1: classifier output goes to `/tmp/`; only `gh` commands touch the PR state
- Stream 2: only `psql_prod` + migration files; no source-tree changes outside the migration tracker
- Stream 3: only writer execution + Smṛti logs; no source-tree changes
- Stream 4: code changes only in the specific files identified by the 5xx triage; no broad refactors
- Stream 5: only the LEL ingest script + the target table

## §8 Why this arc, why now

The prior arc taught the durable lesson: AC verification against worktree state ≠ verification against prod. This arc is the corrective: every AC verifies prod, every stream closes with a prod gate, the wave-complete tag is conditional on a final cross-stream prod gate.

When this arc closes, **V1.3 is genuinely production-live** — the instrument the native sees in the portal matches the instrument the wave seals described. The `brahma-v1-3-production-live` tag means the prod state matches the claimed state, not just that the code is in main.

After this arc, the next macro-phase (M5-A prospective testing + Mīmāṃsā multiplier wake-up) can open with confidence that the foundation is real.

---

*End of CLAUDECODE_BRIEF_V1_3_PRODUCTION_ACTIVATION v1.0. 5 streams; 1 sequential gate + 4 parallel; verify-against-prod discipline binding; wave-close prod gate mandatory.*
