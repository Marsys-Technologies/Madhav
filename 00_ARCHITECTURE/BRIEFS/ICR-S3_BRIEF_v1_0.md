---
session_id: ICR-S3
canonical_id: ICR_S3_BRIEF
version: 1.0
status: ACTIVE
authored_on: 2026-05-21
authored_by: Claude Code (brief-authorship)
branch: feature/m5-coverage-remediation
spec_artifact: 00_ARCHITECTURE/CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md
spec_section: §N.6 ICR-S3
may_touch:
  - platform/src/lib/icr/**
  - platform/scripts/governance/run_icr_detector.ts
  - platform/tests/icr/**
  - 06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json
must_not_touch:
  - platform/src/lib/icr/types.ts
  - platform/src/lib/icr/schema_validator_icr.py
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  - platform/supabase/migrations/**
  - platform/src/app/**
  - platform/src/components/**
gates:
  - tsc
  - vitest_changed
  - intra_signal_munta_detected
---

# ICR-S3 Brief — Intra-Signal Conflict Detector (Muntha Smoke Test)

## §1 Session identity

- **Session:** ICR-S3
- **Stream:** Intra-signal Conflict Resolution (ICR)
- **Phase plan:** `PHASE_M5_PLAN_v1_0.md` §N.6 ICR-S3
- **Branch:** `feature/m5-coverage-remediation`
- **Depends on:** ICR-S1 (types + scaffold) COMPLETE; ICR-S2 (L1 truth index) COMPLETE

## §A — Goal

Implement the Class A conflict detector in `detector.ts`. The detector reads MSR signals, extracts the `claim` and `sources` fields, fetches the cited FORENSIC fields via direct file read (using a new thin `forensic_reader.ts` module), and checks for textual contradictions deterministically — no LLM calls. The primary smoke test is MSR.377 (DIS.013, Muntha conflict): the detector must emit a `ConflictRecord` with `class: A` and `signal_ids_affected: ['MSR.377']`. This conflict must emerge from actual MSR and FORENSIC corpus data; it must not be hard-coded or faked. Before implementing, the session must read `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` to locate MSR.377's claim text and sources, and `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` to locate the contradicting FORENSIC field value. The session must also read the current state of `platform/src/lib/icr/detector.ts` (scaffolded empty in ICR-S1) before writing any implementation.

## §B — Files to touch

| File | Action | Description |
|------|--------|-------------|
| `platform/src/lib/icr/detector.ts` | EDIT | Implement the `detect()` / `detectClassA()` method (currently throws "Not implemented — ICR-S3") |
| `platform/src/lib/icr/forensic_reader.ts` | CREATE | Thin reader extracting FORENSIC field values by section reference; used by detector |
| `platform/tests/icr/detector.test.ts` | CREATE | Vitest unit test with a synthetic MSR fragment containing a known sign-placement mismatch; verifies the detector emits a ConflictRecord |
| `platform/scripts/governance/run_icr_detector.ts` | CREATE | Governance script: runs detector against live corpus, writes output to `06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json` |
| `06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json` | CREATE | Written by the governance script at session time; consumed by ICR-S4 |

**Must not touch:** `platform/src/lib/icr/types.ts` — ConflictRecord and all other ICR types from ICR-S1 must not be modified. The detector implementation must use the existing type definitions unchanged.

## §C — Acceptance criteria

| # | Criterion | Gate |
|---|-----------|------|
| AC.1 | Detector exits with ≥ 1 conflict detected when run against live corpus | `intra_signal_munta_detected` |
| AC.2 | Output JSON contains a ConflictRecord where `signal_ids_affected` includes `MSR.377` and `class === 'A'` | `intra_signal_munta_detected` |
| AC.3 | Detector output serialized to `06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json` | manual verify |
| AC.4 | Unit test passes on synthetic fixture | `vitest_changed` |
| AC.5 | `tsc --noEmit` exits 0 | `tsc` |

## §D — Hard rules

1. **Do not edit any file outside the `may_touch` list.** The `must_not_touch` list is exhaustive for the restricted items.
2. **`platform/src/lib/icr/types.ts` is frozen.** The `ConflictRecord` type from ICR-S1 must be used as-is. Any required additions to the conflict model that are not in the existing type are a session halt — raise to native before proceeding.
3. **The detector must be DETERMINISTIC.** No LLM calls. Detection logic is field lookup and string comparison only: extract the claimed sign/placement from the MSR signal's `claim` text, look up the actual value from the FORENSIC file, compare. If they differ, emit a ConflictRecord.
4. **The Muntha (MSR.377) detection is the smoke test.** If running the detector against the live corpus does not surface MSR.377 as a Class A conflict, the `intra_signal_munta_detected` gate fails and the session halts. Do NOT hard-code MSR.377 into the detector — the conflict must emerge naturally from the corpus data comparison.
5. **Read before implement.** Before writing any detector logic: (a) read `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` to find MSR.377's `claim` text and `sources` block; (b) read `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` to find the contradicting FORENSIC field; (c) read the current `platform/src/lib/icr/detector.ts` to understand the exact scaffold the implementation must fill.
6. **`forensic_reader.ts` must be thin.** It reads the FORENSIC markdown file from the filesystem, locates field values by section heading or structured marker, and returns the string value. No caching, no external dependencies beyond `fs` and `path`.
7. **Output JSON schema.** `ICR_DETECTOR_OUTPUT_v1_0.json` must be a valid JSON array of `ConflictRecord` objects (using the type from `types.ts`). Any deviation from the type schema fails `tsc`.

## §E — Gate definitions

| Gate | Command | Pass condition |
|------|---------|----------------|
| `tsc` | `cd platform && npx tsc --noEmit` | exits 0 |
| `vitest_changed` | `cd platform && npx vitest run --changed` | all changed-file tests pass |
| `intra_signal_munta_detected` | `cd platform && npx tsx scripts/governance/run_icr_detector.ts` then inspect `06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json` | JSON contains a record with `signal_ids_affected` including `"MSR.377"` and `"class": "A"` |

All three gates must pass before the session may claim close.

## §F — Pre-implementation reading checklist

Before writing any code, the implementing session must verify it has read and understood:

- [ ] `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` — locate MSR.377: what is the exact claim text? What sources block does it carry? Which FORENSIC section does it cite?
- [ ] `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — locate the FORENSIC field cited by MSR.377: what is the actual value in the canonical L1 record?
- [ ] `platform/src/lib/icr/detector.ts` — what exact method signature does the scaffold declare? (e.g., `detectClassA(signals: MSRSignal[]): ConflictRecord[]`)
- [ ] `platform/src/lib/icr/types.ts` — what fields does `ConflictRecord` carry? (frozen; must not modify)

The discrepancy between MSR.377's claim and the FORENSIC field value is the evidence the detector must find and encode in the `evidence` field of the ConflictRecord.

## §G — Output artifact

`06_LEARNING_LAYER/ICR_DETECTOR_OUTPUT_v1_0.json` — consumed by ICR-S4 (propose-patch emitter). Must be present and valid at session close. Format:

```json
{
  "generated_at": "<ISO timestamp>",
  "corpus_version": "MSR_v3_0.md v3.1 (514 signals)",
  "conflict_count": <N>,
  "conflicts": [
    {
      "conflict_id": "...",
      "conflict_class": "A",
      "signal_ids_affected": ["MSR.377"],
      "description": "...",
      "detected_at": "<ISO timestamp>",
      "evidence": "..."
    }
    ...
  ]
}
```

The `conflicts` array is what ICR-S4 reads to drive propose-patch emission.

## §H — Next session

ICR-S4 — Propose-patch emitter. For each ConflictRecord in `ICR_DETECTOR_OUTPUT_v1_0.json`, compute the full propose-patch artifact and write to `PROPOSED/`. For MSR.377 specifically: the patch proposes a specific text correction to the Muntha claim, with `before` and `after` strings derived from the discrepancy the detector found. Session ends with NATIVE_REVIEW_REQUIRED halt. Scope: `CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md §N.6 ICR-S4`.

---
*End of ICR-S3_BRIEF_v1_0.md*
