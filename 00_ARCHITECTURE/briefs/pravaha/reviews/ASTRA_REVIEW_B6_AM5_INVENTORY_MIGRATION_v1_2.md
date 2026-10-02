---
artifact: ASTRA_REVIEW_B6_AM5_INVENTORY_MIGRATION
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: "2026-10-02"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: ffc4b5b05
authority: "Review only; authorizes nothing."
---

**Verdict: ACCEPT_WITH_AMENDMENTS.** R6 is closed, and R1–R4 remain closed. R5 is **PARTLY** closed: its remaining deployment-creator defect is repaired, but the restricted-sealer replay test and its claimed permission list are incomplete. That is a follow-up before provisioning that sealer, not a reason to reopen the builder-grant blocker.

**No merge-blocking amendment remains for the reviewed migration scope.** This does not establish production readiness, verifier independence, or completion of the deferred writer/manifest work.

I reviewed `ffc4b5b05fb6c98ac4a7d2b46d1628e052f04edd`, the v1.1 review, and the normative documents on locally available `origin/campaign/pravaha`, finally checked at `04d207167`. No fetch was performed.

File-reference abbreviations:

- **SQL** — [1206_gochara_search_inventory_completeness.sql](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/migrations/1206_gochara_search_inventory_completeness.sql)
- **DB** — [gochara_b6_am5_search_inventory.db.test.ts](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/tests/integration/gochara_b6_am5_search_inventory.db.test.ts)
- **MUT** — [mutation_check_1206.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/scripts/gochara/mutation_check_1206.py)
- **AM5** and **IDENTITY** — respectively `GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT.md` and `IDENTITY_CANONICAL_BYTES_CONTRACT_v1_0.md`, under `00_ARCHITECTURE/briefs/pravaha/design/` at that campaign commit.

**1. Fidelity and closure of previous findings**

| Finding | Judgment | Evidence |
|---|---|---|
| **R1 — commitment equality lacked owning path/version scope** | **CLOSED** | Equality and diagnostics use the full owning key: chart, generation, class, path, version and obligation ID. **SQL:850–878; DB:642–698.** Cross-path/version borrowing regressions pass in inspected CI. |
| **R2 — snapshot convention was unbound** | **CLOSED** | Snapshot insertion checks the publication bridge; first sealing checks publication and claimed partitions, including absent bridges. **SQL:608–615,750–794; DB:778–809.** Records/windows are unnecessary for these checks. |
| **R3 — excluded pin accepted NULL reason** | **CLOSED** | Explicit non-NULL enforcement closes both NULL-reason variants. The new reason remains inside the closed grammar. **SQL:404–417; DB:892–907.** |
| **R4 — session-dependent digest rendering / wrong audit column** | **CLOSED** | L1/dasha helpers pin UTC and float rendering, exclude actual `computed_at`, and scope rows to the chart. Timezone, audit-only and material-change regressions remain. **SQL:262–291; DB:575–613.** |
| **R5 — database, principal, concurrency and mutation evidence** | **PARTLY** | The outstanding creator-default regression is now exercised correctly. However, restricted-sealer replay is not exercised, despite the fixture claiming complete sealer permissions. **DB:211–229,442–464,1222–1245.** See questions 4 and 6. |
| **R6 — missing builder EXECUTE under governed defaults** | **CLOSED** | Explicit grants cover twelve new helpers and five prerequisite functions. Real migrations are applied as `amjis_app` with PUBLIC function execution revoked; construction/finalization succeeds as the builder. Each of the seventeen grants is independently revoked and demonstrated necessary. **SQL:1013–1036; DB:615–627,858–889.** |

The central AM-5 structural contract is implemented:

- A single immutable input snapshot binds the generation, inventories and intervals.
- Finalization is one-shot and checks both stored digests.
- Committed obligations equal stored obligations within each owning pin.
- Every obligation must cover the entire manifest horizon using qualifying searched states.
- Missing inputs, unaccounted registry versions, input drift and partition mismatches refuse first sealing.
- Replay recomputes sealed inventory integrity without demanding later registry versions or current live-input equality.

Evidence: **SQL:307–480,620–679,735–924,930–978**.

It is **not an exact implementation of every earlier v0.5/v0.6 statement**, for these disclosed reasons:

1. **Stronger verification policy.** Every verification row must agree, rather than merely requiring one matching row. A stale disagreeing row blocks sealing, but can be deleted before sealing. **SQL:915–924; DB:718–739; AM5:641–651.**
2. **Changed ledger bytes and stricter bounds.** The `input=` header binds even an empty ledger; whole-second bounds constrain representation. These must accompany the updated canonical vectors and specification. **SQL:49–79,545–557; AM5:633–639.**
3. **F-3 is only partly implemented here.** The new version checks address version selection, but SQL does not enforce the complete writer token/domain contract, registry case-alias prohibition, or serving census. Current fixtures still use identity forms whose replacement is explicitly deferred in **IDENTITY:119–125,156–169**.
4. **F-6 remains deferred.** The aggregate helper exists, but this migration does not incorporate `inventories_digest` into manifest construction or compare replay against an independently stored aggregate commitment. It relies on immutable sealed rows and their recomputation. **SQL:561–569,930–947; AM5:687–694,1281.**

The two requested additions are correct:

- `superseded_by_version` is a structured, non-degrading exclusion: it requires a basis and forbids a ruling reference. **SQL:404–417.**
- `multiple_included_versions` enforces at most one included version per class/path within the generation. **SQL:806–814.**

The additional `superseded_without_included_version` detector is also appropriate: a supersession claim must identify, structurally, another included version of that same path/class/generation. It cannot borrow one from another class or generation. A `computed_empty` replacement does not satisfy this particular assertion. **SQL:818–827; DB:810–856; IDENTITY:114–116.**

**2. Migration safety, ordering, locks and cost**

The migration remains additive against the inspected predecessor definitions. It does not replace existing 1153–1157 functions, constraints or triggers. The new trigger on the existing seal table is **SQL:981–983**. Existing-object fingerprint checks also pass in CI at **DB:426–482**.

There is one intentional qualification: **five existing functions receive additional ACL grants**. Their definitions are unchanged; their privileges are changed deliberately.

Three different forms of replay must remain distinguished:

- The migration runner skips an already-recorded, byte-identical migration.
- Directly executing 1206 twice deliberately fails its gate.
- Repeating a generation seal invokes the sealed-integrity branch.

Thus the file is runner-idempotent, not freely executable twice. **SQL:130–194,950–978; [migrate.ts:797](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/scripts/migrate.ts:797).**

The existing `..._write_guard` sorts before the new `..._z_search_complete`. Publication, coverage-drift and membership checks therefore still execute first, including during replay. PostgreSQL documents alphabetical ordering for equivalent triggers. [PostgreSQL trigger ordering](https://www.postgresql.org/docs/16/trigger-definition.html).

Locking follows **chart EXCLUSIVE → global SHARED**:

- Row guards acquire the chart lock before inspecting seal state.
- Pin/obligation paths obtain the registry lock.
- UPDATE/DELETE statement guards establish chart context before tuple work.
- The new seal guard independently takes both locks before its registry reads.

Evidence: **SQL:585–586,661–662,700–720,954–955**; predecessor lock functions at **1153:430–485**.

The orchestrator uses `hashtext(chart_id)` for its main-connection lock; the governed chart family uses `hashtext('gochara5:chart:' || chart_id)`. The competing-session regression checks that the former does not block the worker. **DB:1106–1155; [locks.py:13](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/python-sidecar/pipeline/orchestrator/locks.py:13).**

I found no new lock-order inversion **under the governed protocol**. Existing writers must still acquire the family lock before legacy publication/coverage DML. The new guards cannot repair a writer that first holds a legacy tuple lock and subsequently requests the chart lock.

Seal insertion performs synchronous input hashing, registry accounting, digest recomputation, commitment checks and per-obligation range aggregation while holding these locks. CI measured **55 ms for the completeness function alone**, with 27 classes × 40 obligations × 2 intervals. It did **not** measure total seal-insert latency; its input fixture has only two facts and two dasha rows. **DB:1213–1218.**

**3. Partial-search acceptance and legitimate-completion refusal**

I reran **W2 exactly as specified**, separately from the broader database fixture:

- Only P1 and P5a registered.
- Both pins included, each with its own nonempty committed set.
- All P1 obligations stored and fully covered.
- No P5a obligations stored.
- Verification merely rehashes the stored inventory.

It produces **`committed_set_mismatch` for P5a**. The extracted SQL predicate independently rejects the same omission.

The database test labelled “W2 exactly” still uses additional excluded P6/P1-version pins through `goodBuild`; it tests the same defect but is not literally that minimal row set. **DB:107–108,392–419,631–639.**

My additional predicate probes checked borrowing across path, version, class and generation; restored-obligation controls; multiple included versions; valid supersession; and attempted supersession borrowing across class, generation or path. They behaved as required.

These independent predicate executions used an in-memory SQLite adaptation of the relevant SQL expressions, **not PostgreSQL trigger execution**. The author’s PostgreSQL adversaries were verified through CI.

Within the declared-inventory/trusted-verifier boundary, I found no remaining structural counterexample that pools different obligations’ coverage, substitutes another snapshot, or hides an omitted committed obligation.

The boundary remains material:

- A false `computed_empty`, or a falsely reduced commitment accompanied by a matching purported verifier digest, can pass structural checks. AM-5 assigns truthful derivation and independence to O-RP-9. **AM5:721–731; DB:699–715.**
- A class absent from both inventory and coverage is not declared complete. Serving must report it as `not_searched` using the normative census. **DB:1053–1057; AM5:710–719.**
- Candidate disagreements and damaged candidate chains remain repairable before sealing through permitted deletion/replacement. **SQL:590,650–658; DB:982–1015.**
- Restricted-sealer replay has the permission defect described next. It does not affect completeness of the stored row set, but can prevent a legitimate replay until the sealer grant is corrected.

**4. Privileges, ownership and separation**

**The builder grant set is necessary and sufficient for the demonstrated inventory construction/finalization workflow.**

The new grants comprise:

- Twelve helpers: hashing, UUIDv8, canonical JSON, UTC rendering, UUID-set validation, input/L1/dasha/AV digest work, inventory preimage, inventory digest and ledger digest.
- Five prerequisite functions: `lock_chart`, `lock_global_shared`, `generation_is_sealed`, `generation_governed`, and `horizon_finite_ok`.

**SQL:1013–1036.** The seventeen individual revoke-and-rebuild tests provide materially stronger necessity evidence than merely inspecting function names. **DB:879–889.**

The role arrangement is sound:

| Principal | Required position |
|---|---|
| `amjis_app` | Migration creator and owner, operating through the governed temporary schema capability. |
| `data_plane_builder` | Grantee: candidate SELECT/INSERT/DELETE, restricted finalization UPDATE, necessary reads and explicit helper execution. |
| Separately authorized sealer | Seal-table INSERT, publication UPDATE, required reads and the complete executable sealing/replay call graph. |
| Independent verifier | Runtime identity and independence remain outside this migration’s proof. |

The builder receives no seal-table INSERT and no execution of `ka_gochara_seal_generation`. Both routes are refused in the role test. Schema creation and TRUNCATE remain refused. **SQL:993–1036; DB:615–627,858–876.**

All seventeen new functions use invoker security and pin `search_path`; there is no SECURITY DEFINER privilege bridge. The fix correctly grants nested invoker callees instead of restoring PUBLIC execution. PostgreSQL applies function defaults from the creating role. [PostgreSQL default privileges](https://www.postgresql.org/docs/16/sql-alterdefaultprivileges.html).

The sufficiency claim has a defined boundary: this demonstrates the inventory workflow with migration 1216 and prerequisite L1 reads. It does not certify every legacy writer path addressed by the separate 1220 work.

**New follow-up — restricted-sealer replay permission is missing.**

The evidence is direct:

1. `SEALER_FUNCTIONS` omits `ka_gochara_search_replay_violations`. **DB:75–83.**
2. The replay branch invokes that function under invoker security. **SQL:964.**
3. Both lifecycle replay calls use `tx(...)` without a role, hence the superuser connection. **DB:157–162,1232,1234.**
4. The fixture and migration commentary nevertheless call the twenty-function list sufficient for the seal path. **DB:460–463; SQL:109–114.**

Consequently, the fixture’s restricted sealer would encounter a function-permission failure on replay. This is a source-established counterexample; I did not reproduce that failure in a local PostgreSQL instance.

Add replay-helper EXECUTE **to the authorized sealer only**, and run initial seal plus both replay calls as that role. Do not add it to the builder. This is a follow-up because 1206 deliberately does not provision the production sealer; it must be resolved before that principal is activated.

**5. Protected-window wiring and rollback**

The checked-in wiring remains correct:

- Deployment lists 1206 after 1204. **[deploy.yml:1085](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/.github/workflows/deploy.yml:1085).**
- The runner’s protected set contains 1206 and routine application is refused. **[migrate.ts:138](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/scripts/migrate.ts:138).**
- My static execution confirmed byte identity between the embedded gate and standalone preflight DO block.
- The workflow pins deployment source and always attempts capability revocation.

These are source checks, not evidence that a protected deployment occurred.

The runner commits migrations separately: failure of 1206 rolls back its own transaction but can leave 1204 committed. **[migrate.ts:830](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/platform/scripts/migrate.ts:830).**

The rollback outline correctly distinguishes unused installation from used installation: remove unused objects in dependency order with ledger reconciliation; after sealing, correct forward. Shared prerequisite grants must not be revoked if another migration or consumer requires them. **SQL:117–127.** This is a documented procedure, not a demonstrated rollback.

**6. Do the tests earn their claims?**

**They earn closure of R6 and substantially repair R5. They do not earn the complete restricted-sealer lifecycle claim.**

I inspected the successful [database CI job 110627192681](https://github.com/Marsys-Technologies/Madhav/actions/runs/36939423754/job/110627192681). Its logs establish:

- PostgreSQL **16.15**.
- **34 passing integration-file tests**: 33 database cases plus the required-URL sentinel.
- Passing creator-default, builder construction/finalization, exact ACL and seventeen individual revoke tests.
- Passing R1–R4, version-selection, competing-session locking, post-seal mutation and registry-advance lifecycle tests.
- **34/34 mutations caught**, zero survivors and zero missing anchors.

CI executed merge commit `d312222982ea743aa5734cb2fa1a6dbb36427a2c`. Comparison with the reviewed head established that the migration, relevant tests and mutation harness were unchanged. These are inspected CI results, not my own PostgreSQL rerun.

My independent read-only executions established:

- **16/16 static test bodies passed**, evaluated in memory using the project TypeScript compiler and Vitest matchers.
- **35/35 campaign model cases passed**, matching the checked-in model output.
- Exact minimal W2 and the additional predicate probes behaved as described.
- All **34 mutation anchors** occur exactly once in the reviewed SQL.

The mutation report needs careful wording. **MUT:115–126** treats any matching test failure as a caught mutation, including static failures; it does not preserve a named behavioral killing test for each mutation. The passing baseline makes the report useful, but it does not prove thirty-four independently demonstrated database behaviors.

The supplied PR body’s **20 database / 10 static / 18 mutation / PG17-only** account is stale. Also, this database job is documented as advisory; `GOCHARA_REQUIRE_DB=1` prevents skipping inside the job, but does not establish required branch protection. **[ci.yml:257](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2867c/.github/workflows/ci.yml:257).**

**Ranked amendments**

**Merge-blocking: none.**

| Rank | Priority | Separate follow-up |
|---:|---|---|
| 1 | **P2 — before sealer activation** | Grant replay-helper execution to the authorized sealer; exercise initial seal and both replays as that role; correct the twenty-function sufficiency claim. |
| 2 | **P2 — before writer/serving acceptance** | Retain the remaining F-3 identity/census obligations and F-6 manifest binding. Update canonical vectors and writer fixtures when the identity contract is adopted; do not describe the two version checks as closing all F-3 work. |
| 3 | **P2 — before protected deployment** | Rehearse with actual runtime principals, prerequisite permissions, writer quiescence and representative input volumes. Measure total seal latency and exercise the applicable rollback/forward-correction procedure. |
| 4 | **P3 — evidence accuracy** | Refresh PR counts, PostgreSQL version and CI commit; preserve mutation-to-test attribution and accurately describe advisory versus required execution. |

**What I could not verify**

I could not rerun PostgreSQL locally: no disposable test database was configured, and the suite creates temporary files/schema state while this review expressly forbids file writes. The mutation harness also rewrites the migration, so I did not run it locally.

I did not verify production ACLs, deployment state, the claim that 1206 is applied nowhere, production sealer/verifier provisioning, O-RP-9 independence, representative production cost, executed rollback, or live branch-protection settings. No production database was contacted.

No file or git state was changed. The detached checkout remained clean at `ffc4b5b05`.