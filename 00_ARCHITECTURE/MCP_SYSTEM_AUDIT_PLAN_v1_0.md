---
canonical_id: MCP_SYSTEM_AUDIT_PLAN
version: 1.0
status: DRAFT-FOR-REVIEW — the exhaustive 360° system-audit plan; we iterate on this before executing
created: 2026-07-01
author: Cowork (planning) — for native Abhisek Mohanty
classification: audit plan (system + astrological + UX), executed via the LIVE MCP connector
instrument: this Cowork conversation is connected to prod amjis-mcp (45 tools) — the audit is run FROM here,
  as a real external LLM client, exercising the whole chain end-to-end.
seed_findings: project_mcp_system_audit (5 defect classes already surfaced by grounding probes)
scope_note: DELIBERATELY OPEN — the native expects the surface area to grow as we audit. New axes/assets/
  findings get appended; this plan is a living checklist, not a fixed list.
changelog:
  - v1.0 (2026-07-01): First exhaustive draft. 8 audit dimensions (A–H), asset+tool coverage matrices,
    3 ground-truth-verified defect clusters seeded, execution model + findings-register schema.
---

# MCP SYSTEM AUDIT — 360° EXHAUSTIVE PLAN (v1.0, draft for review)

> **Goal.** A complete, acharya-grade audit of the entire MARSYS-JIS system as reachable through the MCP: is
> every data asset complete, retrievable, and correctly served? Do the ground principles hold in the served
> output (not just in the code)? Is the experience efficient, productive, and does it synthesize acharya-grade
> insight? Throughout, we continuously log opportunities for correction / improvement / optimization across
> THREE lenses: **system** (wiring, schema, perf), **astrological** (correctness, completeness, depth), and
> **UI/UX** (tool ergonomics, response shape, discoverability, synthesis quality).
>
> **Method.** Run FROM the live MCP connector in this conversation. Every claim is a real tool call with a real
> response, logged. We probe, we read the output critically as an acharya would, and we register findings. This
> plan is the checklist; execution fills the findings register.

## §0 — What the grounding probes already proved (so the plan starts grounded, not blank)

The data is RICH and largely built (`get_chart_quality`: 64,765 MSR signals, 140 CGM nodes, 365 CGM edges,
70 CDLM cells, 94.91% two-pass verified) — but multiple SERVING paths are broken. Five defect classes already
found in ~8 probes (detail in `project_mcp_system_audit` memory):
1. **Runtime-registration gaps** — `list_assets` 404 (resource not registered; D-B family, beyond PR #372).
2. **Surgical-whitelist omissions** — `query_remedies` rejected (D-C family; likely all 7 remedy tools).
3. **Cockpit-route auth gap** — `asset_registry_all` → `/api/cockpit/registry` 401 (new auth-surface class).
4. **L4 Phala schema-drift bugs** — `phala_outlook`: all 4 subsystems error (missing columns `id`/`anchor_id`,
   PL/pgSQL `candidate_time` field gone, `panchanga_daily` relation missing). Live prod SQL/function bugs.
5. **The signals-exist-but-serve-empty contradiction** — scorecard sees 64,765 signals; `get_signals` returns
   0. The deepest finding: the read path returns nothing though the table is populated. Root-cause TBD (orphan
   join filtering everything vs. a serving-query bug). Plus an ayanamsha inconsistency (LAHIRI vs
   lahiri_chitrapaksha) between orientation and scorecard.

This tells us the audit must be SYSTEMATIC across all 45 tools + all assets — spot-checks would miss most of it.

## §1 — The eight audit dimensions (A–H)

### A — Retrievability (does every tool WORK?)
Call all 45 tools with valid inputs on an entitled chart. Classify each: ✅ returns real data · ⬛ returns
empty (200 but no content) · ❌ errors (404/401/400/500). For every non-✅, root-cause the class (registration
/ whitelist / auth / schema / data). Deliverable: a 45-row tool-status matrix. (Seed: ~5 already ❌/⬛.)

### B — Completeness of information (is every ASSET represented + fully populated?)
Enumerate all ~81 build assets L0–L5 (from asset_registry once reachable). For each asset: is it exposed
through some MCP tool/resource? Does that tool return the FULL asset (row counts vs. target_floor / vs. the
scorecard's known counts)? Flag: assets with NO retrieval surface (unreachable data), assets served partially
(truncation/pagination gaps), assets whose live count ≠ expected. Cross-check against the L1–L5 seal records'
canonical counts (chart_facts=27,554; dashas=536,471; divisionals=21,635; MSR 64,765; etc.).

### C — Retrieval correctness & grounding (do the GROUND PRINCIPLES hold in the OUTPUT?)
Not "is it in the code" — "does the served response obey them":
- **§N.5 reference-don't-restate / B.3 derivation ledger:** do signals carry `constituent_facts_array` that
  RESOLVE to real chart_facts? (Seed: 91.5% orphan — the D-A blocker. Quantify per tool.)
- **B.1 facts/interpretation separation:** does L1 data come back as fact (with fact_id), L2+ as interpretation
  citing those facts — no layer collapse in the output?
- **B.11 whole-chart-read:** does get_chart_orientation actually gate/precede domain reads, and is the
  orientation non-empty when it should be?
- **Chart-agnostic #14:** re-probe every chart-scoped tool on a NON-native chart — any native leakage in data,
  fallback, or description? (Regression-guard the whole M0/M0.5 contamination work.)
- **B.10 no fabricated computation:** are numbers cited to a deterministic source (ephemeris provenance seen —
  good), never invented?

### D — Astrological correctness & depth (the ACHARYA lens)
Read the actual astrological CONTENT critically, chart by chart, for the 4 entitled charts:
- Are the natal facts correct (positions, dignities, dashas match the known FORENSIC anchors for 482012f1 —
  Sun Capricorn, Moon Purva Bhadrapada, Lagna Aries, etc.)?
- Are the yogas/signals classically valid — right rule, right houses, right lords? Any spurious or missing yoga?
- Is the synthesis (domain readings, reasoning-units assess_*) acharya-grade — does it reconcile contradictions,
  weight by strength, and read the whole chart — or is it generic/list-like?
- Do dasha/transit (L3) and prediction (L4) outputs make classical sense and carry falsifiers (B.3)?
- Remedies (L0 corpus): classically attested, source-cited, domain-appropriate?
This dimension needs the data-serving fixed first (much is empty now) — but we audit what IS served, and log
astrological gaps as we go.

### E — Synthesis & reasoning-unit quality (the "SUPERLATIVE insight" test / G10)
The reasoning-unit tools (assess_marriage/career/health/wealth, yoga_activation_by_dasha) are the product's
apex. Once data serves: do they produce a reconciled, cited, prioritized VERDICT (not ingredients dumped)? Do
they surface convergence + contradiction? Is it the level an acharya would call "my own level or above"?

### F — UX / ergonomics / discoverability (the CLIENT-EXPERIENCE lens)
As the connecting LLM, is this pleasant + efficient to use?
- Tool descriptions: intent-rich enough to select correctly? (Seed: they're strong — acharya-grade, enforce
  B.11.) Any misleading ones? (Seed: 2 "chart-agnostic" comments were wrong.)
- Response shape: outputSchema + structuredContent + text fallback present? Token-bounded? response_format
  verbosity working? Names not raw UUIDs? Pagination usable?
- Workflow: is list_my_charts → select_chart → orient → domain a smooth path? Redundant/overlapping tools?
  Missing tools an acharya would want? Error messages actionable (do they tell the client how to self-correct)?
- Per-model surface (M6): does declared→profiled actually differ + help?

### G — Performance & robustness
Latency per tool (esp. sidecar-backed + bundle SSE); pagination correctness on large assets (dashas=536k);
graceful degradation (does a sidecar/subsystem failure return a clean error, as phala_outlook does, or crash?);
rate-limit behavior; concurrent/multi-chart isolation under load.

### H — Cross-cutting integrity & governance
Ayanamsha consistency across tools (seed: LAHIRI vs lahiri_chitrapaksha mismatch); provenance envelopes present
+ honest; the scorecard's own FALSE-PASS self-report (defect_001) — are there other false-passes?; asset
counts in health/scorecard vs. reality; the 3 REQUEST-filed sidecar tools' status.

## §2 — Coverage matrices (filled during execution)

**Tool matrix (45 rows):** tool | layer | input used | result (✅/⬛/❌) | defect class | astrological note | UX note.
**Asset matrix (~81 rows):** asset_id | layer | retrieval surface (which tool) | reachable? | complete? (count
vs expected) | grounding-resolves? | notes.

## §3 — Findings register (the running output — 3 lenses per finding)
Each finding: `ID | dimension(A–H) | severity (CRIT/HIGH/MED/LOW) | lens (system/astro/UX) | evidence (the tool
call + response) | root-cause | recommended fix | owner (MCP / retrieval-fork / L-layer / data)`. Severity +
owner let us triage into fix-waves at the end. Seed findings from §0 pre-loaded as F-001…F-005.

## §4 — Execution model
- Run in DIMENSION ORDER but opportunistically: A (retrievability sweep, all 45) first — it maps the terrain
  and tells us what's even testable. Then B (completeness), C (grounding), D/E (astrological + synthesis — gated
  on data serving), F (UX, continuous), G (perf), H (integrity, continuous).
- Every probe is a real MCP call logged with its response. No assertion without evidence.
- We batch related probes, checkpoint findings into the register after each dimension, and PAUSE for your review
  at dimension boundaries (this is collaborative — you'll spot astrological things I'd miss).
- At the end: the findings register → a prioritized FIX-WAVE plan (mirroring the M-series briefs), split by
  owner, with the CRIT/HIGH items (the empty-serve root cause, phala schema drift, MSR resolution) first.

## §5 — Open questions for you (shape the plan before we run)
1. **Depth of the astrological lens (D/E):** how deep do you want the correctness read — full manual acharya
   review of each chart's yogas/synthesis (slow, deep), or a representative sample per domain first?
2. **Fix-as-we-go vs. audit-then-fix:** log everything and fix in waves at the end (cleaner), or fix trivial
   blockers mid-audit so later dimensions become testable (e.g. the whitelist/registration one-liners that are
   currently hiding whole tool families)?
3. **Scope of charts:** all 4 entitled charts, or focus depth on the native 482012f1 + one non-native for the
   chart-agnostic guard?
4. **Anything I've MISSED as a dimension** — you said you're not naming everything; is there an axis (cost,
   security posture, multi-user concurrency, specific astrological systems like Jaimini/KP/divisionals coverage)
   you want as its own dimension?

*End of MCP_SYSTEM_AUDIT_PLAN v1.0 (draft). We refine §1/§5 together, then execute §4 filling §2/§3.*
