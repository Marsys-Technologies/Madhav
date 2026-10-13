```json
{"id":"KV3-B-KYALLOC",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source under fleet/** (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§1.3, §3, §5 Migration allocator, §7, §8.1, §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"platform/scripts/governance/reserve_migration_number.py","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"whole file","sha256":"61fd1664d7099b57d0862ce6bd1169c666ffc402179c924ded12f4b0ff96469a"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyalloc.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyalloc.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyalloc.py -q -p no:cacheprovider",
"expected_result":"exit 0, nothing skipped; concurrent allocation, restart/reuse and conflicting external reservation all shown",
"negative_cases":[
"two concurrent writers never receive the same number",
"a number claimed externally is reported as conflicted (exit 3), never reissued or silently renumbered",
"an unreadable claim table or ref reserves nothing (exit 4)",
"a corrupt store is never rewritten from empty (exit 5)"]},
"packet_sha256":"4bee0b80d8386ae3134cae2fe840a13df916c69dc5b608e555ac30f782e5e370"}
```
# PACKET KV3-B-KYALLOC v1: `kyalloc.py`, the migration allocator

**Pins.** Plan v2.7 @ `e709f60d7` (hash above); base = the reviewed B-0c head the job header carries.

**Owns.** The two `d1_paths` (Python >= 3.9, standard library only). Prohibited: FROZEN paths, every other file — `platform/migrations/**` and `platform/scripts/governance/reserve_migration_number.py` are read-only references.

**Spec (verbatim).**
```excerpt plan §5
**Migration allocator** (`kyalloc.py`): an atomic, persistent reservation keyed by
  item/branch against the repository-wide migration namespace and active reservations;
  all concurrent migration writers observe the same authority; until it is installed,
  the existing reservation procedure stays in force. Tests: concurrent allocation,
  restart/reuse, conflicting external reservation.
```
```excerpt plan §3 Cut
NEW ITEM reports and the
reservation ceremony (replaced by the allocator for migration numbers and the item
lock for shared worktrees — not merely by a typed block)
```
```excerpt plan §8.1
Never `main_sha`, never a migration number (allocated at
   job start).
```
```excerpt plan §1.3
Deterministic first: scheduling, claims, locks, gates, routing, allocation, test
   installation, regeneration, metering are scripts with tests and negative fixtures.
```
Plan §7: the job header carries the allocated migration number, if any.
Reconciliation: the existing reservation procedure is `platform/scripts/governance/reserve_migration_number.py`: ONE sequence over `platform/migrations/` and `platform/supabase/migrations/` (file names `^(\d+)_`); external claims are the rows under `## 2. MIGRATION NUMBER CLAIMS` in `origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` (first cell a number or a range such as `558–563`); next = max + 1; an unreadable claim table refuses instead of guessing. This packet changes none of that and puts nothing in force (installation is B-2).

**Contract.** `python3 -I -B kyalloc.py <verb> …`. Env `KY_RUN` (default `${KY_ROOT:-/Users/Dev/kalayantra}/run`). git = `${KY_GIT:-/usr/bin/git}`, read-only verbs only (`rev-parse`, `ls-tree`, `show`); never a fetch, push or commit; writes only under `$KY_RUN/alloc/`.
The one authority: `$KY_RUN/alloc/migrations.json` = `{"schema": "ky.alloc/1", "reservations": [{"item", "branch", "numbers": [int], "status": "active" | "consumed" | "released" | "conflicted", "reserved_at", "observed": {"ref", "ref_commit", "disk_max", "claims_max", "claims_blob"}, "conflict": null | {"number", "with"}}]}`. Every mutation: exclusive `flock` on `$KY_RUN/alloc/.lock`, the store re-read inside the lock, written as temp + fsync + rename, then one line appended to `$KY_RUN/alloc/journal.jsonl`. An unreadable store is never rewritten from empty.
Namespace — INTERPRETATION of "repository-wide migration namespace": the numbers in both migration directories at `--ref` (default `origin/main`) of `--repo`; the claim table at `--claims-ref` (default `origin/campaign-coordination`); every number this store ever reserved, whatever its status. Ruling P12: a number already claimed on that table (1351–1356 and 1362 included) is part of the namespace and is never handed out; there is no adoption verb.
- `reserve --item ID --branch B --repo R [--count N]` (N default 1). The key (ID, B) already has a reservation that is not `released`: the same numbers, `reused: true` (another N: 64). Otherwise N consecutive numbers from namespace max + 1; gaps are never filled. stdout, one JSON object: `{"item", "branch", "numbers", "status", "reused", "claim_row"}`.
- `check --repo R`: re-observe, update statuses, print the store.
- `release --item ID --branch B --reason TEXT`: status `released`; its numbers are never issued again.
- `show [--item ID]`: print; changes nothing.
Status rules — INTERPRETATION of "conflicting external reservation" — applied by `reserve` and `check` to every active reservation: a reserved number present at `--ref` under a migration path that also exists in the reservation's own branch (`refs/remotes/origin/B`, else `refs/heads/B`) is `consumed`; present at `--ref` otherwise, or named by a claim-table row lacking the token `kyalloc:ID@B`, it is `conflicted` (both parties recorded) — never silently renumbered, never given to another key. `claim_row` is the ready-to-paste table row carrying that token; publishing it stays the existing procedure's conductor action (the allocator never writes the claim table).
Exit: 0 ok · 3 a reservation the call concerns is `conflicted` (`check`: any) · 4 namespace unreadable (ref or claim table), nothing reserved · 5 store unreadable · 64 usage.
No existing component calls kyalloc; the dispatcher will, at job start.

**Depends on.** Wave 1; nothing. The dispatcher packets (KV3-B-KYD*, waves 3–4) may assume `reserve` as above: exit 0 and `numbers`.

**Acceptance.** The front-matter command; tests first, `KY_RUN` a temp directory; fixture repositories are built with `git init` in the test's temp directory (a main ref, a claims ref holding single numbers and a range, both migration directories, item branches):
1. Concurrent allocation: at least 8 processes with distinct keys get distinct, gap-free numbers above the namespace max, a valid store and one journal line each; one key from several processes gets one reservation.
2. Restart/reuse: a new process returns the same numbers and consumes nothing, also beside a stale temp file left by a killed writer; a `--count` mismatch is 64.
3. Conflicting external reservation: the reserved number appears at `--ref` from another branch, or in a claim row without the token: exit 3, `conflicted`, not reissued; a row with the token leaves it `active`; merged from its own branch it is `consumed`.
4. Namespace: both directories and a claim-table range raise the max; with rows `1351–1356` and `1362` on the table none of those seven is ever issued and the next number is above them; an `adopt` verb is 64; a missing ref or claims ref is exit 4 with the store byte-identical.
5. A corrupt store is exit 5, bytes unchanged; released numbers never return.
6. A recording git double shows only `rev-parse`, `ls-tree` and `show` are ever run.
Every status is observed from git and the store in that very call; an unreadable source is exit 4 or 5, never a number.

**Evidence.** `$JOB_SCRATCH/result.json` (card BS-16): each command run with exit code and summary; branch; pushed 40-hex `head_sha`; `pr_number`.

**Branch and PR.** `kalayantra/kv3-b-kyalloc`; one PR to main, "KĀLA-YANTRA v3 KV3-B-KYALLOC: kyalloc.py"; the job never merges, queues or approves it; under the hold nothing merges.

**Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, a database, the network (other than your branch's push and PR), the tracker, the plan, cards, schemas or other packets; create or number a real migration. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
