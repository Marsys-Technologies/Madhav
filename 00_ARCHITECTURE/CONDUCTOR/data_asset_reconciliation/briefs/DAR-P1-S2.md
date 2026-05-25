---
session_id: DAR-P1-S2
phase: 1
status: PENDING
branch: feature/data-asset-reconciliation
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavDataAsset
may_touch:
  - platform/python-sidecar/pipeline/main.py
  - platform/python-sidecar/pipeline/extractors/msr_extractor.py
  - platform/python-sidecar/pipeline/writers/msr_signals_writer.py
  - platform/python-sidecar/rag/chunkers/msr_signal.py
  - platform/python-sidecar/pipeline/ingest_msr.py
must_not_touch:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md
  - platform/src/
  - platform/supabase/migrations/
  - platform/migrations/
---

# DAR-P1-S2: Python pipeline MSR source + count updates

## Context

The Python build pipeline hardcodes `MSR_v3_0.md` as source and `EXPECTED_COUNT=514`.
MSR v5.0 has 573 signals. This session updates all 7 hardcoded locations across 5 files.
The gate-check in `msr_signals_writer.py` will reject any DB load that sends the wrong
count — fixing this here unlocks Phase 3 (pipeline cascade).

## Steps (read each file before editing)

1. `platform/python-sidecar/pipeline/main.py`:
   Find the MSR source path constant (typically `MSR_FILE` or `MSR_SOURCE`).
   Change: `MSR_v3_0.md` → `MSR_v5_0.md`

2. `platform/python-sidecar/pipeline/extractors/msr_extractor.py`:
   - `SOURCE_FILE`: `MSR_v3_0.md` → `MSR_v5_0.md`
   - `EXPECTED_COUNT`: `514` → `573`

3. `platform/python-sidecar/pipeline/writers/msr_signals_writer.py`:
   - `SOURCE_FILE`: `MSR_v3_0.md` → `MSR_v5_0.md`
   - `EXPECTED_COUNT`: `514` → `573`

4. `platform/python-sidecar/rag/chunkers/msr_signal.py`:
   - `SOURCE_FILE`: `MSR_v3_0.md` → `MSR_v5_0.md`
   - `SOURCE_VERSION`: `"3.1"` → `"5.0"` (or whatever the version string field is called)

5. `platform/python-sidecar/pipeline/ingest_msr.py`:
   Update any docstring or inline reference to MSR_v3_0 or count 514.

6. Verify the extractor is importable and shows correct values:
   ```bash
   cd platform/python-sidecar
   python3 -c "from pipeline.extractors.msr_extractor import MSRExtractor; e=MSRExtractor(); print(e.SOURCE_FILE, e.EXPECTED_COUNT)"
   ```
   Expected output: `MSR_v5_0.md 573`

7. Commit:
   ```
   dar: P1-S2 update Python pipeline MSR source + EXPECTED_COUNT to v5.0/573
   ```

## Acceptance criteria

- `grep -rn 'MSR_v3_0' platform/python-sidecar/pipeline/ --include='*.py'` → 0 results
- `grep 'EXPECTED_COUNT = 573' platform/python-sidecar/pipeline/extractors/msr_extractor.py` → match
- `grep 'EXPECTED_COUNT = 573' platform/python-sidecar/pipeline/writers/msr_signals_writer.py` → match
- `grep 'MSR_v5_0' platform/python-sidecar/rag/chunkers/msr_signal.py` → match
- `grep 'SOURCE_VERSION.*5\.0' platform/python-sidecar/rag/chunkers/msr_signal.py` → match
