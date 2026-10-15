```json
{"id":"KV3-B-KYVERSION",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source under fleet/** (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"pairing rule, §10, §11, §14 B-2/B-5","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"clauses.KU-03","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kyversion.sh",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyversion.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kyversion.py -q -p no:cacheprovider",
"expected_result":"exit 0, nothing skipped; each mode passes on its valid fixture, each check refuses alone",
"negative_cases":[
"a missing or unequal canonical / compatibility copy refuses (KU-03)",
"a bootstrap-only installation never passes the normal mode",
"an expected digest unequal to the manifest or the chain's terminal link refuses"]},
"packet_sha256":"be8663b41faead59f2c32b6e558218894f48f5222a8e56a7068b36fd77594ab6"}
```
# KV3-B-KYVERSION: `kyversion.sh`

**Pins.** Plan v2.7 @ `e709f60d7`; base = the job header's reviewed B-0c head.

**Owns.** The two `d1_paths`: `kyversion.sh` (git mode 100755, `#!/bin/bash`, bash 3.2; logic may be one embedded stdlib `python3 -I -B` program) and its tests. Prohibited: FROZEN paths, every other file.

**Spec (verbatim).**
```excerpt plan pairing
the launcher passes that approved digest to every conductor job as an argument taken from
  the activation record, never from the installed manifest it is verifying
```
```excerpt plan pairing
a bootstrap activation authorises bootstrap sources only,
  never campaign admission
```
```excerpt plan §11
manifest digest (from the activation record) → `kyversion.sh
--expected-manifest-digest` → lock
```
```excerpt plan §14 B-2
installed hashes match the reviewed component heads bound by the manifest; `preflight.sh launch` and `kyversion.sh --bootstrap` pass; only the accepted bootstrap receipt permits isolated rehearsal activation — receipt-file existence alone grants no authority
```
```excerpt plan §14 B-5
the final `run/VERSIONS.json`; a **final installation receipt** binding that manifest, the loaded tracker revision, B-3 evidence, B-4 evidence and the validated backfill
```
```excerpt plan §14 B-5
normal `kyversion.sh` green against the final manifest and receipt
```
KU-03 (label `kyversion`):
<!--KU-03-->
For WORKTREE_DISPOSITIONS, ACCEPTANCE_ROOTS and CLOSURE, use the plan’s named paths as canonical. Materialize the paired prompt’s differently named outputs as compatibility copies containing exactly the same reviewed bytes; retain content version 2.2. Record both absolute paths, the canonical role and their common SHA-256 in VERSIONS.bootstrap.json. Consumers use the canonical path; version checks verify both copies. Missing or unequal copies refuse bootstrap acceptance. Neither copy may be edited independently.
<!--/KU-03-->
Carried (b0c-r1 loops review): the final receipt and kyversion independently verify B-3/B-4 evidence.

**Contract.** Usage `kyversion.sh [--bootstrap | --expected-manifest-digest <64 hex>]`; anything else 64. Exit 0 only when every check of the mode ran and passed; else 1, with one stderr line `kyversion: REFUSED <code>: <detail>` per failed check; a check that cannot run refuses. stdout on 0: `kyversion: OK mode=<bootstrap|final> manifest_sha256=<hex> authorises=<bootstrap-only|final-bundle>`. Writes nothing; no network.
Env (as the plists export): `KY_ROOT`, `KY_RUN` (default `$KY_ROOT/run`), `KY_FLEET` (default: the script's directory), `KY_SOURCE_REPO` (the git checkout the manifest is checked in; default as kyctl.sh: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`; no git work tree: refuse).
Existing call forms: kyloop.py `run_helper`: `subprocess.run(["/bin/bash", str(script), *args], capture_output=True, text=True, timeout=300).returncode`, args `["--bootstrap"]` (planner), `["--expected-manifest-digest", digest]` (conductor), `[]` (`derive_completion`; veto loop on a final receipt); only 0 passes. kyctl.sh: `/bin/bash "$KY_FLEET/kyversion.sh" "$varg" >/dev/null 2>&1` (`--bootstrap`, or no argument). PLANNER_LOOP: `bash "$KY_FLEET/kyversion.sh" --bootstrap`.
Files read. `$KY_RUN/INSTALL_RECEIPT.json` (writers: KV3-B-INSTALL, B-5): `mode`; `manifest.manifest_sha256`; `components[] {path, installed_path, sha256}`; final only: `tracker_revision`, `rehearsal {tested_components[] {path, sha256}, results {path, sha256}}`, `coverage {path, sha256, verdict}`, `packets[] {path, sha256}`, `backfill {path, sha256, validated}`. A manifest is the object kymanifest.py `observe` builds (`mode`, `manifest_sha256`, `entrypoints`, `components[] {path, sha256}`, `generated_pairs[]`); the final one, `$KY_RUN/VERSIONS.json`, says `mode: "final"`.
`--bootstrap`, all of:
- B1 receipt `mode == "bootstrap"`.
- B2 reuse, never re-implement: `python3 -I -B "$KY_FLEET/kymanifest.py" check "$KY_RUN/VERSIONS.bootstrap.json" --repo "$KY_SOURCE_REPO" --run "$KY_RUN"` (kyboot.py `run_manifest_check` form: cwd `/`, no `GIT_*` / `PYTHON*` variable) exits 0 and prints JSON with `ok: true` and the manifest file's own `manifest_sha256`.
- B3 the receipt binds that digest.
- B4 installed bytes: `components[]` is non-empty; each entry is a manifest component (same `path`, `sha256`) whose `installed_path` file has that sha256.
- B5 KU-03: each `generated_pairs[]` entry (WORKTREE_DISPOSITIONS, ACCEPTANCE_ROOTS, CLOSURE all present): `canonical_abs` and `compatibility_abs` are both regular files with the entry's `sha256`.
- B6 any `$KY_RUN/ACTIVATION_RECORD*.json` forms a valid chain by the rules of kyloop.py `activation_chain` (broken or forked refuses).
It reads no VERSIONS.json and prints `bootstrap-only`: it can never authorise campaign admission.
Normal mode (no argument), all of: F1 receipt `mode == "final"`; F2 VERSIONS.json has `mode == "final"`, the five-role `entrypoints`, and `manifest_sha256` == sha256 of its canonical JSON without that key (kymanifest.py `canonical`); F3 to F6 = B3 to B6 on it; F7 the receipt's evidence: `rehearsal.tested_components` equals the manifest's `components` (path → sha256); `rehearsal.results`, `coverage`, `backfill` and each `packets[]` entry (non-empty) name an existing file with the recorded sha256; `coverage.verdict == "ACCEPTED"`; `backfill.validated == true`; `tracker_revision` present (recorded, not re-observed: stdout adds `tracker_revision=recorded`).
`--expected-manifest-digest D`: the normal checks, plus `manifest_sha256 == D`, plus a chain exists whose terminal link's manifest digest is D.
INTERPRETATION: the other two modes check only the chain's structure; `--expected-manifest-digest` alone binds the manifest to the chain.

**Depends on.** Wave 2; calls only kymanifest.py (B-0c). Ruling P6: KV3-B-INSTALL (wave 4) writes the bootstrap receipt with the names read above; the final receipt and `VERSIONS.json` are B-5 work; a missing name refuses, never a guess.

**Acceptance.** `acceptance.command`; tests first; each builds a temp `KY_RUN`, `KY_FLEET` and git repository; kymanifest.py is a recording double (argv asserted exactly). One passing run per mode, then one refusing test per check B1 to B6 and F1 to F7, with its code: KU-03 missing copy, unequal copy; changed final manifest; stale tested hashes; missing rehearsal, coverage, packets, backfill; an installed file with other bytes; D unequal to the manifest; D unequal to the terminal link; D without a chain; broken, forked and gapped chains; the double exiting 0 without `ok` or with another digest; a final receipt under `--bootstrap`; a bootstrap receipt in normal mode; both options at once (64); a source repository that is no work tree. Every OK comes from checks that ran in that call; unknown refuses.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): each command, exit code, summary; branch; pushed 40-hex `head_sha`; `pr_number`.

**Branch and PR.** `kalayantra/kv3-b-kyversion`; one PR to main, "KĀLA-YANTRA v3 KV3-B-KYVERSION: kyversion.sh"; never merged, queued or approved by the job.

**Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
