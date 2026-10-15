```json
{"id":"KV3-B-KYPACKET",
"kind":"bootstrap",
"wave":"B",
"build_tier":"opus",
"routing_reason":"control-plane source (plan §9)",
"needs_chart_data":false,
"max_loops":3,
"plan_version":"2.7",
"spec_sources":[
{"path":"00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md","revision":"e709f60d7fcd4559227a25a4d5d83d6431c396b6","section_range":"§6; §7; §8; §14 B-1, B-4","sha256":"96061d91fbc6ac4cd461311944029ee7edffab0b0263c33fe08ce77c954ba90c"},
{"path":"00_ARCHITECTURE/briefs/kalayantra/fleet/templates/ku_bindings.json","revision":"2873019eacd5e3df439027bc8e53035c85755b6c","section_range":"rule; clauses","sha256":"a3fe289264f11fc0399fc3f16c5cab96531a9b3bda971ecdb66ee4b25fd2a95c"}],
"schema_receipt_id":null,
"pw_mechanism_version":null,
"release_pins":"not_applicable: bootstrap",
"d1_paths":[
"00_ARCHITECTURE/briefs/kalayantra/fleet/kypacket.py",
"00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kypacket.py"],
"acceptance":{
"command":"python3 -B -m pytest 00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_kypacket.py -q -p no:cacheprovider",
"expected_result":"all tests pass; a refused packet exits 1 and names its reason code",
"negative_cases":[
"one changed body byte: refused, packet_sha256",
"a 9,001-byte packet: refused, oversize",
"an excerpt absent from its pinned source: refused, excerpt_not_in_source",
"KU-01 altered by one character in a packet owning kyverdicts.py: refused, ku_clause_missing",
"a required_in label outside the registry: exit 66"]},
"packet_sha256":"c1cb91d3bfd7807a90c4853d78ac0ab7e47c23a02596cd533cf6727258061752"}
```
# KV3-B-KYPACKET: `kypacket.py check`

F = `00_ARCHITECTURE/briefs/kalayantra/fleet`, K = its parent, T = `platform/scripts/governance/pravaha_tracker`.

**Pins.** Plan v2.7 at e709f60d7; base = the reviewed B-0c head in the job header.

**Owns.** Create `F/kypacket.py` and `F/tests/test_kypacket.py`; nothing else. Prohibited: FROZEN paths (BS-05); any new file under `F/{cards,schemas,templates,launchd,prompts}` (the bootstrap manifest refuses one).

**Spec** (verbatim).
```excerpt plan §8
`00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md`, ≤ 4 k tokens; schema
`fleet/schemas/packet.json`; admitted by `kypacket.py check` (schema, hashes, size, test
availability, excerpt and reconciliation claims validated against pinned sources; a
failure names its reason). `packet_sha256` is computed over canonical content excluding
that field.

Front matter: `id, kind (feature | artifact | operation | schema-prerequisite |
bootstrap), wave, build_tier + routing_reason, needs_chart_data, max_loops (3),
plan_version, spec_sources[] (path, revision, section range, sha256),
schema_receipt_id, intended_schema (schema-prerequisite packets only),
original_failing_base (feature packets), test_commits[] (sha, digest, path),
expected_failing_assertion, pw_mechanism_version, release_pins (`not_applicable:
bootstrap` for Wave B packets), packet_sha256`.
```
```excerpt plan §7
- Prompt file = role card (≤ 1.5 k tokens) + packet (≤ 4 k) + job header (job id, slot,
  worktree, branch, `base_sha`, prerequisite heads, allocated migration number if any,
  loop, max loops, deadline). Oversized packets are rejected at admission, not at launch.
```
```excerpt ku_bindings.json rule
its check is to compare text_sha256 in every required_in packet
```
Carried obligation (b0c-r1 cards review): enforce ku_bindings, "component names from a fixed registry". The description of `F/schemas/packet.json` lists what it leaves to this check.

**Contract.** `python3 -B F/kypacket.py check <PACKET.md> --repo <absolute repository root>`: read-only, one packet per call.
- stdout: one JSON object `{"schema":"ky.packet_check/1","packet":<absolute path>,"id","admitted":<bool>,"packet_sha256":<computed>,"size":{"method":"calibrated_byte_bound","bytes","bound":9000,"tokens":null},"labels":[],"reasons":[{"code","detail"}]}`. stderr: `refused: <code>: <detail>`, one line per reason.
- Exit 0 admitted · 1 refused · 64 usage · 66 an own input is missing, unreadable or invalid (the repository; `schemas/packet.json`, `templates/ku_bindings.json`, `kyschema.py`, all read beside the script). Non-zero is never admission.
- Standard library only; imports `kyschema` (`load_json_text`, `validate`); git read-only through `KY_GIT` (default `/usr/bin/git`).

All nine checks run; every failure is reported:
1. Format: the name is `PACKET_<ID>_v<n>.md`; UTF-8; the first line is exactly three backticks and `json`; the front matter is the text up to the next line of exactly three backticks and is one strict JSON object. → `not_single_file`, `front_matter_json`
2. Schema: `validate` against `packet.json`; `id` equals the name's `<ID>`. → `schema`, `name_id_mismatch`
3. `packet_sha256` = sha256 of the file's bytes with the 64 hex digits of that field's value replaced by 64 zeros. The B-1 packets are stamped so: keep it. → `packet_sha256` (detail: the computed value)
4. Pins: each `spec_sources[].path` under `--repo` hashes to its `sha256`; where `revision` is a 40-hex commit, the blob `<revision>:<path>` exists with that sha256; `original_failing_base` is a commit in the repository; a non-null `schema_receipt_id` is the `schema_receipt_id` of a `00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v*.json` under `--repo`. → `spec_source_missing`, `spec_source_sha256`, `spec_source_revision`, `commit_unknown`, `schema_receipt_unresolved`
5. Size: file bytes ≤ 9000. → `oversize`. A calibrated byte bound, reported as one: 4,000 tokens ÷ 0.444 tokens per byte; the highest ratio measured with the real program (`F/cards/TOKEN_MEASUREMENT.json`) is 0.418. `tokens` stays null: nothing here measures them.
6. Test availability: feature packets, every `test_commits[]` blob `<sha>:<path>` exists with sha256 `digest`; bootstrap packets, `acceptance.command` names at least one path listed in `d1_paths`. → `test_unavailable`
7. Excerpts: an excerpt is a fenced block whose info string starts with `excerpt`; its content occurs byte for byte in one `spec_sources` file. → `excerpt_not_in_source`; a packet with no such block → `no_excerpt`
8. Reconciliation: every line starting `Reconciliation:` names in backticks at least one `spec_sources[].path`. → `reconciliation_unpinned`
9. KU bindings: in `ku_bindings.json` every clause has sha256(`text`) = `text_sha256` and every `required_in` label is a REGISTRY key, else exit 66. A packet's labels are the REGISTRY labels whose path is in its `d1_paths`. For each clause naming one of them in `required_in`, the packet's bytes contain the clause `text`. → `ku_clause_missing` (detail: the KU id)

REGISTRY (a constant in `kypacket.py`): kyverdicts → `F/kyverdicts.py`; kylock → `F/kylock.sh`; kyversion → `F/kyversion.sh`; local-db → `F/local_db.sh`; preflight-v3 → `F/preflight.sh`; finalize-v3 → `F/finalize.sh`; dispatcher-ready-receipts → `F/kyd_admit.py`; kyloop-crash-cleanup → `F/kyloop.py` (B-0c part 2; ruling P21); tracker-semantics → any path under `T/`.

INTERPRETATION (plan silent; conservative reading): the `excerpt` fence and `no_excerpt` (7; ruling P2); the `Reconciliation:` form (8), which shows a claim is bound to a pinned source, not that it is true; labels derived from `d1_paths`, the packet schema having no label field (9); the commit-blob comparison and the receipt location (4); the bootstrap rule of (6).

Two hashes, both kept (ruling P19): the front matter's follows 3; a launch input's `packet_sha256` is the plain sha256 of the file, compared by `kyboot.py`, not here. No B-0c code calls `kypacket.py`.

**Depends on.** Wave 1; none. KV3-B-KYDADMIT (admission, plan §6) and B-4 may assume the command line, exit codes and JSON above.

**Acceptance.** `acceptance.command`. Tests build their packets and a throwaway git repository under the pytest base and show: one admitted packet of each kind (bootstrap, feature, artifact); for every reason code above, a packet refused with exactly that code; every record of `TOKEN_MEASUREMENT.json` satisfies tokens ÷ bytes × 9000 ≤ 4000. `admitted: true` is printed only when all nine checks ran: a check that could not run is a refusal or exit 66, never a pass. Then run `check` on every `K/packets/PACKET_KV3-B-*_v1.md` present and record exit codes and reasons: this packet must be admitted; a reason on another packet goes to `notes`, unrepaired.

**Evidence.** `$JOB_SCRATCH/result.json` (BS-16): commands, exit codes, pushed `head_sha`, `notes`.

**Branch and PR.** `kalayantra/kv3-b-kypacket`; one PR to `main`: `KĀLA-YANTRA v3 KV3-B-KYPACKET: kypacket.py check`; never merged by the job (hold).

**Do not.** Edit outside `d1_paths`; call a model or the network; rebase or force-push; touch credentials, production, the plan, cards, schemas, templates or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
