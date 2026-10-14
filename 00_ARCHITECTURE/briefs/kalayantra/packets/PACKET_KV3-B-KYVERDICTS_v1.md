```json
{"id":"KV3-B-KYVERDICTS",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§4a.1; §6; §14 B-1","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"KU-01","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyverdicts.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyverdicts.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyverdicts.py -q -p no:cacheprovider",
"expected_result":"all tests pass; a refused publication runs no ky command",
"negative_cases":[
"boundary failure (moved HEAD, dirty tree, missing boundary evidence): no ACCEPTED published",
"substantive conflict resolution, or ancestry alone: no inheritance (KU-01)",
"crash between begin and complete: no second verdict event",
"invalidate without a prior ACCEPTED: nothing appended"]},
"packet_sha256":"34e9670463e2070dd3f60ab126a4119253021d2ac1ca6764e7c48cc1db1cf97a"}
```
# KV3-B-KYVERDICTS: `kyverdicts.py` + shared inheritance predicate

F = `00_ARCHITECTURE/briefs/kalayantra/fleet`.

**Pins.** Plan v2.7 at e709f60d7; base = the job header's reviewed B-0c head.

**Owns.** Create `F/kyverdicts.py` and `F/tests/test_kyverdicts.py`. Prohibited: FROZEN paths; any `EVENTS.jsonl`.

**Spec** (verbatim).
```excerpt plan §6
**Verdict publication (controller-owned).** After a VERIFY/ARTIFACT job exits the
controller checks: exit status, reviewed HEAD unchanged, `git status --porcelain` clean,
tracked-file hash set unchanged, boundary evidence (§7). Only then does it publish
`KY_STREAM=V KY_LANE=<vslot> ky verdict …`. A boundary failure never publishes
ACCEPTED. If a published acceptance is later invalidated, an explicit REJECTED is
appended before any queue action.

**Inheritance predicate (one implementation, used by dispatcher and tracker):** bind old
head, new head, their exact base commits and a comparison of the reviewed patch;
ancestry alone is insufficient; any substantive resolution or unproven difference
requires review of the new head.
```
KU-01 (label `kyverdicts`), verbatim:
```
Audit and guarded completion shall share the same normalized, typed evidence requirements. Data-writing code requires ACCEPTED post_deploy evidence at the observed squash merge commit. Code-only completion requires verified successful deployment containment of its mapped merge commit, without inventing a post_deploy obligation. Artifact and operation completion retain their digest-bound acceptance requirements. Apply the shared reviewed-patch inheritance predicate wherever reviewed-head validity is evaluated.

Acceptance fixtures shall prove: valid code-only completion without post_deploy passes; missing deployment containment fails; data-writing completion with missing or wrong-commit post_deploy evidence fails; invalid inheritance fails. Reconcile remaining legacy claim/verdict findings explicitly before B-2 preflight acceptance. Do not fabricate verdicts, rewrite historical events or suppress unresolved findings.
```
Of KU-01's fixtures this packet owns invalid inheritance. Append only through `ky verdict`.

**Contract A: the predicate, in `F/kyverdicts.py`**. Importing `kyverdicts` runs nothing; standard library only.
`inherits(repo, old_head, new_head) -> bool` (ruling P4; fail-closed) = `inheritance(…)["inherits"] is True`.
`inheritance(repo, old_head, new_head, *, old_base=None, new_base=None, timeout=60)` → `{"inherits": bool, "reason"}` plus the four commits; it never raises. A base not given: `git merge-base <main> <head>`, `<main>` = `origin/main`, else `main`.
True (`identical_patch`) only if all four are 40-hex commits in `repo`, each base is an ancestor of its head, `old_head` is an ancestor of `new_head`, nothing binary changed, and patch(old) = patch(new) byte for byte, patch(b, h) being `git diff --no-color --no-ext-diff --no-textconv --no-renames b h` minus its `index` and `@@` lines (white space counts). Else False: `patch_differs`, `binary_change`, `not_descendant`, `base_not_ancestor`, `unknown_commit`, `unproven_base`, `git_failed`.
INTERPRETATION: this comparison; descent required besides the equal patch; the base derivation.
One module, no copy: the tracker imports top-level `kyverdicts` from `$KY_ROOT/fleet_live` (`PYTHONPATH`: KV3-B-WRAPPERS), replacing `verdicts.merge_only_between`; an import error there: not inherited.

**Contract B: the verbs**; stdout is one JSON `{"published","result","reasons","action_id"}`.
```
snapshot --worktree W --out S
publish --job-id J --item I --phase pre_merge|post_deploy|artifact (--head H | --artifact-digest D --artifact-path P)
  --vslot V --author-id AU --reviewer-id RV --worktree W --snapshot S --job-exit N --result RES --boundary BD --as CID
  [--events E] [--external-review-path X --external-review-sha256 Y]
invalidate --item I --phase PH (--head H | --artifact-digest D) --vslot V --reason TEXT --as CID [--events E]
inherit --repo G --old-head H1 --new-head H2 [--old-base B1 --new-base B2]
```
- `snapshot` (before the job): S = `head`, `status_porcelain`, `tracked_sha256` (as KV3-B-KYBOUNDARY: sha256 over the sorted (path, work-tree file sha256) list of tracked files).
- `publish` requires: N = 0; RES a valid `ky.job_result/1` with `status` `done` and `proposed_verdict.verdict` ACCEPTED or REJECTED (its `head`, if any, = H); AU ≠ RV; W's `HEAD` = S's (= H for `pre_merge`); `git status --porcelain` empty; `tracked_sha256` unchanged; `artifact`: sha256(P) = D; BD, the JSON that `kyboundary.sh check <J>` printed with exit 0, has `result` `intact`. Then, under kyaction record `VERDICT-<J>` (actor: role `dispatcher`, `holder_kind` `controller`, `controller_id` CID) and an allow-listed environment:
  `KY_STREAM=V KY_LANE=<V> $KY_BIN verdict <I> (--head H | --artifact-digest D) --phase <phase> --result <proposed> --detail "job <J>; <summary>"` (+ the external-review pair)
- Unmet requirement: nothing is published (INTERPRETATION: not REJECTED either), reasons, exit 1. Record `done`: skip. `unfinished`: reconcile against E (default `$KY_RUN/EVENTS.jsonl`): a verdict event of this identity and result whose detail starts `job <J>;`: complete; none: publish; E unreadable: exit 3. `in_progress`: exit 3; `failed`: exit 1.
- `invalidate` appends REJECTED (detail `invalidated: <reason>`, record `INVALIDATE-<I>-<phase>-<12 hex of H or D>`) only if the latest verdict of that identity in E is ACCEPTED, else exit 1; the dispatcher runs it before any queue action.
- `inherit` prints the `inheritance` result; exit 0 inherits · 1 not (VERIFY the new head); publishes nothing.
- Exit 0 · 1 refused or negative · 3 unknown, nothing may proceed · 64 usage · 66 input missing. Environment: `KY_RUN`, `KY_BIN` (`$KY_ROOT/bin/ky`), `KY_GIT` (`/usr/bin/git`).
- `ky verdict` as `pravaha_tracker/cli.py` parses it; kyaction's `begin`, `complete`, `reconcile`; no B-0c caller.

**Depends on.** Wave 2; B-0c `kyaction.py` and the `ky` wrapper only. KV3-B-KYBOUNDARY (same wave; tests write BD): `kyboundary.sh check <job_id>` prints one JSON with `result`; exit 0 `intact`, 1 `violated`, 3 `unknown`. KV3-B-TRACKER and KV3-B-WRAPPERS assume A; the KV3-B-KYDKINDS packets call B.

**Acceptance.** `acceptance.command`, with a fake `ky` and throwaway repositories. One ACCEPTED event across two calls and across a crash between `begin` and `complete`. Each requirement failing alone: no `ky` call, exit 1, its reason (also for a file changed under `--assume-unchanged`). Predicate True: conflict-free merge of main. False, each with its reason: substantive conflict resolution, one added commit, indentation-only change, rebased identical patch, unknown commit, no main ref, git timeout, binary change; forcing the comparison equal fails a test. Nothing is True, `published` or exit 0 by default.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): commands, exit codes, pushed `head_sha`, `notes`.

**Branch and PR.** `kalayantra/kv3-b-kyverdicts`; one PR to `main`: `KĀLA-YANTRA v3 KV3-B-KYVERDICTS: kyverdicts.py + inheritance predicate`; never merged by the job.

**Do not.** Edit outside `d1_paths`; run the real `ky` or tracker; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
