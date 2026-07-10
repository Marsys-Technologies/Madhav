# TAP CI suite (R6 lane 5-harness)

Implements the CI-automatable half of `00_ARCHITECTURE/TOTAL_AUDIT_PROTOCOL_v1_0.md`
§3, per the Phase 5 line item in `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md`:
"TAP CI suite: the 7 seam-conservation checks (TAP-5 spec), TAP-6 grep set,
TAP-7 8 gates, S-13 live coverage matrix." Also covers the per-tool MCP smoke
battery and SC-17/18/19 boot-time pointer validation named in the R6
lane-5-harness brief.

## Scripts

| Script | Battery | Needs DB? | Needs live MCP server? |
|---|---|---|---|
| `tap6_method_grep.ts` | TAP-6 method audit (grep set) | No | No |
| `sc_pointer_validation.ts` | Boot-time pointer validation (SC-17/18/19 + Law-7) | No | No |
| `mcp_tool_smoke.ts` | Per-tool smoke battery | No | Yes (falls back to PLAN mode) |
| `s13_coverage_matrix_live.ts` | S-13 / TAP-5 Law-1 | Yes | No |
| `tap5_seam_conservation.ts` | TAP-5, all 7 laws | Yes (Laws 1/2/3/5/6); Law-4 is static | No |
| `tap7_distribution_gates.ts` | TAP-7, all 8 gates | Yes (Gates 1-7); Gate 8 needs a live API | No |

## Running locally against the real DB

The DB-backed scripts use the project's `pg` pool (`platform/src/lib/db/client.ts`),
which requires `DATABASE_URL`. In this sandbox that module also needs `npm install`
run once (`server-only` + `pg` are not vendored into every worktree checkout).

```bash
cd platform
npm install   # first time only, if node_modules is missing

# Point at a running Cloud SQL Auth Proxy:
#   cloud-sql-proxy <INSTANCE_CONNECTION_NAME> &
export DATABASE_URL="postgresql://<user>:<password>@127.0.0.1:5432/amjis"

npx tsx --conditions=react-server scripts/audit/tap/s13_coverage_matrix_live.ts
npx tsx --conditions=react-server scripts/audit/tap/tap5_seam_conservation.ts
npx tsx --conditions=react-server scripts/audit/tap/tap7_distribution_gates.ts
```

The static scripts need no DB and no `npm install` beyond `tsx` itself:

```bash
npx tsx scripts/audit/tap/tap6_method_grep.ts
npx tsx scripts/audit/tap/sc_pointer_validation.ts
npx tsx scripts/audit/tap/mcp_tool_smoke.ts   # PLAN mode without MCP_SERVER_URL
```

## Exit codes (shared convention, `lib/tap_db.ts:printReport`)

- `0` — every check PASSED or was QUARANTINED against a cited register row.
- `1` — at least one hard FAIL (a NEW, untracked violation).
- `3` — the whole battery was SKIPPED-WITH-REASON (DB/server unreachable).
  Never conflated with a PASS.
- `4` — script-internal error (bug in the harness itself, not a finding).

## Ratchet discipline

`tap6_baseline.json` and `sc_pointer_baseline.json` are the "known, tracked,
OPEN" allowlists. Every entry cites the `MARSYS_DEFECT_GAP_REGISTER_v2_0.md`
row that owns the fix. When a fixing lane closes that row:

1. Delete the corresponding baseline entry.
2. Re-run the script — it will now enforce the fix (a regression flips the
   check back to FAIL instead of silently staying green).

Do **not** delete a baseline entry to make CI green without the underlying
fix landing — that defeats the entire purpose of this harness.

## CI wiring

`.github/workflows/tap-ci.yml` runs the static jobs (`tap6-method-audit`,
`sc-pointer-validation`) unconditionally — they gate every push/PR today.
The DB-backed job (`tap-db-gates`) and the live MCP smoke job
(`mcp-tool-smoke-plan`) run with `continue-on-error: true` until
`TAP_DATABASE_URL` / `TAP_MCP_SERVER_URL` / `TAP_MCP_SMOKE_BEARER_TOKEN`
repo secrets are provisioned — remove `continue-on-error` once they are, so
those batteries start gating merges too.
