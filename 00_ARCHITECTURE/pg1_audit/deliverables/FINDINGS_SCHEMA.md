# pg1_findings.jsonl schema (Lane A-0)

One JSON object per line, append-only. Every lane appends ONLY to its own
`00_ARCHITECTURE/pg1_audit/deliverables/pg1_findings_<lane>.jsonl` shard
(avoids write contention across parallel lanes); Z-1 concatenates all shards
into the canonical `pg1_findings.jsonl` at synthesis time.

```json
{"id":"PG1-0001","lane":"C-1","assumption":"A13",
 "class":"stale|confirmed|partial|unverifiable|new_defect",
 "claim":"...","reality":"...",
 "evidence":[{"file":"...","line":123,"quote":"..."}],
 "severity":"critical|high|medium|low|informational",
 "affects":["§16.1 F-04"],"recommended_action":"...","confidence":"high|medium|low"}
```

Rules (validated by `scripts/validate_findings.py`):
- `evidence` MUST be a non-empty array with at least one `{file,line}` pair for
  any `class` other than `unverifiable`.
- `id` MUST be unique within a shard and prefixed `PG1-` + zero-padded 4-digit
  sequence, lane-scoped (e.g. `PG1-C1-0001`) to guarantee uniqueness across
  shards without coordination.
- `assumption` is one of `A1`..`A32`, or `NEW` for a defect not tied to a
  numbered assumption (goes to Z-1's `F-` sequence instead).
