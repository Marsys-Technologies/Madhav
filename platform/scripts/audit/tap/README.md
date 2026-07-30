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
| `r18_param_noop_audit.ts` | R-18 estate-wide param no-op audit (static, ratchet-baselined) | No | No |
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

`tap6_baseline.json`, `sc_pointer_baseline.json`, and `sc_pointer_occurrences.json`
are the "known, tracked, OPEN" allowlists. Every entry cites the
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` row that owns the fix. When a fixing
lane closes that row:

1. Delete the corresponding baseline entry (and, for the pointer battery,
   its matching `sc_pointer_occurrences.json` entries).
2. Re-run the script — it will now enforce the fix (a regression flips the
   check back to FAIL instead of silently staying green).

Do **not** delete a baseline entry to make CI green without the underlying
fix landing — that defeats the entire purpose of this harness.

**Granularity (Ring-2 fix, post-`bacade1c`):** both baselines key on more
than just "which file has this problem":

- `tap6_baseline.json` keys on `(pattern, file, line_hash)` — a hash of the
  exact matched line's trimmed text. A first cut keyed on `(pattern, file)`
  alone, which meant a brand-new, unrelated occurrence of an already-banned
  pattern added anywhere else in an already-baselined file would silently
  pass. Verified by injecting a second, unrelated `# safe fallback` line
  into an already-baselined file — it correctly flipped the check to FAIL;
  reverting restored a clean exit 0.
- `sc_pointer_validation.ts` keys the "is this occurrence already known"
  question on `(instrument, file, line_hash)` via `sc_pointer_occurrences.json`,
  layered on top of `sc_pointer_baseline.json`'s per-instrument register-row
  citation. A first cut treated "instrument name is baselined" as sufficient
  to quarantine ANY occurrence of that name anywhere in the tree; verified
  the fix by injecting a brand-new `get_dignity` pointer into an
  already-baselined file — it correctly flipped to FAIL; reverting restored
  a clean exit 0.

## Pointer baseline: RATCHET AT ZERO + structural expiry (SAMĀPTI A2, 2026-07-30)

`sc_pointer_baseline.json` and `sc_pointer_occurrences.json` are now **empty**.
Every instrument they carried (SC-17 `bodha_bundle_get`; SC-18 `get_dignity` /
`get_avasthas` / `get_divisionals` / `query_signals`; the never-filed NEW-P1
`get_strength`; the never-filed NEW-P2 `query_classical_texts`, now register row
SC-23) is fixed in production, and the four remaining occurrences — all test
fixtures modelling the old non-existent names — were repointed at the live tools
production emits. Consequence: **any** unresolved pointer anywhere under
`platform-mcp/src` or `platform/src/lib/retrieval` now fails CI. Do not re-add a
baseline entry to turn a red build green.

Two checks keep the ratchet from loosening again:

- `SC-pointer:baseline-freshness` FAILs when a `sc_pointer_baseline.json` entry
  no longer reproduces against the live tree.
- `SC-pointer:occurrence-freshness` FAILs when a `sc_pointer_occurrences.json`
  entry no longer matches a live hit.

This is the structural answer to "document the quarantine with an expiry":
rather than a date nobody re-reads, **an entry expires the moment the defect it
describes stops reproducing.** It exists because four instruments sat
QUARANTINED for 20 days after their production pointers were fixed, and the
occurrence ledger still listed production sites in `registry_bridge.ts`,
`register_d9_judgment.ts`, `register_p1_ganita.ts` and `register_d10_pact.ts`
weeks after those lines were repaired — so the report could not answer which SC
rows were genuinely open. Verified by re-adding a stale `get_dignity` entry: the
check flipped to FAIL naming the exact entry to delete; removing it restored
exit 0.

**Declared bounds** (see the file's own docstring — a detector that overclaims
its coverage is itself a §N.8 violation): line-level regex, so pointers built
from a variable are invisible; matches inside comments are skipped (prose
documenting a dead pointer is not a dead pointer — before this exclusion the
check flagged its own documentation, which is how the placeholder
`instrument: 'x'` in a `response_budget` unit test became an unregistered
`SC-pointer:x` FAIL on `main`); test fixtures ARE scanned, by the convention
documented at `platform-mcp/src/lib/kala_envelope.test.ts`, but are classified
`test_fixture` vs `production` in the report so a FAIL can be triaged without
opening every file; and a resolving name proves nothing about the tool working
(that is `mcp_tool_smoke.ts`'s job).

Verified can-fail: injecting `instrument: 'totally_fake_tool_xyz'` at
`registry_bridge.ts:573` flipped the check to FAIL (and `tap:5`'s Law-7 with
it, exit 0 → 1); reverting restored exit 0. A companion probe confirmed the
comment exclusion is not a bypass — a bogus pointer in real code with a
trailing comment was caught, while the same name inside a `//` line was not.

## Law-7 is a real detector now (SAMĀPTI A2, 2026-07-30)

`tap5_seam_conservation.ts`'s Law-7 row used to be a hardcoded
`status: 'QUARANTINED'` string that named `sc_pointer_validation.ts` but never
ran it — TAP-5 reported a Law-7 status it had not measured, an earned-signal
(§N.8) violation inside the audit harness itself. It now imports
`runPointerValidation()` and folds in the real verdict (worst-status-wins), so
`npm run tap:5-seam-conservation` earns Law-7's status on every run.
`sc_pointer_validation.ts` only self-executes under `require.main === module`,
so importing it does not trigger its `process.exit`.

## The RC-14 gate: "registered" != "served" (SAMĀPTI A2 reopen-1, 2026-07-30)

`lib/mcp_registered_tools.ts` claimed to enumerate "every MCP tool name actually
registered on the live server." That claim was **false by 43 names** from
2026-07-23 onward. The RC-14 breaking flip retired 43 legacy tool names via a
central RUNTIME gate (`platform-mcp/src/lib/deprecated_tool_gate.ts`) and
deliberately LEFT their `server.tool('legacy', …)` call sites in source. A
source scan therefore saw them; the deployed server did not serve them.

Cost: `sc_pointer_validation.ts` **PASSED 32 production drill-pointer/recover
sites that dead-ended live** with `MCP error -32602: Tool <name> not found` —
the exact SC-18 harm, reintroduced wholesale and invisible for a week to the
check built to catch it. It was found by an independent live probe, not by CI.

Two fixes:

1. `collectRegisteredTools()` subtracts the gate. Verified exact against the
   live catalog on 2026-07-30: **167 call sites − 43 gated = 124 = live
   `tools/list`, set-for-set identical** (zero either way). CI stays offline and
   is now live-accurate. `collectRegistrationCallSites()` exposes the raw
   pre-gate set for diagnostics. The gate parser THROWS rather than degrading —
   a silent fallback would restore the over-approximation invisibly.
2. `runLiveCatalogParity()` (opt-in) measures the model against a real
   `tools/list`, so model drift from some *future* gate is detectable instead of
   assumed away. Enable with `MCP_SERVER_URL` + `MCP_SMOKE_BEARER_TOKEN` (same
   vars as `mcp_tool_smoke.ts`). It returns SKIPPED-WITH-REASON — never PASS —
   when unset. **Use a first-party Bearer key:** that resolves to the `full`
   profile, where `applyProfileGate()` is a no-op; an OAuth token returns a
   profile-narrowed catalog and makes the comparison meaningless.

Verified can-fail: adding a `server.tool('phantom_tool_zzz')` call site flipped
the parity check to FAIL ("125 modelled vs 124 live … phantom_tool_zzz");
re-introducing a single RC-14 legacy pointer flipped the static battery to FAIL.
Both reverted to exit 0.

**Generalize this:** a static check whose title names "the live server" must
model every runtime gate between registration and serving, or say plainly that
it does not. See `00_ARCHITECTURE/briefs/samapti/SAMAPTI_MCP_TOOL_GAP_CHARACTERIZATION_v1_0.md`
for the full reconciliation, including why `mcp_server_info`'s `tool_count: 152`
is a third, non-comparable number.

## Tool enumeration correctness (Ring-2 fix, post-`bacade1c`)

`lib/mcp_registered_tools.ts` is the single source of truth for "is `name`
a live MCP tool." The first cut of `sc_pointer_validation.ts` and
`mcp_tool_smoke.ts` each carried their own copy of this logic, and both only
matched literal `server.tool('name', ...)` call sites — missing the
`regAlias(server, '<name>', ...)` / `globalAlias(server, '<name>', ...)`
helper indirection `register_p1_aliases.ts` uses for 24 of its 47 aliased
tools. That produced two false-positive "unresolved pointer" findings
(`phala_predictive_anchors_get`, `bodha_remedies_get` — both genuinely
registered via `regAlias`). Fixed by resolving `regAlias`/`globalAlias` call
sites too; the live tool count went from 109 → 133 once fixed, and both
false positives dropped out of the unresolved-pointer report.

## CI wiring

`.github/workflows/tap-ci.yml` runs the static jobs (`tap6-method-audit`,
`sc-pointer-validation`) unconditionally — they gate every push/PR today.
The DB-backed job (`tap-db-gates`) and the live MCP smoke job
(`mcp-tool-smoke-plan`) run with `continue-on-error: true` until
`TAP_DATABASE_URL` / `TAP_MCP_SERVER_URL` / `TAP_MCP_SMOKE_BEARER_TOKEN`
repo secrets are provisioned — remove `continue-on-error` once they are, so
those batteries start gating merges too.
