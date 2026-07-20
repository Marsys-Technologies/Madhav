---
lane: S-1
wave: PG-1
title: Signal editorial sizing — is bodha_msr_signals text actually unreadable?
status: CLOSED
date: 2026-07-19
---

# PG1 Lane S-1 — Signal editorial sizing

## Scope
Read-only DB (mcp__postgres__query, SELECT-only) audit of `bodha_msr_signals` for
canonical chart `482012f1-710e-4a25-994a-93821f5871aa`, plus a grep-and-read of
`00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` for assumptions A-30
and A-32. No writes outside this lane's two designated files. No app/MCP-server
code was inspected — DB and live MCP tool surface only.

## Headline finding
**§13.6's premise is confirmed, not merely assumed.** The 20-row unweighted
sample (LIMIT 20, arrival order) of `signal_headline_text` /
`signal_summary_text` is 20-for-20 raw internal register — deterministic
`category=... | key=... | value_num=...` renders of config keys, internal
metric names (`graha_yuddha_per_varga`, `house_bhava_bala_subscore`,
`graha_centrality:degree_centrality`), varga codes (D2/D6/D12/D20/D21), and in
one case an internal methodological caveat baked straight into the served
text (`varga_assumption=physical_phenomenon_extended_to_mathematical_varga`).
This reads closer to a debug/audit log line than to any register a layperson
could parse. Nothing in the sample is closer to plain language than anything
else — there is no "easy 30%" hiding in the corpus that would shrink the
workstream. The architecture doc's own §16.6 table (line 2674) already
reached this verdict from the migration/schema comments; this lane
corroborates it against live production data end-to-end.

**Mitigating finding (PG1-S1-0002):** the corpus is heavily concentrated by
`signal_type_id` — the top 10 types cover >21,000 of 49,705 rows for this one
chart. If the eventual fix is a per-`signal_type_id` NL template rather than
per-row hand-authoring, the effort driver is "how many distinct
`signal_type_id` values exist chart-wide" (not sampled — recommend
`SELECT count(DISTINCT signal_type_id) FROM bodha_msr_signals` as the actual
sizing query), not the 49,705 row count. This does not shrink the workstream
to trivial — acharya-grade (§J) phrasing per template is still real editorial
work — but it reframes the sizing unit correctly.

## Citation-frequency priority list (§19 P5') — UNVERIFIABLE
No `message_parts` child-row table exists. `conversation_messages` stores
whatever citation structure exists inline in a `parts_json` JSONB blob (7
columns total: id, conversation_id, parent_message_id, role, parts_json,
metadata_json, created_at) — consistent with the architecture doc's own
finding that A-08 (structured `message_parts` rows) is itself still-pending
target-architecture work. A full-table `ILIKE` scan of `parts_json` for
`signal_id`, `"kind":"signal"`, and `bodha_msr_signals` returned **zero**
matching rows across the entire table. Either no conversation has ever cited
an MSR signal by id, or citations are shaped differently than these three
probes assumed — this lane cannot distinguish the two without app-code
access (out of scope; DB/MCP read-only). **A top-50 citation-frequency
priority list cannot be produced from currently queryable data.** Recommend
substituting a row-volume-based or domain-relevance-based prioritization
heuristic for §19 P5' until/unless a code-scoped lane locates a citation
linkage.

## A-30 / A-32 verdicts — UNVERIFIABLE (out of this lane's scope)
- **A-30** (§14.6, minimum-n gated calibration, collect-only phase) concerns
  the calibration/serving loop-back, not signal-text readability. Orthogonal
  to this lane's charge; the document's own §14.6/§16.6 self-assessment
  already states the underlying problem (n=7 Brier precision theater) is
  real and A-30 is the proposed (not yet built) fix. No calibration table was
  queried by this lane.
- **A-32** (§14.8, disagreement captured as first-class rows) concerns
  conversational dispute/correction capture. The doc's own §16.6 already
  marks this ABSENT/stubbed (F-25c: feedback UI silently discards). This
  lane found no dispute/correction column in `conversation_messages`'s
  7-column schema, but did not exhaustively probe `metadata_json` shape —
  recommend routing full A-32 verification to a lane scoped to that table's
  feedback-endpoint interaction.

Both are reported as `unverifiable` (empty evidence, per the findings-format
rule) rather than given a false verdict — folding them into a
signal-editorial-sizing lane's evidence would overreach past what this lane
actually queried.

## Findings summary
5 findings in `pg1_findings_S-1.jsonl`:
- PG1-S1-0001 (confirmed, high) — §13.6 unreadability confirmed against live data.
- PG1-S1-0002 (confirmed, medium) — sizing unit should be `signal_type_id` count, not row count.
- PG1-S1-0003 (unverifiable, high) — no queryable citation linkage exists for §19 P5' prioritization.
- PG1-S1-0004 (unverifiable, informational) — A-30 out of this lane's evidentiary scope.
- PG1-S1-0005 (unverifiable, informational) — A-32 out of this lane's evidentiary scope.
