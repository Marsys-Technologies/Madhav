---
artifact: PROTECTED_WINDOW_REHEARSAL_PLAN
version: "1.0"
status: EXECUTABLE CHECKLIST — mechanical part (M1–M4) is scripted and was run once by its author on PostgreSQL 15; operator part (O1–O7) needs the steward/native. Authorizes nothing; touches no production system.
date: 2026-10-02
author: Stream B (Śāstra), item B6.0 — Codex round 8 R8-10 (steward M20261002T032818-fea8)
audience: "Stream C (Kimi) executes M1–M4 on a DISPOSABLE database; the steward owns O1–O7"
files: "runbooks/rehearsal/run_window_rehearsal.sh · prod_ledger_2026-10-02.txt · EXPECTED_WINDOW_SHA256.txt; PR #2919 tests/integration/gochara_b6_rehearsal_volume.db.test.ts"
---

# Protected-window rehearsal — 1204 → 1206 → 1232 → 1233

**What it proves / does not prove.** It rehearses *source, ordering, ownership, privileges, recovery and cost* on a disposable PostgreSQL 15 that mirrors production's ledger, schema ownership, default privileges and roles. It is **not** evidence about production itself (no production credential is used or needed) and it does not exercise the not-yet-existing sealer/verifier principals in production — it proves the *proposed* least-privilege sets.

## 0. The exact inputs (record them in the rehearsal record)
| item | value at this plan |
|---|---|
| **1204** (AM-7) | PR #2817 head `b9d5d2718` — file sha256 `a0b267f7ef6002a1…` |
| **1206** (AM-5, v1.2) | PR #2867 head `fc10a91fe` — `1ec9008f36782029…` |
| **1232** (AM-14) | PR #2909 head `358c33211` — `f2ef6406604b819d…` |
| **1233** (AM-21 part 2) | PR #2919 head `3994a57dc` — `958b911703eee352…` |
| 1153–1157 | applied in production; re-applied in the rehearsal through the real runner (hashes in `EXPECTED_WINDOW_SHA256.txt`) |
| **application head** | the steward names the deployment ref (the integration of the four PRs over `origin/main`; the reviewed writer head was `f4767b0e6`). **The rehearsal runs on that ref**: `git worktree add <dir> origin/main && git -C <dir> merge <#2817> <#2867> <#2909> <#2919>`; record `git rev-parse HEAD`. |
| window wiring | `platform/scripts/migrate.ts` `PROTECTED_PUBLIC_SCHEMA_MIGRATIONS` and `.github/workflows/deploy.yml` (`gochara_contracts_schema_migration`) list exactly: 1153–1157, 1204, 1206, 1232, 1233 |
| **PostgreSQL** | production is **15.18** (Cloud SQL); the rehearsal MUST run on PostgreSQL **15** (CI's advisory DB job is `postgres:16` — not the target) |
After **any** change to a window file regenerate `EXPECTED_WINDOW_SHA256.txt`: `(cd platform/migrations && shasum -a 256 <the nine files>) > runbooks/rehearsal/EXPECTED_WINDOW_SHA256.txt`; the script refuses a mismatch.

## M1 — the real invocation against a production-shaped ledger (SCRIPTED)
`PGPORT=<disposable pg15 port> REPO=<integration worktree> runbooks/rehearsal/run_window_rehearsal.sh` — loopback only, creates database `gochara_rehearsal`.
It builds: schema `public` owned by **`data_plane_schema_owner`**, `amjis_app` (LOGIN, USAGE only, **CREATE only inside the window** — `GRANT/REVOKE CREATE` exactly as `jataka-schema-capability.ts`), `ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC`, roles `data_plane_builder`, `gochara_sealer`, `gochara_verifier`; the 1081/1087/1152 parents; and the **ledger = the production `_migrations_applied` filenames as of 2026-10-02** (912 names, `prod_ledger_2026-10-02.txt`; refresh it with a read-only `SELECT filename FROM _migrations_applied` before the real window).
Then, with the **real** `npx tsx scripts/migrate.ts --only <the deploy list>` (`ONLY` = the list `deploy.yml` builds):
| step | expected | status on 2026-10-02 |
|---|---|---|
| S3a the invocation against today's ledger | **REFUSED**: `--only would jump unapplied predecessor migration(s): 1230_ka_gochara_registry_revert_1091_pin.sql` — nothing from the window applied | **reproduced** |
| S3b the routine deploy applies 1230 (a routine migration, merged in #2889, not yet applied in production) | prerequisite of the window | represented by its ledger row |
| S3c per-file failure recovery: force 1233 to fail | 1204, 1206, 1232 stay committed (**separate file transactions**); 1233 not recorded, no partial columns; after removing the cause the **same invocation** applies only 1233; all four recorded exactly once | **reproduced** |
| S4 ownership | every `ka_gochara_*` function and table owned by `amjis_app`; `amjis_app` holds **no** CREATE after the window; **no** `ka_gochara_*` function has PUBLIC EXECUTE | **reproduced** |
**The ledger precondition (the answer to Codex's `migrate.ts:756–763` point).** `--only` refuses every unselected, unapplied file whose number is ≤ the highest selected number. Against the 2026-10-02 production ledger exactly **one** such file exists: **`1230_ka_gochara_registry_revert_1091_pin.sql`**. So the single deployment invocation works **only after the routine deploy has applied 1230** (or 1230 is otherwise recorded). The live fixtures' intervening 1216 application is *not* the proof — the production ledger already holds 1216/1220/1225/1231.

## M2 — role behaviour, applied under the deployment-faithful mirror (SCRIPTED + existing suites)
Run on PG15 (`GOCHARA_REQUIRE_DB=1 GOCHARA_A51_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:<port>/gochara_a51_test npx vitest run tests/integration/gochara_b6_am5_search_inventory.db.test.ts tests/integration/gochara_b6_am14_moon_domain.db.test.ts tests/integration/gochara_b6_am21_p1_anchor.db.test.ts --no-file-parallelism`) — **55 tests, passed on PG15.17 on 2026-10-02**: initial seal and both replays **as the restricted sealer**, builder refusals (permission denied for the seal function, the seal table, seal-side helpers), replay-helper EXECUTE proven necessary, the six-table matrix, the Moon-resolved daśā case (1232), the anchor CHECKs and sealed-generation freeze (1233).
**What each principal must be REFUSED (the script's S4 asserts the privilege part; the suites assert the behaviour):**
| principal | must be refused | status |
|---|---|---|
| `data_plane_builder` | seal function, `ka_gochara_generation_seal` INSERT, completeness/replay checks, 1232's two helpers, any UPDATE beyond `(inventory_digest, ledger_digest, finalized_at)` on the inventory header | **asserted** |
| `data_plane_builder` | **writing independent-verification rows** (`ka_gochara_search_inventory_verification` INSERT/DELETE) | **FINDING — currently GRANTED** (1206 §7 line ~993). PC-4 requires removal; see O4 |
| `gochara_sealer` | any inventory/record/window content write | **asserted** |
| `gochara_verifier` (proposed) | writing obligations, intervals, records, windows; sealing | **asserted** (proposed set: SELECT on inventory/snapshot/pin/obligation/interval/record/window/coverage + L1 facts/dashas; INSERT on the verification table only) |
| `PUBLIC` | EXECUTE on any `ka_gochara_*` function | **asserted** |

## M3 — realistic 26-class volume, contention and seal timing (HARNESS, opt-in)
`GOCHARA_REHEARSAL=1 REHEARSAL_OUT=<file>.json REHEARSAL_OB_PER_PIN=<n> REHEARSAL_INTERVALS_PER_OB=<m> GOCHARA_A51_TEST_DATABASE_URL=… npx vitest run tests/integration/gochara_b6_rehearsal_volume.db.test.ts` (PR #2919). It builds the **26 classes** (the registry's 27 minus `birth_anchor`, its epoch tautology — **confirm with Stream A**) as the builder, then seals as the sealer, then times the replay check; and runs a builder transaction on a second generation while the sealer seals the first. **It invents no pass/fail bound** — the steward sets what is acceptable.
Indicative result, **PostgreSQL 15.17, one laptop, synthetic rows, no competing load** (not production-shaped; replace with Kimi's run on the real obligation counts):
| scale (26 classes × 3 included pins) | obligations / intervals | construct | finalise | **seal** | replay check | other-generation builder write during seal |
|---|---|---|---|---|---|---|
| 30 ob/pin × 3 intervals | 2 340 / 7 020 | 1.11 s | 0.12 s | **64 ms** | 49 ms | waited ≈ 28 ms |
| 96 ob/pin × 8 intervals | 7 488 / 59 904 | 7.47 s | 0.82 s | **453 ms** | 386 ms | waited ≈ 422 ms (≈ the seal) |
Reading: sealing is cheap at these volumes and **serialises with other writes on the same chart** (the chart family key) — a builder write to another generation waits for the seal. The real obligation counts per class come from Stream A's inventory (`REHEARSAL_OB_PER_PIN`; the harness generates up to 96 distinct tuples per pin).

## M4 — gaps the rehearsal found (to be closed before restricted execution (c))
1. **The eval-window write path has NO grants.** 1216 explicitly DEFERS `ka_gochara_eval_window` and `ka_gochara_eval_window_record` ("no write path exists yet"), and 1220 covers only the contact/record writer flow. The builder therefore cannot write a window or its membership today. Static analysis of 1156's guards predicts, beyond SELECT/INSERT on the two tables: EXECUTE on `ka_gochara_facts_horizon(jsonb)`, `ka_gochara_membership_violation(jsonb,uuid,text,jsonb,tstzrange[])` and `ka_gochara_text_array_ok(text[],integer)` — **to be confirmed and completed by the 1206-R6 method** (run Stream A's window-writing flow as the builder under the mirror; add one EXECUTE per `permission denied for function X` until it converges). A grants-only migration (proposed **1234**, routine route like 1216/1220) is the vehicle. 1220 is not evidence for this flow (Codex R8-10).
2. **Builder verification-write capability** (above) — a grants-only change (REVOKE INSERT/DELETE from the builder; GRANT INSERT to a provisioned `gochara_verifier`); it changes the accepted 1206 §7 behaviour and the live suites' `verify` helper (which runs as the builder), so it needs the steward's word.
3. **Sealer and verifier principals are not provisioned in production** (only `amjis_app`, `data_plane_builder`, `data_plane_migrator`, `data_plane_schema_owner` exist).
4. **The routine migration 1230 must be applied before the window** (ledger precondition).

## Operator part (the steward / native; nothing here is scripted or authorised by this plan)
| # | step | evidence to record |
|---|---|---|
| O1 | name the deployment ref; regenerate `EXPECTED_WINDOW_SHA256.txt`; refresh `prod_ledger_*.txt` with a read-only ledger query | integration SHA; ledger snapshot date |
| O2 | have the routine deploy apply **1230** (or record it); re-run M1 S3a → expect it to proceed to the window | ledger shows 1230 |
| O3 | rerun M1–M3 on PG15 at the real obligation counts (Kimi) | the JSON from M3, the script transcript |
| O4 | decide M4.1 (author 1234) and M4.2 (verifier split); provision the sealer and verifier principals with the exact grant sets the suites/script use | role/grant evidence from a read-only query after provisioning |
| O5 | dispatch the protected window: `deploy.yml` with `gochara_contracts_schema_migration=true` (the capability is granted and revoked around the run) | the run URL; ledger rows for 1204/1206/1232/1233 |
| O6 | post-window read-only checks: table/function owners, PUBLIC EXECUTE count (0), `has_function_privilege` matrix per role, the four ledger rows, the three CHECK names on the record table | query outputs |
| O7 | actual-role evidence: initial seal + both replays under the real sealer on a disposable restore or a real candidate; builder refusal; verifier access | transcripts |
