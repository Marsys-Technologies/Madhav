VERDICT: REJECT

Reviewed HEAD `b356ea955d8c` against local `origin/main` `091362f315a2`, plus `.DESIGN_BRIEF.md`. **Findings 1–4 block merge. Finding 5 is nonblocking.** No files modified; no database or network access.

1. **P1 — A small request repeatedly runs verification over the entire generation.**

   [serving_reader.py:522](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L522) calls the constructor per class. [scope_response.py:159](platform/python-sidecar/services/gochara_kernel/scope_response.py#L159) then calls the generation-wide violations function, filtering its output afterward. That function recomputes window digests, expected sets, membership joins and input digests; each grain’s input digest includes **every contact in the generation** ([1240:319](platform/migrations/1240_gochara_window_verification_gate.sql#L319), [1240:507](platform/migrations/1240_gochara_window_verification_gate.sql#L507)). Qualification adds one query per returned window ([scope_response.py:175](platform/python-sidecar/services/gochara_kernel/scope_response.py#L175)).

   **Concrete input:** canonical chart, sealed `5.0` covering 1998–2084, `date_from="2030-01-01T00:00:00Z"`, `date_to="2030-01-02T00:00:00Z"`, `limit=1`, classes omitted. Every otherwise-complete class still repeats the full-generation check. Neither dates nor limit constrain that work.

   The author’s timeout concern is credible from the query structure; **I did not measure whether it exceeds 15 seconds**. The timeout is per statement, not per HTTP request.

   **Required change:** keep `coverage_response` authoritative, but let it consume immutable verification attestations bound to the seal/manifest through indexed reads; move full replay outside the request path and batch qualification reads. Calling the expensive function once per request removes duplication, but does **not** remove the single-call timeout risk.

2. **P2 — Half-open window semantics are assumed rather than enforced.**

   The instant predicate uses the stored range’s bounds directly: `w.interval @> instant` ([serving_reader.py:264](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L264)). Unlike the manifest horizon, window bounds are not rejected when they differ from `[)`.

   The actual schema requires a finite, nonempty interval, but does not require half-open bounds ([1156:283](platform/migrations/1156_gochara_eval_window.sql#L283), [1153:417](platform/migrations/1153_gochara_sky_event_substrate.sql#L417)). Window verification reads endpoints without bound flags, and the relevant digests also omit those flags ([window_verifier.py:200](platform/python-sidecar/services/gochara_kernel/window_verifier.py#L200), [1240:243](platform/migrations/1240_gochara_window_verification_gate.sql#L243)).

   **Concrete input:** a stored window `[2025-01-10T00:00Z, 2025-02-20T00:00Z]`, inside the manifest horizon, queried at `2025-02-20T00:00Z`. The reader includes it, violating the required exclusive end. Changing only `[)` to `[]` preserves the endpoints used by those digest checks.

   **Required change:** refuse incompatible stored bounds by name, and protect the invariant in verification/schema through the appropriate follow-up. The existing boundary test only exercises a correctly constructed `[)` window ([test_w1_serving_reader.py:468](platform/python-sidecar/tests/l3/gochara/test_w1_serving_reader.py#L468)).

3. **P2 — Missing coverage can become an empty success, including a constructor refusal.**

   When classes are omitted, the class list is derived solely from inventory and matching windows ([serving_reader.py:301](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L301)). If both are empty, the constructor loop never runs, yet the reader returns success ([serving_reader.py:520](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L520)).

   **Concrete input:** matching published manifest and seal, recognized policy and bounded horizon, but no inventory or matching windows; omit `event_classes`. An offline connection stub reproduced:

   ```json
   {"refusal": null, "windows": [], "classes": []}
   ```

   A second concrete case—request `["marriage"]` with `stored_scope` missing—makes the real constructor return `completeness="refused"` and `refusal="stored_scope_missing"` ([scope_response.py:229](platform/python-sidecar/services/gochara_kernel/scope_response.py#L229)). The reader retains that only inside class coverage while returning top-level `refusal: null, windows: []`.

   **Required change:** make absent class evidence a named unknown/refusal, and propagate constructor refusals consistently. Preserve per-class detail for mixed answers. Also avoid the unconditional “verified contact intervals” disclosure when the constructor reports refused or unverified ([serving_reader.py:63](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L63)).

4. **P2 — The guessed near-miss schema does not fail closed on every mismatch.**

   Compatibility checks examine column **names**, not types, keys, relationships or permitted values ([serving_reader.py:333](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L333)). Counting occurrences and then using an inner object join can silently lose them ([serving_reader.py:359](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L359)). Stored `standing` and `score` pass through unchecked ([serving_reader.py:380](platform/python-sidecar/services/gochara_kernel/serving_reader.py#L380)).

   **Concrete inputs, reproduced with offline stubs:**
   - Matching column names, version `"1"`, one occurrence whose object has no matching row: `near_miss_layer="present"`, `near_miss_intervals=[]`, matched `1`, returned `0`, truncated `true`; **no `schema_mismatch`**.
   - Same readable shape with `score=0.75`: the response exposes that score and `score_reason=null`, violating the unscored near-miss contract.

   **Required change:** retain an explicit unavailable stub until the real migration contract exists, or validate that contract and reject incompatible rows/joins by name. The current tests manufacture their schema from the reader’s own mapping and supply the null-score constraint themselves ([test_w1_serving_reader.py:536](platform/python-sidecar/tests/l3/gochara/test_w1_serving_reader.py#L536)); they cannot establish compatibility with migration 1308.

5. **P3 — Connection cleanup excludes failures during connection configuration.**

   `_connect()` opens the connection before setting its properties ([gochara_v5.py:92](platform/python-sidecar/routers/gochara_v5.py#L92)). If a property assignment raises, the route’s connection-opening exception handler has no handle to close; the later `finally` is never entered.

   **Concrete fault input:** a valid request with `psycopg.connect` returning a handle whose `read_only` setter raises. An offline fault injection confirmed `close()` was not called.

   Wrap post-connect configuration in cleanup-on-error. Ordinary success and reader-error paths already roll back and close correctly.

The remaining checks:

| Area | Assessment |
|---|---|
| Publication/seal gates | Explicitly refuse candidate, superseded, rolled-back, unsealed and test-slice generations; seal manifest identity is compared. All nine named refusal codes have reachable branches. |
| Chart/generation isolation | Window, membership, relationship and contact queries are scoped correctly. Physical objects are intentionally global immutable identities keyed by UUID, so their join needs no nonexistent chart/generation columns ([1153:619](platform/migrations/1153_gochara_sky_event_substrate.sql#L619)). |
| Schema and SQL | Core referenced names match 1081, 1153, 1155, 1156, 1206, 1233 and 1240. New singleton selections pin unique keys and order explicitly; inherited constructor lookups pin primary/unique keys. Request values are parameters; interpolated identifiers are static validated names. |
| Dates | Equal/reversed ranges are named refusals; naive datetimes are rejected; ordinary non-UTC offsets normalize correctly. Start/end/both-side horizon clipping works. Finding 2 qualifies window-boundary correctness. |
| All-NULL | Core window fields preserve stored nulls and `unqualified`; no adversity flag or numeric ordering is invented. Policy, horizon and scored edge come from the manifest. Missing scored-edge pins remain explicitly unknown. |
| HTTP/auth/read-only | Mount uses the existing `verify_api_key`, plus the same fail-closed local check as the yoga router. Domain refusals return 200; malformed route input returns 422; read/connect failures produce generic named 5xx bodies. No DSN, SQL or stack is returned by those handlers. Read-only settings and repeatable-read isolation are explicit; no commit path found. |
| CI | [ci.yml:424](.github/workflows/ci.yml#L424) adds exactly the three files to the existing `GOCHARA_A53_REQUIRE_DB=1` step. No other job configuration changes. However, existing Governance Gates also collects them through `pytest tests/` ([ci.yml:2120](.github/workflows/ci.yml#L2120)); “no effect on other jobs” would be too strong. |
| Owner decisions | No policy switch or election-avoidance recommendation is implemented. Supporting either manifest-selected policy does not itself decide which generation the owner should serve. |

The refusal, null-preservation, clipping, ordering, constructor-spy and grant-revocation tests contain meaningful assertions: removing those protections would fail them. Source-string checks are weaker evidence, and comparing the route response with the same reader does not independently validate reader semantics.

**The positive seal fixture is not a real-seal integration test.** It disables seal guards and inserts the row directly ([test_w1_serving_reader.py:48](platform/python-sidecar/tests/l3/gochara/test_w1_serving_reader.py#L48)); its helper also rewrites search states with guards disabled. The real path publishes, invokes the seal gate and writes a mandatory approval receipt ([seal_flow.py:58](platform/python-sidecar/services/gochara_kernel/seal_flow.py#L58)). The positive serving test instead expects no receipt. I found no definite receipt-column mismatch, but these tests could pass while a real sealed-generation path fails. Add a positive read/route test using the actual seal flow.

Verification performed: six changed Python files parsed, `git diff --check` passed, 13 offline refusal assertions and four clipping/offset assertions passed, and the stated stub counterexamples were reproduced. **Not verified:** PostgreSQL execution, actual seal execution, database grants, real-generation latency, deployed behavior or CI results. No repository database tests were run.

