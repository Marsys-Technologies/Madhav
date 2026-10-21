# Executor pin shards (SR-CHURN-CUT 3, extended by SR-CHURN-CUT 5)

**The rule: adding or changing one executor kind adds exactly one new file here, `<ITEM>.json`, plus the kind's own `fleet/executor_ops.json`
entry, code and tests. It edits no census line and no hash pin in any test.** CI refuses a diff that changes a kind in `executor_ops.json` without a
shard that names it, and refuses an edit to a frozen BASE literal of the census tests (`generated_paths.py`: `kind_shard_required`,
`frozen_base_violations`; the BASE names are listed in `platform/scripts/governance/generated_paths.json` `frozen_base_literals`).

Format and rules: `fleet/executor_pin_shards.py`. Schema `ky.executor_pin_shard/2` is a superset of `/1` (a `/1` shard stays valid). Optional keys:

| key | what it pins | consumed by |
|---|---|---|
| `entries` | the exact `executor_ops.json` entry of each kind (key order included); a known kind is replaced in place, a new one inserted after `after` | `test_executor_table.assert_table_matches_pin`, `test_operation_adapters`, `test_w4_smalltest_enablement`, `test_operation_dryrun` |
| `classes` | hand-declared safety classes per kind: `signed_only`, `cancel_lane`, `mechanical_exempt`, `remote_async`, `teardown`, `no_dryrun`, `dryrun_census`, `marker_client_env`, `marker_in_process`, `marker_no_database`. The **full** class set of a kind replaces its earlier one; `[]` removes all | `test_executor_mechanical_production`, `test_executor_mechanical_acceptance`, `test_executor_a8` |
| `w4_bindings` | `[needs, script, fixed_args, allowed_args, production, timeout_s]` of a kind | `test_w4_smalltest_enablement` |
| `function_hashes` | `{"W4" \| "K9": {function: sha256}}` of the `executor.py` function or constant segments the boundary test treats as reviewed additions; a later shard replaces a digest | `test_executor_table.boundary_violations` |
| `rebase` | `true` only for the cockpit compacting shards into the BASE literals | the CI guard |

Everything in a shard is **hand-written and reviewed**. The BASE literals in the tests, the shards and `executor.py` / `executor_ops.json` are three
independent declarations; nothing here is generated from `executor_ops.json` or `executor.py` (§N.8). `classes` and `function_hashes` in particular state
what the executor *must* be: take the digest of the function you reviewed, not of whatever the file now holds, and declare the class from the doctrine
(`MECHANICAL_ACCEPTANCE_v1_0.md`: deletions and serving changes are never mechanical), not from `executor.py`.

Shards apply in file-name order after the BASE literals. A merged shard is never edited or removed (CI refuses it); the next change to the same kind
is a new shard that replaces the entry, the classes or the digest. Folding is idempotent, so compacting shards into BASE leaves the old shards harmless.
`pending/` is not loaded: a shard parked there is inactive until it is moved up.

Draft a shard with
`python3 fleet/executor_pin_shards.py scaffold --item <ITEM> --base <executor_ops.json at main>`: it drafts `entries` and prints `classes` and
`function_hashes` as `"TODO: hand-review"`, which `load_shards` refuses until they are replaced by reviewed values or deleted. The draft is a
proposal, not evidence. `python3 fleet/executor_pin_shards.py check` loads every shard, checks it against the table and prints the folded census for the reviewer.

Two kind PRs that each add one shard merge without a textual conflict in the census tests, `executor.py`'s one-per-line kind sets, or this directory.
Two PRs that change the *same* hashed `executor.py` function still need a re-derived digest after the second merge (one more shard).
