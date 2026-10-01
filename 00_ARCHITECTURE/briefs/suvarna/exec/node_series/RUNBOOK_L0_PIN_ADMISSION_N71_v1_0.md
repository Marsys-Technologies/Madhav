---
artifact: RUNBOOK_L0_PIN_ADMISSION_N71
version: "1.0"
status: "REHEARSED on a scratch checkout of main (2026-10-02, nothing pushed); to be run for Pravāha's #2882 (bg_gochara_arcs) and again for Suvarṇa's bg_ephemeris change"
produced_by: Exec Suvarṇa
decision: "N-71 (Strategic Suvarṇa under the owner's delegation N-43; owner informed 2026-10-02)"
---

# L0 pin admission under N-71 (the lightest valid form)

**What it is.** The L0 analysis-receipts test (`platform/src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts`) stays as a tripwire: it compares the sha256 of the `bg_` slice of `nirmana-writer-digests.json` with `layers.L0.pin.writer_inventory_sha256` in `nirmana-analysis-layer-pins.json`. It has no hard-coded expectation. When an L0 writer digest moves only through an import-closure change, the pin is advanced by a **successor admission** that states exactly which single L0 digest moved ("exactly one L0 digest moved (<asset>), other 39 byte-identical") with the before and after inventory sha.

## Measured facts (rehearsal)
- An edit to `services/w2g/db_source.py` moves exactly two writer digests on main: `bg_gochara_arcs` (L0) and `ka_gochara` (L3). L0 inventory before `64b8859fe6925c178719f6da8b130de73cd29ffe03dcf4bdc19bd0981a0ffff1`. L3 is the other team's layer pin.
- The lightest class is accepted: classification `<asset>=derived_import_change` with the EXISTING `EXPECTED_REVIEW_ARTIFACTS['L0']` acceptance artifact; no `SOURCE_ACCEPTANCE_BINDINGS` entry and no new review needed. Rehearsal result: "admitted L0 successor l0:0c162be16310:6c89138a235c", `changed_assets ['bg_gochara_arcs']`, receipts test 3/3 passed.
- `suvarna_reader` can run the generator: it has USAGE on `nirmana_evidence` and SELECT on `nirmana_evidence.nirmana_elevation_campaign_definitions` (the frozen manifest). No admin secret.

## Sequence
0. **Authority record on main first** (docs PR, two commits: the first introduces `00_ARCHITECTURE/briefs/nirmana/L0_N71_PINS_READMISSION_AUTHORITY_v1_0.md`, the second quotes the first commit's SHA as the immutable approval identity; after squash-merge, `evidence_commit` is the squash commit on main, `authority_commit` is the first commit's SHA). Note its sha256 after merge.
1. **The source branch freezes** with regenerated `nirmana-writer-digests.json` (and census) at head `S`. Admission requires `inventory_at(S) == candidate inventory`, so `S` must contain the regenerated digests.
2. **ONE admission commit on top of `S`** (none of the source branch's code touched). Files, exactly: `platform/scripts/generate/nirmana_analysis_layer_pins.py` (two constant entries: `AUTHORITY_BINDINGS["N-71"]` = {authority_commit, evidence_commit, path, sha256 of the blob at evidence_commit, `decision_binding: "status: PINS_READMISSION_AUTHORIZED"`, `authority_identity_binding` = the backtick-quoted authority commit}; `AUTHORIZED_SOURCE_COMMITS["N-71"]["L0"] = frozenset({S})`) and `platform/src/generated/nirmana-analysis-layer-pins.json`.
3. Command (from `platform/`; read-only DSN as the reader; never print it):
   `( source ~/.config/suvarna/pgenv.sh; DATABASE_URL='postgresql://' python -m scripts.generate.nirmana_analysis_layer_pins --admit-successor --layer L0 --protected-baseline-commit <main tip> --source-commit <S> --historical-snapshot-commit <main tip> --definition-snapshot-commit 5142109f7f219ea860f859e322646f79d875bee8 --authority-decision N-71 --authority-commit <first commit of the docs PR> --review-artifact '{"commit":"f6fed12c794224329f6b3b436f8b1b814499d06d","path":"00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE_v1_0.md","sha256":"abeb3ffa67d646bdbf4777145ba43e97318e04da9226c78a3fb2e0876b7e76f4","decision_binding":"status: PRODUCER_READY_ACCEPTED"}' --reason "<bounded reason>" --classification <asset>=derived_import_change )`
4. **Verify before pushing:** exactly one L0 digest differs between main's and the branch's `nirmana-writer-digests.json` (`bg_` entries); the admission commit's diff contains only the two files above; `python -m scripts.generate.nirmana_analysis_layer_pins --check --protected-baseline-commit <main tip>` reports NO line mentioning L0; `npx vitest run src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts` passes. State in the commit message and PR body: "exactly one L0 digest moved (<asset>), other 39 byte-identical", before sha, after sha.

## Gotchas found in the rehearsal
- `--check` (every variant) is RED on clean main for L1, L2 and L3 ("writer_inventory_sha256 is stale", "changed_assets do not match exact delta"): pre-existing, not L0, and `test_nirmana_analysis_layer_pins.py` has 9 known failures. "Green" for the admission means: no L0 failure and the receipts test passing; do not try to fix other layers' pins in this commit.
- The authority document must contain its own approval identity string, so it cannot quote its own commit: hence two commits.
- The review artifact for L0 must equal `EXPECTED_REVIEW_ARTIFACTS['L0']` exactly; a different artifact forces a `SOURCE_ACCEPTANCE_BINDINGS` entry (heavier path).
- zsh does not word-split unquoted variables: pass flags explicitly, not via `$flags`.
- After squash-merge the source head `S` is not an ancestor of main; the precedents (D-PINS-A2 for L3) were admitted in the same shape and passed CI. Not re-verified here.
- For `bg_ephemeris` (Suvarṇa) the same procedure applies with its own source commit and `bg_ephemeris=...` classification (an intentional change, not derived: use `approved_intentional_change` and a bound review if the generator demands one for that class); the second admission rebases over the first.
