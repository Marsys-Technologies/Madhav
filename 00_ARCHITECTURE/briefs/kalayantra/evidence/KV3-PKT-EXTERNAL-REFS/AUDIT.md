# KV3-PKT-EXTERNAL-REFS — repository input audit

Date: 2026-10-14. Scope: all 51 files under `00_ARCHITECTURE/briefs/kalayantra/packets/`.
Changed 25 packets (references, citation offsets, and digest stamps only); archived 25 external inputs.
All 44 previously admitted packets remain admitted. Seven pre-existing refusals remain; every packet is now ≤9,000 bytes.

Authority read: `CLAUDE.md` §I/§N; `KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md`; `KALAYANTRA_RELAUNCH_PLAN_v2_7.md` §5/§7/§8 (repository-relative campaign paths below share `00_ARCHITECTURE/briefs/kalayantra/`); `fleet/cards/KARAKA.md` and `fleet/cards/PARIKSAKA.md`.

## Provenance and privacy

Each archive has exactly two added provenance lines: original source path, then original SHA-256 and date. Packet citations into these files were shifted by +2 to remain ordinary physical file-line citations. Redaction preserves line count. Original and archived hashes are distinguished below. Code and JSON copies are read-only evidence, never runtime imports; JSON provenance uses two `//` lines, so a consumer needing the original JSON payload must exclude those two lines.

Private-data screening ran before copying: account identifiers, emails, credential-shaped tokens/keys/assignments, and owner personal instruction text. Product rulings and implementation contracts remain intact. No credentials or account IDs were found. Email-shaped strings (including synthetic fixtures) and two owner personal instruction spans were redacted; the owner name in one authority introduction was also removed.

## Interpretations and cockpit follow-up

- (I) INTERPRETATION: live runtime contracts, output destinations, forbidden paths, tool defaults and fixture stand-ins are not static job READ inputs. Retaining these literals preserves the contract; it does not authorize a worker to access the real directories or programs.
- (I) INTERPRETATION: run-directory input references retained below are exclusively requirements for controller-supplied evidence (release/seed receipts, inventories, verdicts, event/decision snapshots, test manifests, operation receipts, audit/handover records, planner state). The controller must supply digest-bound bytes or a permitted evidence view before launch; this audit does not claim that such a view is already supplied. If absent/inaccessible/changed, the job blocks. No worker permission expansion or invented job-folder interface is introduced. Output-only run paths remain cockpit promotion targets.
- (I) INTERPRETATION: archive copies share this job item directory; original basenames are preserved and `engines/` / `ops/` separate the source families.
- (I) INTERPRETATION: missing retired worktree inputs use existing repository counterparts for reading only. No original hash is invented and no historical equality or inherited acceptance is claimed. K7-4: `platform/python-sidecar/services/ka_sangam/jury/reader_contract.json` and `platform/src/lib/retrieval/registry/layers/L3_kala/view_common.ts`; KA-4b: the same layer’s `view_elect.ts`, `view_common.ts`, `views_registry.integration.test.ts`, plus `platform/scripts/generate_muhurta_undertakings.ts`; KV3-SCHEMA-2: `platform/python-sidecar/services/ka_sangam/jury/candidate.py`. Cockpit must recheck the existing accepted-head/base gates before treating these as historical evidence.
- (I) INTERPRETATION: KV3-B-BASELINE SRC denotes the payload after the archive’s two provenance lines. Its exact original byte hash remains `28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176`; the existing `scripts/token_economy/token_baseline.py` matches that original too. The unchanged-copy/hash contract applies to payload bytes, not the provenance wrapper.
- (I) INTERPRETATION: an installed `fleet_live/precheck.sh` reference is a program input, not supplied evidence; J-0d, K7-4, KA-4b and KA-4c now invoke the existing repository `fleet/precheck.sh`.
- (I) INTERPRETATION: other `$KY_FLEET/precheck.sh` call forms retain the existing launcher variable; the controller must bind it to the repository fleet for a restricted job. Bootstrap `$KY_FLEET`, `$KY_RUN`, `$KY_ROOT`, `$KY_SOURCE_REPO` and `$KY_SCRATCH` references describe runtime implementations or fixture-supplied roots, not permission to read installed host state during a builder/verifier test.
- Cockpit: supply the retained runtime evidence at launch, recheck substituted current repository reads, and repair the seven pre-existing packet refusals separately. No remaining static external-file read or unresolved static input path was found. No Git writes, background processes, database calls, network calls or controller mutations were run.

## Copied files

### `SURROGATE_ANSWERS_01-02.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWERS_01-02.md`.
- Original SHA-256: `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Archived SHA-256: `bc16b15782460471a3f40405c65266b3a72000baf51fdd8e194cea61a450c9eb`.
- Payload SHA-256: `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Redactions: none.

### `SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md`.
- Original SHA-256: `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Archived SHA-256: `bbfe347943d8af7e6f088d47ca7a0c9000a22e8467b0c9dcba6fc3e08121fd7f`.
- Payload SHA-256: `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Redactions: none.

### `SURROGATE_ANSWER_06_AUDIT_AND_SCHEMA2.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_06_AUDIT_AND_SCHEMA2.md`.
- Original SHA-256: `9bbbe55a3dd79fecded46b0f23923b4d8c358af29dcaa198b7b226e90408facb`.
- Archived SHA-256: `e86320cfe226756b103431aa1bd337dcbf350e65ccd34321737d3bbebd5acd6f`.
- Payload SHA-256: `9bbbe55a3dd79fecded46b0f23923b4d8c358af29dcaa198b7b226e90408facb`.
- Redactions: none.

### `SURROGATE_ANSWER_11_OWNER_OPEN_ITEMS.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_11_OWNER_OPEN_ITEMS.md`.
- Original SHA-256: `8d7bf3dd0a8ae86eae83d3d9cf39260254fa639dd9d58e15605124fdfa4c4779`.
- Archived SHA-256: `156299bd96fa4cfb16a7949b5e550373baeebe7dd0bb092fb6433a5a054f5729`.
- Payload SHA-256: `f028583ae191d23c8c2b4c16f017b6f16e9c1bb0f33e68676122b7d0ce4f518b`.
- Redactions: original line 3: owner_personal_instruction.

### `B4_RULINGS.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/lane2/B4_RULINGS.md`.
- Original SHA-256: `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
- Archived SHA-256: `a61b44dc65a0449237f87eb84573dce1da491666ceda81ff228b97eb626a6dfd`.
- Payload SHA-256: `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
- Redactions: none.

### `OWNER_RULINGS_DIGEST_A.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md`.
- Original SHA-256: `f35373f77548555f00a20b294f42d094104ad51197dfdb786887b626a887909a`.
- Archived SHA-256: `6dd8b66b8d123f6f3e1866f4a5a710a7f9fd9943dd61ff1909b8821903a7c29e`.
- Payload SHA-256: `e1263cac03b2ee9893ad3ddf48cdf76106f2740c7a0370f097a1071d70d0e45f`.
- Redactions: original line 3: owner_personal_instruction_and_name.

### `OWNER_RULINGS_K7-4_TABLE.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/lane2/owner/OWNER_RULINGS_K7-4_TABLE.md`.
- Original SHA-256: `23b5987d4b2cba7a1869a55118bffc16169e7cabb5f78ffd5cd02517a4e67a0c`.
- Archived SHA-256: `ace721e4171da81f6a738c08b7593cd843508f7f808682de961e44a6575c9d7f`.
- Payload SHA-256: `23b5987d4b2cba7a1869a55118bffc16169e7cabb5f78ffd5cd02517a4e67a0c`.
- Redactions: none.

### `DEFINE_KV3-SCHEMA-1.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T220409Z-b4-define-kv3-schema-1/DEFINE_KV3-SCHEMA-1.md`.
- Original SHA-256: `241e9ba26b646d428a4314de155436e1610e18fe119a966d75dab976e4a3d203`.
- Archived SHA-256: `88d84dbf48a858c7d76cfc4d73fd61e5c9622772f50235ac6c21c892e1ced1bf`.
- Payload SHA-256: `241e9ba26b646d428a4314de155436e1610e18fe119a966d75dab976e4a3d203`.
- Redactions: none.

### `DEFINE_K8-R26.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T211639Z-b4-define-k8-r26/DEFINE_K8-R26.md`.
- Original SHA-256: `2fc2f0e6758380d41d478a21cd8a3f16c51e284d00777d363db7179f85a30701`.
- Archived SHA-256: `7c39f32c102926b1a8bfb6ec3aea1b4d98614b24238dd2196a62dc281f6b2a1b`.
- Payload SHA-256: `2fc2f0e6758380d41d478a21cd8a3f16c51e284d00777d363db7179f85a30701`.
- Redactions: none.

### `DEFINE_KA-3a.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/jobs/J-20261012T184241Z-b4-define-ka-3a/DEFINE_KA-3a.md`.
- Original SHA-256: `be61c28b34a43f5d8c01ce9f01f1077fb88a03136ed7ae878b841a342df46b7f`.
- Archived SHA-256: `2d2671f6f831f0cd036facf895f46723f3a8b065814c02e1cf22d75c3748c1fe`.
- Payload SHA-256: `be61c28b34a43f5d8c01ce9f01f1077fb88a03136ed7ae878b841a342df46b7f`.
- Redactions: none.

### `K7-3_PINS.md`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261013T115956Z-k73-pins/K7-3_PINS.md`.
- Original SHA-256: `26b72c85091013458c3d82edfd3cff1a24f239399eadf5110a174a51d234dbfd`.
- Archived SHA-256: `4836c200b28606b616564f4dd8933106af4e5d1205429533c7842733ca5d5bc8`.
- Payload SHA-256: `26b72c85091013458c3d82edfd3cff1a24f239399eadf5110a174a51d234dbfd`.
- Redactions: none.

### `engines/kyengine.py`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/launchers/cockpit/kyengine.py`.
- Original SHA-256: `4ba634ba17d0f903ae496aaf1396167ec84482ab963aff525c12e0bd4c3c3a8d`.
- Archived SHA-256: `fda8deee14b20d8aa054a3671d27d59ab59bb60fd5a834d96ede04b7bdc53c64`.
- Payload SHA-256: `4ba634ba17d0f903ae496aaf1396167ec84482ab963aff525c12e0bd4c3c3a8d`.
- Redactions: none.

### `engines/kyfinish.py`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/launchers/cockpit/kyfinish.py`.
- Original SHA-256: `a744b32b784faec24dd8968faf4f43f21692b54413a9fe90de767bb2ed9344fe`.
- Archived SHA-256: `a922a3c742a2455a1065dfdda8e3defcacccfb3f48e261d03d18fa99f697d808`.
- Payload SHA-256: `d41d41a4c531b87b350c972bd2d1151b830987d8622405736531667e6a7f7229`.
- Redactions: original line 44: email.

### `engines/result.json`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/reviews/b0c-engines/jobs/review-engines-r4/result.json`.
- Original SHA-256: `a812696b55095bf960f55ad155a7608ef38d0cf4d40f0abbb9050a9c37371e70`.
- Archived SHA-256: `a4d92b95db9a46234f88a49a01653a96c355cbe0e44392d8232ee5f36e847b0c`.
- Payload SHA-256: `a812696b55095bf960f55ad155a7608ef38d0cf4d40f0abbb9050a9c37371e70`.
- Redactions: none.

### `engines/kyqualify.py`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b0c-engines/00_ARCHITECTURE/briefs/kalayantra/fleet/kyqualify.py`.
- Original SHA-256: `57d136fea6fd8166d9fcca057fc913d688d94dc9d994c37d20a60aa917644706`.
- Archived SHA-256: `92db1006b4d668ef8e81fbc6515c6b6f06ed33593601902179b9727e6ab28389`.
- Payload SHA-256: `57d136fea6fd8166d9fcca057fc913d688d94dc9d994c37d20a60aa917644706`.
- Redactions: none.

### `engines/kyboot.py`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b0c-engines/00_ARCHITECTURE/briefs/kalayantra/fleet/kyboot.py`.
- Original SHA-256: `e81ea4a79b9c7fe0c808604395b0407e1b242836c9c2abb4744e935a58144df8`.
- Archived SHA-256: `2ceefc3c749efac0391e934610a9878a33bf72a9c9a517e56a4fcbe0bda06644`.
- Payload SHA-256: `e81ea4a79b9c7fe0c808604395b0407e1b242836c9c2abb4744e935a58144df8`.
- Redactions: none.

### `engines/job_result_launcher_commit.json`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b0c-engines/00_ARCHITECTURE/briefs/kalayantra/fleet/schemas/job_result_launcher_commit.json`.
- Original SHA-256: `fd071415769b492b5a103ec51aea6d36955541415a2b6dae4c971ed8c1a01356`.
- Archived SHA-256: `8f5c24db274188a824654c09c41e2bc4951368407d42603e838a72451c92d13a`.
- Payload SHA-256: `fd071415769b492b5a103ec51aea6d36955541415a2b6dae4c971ed8c1a01356`.
- Redactions: none.

### `ops/ops/common.py`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/ops/common.py`.
- Original SHA-256: `df4602cca69ca8603fda47df308e8d68e5df934c2d27fc3695dd24ac9e4edb96`.
- Archived SHA-256: `0964546ce8cf6f9e9b6203460ca21a119b0686d9e38ffad73aa3dee1639cfef1`.
- Payload SHA-256: `df4602cca69ca8603fda47df308e8d68e5df934c2d27fc3695dd24ac9e4edb96`.
- Redactions: none.

### `ops/ops/README.md`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/ops/README.md`.
- Original SHA-256: `b7c9a6c91ad6817bb5dde602fb652e0214aefe47e6f589cc42d8e2bffb22ac95`.
- Archived SHA-256: `1c53b969405a12010bf6d4c9a6a4aff6276ebff08db674145c9f38442e1efc61`.
- Payload SHA-256: `b7c9a6c91ad6817bb5dde602fb652e0214aefe47e6f589cc42d8e2bffb22ac95`.
- Redactions: none.

### `ops/operation_adapters.py`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/operation_adapters.py`.
- Original SHA-256: `7c60341f04be7353bd1b470f83bcc4527e5f9738970bb4cdf8a0d87447fee8a4`.
- Archived SHA-256: `82dc9f6a2c623d991d1628315e6567cb48a37199e374c48e30976b2a17f2b553`.
- Payload SHA-256: `7c60341f04be7353bd1b470f83bcc4527e5f9738970bb4cdf8a0d87447fee8a4`.
- Redactions: none.

### `ops/executor_ops.json`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json`.
- Original SHA-256: `65d3f27eacdc106378500cf6c3b79ef756f7f3022ce86b904e1200a77802c16f`.
- Archived SHA-256: `a7937478f7fde35d529300d9b2f78e641889cf3d0eab94d80d999787917fdf0e`.
- Payload SHA-256: `65d3f27eacdc106378500cf6c3b79ef756f7f3022ce86b904e1200a77802c16f`.
- Redactions: none.

### `ops/tests/test_ops_backup.py`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_ops_backup.py`.
- Original SHA-256: `c719265c416f17a12007ae912c5cec6e0264fdb5ea6f633ffb121de09be5be3a`.
- Archived SHA-256: `536c409ed4c517f9a79cc33f63d9feeaa51bc4632a651ca808d85b1b8f8f56a9`.
- Payload SHA-256: `e7e1c6cac13eaaa180efd0edf41e5bdadf1292de3bd6c31f230ce74b1613285f`.
- Redactions: original line 168: email.

### `ops/tests/test_operation_adapters.py`

- Source: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts/00_ARCHITECTURE/briefs/kalayantra/fleet/tests/test_operation_adapters.py`.
- Original SHA-256: `5eaa749f8c4c71e528e23921d4efe4bc86b9ad1110e7e1e5240a04a81ba12cc7`.
- Archived SHA-256: `75b86e11e7c24433c82efb6580e42c4dfd877ae9617092fdc8cb99a8979f6dfa`.
- Payload SHA-256: `8790d828dcd1b0191f75bacb8a3c21b286a3c2976d81a4a5b1dc850da71898ce`.
- Redactions: original line 706: email.

### `SMALL_TEST_SITTING_CHECKLIST_v1_0.md`

- Source: `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/runbooks/SMALL_TEST_SITTING_CHECKLIST_v1_0.md`.
- Original SHA-256: `37d6cc9bafdf815a96a0311fdec448094705a055f95cbd691492c4b8fb72290b`.
- Archived SHA-256: `d71ddc90005ff3c3bd4605a4448f07fbee58375b080ee0f57195f556e80cebde`.
- Payload SHA-256: `37d6cc9bafdf815a96a0311fdec448094705a055f95cbd691492c4b8fb72290b`.
- Redactions: none.

### `token_baseline.py`

- Source: `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/token_baseline.py`.
- Original SHA-256: `28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176`.
- Archived SHA-256: `282ec2e27acc46af871954e2b5aa9dd1236bf806575dc863079d1099c4b96289`.
- Payload SHA-256: `28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176`.
- Redactions: none.

## Per-packet results

Unchanged packet digests are included to make the scan exhaustive.

### `PACKET_J-0c_v1.md`

- References/stamp changed: true; bytes: 8629.
- Packet digest after: `8bbe83607efc872dbb46d0f7d1be26d4657aed450e2dc75d2bbe5d78ed41aeb4`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 8: Read /Users/Dev/kalayantra/run/J0_PR_INVENTORY.json and J0_STATE_INVENTORY.json in full; digest actual bytes and record observations. Current J0_DISPOSITION.json v1.1 is the repair base, not an accepted output. Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:80: supply 24 decisions, 4 sealed, 7 holds and fix phase order. Compare the inputs rather than blindly reusing these totals.
  - Packet line 10: /Users/Dev/kalayantra/run/J0_DISPOSITION.json; optional J0_DISPOSITION.md as its rendered view only. Governed write authority is the item's model brief, not d1_paths. An assigned sandbox that cannot write this run path must return a scratch proposal for cockpit promotion, never bypass its boundary. No implementation, new checker, model edit, other artifact writer, inherited landing, state/permission change or program under run/.
  - Packet line 29: python3 -I -B 00_ARCHITECTURE/briefs/kalayantra/fleet/accept/j0_disposition.py check /Users/Dev/kalayantra/run/J0_DISPOSITION.json --inventory-prs /Users/Dev/kalayantra/run/J0_PR_INVENTORY.json --inventory-state /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json --repo "$PWD"
  - Packet line 31: Negative fixtures: missing/extra/duplicate rows; wrong inventory digest; count omitted/miscounted; malformed heads/refs; dependency replacement; forbidden phase/phase-order violation; PR3141 outside8; reserved owner changed or unresolved class dropped. Reuse installed suite, mutate scratch only; every named negative must be rejected. KY_ITEM=J-0c bash "$KY_FLEET/precheck.sh" --item. Independently compare all proposal rows/source evidence and complete old/new diff. A semantic CLI pass alone does not prove upstream acceptance or approve a landing.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 8: Read controller-supplied /Users/Dev/kalayantra/run/J0_PR_INVENTORY.json and J0_STATE_INVENTORY.json in full; digest actual bytes and record observations. Current J0_DISPOSITION.json v1.1 is the repair base, not an accepted output. Source: 00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:82: supply 24 decisions, 4 sealed, 7 holds and fix phase order. Compare the inputs rather than blindly reusing these totals. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 10: /Users/Dev/kalayantra/run/J0_DISPOSITION.json; optional J0_DISPOSITION.md as its rendered view only. Governed write authority is the item's model brief, not d1_paths. An assigned sandbox that cannot write this run path must return a scratch proposal for cockpit promotion, never bypass its boundary. No implementation, new checker, model edit, other artifact writer, inherited landing, state/permission change or program under run/. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 29: python3 -I -B 00_ARCHITECTURE/briefs/kalayantra/fleet/accept/j0_disposition.py check /Users/Dev/kalayantra/run/J0_DISPOSITION.json --inventory-prs /Users/Dev/kalayantra/run/J0_PR_INVENTORY.json --inventory-state /Users/Dev/kalayantra/run/J0_STATE_INVENTORY.json --repo "$PWD" — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 31: Negative fixtures: missing/extra/duplicate rows; wrong inventory digest; count omitted/miscounted; malformed heads/refs; dependency replacement; forbidden phase/phase-order violation; PR3141 outside8; reserved owner changed or unresolved class dropped. Reuse installed suite, mutate scratch only; every named negative must be rejected. KY_ITEM=J-0c bash "$KY_FLEET/precheck.sh" --item. Independently compare all proposal rows/source evidence and complete old/new diff. A semantic CLI pass alone does not prove upstream acceptance or approve a landing. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_J-0d_v1.md`

- References/stamp changed: true; bytes: 8994.
- Packet digest after: `0474e382d4a6bb6a2b85adfb06721655e59677379719d066ccb679bbfb6b0c52`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: M=00_ARCHITECTURE/control/kalayantra/plan_model.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3. 1-based lines.
  - Packet line 8: Release SUVARNA-L0L2-CLOSE-REV30-20261013. Historical schema v2.2; no DB/window/proof. Wave0 J-0c→J-0d→J-0→J-0m (plan:720-722). Require accepted J-0a/b/repaired J-0c at unchanged digests. Read /Users/Dev/kalayantra/run/{J0_PR_INVENTORY,J0_STATE_INVENTORY,J0_DISPOSITION}.json plus inherited sources. S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:80: repair→map→register.
  - Packet line 10: Only /Users/Dev/kalayantra/run/J0_FILE_OWNERSHIP.json (M:7101-7110); sandbox stages in JOB_SCRATCH for promotion. Scratch Python only; no permanent code/model edits or run/ program. Preparation: this packet/job evidence.
  - Packet line 20: 3. (I) INTERPRETATION J0D-I3: snapshot paths/heads; no fresh-diff claim (/Users/Dev/kalayantra/run/J0_PR_INVENTORY.json:4-26; M:7110).
  - Packet line 36: Positive fixture: multi-owner/shared, braces/directories, inactive entry, sourced exclusion/gate. Both run negatives: omitted/extra/duplicate row; bad hash/head/count; missing/wrong owner/false no-overlap; prose→clear; unreviewed exclusion; duplicate writable path/output; invented ID; wrong endpoint/path/missing wait; unresolved binding; cycle via model edge or landing→J-0m. Each refuses/unknown. No invented red history. Execution: KY_ITEM=J-0d bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 8: Release SUVARNA-L0L2-CLOSE-REV30-20261013. Historical schema v2.2; no DB/window/proof. Wave0 J-0c→J-0d→J-0→J-0m (plan:720-722). Require accepted J-0a/b/repaired J-0c at unchanged digests. Read controller-supplied /Users/Dev/kalayantra/run/{J0_PR_INVENTORY,J0_STATE_INVENTORY,J0_DISPOSITION}.json plus inherited sources. S/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:82: repair→map→register. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 10: Only /Users/Dev/kalayantra/run/J0_FILE_OWNERSHIP.json (M:7101-7110); sandbox stages in JOB_SCRATCH for promotion. Scratch Python only; no permanent code/model edits or run/ program. Preparation: this packet/job evidence. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 20: 3. (I) INTERPRETATION J0D-I3: snapshot paths/heads; no fresh-diff claim (/Users/Dev/kalayantra/run/J0_PR_INVENTORY.json:4-26; M:7110). — controller-supplied runtime evidence or output for cockpit promotion.

### `PACKET_J-0m_v1.md`

- References/stamp changed: true; bytes: 8696.
- Packet digest after: `f3470687628199d587afab98f0fe5314a5c8c4ed9141536807bad90f09f46387`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 7: Release SUVARNA-L0L2-CLOSE-REV30-20261013; run/revision in front matter. Wave 0 per plan §14. Schema v2.2 is historical and supplies no model proof; no protected window. Producer/owner S, not K. Execute only after independently accepted J-0a/b/c/d artifacts and earned J-0 join. Future input artifacts are prerequisites, never invented rows or a reason to bypass their acceptance. Plan model current brief is at 00_ARCHITECTURE/control/kalayantra/plan_model.json:4444-4467; J-0 join :4410-4437. Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:80, repair→map→register.
  - Packet line 18: Consume unchanged digest-bound J0_PR_INVENTORY.json, J0_STATE_INVENTORY.json, J0_DISPOSITION.json, J0_FILE_OWNERSHIP.json from /Users/Dev/kalayantra/run/. Preserve original snapshot/evidence and unresolved decisions/holds. One PR-sized inherited landing child per accepted PR or remaining source item, or recorded not-applicable backed by accepted disposition. Each child carries actual landing phase, owner, depends_on, full brief (spec/owns/tests/compat, normalized migration/op if applicable), completion_kind, producer, reviewer_rule, detector and step evidence appropriate to its kind (plan §6; charter §4.4). Reuse an existing exact-scope registered item when it already maps that row; no duplicate item or artifact writer.
  - Packet line 29: Scratch negative fixtures: duplicate child ID, unknown dependency/owner, missing required declaration, dependency cycle must be rejected by check_model; omitted/duplicated source row, wrong PR head, widened owns, missing shared wait, double artifact writer, removed parent dependency or flag with incomplete mapping must be rejected by the independent correspondence review. Restore all fixture mutations; output model unchanged except admitted declarations. KY_ITEM=J-0m bash "$KY_FLEET/precheck.sh" --item. No DB proof/readback needed.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 18: Consume controller-supplied unchanged digest-bound J0_PR_INVENTORY.json, J0_STATE_INVENTORY.json, J0_DISPOSITION.json, J0_FILE_OWNERSHIP.json from /Users/Dev/kalayantra/run/. Preserve original snapshot/evidence and unresolved decisions/holds. One PR-sized inherited landing child per accepted PR or remaining source item, or recorded not-applicable backed by accepted disposition. Each child carries actual landing phase, owner, depends_on, full brief (spec/owns/tests/compat, normalized migration/op if applicable), completion_kind, producer, reviewer_rule, detector and step evidence appropriate to its kind (plan §6; charter §4.4). Reuse an existing exact-scope registered item when it already maps that row; no duplicate item or artifact writer. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 29: Scratch negative fixtures: duplicate child ID, unknown dependency/owner, missing required declaration, dependency cycle must be rejected by check_model; omitted/duplicated source row, wrong PR head, widened owns, missing shared wait, double artifact writer, removed parent dependency or flag with incomplete mapping must be rejected by the independent correspondence review. Restore all fixture mutations; output model unchanged except admitted declarations. KY_ITEM=J-0m bash "$KY_FLEET/precheck.sh" --item. No DB proof/readback needed. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_J-1a_v1.md`

- References/stamp changed: true; bytes: 8988.
- Packet digest after: `a42c736ddf40b68abc0dbea10285121db1d4f7d96e450f9c4104f6c6f7c790ae`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases: P/A/C=spec_sources[1/2/3].path; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; O=/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-kv3-b-ops-scripts; T=/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/runbooks/SMALL_TEST_SITTING_CHECKLIST_v1_0.md. Lines 1-based.
  - Packet line 20: 2. (I) INTERPRETATION J1-I2: source-row/child bijection from accepted J-0c/d/m; preserve holds. Exclude PR3141; hold PR3140 outside phase 1 pending sourced reconciliation (C:96-104; T:61; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:51).
  - Packet line 35: KY_ITEM=J-1a bash "$KY_FLEET/precheck.sh" --item at launch; no DB proof claimed here.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SMALL_TEST_SITTING_CHECKLIST_v1_0.md` — `37d6cc9bafdf815a96a0311fdec448094705a055f95cbd691492c4b8fb72290b`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/ops/executor_ops.json` — `65d3f27eacdc106378500cf6c3b79ef756f7f3022ce86b904e1200a77802c16f`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/ops/operation_adapters.py` — `7c60341f04be7353bd1b470f83bcc4527e5f9738970bb4cdf8a0d87447fee8a4`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/ops/ops/README.md` — `b7c9a6c91ad6817bb5dde602fb652e0214aefe47e6f589cc42d8e2bffb22ac95`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/ops/ops/common.py` — `df4602cca69ca8603fda47df308e8d68e5df934c2d27fc3695dd24ac9e4edb96`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/ops/tests/test_operation_adapters.py` — `5eaa749f8c4c71e528e23921d4efe4bc86b9ad1110e7e1e5240a04a81ba12cc7`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/ops/tests/test_ops_backup.py` — `c719265c416f17a12007ae912c5cec6e0264fdb5ea6f633ffb121de09be5be3a`.
- Kept external references and why:
  - Packet line 21: 2. (I) INTERPRETATION J1-I2: source-row/child bijection from accepted J-0c/d/m; preserve holds. Exclude PR3141; hold PR3140 outside phase 1 pending sourced reconciliation (C:96-104; T:63; /Users/Dev/kalayantra/run/J0_DISPOSITION.json:51). — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 36: KY_ITEM=J-1a bash "$KY_FLEET/precheck.sh" --item at launch; no DB proof claimed here. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_J-3b_v1.md`

- References/stamp changed: true; bytes: 8946.
- Packet digest after: `99a3b09799ac9c104994c924783b70d3374301d7165e5a14560f9f2bfaa4eabb`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases: Y=platform/python-sidecar; F=00_ARCHITECTURE/briefs/kalayantra/fleet; P/C/R=spec_sources[0..2].path; E=Y/services/gochara_eval/extract.py; Z=F/FROZEN_PATHS.txt; M/SR=00_ARCHITECTURE/control/kalayantra/{plan_model.json,SCHEMA_RECEIPT_v2_2.json}; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; MR=94c41df3de30d1634685fee25c109183fbd4cb0f:Y/services/gochara_kernel/measuring_report.py; OA=26806eeaa:F/operation_adapters.py. Git citations=immutable blobs; lines 1-based.
  - Packet line 35: DB/ephemeris run, exit0/no skips; CI/Kāla DB Tests/independent review. Repo: KY_ITEM=J-3b bash "$KY_FLEET/precheck.sh" --item.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 35: DB/ephemeris run, exit0/no skips; CI/Kāla DB Tests/independent review. Repo: KY_ITEM=J-3b bash "$KY_FLEET/precheck.sh" --item. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_J-4p_v1.md`

- References/stamp changed: true; bytes: 8953.
- Packet digest after: `e448e2a3a76b70a881f5d519f7948479387a898eae38e5f100aeb8ba6c266be2`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Paths repo-relative, lines1-based. P/S/D/A=spec_sources[0..3].path; Y=platform/python-sidecar/; K=Y/services/gochara_kernel/; R=Y/services/gochara_rules/; C=Y/scripts/kala_gochara_cutover/; T=Y/tests/l3/gochara/; U=Y/tests/l3/gochara_rules/; M/SR=00_ARCHITECTURE/control/kalayantra/{plan_model.json,SCHEMA_RECEIPT_v2_2.json}; F=00_ARCHITECTURE/briefs/kalayantra/fleet/; E=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; O=E/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md; DD=Y/services/gochara_grammar/dasha_data.py; IS=K/inventory_store.py; B=C/step06b_windows_projection.py; SQL=platform/migrations/1206_gochara_search_inventory_completeness.sql.
  - Packet line 8: Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,13-19; registry30(job). Wave0 before J-1a/J-4d (P:720-726); accepted install/J-0m/K0-SV heads+squashes required.
  - Packet line 9: SR:5,8-15 historical; /Users/Dev/kalayantra/run/schema/prod_schema.sql:5573-5595,14274-14290 columns confirmed; seeded2026-10-12T07:15:26Z; SHA256=f82aa93c60c397eb3e44c5317a1721bfa75db6a9fd32c551b5c5f89796804120. Schema/ledger≠SR:16-25. Measured current receipt/rebind before BUILD (E/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:81). PW1.0=00_ARCHITECTURE/briefs/kalayantra/KALA_PROTECTED_WINDOW_v1_0.md:3.
  - Packet line 49: Platform: npm run codegen:capability-estate-census; then :check. Exit0/no skips. KY_ITEM=J-4p bash "$KY_FLEET/precheck.sh" --item. Independent rerun/mutants+CI/Kāla DB Tests at reviewed head.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/OWNER_RULINGS_DIGEST_A.md` — `f35373f77548555f00a20b294f42d094104ad51197dfdb786887b626a887909a`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 9: Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,13-19; registry30(job). Wave0 before J-1a/J-4d (P:720-726); accepted install/J-0m/K0-SV heads+squashes required. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 10: SR:5,8-15 historical; /Users/Dev/kalayantra/run/schema/prod_schema.sql:5573-5595,14274-14290 columns confirmed; seeded2026-10-12T07:15:26Z; SHA256=f82aa93c60c397eb3e44c5317a1721bfa75db6a9fd32c551b5c5f89796804120. Schema/ledger≠SR:16-25. Measured current receipt/rebind before BUILD (E/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:83). PW1.0=00_ARCHITECTURE/briefs/kalayantra/KALA_PROTECTED_WINDOW_v1_0.md:3. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 50: Platform: npm run codegen:capability-estate-census; then :check. Exit0/no skips. KY_ITEM=J-4p bash "$KY_FLEET/precheck.sh" --item. Independent rerun/mutants+CI/Kāla DB Tests at reviewed head. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K3-1b_v1.md`

- References/stamp changed: true; bytes: 8958.
- Packet digest after: `9d783e386777261f4444d001bd14442aca931c0cc4ffa3019fa9768fb92c0019`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: P/A=spec_sources[0/1].path; Y=platform/python-sidecar/; M=platform/migrations/; F=00_ARCHITECTURE/briefs/kalayantra/fleet/; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md. Lines 1-based. Release SUVARNA-L0L2-CLOSE-REV30-20261013.
  - Packet line 36: Y: python3 -B -m pytest tests/l3/ka_vighnakara -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest". Admitted DB slot: exit0/no skips; source-output axes/IDs/pins/reasons, noncandidate preservation. KY_ITEM=K3-1b bash "$KY_FLEET/precheck.sh" --item. No forecaster/rates/weights or writes/commit/close/asset_throughput.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWERS_01-02.md` — `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Kept external references and why:
  - Packet line 36: Y: python3 -B -m pytest tests/l3/ka_vighnakara -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest". Admitted DB slot: exit0/no skips; source-output axes/IDs/pins/reasons, noncandidate preservation. KY_ITEM=K3-1b bash "$KY_FLEET/precheck.sh" --item. No forecaster/rates/weights or writes/commit/close/asset_throughput. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K3-2_v1.md`

- References/stamp changed: true; bytes: 8962.
- Packet digest after: `8588f6dcad8ae88875c849b7ac1719dd3d6fadab472e9c882d4d7abd63506612`.
- admitted before/after: **false / false**.
- Checker reasons after: spec_source_sha256.
- External references found before:
  - Packet line 7: P/A/V=spec_sources[0..2].path; Y=platform/python-sidecar; D=Y/services/gochara_rules/vedha_derive.py; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md. Lines1-based.
  - Packet line 38: Y: KALA_REQUIRE_DB=1 python3 -B -m pytest tests/l3/ka_vighnakara tests/l3/kala_db/ka_vighnakara -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest". Exit0/no skips; CI/DB. python3 -B -m pipeline.orchestrator.provenance_inventory then --check; platform npm run codegen:capability-estate-census then :check. KY_ITEM=K3-2 bash "$KY_FLEET/precheck.sh" --item.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWERS_01-02.md` — `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Kept external references and why:
  - Packet line 38: Y: KALA_REQUIRE_DB=1 python3 -B -m pytest tests/l3/ka_vighnakara tests/l3/kala_db/ka_vighnakara -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest". Exit0/no skips; CI/DB. python3 -B -m pipeline.orchestrator.provenance_inventory then --check; platform npm run codegen:capability-estate-census then :check. KY_ITEM=K3-2 bash "$KY_FLEET/precheck.sh" --item. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K4-2a_v1.md`

- References/stamp changed: true; bytes: 8979.
- Packet digest after: `96794db2a3af04ea8395652de4577408211e2ed3e5cdbdc5281067c23174eb59`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2a.c7dcc7ee8d0d066f0f6cfb20e548c67f2a476d5a.md. Code: `git show M:<path>`.
  - Packet line 38: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2a.txt`. 
  - Packet line 39: `KY_ITEM=K4-2a bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 6: Aliases: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run (controller evidence); U=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2a.c7dcc7ee8d0d066f0f6cfb20e548c67f2a476d5a.md. Code: `git show M:<path>`. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 38: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2a.txt`.  — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 39: `KY_ITEM=K4-2a bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K4-2aw_v1.md`

- References/stamp changed: true; bytes: 8717.
- Packet digest after: `ea474ecc1f36f64871bc681ce4ca613f03966cb4e2a9b4089039e7ac04857743`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2aw.956a250197e437e7a43d41bb6e5260bf9ab6cd82.md. Code: `git show M:<path>`.
  - Packet line 38: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2aw.txt`. Also Y/tests/test_fix_plan_proofs.py FIX5; retain full jury coverage.
  - Packet line 39: `KY_ITEM=K4-2aw bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 6: Aliases: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run (controller evidence); U=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2aw.956a250197e437e7a43d41bb6e5260bf9ab6cd82.md. Code: `git show M:<path>`. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 38: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2aw.txt`. Also Y/tests/test_fix_plan_proofs.py FIX5; retain full jury coverage. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 39: `KY_ITEM=K4-2aw bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K4-2b_v1.md`

- References/stamp changed: true; bytes: 8721.
- Packet digest after: `3b3d527ce4e5e4ab461c5708ec9c7689bafa39820d329b3e8793fe828af29de7`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2b.c3c16d1c4cadbe882f973abf7f3f4ed1d72715d0.md. Code: `git show M:<path>`.
  - Packet line 37: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2b.txt`. 
  - Packet line 38: `KY_ITEM=K4-2b bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 6: Aliases: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run (controller evidence); U=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-2b.c3c16d1c4cadbe882f973abf7f3f4ed1d72715d0.md. Code: `git show M:<path>`. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 37: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-2b.txt`.  — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 38: `KY_ITEM=K4-2b bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K4-3_v1.md`

- References/stamp changed: true; bytes: 8944.
- Packet digest after: `6f45f46bfb4e002728549cfbe2b7b587279c7b3fc24c7e4aab07fb1cf12c88aa`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases, 1-based lines: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run; U=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-3.912efb617ffe9b7e33af5a3a3c22045a74bbd2be.md. Code: `git show M:<path>`.
  - Packet line 38: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-3.txt`. 
  - Packet line 39: `KY_ITEM=K4-3 bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05).
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 6: Aliases: P/A=spec_sources[0/1].path; R=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; F=00_ARCHITECTURE/briefs/kalayantra/fleet; Y=platform/python-sidecar; RUN=/Users/Dev/kalayantra/run (controller evidence); U=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; E=RUN/EVENTS.jsonl; V=RUN/verdicts/K4-3.912efb617ffe9b7e33af5a3a3c22045a74bbd2be.md. Code: `git show M:<path>`. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 38: Qualified interpreter/SQL slot, cwd repo: `xargs python3 -B -m pytest -q -rs -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest" < /Users/Dev/kalayantra/run/tests/K4-3.txt`.  — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 39: `KY_ITEM=K4-3 bash "$KY_FLEET/precheck.sh" --item`. Exit0/no skips/setup errors. Carry mutants only with source/fixture/log hash equality + head controls. Required CI at H incl relevant Kāla DB Tests successful; absent/skipped/pending/red insufficient (A:26-29; F/cards/PARIKSAKA.md PA-05). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K7-3_v1.md`

- References/stamp changed: true; bytes: 8931.
- Packet digest after: `91ee719152f9042fb51253914505c77cbff887837b3dae03e53db496d65b0736`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: P/A=spec_sources[0/1].path; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; R=platform/src/lib/retrieval/registry/layers/L3_kala; C=R/view_common.ts; Y=platform/python-sidecar; U=/Users/Dev/kalayantra/run; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; X=S/fast/jobs/X-20261013T115956Z-k73-pins/K7-3_PINS.md. H=959d324483de3f3f26da98d4cc9b60d88cf39417; M/P current.
  - Packet line 50: Commands: platform `KALA_VIEW_DB_TESTS=1 npm test -- src/lib/retrieval/registry/layers/L3_kala`; platform-mcp `KALA_VIEW_DB_TESTS=1 python3 -B -m pytest src/tools/kala_views/test_published_now_item.py`; budget suite; platform both codegen:capability-estate-census:check/codegen:capability-knowledge:check. `KY_ITEM=K7-3 bash "$KY_FLEET/precheck.sh" --item`; TESTS newline-owned paths. Exit0/no skips; disposable SQL/CI/Kāla DB Tests. Three tests_and_verdict steps: these paths/commands + independent ACCEPTED named steps (S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:75); cockpit generic detector, no null closure.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_11_OWNER_OPEN_ITEMS.md` — `8d7bf3dd0a8ae86eae83d3d9cf39260254fa639dd9d58e15605124fdfa4c4779`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/K7-3_PINS.md` — `26b72c85091013458c3d82edfd3cff1a24f239399eadf5110a174a51d234dbfd`.
- Kept external references and why:
  - Packet line 6: P/A=spec_sources[0/1].path; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; R=platform/src/lib/retrieval/registry/layers/L3_kala; C=R/view_common.ts; Y=platform/python-sidecar; U=/Users/Dev/kalayantra/run (controller evidence); S=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; X=S/K7-3_PINS.md. H=959d324483de3f3f26da98d4cc9b60d88cf39417; M/P current. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 50: Commands: platform `KALA_VIEW_DB_TESTS=1 npm test -- src/lib/retrieval/registry/layers/L3_kala`; platform-mcp `KALA_VIEW_DB_TESTS=1 python3 -B -m pytest src/tools/kala_views/test_published_now_item.py`; budget suite; platform both codegen:capability-estate-census:check/codegen:capability-knowledge:check. `KY_ITEM=K7-3 bash "$KY_FLEET/precheck.sh" --item`; TESTS newline-owned paths. Exit0/no skips; disposable SQL/CI/Kāla DB Tests. Three tests_and_verdict steps: these paths/commands + independent ACCEPTED named steps (S/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:77); cockpit generic detector, no null closure. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K7-4_v1.md`

- References/stamp changed: true; bytes: 8966.
- Packet digest after: `3219f04ee8d3d14b497cd5a80129ba295c79cc24d338e951bc56ba9e13e2affa`.
- admitted before/after: **false / false**.
- Checker reasons after: schema, test_unavailable.
- External references found before:
  - Packet line 7: P=00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md; C=spec_sources[0].path; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; Y=platform/python-sidecar; R=platform/src/lib/retrieval/registry/layers/L3_kala; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; T=S/engines/lane2/owner/OWNER_RULINGS_K7-4_TABLE.md; O=S/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md; U=/Users/Dev/kalayantra/wt/k2/Y/services/ka_sangam/jury/reader_contract.json; L=/Users/Dev/kalayantra/wt/k5/R/view_common.ts.
  - Packet line 49: repo: `KY_ITEM=K7-4 bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item`
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/OWNER_RULINGS_DIGEST_A.md` — `f35373f77548555f00a20b294f42d094104ad51197dfdb786887b626a887909a`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/OWNER_RULINGS_K7-4_TABLE.md` — `23b5987d4b2cba7a1869a55118bffc16169e7cabb5f78ffd5cd02517a4e67a0c`.
- Kept external references and why:
  - None.
- (I) INTERPRETATION: missing retired wt/k2 and wt/k5 reads now resolve to existing repository files; historical equality is unverified, accepted-base gates remain.

### `PACKET_K8-R26_v1.md`

- References/stamp changed: true; bytes: 8949.
- Packet digest after: `0a60930c2944505766bbdbf1bfc514a77dca5c5f952c158f9df8c9bbad290154`.
- admitted before/after: **false / false**.
- Checker reasons after: spec_source_sha256.
- External references found before:
  - Packet line 8: Citation keys: P=00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md; C=00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md; F=00_ARCHITECTURE/briefs/kalayantra/fleet; B=F/kyd_kinds_build.py; L=F/kyd_kinds_land.py; V=F/kyverdicts.py; G=platform/scripts/governance/pravaha_tracker/completion.py; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3.
  - Packet line 10: M:4204-4213: /Users/Dev/kalayantra/run/K8_GATE_TABLE_R26.md (pointer); 00_ARCHITECTURE/briefs/l3_families/measurements/K8_GATE_TABLE_R26_v1_0.md (canonical). S adds existing PR oracle 00_ARCHITECTURE/briefs/l3_families/measurements/test_k8_gate_table.py to model owns before routing. Documents/offline oracle only. Model correction/registration/PR disposition are cockpit/S work. Restricted workers stage scratch proposals for promotion.
  - Packet line 33: Assigned PR worktree: `python3 -B -m pytest 00_ARCHITECTURE/briefs/l3_families/measurements/test_k8_gate_table.py -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"`; `KY_ITEM=K8-R26 bash "$KY_FLEET/precheck.sh" --item`. Exit0/all tests + green applicable CI. Extend oracle: omission/duplicate, wrong locator/binding/revision/introduction, same-version stale source, NONE→PASS, unsupported N/A/prose, runtime diff. Scratch mutations via existing K8_GATE_TABLE_DOC (oracle:13). Keyword checks alone prove no prose meaning. Reject missing/wrong digest, same author/reviewer, changed head/bytes, missing KYD/impact disposition or open dependency. No new interface.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_11_OWNER_OPEN_ITEMS.md` — `8d7bf3dd0a8ae86eae83d3d9cf39260254fa639dd9d58e15605124fdfa4c4779`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/DEFINE_K8-R26.md` — `2fc2f0e6758380d41d478a21cd8a3f16c51e284d00777d363db7179f85a30701`.
- Kept external references and why:
  - Packet line 11: M:4204-4213: /Users/Dev/kalayantra/run/K8_GATE_TABLE_R26.md (pointer); 00_ARCHITECTURE/briefs/l3_families/measurements/K8_GATE_TABLE_R26_v1_0.md (canonical). S adds existing PR oracle 00_ARCHITECTURE/briefs/l3_families/measurements/test_k8_gate_table.py to model owns before routing. Documents/offline oracle only. Model correction/registration/PR disposition are cockpit/S work. Restricted workers stage scratch proposals for promotion. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 34: Assigned PR worktree: `python3 -B -m pytest 00_ARCHITECTURE/briefs/l3_families/measurements/test_k8_gate_table.py -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest"`; `KY_ITEM=K8-R26 bash "$KY_FLEET/precheck.sh" --item`. Exit0/all tests + green applicable CI. Extend oracle: omission/duplicate, wrong locator/binding/revision/introduction, same-version stale source, NONE→PASS, unsupported N/A/prose, runtime diff. Scratch mutations via existing K8_GATE_TABLE_DOC (oracle:13). Keyword checks alone prove no prose meaning. Reject missing/wrong digest, same author/reviewer, changed head/bytes, missing KYD/impact disposition or open dependency. No new interface. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_K8-REG_v1.md`

- References/stamp changed: true; bytes: 8989.
- Packet digest after: `20d5c7a288e595987136701c78826fd16f3fed5946f7142da1091a1279818411`.
- admitted before/after: **false / false**.
- Checker reasons after: spec_source_sha256.
- External references found before:
  - Packet line 6: P/M/A/E/F/N=spec_sources[0..5].path; Y=platform/python-sidecar; G=platform/scripts/governance; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3. 1-based citations.
  - Packet line 8: Release SUVARNA-L0L2-CLOSE-REV30-20261013 (/Users/Dev/kalayantra/run/RELEASE_RECEIPT.json); Wave1 preparation (P:728-730; S/engines/lane2/B4_RULINGS.md:5).
  - Packet line 49: KY_ITEM=K8-REG bash "$KY_FLEET/precheck.sh" --item. Exit0/negatives/CI/Kala DB Tests. Independent head verdict + deployed-squash containment/readback (P:380-389), never branch alone.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - Packet line 9: Release SUVARNA-L0L2-CLOSE-REV30-20261013 (/Users/Dev/kalayantra/run/RELEASE_RECEIPT.json); Wave1 preparation (P:728-730; S/B4_RULINGS.md:7). — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 50: KY_ITEM=K8-REG bash "$KY_FLEET/precheck.sh" --item. Exit0/negatives/CI/Kala DB Tests. Independent head verdict + deployed-squash containment/readback (P:380-389), never branch alone. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KA-3a_v1.md`

- References/stamp changed: true; bytes: 8994.
- Packet digest after: `c36614a320d929d9d935adb01e83722c7e1f6f852704dce62b8369e5fdf4f6e6`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Y=platform/python-sidecar; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; SR=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; C=Y/services/kala_core; D=Y/services/gochara_rules/vedha_derive.py; SQL=/Users/Dev/kalayantra/run/schema/prod_schema.sql. Lines1-based.
  - Packet line 8: Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json. Wave1 preparation. Require activation/J-0m ownership/K0a-4/KA-1w/KA-2 heads+squashes/inherited landing (M:2734-2738,2771). SR historical: fresh schema/slot before BUILD, approved window/readback before consumers.
  - Packet line 42: Y: python3 -B -m pipeline.orchestrator.provenance_inventory; then --check. Platform: npm run codegen:capability-estate-census; then :check. Inventory hash equality. KY_ITEM=KA-3a bash "$KY_FLEET/precheck.sh" --item. Exit0/no skips; CI/Kāla DB Tests/review. Five steps M:2742-2746: tests+verdict (answer05:75).
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/OWNER_RULINGS_DIGEST_A.md` — `f35373f77548555f00a20b294f42d094104ad51197dfdb786887b626a887909a`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWERS_01-02.md` — `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Kept external references and why:
  - Packet line 6: Y=platform/python-sidecar; M=00_ARCHITECTURE/control/kalayantra/plan_model.json; SR=00_ARCHITECTURE/control/kalayantra/SCHEMA_RECEIPT_v2_2.json; S=00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS; C=Y/services/kala_core; D=Y/services/gochara_rules/vedha_derive.py; SQL=/Users/Dev/kalayantra/run/schema/prod_schema.sql. Source lines. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 9: Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json. Wave1 preparation. Require activation/J-0m ownership/K0a-4/KA-1w/KA-2 heads+squashes/inherited landing (M:2734-2738,2771). SR historical: fresh schema/slot before BUILD, approved window/readback before consumers. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 43: Y: python3 -B -m pipeline.orchestrator.provenance_inventory; then --check. Platform: npm run codegen:capability-estate-census; then :check. Inventory hash equality. KY_ITEM=KA-3a bash "$KY_FLEET/precheck.sh" --item. Exit0/no skips; CI/Kāla DB Tests/review. Five steps M:2742-2746: tests+verdict (answer05:77). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KA-3b_v1.md`

- References/stamp changed: true; bytes: 8957.
- Packet digest after: `a9760c332f20c8f3ab2e519b8819ac914565a86fd1081b9f8189cd4eb02d9e39`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 7: P/M/C/A/W/D/B/V=spec_sources[0..7].path; Y=platform/python-sidecar; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md; R=S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md. Lines 1-based.
  - Packet line 8: Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,18; revision 30 from cockpit. Wave 1=P:728-730 preparation. Historical SR v2.2; children need current schema/accepted heads/squash mappings. Keep D-R8/J-0m/KA-3a (M:2824-2828).
  - Packet line 36: Registration checker platform/scripts/governance/pravaha_tracker/server.py:269-315: check_model(candidate_model)==[]; reviewer checks correspondence. KY_ITEM=KA-3b bash "$KY_FLEET/precheck.sh" --item checks descriptor, never launches join.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWERS_01-02.md` — `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/DEFINE_KA-3a.md` — `be61c28b34a43f5d8c01ce9f01f1077fb88a03136ed7ae878b841a342df46b7f`.
- Kept external references and why:
  - Packet line 9: Release SUVARNA-L0L2-CLOSE-REV30-20261013; /Users/Dev/kalayantra/run/RELEASE_RECEIPT.json:2,18; revision 30 from cockpit. Wave 1=P:728-730 preparation. Historical SR v2.2; children need current schema/accepted heads/squash mappings. Keep D-R8/J-0m/KA-3a (M:2824-2828). — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 37: Registration checker platform/scripts/governance/pravaha_tracker/server.py:269-315: check_model(candidate_model)==[]; reviewer checks correspondence. KY_ITEM=KA-3b bash "$KY_FLEET/precheck.sh" --item checks descriptor, never launches join. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KA-4b_v1.md`

- References/stamp changed: true; bytes: 8994.
- Packet digest after: `b0a275ea51102aefac6c6791aba08fa2dc401e27da7a724066aec4d6028f842b`.
- admitted before/after: **false / false**.
- Checker reasons after: schema, test_unavailable.
- External references found before:
  - Packet line 7: S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; O=S/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md;
  - Packet line 8: R=platform/src/lib/retrieval/registry/layers/L3_kala; B=platform/src/lib/retrieval/registry/layers/L0_brahmagyan; E=platform-mcp/src/tools/kala_views; H=platform-mcp/src/lib; W=/Users/Dev/kalayantra/wt/k7.
  - Packet line 58: Root `KY_ITEM=KA-4b bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item`; TESTS newline-delimited platform paths per F/precheck.sh:94-103; MCP separately.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/OWNER_RULINGS_DIGEST_A.md` — `f35373f77548555f00a20b294f42d094104ad51197dfdb786887b626a887909a`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWERS_01-02.md` — `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Kept external references and why:
  - None.
- (I) INTERPRETATION: missing retired wt/k7 reads now resolve to existing repository files; historical equality is unverified, accepted-base gates remain.

### `PACKET_KA-4c_v1.md`

- References/stamp changed: true; bytes: 8984.
- Packet digest after: `1ca7488f2779ae7ced48f76818af62b4e8efaa774b1e63728a4ac046ff214075`.
- admitted before/after: **false / false**.
- Checker reasons after: schema, test_unavailable.
- External references found before:
  - Packet line 7: Prefixes: Y=platform/python-sidecar; F=00_ARCHITECTURE/briefs/kalayantra/fleet; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; U=S/engines/surrogate/SURROGATE_ANSWERS_01-02.md; O=S/engines/lane2/owner/OWNER_RULINGS_DIGEST_A.md; B=S/engines/lane2/B4_RULINGS.md.
  - Packet line 59: cwd repo: `KY_ITEM=KA-4c bash /Users/Dev/kalayantra/fleet_live/precheck.sh --item`
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/B4_RULINGS.md` — `97921da696399500ad7f32fa0d6149d8a860924578534c9a820ad052da96c89e`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/OWNER_RULINGS_DIGEST_A.md` — `f35373f77548555f00a20b294f42d094104ad51197dfdb786887b626a887909a`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWERS_01-02.md` — `ac796ea0551dd9eee59977dec56eacac40a8aa62f738c065bc1e4e313c1237ee`.
- Kept external references and why:
  - None.

### `PACKET_KV3-B-BASELINE_v1.md`

- References/stamp changed: true; bytes: 8648.
- Packet digest after: `5542363a48bb1ebab82a93dcda1728434c02ba6a21b6176b7a5bf338320d0870`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 26: "a test that would read ~/.claude, ~/.codex or /Users/Dev/kalayantra/logs: the root guard fails it"]},
  - Packet line 31: P = `scripts/token_economy/token_baseline.py`; SRC = `/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/token_baseline.py`; H = `28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176`.
  - Packet line 58: 2. What P is (read from the bytes; do not change it). Read-only, standard library. `python3 -B P [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--json OUT] [--md OUT] [--waste] [--jobs N]`, exit 0; `main(argv=None)`. Three module-level roots: `CLAUDE_ROOT` (`~/.claude/projects`, `**/*.jsonl`), `CODEX_ROOT` (`~/.codex/sessions`, `**/rollout-*.jsonl`), `FLEET_LOGS` (`/Users/Dev/kalayantra/logs`, `*.log`). Four classes, `CLASSES` = `input`, `output`, `cache_creation`, `cache_read`. A call is keyed `(message.id, requestId)`; repeats keep the per-class maximum, within a file and across files. A line that is not JSON is skipped. Only paths that `is_madhav()` accepts are counted (the pytest base path may itself hold one of its tokens: assert that filter on the function, not on a directory name). JSON keys include `sources` (`claude_files`, `claude_files_with_usage`, `codex_madhav_sessions`, `fleet_logs`, `claude_api_calls_deduped`, `claude_cross_file_duplicate_keys_dropped`), `grand_total` (the four classes + `total`), `by_provider`, `by_role`, `by_model`, `by_workspace`, `top_sessions` (20 at most).
  - Packet line 69: **Depends on.** Wave 1; nothing. KV3-B-KYREPORT (wave 2) may assume: the path P; the call form `python3 -B <installed copy> [--since D] [--until D] --json OUT` and the keys of 2; that nothing is installed or reported from P until this packet's pushed head is independently reviewed and imported by `kyreport.py baseline-import` (receipt `$KY_RUN/BASELINE_RECEIPT.json`): until then every baseline-backed figure is `unknown`.
  - Packet line 77: **Do not.** Edit P's bytes; run P against the real roots; read `~/.claude`, `~/.codex`, `/Users/Dev/kalayantra/logs` or any other scratch file; install or import the baseline; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/token_baseline.py` — `28c1bb5b9df644a0a60a44a80b0a9a01c949db2838e03bf766631411b45c4176`.
- Kept external references and why:
  - Packet line 26: "a test that would read ~/.claude, ~/.codex or /Users/Dev/kalayantra/logs: the root guard fails it"]}, — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 58: 2. What P is (read from the bytes; do not change it). Read-only, standard library. `python3 -B P [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--json OUT] [--md OUT] [--waste] [--jobs N]`, exit 0; `main(argv=None)`. Three module-level roots: `CLAUDE_ROOT` (`~/.claude/projects`, `**/*.jsonl`), `CODEX_ROOT` (`~/.codex/sessions`, `**/rollout-*.jsonl`), `FLEET_LOGS` (`/Users/Dev/kalayantra/logs`, `*.log`). Four classes, `CLASSES` = `input`, `output`, `cache_creation`, `cache_read`. A call is keyed `(message.id, requestId)`; repeats keep the per-class maximum, within a file and across files. A line that is not JSON is skipped. Only paths that `is_madhav()` accepts are counted (the pytest base path may itself hold one of its tokens: assert that filter on the function, not on a directory name). JSON keys include `sources` (`claude_files`, `claude_files_with_usage`, `codex_madhav_sessions`, `fleet_logs`, `claude_api_calls_deduped`, `claude_cross_file_duplicate_keys_dropped`), `grand_total` (the four classes + `total`), `by_provider`, `by_role`, `by_model`, `by_workspace`, `top_sessions` (20 at most). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 69: **Depends on.** Wave 1; nothing. KV3-B-KYREPORT (wave 2) may assume: the path P; the call form `python3 -B <installed copy> [--since D] [--until D] --json OUT` and the keys of 2; that nothing is installed or reported from P until this packet's pushed head is independently reviewed and imported by `kyreport.py baseline-import` (receipt `$KY_RUN/BASELINE_RECEIPT.json`): until then every baseline-backed figure is `unknown`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 77: **Do not.** Edit P's bytes; run P against the real roots; read `~/.claude`, `~/.codex`, `/Users/Dev/kalayantra/logs` or any other scratch file; install or import the baseline; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
- (I) INTERPRETATION: SRC denotes the archived payload after its two provenance lines; original SHA H and unchanged-copy contract apply to payload bytes, not the provenance wrapper. Existing P also hashes exactly to H.

### `PACKET_KV3-B-EXECUTOR-TABLE_v1.md`

- References/stamp changed: false; bytes: 8978.
- Packet digest after: `7a347319d4578285833c0b082e5a57f1acae1a09f61bdc4a9341e09692f7ca84`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 37: **Owns** `F/executor_ops.json`; in `F/executor.py` and `F/executor.sh` ONLY the git-handle path (`GIT`); `F/tests/test_executor_table.py` (new). Prohibited: every other line of executor.py; the running executor, `$KY_ROOT/exec`, `$KY_RUN/ops`, the installed trees; the plan model (read-only); FROZEN paths.
  - Packet line 64: B. executor.py: `GIT` = `KY_SOURCE_REPO` from the environment, default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign` (plan §5 campaign checkout; as in kyctl.sh and kyveto.py), replacing `KY_ROOT/wt/campaign`; INTERPRETATION: the repository whose `origin/main` supplies table and scripts is thereby environment-selected, as `KY_ROOT` already made it. executor.sh: the same for its `GIT`. No other code line changes. `validate`, `execute`, `run_one`, `main`, `lease_live`, `request_digest`, `fence_quiescent`, `refresh_refusal_reason`, `handover_from_main`, `refresh_from_main_or_fail_closed`, `capabilities`, `run_group` and every constant (`CHILD_ENV_ALLOW`, `SAFE_*`, `APPROVAL_MAX_AGE_S`, `MAX_TIMEOUT`, `CANONICAL_CHART`) stay byte-identical: that is the authority boundary.
  - Packet line 67: - request `$KY_RUN/ops/requests/<operation_id>.json`: `{operation_id, kind, item_id, idempotency_key, requested_by, kyd, args, timeout_s?}`; a production kind adds `chart_id` (the canonical chart), `lease_id`, `reviewed_commit` (merged to main), `expires_at`, `acceptance_receipt` (a path under `run/ops/acceptance/`);
  - Packet line 68: - acceptance `$KY_RUN/ops/acceptance/<operation_id>.json`: `{result: "ACCEPTED", operation_id, by: v1|v2|v3|v4, reviewed_commit, ts, request_sha256, rows, checks: {backup_taken, restore_verified, dry_run_passed}}`; `request_sha256` = sha256 of the request as sorted compact JSON without `acceptance_receipt`; at most 3 h old;
  - Packet line 69: - receipt `$KY_RUN/ops/receipts/<operation_id>.json`: `{operation_id, kind, item_id, status: RUNNING|COMPLETED|FAILED|REFUSED|INTERRUPTED, reason, exit_code, request_sha256, reviewed_commit, output_file, output_sha256, ts}`;
  - Packet line 70: - fence `$KY_RUN/ops/PRODUCTION_PENDING.json`, quiescence `…/acceptance/<operation_id>.quiescence.json` `{operation_id, request_sha256, result: "ACCEPTED", by, ts}`;
  - Packet line 84: **Do not** edit outside Owns (plan, cards, schemas, packets, model); enable an entry; start or stop the executor; write an operation request; fetch or touch the campaign checkout; rebase or force-push; read credentials, `executor.env` or pgenv; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 37: **Owns** `F/executor_ops.json`; in `F/executor.py` and `F/executor.sh` ONLY the git-handle path (`GIT`); `F/tests/test_executor_table.py` (new). Prohibited: every other line of executor.py; the running executor, `$KY_ROOT/exec`, `$KY_RUN/ops`, the installed trees; the plan model (read-only); FROZEN paths. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 64: B. executor.py: `GIT` = `KY_SOURCE_REPO` from the environment, default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign` (plan §5 campaign checkout; as in kyctl.sh and kyveto.py), replacing `KY_ROOT/wt/campaign`; INTERPRETATION: the repository whose `origin/main` supplies table and scripts is thereby environment-selected, as `KY_ROOT` already made it. executor.sh: the same for its `GIT`. No other code line changes. `validate`, `execute`, `run_one`, `main`, `lease_live`, `request_digest`, `fence_quiescent`, `refresh_refusal_reason`, `handover_from_main`, `refresh_from_main_or_fail_closed`, `capabilities`, `run_group` and every constant (`CHILD_ENV_ALLOW`, `SAFE_*`, `APPROVAL_MAX_AGE_S`, `MAX_TIMEOUT`, `CANONICAL_CHART`) stay byte-identical: that is the authority boundary. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 67: - request `$KY_RUN/ops/requests/<operation_id>.json`: `{operation_id, kind, item_id, idempotency_key, requested_by, kyd, args, timeout_s?}`; a production kind adds `chart_id` (the canonical chart), `lease_id`, `reviewed_commit` (merged to main), `expires_at`, `acceptance_receipt` (a path under `run/ops/acceptance/`); — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 68: - acceptance `$KY_RUN/ops/acceptance/<operation_id>.json`: `{result: "ACCEPTED", operation_id, by: v1|v2|v3|v4, reviewed_commit, ts, request_sha256, rows, checks: {backup_taken, restore_verified, dry_run_passed}}`; `request_sha256` = sha256 of the request as sorted compact JSON without `acceptance_receipt`; at most 3 h old; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 69: - receipt `$KY_RUN/ops/receipts/<operation_id>.json`: `{operation_id, kind, item_id, status: RUNNING|COMPLETED|FAILED|REFUSED|INTERRUPTED, reason, exit_code, request_sha256, reviewed_commit, output_file, output_sha256, ts}`; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 70: - fence `$KY_RUN/ops/PRODUCTION_PENDING.json`, quiescence `…/acceptance/<operation_id>.quiescence.json` `{operation_id, request_sha256, result: "ACCEPTED", by, ts}`; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 84: **Do not** edit outside Owns (plan, cards, schemas, packets, model); enable an entry; start or stop the executor; write an operation request; fetch or touch the campaign checkout; rebase or force-push; read credentials, `executor.env` or pgenv; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-FINALIZE_v1.md`

- References/stamp changed: false; bytes: 8988.
- Packet digest after: `9eb73c8d00dbe89ffe44120a5e14cd4eab56cd784d8fb4392e353196517242ec`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 40: PID/PGID + process-start identity; write `$KY_RUN/DRAIN_RECEIPT.json` from measured drain
  - Packet line 43: "$KY_RUN/DRAIN_RECEIPT.json"`. Remove eligible owned item worktrees and session DBs;
  - Packet line 44: write `$KY_RUN/FINAL_RECEIPT.json` binding the accepted drain digest, close-report
  - Packet line 49: --artifact-path "$KY_RUN/FINAL_RECEIPT.json"`. The tracker stays available throughout.
  - Packet line 57: **Contract.** R = $KY_RUN, F = $KY_FLEET, ky = $KY_ROOT/bin/ky.
  - Packet line 58: - bash finalize.sh (an argument → exit 64). Run by executor.py execute() (op finalize) as ["bash", <temporary copy>], cwd $KY_ROOT, env = its CHILD_ENV_ALLOW + SE_EPHE_PATH + KY_ROOT only, 21600 s: no dirname "$0"; R, F default from $KY_ROOT; KY_SCRATCH, KY_SOURCE_REPO as kyctl.sh l.65–67. Exit 0 only after C-4's guarded completion, else 1. KY_* knobs kept.
  - Packet line 63:  3. Each worktree (never $KY_SOURCE_REPO): absent | clean | dirty_kept | unpushed_kept | busy_kept.
  - Packet line 66:  6. Clean + pushed worktrees: git -C "$KY_SOURCE_REPO" worktree remove <path> (no --force, no rm -rf), worktree prune: removed | remove_failed. Then bash F/local_db.sh close --session <id> per session_id in R/local_db/*.json (none: once, its own session name).
  - Packet line 80: **Do not.** Rebase or force-push; read credentials; touch production or docker. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 40: PID/PGID + process-start identity; write `$KY_RUN/DRAIN_RECEIPT.json` from measured drain — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 43: "$KY_RUN/DRAIN_RECEIPT.json"`. Remove eligible owned item worktrees and session DBs; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 44: write `$KY_RUN/FINAL_RECEIPT.json` binding the accepted drain digest, close-report — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 49: --artifact-path "$KY_RUN/FINAL_RECEIPT.json"`. The tracker stays available throughout. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 57: **Contract.** R = $KY_RUN, F = $KY_FLEET, ky = $KY_ROOT/bin/ky. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 58: - bash finalize.sh (an argument → exit 64). Run by executor.py execute() (op finalize) as ["bash", <temporary copy>], cwd $KY_ROOT, env = its CHILD_ENV_ALLOW + SE_EPHE_PATH + KY_ROOT only, 21600 s: no dirname "$0"; R, F default from $KY_ROOT; KY_SCRATCH, KY_SOURCE_REPO as kyctl.sh l.65–67. Exit 0 only after C-4's guarded completion, else 1. KY_* knobs kept. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 63:  3. Each worktree (never $KY_SOURCE_REPO): absent | clean | dirty_kept | unpushed_kept | busy_kept. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 66:  6. Clean + pushed worktrees: git -C "$KY_SOURCE_REPO" worktree remove <path> (no --force, no rm -rf), worktree prune: removed | remove_failed. Then bash F/local_db.sh close --session <id> per session_id in R/local_db/*.json (none: once, its own session name). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 80: **Do not.** Rebase or force-push; read credentials; touch production or docker. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-INSTALL_v1.md`

- References/stamp changed: false; bytes: 8993.
- Packet digest after: `05b73c1802c4c76d990dcb2f74d3c2dfe69afa6f139693a291de21d57e342340`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 47:   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, created in B-2
  - Packet line 50: **Contract.** ROOT = `--root`, default `$KY_ROOT`; R = `ROOT/run`; F = `ROOT/fleet_live`; (I) = INTERPRETATION.
  - Packet line 52: - B-2 only (I): ROOT = `/Users/Dev/kalayantra` needs `--action ID`, an INTENDED kyaction record of kind `install` binding M's sha256 and S's commit; it completes or fails it. Fail closed (ruling P29): any other ROOT → exit 1 unless `KY_LAUNCHAGENTS_DIR`, `KY_LAUNCHCTL`, `KY_CAMPAIGN_CHECKOUT` (step 5's path) and `PRAVAHA_URL` are each given explicitly, none equal to its real default. Ruling P39: both are decided FIRST, before M, S or any path under ROOT (STOP files included) is read or written, each with its stderr code `E_ACTION`, `E_UNSET <VAR>` or `E_REAL <VAR>`; its test passes an M and S that cannot verify, HOME = the pytest base, and asserts the code.
  - Packet line 65:   6. Tracker: write `${KY_LAUNCHAGENTS_DIR:-~/Library/LaunchAgents}/com.madhav.kalayantra.tracker.plist` (install_tracker.sh's block + `F` on PYTHONPATH, step 5's checkout); restart it (`${KY_LAUNCHCTL:-/bin/launchctl}`): `/api/health` ok, no `model_error`, process started after the swap (I). Then, before any receipt: publish `STAGED_MODEL_ACTIONS_v2_2.json` with the installed `ky` — `decide <D> --outcome refused --as steward --delegated --detail …`, `park <item> --as steward --detail …`, `block KV3-SCHEMA-1 --as steward --detail …`; once each (an existing event is skipped, reported).
  - Packet line 80: **Do not.** Rebase or force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 47:   `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`, created in B-2 — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 50: **Contract.** ROOT = `--root`, default `$KY_ROOT`; R = `ROOT/run`; F = `ROOT/fleet_live`; (I) = INTERPRETATION. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 52: - B-2 only (I): ROOT = `/Users/Dev/kalayantra` needs `--action ID`, an INTENDED kyaction record of kind `install` binding M's sha256 and S's commit; it completes or fails it. Fail closed (ruling P29): any other ROOT → exit 1 unless `KY_LAUNCHAGENTS_DIR`, `KY_LAUNCHCTL`, `KY_CAMPAIGN_CHECKOUT` (step 5's path) and `PRAVAHA_URL` are each given explicitly, none equal to its real default. Ruling P39: both are decided FIRST, before M, S or any path under ROOT (STOP files included) is read or written, each with its stderr code `E_ACTION`, `E_UNSET <VAR>` or `E_REAL <VAR>`; its test passes an M and S that cannot verify, HOME = the pytest base, and asserts the code. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 65:   6. Tracker: write `${KY_LAUNCHAGENTS_DIR:-~/Library/LaunchAgents}/com.madhav.kalayantra.tracker.plist` (install_tracker.sh's block + `F` on PYTHONPATH, step 5's checkout); restart it (`${KY_LAUNCHCTL:-/bin/launchctl}`): `/api/health` ok, no `model_error`, process started after the swap (I). Then, before any receipt: publish `STAGED_MODEL_ACTIONS_v2_2.json` with the installed `ky` — `decide <D> --outcome refused --as steward --delegated --detail …`, `park <item> --as steward --detail …`, `block KV3-SCHEMA-1 --as steward --detail …`; once each (an existing event is skipped, reported). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 80: **Do not.** Rebase or force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYALLOC_v1.md`

- References/stamp changed: false; bytes: 8745.
- Packet digest after: `4bee0b80d8386ae3134cae2fe840a13df916c69dc5b608e555ac30f782e5e370`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 59: **Contract.** `python3 -I -B kyalloc.py <verb> …`. Env `KY_RUN` (default `${KY_ROOT:-/Users/Dev/kalayantra}/run`). git = `${KY_GIT:-/usr/bin/git}`, read-only verbs only (`rev-parse`, `ls-tree`, `show`); never a fetch, push or commit; writes only under `$KY_RUN/alloc/`.
  - Packet line 60: The one authority: `$KY_RUN/alloc/migrations.json` = `{"schema": "ky.alloc/1", "reservations": [{"item", "branch", "numbers": [int], "status": "active" | "consumed" | "released" | "conflicted", "reserved_at", "observed": {"ref", "ref_commit", "disk_max", "claims_max", "claims_blob"}, "conflict": null | {"number", "with"}}]}`. Every mutation: exclusive `flock` on `$KY_RUN/alloc/.lock`, the store re-read inside the lock, written as temp + fsync + rename, then one line appended to `$KY_RUN/alloc/journal.jsonl`. An unreadable store is never rewritten from empty.
  - Packet line 85: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, a database, the network (other than your branch's push and PR), the tracker, the plan, cards, schemas or other packets; create or number a real migration. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 59: **Contract.** `python3 -I -B kyalloc.py <verb> …`. Env `KY_RUN` (default `${KY_ROOT:-/Users/Dev/kalayantra}/run`). git = `${KY_GIT:-/usr/bin/git}`, read-only verbs only (`rev-parse`, `ls-tree`, `show`); never a fetch, push or commit; writes only under `$KY_RUN/alloc/`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 60: The one authority: `$KY_RUN/alloc/migrations.json` = `{"schema": "ky.alloc/1", "reservations": [{"item", "branch", "numbers": [int], "status": "active" | "consumed" | "released" | "conflicted", "reserved_at", "observed": {"ref", "ref_commit", "disk_max", "claims_max", "claims_blob"}, "conflict": null | {"number", "with"}}]}`. Every mutation: exclusive `flock` on `$KY_RUN/alloc/.lock`, the store re-read inside the lock, written as temp + fsync + rename, then one line appended to `$KY_RUN/alloc/journal.jsonl`. An unreadable store is never rewritten from empty. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 85: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, a database, the network (other than your branch's push and PR), the tracker, the plan, cards, schemas or other packets; create or number a real migration. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYBOUNDARY_v1.md`

- References/stamp changed: false; bytes: 8997.
- Packet digest after: `c8499dd72ad0a9114ff19a01a1316ea7fdb3a6d1de33691a8f8ba3a356e80310`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 24: "a write under $KY_RUN, $KY_FLEET, $KY_ROOT/bin, the item worktree or another job's scratch: each fails",
  - Packet line 54: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 58: **Contract.** F = `$KY_FLEET`, S = `job_scratch`. Read only from the state: `worktree`, `head`, `slot`, `job_scratch`, `tmp_path`.
  - Packet line 72: **Acceptance.** `acceptance.command`. The plan's fixtures, each a command a Bash tool would run inside `exec`, each asserting that it failed AND the bytes are unchanged (hash) AND `check` exits 0: the three attack classes of the negative cases plus writes to `~/Library/LaunchAgents`. Ruling P28: every attack target is a stand-in under the pytest base (temporary KY roots, HOME redirected there); the suite refuses to run when a target resolves outside it; the control never touches a real path. Detector controls (no result may be a proxy): with the boundary disabled the same attacks succeed and `check` exits 1; the chmod-only view is defeated. Positive: writes to S, a cache directory and `TMPDIR`, a loopback TCP connection, `git log`, `git diff` and reading every tracked file all work. Timeout: a fake program starts `sleep 600` and ignores TERM inside `exec`; a test supervisor sends TERM then KILL to the group and observes `killpg(pgid, 0)` → ESRCH and the child gone by pid and start identity. A fixture that cannot run on this host is `unknown`: acceptance fails.
  - Packet line 74: **Evidence.** `$JOB_SCRATCH/result.json` (BS-16), the chosen mechanism and each candidate's fixture results in `notes`. **Branch and PR.** `kalayantra/kv3-b-kyboundary`; one PR to main "KĀLA-YANTRA v3 KV3-B-KYBOUNDARY: verifier boundary"; never merged by the job. **Do not.** Run the real `claude`; leave a mount, image or view behind; force-push. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 24: "a write under $KY_RUN, $KY_FLEET, $KY_ROOT/bin, the item worktree or another job's scratch: each fails", — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 54: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 58: **Contract.** F = `$KY_FLEET`, S = `job_scratch`. Read only from the state: `worktree`, `head`, `slot`, `job_scratch`, `tmp_path`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 72: **Acceptance.** `acceptance.command`. The plan's fixtures, each a command a Bash tool would run inside `exec`, each asserting that it failed AND the bytes are unchanged (hash) AND `check` exits 0: the three attack classes of the negative cases plus writes to `~/Library/LaunchAgents`. Ruling P28: every attack target is a stand-in under the pytest base (temporary KY roots, HOME redirected there); the suite refuses to run when a target resolves outside it; the control never touches a real path. Detector controls (no result may be a proxy): with the boundary disabled the same attacks succeed and `check` exits 1; the chmod-only view is defeated. Positive: writes to S, a cache directory and `TMPDIR`, a loopback TCP connection, `git log`, `git diff` and reading every tracked file all work. Timeout: a fake program starts `sleep 600` and ignores TERM inside `exec`; a test supervisor sends TERM then KILL to the group and observes `killpg(pgid, 0)` → ESRCH and the child gone by pid and start identity. A fixture that cannot run on this host is `unknown`: acceptance fails. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 74: **Evidence.** `$JOB_SCRATCH/result.json` (BS-16), the chosen mechanism and each candidate's fixture results in `notes`. **Branch and PR.** `kalayantra/kv3-b-kyboundary`; one PR to main "KĀLA-YANTRA v3 KV3-B-KYBOUNDARY: verifier boundary"; never merged by the job. **Do not.** Run the real `claude`; leave a mount, image or view behind; force-push. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYDADMIT_v1.md`

- References/stamp changed: false; bytes: 8998.
- Packet digest after: `ddedd7276b8c73682f6dff6d1ac3a6818abeae17d13d2b089095fb2277a859ec`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 65: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 77:   - launch (model runners; I): $KY_RUN/QUALIFICATIONS/<role>-<model>.json (claude-sonnet-5-5 for tier sonnet, else claude-opus-5-5) is PASS, context launchd; facts.launch = the launch keys model … disallowed_tools: from its binds (extra_flags), but deadline (now + deadline_seconds), mcp_config (fleet/mcp.none.json, or mcp.marsys-only.json for chart data; the bound sha256); max_turns > 0, ≤ the kind's §7 cap (ARTIFACT 60, SURROGATE 30, MODEL and REQUEST-PREP 300).
  - Packet line 79:   - slot_not_ready, slot_foreign (KU-02): $KY_RUN/local_db/<slot>.json is READY, three seed hashes, session_id = controller_id, and bash fleet/local_db.sh check <slot> exits 0 now.
  - Packet line 82: - admit(ctx, job), after kyd_jobs.open: worktree, for a job holding item.<item> (registered, on the job's branch, that lock owned by controller_id); then (BUILD, feature packet; §8.6): missing test_commits[] files added and committed; KY_ITEM=<item> TESTS=<paths> bash fleet/precheck.sh --item in the worktree: 0 → already_green (refused; ARTIFACT: KV3-B-KYDKINDS-BUILD), 1 with expected_failing_assertion in the output → expected_red, else unclassified (refused) (I); $KY_RUN/admission/<item>.json = {item, base_sha, test_digests, result}.
  - Packet line 88: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydadmit; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDADMIT: kyd_admit.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky, gh, docker or a database; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 65: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 77:   - launch (model runners; I): $KY_RUN/QUALIFICATIONS/<role>-<model>.json (claude-sonnet-5-5 for tier sonnet, else claude-opus-5-5) is PASS, context launchd; facts.launch = the launch keys model … disallowed_tools: from its binds (extra_flags), but deadline (now + deadline_seconds), mcp_config (fleet/mcp.none.json, or mcp.marsys-only.json for chart data; the bound sha256); max_turns > 0, ≤ the kind's §7 cap (ARTIFACT 60, SURROGATE 30, MODEL and REQUEST-PREP 300). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 79:   - slot_not_ready, slot_foreign (KU-02): $KY_RUN/local_db/<slot>.json is READY, three seed hashes, session_id = controller_id, and bash fleet/local_db.sh check <slot> exits 0 now. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 82: - admit(ctx, job), after kyd_jobs.open: worktree, for a job holding item.<item> (registered, on the job's branch, that lock owned by controller_id); then (BUILD, feature packet; §8.6): missing test_commits[] files added and committed; KY_ITEM=<item> TESTS=<paths> bash fleet/precheck.sh --item in the worktree: 0 → already_green (refused; ARTIFACT: KV3-B-KYDKINDS-BUILD), 1 with expected_failing_assertion in the output → expected_red, else unclassified (refused) (I); $KY_RUN/admission/<item>.json = {item, base_sha, test_digests, result}. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 88: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydadmit; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDADMIT: kyd_admit.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky, gh, docker or a database; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYDISPATCH_v1.md`

- References/stamp changed: false; bytes: 8939.
- Packet digest after: `6fd3308a7758edf0f8614e3040ba664c51e37a6cdc345e87d8c35aea05c2dd4f`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 36: `$KY_FLEET/kydispatch.py` (launchd `KeepAlive`, 30 s tick); atomic instance lock via
  - Packet line 42: **Precedence each tick:** `run/STOP_dispatcher` → exit. `$KY_ROOT/HOLD` → no admissions
  - Packet line 69: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`): the engine reads and writes it only through kyd_jobs, whose packet pins the keys, and reads job state only through kyd_jobs' return values (`outcome`: `done | blocked | failed | interrupted | timed_out | refused`).
  - Packet line 71: **Contract.** `/opt/homebrew/bin/python3 -u $KY_FLEET/kydispatch.py` · `--once`, `--dry`: one tick (`--dry`: no lock, read-only; stdout `{"schema": "ky.dispatch_plan/1", "jobs": [{kind, item, key, pool, decision}]}`; decision (I): `launch`, `park`, `refused:<code of the refusing step>` or `wait:<hold|gate|backoff|slot|stale>`). Exit 0 clean stop · 75 no lock · 78 a credential variable name set · 64 usage. Modules: its directory; scripts: $KY_FLEET.
  - Packet line 73: Loop file $KY_RUN/loops/dispatcher.json (kyloop.py's loop_state, update_loop_state; enabled is kyloop.py admin's): last_iteration_at, controller{id, pid}, waiting, log_path; its own backoff, tracker, priority.
  - Packet line 79: 5. Freshness (I): `ky next --json` has an integer version (none in the snapshot fallback) above the last tick's, or equal with $KY_RUN/EVENTS.jsonl unchanged (size, sha256); else ctx.next is None.
  - Packet line 84: Capacity: N, M = integers 1–8 in $KY_RUN/KY_WORKERS, $KY_RUN/KY_VERIFIERS (kyveto.py's; maxima 8 (I): owner direction of 2026-10-12, recorded in PLANNER_STATE active.owner_directions_20261012; not yet in the owner decisions file); absent → 6, 4; unreadable → 0. limits.copies = 10 (I). Ready work above a maximum → ctx.awaiting("capacity-above-max", …).
  - Packet line 86: Messaging: journal appends to $KY_RUN/JOURNAL_DISPATCHER.md; for the quoted events also `bash fleet/kynotify.sh "<text>" --level …` inside act, once per changed condition. awaiting writes a ky.awaiting/1 item.
  - Packet line 89: - repo: $KY_SOURCE_REPO, else the plan §5 campaign checkout; model: the plan model's absolute path in repo; now(): UTC.
  - Packet line 91: - events(item): its lines of $KY_RUN/EVENTS.jsonl.
  - Packet line 94: - accepted = kyd_kinds_land.accepted_head; priority: owner priority commands, then $KY_RUN/PRIORITY.txt.
  - Packet line 100: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydispatch; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDISPATCH: kydispatch.py"; never merged by the job. **Do not.** Edit outside `d1_paths`; run the real `claude`, `ky` or `gh`; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 36: `$KY_FLEET/kydispatch.py` (launchd `KeepAlive`, 30 s tick); atomic instance lock via — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 42: **Precedence each tick:** `run/STOP_dispatcher` → exit. `$KY_ROOT/HOLD` → no admissions — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 69: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`): the engine reads and writes it only through kyd_jobs, whose packet pins the keys, and reads job state only through kyd_jobs' return values (`outcome`: `done | blocked | failed | interrupted | timed_out | refused`). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 71: **Contract.** `/opt/homebrew/bin/python3 -u $KY_FLEET/kydispatch.py` · `--once`, `--dry`: one tick (`--dry`: no lock, read-only; stdout `{"schema": "ky.dispatch_plan/1", "jobs": [{kind, item, key, pool, decision}]}`; decision (I): `launch`, `park`, `refused:<code of the refusing step>` or `wait:<hold|gate|backoff|slot|stale>`). Exit 0 clean stop · 75 no lock · 78 a credential variable name set · 64 usage. Modules: its directory; scripts: $KY_FLEET. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 73: Loop file $KY_RUN/loops/dispatcher.json (kyloop.py's loop_state, update_loop_state; enabled is kyloop.py admin's): last_iteration_at, controller{id, pid}, waiting, log_path; its own backoff, tracker, priority. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 79: 5. Freshness (I): `ky next --json` has an integer version (none in the snapshot fallback) above the last tick's, or equal with $KY_RUN/EVENTS.jsonl unchanged (size, sha256); else ctx.next is None. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 84: Capacity: N, M = integers 1–8 in $KY_RUN/KY_WORKERS, $KY_RUN/KY_VERIFIERS (kyveto.py's; maxima 8 (I): owner direction of 2026-10-12, recorded in PLANNER_STATE active.owner_directions_20261012; not yet in the owner decisions file); absent → 6, 4; unreadable → 0. limits.copies = 10 (I). Ready work above a maximum → ctx.awaiting("capacity-above-max", …). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 86: Messaging: journal appends to $KY_RUN/JOURNAL_DISPATCHER.md; for the quoted events also `bash fleet/kynotify.sh "<text>" --level …` inside act, once per changed condition. awaiting writes a ky.awaiting/1 item. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 89: - repo: $KY_SOURCE_REPO, else the plan §5 campaign checkout; model: the plan model's absolute path in repo; now(): UTC. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 91: - events(item): its lines of $KY_RUN/EVENTS.jsonl. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 94: - accepted = kyd_kinds_land.accepted_head; priority: owner priority commands, then $KY_RUN/PRIORITY.txt. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 100: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydispatch; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDISPATCH: kydispatch.py"; never merged by the job. **Do not.** Edit outside `d1_paths`; run the real `claude`, `ky` or `gh`; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYDJOBS_v1.md`

- References/stamp changed: false; bytes: 8999.
- Packet digest after: `f49bd7a43abad08112dd3d7fb0d91acf6845bebd9cdbf4b43cd0662998a06a1b`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 36: each job records `JOB_SCRATCH=$KY_SCRATCH/jobs/$JOB_ID`
  - Packet line 70: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 81: - attempts(ctx, intent) -> {attempt, blocked} from $KY_RUN/jobs/failures.json {item: {failure_fp: {count, evidence_fp}}} (never reset; quota not counted): blocked at count ≥ 3 with an unchanged evidence_fp (I), or after two interrupted jobs of the key.
  - Packet line 82: - open(ctx, intent, slot, facts) -> a prepared job, or None with all undone: lock job.<key> (kyaction.acquire_lock), then a fresh look ($KY_RUN/handled/job.<key>.json, or a job of that key or slot not ended -> None); locks[]; claim: ky claim <item> --worker <slot> --lease 10800, claim_id from stdout; worktree: with item.<item> in locks[], /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item, lower case> on branch kalayantra/<same> (I), added at facts.base_sha if absent; else repo; facts.migration not null: python3 fleet/kyalloc.py reserve --item I --branch B --repo R -> numbers[0]; scratch/jobs/<job_id>/ with prompt.md, stdout.jsonl, stderr.log, tmp/; prompt = card bytes, packet bytes, the line `--- job header ---`, one JSON object (the §7 header fields, header); facts.launch -> model … disallowed_tools, the other facts -> their keys; verifier pool -> boundary verifier.
  - Packet line 92: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydjobs; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDJOBS: kyd_jobs.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real claude, ky, gh or a database; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 36: each job records `JOB_SCRATCH=$KY_SCRATCH/jobs/$JOB_ID` — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 70: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 81: - attempts(ctx, intent) -> {attempt, blocked} from $KY_RUN/jobs/failures.json {item: {failure_fp: {count, evidence_fp}}} (never reset; quota not counted): blocked at count ≥ 3 with an unchanged evidence_fp (I), or after two interrupted jobs of the key. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 82: - open(ctx, intent, slot, facts) -> a prepared job, or None with all undone: lock job.<key> (kyaction.acquire_lock), then a fresh look ($KY_RUN/handled/job.<key>.json, or a job of that key or slot not ended -> None); locks[]; claim: ky claim <item> --worker <slot> --lease 10800, claim_id from stdout; worktree: with item.<item> in locks[], /Users/Dev/worktrees.noindex/madhav/claude/kalayantra-<item, lower case> on branch kalayantra/<same> (I), added at facts.base_sha if absent; else repo; facts.migration not null: python3 fleet/kyalloc.py reserve --item I --branch B --repo R -> numbers[0]; scratch/jobs/<job_id>/ with prompt.md, stdout.jsonl, stderr.log, tmp/; prompt = card bytes, packet bytes, the line `--- job header ---`, one JSON object (the §7 header fields, header); facts.launch -> model … disallowed_tools, the other facts -> their keys; verifier pool -> boundary verifier. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 92: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydjobs; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDJOBS: kyd_jobs.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real claude, ky, gh or a database; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYDKINDS-BUILD_v1.md`

- References/stamp changed: false; bytes: 8996.
- Packet digest after: `23a35aafdbeb3ae833a3afa850f465f8161cda5cb4e2ea14114cd2e30d589d6c`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 52: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 60: - BUILD: ready K items in `ctx.priority` order (absent from it: none), `ctx.pr` None; lock `item.<item>`, card `fleet/cards/KARAKA.md`, packet `repo/00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md` (highest n). `$KY_RUN/admission/<item>.json` saying `already_green`: no BUILD, but an ARTIFACT intent (`header.assessment` `already_satisfied`).
  - Packet line 63: - STEP (script): an unrecorded step with `ctx.verify(item, step)` True (null detector: none; ruling P18); `start` writes it to `$KY_RUN/jobs/<job_id>/step.json`, the row's `--evidence`.
  - Packet line 73: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydkinds-build; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-BUILD: kyd_kinds_build.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky or gh; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 52: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 60: - BUILD: ready K items in `ctx.priority` order (absent from it: none), `ctx.pr` None; lock `item.<item>`, card `fleet/cards/KARAKA.md`, packet `repo/00_ARCHITECTURE/briefs/kalayantra/packets/PACKET_<ID>_v<n>.md` (highest n). `$KY_RUN/admission/<item>.json` saying `already_green`: no BUILD, but an ARTIFACT intent (`header.assessment` `already_satisfied`). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 63: - STEP (script): an unrecorded step with `ctx.verify(item, step)` True (null detector: none; ruling P18); `start` writes it to `$KY_RUN/jobs/<job_id>/step.json`, the row's `--evidence`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 73: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydkinds-build; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-BUILD: kyd_kinds_build.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky or gh; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYDKINDS-LAND_v1.md`

- References/stamp changed: false; bytes: 8997.
- Packet digest after: `3486423dbfcbe0acce9545840ec7dfd97dbd6ac02fc403f906dab49ae874b20d`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 49: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 60: - `park`, for a `queue` intent under `HOLD_MERGES` (owner decision D-6 revised) in place of admission: `$KY_RUN/merge_requests/<item>.json` `{schema: "ky.merge_request/1", item, pr, registered_head, recorded_at}`; no GitHub call. After the hold a parked request waits for the surrogate (I; D-5): `ctx.awaiting("merge-<item>", …)`, then an EFFECTIVE or EXECUTED decision for that id in `$KY_RUN/DECISIONS_SURROGATE.jsonl`, the parked head still `pr.head`.
  - Packet line 67: **Evidence.** `$JOB_SCRATCH/result.json`. **Branch and PR.** `kalayantra/kv3-b-kydkinds-land`; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-LAND: kyd_kinds_land.py"; never merged by the job. **Do not.** Edit outside `d1_paths`; run the real `ky` or `gh`; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 49: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 60: - `park`, for a `queue` intent under `HOLD_MERGES` (owner decision D-6 revised) in place of admission: `$KY_RUN/merge_requests/<item>.json` `{schema: "ky.merge_request/1", item, pr, registered_head, recorded_at}`; no GitHub call. After the hold a parked request waits for the surrogate (I; D-5): `ctx.awaiting("merge-<item>", …)`, then an EFFECTIVE or EXECUTED decision for that id in `$KY_RUN/DECISIONS_SURROGATE.jsonl`, the parked head still `pr.head`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 67: **Evidence.** `$JOB_SCRATCH/result.json`. **Branch and PR.** `kalayantra/kv3-b-kydkinds-land`; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-LAND: kyd_kinds_land.py"; never merged by the job. **Do not.** Edit outside `d1_paths`; run the real `ky` or `gh`; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYDKINDS-OPS_v1.md`

- References/stamp changed: false; bytes: 8999.
- Packet digest after: `28f5a7b966d8eeb83f274a313881620da3e3298df397e1fbf14cd0c9e0961d09`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 50: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 58: - REQUEST-PREP: a ready N-owned operation item with no $KY_RUN/ops/prepared/<operation_id>.json (I). script: the request executor.py validate accepts, from brief.op and the table at origin/main; an underivable field → a model job.
  - Packet line 59: - PRE-ACCEPT: a prepared request without acceptance. The job proposes $JOB_SCRATCH/acceptance.json; finish, after `bash fleet/kyboundary.sh check <job_id>` exits 0, the request digest unchanged, writes `$KY_RUN/ops/acceptance/<operation_id>.json` (`by` = the slot) through act (I).
  - Packet line 60: - EXECUTE (script): an acceptance matching the prepared request's digest → act writes `$KY_RUN/ops/requests/<operation_id>.json` (the request plus acceptance_receipt); never starts executor.py, holds no credential, dispatches no workflow (I). A receipt not COMPLETED → ctx.awaiting, no resubmission.
  - Packet line 63: - RULING: one job per message of `ky inbox --stream N --json` (a list with msg_id); lock `msg.<msg_id>`; done once acked, then `$KY_RUN/handled/msg.<msg_id>.json`.
  - Packet line 64: - SURROGATE: per `$KY_RUN/awaiting/<id>.json` (not `*.owner_decision.json`). Fingerprint (I): sha256 of canonical `{id, item, question, options, evidence, each evidence file's sha256}`. No intent while `$KY_RUN/handled/awaiting.<id>.json` carries it; lock `awaiting.<id>`; start reads that record again under the lock; finish writes it from the job's line in $KY_RUN/DECISIONS_SURROGATE.jsonl; a hard stop → journal `hard stop`. No `ky decide` here. Once kyveto.status() shows the decision EXECUTED, VETOED or FAILED, a script intent moves the item to awaiting/done/.
  - Packet line 65: - PLAN: a non-empty $KY_RUN/REPACKET.txt, or, as the wave boundary (I), open items, none ready or `running` with an admitted packet.
  - Packet line 71: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydkinds-ops; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-OPS: kyd_kinds_ops.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky, gh or executor; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 50: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 58: - REQUEST-PREP: a ready N-owned operation item with no $KY_RUN/ops/prepared/<operation_id>.json (I). script: the request executor.py validate accepts, from brief.op and the table at origin/main; an underivable field → a model job. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 59: - PRE-ACCEPT: a prepared request without acceptance. The job proposes $JOB_SCRATCH/acceptance.json; finish, after `bash fleet/kyboundary.sh check <job_id>` exits 0, the request digest unchanged, writes `$KY_RUN/ops/acceptance/<operation_id>.json` (`by` = the slot) through act (I). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 60: - EXECUTE (script): an acceptance matching the prepared request's digest → act writes `$KY_RUN/ops/requests/<operation_id>.json` (the request plus acceptance_receipt); never starts executor.py, holds no credential, dispatches no workflow (I). A receipt not COMPLETED → ctx.awaiting, no resubmission. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 63: - RULING: one job per message of `ky inbox --stream N --json` (a list with msg_id); lock `msg.<msg_id>`; done once acked, then `$KY_RUN/handled/msg.<msg_id>.json`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 64: - SURROGATE: per `$KY_RUN/awaiting/<id>.json` (not `*.owner_decision.json`). Fingerprint (I): sha256 of canonical `{id, item, question, options, evidence, each evidence file's sha256}`. No intent while `$KY_RUN/handled/awaiting.<id>.json` carries it; lock `awaiting.<id>`; start reads that record again under the lock; finish writes it from the job's line in $KY_RUN/DECISIONS_SURROGATE.jsonl; a hard stop → journal `hard stop`. No `ky decide` here. Once kyveto.status() shows the decision EXECUTED, VETOED or FAILED, a script intent moves the item to awaiting/done/. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 65: - PLAN: a non-empty $KY_RUN/REPACKET.txt, or, as the wave boundary (I), open items, none ready or `running` with an admitted packet. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 71: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kydkinds-ops; one PR to main "KĀLA-YANTRA v3 KV3-B-KYDKINDS-OPS: kyd_kinds_ops.py"; never merged by the job. **Do not.** Edit outside d1_paths; run the real ky, gh or executor; force-push; read credentials. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYGATE_v1.md`

- References/stamp changed: false; bytes: 8998.
- Packet digest after: `1ab7c986ef52bdb5d00c57b8d450e827d91e0a209abbff0c6bfcaf0e48d80555`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 70: - R1 `python3 -I -B "$KY_FLEET/kyschema.py" validate "$KY_FLEET/schemas/release_receipt.json" "$KY_RUN/RELEASE_RECEIPT.json"` exits 0.
  - Packet line 73: - R4 locally observable: `coordination_commit` and `main_commit` are commits in `$KY_SOURCE_REPO`, `main_commit` is contained in `origin/main`, PR numbers are unique; git not answering is WAIT. The other evidence fields are bound by R2, not re-observed: printed as `unobserved=<fields>`.
  - Packet line 74: - A, final Wave B acceptance (receipt and manifest fields as KV3-B-KYVERSION names them; ruling P6: a missing one is WAIT, never a guess): A1 `mode == "final"` (`bootstrap_only_installation`); A2 VERSIONS.json's recomputed digest == its `manifest_sha256` == the receipt's `manifest.manifest_sha256` (`changed_final_manifest`); A3 `rehearsal.results` names a file with its sha256 (`absent_rehearsal`); A4 `rehearsal.tested_components` == the manifest's `components` (`stale_tested_hashes`); A5 `coverage.verdict == "ACCEPTED"`, its file has its sha256, `packets[]` is non-empty (`missing_coverage`); A6 `backfill.validated == true`; A7 `/bin/bash "$KY_FLEET/kyversion.sh"` (pre-resume), or the same with `--expected-manifest-digest <approved_bundle_digest>` (full), exits 0 within 300 s; missing, non-zero or timed out is `final_acceptance_unverified`.
  - Packet line 75: - H `$KY_ROOT/HOLD` is absent (`global_hold`). Ruling P7 (INTERPRETATION): `$KY_RUN/HOLD_MERGES` never closes the gate (it blocks queue submission); only printed.
  - Packet line 76: - N `$KY_RUN/OWNER_RESUME.json`: `binding == "N-467"`; `release_receipt_digest` == R2's digest (`stale_resume`); `approved_bundle_digest` == A2's digest; `decided_by {kind: "owner" | "surrogate_decision", id}`; `ts` (UTC). Each missing field is its own reason. (`binding`, `approved_bundle_digest`: as kyloop.py and test_kyctl.py; the other three names: INTERPRETATION.)
  - Packet line 87: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the plan, cards, schemas or other packets; write a resume record or remove a hold outside a test's temp directory. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 70: - R1 `python3 -I -B "$KY_FLEET/kyschema.py" validate "$KY_FLEET/schemas/release_receipt.json" "$KY_RUN/RELEASE_RECEIPT.json"` exits 0. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 73: - R4 locally observable: `coordination_commit` and `main_commit` are commits in `$KY_SOURCE_REPO`, `main_commit` is contained in `origin/main`, PR numbers are unique; git not answering is WAIT. The other evidence fields are bound by R2, not re-observed: printed as `unobserved=<fields>`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 74: - A, final Wave B acceptance (receipt and manifest fields as KV3-B-KYVERSION names them; ruling P6: a missing one is WAIT, never a guess): A1 `mode == "final"` (`bootstrap_only_installation`); A2 VERSIONS.json's recomputed digest == its `manifest_sha256` == the receipt's `manifest.manifest_sha256` (`changed_final_manifest`); A3 `rehearsal.results` names a file with its sha256 (`absent_rehearsal`); A4 `rehearsal.tested_components` == the manifest's `components` (`stale_tested_hashes`); A5 `coverage.verdict == "ACCEPTED"`, its file has its sha256, `packets[]` is non-empty (`missing_coverage`); A6 `backfill.validated == true`; A7 `/bin/bash "$KY_FLEET/kyversion.sh"` (pre-resume), or the same with `--expected-manifest-digest <approved_bundle_digest>` (full), exits 0 within 300 s; missing, non-zero or timed out is `final_acceptance_unverified`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 75: - H `$KY_ROOT/HOLD` is absent (`global_hold`). Ruling P7 (INTERPRETATION): `$KY_RUN/HOLD_MERGES` never closes the gate (it blocks queue submission); only printed. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 76: - N `$KY_RUN/OWNER_RESUME.json`: `binding == "N-467"`; `release_receipt_digest` == R2's digest (`stale_resume`); `approved_bundle_digest` == A2's digest; `decided_by {kind: "owner" | "surrogate_decision", id}`; `ts` (UTC). Each missing field is its own reason. (`binding`, `approved_bundle_digest`: as kyloop.py and test_kyctl.py; the other three names: INTERPRETATION.) — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 87: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the plan, cards, schemas or other packets; write a resume record or remove a hold outside a test's temp directory. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYJOB-ENGINES_v1.md`

- References/stamp changed: true; bytes: 8836.
- Packet digest after: `d07f1423e77e937594721a64c69cd4cbc289689f8f17afa8d946cf64984258d4`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 38: **Pins.** Plan v2.7 @ e709f60d7; base: job header. F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; E = `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-b0c-engines/` + F; S = `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3`; C = S + `/engines/launchers/cockpit`; R = S + `/reviews/b0c-engines`; P = `/Users/Dev/kalayantra/run/PLANNER_STATE.json`. E/C/R not runtime imports.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines/kyengine.py` — `4ba634ba17d0f903ae496aaf1396167ec84482ab963aff525c12e0bd4c3c3a8d`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines/kyfinish.py` — `a744b32b784faec24dd8968faf4f43f21692b54413a9fe90de767bb2ed9344fe`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines/result.json` — `a812696b55095bf960f55ad155a7608ef38d0cf4d40f0abbb9050a9c37371e70`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines/kyboot.py` — `e81ea4a79b9c7fe0c808604395b0407e1b242836c9c2abb4744e935a58144df8`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines/kyqualify.py` — `57d136fea6fd8166d9fcca057fc913d688d94dc9d994c37d20a60aa917644706`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines/job_result_launcher_commit.json` — `fd071415769b492b5a103ec51aea6d36955541415a2b6dae4c971ed8c1a01356`.
- Kept external references and why:
  - Packet line 38: **Pins.** Plan v2.7 @ e709f60d7; base: job header. F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; E = `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/engines`; C = E; R = E; P = `/Users/Dev/kalayantra/run/PLANNER_STATE.json` (controller evidence). E/C/R not runtime imports. — controller-supplied runtime evidence or output for cockpit promotion.

### `PACKET_KV3-B-KYJOB_v1.md`

- References/stamp changed: false; bytes: 8996.
- Packet digest after: `443bf430cbe0039bc172accd5f4d21d1539354958d430ca32da53911f527b083`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 22: "a credential variable name set, or a wrapper in $KY_ROOT/bin: exit 78, nothing launched",
  - Packet line 35: # all values from $KY_RUN/jobs/<job_id>/state.json; every path absolute
  - Packet line 37: exec env -i HOME="$HOME" PATH="$KY_ROOT/bin:$NODE_BIN:/opt/homebrew/bin:/usr/bin:/bin" \
  - Packet line 39:   ZDOTDIR="$KY_ROOT/zdotdir" KY_ROOT="$KY_ROOT" KY_RUN="$KY_RUN" KY_FLEET="$KY_FLEET" \
  - Packet line 40:   KY_STREAM="$STREAM" KY_LANE="$SLOT" KY_ITEM="$ITEM" KY_PY="$KY_ROOT/venv/bin/python" \
  - Packet line 45:     --output-format stream-json --verbose --add-dir "$KY_ROOT" \
  - Packet line 78: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null).
  - Packet line 84: **Contract.** R = $KY_RUN, F = $KY_FLEET, S = job_scratch.
  - Packet line 87: - Environment (I), extending the quoted line: KY_SCRATCH and JOB_SCRATCH (= S = $KY_SCRATCH/jobs/<job_id>), and KY_RUN_ID (= job_id), KY_ROLE (= role), KY_CONTROLLER_ID (= controller_id). Fixture runs add the validated PRAVAHA_* from fixture{}. Nothing else survives.
  - Packet line 90:   - 78: a name matching the quoted pattern in its own environment (names only); no_wrappers (as kalayantra_fleet.sh): a file in $KY_ROOT/bin other than ky, kybrief.
  - Packet line 100: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kyjob; one PR to main "KĀLA-YANTRA v3 KV3-B-KYJOB: kyjob.sh"; never merged by the job. **Do not.** Edit outside d1_paths; run the real claude; force-push; read credentials or print a variable's value. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 22: "a credential variable name set, or a wrapper in $KY_ROOT/bin: exit 78, nothing launched", — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 35: # all values from $KY_RUN/jobs/<job_id>/state.json; every path absolute — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 37: exec env -i HOME="$HOME" PATH="$KY_ROOT/bin:$NODE_BIN:/opt/homebrew/bin:/usr/bin:/bin" \ — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 39:   ZDOTDIR="$KY_ROOT/zdotdir" KY_ROOT="$KY_ROOT" KY_RUN="$KY_RUN" KY_FLEET="$KY_FLEET" \ — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 40:   KY_STREAM="$STREAM" KY_LANE="$SLOT" KY_ITEM="$ITEM" KY_PY="$KY_ROOT/venv/bin/python" \ — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 45:     --output-format stream-json --verbose --add-dir "$KY_ROOT" \ — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 78: **Job state.** `$KY_RUN/jobs/<job_id>/state.json` (`ky.job/1`; writers: `kyd_jobs.py`, finalize.sh; paths absolute; unset keys null). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 84: **Contract.** R = $KY_RUN, F = $KY_FLEET, S = job_scratch. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 87: - Environment (I), extending the quoted line: KY_SCRATCH and JOB_SCRATCH (= S = $KY_SCRATCH/jobs/<job_id>), and KY_RUN_ID (= job_id), KY_ROLE (= role), KY_CONTROLLER_ID (= controller_id). Fixture runs add the validated PRAVAHA_* from fixture{}. Nothing else survives. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 90:   - 78: a name matching the quoted pattern in its own environment (names only); no_wrappers (as kalayantra_fleet.sh): a file in $KY_ROOT/bin other than ky, kybrief. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 100: **Evidence.** $JOB_SCRATCH/result.json. **Branch and PR.** kalayantra/kv3-b-kyjob; one PR to main "KĀLA-YANTRA v3 KV3-B-KYJOB: kyjob.sh"; never merged by the job. **Do not.** Edit outside d1_paths; run the real claude; force-push; read credentials or print a variable's value. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYLOCK_v1.md`

- References/stamp changed: false; bytes: 8992.
- Packet digest after: `58d404dc12f009ba45f32938d9ab66dc4e5ee2befc619b9884e20326b91a9838`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 58: **Contract.** Env `KY_RUN` (default `${KY_ROOT:-/Users/Dev/kalayantra}/run`), `KY_FLEET` (default: the script's directory). Lock = directory `$KY_RUN/locks/<role>`, role `^[a-z][a-z0-9_]{0,31}$`; identity `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` and no `..`, else 70.
  - Packet line 63: - `release <role> <identity>`: the caller must be the recorded owner (id, holder pid, start), else 73. Then the KU-02 step `/bin/bash "$KY_FLEET/local_db.sh" close --session <identity>` (900 s; needs `KY_SCRATCH`). Only its exit 0 buries the lock (ruling P26): 0 `released`. Missing, non-zero or timed out: 74, lock KEPT, naming the session whose databases remain. A takeover never runs this step.
  - Packet line 66: Tests-only hook `KY_LOCK_PS` (absolute path replacing `/bin/ps`): the line ends `test_hook=ps`; refused when `KY_RUN` is `/Users/Dev/kalayantra/run`.
  - Packet line 84: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, a database, the tracker, the real `local_db.sh`. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time; signal-0 probes only.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 58: **Contract.** Env `KY_RUN` (default `${KY_ROOT:-/Users/Dev/kalayantra}/run`), `KY_FLEET` (default: the script's directory). Lock = directory `$KY_RUN/locks/<role>`, role `^[a-z][a-z0-9_]{0,31}$`; identity `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` and no `..`, else 70. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 63: - `release <role> <identity>`: the caller must be the recorded owner (id, holder pid, start), else 73. Then the KU-02 step `/bin/bash "$KY_FLEET/local_db.sh" close --session <identity>` (900 s; needs `KY_SCRATCH`). Only its exit 0 buries the lock (ruling P26): 0 `released`. Missing, non-zero or timed out: 74, lock KEPT, naming the session whose databases remain. A takeover never runs this step. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 66: Tests-only hook `KY_LOCK_PS` (absolute path replacing `/bin/ps`): the line ends `test_hook=ps`; refused when `KY_RUN` is `/Users/Dev/kalayantra/run`. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 84: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, a database, the tracker, the real `local_db.sh`. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time; signal-0 probes only. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYPACKET_v1.md`

- References/stamp changed: false; bytes: 8997.
- Packet digest after: `c1cb91d3bfd7807a90c4853d78ac0ab7e47c23a02596cd533cf6727258061752`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 94: **Do not.** Edit outside `d1_paths`; call a model or the network; rebase or force-push; touch credentials, production, the plan, cards, schemas, templates or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 94: **Do not.** Edit outside `d1_paths`; call a model or the network; rebase or force-push; touch credentials, production, the plan, cards, schemas, templates or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYREGEN_v1.md`

- References/stamp changed: false; bytes: 8993.
- Packet digest after: `84bf40dc22d11470095934b11ffe8e140b13e582ff95e1e8161a621b05afed77`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 60: **Contract.** `kyregen.sh <job_id>` — INTERPRETATION: the §7 convention of `kyjob.sh <job_id>` (all values from `$KY_RUN/jobs/<job_id>/state.json`, every path absolute). Env: `KY_ROOT`, `KY_RUN`, `KY_FLEET`; `KY_RUN_ID`, `KY_ROLE`, `KY_CONTROLLER_ID` (action records); git = `${KY_GIT:-/usr/bin/git}`; tracker CLI = `${KY_BIN:-$KY_ROOT/bin/ky}`.
  - Packet line 63: 1. Preconditions (else 73): `queue_authorised` is false; worktree HEAD == `registered_head`; `git status --porcelain` is empty; `base_sha` is not yet contained in HEAD; `$KY_RUN/locks/item.<item>/owner.json` names a live owner that is this process or an ancestor (liveness as kyaction.py `process_matches`; unknown refuses) — INTERPRETATION: the dispatcher holds the plan's item lock, kyregen takes none; sha256 of `generator.path` == `generator.sha256`, else 4 (pinned generator).
  - Packet line 68: 6. Push, never forced, inside an action record `JOB-$KY_RUN_ID-push`, kind `git_push`, inputs `{"remote": "origin", "ref": "refs/heads/<branch>", "commit": "<new head>"}`, through the B-0c job verbs: JSON on stdin of `python3 "$KY_FLEET/kyaction.py" begin` (exit 3 = the record exists: do not push), then `git push origin HEAD:refs/heads/<branch>`, then `complete` only when `git ls-remote origin refs/heads/<branch>` shows the new head, else `fail`.
  - Packet line 69: 7. Register inside an action record `JOB-$KY_RUN_ID-review`, kind `tracker_event`: `KY_STREAM=<stream> KY_LANE=<slot> ky review <item> --detail "PR #<pr> @ <new head, 40 hex>"`; exit 0: `complete`; else `fail`.
  - Packet line 70: 8. Once step 5 is done (also before an exit 6) write `$KY_RUN/jobs/<job_id>/regen.json` (temp + rename): `{"schema": "ky.regen/1", "job_id", "item", "pr", "old_head", "new_head", "old_base" (merge-base of the old head and `base_sha`), "new_base" (`base_sha`), "conflicted_paths", "outputs": [{"path", "sha256_before", "sha256_after"}], "generator": {"argv", "sha256"}, "tests": [{"argv", "exit"}], "pushed", "review_registered", "inheritance": null}`. `inheritance` is always null: the patch predicate (`kyverdicts.inherits`, ruling P4) is evaluated by the dispatcher and the tracker, never here; undecided means VERIFY.
  - Packet line 90: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the real `ky`, any real PR branch, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 60: **Contract.** `kyregen.sh <job_id>` — INTERPRETATION: the §7 convention of `kyjob.sh <job_id>` (all values from `$KY_RUN/jobs/<job_id>/state.json`, every path absolute). Env: `KY_ROOT`, `KY_RUN`, `KY_FLEET`; `KY_RUN_ID`, `KY_ROLE`, `KY_CONTROLLER_ID` (action records); git = `${KY_GIT:-/usr/bin/git}`; tracker CLI = `${KY_BIN:-$KY_ROOT/bin/ky}`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 63: 1. Preconditions (else 73): `queue_authorised` is false; worktree HEAD == `registered_head`; `git status --porcelain` is empty; `base_sha` is not yet contained in HEAD; `$KY_RUN/locks/item.<item>/owner.json` names a live owner that is this process or an ancestor (liveness as kyaction.py `process_matches`; unknown refuses) — INTERPRETATION: the dispatcher holds the plan's item lock, kyregen takes none; sha256 of `generator.path` == `generator.sha256`, else 4 (pinned generator). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 68: 6. Push, never forced, inside an action record `JOB-$KY_RUN_ID-push`, kind `git_push`, inputs `{"remote": "origin", "ref": "refs/heads/<branch>", "commit": "<new head>"}`, through the B-0c job verbs: JSON on stdin of `python3 "$KY_FLEET/kyaction.py" begin` (exit 3 = the record exists: do not push), then `git push origin HEAD:refs/heads/<branch>`, then `complete` only when `git ls-remote origin refs/heads/<branch>` shows the new head, else `fail`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 69: 7. Register inside an action record `JOB-$KY_RUN_ID-review`, kind `tracker_event`: `KY_STREAM=<stream> KY_LANE=<slot> ky review <item> --detail "PR #<pr> @ <new head, 40 hex>"`; exit 0: `complete`; else `fail`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 70: 8. Once step 5 is done (also before an exit 6) write `$KY_RUN/jobs/<job_id>/regen.json` (temp + rename): `{"schema": "ky.regen/1", "job_id", "item", "pr", "old_head", "new_head", "old_base" (merge-base of the old head and `base_sha`), "new_base" (`base_sha`), "conflicted_paths", "outputs": [{"path", "sha256_before", "sha256_after"}], "generator": {"argv", "sha256"}, "tests": [{"argv", "exit"}], "pushed", "review_registered", "inheritance": null}`. `inheritance` is always null: the patch predicate (`kyverdicts.inherits`, ruling P4) is evaluated by the dispatcher and the tracker, never here; undecided means VERIFY. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 90: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the real `ky`, any real PR branch, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYREPORT_v1.md`

- References/stamp changed: false; bytes: 8998.
- Packet digest after: `37aec20c4e5c420db76f67adb47fd0e3b3a52b914af4de938d7cef8de4aa357d`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 31: F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; R = `$KY_RUN`.
  - Packet line 77: - `completions`: E (default `R/EVENTS.jsonl`) and M via the tracker's `state.build_snapshot` (`KY_TRACKER_LIVE`, default `$KY_ROOT/tracker_live`).
  - Packet line 96: **Do not.** Edit outside `d1_paths`; let tests reach the network or a model; read `~/.claude` or credentials; rebase or force-push; touch production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 31: F = `00_ARCHITECTURE/briefs/kalayantra/fleet`; R = `$KY_RUN`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 77: - `completions`: E (default `R/EVENTS.jsonl`) and M via the tracker's `state.build_snapshot` (`KY_TRACKER_LIVE`, default `$KY_ROOT/tracker_live`). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 96: **Do not.** Edit outside `d1_paths`; let tests reach the network or a model; read `~/.claude` or credentials; rebase or force-push; touch production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. Signals go only to groups the test started, known by pid and start time. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYROUTE_v1.md`

- References/stamp changed: false; bytes: 8996.
- Packet digest after: `f9211eb9e973c785ed1b5a070199871f8ee8571566cb579a6514ff07dd83d05e`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 97: **Do not.** Edit outside `d1_paths` or any frozen file; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 97: **Do not.** Edit outside `d1_paths` or any frozen file; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYVERDICTS_v1.md`

- References/stamp changed: false; bytes: 8996.
- Packet digest after: `34e9670463e2070dd3f60ab126a4119253021d2ac1ca6764e7c48cc1db1cf97a`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 64: One module, no copy: the tracker imports top-level `kyverdicts` from `$KY_ROOT/fleet_live` (`PYTHONPATH`: KV3-B-WRAPPERS), replacing `verdicts.merge_only_between`; an import error there: not inherited.
  - Packet line 78: - Unmet requirement: nothing is published (INTERPRETATION: not REJECTED either), reasons, exit 1. Record `done`: skip. `unfinished`: reconcile against E (default `$KY_RUN/EVENTS.jsonl`): a verdict event of this identity and result whose detail starts `job <J>;`: complete; none: publish; E unreadable: exit 3. `in_progress`: exit 3; `failed`: exit 1.
  - Packet line 81: - Exit 0 · 1 refused or negative · 3 unknown, nothing may proceed · 64 usage · 66 input missing. Environment: `KY_RUN`, `KY_BIN` (`$KY_ROOT/bin/ky`), `KY_GIT` (`/usr/bin/git`).
  - Packet line 92: **Do not.** Edit outside `d1_paths`; run the real `ky` or tracker; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 64: One module, no copy: the tracker imports top-level `kyverdicts` from `$KY_ROOT/fleet_live` (`PYTHONPATH`: KV3-B-WRAPPERS), replacing `verdicts.merge_only_between`; an import error there: not inherited. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 78: - Unmet requirement: nothing is published (INTERPRETATION: not REJECTED either), reasons, exit 1. Record `done`: skip. `unfinished`: reconcile against E (default `$KY_RUN/EVENTS.jsonl`): a verdict event of this identity and result whose detail starts `job <J>;`: complete; none: publish; E unreadable: exit 3. `in_progress`: exit 3; `failed`: exit 1. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 81: - Exit 0 · 1 refused or negative · 3 unknown, nothing may proceed · 64 usage · 66 input missing. Environment: `KY_RUN`, `KY_BIN` (`$KY_ROOT/bin/ky`), `KY_GIT` (`/usr/bin/git`). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 92: **Do not.** Edit outside `d1_paths`; run the real `ky` or tracker; rebase or force-push; touch credentials, production, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-KYVERSION_v1.md`

- References/stamp changed: false; bytes: 8986.
- Packet digest after: `be8663b41faead59f2c32b6e558218894f48f5222a8e56a7068b36fd77594ab6`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 63: Env (as the plists export): `KY_ROOT`, `KY_RUN` (default `$KY_ROOT/run`), `KY_FLEET` (default: the script's directory), `KY_SOURCE_REPO` (the git checkout the manifest is checked in; default as kyctl.sh: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`; no git work tree: refuse).
  - Packet line 64: Existing call forms: kyloop.py `run_helper`: `subprocess.run(["/bin/bash", str(script), *args], capture_output=True, text=True, timeout=300).returncode`, args `["--bootstrap"]` (planner), `["--expected-manifest-digest", digest]` (conductor), `[]` (`derive_completion`; veto loop on a final receipt); only 0 passes. kyctl.sh: `/bin/bash "$KY_FLEET/kyversion.sh" "$varg" >/dev/null 2>&1` (`--bootstrap`, or no argument). PLANNER_LOOP: `bash "$KY_FLEET/kyversion.sh" --bootstrap`.
  - Packet line 65: Files read. `$KY_RUN/INSTALL_RECEIPT.json` (writers: KV3-B-INSTALL, B-5): `mode`; `manifest.manifest_sha256`; `components[] {path, installed_path, sha256}`; final only: `tracker_revision`, `rehearsal {tested_components[] {path, sha256}, results {path, sha256}}`, `coverage {path, sha256, verdict}`, `packets[] {path, sha256}`, `backfill {path, sha256, validated}`. A manifest is the object kymanifest.py `observe` builds (`mode`, `manifest_sha256`, `entrypoints`, `components[] {path, sha256}`, `generated_pairs[]`); the final one, `$KY_RUN/VERSIONS.json`, says `mode: "final"`.
  - Packet line 68: - B2 reuse, never re-implement: `python3 -I -B "$KY_FLEET/kymanifest.py" check "$KY_RUN/VERSIONS.bootstrap.json" --repo "$KY_SOURCE_REPO" --run "$KY_RUN"` (kyboot.py `run_manifest_check` form: cwd `/`, no `GIT_*` / `PYTHON*` variable) exits 0 and prints JSON with `ok: true` and the manifest file's own `manifest_sha256`.
  - Packet line 72: - B6 any `$KY_RUN/ACTIVATION_RECORD*.json` forms a valid chain by the rules of kyloop.py `activation_chain` (broken or forked refuses).
  - Packet line 86: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 63: Env (as the plists export): `KY_ROOT`, `KY_RUN` (default `$KY_ROOT/run`), `KY_FLEET` (default: the script's directory), `KY_SOURCE_REPO` (the git checkout the manifest is checked in; default as kyctl.sh: `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`; no git work tree: refuse). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 64: Existing call forms: kyloop.py `run_helper`: `subprocess.run(["/bin/bash", str(script), *args], capture_output=True, text=True, timeout=300).returncode`, args `["--bootstrap"]` (planner), `["--expected-manifest-digest", digest]` (conductor), `[]` (`derive_completion`; veto loop on a final receipt); only 0 passes. kyctl.sh: `/bin/bash "$KY_FLEET/kyversion.sh" "$varg" >/dev/null 2>&1` (`--bootstrap`, or no argument). PLANNER_LOOP: `bash "$KY_FLEET/kyversion.sh" --bootstrap`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 65: Files read. `$KY_RUN/INSTALL_RECEIPT.json` (writers: KV3-B-INSTALL, B-5): `mode`; `manifest.manifest_sha256`; `components[] {path, installed_path, sha256}`; final only: `tracker_revision`, `rehearsal {tested_components[] {path, sha256}, results {path, sha256}}`, `coverage {path, sha256, verdict}`, `packets[] {path, sha256}`, `backfill {path, sha256, validated}`. A manifest is the object kymanifest.py `observe` builds (`mode`, `manifest_sha256`, `entrypoints`, `components[] {path, sha256}`, `generated_pairs[]`); the final one, `$KY_RUN/VERSIONS.json`, says `mode: "final"`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 68: - B2 reuse, never re-implement: `python3 -I -B "$KY_FLEET/kymanifest.py" check "$KY_RUN/VERSIONS.bootstrap.json" --repo "$KY_SOURCE_REPO" --run "$KY_RUN"` (kyboot.py `run_manifest_check` form: cwd `/`, no `GIT_*` / `PYTHON*` variable) exits 0 and prints JSON with `ok: true` and the manifest file's own `manifest_sha256`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 72: - B6 any `$KY_RUN/ACTIVATION_RECORD*.json` forms a valid chain by the rules of kyloop.py `activation_chain` (broken or forked refuses). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 86: **Do not.** Edit outside `d1_paths`; rebase or force-push; read or print a credential or the environment; touch production, the tracker, the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-LOCALDB_v1.md`

- References/stamp changed: false; bytes: 8995.
- Packet digest after: `377cc19cc482366ffff64e5948b054b8d7b0b7e9aa8299488a7486e30abfc4dc`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 61: **Contract** `bash local_db.sh <command>`. Exit 0 ok or READY; 1 FAILED or not verified; 2 refused, nothing changed; 64 usage. S: `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` and no `..`, else exit 2 before any docker, psql or filesystem call. R = `realpath($KY_SCRATCH)`.
  - Packet line 62: - `slots`: one per line, `b1..bN` then `v1..vM`; N, M: integers in `$KY_RUN/KY_WORKERS`, `$KY_RUN/KY_VERIFIERS`, each 1–8. Missing, unreadable, out of range: exit 1, no output.
  - Packet line 64: - `db <slot> --session S`: creates or re-validates `ky_<slot>`, marked `COMMENT 'ky.session=S'`. READY only when: slot configured; `$KY_RUN/schema/{prod_schema.sql,migrations_applied_data.sql,asset_registry_data.sql}` non-empty; restore errors = today's expected set; the migration runner (`npx tsx scripts/migrate.ts` in `$KY_SOURCE_REPO/platform`, `MIGRATE_APPLY_PROTECTED=1`) exits 0; today's count floors hold; mount and session marks verify. An existing database is trusted only with a READY receipt of the same session, container id and seed hashes; else FAILED.
  - Packet line 67: - `close --session S` (INTERPRETATION of KU-02 "session ownership") prints `close session=S dropped=<n> container=<c>`; in order. No `ky-pg`: c `absent`, exit 0. One `up` would not reuse: reported, no stop, rm or rename; `incompatible`, exit 0. An unmarked non-system database is foreign: no removal, no hand-over; `unmarked_database`, exit 1. Else drops S's databases and receipts; no other session's database remains: removes the container and the resolved direct child of `R/db` holding its bind mount, whatever its label (`removed`); else both pass to a remaining session T, recorded atomically in `$KY_RUN/local_db/container.json` as `{"owner": T, "storage": <absolute path>, "from": S}` (`handed_over`); docker, server and directory observed again: exit 0 = S's databases gone and the container removed or handed over on record; else 1 (also S's label on a container with no record).
  - Packet line 69: - `seed`: operator or executor only (refused if KY_LANE, KY_ITEM or JOB_SCRATCH is set); writes the three files to `$KY_RUN/schema/`; a missing or empty registry dump fails it. Runs as a lone copy (executor.py: `bash <copy> seed`).
  - Packet line 71: Receipt `$KY_RUN/local_db/<slot>.json` (atomic; removed before a restore starts): `{"schema":"ky.slot_db/1","slot","database","result":"READY|FAILED","reason","session_id","container":{"name","id","image","port"},"mount_source","seed":{"schema_sha256","ledger_sha256","registry_sha256"},"runner_rc","tables","kala_tables","ledger","unexpected_restore_errors","tools","ts"}`.
  - Packet line 73: Environment: KY_RUN (default `$KY_ROOT/run`); KY_SCRATCH (required, absolute, existing); KY_SOURCE_REPO (replaces KY_REPO; default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`). Test overrides (absolute paths): KY_DOCKER, KY_PSQL, KY_PG_DUMP, KY_NPX (paths in the receipt's `tools`); KY_PGENV (seed's settings file; tests only: exit 2 if KY_RUN is `/Users/Dev/kalayantra/run`). Logs: `$KY_SCRATCH/db/`.
  - Packet line 77: INTERPRETATION: (1) slot counts are read (plan `b1..b6`, `v1..v4` = §4's maxima); (2) session = `--session`, the role-lock owner's `session_or_run_id`; (3) the seed stays in `$KY_RUN/schema/` (§5: DB dumps under KY_SCRATCH).
  - Packet line 87: **Do not** edit outside Owns; run real docker, psql, pg_dump, the runner or the network; touch the existing `ky-pg`; rebase or force-push; read credentials or pgenv; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 61: **Contract** `bash local_db.sh <command>`. Exit 0 ok or READY; 1 FAILED or not verified; 2 refused, nothing changed; 64 usage. S: `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$` and no `..`, else exit 2 before any docker, psql or filesystem call. R = `realpath($KY_SCRATCH)`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 62: - `slots`: one per line, `b1..bN` then `v1..vM`; N, M: integers in `$KY_RUN/KY_WORKERS`, `$KY_RUN/KY_VERIFIERS`, each 1–8. Missing, unreadable, out of range: exit 1, no output. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 64: - `db <slot> --session S`: creates or re-validates `ky_<slot>`, marked `COMMENT 'ky.session=S'`. READY only when: slot configured; `$KY_RUN/schema/{prod_schema.sql,migrations_applied_data.sql,asset_registry_data.sql}` non-empty; restore errors = today's expected set; the migration runner (`npx tsx scripts/migrate.ts` in `$KY_SOURCE_REPO/platform`, `MIGRATE_APPLY_PROTECTED=1`) exits 0; today's count floors hold; mount and session marks verify. An existing database is trusted only with a READY receipt of the same session, container id and seed hashes; else FAILED. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 67: - `close --session S` (INTERPRETATION of KU-02 "session ownership") prints `close session=S dropped=<n> container=<c>`; in order. No `ky-pg`: c `absent`, exit 0. One `up` would not reuse: reported, no stop, rm or rename; `incompatible`, exit 0. An unmarked non-system database is foreign: no removal, no hand-over; `unmarked_database`, exit 1. Else drops S's databases and receipts; no other session's database remains: removes the container and the resolved direct child of `R/db` holding its bind mount, whatever its label (`removed`); else both pass to a remaining session T, recorded atomically in `$KY_RUN/local_db/container.json` as `{"owner": T, "storage": <absolute path>, "from": S}` (`handed_over`); docker, server and directory observed again: exit 0 = S's databases gone and the container removed or handed over on record; else 1 (also S's label on a container with no record). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 69: - `seed`: operator or executor only (refused if KY_LANE, KY_ITEM or JOB_SCRATCH is set); writes the three files to `$KY_RUN/schema/`; a missing or empty registry dump fails it. Runs as a lone copy (executor.py: `bash <copy> seed`). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 71: Receipt `$KY_RUN/local_db/<slot>.json` (atomic; removed before a restore starts): `{"schema":"ky.slot_db/1","slot","database","result":"READY|FAILED","reason","session_id","container":{"name","id","image","port"},"mount_source","seed":{"schema_sha256","ledger_sha256","registry_sha256"},"runner_rc","tables","kala_tables","ledger","unexpected_restore_errors","tools","ts"}`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 73: Environment: KY_RUN (default `$KY_ROOT/run`); KY_SCRATCH (required, absolute, existing); KY_SOURCE_REPO (replaces KY_REPO; default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`). Test overrides (absolute paths): KY_DOCKER, KY_PSQL, KY_PG_DUMP, KY_NPX (paths in the receipt's `tools`); KY_PGENV (seed's settings file; tests only: exit 2 if KY_RUN is `/Users/Dev/kalayantra/run`). Logs: `$KY_SCRATCH/db/`. — controller-supplied runtime evidence or output for cockpit promotion.
  - Packet line 77: INTERPRETATION: (1) slot counts are read (plan `b1..b6`, `v1..v4` = §4's maxima); (2) session = `--session`, the role-lock owner's `session_or_run_id`; (3) the seed stays in `$KY_RUN/schema/` (§5: DB dumps under KY_SCRATCH). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 87: **Do not** edit outside Owns; run real docker, psql, pg_dump, the runner or the network; touch the existing `ky-pg`; rebase or force-push; read credentials or pgenv; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-OPS-CONTRACT_v1.md`

- References/stamp changed: false; bytes: 8945.
- Packet digest after: `8132114946a537fac04a8f7428ed41f7c8ba157b83df939ee647c85e092add44`.
- admitted before/after: **false / false**.
- Checker reasons after: spec_source_sha256.
- External references found before:
  - None.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - None.

### `PACKET_KV3-B-PRECHECK_v1.md`

- References/stamp changed: false; bytes: 8685.
- Packet digest after: `608f3496ef51ca14270dcf751031355c00cbbdf7ed1807b260b5756b82f2a82a`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 21: "expected_result":"all tests pass; with KY_RUN set nothing under $KY_ROOT/run is read or written",
  - Packet line 52: Plus `KY_ITEM=<ID> bash $KY_FLEET/precheck.sh --item`.
  - Packet line 62: 1. Run directory. After line 10 add `KY_RUN="${KY_RUN:-$KY_ROOT/run}"`. INTERPRETATION: when `KY_RUN` is set but is not an absolute path of an existing directory, print the reason and exit 1 before step 1; never fall back to the live directory.
  - Packet line 63: 2. Replace the three uses of `$KY_ROOT/run` by `$KY_RUN`:
  - Packet line 64:    - lines 22–23, the heavy-step lock and its comment → `$KY_RUN/precheck_heavy.lock`;
  - Packet line 65:    - line 92, the item's test manifest → `$KY_RUN/tests/$KY_ITEM.txt` (both occurrences);
  - Packet line 66:    - line 110, the migration log → `$KY_RUN/precheck_migrate_${LANE}.log` (and the path its failure message prints).
  - Packet line 67:    After the change the script reads and writes nothing under `$KY_ROOT/run` when `KY_RUN` points elsewhere.
  - Packet line 68: 3. Test manifest, the interface the launcher (KV3-B-KYJOB, wave 3; plan §7) may assume, unchanged in form: `TESTS`, when non-empty, is the manifest (newline-delimited paths relative to the repository root); otherwise the file `$KY_RUN/tests/$KY_ITEM.txt`, one path per line. With neither, a diff that changes code stays RED (line 102).
  - Packet line 78: **Acceptance.** The front matter's `acceptance.command`. Each test copies the script next to a manifest it writes, into a throwaway git repository under the pytest base (an `origin/main` ref, stub `npm`, `npx`, `gitleaks` first on `PATH`, a stub `platform/scripts/governance/secret_scan.sh`, `KY_PY` = the test interpreter, `--item` mode), with `KY_ROOT` and `KY_RUN` in separate temporary directories; no network, no database, no real `/Users/Dev/kalayantra` path. The tests show:
  - Packet line 79: - manifests naming different tests under `$KY_ROOT/run/tests/` and `$KY_RUN/tests/`: only the `KY_RUN` one runs, and the listing and hashes under `$KY_ROOT/run` are identical before and after;
  - Packet line 80: - `TESTS` wins over both; with `KY_RUN` unset the `$KY_ROOT/run/tests/` manifest is used as before;
  - Packet line 89: **Do not.** No control-plane edit outside `d1_paths`; no removed or weakened prohibition; no rebase or force-push; no credentials; no production; no database; no edits to the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 21: "expected_result":"all tests pass; with KY_RUN set nothing under $KY_ROOT/run is read or written", — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 52: Plus `KY_ITEM=<ID> bash $KY_FLEET/precheck.sh --item`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 62: 1. Run directory. After line 10 add `KY_RUN="${KY_RUN:-$KY_ROOT/run}"`. INTERPRETATION: when `KY_RUN` is set but is not an absolute path of an existing directory, print the reason and exit 1 before step 1; never fall back to the live directory. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 63: 2. Replace the three uses of `$KY_ROOT/run` by `$KY_RUN`: — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 64:    - lines 22–23, the heavy-step lock and its comment → `$KY_RUN/precheck_heavy.lock`; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 65:    - line 92, the item's test manifest → `$KY_RUN/tests/$KY_ITEM.txt` (both occurrences); — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 66:    - line 110, the migration log → `$KY_RUN/precheck_migrate_${LANE}.log` (and the path its failure message prints). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 67:    After the change the script reads and writes nothing under `$KY_ROOT/run` when `KY_RUN` points elsewhere. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 68: 3. Test manifest, the interface the launcher (KV3-B-KYJOB, wave 3; plan §7) may assume, unchanged in form: `TESTS`, when non-empty, is the manifest (newline-delimited paths relative to the repository root); otherwise the file `$KY_RUN/tests/$KY_ITEM.txt`, one path per line. With neither, a diff that changes code stays RED (line 102). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 78: **Acceptance.** The front matter's `acceptance.command`. Each test copies the script next to a manifest it writes, into a throwaway git repository under the pytest base (an `origin/main` ref, stub `npm`, `npx`, `gitleaks` first on `PATH`, a stub `platform/scripts/governance/secret_scan.sh`, `KY_PY` = the test interpreter, `--item` mode), with `KY_ROOT` and `KY_RUN` in separate temporary directories; no network, no database, no real `/Users/Dev/kalayantra` path. The tests show: — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 79: - manifests naming different tests under `$KY_ROOT/run/tests/` and `$KY_RUN/tests/`: only the `KY_RUN` one runs, and the listing and hashes under `$KY_ROOT/run` are identical before and after; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 80: - `TESTS` wins over both; with `KY_RUN` unset the `$KY_ROOT/run/tests/` manifest is used as before; — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 89: **Do not.** No control-plane edit outside `d1_paths`; no removed or weakened prohibition; no rebase or force-push; no credentials; no production; no database; no edits to the plan, cards, schemas or other packets. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-PREFLIGHT_v1.md`

- References/stamp changed: false; bytes: 8992.
- Packet digest after: `c37e0589472f26ce1d0f6033b94307d96fa2b3df84f2c6453843a1f6a91fc3f2`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 51: `launch`: repairs nothing; first removes `$KY_RUN/LAUNCH_RECEIPT.json`; then, in order:
  - Packet line 53: 2. `claude` — `$CLAUDE_BIN` (default `/Users/Dev/.local/bin/claude`) is executable and `--version` is ≥ 2.1.296.
  - Packet line 54: 3. `smoke` — Claude only: no Codex binary, profile or model, no `kalayantra_fleet.sh smoke`. For every `$KY_FLEET/templates/LAUNCH_CONFIG.<role>.json`: the receipt `$KY_RUN/QUALIFICATIONS/<role>-<model>.json` exists and `/opt/homebrew/bin/python3 -I -B $KY_FLEET/kyqualify.py check <receipt> --config <config> --require-context launchd` exits 0.
  - Packet line 55: 4. `dependencies` — the campaign checkout (`$KY_SOURCE_REPO`, default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`) is a git work tree; `$KY_ROOT/venv/bin/python -c 'import pytest, psycopg, swisseph'`; `platform/node_modules` and `platform-mcp/node_modules` exist; the three ephemeris files match `ephemeris_pins.py`.
  - Packet line 57: 6. `audit` (KU-01) — `KY_STREAM=S $KY_ROOT/bin/ky audit --since kickoff`. Exit 0: ok. Exit 1: every `FAIL <code> <ref>: …` line is echoed and must be reconciled explicitly — `$KY_RUN/AUDIT_RECONCILIATION.json` `{"schema":"ky.audit_reconciliation/1","entries":[{"code","ref","disposition","authority"}]}` must list exactly the findings' (code, ref) pairs (a finding without an entry, an entry without a finding, an empty `disposition` or `authority`: FAIL), and the count in `AUDIT FAIL: <n> findings` must equal the lines parsed. Any other exit: FAIL. Ruling P17: a planner job authors the record, an independent ARTIFACT review accepts it, preflight requires the accepted digest: `$KY_RUN/AUDIT_RECONCILIATION.review.json` {`verdict` "ACCEPTED", `inputs`: the record's sha256 as it is now, `reviewer_session_id` ≠ `author_session_id`}, else FAIL. Preflight never writes either file.
  - Packet line 58: 7. `slots` — `bash $KY_FLEET/local_db.sh slots` exits 0 with at least one `b` and one `v` slot (no lane list or count of its own). Ruling P16, slot PROVISIONABILITY, no standing pool required: for X = the first slot listed and its own session S = `PREFLIGHT-<UTC>-<pid>` (LOCALDB grammar `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`, no colon), `local_db.sh up --session S`, `db X --session S`, `check X` each exit 0; `$KY_RUN/local_db/X.json` is READY for S with `seed` hashes equal to the sha256 of the three `$KY_RUN/schema/` files; then `close --session S` exits 0 and the receipt is gone (KU-02). A failing step: FAIL naming it; `close` is still attempted.
  - Packet line 60: On success only, atomically: `$KY_RUN/LAUNCH_RECEIPT.json` = `{"schema":"ky.launch_receipt/3","mode":"launch","ts","checks":[…],"slots":[…],"slot_proof":{"slot","session","seed":{…},"closed":true},"claude":{"path","version","sha256"},"qualifications":[{"role","model","receipt_sha256","config_sha256"}],"audit":{"exit","findings":[{"code","ref"}],"reconciliation_sha256","review_sha256"},"campaign_head","model_sha256","preflight_sha256"}`, JSON indent 1 (the model's B-3 detector reads `"mode": "launch"`).
  - Packet line 62: Environment: KY_ROOT, KY_RUN, KY_FLEET (default `$KY_ROOT/fleet_live`), KY_SCRATCH (for local_db.sh), KY_SOURCE_REPO, CLAUDE_BIN, PRAVAHA_URL, SE_EPHE_PATH; test override KY_CURL (absolute path).
  - Packet line 74: **Do not** edit outside Owns; run the real `ky`, `claude`, `local_db.sh`, docker or the tracker; author reconciliation entries; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 51: `launch`: repairs nothing; first removes `$KY_RUN/LAUNCH_RECEIPT.json`; then, in order: — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 53: 2. `claude` — `$CLAUDE_BIN` (default `/Users/Dev/.local/bin/claude`) is executable and `--version` is ≥ 2.1.296. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 54: 3. `smoke` — Claude only: no Codex binary, profile or model, no `kalayantra_fleet.sh smoke`. For every `$KY_FLEET/templates/LAUNCH_CONFIG.<role>.json`: the receipt `$KY_RUN/QUALIFICATIONS/<role>-<model>.json` exists and `/opt/homebrew/bin/python3 -I -B $KY_FLEET/kyqualify.py check <receipt> --config <config> --require-context launchd` exits 0. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 55: 4. `dependencies` — the campaign checkout (`$KY_SOURCE_REPO`, default `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign`) is a git work tree; `$KY_ROOT/venv/bin/python -c 'import pytest, psycopg, swisseph'`; `platform/node_modules` and `platform-mcp/node_modules` exist; the three ephemeris files match `ephemeris_pins.py`. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 57: 6. `audit` (KU-01) — `KY_STREAM=S $KY_ROOT/bin/ky audit --since kickoff`. Exit 0: ok. Exit 1: every `FAIL <code> <ref>: …` line is echoed and must be reconciled explicitly — `$KY_RUN/AUDIT_RECONCILIATION.json` `{"schema":"ky.audit_reconciliation/1","entries":[{"code","ref","disposition","authority"}]}` must list exactly the findings' (code, ref) pairs (a finding without an entry, an entry without a finding, an empty `disposition` or `authority`: FAIL), and the count in `AUDIT FAIL: <n> findings` must equal the lines parsed. Any other exit: FAIL. Ruling P17: a planner job authors the record, an independent ARTIFACT review accepts it, preflight requires the accepted digest: `$KY_RUN/AUDIT_RECONCILIATION.review.json` {`verdict` "ACCEPTED", `inputs`: the record's sha256 as it is now, `reviewer_session_id` ≠ `author_session_id`}, else FAIL. Preflight never writes either file. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 58: 7. `slots` — `bash $KY_FLEET/local_db.sh slots` exits 0 with at least one `b` and one `v` slot (no lane list or count of its own). Ruling P16, slot PROVISIONABILITY, no standing pool required: for X = the first slot listed and its own session S = `PREFLIGHT-<UTC>-<pid>` (LOCALDB grammar `^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$`, no colon), `local_db.sh up --session S`, `db X --session S`, `check X` each exit 0; `$KY_RUN/local_db/X.json` is READY for S with `seed` hashes equal to the sha256 of the three `$KY_RUN/schema/` files; then `close --session S` exits 0 and the receipt is gone (KU-02). A failing step: FAIL naming it; `close` is still attempted. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 60: On success only, atomically: `$KY_RUN/LAUNCH_RECEIPT.json` = `{"schema":"ky.launch_receipt/3","mode":"launch","ts","checks":[…],"slots":[…],"slot_proof":{"slot","session","seed":{…},"closed":true},"claude":{"path","version","sha256"},"qualifications":[{"role","model","receipt_sha256","config_sha256"}],"audit":{"exit","findings":[{"code","ref"}],"reconciliation_sha256","review_sha256"},"campaign_head","model_sha256","preflight_sha256"}`, JSON indent 1 (the model's B-3 detector reads `"mode": "launch"`). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 62: Environment: KY_ROOT, KY_RUN, KY_FLEET (default `$KY_ROOT/fleet_live`), KY_SCRATCH (for local_db.sh), KY_SOURCE_REPO, CLAUDE_BIN, PRAVAHA_URL, SE_EPHE_PATH; test override KY_CURL (absolute path). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 74: **Do not** edit outside Owns; run the real `ky`, `claude`, `local_db.sh`, docker or the tracker; author reconciliation entries; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-STEP-CLOSURE_v1.md`

- References/stamp changed: true; bytes: 8961.
- Packet digest after: `1d6e7085b40b587348f4a6084d25a25af9c112ec23fb30b01929dc6801a8f33c`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 7: **Owns/pins.** Base=reviewed job head; d1_paths only; helper/test NEW; no model/workflow/card/manifest/executor/completion/audit/dispatcher edits. CLAUDE.md:139–141; ruling /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:75,78.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
- Kept external references and why:
  - None.

### `PACKET_KV3-B-TRACKER_v1.md`

- References/stamp changed: false; bytes: 8989.
- Packet digest after: `85fc0a67adfea815e09b41cc51dc59223b3706afc6f13d7b097db74eae057c0b`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 85: **Do not** edit outside Owns (plan, cards, schemas, packets, model); write a tracker event outside a temp EVENTS file; run `ky` or the tracker service; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 85: **Do not** edit outside Owns (plan, cards, schemas, packets, model); write a tracker event outside a temp EVENTS file; run `ky` or the tracker service; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-B-WRAPPERS_v1.md`

- References/stamp changed: false; bytes: 8483.
- Packet digest after: `fad33356a22b65a0a614b8654faccf1a2302fb5c58b33ec6bf94f5979db0cef1`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 26: "a fixture path outside $KY_SCRATCH/fixture/ (also through a symlink), or KY_SCRATCH unset: exit 78"]},
  - Packet line 33: **Owns** `F/bin/ky`, `F/bin/kybrief` (new; the only wrapper source), `F/tests/test_kywrappers.py` (new), and in `F/install_tracker.sh` ONLY the two heredocs that generate the wrappers (lines 26–48 today), replaced by installing those two files. Prohibited: `/Users/Dev/kalayantra/bin/{ky,kybrief}` and every installed tree (never written, never executed); the tracker package; the rest of install_tracker.sh; FROZEN paths.
  - Packet line 56: `ky <tracker CLI arguments>` decides one of two modes before anything runs. ROOT = the real directory above the wrapper's own `bin/` (installed: `/Users/Dev/kalayantra`); `KY_ROOT` in the environment is not consulted. CAMPAIGN = `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign` (plan §5; replaces `$KY_ROOT/wt/campaign`; ruling P9: B-2 creates it at the accepted source head and it is not fast-forwarded to `origin/main` during the hold, so the reconciled model is there).
  - Packet line 58: - FIXTURE — any other case: all seven must be set and valid, and are passed on unchanged. Valid = port an integer 1024–65535 other than 8767; URL exactly `http://127.0.0.1:<port>`; HOME, EVENTS, PLAN_MODEL, REPO and HOLD absolute, their real paths (nearest existing ancestor) inside `realpath($KY_SCRATCH)/fixture/`; `KY_SCRATCH` set and absolute. This is the check the cards FIXTURE_BUILDER FB-02 and FIXTURE_VERIFIER FV-02 make.
  - Packet line 77: **Acceptance** Tests first; command above. Tests copy the wrappers into a temp ROOT whose `tracker_live/pravaha_tracker/cli.py` is a stub recording its arguments and the seven values; they never touch `/Users/Dev/kalayantra`. Must show: LIVE defaults exactly as listed, with an empty environment and with kyveto's nine-name environment; a complete valid fixture set passed through unchanged; arguments containing spaces and exit statuses 0, 1, 2, 3 passed through; `kybrief` reading the fixture model in FIXTURE mode and, in LIVE mode, opening exactly the default path (shown from its output whether or not the campaign checkout exists). Negative: the three cases above for `ky` and for `kybrief`, each of the seven names in turn; in every refusal the stub did not run and no file changed. A source test fails if install_tracker.sh still assigns a `PRAVAHA_` value outside its launchd plist block. No output ever contains an environment value. A mode the wrapper cannot decide is REFUSED, never LIVE.
  - Packet line 83: **Do not** edit outside Owns (plan, cards, schemas, other packets, tracker); run or write an installed wrapper; run `install_tracker.sh` or the tracker; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra.
- Copied file reads used by this packet (original SHA-256):
  - None.
- Kept external references and why:
  - Packet line 26: "a fixture path outside $KY_SCRATCH/fixture/ (also through a symlink), or KY_SCRATCH unset: exit 78"]}, — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 33: **Owns** `F/bin/ky`, `F/bin/kybrief` (new; the only wrapper source), `F/tests/test_kywrappers.py` (new), and in `F/install_tracker.sh` ONLY the two heredocs that generate the wrappers (lines 26–48 today), replaced by installing those two files. Prohibited: `/Users/Dev/kalayantra/bin/{ky,kybrief}` and every installed tree (never written, never executed); the tracker package; the rest of install_tracker.sh; FROZEN paths. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 56: `ky <tracker CLI arguments>` decides one of two modes before anything runs. ROOT = the real directory above the wrapper's own `bin/` (installed: `/Users/Dev/kalayantra`); `KY_ROOT` in the environment is not consulted. CAMPAIGN = `/Users/Dev/worktrees.noindex/madhav/claude/kalayantra-campaign` (plan §5; replaces `$KY_ROOT/wt/campaign`; ruling P9: B-2 creates it at the accepted source head and it is not fast-forwarded to `origin/main` during the hold, so the reconciled model is there). — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 58: - FIXTURE — any other case: all seven must be set and valid, and are passed on unchanged. Valid = port an integer 1024–65535 other than 8767; URL exactly `http://127.0.0.1:<port>`; HOME, EVENTS, PLAN_MODEL, REPO and HOLD absolute, their real paths (nearest existing ancestor) inside `realpath($KY_SCRATCH)/fixture/`; `KY_SCRATCH` set and absolute. This is the check the cards FIXTURE_BUILDER FB-02 and FIXTURE_VERIFIER FV-02 make. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 77: **Acceptance** Tests first; command above. Tests copy the wrappers into a temp ROOT whose `tracker_live/pravaha_tracker/cli.py` is a stub recording its arguments and the seven values; they never touch `/Users/Dev/kalayantra`. Must show: LIVE defaults exactly as listed, with an empty environment and with kyveto's nine-name environment; a complete valid fixture set passed through unchanged; arguments containing spaces and exit statuses 0, 1, 2, 3 passed through; `kybrief` reading the fixture model in FIXTURE mode and, in LIVE mode, opening exactly the default path (shown from its output whether or not the campaign checkout exists). Negative: the three cases above for `ky` and for `kybrief`, each of the seven names in turn; in every refusal the stub did not run and no file changed. A source test fails if install_tracker.sh still assigns a `PRAVAHA_` value outside its launchd plist block. No output ever contains an environment value. A mode the wrapper cannot decide is REFUSED, never LIVE. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
  - Packet line 83: **Do not** edit outside Owns (plan, cards, schemas, other packets, tracker); run or write an installed wrapper; run `install_tracker.sh` or the tracker; rebase or force-push; read credentials; touch production. Never: the real launchctl; a signal to a process this job's test did not itself start; a tracker-state ky verb; a write under /Users/Dev/kalayantra. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-SCHEMA-1_v1.md`

- References/stamp changed: true; bytes: 8895.
- Packet digest after: `e10fd83596adaea323e764eb9fb442f12f8fbe5f5bb3075a555fdbeca7160c53`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 8: Authority S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3; S/engines/surrogate/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md:57,86: Kāla writes nullable vocabulary column/meaning comments; notice to SS, only 24h objection window. Study S/jobs/J-20261012T220409Z-b4-define-kv3-schema-1/DEFINE_KV3-SCHEMA-1.md:59-65: column/no-backfill. Q2 custody exception covers no writer/serving change.
  - Packet line 30: cwd platform/python-sidecar: KALA_REQUIRE_DB=1 python3 -B -m pytest tests/l3/kala_db/certification/test_citation_resolution_tier_schema.py -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest". Qualified loopback disposable PostgreSQL only; no skips. Repo: KY_ITEM=KV3-SCHEMA-1 bash "$KY_FLEET/precheck.sh" --item. Required CI/Kāla DB Tests/independent head review; schema-prerequisite test captures real base failure.
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/DEFINE_KV3-SCHEMA-1.md` — `241e9ba26b646d428a4314de155436e1610e18fe119a966d75dab976e4a3d203`.
- Kept external references and why:
  - Packet line 30: cwd platform/python-sidecar: KALA_REQUIRE_DB=1 python3 -B -m pytest tests/l3/kala_db/certification/test_citation_resolution_tier_schema.py -q -p no:cacheprovider --basetemp="$JOB_SCRATCH/pytest". Qualified loopback disposable PostgreSQL only; no skips. Repo: KY_ITEM=KV3-SCHEMA-1 bash "$KY_FLEET/precheck.sh" --item. Required CI/Kāla DB Tests/independent head review; schema-prerequisite test captures real base failure. — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.

### `PACKET_KV3-SCHEMA-2_v1.md`

- References/stamp changed: true; bytes: 8999.
- Packet digest after: `e37d5bd749e7c9f439b0cb24151a32894269d8b8e495b9dd8fcc7c2d25d42a0d`.
- admitted before/after: **true / true**.
- Checker reasons after: none.
- External references found before:
  - Packet line 6: Aliases: Y=platform/python-sidecar; F=00_ARCHITECTURE/briefs/kalayantra/fleet; S=/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3.
  - Packet line 28: Persistence: Y/services/ka_kshetra/writer.py:833-850,879-901 writes/reads legacy DHARA NullResult, not shared Experiment. /Users/Dev/kalayantra/wt/k2/platform/python-sidecar/services/ka_sangam/jury/candidate.py:232-242,268-279 stores shared NullResult + estimand/conditioning as conditional_null/pipeline_null. Flatten TYPE fields; no jury→field values. Y/tests/l3/kala_core/measure/test_measure.py:79-87 distinguishes three experiments. Keep old null_max_stats/replicates distinct from NEW null_statistics/denominator.
  - Packet line 39: Repo: KY_ITEM=KV3-SCHEMA-2 bash "$KY_FLEET/precheck.sh" --item
- Copied file reads used by this packet (original SHA-256):
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_05_RULINGS_AND_ORDER.md` — `00c7d0baa3543ca59492c4599fafc135b956d7574bd0da886c282684ee339385`.
  - `00_ARCHITECTURE/briefs/kalayantra/evidence/KV3-PKT-EXTERNAL-REFS/SURROGATE_ANSWER_06_AUDIT_AND_SCHEMA2.md` — `9bbbe55a3dd79fecded46b0f23923b4d8c358af29dcaa198b7b226e90408facb`.
- Kept external references and why:
  - Packet line 40: Repo: KY_ITEM=KV3-SCHEMA-2 bash "$KY_FLEET/precheck.sh" --item — runtime contract/default, prohibition or fixture stand-in; no static worker READ dependency.
- (I) INTERPRETATION: retired wt/k2 source is missing; existing repository candidate.py supplies the read. Historical equality is unverified; inherited acceptance gates remain.

## Validation

- For every packet: `python3 -I -B 00_ARCHITECTURE/briefs/kalayantra/fleet/kypacket.py check <packet> --repo <working-copy>`.
- All 44 previously admitted packets: exit 0, admitted:true. The same seven pre-existing refusals: exit 1; no new refusals.
- All 51 packet digests compute and match; all 51 packet sizes ≤9,000 bytes.
- 25 copies: source/header hashes, payload equality after declared redactions, basename preservation, line-count preservation, and no symlinks verified.
- 126 shifted file references: cited source endpoints retain their text at original line +2 (excluding declared redaction spans).
- Privacy and external-static-reference checks passed. No unrelated source/schema/contract edits.
