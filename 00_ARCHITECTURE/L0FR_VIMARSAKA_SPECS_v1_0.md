---
artifact: L0FR_VIMARSAKA_SPECS_v1_0.md
canonical_id: L0FR_VIMARSAKA
version: 1.0
status: CURRENT
authored_by: Cowork 2026-06-07
---

# L0FR Vimarśaka Review Agent Specifications

Three specialized autonomous reviewers replace v1.1 operator gates. Each Vimarśaka has full read access + decision authority.

## Universal Vimarśaka Discipline

All three Vimarśakas operate under shared rules:

1. **Programmatic over impressionistic.** Every check is a command or query with a defined pass criterion. "Looks good" is never a valid reason.
2. **Rework loops bounded at 3 attempts.** If a stream fails review 3 times, escalate to Tier-3.
3. **Decision audit trail.** Every decision logged to `00_ARCHITECTURE/CONDUCTOR/l0fr/smriti/vimarsaka_<gate>_<attempt>.md` with: checks run, results, pass/fail per check, decision, reasoning.
4. **No silent approvals.** If a check is skipped (e.g., infrastructure unavailable), it's logged as a known residual and explicitly noted in the decision.
5. **Tier-3 escalation triggers async native notification but does NOT pause other streams.** Failed streams pause; healthy streams continue.

**LLM: NONE.** Per memory `feedback_deterministic_first_for_data_build` (2026-06-07): all Vimarśaka checks are programmatic Python + SQL + shell. No LLM judgment. Quality compromise: structural validation only, no semantic quality scoring. Cost: $0 per Vimarśaka pass.

---

## Vimarśaka-A — Architecture Reviewer (post-Stream A)

### Mission
Validate that Stream A delivered a clean foundation: infrastructure, schema, kill-list audit, retrieval registry scaffolding, 4 adapters, OAuth flow, 5 pattern-validation capabilities.

### Programmatic checks

```bash
#!/bin/bash
# Vimarśaka-A check script — run from /Users/Dev/Vibe-Coding/Apps/MadhavL0FR-A

PASS=0; FAIL=0
check() {
  local name=$1; local expected=$2; local actual=$3
  if [ "$expected" = "$actual" ]; then PASS=$((PASS+1)); echo "✓ $name"
  else FAIL=$((FAIL+1)); echo "✗ $name (expected: $expected, actual: $actual)"; fi
}

# 1. Audience tier residual = 0
RESIDUAL=$(grep -rn "audience_tier\|audienceTier\|tier\s*=\s*['\"]client" \
  --include="*.ts" --include="*.tsx" --include="*.py" --include="*.sql" \
  platform/src platform-mcp 2>/dev/null \
  | grep -v "SESSION_LOG\|00_ARCHITECTURE\|memory" | wc -l)
check "audience_tier residual = 0" "0" "$RESIDUAL"

# 2. Migration 081 applied
MIGRATION=$(psql_prod -At -c "SELECT count(*) FROM information_schema.tables WHERE table_name IN ('sutravali_rules','sutravali_review','chart_panchanga_cache','classical_texts_source','remedy_review_queue')")
check "5 new tables exist in prod" "5" "$MIGRATION"

# 3. .se1 files in GCS
SE1_COUNT=$(gcloud storage ls gs://madhav-ephemeris/se1/ 2>/dev/null | wc -l)
check ".se1 files in GCS ≥ 8" "true" "$([ $SE1_COUNT -ge 8 ] && echo true || echo false)"

# 4. .se1 files bundled in brahma-pipeline Dockerfile
BUNDLED=$(grep -c "COPY.*ephe\|SWE_EPHE_PATH" $BRAHMA_PIPELINE_PATH/Dockerfile)
check ".se1 bundled in brahma-pipeline" "true" "$([ $BUNDLED -ge 1 ] && echo true || echo false)"

# 5. .se1 files bundled in python-sidecar Dockerfile
SIDECAR_BUNDLED=$(grep -c "COPY.*ephe\|SWE_EPHE_PATH" platform/python-sidecar/Dockerfile)
check ".se1 bundled in python-sidecar" "true" "$([ $SIDECAR_BUNDLED -ge 1 ] && echo true || echo false)"

# 6. Retrieval registry types.ts exists
TYPES_EXISTS=$(test -f platform/src/lib/retrieval/registry/types.ts && echo "true" || echo "false")
check "registry/types.ts exists" "true" "$TYPES_EXISTS"

# 7. Capability interface authored (grep for the key fields)
CAP_INTERFACE=$(grep -E "uri:|type:.*'tool'.*'resource'.*'prompt'|llm_hints:" platform/src/lib/retrieval/registry/types.ts | wc -l)
check "Capability interface complete" "true" "$([ $CAP_INTERFACE -ge 3 ] && echo true || echo false)"

# 8. 4 adapter directories exist
ADAPTERS=$(ls -d platform/src/lib/retrieval/adapters/{agentic_loop,bulk_context,openai_function_calling,hybrid} 2>/dev/null | wc -l)
check "4 adapter directories" "4" "$ADAPTERS"

# 9. Agentic loop modules present
AGENTIC_MODULES=$(ls platform/src/lib/retrieval/adapters/agentic_loop/*.ts 2>/dev/null | wc -l)
check "agentic_loop has ≥7 modules" "true" "$([ $AGENTIC_MODULES -ge 7 ] && echo true || echo false)"

# 10. OAuth endpoints in platform-mcp
OAUTH_EXISTS=$(grep -rn "oauth/authorize\|oauth/token" $BRAHMA_PIPELINE_PATH/../platform-mcp/src 2>/dev/null | wc -l)
check "OAuth endpoints exist" "true" "$([ $OAUTH_EXISTS -ge 2 ] && echo true || echo false)"

# 11. parity_check.ts compiles
cd platform && npx tsc --noEmit src/lib/retrieval/registry/parity_check.ts 2>&1 | grep -c "error" | (read N; [ $N -eq 0 ] && echo "true" || echo "false")
check "parity_check compiles" "true" "$(npx tsc --noEmit src/lib/retrieval/registry/parity_check.ts 2>&1 | grep -c "error" | awk '{print ($1==0)?"true":"false"}')"

# 12. 5 pattern-validation capabilities registered
CAP_COUNT=$(node -e "const r=require('./platform/src/lib/retrieval/registry'); console.log(r.listCapabilities().length)" 2>/dev/null || echo "0")
check "≥5 capabilities registered" "true" "$([ $CAP_COUNT -ge 5 ] && echo true || echo false)"

# 13. resolve_entity callable via MCP
MCP_RESPONSE=$(curl -s -X POST http://localhost:8080/mcp/tools/resolve_entity \
  -H "Content-Type: application/json" -d '{"name":"Shani"}' | jq -r '.result.canonical_id' 2>/dev/null)
check "MCP resolve_entity('Shani') = Saturn" "Saturn" "$MCP_RESPONSE"

# 14. resolve_entity callable via Consume Chat
CHAT_RESPONSE=$(curl -s "http://localhost:3000/api/retrieval/L0/resolve_entity?name=Shani" -b "__session=$SESSION_COOKIE" | jq -r '.canonical_id' 2>/dev/null)
check "Consume Chat resolve_entity('Shani') = Saturn" "Saturn" "$CHAT_RESPONSE"

# 15. Schema migration 081 idempotent (re-run safely)
MIGRATION_RERUN=$(psql_prod -f platform/supabase/migrations/081_l0fr_schema.sql 2>&1 | grep -c "ERROR")
check "Migration 081 idempotent" "0" "$MIGRATION_RERUN"

# Decision
echo "PASS: $PASS / 15"
echo "FAIL: $FAIL / 15"
if [ $FAIL -eq 0 ]; then
  echo "DECISION: APPROVE"
  echo "approved" > /tmp/vimarsaka_a_decision
elif [ $FAIL -le 3 ]; then
  echo "DECISION: REJECT_WITH_FEEDBACK (≤3 attempts allowed)"
  echo "reject" > /tmp/vimarsaka_a_decision
else
  echo "DECISION: ESCALATE_TIER3"
  echo "escalate" > /tmp/vimarsaka_a_decision
fi
```

### Decision logic
- 15/15 PASS → APPROVE (state.yaml: vimarsaka_a.status=pass; unblock B/C/E/F/G)
- 12-14/15 PASS → REJECT_WITH_FEEDBACK; surface specific failures to Stream A Conductor; rework attempt N+1
- ≤11/15 PASS or attempts>3 → ESCALATE_TIER3

### Smṛti output (mandatory)
```yaml
gate: vimarsaka_a
attempt: 1
checks_run: 15
checks_passed: <N>
checks_failed: <N>
failures: [<check_name>: <expected> vs <actual>, ...]
decision: APPROVE | REJECT_WITH_FEEDBACK | ESCALATE_TIER3
reasoning: <one paragraph>
next_action: <unblock streams | send feedback to Stream A Conductor | notify native>
```

---

## Vimarśaka-C — Content Quality Reviewer (mid-Stream C, Python-only)

### Mission
Validate text chunking STRUCTURAL quality on the first 3 ingested texts (BPHS, Phaladeepika, Jataka Parijata) before Stream C continues and before Stream D spawns. Per deterministic-first principle: NO semantic LLM scoring; structural Python checks only.

### Programmatic checks (Python + SQL only)

```bash
# Random sample of 50 chunks across 3 texts; check each on structural criteria.

PASS=0; FAIL=0

# Per-chunk structural checks (deterministic):
for chunk in $(psql_prod -At -c "
  SELECT chunk_id, text_id, verse_ref, content_en, content_sa, source_citation,
         length(content_en) as len_en
  FROM classical_text_chunks
  WHERE text_id IN ('BPHS', 'PHALADEEPIKA', 'JATAKA_PARIJATA')
  ORDER BY random() LIMIT 50;
"); do

  # 1. verse_ref non-null and matches regex pattern
  python -c "import re; assert re.match(r'^(CH|Verse|V|S)\d+', '$verse_ref')" 2>/dev/null \
    && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
  
  # 2. content_en length between 30 and 2000 chars (rejects fragments + overlong chunks)
  [ $len_en -ge 30 ] && [ $len_en -le 2000 ] \
    && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
  
  # 3. source_citation non-null
  [ -n "$source_citation" ] \
    && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
  
  # 4. content_en starts with capital letter, Sanskrit marker, or digit (not mid-sentence)
  python -c "import re; assert re.match(r'^[A-Z\d०-९ऀ-ॿ]', '$content_en')" 2>/dev/null \
    && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
  
  # 5. content_sha256 valid (32-char hex)
  python -c "import re; assert re.match(r'^[0-9a-f]{32,64}$', '$content_sha256')" 2>/dev/null \
    && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
done

# Pass rate
TOTAL=$((PASS+FAIL))
PCT=$((PASS*100/TOTAL))
echo "Structural pass rate: $PCT%"
```

### Decision logic (deterministic thresholds)
- Pass rate ≥ 85% → APPROVE (state.yaml: vimarsaka_c.status=midway_pass; Stream C continues + Stream D spawns)
- Pass rate 70-85% → REJECT_WITH_FEEDBACK; specific failing chunks flagged for Stream C to re-chunk OR park
- Pass rate < 70% → ESCALATE_TIER3

**Quality risk documented:** structural checks pass even if translation is poor or content is wrong, as long as parse structure is intact. Native accepts this trade-off for full determinism.

### Smṛti output
```yaml
gate: vimarsaka_c
attempt: <N>
sample_size: 50
texts_sampled: [BPHS, PHALADEEPIKA, JATAKA_PARIJATA]
checks_total: 250  # 50 chunks × 5 structural checks
checks_passed: <N>
pass_rate_pct: <0-100>
breakdown:
  verse_ref_valid: <N>/50
  length_in_range: <N>/50
  citation_non_null: <N>/50
  starts_properly: <N>/50
  sha256_valid: <N>/50
failing_chunks: [<chunk_id>: <which_check_failed>, ...]
decision: APPROVE | REJECT_WITH_FEEDBACK | ESCALATE_TIER3
reasoning: structural-only per deterministic-first principle
```

---

## Vimarśaka-Z — Integration Seal Reviewer (pre-seal)

### Mission
Comprehensive integration validation after all 7 streams close. SEAL authority. Must run all-adapter smoke tests, ChatGPT MCP round-trip, first end-to-end build.

### Programmatic checks

```bash
PASS=0; FAIL=0; SOFT_FAIL=0

# === Capability registration completeness ===

# Stream B capabilities: 4 tools + 2 resources = 6
B_CAPS=$(node -e "const r=require('./platform/src/lib/retrieval/registry'); console.log(r.listCapabilities().filter(c => c.uri.includes('L0') && (c.uri.includes('ephemeris') || c.uri.includes('planet') || c.uri.includes('aspect') || c.uri.includes('retrograde'))).length)")
[ $B_CAPS -ge 6 ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# Same for C, D, E, F (see master plan §8)
# ... (similar checks per stream)

# === Adapter smoke tests ===

# Test capability through all 4 adapters
TEST_CAPABILITY="marsys://tool/L0/query_planet_position"
TEST_ARGS='{"date":"1984-02-05","body":"Sun","ayanamsha":"Lahiri"}'
EXPECTED_LONG="271.8"  # Capricorn 21°48' = ~271.8°

# Agentic loop adapter (Claude-style)
AGENTIC=$(curl -s -X POST http://localhost:3000/api/retrieval/adapters/agentic_loop/test \
  -d "{\"capability\":\"$TEST_CAPABILITY\",\"args\":$TEST_ARGS}" \
  | jq -r '.longitude_tropical' | cut -c1-5)
[ "$AGENTIC" = "$EXPECTED_LONG" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# Bulk context adapter (Gemini-style)
BULK=$(curl -s -X POST http://localhost:3000/api/retrieval/adapters/bulk_context/test \
  -d "{\"capability\":\"$TEST_CAPABILITY\",\"args\":$TEST_ARGS}" \
  | jq -r '.bundled.longitude_tropical' | cut -c1-5)
[ "$BULK" = "$EXPECTED_LONG" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# OpenAI function calling adapter
OPENAI=$(curl -s -X POST http://localhost:3000/api/retrieval/adapters/openai_function_calling/test \
  -d "{\"capability\":\"$TEST_CAPABILITY\",\"args\":$TEST_ARGS}" \
  | jq -r '.tool_call_result.longitude_tropical' | cut -c1-5)
[ "$OPENAI" = "$EXPECTED_LONG" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# Hybrid adapter
HYBRID=$(curl -s -X POST http://localhost:3000/api/retrieval/adapters/hybrid/test \
  -d "{\"capability\":\"$TEST_CAPABILITY\",\"args\":$TEST_ARGS}" \
  | jq -r '.result.longitude_tropical' | cut -c1-5)
[ "$HYBRID" = "$EXPECTED_LONG" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# === ChatGPT MCP roundtrip (automated via Playwright or curl) ===

# Authenticate via OAuth
OAUTH_TOKEN=$(curl -s -X POST http://localhost:8080/mcp/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=test&client_secret=$MCP_TEST_SECRET" \
  | jq -r '.access_token')

# Invoke a tool with the token
MCP_TOOL_RESULT=$(curl -s -X POST http://localhost:8080/mcp/tools/query_planet_position \
  -H "Authorization: Bearer $OAUTH_TOKEN" \
  -d "$TEST_ARGS" | jq -r '.longitude_tropical' | cut -c1-5)
[ "$MCP_TOOL_RESULT" = "$EXPECTED_LONG" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# === First --global-build smoke test ===

RUN_ID=$(uuidgen)
psql_prod -c "INSERT INTO build_runs (id, chart_id, scope, action, plan, state, triggered_by)
  VALUES ('$RUN_ID', NULL, 'global', 'build',
    '[\"brahmagyan.kalapancanga\",\"brahmagyan.sarani\",\"brahmagyan.samanvaya\",\"brahmagyan.shastra\",\"brahmagyan.upaya_kosha\",\"brahmagyan.sutravali\"]'::jsonb,
    'planned', 'vimarsaka_z')"

gcloud run jobs execute brahma-build-pipeline-job \
  --region=asia-south1 --project=madhav-astrology \
  --args=--global-build,--run-id,$RUN_ID --wait

GLOBAL_BUILD_STATE=$(psql_prod -At -c "SELECT state FROM build_runs WHERE id='$RUN_ID'")
[ "$GLOBAL_BUILD_STATE" = "completed" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# === First per-chart L1 build (PyHora integration) ===

# Build ganita.graha_sthana for native via PyHora
PER_CHART_RUN=$(curl -s -X POST http://localhost:3000/api/cockpit/runs \
  -d '{"chart_id":"482012f1-...","scope":"asset","scope_target":"ganita.graha_sthana","action":"build"}' \
  | jq -r '.run_id')

sleep 60  # PyHora compute time

PER_CHART_STATE=$(psql_prod -At -c "SELECT state FROM build_runs WHERE id='$PER_CHART_RUN'")
[ "$PER_CHART_STATE" = "completed" ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# === Corpus completeness floors ===

EPHEMERIS_ROWS=$(psql_prod -At -c "SELECT count(*) FROM ephemeris_daily")
[ $EPHEMERIS_ROWS -ge 820000 ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

CHUNK_COUNT=$(psql_prod -At -c "SELECT count(*) FROM classical_text_chunks")
[ $CHUNK_COUNT -ge 6000 ] && PASS=$((PASS+1)) || SOFT_FAIL=$((SOFT_FAIL+1))

RULE_COUNT=$(psql_prod -At -c "SELECT count(*) FROM sutravali_rules")
[ $RULE_COUNT -ge 3000 ] && PASS=$((PASS+1)) || SOFT_FAIL=$((SOFT_FAIL+1))

REMEDY_COUNT=$(psql_prod -At -c "SELECT count(*) FROM brahma_remedy_corpus")
[ $REMEDY_COUNT -ge 500 ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# === Audience tier kill verified maintained ===

RESIDUAL=$(grep -rn "audience_tier\|audienceTier" --include="*.ts" --include="*.py" \
  platform/src platform-mcp 2>/dev/null | grep -v SESSION_LOG | wc -l)
[ $RESIDUAL -eq 0 ] && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

# === Decision ===

echo "PASS: $PASS"
echo "FAIL: $FAIL (hard)"
echo "SOFT_FAIL: $SOFT_FAIL (corpus floors short — log as residual but still seal)"

if [ $FAIL -eq 0 ]; then
  echo "DECISION: SEAL"
elif [ $FAIL -le 2 ] && [ $((PASS+SOFT_FAIL)) -ge 18 ]; then
  echo "DECISION: DELTA_DEPLOY (spawn small fix-up streams for the 1-2 failures; re-review)"
else
  echo "DECISION: ESCALATE_TIER3"
fi
```

### Decision logic
- 0 hard fails → SEAL; write `00_ARCHITECTURE/L0FR_SEALED_v1_0.md` artifact; commit + tag `brahma-l0fr-sealed-2026-XX-XX`
- 1-2 hard fails (and overall ≥18/20 pass+soft) → DELTA_DEPLOY: spawn focused fix-up streams for the specific failures, re-review; max 2 delta-deploy iterations
- >2 hard fails or 2 delta-deploys exhausted → ESCALATE_TIER3

### Smṛti output (FINAL)
```yaml
gate: vimarsaka_z
attempt: <N>
sealing_attempt: <N>
checks_run: 20
checks_passed: <N>
checks_failed_hard: <N>
checks_failed_soft: <N>
adapter_smoke_results:
  agentic_loop: PASS|FAIL
  bulk_context: PASS|FAIL
  openai_function_calling: PASS|FAIL
  hybrid: PASS|FAIL
chatgpt_mcp_roundtrip: PASS|FAIL
global_build_end_to_end: PASS|FAIL
per_chart_l1_build: PASS|FAIL
corpus_floors:
  ephemeris: <N> / 820,000 → PASS|FAIL
  text_chunks: <N> / 6,000 → PASS|SOFT_FAIL
  sutravali: <N> / 3,000 → PASS|SOFT_FAIL
  remedies: <N> / 500 → PASS|FAIL
audience_tier_residual: 0 / 0 → PASS
decision: SEAL | DELTA_DEPLOY | ESCALATE_TIER3
reasoning: <one paragraph>
residuals_for_post_seal: [<item>, ...]
```
