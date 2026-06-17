---
brief_id: M2_F2_MANIFEST_COMPLETENESS
karn_session_name: KARN-W7-R2-MANIFEST-COMPLETENESS
wave: 7
stream: F
status: READY
authored_by: Claude (Cowork) 2026-04-30 — Wave 7 open
authored_for: Claude Code execution (autonomous, long-running)
session_type: repair (manifest completeness — add absent source-document entries)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §F2
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: |
    KARN-W5-R2-D234-BUNDLE (Wave 5) — COMPLETE. Created retrieval tools
    for remedial_codex_query and timeline_query. Those tool entries reference
    source_canonical_ids that are NOT in CAPABILITY_MANIFEST.json.
    KARN-W6-R1-COMPOSITION-RULES — COMPLETE. remedialRule + timelineRule
    reference these source canonical IDs at runtime (path B silent-skip in prod).
parallel_stream_note: |
  W7-R2 (this brief) runs concurrently with:
  - KARN-W7-R1-AUDIT-REPAIR (F1 — DB backfill; no manifest overlap)
  - KARN-W7-R3-EVAL-HARNESS (F3 — new eval scaffold; no manifest overlap)
  W7-R2 is the ONLY brief that modifies CAPABILITY_MANIFEST.json in Wave 7.
estimated_time: 1 day single Claude Code session
---

# CLAUDECODE_BRIEF_M2_F2_MANIFEST_COMPLETENESS
## Wave 7 — CAPABILITY_MANIFEST Source Document Registration

---

## §0 — Pre-flight (read before any tool call)

```
ROOT = ~/Vibe-Coding/Apps/Madhav
MANIFEST = ~/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
```

Read in order before any action:
1. This brief (complete)
2. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — current state (106 entries, v1.6)
3. `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md` — frontmatter only (first 40 lines)
4. `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md` — frontmatter only (first 40 lines)
5. `05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md` — frontmatter only (first 40 lines)

Emit session-open handshake per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §1 — Problem statement

Three source-document canonical IDs are referenced by retrieval-tool manifest
entries but are not themselves registered as manifest entries:

| Missing canonical_id | Referenced by | File path |
|---|---|---|
| `REMEDIAL_CODEX_v2_0_PART1` | `RETRIEVAL_TOOL_REMEDIAL_CODEX_QUERY.source_canonical_ids` | `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md` |
| `REMEDIAL_CODEX_v2_0_PART2` | `RETRIEVAL_TOOL_REMEDIAL_CODEX_QUERY.source_canonical_ids` | `04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md` |
| `LIFETIME_TIMELINE_v1_0` | `RETRIEVAL_TOOL_TIMELINE_QUERY.source_canonical_ids` | `05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md` |

This means:
- `composition_rules.ts` `remedialRule` and `timelineRule` cannot locate these
  files from the manifest at runtime (path B: collectEntries silent-skip)
- `drift_detector.py` cannot verify file integrity for these sources
- The manifest's `entry_count` (currently 106) undercounts actual tracked files

---

## §2 — Scope

```
MAY TOUCH:
  00_ARCHITECTURE/CAPABILITY_MANIFEST.json   (add 3 new entries + bump version/count)
  00_ARCHITECTURE/BRIEFS/M2_PROVENANCE_AUDIT_RESULTS.md   (optional — update advisory
    section if manifest gap was recorded there; do NOT touch if not present)

MUST NOT TOUCH:
  04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md   (read only)
  04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md   (read only)
  05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md    (read only)
  04_REMEDIAL_CODEX/REMEDIAL_CODEX_v1_0_PART1.md  (predecessor — do not register)
  04_REMEDIAL_CODEX/REMEDIAL_CODEX_v1_0_PART2.md  (predecessor — do not register)
  platform/src/**
  Any file not listed in MAY TOUCH
```

---

## §3 — Implementation

### §3.1 — Compute file fingerprints

For each of the three source files, compute SHA-256:

```bash
sha256sum 04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md \
          04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md \
          05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md
```

Record the hex digest for each. These go into the `fingerprint` field.

### §3.2 — Read source file frontmatter

From each file's frontmatter, extract: `version`, `status`, any `layer` field,
a one-line `description`. If no frontmatter, infer from filename + content scan.

### §3.3 — Add three manifest entries

Insert these three entries into the `entries` array of `CAPABILITY_MANIFEST.json`.
Insert them in layer order: L4 entries together, then L5. Insert after the last
existing L3.5 entry and before the governance/infra entries at the bottom, OR
group by layer with the other L2.5/L3 entries — follow the existing ordering
pattern in the file.

Entry template for REMEDIAL_CODEX PART1:

```json
{
  "canonical_id": "REMEDIAL_CODEX_v2_0_PART1",
  "path": "04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART1.md",
  "version": "<from frontmatter>",
  "status": "CURRENT",
  "layer": "L4",
  "expose_to_chat": false,
  "representations": ["file"],
  "interface_version": "1.0",
  "fingerprint": "<sha256 computed above>",
  "native_id": "abhisek",
  "gcs_uri": "gs://madhav-marsys-sources/L4/remedial/REMEDIAL_CODEX_v2_0_PART1.md",
  "phase": "M2-D3 Wave5",
  "description": "Remedial prescriptions Part 1: gemstone, mantra, yantra, devata assignments for afflicted/debilitated planets. Source for doc_type=l4_remedial RAG chunks.",
  "downstream_canonical_id": "RETRIEVAL_TOOL_REMEDIAL_CODEX_QUERY"
}
```

Entry template for REMEDIAL_CODEX PART2:

```json
{
  "canonical_id": "REMEDIAL_CODEX_v2_0_PART2",
  "path": "04_REMEDIAL_CODEX/REMEDIAL_CODEX_v2_0_PART2.md",
  "version": "<from frontmatter>",
  "status": "CURRENT",
  "layer": "L4",
  "expose_to_chat": false,
  "representations": ["file"],
  "interface_version": "1.0",
  "fingerprint": "<sha256 computed above>",
  "native_id": "abhisek",
  "gcs_uri": "gs://madhav-marsys-sources/L4/remedial/REMEDIAL_CODEX_v2_0_PART2.md",
  "phase": "M2-D3 Wave5",
  "description": "Remedial prescriptions Part 2: dinacharya, propitiation practices, timing guidance. Source for doc_type=l4_remedial RAG chunks.",
  "downstream_canonical_id": "RETRIEVAL_TOOL_REMEDIAL_CODEX_QUERY"
}
```

Entry template for LIFETIME_TIMELINE:

```json
{
  "canonical_id": "LIFETIME_TIMELINE_v1_0",
  "path": "05_TEMPORAL_ENGINES/LIFETIME_TIMELINE_v1_0.md",
  "version": "1.0",
  "status": "CURRENT",
  "layer": "L5",
  "expose_to_chat": false,
  "representations": ["file"],
  "interface_version": "1.0",
  "fingerprint": "<sha256 computed above>",
  "native_id": "abhisek",
  "gcs_uri": "gs://madhav-marsys-sources/L5/temporal/LIFETIME_TIMELINE_v1_0.md",
  "phase": "M2-D4 Wave5",
  "description": "Lifetime Jyotish timeline: dasha phase arcs, structural inflection points, event windows. Source for doc_type=l5_timeline RAG chunks (9 chunks).",
  "downstream_canonical_id": "RETRIEVAL_TOOL_TIMELINE_QUERY"
}
```

**Adjust field values** (description, version, etc.) based on what you actually
read from the frontmatter. Do not use placeholder values verbatim — they are
templates.

### §3.4 — Update manifest metadata

After adding the three entries:

1. Bump `entry_count`: 106 → 109
2. Bump `manifest_version`: "1.6" → "1.7"
3. Update `last_updated`: "2026-04-30T21:00:00Z" → current timestamp (ISO 8601)
4. Update `last_updated_by`: "KARN-W7-R2-MANIFEST-COMPLETENESS"
5. Recompute `manifest_fingerprint`:
   ```bash
   # The manifest's own fingerprint convention is a descriptive string, not a hash:
   # current value: "d234_bundle_wave5_2026-04-30"
   # new value: "f2_manifest_completeness_w7_2026-04-30"
   ```
   Match the existing convention (descriptive slug, not a SHA).

### §3.5 — Validate JSON

After writing the file:

```bash
python3 -c "import json; data = json.load(open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json')); print(f'Valid JSON: {len(data[\"entries\"])} entries')"
```

Must print `Valid JSON: 109 entries`. If not, fix JSON syntax before proceeding.

### §3.6 — Cross-check source_canonical_ids resolution

Verify that the retrieval tool entries now have resolvable source_canonical_ids:

```bash
python3 - <<'EOF'
import json
manifest = json.load(open('00_ARCHITECTURE/CAPABILITY_MANIFEST.json'))
canonical_ids = {e['canonical_id'] for e in manifest['entries']}
for e in manifest['entries']:
    for src in e.get('source_canonical_ids', []):
        if src not in canonical_ids:
            print(f"UNRESOLVED: {e['canonical_id']} -> {src}")
print("Cross-check complete.")
EOF
```

Must print `Cross-check complete.` with no UNRESOLVED lines.

---

## §4 — Acceptance criteria

| # | Criterion |
|---|---|
| AC.1 | `CAPABILITY_MANIFEST.json` is valid JSON |
| AC.2 | `entry_count` = 109 |
| AC.3 | `manifest_version` = "1.7" |
| AC.4 | `REMEDIAL_CODEX_v2_0_PART1` entry present with correct path + sha256 fingerprint |
| AC.5 | `REMEDIAL_CODEX_v2_0_PART2` entry present with correct path + sha256 fingerprint |
| AC.6 | `LIFETIME_TIMELINE_v1_0` entry present with correct path + sha256 fingerprint |
| AC.7 | All three new entries have `layer` field set (L4 or L5 as appropriate) |
| AC.8 | Cross-check script prints `Cross-check complete.` with zero UNRESOLVED lines |
| AC.9 | No predecessor files (REMEDIAL_CODEX_v1_0_*) added to manifest |
| AC.10 | SESSION_LOG appended with session entry |

---

## §5 — Halt conditions

Stop and report to native if:
- Either REMEDIAL_CODEX v2 file does not exist at the expected path
- LIFETIME_TIMELINE_v1_0.md does not exist at `05_TEMPORAL_ENGINES/`
- `sha256sum` returns different results across two runs (file mutation mid-session)
- JSON validation fails after 2 repair attempts

---

## §6 — Closing summary template

```
=== KARN-W7-R2 CLOSE ===
CAPABILITY_MANIFEST.json:
  version: 1.6 → 1.7
  entry_count: 106 → 109
  Added:
    REMEDIAL_CODEX_v2_0_PART1  (L4, sha256: <first 8 chars>...)
    REMEDIAL_CODEX_v2_0_PART2  (L4, sha256: <first 8 chars>...)
    LIFETIME_TIMELINE_v1_0     (L5, sha256: <first 8 chars>...)
Cross-check: PASS (0 unresolved source_canonical_ids)
JSON valid: 109 entries
SESSION_LOG: appended
```
