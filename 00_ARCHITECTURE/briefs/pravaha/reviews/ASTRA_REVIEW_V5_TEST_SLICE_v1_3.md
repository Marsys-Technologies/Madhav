VERDICT: ACCEPT_WITH_AMENDMENTS

Reviewed the full requested diff through `9695cd0ea242f7c4c466661a5bb7b93d8555024b`. **No must-fix-before-small-test defect found within the stated boundary:** two unsealed runs, canonical chart, no publication or authority change. Normal v5 serving needs the amendments below.

**P2 — Published v5 reads fail through the actual SQL proxy.**

[register_gochara_contact_ledger.ts:367](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:367) introduces two queries incompatible with the transport:

- The `to_regclass` query has no `FROM`; the proxy rejects it at [route.ts:186](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform/src/app/api/mcp/db/query/route.ts:186).
- The subsequent seal query references `ka_gochara_generation_seal`, which is absent from the allowlist; rejection occurs at line 198.

**Failure:** request a published, sealed `5.0` generation. Instead of serving it, the tool returns an HTTP-400-derived error. Published-but-unsealed diagnostic reads also fail.

I reproduced this offline using the actual reader and proxy validator with mocked transport. The new mocked-fetch tests bypass this validation.

**Timing: next window is acceptable for the small test; fix before normal published-v5 serving.** Support the seal lookup through the real transport and add a test exercising its validator.

**P2 — The new lock unintentionally restricts legacy publication to the canonical chart.**

[ledger.py:671](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform/python-sidecar/services/gochara_kernel/ledger.py:671) takes the Gochara-5 lock for **every generation**, including legacy publication. That function explicitly refuses other charts at [1153:446](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform/migrations/1153_gochara_sky_event_substrate.sql:446).

**Failure:** the existing legacy `step08_flip.py --chart-id <other-chart>` reaches `ledger.publish()` at line 163 and now fails before reading its valid legacy candidate. The same restriction affects an otherwise idempotent publication call.

**Timing: next window; not a blocker for the canonical-chart small test.** Scope this particular lock requirement to governed generations, or explicitly resolve the shared helper’s legacy compatibility.

**P3 — Diagnostics incorrectly report previously sealed generations as unsealed.**

At [register_gochara_contact_ledger.ts:365](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform-mcp/src/tools/retrieval/register_gochara_contact_ledger.ts:365), `sealed` remains `false` unless status is currently `published`.

**Failure:** a sealed generation is legitimately superseded or withdrawn. A diagnostic read then reports `sealed:false` and describes its immutable historical rows as build output under construction. Those lifecycle transitions explicitly retain the seal and attested rows at [1240:975](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform/migrations/1240_gochara_window_verification_gate.sql:975).

**Timing: next window.** Determine seal history independently of publication status when constructing diagnostics.

**A. Round-3 P1: resolved for the supported production path; only partly protected without the lock.**

- `publish()` opens its transaction/savepoint before `_publish_locked()`. The lock precedes every manifest/content read, including the already-published branch. Strictly, the catalog probe itself precedes the lock.
- With migration 1153 applied, the schema-qualified signature resolves. Missing execution permission would raise; it would not silently select the fallback.
- The conditional update at [ledger.py:709](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform/python-sidecar/services/gochara_kernel/ledger.py:709) independently closes the original check-to-flip race: it rechecks candidate status and both slice indicators.
- It is **not an unconditional database guarantee**. Without cooperating locks, a stale `publish_candidate()` caller can read candidate status, let publication finish, then replace the vector through its `WHERE manifest_id` update at line 555. The deferred CHECK must cover vector-changing updates too.

The v5 writer takes the chart lock before calling `publish_candidate()`. Approved sealing already holds the same chart lock and the global **shared** lock. Reacquiring that transaction’s chart lock introduces no lock-order inversion or apparent deadlock.

**B. Round-3 P2: resolved for normal contact-ledger serving.**

An unstamped candidate left by an interrupted slice-to-full rebuild now receives `candidate_not_served` before coverage queries. Explicitly pinned candidates need only the manifest read. Slice-stamped manifests are refused **before** the diagnostic exception, including when `diagnostic=true`.

Diagnostics require explicit opt-in and retain a top-level warning in both successful and overflow responses. They deliberately permit inconsistent candidate rows; they are not a consistent snapshot or row-origin guarantee. Legacy 3.x/4.x reader behavior remains unchanged. I found no in-tree consumer requiring unlabelled 5.x candidate reads.

Seal existence is otherwise a reasonable serving condition: the seal binds the manifest, and the SQL guards prevent subsequent mutation of sealed content. Separate reads can observe a concurrent withdrawal, but that does not reopen the candidate-rebuild mixing problem.

**Other readers do lack this rule.** The shared coverage path in [register_gochara_windows.ts:1075](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform-mcp/src/tools/retrieval/register_gochara_windows.ts:1075) accepts any authority-selected manifest and reads its coverage at line 1224 without publication/seal/slice checks. An authority pointer naming a v5 candidate would expose that coverage. Migration 1236 prevents such a pointer **if applied**; I did not verify deployment. This existing gap belongs before any v5 authority flip, not before the stated test, which does not change authority. I found no additional registered reader directly serving the new v5 contact/record/evaluation-window tables.

**C. Transaction ownership**

`with conn.transaction()` at `ledger.py:666` **does commit when entered on an idle connection**, including an idle non-autocommit connection. Inside an existing transaction it creates/releases a savepoint and does not commit the outer transaction.

Current relevant callers are safe: approved sealing opens its outer transaction at `seal_flow.py:232`; the legacy flip performs earlier reads; the test-slice writer never calls `publish()`. Thus I found no current violation of the writer’s `ctx.db_conn` ownership contract. The helper should nevertheless not be described as universally commit-free.

**D. Verification and test strength**

- **157 offline tests passed; 5 skipped; 103 database/file-writing cases were deselected.**
- Implementation lock, both changed writer fingerprints, checked census hashes, and golden pins were consistent. Golden transport checks passed; CI includes the new suites.
- The new database tests target lock order, the conditional flip, and the original interleaving meaningfully, but I did not execute them.
- The real P1 regression reaches a sentinel at the ephemeris call. It proves passage through scope validation, not successful geometry or window production.
- The AST guard passed and pins the two current explicit overrides. It remains a source regression guard, not a runtime restriction against aliases or `**kwargs`.

**E. Small-test risk**

I found no additional slicing defect that necessarily prevents either approved run. Both verifier overrides derive from the validated marker; persisted verification still positively refuses slices at `verification_job.py:180`.

Replacement remains limited to the unsealed chart×generation chain, with candidate/seal checks before deletion at [record_store.py:588](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-slice4/platform/python-sidecar/services/gochara_kernel/record_store.py:588). No new deletion of L1 facts, global substrate, other generations, or Moon on-demand partitions was found. Each run intentionally replaces the preceding candidate output.

**Not verified:** database execution or concurrency, deployed migrations/grants/authority values, complete real-ephemeris execution of either run, teardown, external MCP consumers, full Vitest execution, or live CI. No files were modified; no database or network access occurred.

