VERDICT: REJECT

Reviewed the full change and round delta at **`f1a50b20c03bdae52dd598ee222f5655075d1c55`**. Database-produced copies resolve authenticity, but population enforcement remains incomplete. The round also introduces drift-reporting defects.

| Prior finding | Round-2 status | Assessment |
|---|---|---|
| 1. Complete dasha population | **Partly** | Capture uses the **bound manifest horizon**, with overlap `start < upper(horizon)` and `end > lower(horizon)`. The writer independently checks completeness, but INSERT and drift checks still derive their system/level scope from the submitted population. Entire omitted levels remain invisible. |
| 2. Authenticity of the copy | **Resolved** | The BEFORE INSERT trigger constructs both copies from live rows, overwrites submitted content and metadata, checks content digests, and derives metadata digests itself. A consistently forged submitted copy is no longer authoritative. See [1305:293–320](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:293). |
| 3. Computation consumes separate live reads | **Partly** | Normal computation with a valid new snapshot uses its copies. Legacy/missing-copy fallbacks remain, and the regression guard does not cover every later path or detect arbitrary added reads. |
| 4. Numeric exactness | **Partly** | The original Python digest round trip is fixed: hashing stays in PostgreSQL, nested JSONB numbers are recursively normalized, and copy decoding preserves Decimal values. An existing computation guard still rounds sufficiently precise Decimals before checking equality. |
| 5. Hard-change details and ordinal identity | **Partly** | Hard-first sorting and truncation disclosure are fixed. A separate, genuinely ordinal `ordinal_path` was added; `lord_path` still contains names. Movement matching can nevertheless misidentify a deletion as a move. |
| 6. First seal requires a copy; replay survives | **Partly** | The Python seal flow refuses legacy first seals and includes 1305 in its migration inventory. The authoritative SQL first-seal gate still accepts the legacy shape. Existing SQL replay branches remain unchanged; actual replay was not tested. |

1. **P1 — Database population completeness still depends on what the builder included.**

   [1305:276–280](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:276) derives `(ayanamsha, system, level, tier)` exclusively from the copy. The trigger compares that selected population at lines 314–315; subsequent drift uses the same helper at lines 397–400.

   **Failure:** omit **every AD row**, retaining MD and PD rows and supplying their correct digests. There is no level-2 selector left, so the database never compares against live AD rows. Missing, extra and changed rows are detected only within represented scope. Facts have the analogous subject-selection dependency at lines 192–194.

   The independent capture check correctly queries the fixed MD/AD/PD contract at [inventory_verifier.py:824–858](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:824), but it is a **writer-side call**, not an INSERT invariant. The builder retains direct INSERT permission. Later copy verification still passes `rows, rows` at line 819. My pure-function reproduction detects the omitted AD against an independent population and returns no violations against itself.

   Derive required population scope independently of the submitted IDs, and enforce it during INSERT. This finding establishes an accepted incomplete snapshot, not a demonstrated bypass of every downstream seal check.

2. **P2 — First-seal refusal is confined to the Python flow.**

   [seal_brief.py:240–247](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/seal_brief.py:240) correctly rejects a legacy first seal. However, [1305:379–388](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:379) explicitly permits legacy snapshots whose old digests still match. The SQL seal trigger calls that completeness function at [1206:975](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1206_gochara_search_inventory_completeness.sql:975).

   **Failure:** an older pinned verifier/sealer client can first-seal an otherwise qualified legacy candidate, with valid verification, brief and receipt, after 1305 is installed. No SQL predicate requires its copy.

   Add the requirement specifically to the first-seal branch, preserving the existing integrity-only replay branch. The new test at [test_g12_snapshot_copy.py:413–433](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:413) calls `_build_payload`; despite its name, it performs neither an actual seal nor sealed replay.

3. **P2 — An additional live fact crashes the staleness report.**

   [staleness.py:148–150](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/staleness.py:148) accesses `x["key"]["start_iso"]` for every newly appearing key, including facts. Fact keys contain `fact_id`, not `start_iso`.

   **Failure:** after capture, add a conflicting SUN fact with another ID. SQL detects a changed population, but formatting raises **`KeyError: 'start_iso'`**, so no drift report is returned. I reproduced this using the actual `_changes` function. Restrict movement suppression to dashas.

4. **P2 — A metadata-only dasha tier change becomes hard content drift.**

   The live population is filtered by the **copied tier** at [1305:277–280](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:277).

   **Failure:** change only a consumed row’s `verification_pass_status` from `two_pass_verified` to another tier. Its natural key and numerical content remain unchanged, but it disappears from the live population. The content digest changes and completeness reports hard `input_snapshot_drift`, contradicting the explicit soft-tier contract at [staleness.py:34–37](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/staleness.py:34).

   Capture eligibility and later content/metadata comparison need separate selection rules.

5. **P2 — Ordinal movement matching still confuses deletion with movement.**

   [1305:216–233](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:216) computes ordinals by counting current siblings. Deleting an earlier sibling renumbers later siblings. [staleness.py:127–136](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/staleness.py:127) accepts the first ordinal match, including a live row already matched to another stored natural key.

   **Failure reproduced:** stored Venus MD at 2000 has ordinal 1; Sun MD at 2020 has ordinal 2. Delete Venus; Sun becomes ordinal 1. The formatter reports Venus **“moved” to 2020**, and separately reports Sun’s ordinal changing.

   Movement matching must exclude already matched rows and require an unambiguous correspondence. Hard-first sorting and truncation disclosure themselves passed my pure-function check.

6. **P2 — The no-live-read tests do not enforce the required boundary.**

   [test_g12_snapshot_copy.py:384–394](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:384) drops L1 tables but runs only inventory and coverage. Lines 403–410 exempt nine entire files and match only literal uppercase SQL.

   **Failure scenario:** reintroduce `fetch_chart_context(...)` in the later record substep. The grep sees no new SQL table reference, and the table-drop test never executes that substep. Both guards pass. A direct live query added inside an allowlisted file also passes the static guard.

   Exercise every computational substep with live reads forbidden, or instrument the connection/helper boundary. The current normal-copy implementation is improved; its regression protection is incomplete.

7. **P2 — The generated writer digest is stale after round 2.**

   [nirmana-writer-digests.json:90](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/src/generated/nirmana-writer-digests.json:90) contains `365da8ded9f509497…`. Recomputing with the repository’s source-closure hash functions gives:

   `22950ba665ac6fe592c407fb0454cdbbb0b29f101f3d300a45479aa6290cf0e4`

   **Failure:** the generated provenance inventory no longer identifies this writer’s code; its `--check` comparison rejects the artifact at [provenance_inventory.py:46–52](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/pipeline/orchestrator/provenance_inventory.py:46). The census’s internal hash and inventory-file fingerprint match, but they match the stale inventory. Regenerate both dependent artifacts.

8. **P2 — End-to-end numeric computation retains a pre-existing precision hole.**

   This is **not introduced by this diff**, but limits the requested exactness claim. [targets.py:88](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/targets.py:88) and [inventory_verifier.py:175](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:175) compare against `Decimal.normalize()`, which applies the decimal context’s precision.

   **Failure reproduced:** `Decimal("12.50000000000000000000000000001")` is accepted as float `12.5` under the default context. The SQL snapshot/hash preserves the difference; computation silently loses it. Compare against the original Decimal without context-rounding it first.

The remaining live L1 reads in the reviewed v5/kernel call graph are:

| Read sites | Classification |
|---|---|
| [chart_context.py:48, 111–116](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/chart_context.py:48) — `chart_facts` | Snapshot capture; also post-snapshot legacy, missing-column and missing-snapshot fallback. |
| [dasha_read.py:85, 105–111, 162–167](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/dasha_read.py:85), delegating to `gochara_grammar/dasha_data.py:220` — `chart_dashas` | Build census and period capture; same post-snapshot legacy/missing-copy fallback. |
| [inventory_store.py:196](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/inventory_store.py:196) — `chart_dashas` | Legacy ledger input; new snapshots use copies. |
| [inventory_verifier.py:184, 585, 843, 850, 853](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:184) | Facts/ledger legacy branches; independent live build census, consumed-row and complete-population queries at capture. Legacy verification also takes these live paths. |
| [record_verifier.py:34–35](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/record_verifier.py:34) — `chart_dashas` | Legacy arm of a UNION. New-copy execution disables that data arm, but the SQL still requires the live relation and permissions. |
| [seal_brief.py:329](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/seal_brief.py:329) — `chart_facts` | Legacy natal-tier disclosure. |
| [1305:155, 177, 190](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:155) — `chart_facts` | Database copy construction and intentional live-population comparison. |
| [1305:208, 211, 220, 224, 227, 231, 246–247, 256, 275](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:208) — `chart_dashas` | Database copy/population construction, including ancestors and sibling ordinals; intentional drift reads. The Moon-domain legacy fallback at line 340 also invokes these helpers. |
| [1206:273, 289](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1206_gochara_search_inventory_completeness.sql:273) | Old facts/dasha digest functions, retained for legacy capture and drift. |
| `staleness.py:63–66, 84–85, 167–170`; `verification_job.py:556`; `seal_brief.py:248` | Indirect live reads through the above SQL helpers/completeness gate: reporting and candidate admission, rather than copy-based numerical derivation. |

The writer’s later context reads at `ka_gochara_v5.py:951,1066` and P1 reader at `1152` now use snapshots. Shared grammar readers outside this call graph remain unrelated live readers; comments and privilege-table declarations are not data reads.

Migration and consistency checks:

- **1305 remains additive:** four nullable columns, a NOT VALID CHECK, a new trigger and helpers; no previously applied migration is edited. Existing immutability and sealed-write guards remain.
- **Preflight fails closed in source:** missing prerequisites, reapplication, G8-first ordering and unexpected prior function definitions are rejected at [1305:59–97](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:59). Actual PostgreSQL-rendered hash pins and effective role privileges were not verified.
- **Replacement bodies checked:** completeness is the prior 1232 body with the declared drift block replaced; Moon-domain changes its declared source to the copy/legacy helper. Identity recipes remain unchanged, although component values change.
- **1306 stacking is unproved:** 1306 is absent. The ordering test substitutes a comment marker, not the real later replacement. Actual `1305 → 1306` must demonstrate that 1306 retains these edits.
- **Implementation lock matches:** recomputed digest `113d01e3e5a7c077…` matches [implementation_digest.lock.json:2](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12b/platform/python-sidecar/services/gochara_kernel/implementation_digest.lock.json:2). This does not cure the separate generated writer-digest mismatch. Locking/concurrency behavior was inspected, not exercised.

The added tests discriminate several fixes, especially database-overwritten forged copies and exact SQL numeric drift. They miss whole-level omission, added-fact reporting, tier-only drift, deletion-induced ordinal reassignment, all computational substeps, and actual first-seal/replay. The nested-JSON test exercises normalization, not a full tiny-value-change round trip. The mutation harness was not run; its source counts any nonzero pytest result as a killed mutation, so infrastructure failure alone is insufficient evidence.

I executed source-only reproductions, two pure source tests, Python syntax parsing, function-body comparisons, hash checks and `git diff --check`. **I did not run PostgreSQL, database tests, migrations, the mutation suite, restricted-role execution, concurrency tests, a full build/seal/replay, or actual 1306 stacking. No network was used and no files were modified.**

