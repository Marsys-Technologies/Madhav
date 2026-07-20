---
lane: D-3
status: verifying
implementer_model: claude-sonnet-5
verifier_model: opus
attempts: 1
---

## Scope

Read-only DB + code audit of the prediction/calibration substrate described in
`PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §7 / §7.4 / §14A:

1. Existence + schema of `brahma_mimamsa_prediction_ledger`, `mimamsa_calibration`,
   `brahma_mimamsa_answer_quality`, `brahma_phala_anchors`.
2. Whether `prediction_detector.ts` fires in the live request path or is dead code.
3. Actual Postgres roles and their grants on the ledger/calibration tables.
4. The critical question: is the §7.4 NO-LEAKAGE role-separation design ("arm 1")
   real, or does one serving credential have unrestricted write access to
   everything it's designed to be walled off from.

Tooling: `mcp__postgres__query` (SELECT-only) against the live DB, `Grep`/`Read`
over `platform/src` and `platform-mcp/src`. No writes to application code, only
to this lane's two designated deliverable files.

## Findings summary

4 findings (PG1-D3-0001..0004): 2 `confirmed`, 1 `partial`, 1 `new_defect`.
Severity: 1 `critical`, 3 `medium`.

**Headline finding (PG1-D3-0004, critical):** §7.4's five designed DB roles
(`role_web_serve`, `role_orchestrator`, `role_ledger_write`, `role_jobs`,
`role_sidecar`) do not exist anywhere. `pg_roles` shows exactly one
application role, `amjis_app`, which is the same credential
`platform/src/lib/db/client.ts` uses for every web-serving request
(including the consult chat route). `amjis_app` holds full CRUD (SELECT,
INSERT, UPDATE, DELETE, TRUNCATE) on `mimamsa_predictions` — the real,
populated (384-row) prediction ledger with outcome data — and on
`mimamsa_calibration`, the exact two write surfaces §7.4 designs
`role_web_serve` to be explicitly denied. A repo-wide grep for all five role
name strings across `platform/`, `platform-mcp/`, `infra/` returns zero
matches. The NO-LEAKAGE arm-1 role separation is 0% built — an aspirational
design with no implementation, not a partial or drifted one.

**Secondary findings:**
- PG1-D3-0001: none of the architecture doc's three `brahma_`-prefixed table
  names exist; the real tables are `mimamsa_predictions`, `phala_anchors`,
  `mimamsa_qa_eval` — different names, no `brahma_` prefix anywhere in the
  live schema.
- PG1-D3-0002: `prediction_detector.ts` is genuinely wired into
  `platform/src/app/api/chat/consult/route.ts` via
  `onfinish_writethrough.ts` (not dead code) and fires + writes
  unconditionally per the code path, but its target table `mcp_predictions`
  has 0 rows and `conversation_messages` also has 0 rows in this DB instance
  (despite `chart_facts` holding 276,206 rows, confirming this is the live
  populated DB, not an empty dev copy) — so runtime firing cannot be
  confirmed from DB state; either the consult path has seen zero traffic
  against this DB, or writes are silently failing (the write is wrapped in a
  swallowing try/catch).
- PG1-D3-0003 (new defect): two disjoint, unreconciled prediction ledgers
  exist — `mcp_predictions` (chat-side detector, 0 rows) and
  `mimamsa_predictions` (L5 orchestrator build-time writer `mi_bhavisya`,
  384 rows, the one actually referenced by `mimamsa_calibration` and
  `phala_anchors`). The architecture doc's §7 diagram presents one coherent
  ledger; the codebase built two.

## Evidence log

All four findings in `pg1_findings_D-3.jsonl` carry `db:<table>` or file+line
evidence: `information_schema.tables`/`role_table_grants`/`pg_roles` query
results, plus `platform/src/lib/predictions/calibration_producer.ts`,
`platform/src/lib/pipelines/shared/onfinish_writethrough.ts`,
`platform/src/lib/cockpit/assetClearSpec.ts`, and
`platform/src/lib/db/client.ts`.

## Receipt

```json
{"lane":"D-3","verifier_model":"opus","diff_reviewed":"pending",
 "findings":{"emitted":4,"schema_valid":4,"evidence_complete":4},
 "assertions":{"script":"scripts/validate_findings.py","green":["pg1_findings_D-3.jsonl: 0 violations"],"red":[]},
 "scope_warden":"pass","verdict":"PENDING_REVIEW","diagnosis":""}
```
