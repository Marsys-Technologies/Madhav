```json
{"id":"KV3-B-KYREGEN",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source under fleet/** (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§4a.1, §6 REGEN row and inheritance predicate, §7, §8, §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyregen.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyregen.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyregen.py -q -p no:cacheprovider",
"expected_result":"exit 0, nothing skipped; a confined conflict is merged, regenerated, tested, pushed and registered at the new 40-hex head",
"negative_cases":[
"a conflict outside the declared generated outputs changes nothing (exit 3)",
"a generator that differs from its pin, or writes an undeclared path, changes nothing (exit 4)",
"a failing test pushes nothing (exit 5)",
"a rejected push or failed registration is never reported as done (exit 6)"]},
"packet_sha256":"84bf40dc22d11470095934b11ffe8e140b13e582ff95e1e8161a621b05afed77"}
```
# KV3-B-KYREGEN: `kyregen.sh`, the REGEN job script

**Pins.** Plan v2.7 @ `e709f60d7`; base = the reviewed B-0c head in the job header.

**Owns.** The two `d1_paths`: `kyregen.sh` (git mode 100755, `#!/bin/bash`, bash 3.2; logic may be one embedded stdlib `python3 -I -B` program) and its tests. Prohibited: FROZEN paths, every other file.

**Spec (verbatim).**
```excerpt plan §6 REGEN row: trigger, model, identity, post-action
PR DIRTY/CONFLICTING confined to declared generated outputs | script, pinned generator | item lock | merge base; regenerate only declared outputs; run applicable tests; record hashes; push; **register `ky review … @ <new head>`**; inheritance only by the patch predicate (below), else VERIFY
```
```excerpt plan §6
**Inheritance predicate (one implementation, used by dispatcher and tracker):** bind old
head, new head, their exact base commits and a comparison of the reviewed patch;
ancestry alone is insufficient; any substantive resolution or unproven difference
requires review of the new head. Applied to every inherited Wave 0 head. After every
head change the owning stream registers `ky review <ID> --detail "PR #<n> @ <new-head>"`.
```
```excerpt plan §6 MERGE
workers never push under an outstanding queue authorisation
```
```excerpt plan §8.9
no
   rebase/force-push, merge `origin/main` only when DIRTY outside generated files (else
   REGEN)
```
```excerpt plan §4a.1
before any side effect
   (push, PR, merge, tracker event, launch, notification) the actor persists
   `run/actions/<action_id>.json` {inputs, target identity, intended transition}; after it,
   the observed result
```

**Contract.** `kyregen.sh <job_id>` — INTERPRETATION: the §7 convention of `kyjob.sh <job_id>` (all values from `$KY_RUN/jobs/<job_id>/state.json`, every path absolute). Env: `KY_ROOT`, `KY_RUN`, `KY_FLEET`; `KY_RUN_ID`, `KY_ROLE`, `KY_CONTROLLER_ID` (action records); git = `${KY_GIT:-/usr/bin/git}`; tracker CLI = `${KY_BIN:-$KY_ROOT/bin/ky}`.
`state.json` keys read, as KV3-B-KYDJOBS pins the job state: `kind` (`"REGEN"`), `item`, `stream`, `slot`, `worktree`, `branch`, `pr`, `registered_head`, `base_sha` (the exact base commit to merge, already fetched), `queue_authorised`, `regen {outputs[] (repository-relative files), generator {argv[], path, sha256}, tests[] (argv lists)}`.
Steps, in order; any refusal before step 6 leaves the worktree clean at `registered_head`:
1. Preconditions (else 73): `queue_authorised` is false; worktree HEAD == `registered_head`; `git status --porcelain` is empty; `base_sha` is not yet contained in HEAD; `$KY_RUN/locks/item.<item>/owner.json` names a live owner that is this process or an ancestor (liveness as kyaction.py `process_matches`; unknown refuses) — INTERPRETATION: the dispatcher holds the plan's item lock, kyregen takes none; sha256 of `generator.path` == `generator.sha256`, else 4 (pinned generator).
2. `git merge --no-commit --no-ff <base_sha>`. Every unmerged path must be a declared output; otherwise `git merge --abort`, exit 3.
3. Run `generator.argv` in the worktree, then `git add` the declared outputs. No conflict may remain, and beyond what the merge itself staged only declared outputs may have changed (no other modified or untracked file); otherwise abort, exit 4.
4. Run each `tests[]` argv in the worktree; a non-zero exit: abort, exit 5.
5. Commit the merge (message `REGEN <item>: merge <base_sha>, regenerate declared outputs`); new head = HEAD.
6. Push, never forced, inside an action record `JOB-$KY_RUN_ID-push`, kind `git_push`, inputs `{"remote": "origin", "ref": "refs/heads/<branch>", "commit": "<new head>"}`, through the B-0c job verbs: JSON on stdin of `python3 "$KY_FLEET/kyaction.py" begin` (exit 3 = the record exists: do not push), then `git push origin HEAD:refs/heads/<branch>`, then `complete` only when `git ls-remote origin refs/heads/<branch>` shows the new head, else `fail`.
7. Register inside an action record `JOB-$KY_RUN_ID-review`, kind `tracker_event`: `KY_STREAM=<stream> KY_LANE=<slot> ky review <item> --detail "PR #<pr> @ <new head, 40 hex>"`; exit 0: `complete`; else `fail`.
8. Once step 5 is done (also before an exit 6) write `$KY_RUN/jobs/<job_id>/regen.json` (temp + rename): `{"schema": "ky.regen/1", "job_id", "item", "pr", "old_head", "new_head", "old_base" (merge-base of the old head and `base_sha`), "new_base" (`base_sha`), "conflicted_paths", "outputs": [{"path", "sha256_before", "sha256_after"}], "generator": {"argv", "sha256"}, "tests": [{"argv", "exit"}], "pushed", "review_registered", "inheritance": null}`. `inheritance` is always null: the patch predicate (`kyverdicts.inherits`, ruling P4) is evaluated by the dispatcher and the tracker, never here; undecided means VERIFY.
Exit: 0 pushed and registered · 3 conflict outside the declared outputs · 4 generator pin, or generator wrote elsewhere · 5 tests failed · 6 push or registration failed or unknown (its action record stays for reconciliation; nothing is retried) · 73 precondition · 64 usage or invalid state.
A re-run finds regen.json for the same `registered_head` first: after 0 it does nothing and exits 0; after 6 it exits 6 until the records are settled. No existing component calls kyregen.

**Depends on.** Wave 2; needs only B-0c kyaction.py (job verbs; exit codes in its docstring) and the wave-1 `ky` wrapper (`ky review` as above, the plan's form). Assumed of the dispatcher (KV3-B-KYDJOBS, KV3-B-KYDKINDS-LAND, wave 3; tests write the state themselves): it writes state.json with the keys above, holds the item lock, sets the three `KY_*` ids and reconciles `JOB-<run id>-*` records as kyloop.py does. KV3-B-KYVERDICTS' `kyverdicts.inherits` is theirs to call, never called here.

**Acceptance.** The front-matter command; tests first; temp `KY_*` directories; a bare fixture `origin` and a worktree made with `git init`; a fixture generator; a recording `ky` double (`KY_BIN`) and a recording git wrapper (`KY_GIT`); the real kyaction.py.
1. Conflict confined to declared outputs: a two-parent merge commit, outputs regenerated, hashes recorded, remote head == new head, `ky review` argv exactly as above, both records DONE, `inheritance` null, exit 0.
2. Conflict in an undeclared path: 3.
3. Generator hash mismatch: 4, generator never run; generator writing an undeclared path: 4.
4. Failing test: 5, nothing pushed.
5. Dirty worktree, HEAD unequal to the registered head, `queue_authorised` true, lock absent, foreign or unknown: 73.
6. Push rejected (remote moved): 6, record FAILED, no `ky review`; `ky` non-zero: 6, `pushed` true, `review_registered` false.
7. After 2 to 5 the worktree is clean at the registered head; a re-run after success does nothing; no git argv ever holds `--force`, `-f` or `rebase`.
`pushed` and `review_registered` are true only from the observed remote head and the `ky` exit; unknown is null with exit 6.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): each command, exit code, summary; branch; pushed 40-hex `head_sha`; `pr_number`.

**Branch and PR.** `kalayantra/kv3-b-kyregen`; one PR to main, "KĀLA-YANTRA v3 KV3-B-KYREGEN: kyregen.sh"; never merged, queued or approved by the job (hold).

**Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the real `ky`, any real PR branch, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
