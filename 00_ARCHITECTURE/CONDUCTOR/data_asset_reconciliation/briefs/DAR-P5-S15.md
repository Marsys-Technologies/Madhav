---
session_id: DAR-P5-S15
phase: 5
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - platform/python-sidecar/tools/generate_derivation_ledger_stubs.py  # create
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
  - platform/migrations/
---

# DAR-P5-S15: Build derivation_ledger stub generator

## Context

MSR v5.0 has 573 signals. The B.3 architecture principle requires every signal to carry a
`derivation_ledger.l1_sources` block listing the FORENSIC v8.0 fact IDs it consumes.
The DAR audit found 419/573 signals lack this (CF.V13.1). This session builds the stub
generator tool that seeds the grounding blocks, which Sessions S16–S20 then populate.

## Steps

1. Read `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` — understand the signal structure.
   Each signal has: `signal_id`, `domain`, `title`, optionally `derivation_ledger`.

2. Read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — understand the `v6_id`
   fact reference scheme (e.g. `F.LAGNA.001`, `F.SUN.POS.001`, etc.).

3. Create `platform/python-sidecar/tools/generate_derivation_ledger_stubs.py`:

   The script must:
   - Accept `--source` (path to MSR_v5_0.md), `--dry-run` (print count, don't write), `--output` (path)
   - Parse all 573 signals from the MSR markdown
   - For each signal WITHOUT a `derivation_ledger:` block, generate a stub:
     ```yaml
     derivation_ledger:
       l1_sources: []  # TODO: fill with FORENSIC v6_id references
       grounding_status: PENDING
       grounded_by: ~
       grounded_date: ~
     ```
   - In `--dry-run` mode: print `stubs_generated: <count>` and `already_grounded: <count>`
   - In normal mode: write the updated MSR file with stubs inserted

4. Test the dry-run:
   ```bash
   python3 platform/python-sidecar/tools/generate_derivation_ledger_stubs.py \
     --source 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md \
     --dry-run
   ```
   Expected output includes: `stubs_generated: 419` (approximately)

5. Commit:
   ```
   dar: P5-S15 build derivation_ledger stub generator (419 signals → grounding sessions S16-S20)
   ```

## Acceptance criteria

- `test -f platform/python-sidecar/tools/generate_derivation_ledger_stubs.py` → TRUE
- `python3 .../generate_derivation_ledger_stubs.py --dry-run 2>&1 | grep -q 'stubs_generated'` → match
