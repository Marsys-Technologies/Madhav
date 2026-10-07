VERDICT: REJECT

**P1 — The new reset relies on resume behaviour that the checked-in orchestrator does not implement.**

The reset at [ka_gochara_v5.py:477](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:477) explicitly assumes completed substeps, including `snapshot`, are skipped. However, `_drive_substeps` only skips keys supplied through `completed_keys`; its default is empty (`asset_runner.py:826,867,875`). The production call at [asset_runner.py:1179](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1179) supplies no completed keys, and the v5 plan always returns all steps (`ka_gochara_v5.py:295–348`).

**Failure scenario:** several classes commit successfully, a later substep fails, and the asset is retried. The retry executes `snapshot` again and deletes those committed contacts, records and windows. A subsequent failure leaves less durable output than before the retry; repeated timeouts cannot make progress through the claimed resume mechanism.

The missing resume plumbing predates this patch, but the new generation-wide deletion depends on it. The new test conceals that integration gap by manually using `head=False`, rather than exercising the orchestrator (`test_a55_replace_chain.py:291–305`).

**Required amendment:** establish durable completion tracking tied to the build’s inputs, including horizon, and exercise the actual retry path. Alternatively, explicitly revise the contract to whole-build replay; the current “resumed build never re-runs it” claim is false.

**P2 — The new integration fixture does not test replacement of a populated complete chain.**

`_World.build()` executes inventory, coverage and record steps only; it never builds windows or persists verification rows. Its state comparison checks selected contact fields, record counts and coverage horizons ([test_a55_replace_chain.py:158](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:158)).

**Failure scenario left uncovered:** rebuilding a previously completed and verified candidate encounters a cascade, trigger or builder-permission problem involving populated window memberships or verification rows. These new database scenarios would not exercise it. Record support or result differences that preserve row counts are also invisible to `state()`.

Add a populated-chain replacement test under the builder role, with windows, memberships, prerequisites and both verification tables present. Include snapshot rollback and preservation of another generation and Moon coverage.

The following answers use checkout-relative file references; Python basenames are under `platform/python-sidecar/`.

**1. Delete completeness and scope**

I found no omitted v5 build-output table or invalid FK ordering in the checked-in migrations.

| Chart × generation table | Replacement treatment and evidence |
|---|---|
| `ka_gochara_eval_window` | Explicit delete, `record_store.py:581`. |
| `ka_gochara_eval_window_record` | Cascades from windows; composite FK includes chart and generation, `platform/migrations/1156_gochara_eval_window.sql:346–353`. |
| `ka_gochara_relationship_record` | Explicit delete, `record_store.py:582`. |
| `ka_gochara_record_prerequisite` | Cascades from records, `1155_gochara_relationship_record.sql:647–649`. |
| `ka_gochara_contact` | Explicit delete of **all** matching contacts, including shared contacts and orphans, `record_store.py:583`. |
| `kala_gochara_coverage` | Explicit delete of matching `event_class` partitions only, `record_store.py:585`. |
| `ka_gochara_search_interval` | Deleted by the following inventory reset, `inventory_store.py:33–38,103–106`. |
| `ka_gochara_search_obligation` | Same, after intervals. |
| `ka_gochara_search_path_pin` | Same, after obligations. |
| `ka_gochara_search_inventory` | Same, after pins. |
| `ka_gochara_search_input_snapshot` | Deleted last, then reinserted, `inventory_store.py:107–109`; `ka_gochara_v5.py:483–487`. |
| `kala_gochara_publication` | Candidate manifest replaced **in place**, rather than deleted, `ledger.py:514–558`. |

Two additional tables are written by the separate verifier:

- `ka_gochara_search_inventory_verification`: removed through the inventory-header cascade (`1206_gochara_search_inventory_completeness.sql:492–496`).
- `ka_gochara_eval_window_verification`: removed through inventory/pin cascades (`1240_gochara_window_verification_gate.sql:183–188`).

The writer itself reports verification without persisting those rows (`ka_gochara_v5.py:593–607`).

The separate publication machinery also writes `ka_gochara_seal_brief`, `ka_gochara_generation_seal` and `ka_gochara_seal_approval`. These are retained audit/sealing records, not rebuild output (`seal_brief.py:426`; `seal_flow.py:76`; migration `1153:990`). A changed candidate must obtain a current brief; retaining historical briefs is intentional.

Shared tables remain untouched: `ka_gochara_sky_convention`, `ka_gochara_physical_object`, `ka_gochara_sky_event`, `ka_gochara_contact_identity`, `kala_gochara_convention`, `ka_gochara_convention_bridge`, and the six registry tables `ka_gochara_predicate`, `ka_gochara_factor`, `ka_gochara_rule_path`, `ka_gochara_rule_path_prerequisite`, `ka_gochara_rule_path_soft_factor`, `ka_gochara_rule_path_seal` (`substrate.py:380,394,424`; `record_store.py:484,783`; `ledger.py:377`; `rule_registry.py:473–493`).

The important restrictive FKs are record→contact/coverage and window→coverage; the deletion order respects them (`1155:542–547`; `1156:300–302`). The deferred prerequisite finalizer returns harmlessly when its record has disappeared (`1155:791–797`).

All explicit deletes carry both scope columns. Cascades retain the same scope through composite FKs. No deletion of another chart, generation or shared reference row was found.

**2. Sealed safety**

Within the required transaction, the check/delete sequence is race-free:

- `_refuse_if_sealed()` invokes `ka_gochara_generation_is_sealed` before deletion (`record_store.py:521–529,578`).
- That SQL function **takes the chart transaction lock before reading the seal** (`1153_gochara_sky_event_substrate.sql:1004–1010`).
- Sealing takes the same lock (`1153:982`).
- The lock helper enforces `READ COMMITTED` and uses `pg_advisory_xact_lock` (`1153:433–453`).

Consequently, a sealer cannot commit between the check and deletion while the writer’s transaction remains open.

Database guards independently refuse sealed deletion of contacts, records, prerequisites, windows, memberships, inventories and verification rows (`1153:1119–1125`; `1155:419–436`; `1206:586–593`; `1240:1087–1094`). Migration 1240 also closes the older contact-enrichment exception for generations carrying `result_policy` (`1240:953–988,1053–1059`).

There are intentional exceptions to the broad phrase “no sealed rows can change”: publication lifecycle transitions, Moon query coverage, and historical pre-policy enrichment rules. This patch does not expand them (`1240:963,966–985`).

**3. Crash, resume, horizon changes and concurrency**

| Scenario | Result from the checked-in code |
|---|---|
| **(a) Crash mid-build, then retry** | The failing substep rolls back; earlier commits survive initially (`asset_runner.py:888–915`). The actual retry replays the snapshot and clears them: **P1**. A crash inside the snapshot transaction rolls back its deletions together. |
| **(b) Completed candidate, fresh dispatch at another horizon** | If the complete writer plan actually executes, the snapshot removes old output before class writes. Shared and orphan contacts cannot retain old bounds. The manifest is updated first (`ka_gochara_v5.py:457–483`). |
| **(c) Changed horizon with snapshot already considered complete** | The driver’s completion identity is only `step.key`; horizon is absent (`asset_runner.py:875`). Keys such as `snapshot` are constant (`ka_gochara_v5.py:121–122`). Reusing a supplied completion set across horizons can skip replacement; supplying every key can leave all old output untouched. **The current production caller does not supply such a set**, so this is a hazard when implementing resume, not a demonstrated current production skip path. |
| **(d) Two concurrent builds** | The normal runner holds a session-level chart lock across the run; the second run defers (`runner.py:1313–1318,1462–1475`; `locks.py:5–17`). Direct callers using only the kernel’s per-transaction lock could interleave between substeps; that lock alone does not protect an entire build. |

`_verify_live_inputs()` does not compare the requested horizon with the manifest horizon (`ka_gochara_v5.py:181–198`). Also, the standard runner currently constructs config with chart and birth parameters only, so arbitrary horizon forwarding is not demonstrated by that call path (`asset_runner.py:1119–1122`).

**4. Conflict comparison**

The comparison covers all **13 supplied non-key columns**. The three key columns select the row. The only schema column intentionally excluded is database-generated `created_at` (`record_store.py:342–369,744–774`; migration `1153:1042–1061`).

- Python `None` comparison correctly distinguishes NULL from a value; there is no SQL `NULL = value` ambiguity.
- Both accuracy columns are `REAL`. Rounding both sides through float4 matches stored precision and introduces no additional tolerance.
- A difference below float4 representability cannot be preserved by these columns anyway. Distinct representable values remain distinguishable.
- Coverage is compared as decoded JSON values; timestamps and other payload fields are compared directly.

I found no legitimate same-input sharing case that should fail: contact geometry is derived over the full domain and clipped to the common build horizon before class-specific record support is applied (`record_store.py:1231–1278,1344–1373`). Point contacts similarly use geometry and horizon, not event class (`record_store.py:230–303`).

I did not execute every class/path combination to prove deterministic equality operationally.

**5. Other callers**

Both residence and point insertions now enforce the stronger check (`record_store.py:812,843`). A direct grain rebuild that changes a shared contact’s bounds without the generation reset now raises instead of silently keeping stale bounds. That is a deliberate behavioural change callers must respect.

The Moon path writes coverage only; it does not insert stored contacts or records (`moon_on_demand.py:183–205`). Its partitions survive the reset.

I found no separate checked-in v5 slice execution path. The existing class/grain deletion functions remain available and unchanged.

v4.1 uses the separate legacy ledger path and plural `kala_gochara_contacts`/`kala_gochara_windows` tables; its writer digest is unchanged (`ka_gochara_v4_41_candidate.py:309–316`; `ledger.py:428–446`; `platform/src/generated/nirmana-writer-digests.json:89`).

**6. Test discrimination**

By source inspection, the extension, narrowing and orphan scenarios meaningfully target the old defect: they compare rebuilt output with a fresh build and/or reject retained out-of-horizon contacts (`test_a55_replace_chain.py:238–274`). I did not run those database tests against either revision.

The sealed and manual-resume tests passing on old code is unsurprising: they are regression guards, not evidence that this patch establishes sealing or orchestrator resume.

**P3 — Certification does not replace the reset guarantee.** The narrowing mutation test explicitly demonstrates that a stale contact extending beyond the requested horizon can pass certification because the comparison clips it (`test_a55_replace_chain.py:380–390`). If replacement is skipped, certification cannot be relied on to catch that case.

Besides P1/P2, important missing coverage includes concurrent sealing, full point-contact conflict behaviour, and changes to every compared field, including both directions of NULL transitions.

**7. Locks, goldens, digests and CI**

The changes are consistent with the implementation:

- Implementation-lock verification passed. Geometry and evaluation hashes changed; window hash did not, matching module ownership (`input_vector.py:54–69`; `implementation_digest.lock.json:2–7`).
- Writer-digest verification passed; only v5’s entry changed (`nirmana-writer-digests.json:90`).
- Decoded golden changes were confined to derived digests, commits, timestamps and manifest identity. I found no changed business outcomes, counts or horizons. The stdout/log payloads agree.
- The census diff contains only its content digest, writer-inventory fingerprint and source revision. I independently verified its content hash and that fingerprint; I did not rerun the full census generator.
- `.github/workflows/ci.yml:424` only adds `test_a55_replace_chain.py` to the existing test command.

**8. Other production-data risks and verification limits**

I found no additional cross-scope deletion, sealed-output corruption or transaction ownership violation introduced by this diff. Replacement remains atomic **per snapshot substep**, not across the entire build; after its commit, later failure leaves an incomplete unsealed candidate. P1 makes the claimed recovery behaviour unreliable.

Reviewed the requested diff through HEAD `5f23de8b756e26a410c69447e708c9245f483bac`. **46 database-free tests passed**: five new tests and 41 existing substep/serializer tests. Digest checks and `git diff --check` passed. The working tree remained clean.

**Not verified:** database integration tests, old-versus-new database execution, applied migrations or production privileges, live concurrency, real ephemeris builds, deployed behaviour, or CI execution. No database or network operations were run, and no files were modified.

