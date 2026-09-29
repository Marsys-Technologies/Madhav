# 12.10c MERGE HYGIENE RUNBOOK — PR #2731 second-merger regeneration

- **Status:** DOCUMENTED 2026-09-27 (ADK-0018 runway item b). **This runbook is
  instructions for the merger — nothing here has been executed by this lane,
  and none of it may run before the second merge lands.**
- **Source requirement:** `briefs/GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md`
  §12 row 12.10c, carried by `HOLD_STATE_2026-09-24.md` ("What a merger needs
  to know").
- **Scope:** whoever merges **second** between this branch
  (`l3/gochara-autonomous-wp0-7`, PR #2731) and the L0 lane. Both branches edit
  `ka_vedha_gochara/logic.py` in different hunks; `git merge-tree` shows a
  clean merge (per the L0 session). The hygiene below is required **because the
  three generated artifacts fingerprint each other** — a clean textual merge
  still leaves them mutually stale.
- **Exit gate (from the brief):** CI green on the second merge **without a
  manual pin fix**.
- **Decision authority for the new generations:**
  `NATIVE-2026-09-24-L0-REPAIR-REPIN`, with pinned generation ids
  `l0:7d40f8c70640:64b8859fe692`, `l2:7d40f8c70640:dbbbb24c09cb`,
  `l3:7d40f8c70640:dfcf30d8b3d2`.

## Ordering constraint

Run every step **after** the merge commit exists, against the **merged tree**
(check out the merge result; do not run on either parent). The digests hash
writer source, the pins hash the digests, and the census's provenance records
the source revision — running any of them on a pre-merge tree regenerates a
fingerprint of the wrong content.

## Step 1 — Regenerate `nirmana-writer-digests.json`

Generator (verified to exist this session):
`platform/python-sidecar/pipeline/orchestrator/provenance_inventory.py`
(discovers every executable sidecar writer via `WRITER_REGISTRY`, sha256s their
source, writes the checked-in artefact).

```
cd platform/python-sidecar
python -m pipeline.orchestrator.provenance_inventory
# verify (CI runs this form; must be clean before commit):
python -m pipeline.orchestrator.provenance_inventory --check
```

Output: `platform/src/generated/nirmana-writer-digests.json`.

## Step 2 — Re-admit the L3 pin

Generator: `platform/scripts/generate/nirmana_analysis_layer_pins.py`
(`--admit-successor` appends one reviewed layer successor while retaining the
complete predecessor; `--layer L3` regenerates ONLY L3's record so the other
layers' committed `convergence_commit` claims are not falsely restated — see
NIRMANA issue #1814). Requires `DATABASE_URL` (the frozen campaign manifest in
`nirmana_evidence.nirmana_elevation_campaign_definitions` is the authority for
receipt_count / non_writer_assets).

Shape of the command — every immutable commit value must be filled from the
merged tree at merge time, never copied from a prior run:

```
cd platform
DATABASE_URL=<read-only DSN against the evidence DB> \
python -m scripts.generate.nirmana_analysis_layer_pins \
  --admit-successor --layer L3 \
  --protected-baseline-commit <main tip at merge time> \
  --convergence-commit <reviewed commit on the merged tree> \
  --source-commit <immutable implementation predecessor> \
  --historical-snapshot-commit <commit whose writer inventory reconstructs the active predecessor> \
  --authority-decision NATIVE-2026-09-24-L0-REPAIR-REPIN \
  --authority-commit <immutable approval commit> \
  --review-artifact <acceptance-artifact JSON; repeat per review> \
  --definition-snapshot-commit <pin/inventory snapshot commit> \
  --reason "<bounded evidence-backed successor reason>" \
  --classification <asset_id=classification for every changed L3 asset>
# verify afterwards (offline, no DB):
python -m scripts.generate.nirmana_analysis_layer_pins --check
```

Output: `platform/src/generated/nirmana-analysis-layer-pins.json`.

## Step 3 — Regenerate `capability_estate_census.json`

Generator (npm script, verified in `platform/package.json`):

```
cd platform
npm run codegen:capability-estate-census -- \
  --generated-at=<ISO 8601 timestamp of the regeneration> \
  --source-revision=<40-hex SHA of the merged tree>
# verify:
npm run codegen:capability-estate-census:check
```

(`--source-revision` takes the merge commit SHA; when omitted the generator
falls back to the committed provenance — pass it explicitly so the census
records the merged tree, per the script's own usage line.)

## Step 4 — Conjunct-(j)/1072 interplay (recorded state; merge-time note stands)

From `platform/python-sidecar/scripts/kala_gochara_cutover/evidence/step05_evidence.md`
(§"Conjunct-(j)/1072 interplay — recorded state") and
`REMAINDER_FINAL_REPORT_v1_0.md` E-017:

- Migration **1072 is NOT applied** in production (cherry-picked but
  unapplied); production `target_table` stays `kala_gochara_windows`, which is
  exactly what the step-5 registry re-pin (1091) conjunct (j) gates on.
- If 1072 is ever applied later it would flip `target_table` to
  `kala_gochara_windows_v2` and **break conjunct (j)**. The merger must not
  apply 1072 as part of merge hygiene, and must not "fix" the step04
  APPLY_SET REFUSED-migrations guard (1085/1086 exit 3) by re-adding those
  numbers.
- 12.10c regenerations are file-only artifacts; they neither apply nor require
  1072.

## Step 5 — Commit and verify

1. `git status` should show exactly the three regenerated files (and nothing
   else): `platform/src/generated/nirmana-writer-digests.json`,
   `platform/src/generated/nirmana-analysis-layer-pins.json`,
   `platform/src/generated/capability_estate_census.json`.
2. Commit them on the merge branch with a message naming
   `NATIVE-2026-09-24-L0-REPAIR-REPIN` and the three pinned generation ids.
3. The exit gate is CI green on the second merge **without a manual pin fix** —
   if either `--check` above fails after the regeneration commit, the merge is
   not hygienic; stop and investigate rather than hand-editing a pin.
