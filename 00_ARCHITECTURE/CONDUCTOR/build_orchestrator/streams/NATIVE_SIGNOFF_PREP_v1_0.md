# Native Sign-Off Preparation — Multi-Ayanamsha Build

## What to review

### 1. Red-team (REQUIRED before final close)

File: `00_ARCHITECTURE/RED_TEAM_MULTI_AYANAMSHA_BUILD_v1_0.md`
Execute each of the 8 attack surface tests. Record Class-1/2/3 findings.
Zero Class-1 findings required.

### 2. ACC1 answer:eval baseline

After triggering the native chart build (chart_id 362f9f17-95a5-490b-a5a7-027d3e0efda0):

```bash
python platform/scripts/answer_eval/run_eval.py --output platform/evals/post_build_orchestrator_eval.json
```

Target: B.11 floor >= 60%, layer_cov >= 65%.

### 3. Production migrations

Apply migrations 140-153 in order to Cloud SQL. Use:

```bash
for f in 140 141 142 143 144 145 146 147 148 149 150 151 152 153; do
  psql "$DB_URL" -f platform/migrations/${f}_*.sql
done
```

### 4. Build pipeline verification

Trigger native chart build:

```bash
curl -X POST https://amjis-web-<revision>.a.run.app/api/build/start \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"chart_id":"362f9f17-95a5-490b-a5a7-027d3e0efda0"}'
```

Monitor at /admin/tracker until status=complete.

### 5. Smoke tests post-deploy

```bash
DB_URL=$PRODUCTION_DB_URL pytest platform/tests/integration/test_multi_tenant_smoke.py -v
```

## Sign-off checklist

- [ ] Red-team IS.8(b) executed — 0 Class-1 findings
- [ ] ACC1 answer:eval baseline — B.11 >= 60%
- [ ] Migrations 140-153 applied to production
- [ ] Native chart build triggered + completed
- [ ] Multi-tenant smoke test PASS (5/5 tests)
- [ ] CLAUDE.md §E updated with workstream COMPLETE status
- [ ] PROJECT_ARCHITECTURE v2.3 reviewed and approved

When all items checked: **workstream is FULLY CLOSED**.
