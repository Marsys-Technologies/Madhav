---
artifact: CLAUDECODE_BRIEF_GA8_STRUCTURAL_ENUMERATION_v2_0.md
canonical_id: GA8_STRUCTURAL_ENUMERATION_BRIEF
version: 2.0
status: CURRENT
supersedes: CLAUDECODE_BRIEF_GA8_T1_STRUCTURAL_WRITER_v1_0.md (the predicate-firing model — DEAD)
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
governing_decision: 00_ARCHITECTURE/L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md (B.1 + SIG.MSR.377 purged from reasoning)
target_writer: platform/python-sidecar/ga_writers/ga_structural_writer.py (REBUILD — reopens sealed L1; native-approved)
data_plane: ALWAYS prod via Cloud SQL proxy — never local Postgres
delivery_model: branch + plan-then-execute; surgical migrations one at a time, tracker rows
---

# GA8 — Structural Enumeration Rebuild — Execution Brief v2.0

## §0 — Why v2.0 supersedes v1.0 (read first)

The v1.0 GA8 brief described `ga_structural` as a **predicate-firing writer** — "fire-check all 200+
G12 yogas," evaluate a catalog against the chart. **That model is DEAD** (governing decision
`L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0`). Two legacy artifacts were driving it and are PURGED
from the reasoning: PROJECT_ARCHITECTURE **§B.1** (legacy governance — the source of the L1/L2
ambiguity) and **SIG.MSR.377** (a historical note about data that no longer exists). Do not reason
from either.

**The new model — ga_structural is the SOLE deterministic relationship-ENUMERATION engine in L1:**
- It generates the chart's complete relational fabric by **EXHAUSTIVE ENUMERATION**, not predicate
  matching. (It already does this for D1 aspects/argala/dispositors — `for graha in grahas`,
  every-sign × every-sign. We extend that method to all vargas; we do NOT introduce predicates.)
- **Named yogas/doshas are a LABEL over the enumeration**, sourced from the L0 catalog — never a
  gate. A configuration with no classical name is STILL recorded.
- **No predicate registry. No hardcoded 24-yoga / 15-dosha lists. No G52 firing.** A predicate
  system is bounded by its catalog and can never cover all of a native's relationships; enumeration
  is complete by the chart's own finite combinatorics.
- MSR (L2) does NOT re-fire — it projects this fabric + adds population-level significance. GA8 owns
  the fabric; MSR owns rank/convergence/contradiction/domain-salience.

## §1 — Scope of THIS brief (Option B — static fabric only; native-decided 2026-06-12)

**IN SCOPE — the static multi-varga relational fabric:**
- Exhaustive enumeration of, across **all 16 shodasha vargas (D1…D60) × all 5 ayanamshas**:
  - **Aspects** (Parāśarī graha-drishti + Jaimini rāśi-drishti + Tājik) — every graha to every
    graha/house, full matrix, per varga.
  - **Conjunctions** — every graha pair within orb, per varga.
  - **Dispositor chains** — to terminus, per varga (D9/D10 chains are first-class, not D1-only).
  - **Parivartana / mutual reception** — per varga.
  - **Dignity / placement state** — every graha's dignity, per varga (this is what vargas are FOR).
  - **Vargottama / cross-varga sameness** — inherently multi-varga (same sign across charts).
  - **Argala / virodha-argala** matrices — per varga.
  - **Avasthas, composite states, functional class, karakatva** — per varga where classically defined.
- **Named-pattern LABELS** — where an enumerated configuration matches an L0 `brahma_yoga_catalog` /
  `brahma_dosha_catalog` definition (via its `formation_rule_jsonb`), attach the name + citation.
  Unmatched configurations are STILL stored as structural relationships.

**OUT OF SCOPE — deferred (do NOT build here):**
- **Dasha-temporal activation** (when a relationship is active/dormant by period) — a SEPARATE pass,
  likely **L3 Kāla** (the time layer), not L1. ga_structural is the STATIC fabric only.
- MSR/L2 population enrichment (rank, convergence, contradiction, domain-salience) — that's bo_laksana.

## §2 — The three rebuild requirements (what changes in ga_structural_writer.py)

### R1 — Expand enumeration from D1-only to all 16 vargas
Today the writer enumerates aspects/conjunctions/dispositors on **D1 only**, and merely
*checks-existence* of `chart_divisionals` (line ~548) without reading it. **Change:** read the varga
positions from `chart_divisionals` (GA6 already computes all 30 vargas) and run the SAME enumeration
loops per varga × per ayanamsha. Keep the existing enumeration logic; parameterize it by varga.
(Note: GA6 computes 30 vargas; this brief's aspect/conjunction enumeration targets the 16 shodasha
vargas — confirm the varga set with the native if GA6's extra 14 should also carry aspects.)

### R2 — Named patterns become a LABEL pass over enumeration, sourced from L0
Remove the hardcoded `YOGA_LIBRARY` (24) and `DOSHA_LIBRARY` (15). Replace with: after enumeration,
for each enumerated configuration, look up `brahma_yoga_catalog.formation_rule_jsonb` /
`brahma_dosha_catalog` — if a definition matches, attach `classical_name` + `classical_citation` +
`source_chunk_ids` to that relationship row. **The label NEVER decides whether the row exists** — the
enumerated relationship is always stored; the name is an optional column. Configurations with no
catalog match get an explicit `classical_name = NULL` / `uncatalogued = true` marker (so absence is
queryable, never silent).

### R3 — Real fact_id references (drop _mock_fact_id_ref)
`_mock_fact_id_ref` produces references that do NOT resolve to real `chart_facts` rows (it hardcodes
`key='rupa'`, `chart_prefix`, `build_id='ga3_build'`). **Replace every call with the real `_fact_id`
formula** (`sha256("{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}")[:16]`) so
`constituent_facts_array` resolves to actual upstream rows. This restores the L1-authority spine.

## §3 — DISAMBIGUATION (hard requirement — native-flagged)

**Every relationship row MUST be fully qualified.** "Jupiter-Venus conjunction" alone is a defect.
Each row carries: **`varga` (D1/D9/D10/…) + `sign` + `ayanamsha_id` + the houses/degrees/orb
involved.** So:
- "Jupiter-Venus conjunction in **D1, Sagittarius, lahiri**" is a DISTINCT row from
- "Jupiter-Venus conjunction in **D9, Virgo, lahiri**" — different `varga` + `sign` ⇒ different row,
  different `fact_id`.
The `fact_category`/`fact_subject`/`fact_key` grammar must encode varga + the participating bodies;
`fact_value_jsonb` carries sign/house/degree/orb. **No relationship row without full
varga + sign + ayanamsha + position context.** A row that can't say which varga and sign it lives in
fails the build.

## §4 — Two-pass verification moves HERE
Verification belongs where computation happens. GA8 runs two-pass on every enumerated relationship:
(1) engine enumeration; (2) independent re-derivation of the geometric/lordship rule; divergence →
`divergent_flagged` → HALT. (No JH-parity oracle — internal consistency + classical re-derivation +
FORENSIC grounding only.) The label pass is verified against the L0 catalog match.

## §5 — Orchestrator conformance (FROZEN contract — embed verbatim, do NOT extend)
GA8 stays a `@register('ga_structural')` `WriterBase` subclass on the FROZEN contract. It will be
HEAVY (16 vargas × 5 ayanamshas) → use `plan_substeps` (e.g. per-ayanamsha or per-varga sub-steps) +
`run_substep`. Runs on `ctx.db_conn`, never commits/closes; no `asset_throughput` writes; reads
`chart_id`/`birth_params` from `ctx.config`; per-chart delete-then-insert idempotency scoped to the
sub-step key; FORENSIC asserts guarded `if chart_id == CANONICAL_CHART_ID`. **No orchestrator change.**

## §6 — Floors + completeness
Floors aspirational. Expected static-fabric volume ~50–120k rows/native (16 vargas × 5 ayanamshas ×
~45 graha-pairs + dispositors/dignity/vargottama). Set `target_floor` = achieved count after build.
**No threshold drop** — weak/wide-orb relationships emitted with a low strength value, never dropped.
Completeness self-check: emit a build-time coverage line ("N relationships enumerated, M named, K
uncatalogued") so completeness is measurable.

## §7 — Acceptance criteria  [verify-against: prod]
- [ ] Aspects + conjunctions enumerated across all 16 vargas × 5 ayanamshas (not D1-only). `[verify: psql_prod count by varga]`
- [ ] Every relationship row carries varga + sign + ayanamsha + position; no unqualified rows. `[verify: psql_prod — assert no NULL varga/sign on relationship categories]`
- [ ] No `YOGA_LIBRARY`/`DOSHA_LIBRARY` hardcode remains; named patterns sourced from `brahma_yoga_catalog`; uncatalogued configs stored with `classical_name NULL`/`uncatalogued` flag. `[verify: grep writer + psql_prod]`
- [ ] `_mock_fact_id_ref` removed; `constituent_facts_array` resolves to real chart_facts rows. `[verify: psql_prod join test — every referenced fact_id exists]`
- [ ] Two-pass verification present; zero `divergent_flagged`. `[verify: build log]`
- [ ] FORENSIC native anchors still pass (guarded to native chart). `[verify: build log]`
- [ ] Orchestrator builds it heavy with sub-step heartbeats; no contract change. `[verify: SSE + git diff orchestrator = none]`
- [ ] Dasha-temporal NOT built here (deferred to L3 Kāla). `[verify: no dasha-window rows]`

## §8 — Out of scope / do NOT touch
The other 8 ga_ writers; the FROZEN orchestrator; MSR/bo_laksana (separate brief — already respecced
to projection in A10 v1.2); the dasha-temporal layer (L3 Kāla). This brief rebuilds ga_structural's
internal logic ONLY.

---
*End of GA8_STRUCTURAL_ENUMERATION_BRIEF v2.0. ga_structural becomes the sole exhaustive relationship-
enumeration engine across all 16 vargas × 5 ayanamshas, fully disambiguated, named-by-label-not-gate
from L0, real fact_ids, two-pass here, dasha-temporal deferred to L3. Supersedes the dead predicate-
firing v1.0 brief.*
