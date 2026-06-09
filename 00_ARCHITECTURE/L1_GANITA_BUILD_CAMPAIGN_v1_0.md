---
artifact: L1_GANITA_BUILD_CAMPAIGN_v1_0.md
canonical_id: L1_GANITA_BUILD_CAMPAIGN
version: 1.0
status: CURRENT
authored_by: Claude Code (autonomous, 2026-06-10) — derived from L1_GANITA_BUILD_CAMPAIGN_HANDOFF_v1_0.md
wave: l1-ganita-build
purpose: >
  Execution-mode campaign document for the L1 Gaṇita (chart-facts) layer build.
  Sub-agents read §A (principles), §B (DAG + storage map), §D (context-decay protection),
  §E (gate-validators), §G (aspirational targets). For background / planning rationale,
  see L1_GANITA_BUILD_CAMPAIGN_HANDOFF_v1_0.md.
changelog:
  - v1.0 (2026-06-10): Initial exec-mode doc authored at conductor kickoff.
    Grounded against main HEAD c78c0d45 (Phase 0 complete).
---

# L1 Gaṇita Build Campaign — Execution Document v1.0

## §A — Governing Principles (binding on every sub-agent)

1. **Deterministic accuracy over volume.** L1 is pure computation — Python/PyJHora,
   **zero generative LLM**. Embeddings (deterministic transforms) are fine; nothing else.
2. **Floors are aspirational, NOT gates.** Aspirational targets live in `volume_explanation`
   and are listed in §G below. **Never fabricate a row to hit a number.** **Never halt a build
   for being under a floor.** The only hard gate is integrity (prime directive + FORENSIC +
   two-pass). A session with fewer rows but full integrity **PASSES**; one that hits its target
   with one fabricated value **FAILS**.
3. **PyJHora is the engine.** `natal_engine/` is deleted. No JH-parity oracle — verification is
   internal-consistency + FORENSIC grounding only.
4. **Atomic grain.** Every queryable sub-value is its own row. `fact_value_jsonb` is reserved for
   irreducible composites only (rule: if a `WHERE` clause should be able to match it, it must be
   a column/row, not JSONB). Each JSONB use must be justified in code comments.
5. **No audience tier anywhere.** Strip on sight.
6. **Postgres-direct.** Writers insert via parameterized SQL. No JSONL/markdown dump intermediary.
7. **Canonical chart_id = `482012f1-710e-4a25-994a-93821f5871aa`** (confirmed on prod 2026-06-10;
   only real native row; `asset_throughput` already keyed to it). `362f9f17-…` is a dead phantom —
   the specs use it as placeholder only; **never write it to prod**.
8. **Birth parameters (invariant):** Abhisek Mohanty, 1984-02-05T10:43:00 IST,
   lat 20.27, lon 85.84, tz_offset +5:30, Bhubaneswar, Odisha, India.

---

## §B — DAG and Storage Map

### B.1 — Dependency DAG

```
ga3-chart-facts  (requires: phase0_done external gate)
      │ creates: chart_facts schema, CHART_FACTS_SCHEMA.json, all tables
      │ writers: ga_positions (→ ganita_positions) + ga_strength (→ chart_facts)
      │
      ├──► ga4-panchanga         branch: feature/ga4-panchanga-writer
      │    depends_on: ga3
      │
      ├──► ga5-sensitive         branch: feature/ga5-sensitive-points-writer
      │    depends_on: ga3
      │
      ├──► ga6-vargas            branch: feature/ga6-vargas-writer
      │    depends_on: ga3
      │
      └──► ga7-dashas            branch: feature/ga7-dashas-writer
           depends_on: ga3
                │
                ▼  (all four must pass)
          ga8-structural         branch: feature/ga8-t1-structural-writer
          depends_on: ga3+ga4+ga5+ga6+ga7
                │
                ▼
          ga9-sade-sati          branch: feature/ga9-sade-sati-writer
          depends_on: ga3+ga4+ga6+ga7+ga8
                │
                ▼
          red-team-is8b → wave-close
```

GA3 is **load-bearing** — the wave halts if it fails.
GA4/GA5/GA6/GA7 are **independent of each other** and run in parallel after GA3 passes.
GA8 is the **convergence node** (joins GA3–GA7 rows; no upstream = halt-clean).
GA9 **cross-references everything** (most downstream L1 writer).

### B.2 — Storage Map (which category → which table)

| GA asset      | Categories (A-spec §3 groups)                                  | Target table       | Aspirational target |
|---|---|---|---|
| `ga_positions`  | per-graha core: longitude/sign/nakshatra/pada/speed/dignity/kp | `ganita_positions` | ~50+ rows           |
| `ga_strength`   | shadbala (7 sub-balas), vimsopaka, ishta/kashta, ashtakavarga, bhava_bala | `chart_facts` | ~11,000 rows    |
| `ga_panchanga`  | birth-instant panchanga (5 angas + windows + baselines)        | `chart_facts`      | ~600–800 rows       |
| `ga_sensitive`  | 30 esoteric/Tajik/KP/Nadi/LK categories                        | `chart_facts`      | ~13,000 rows        |
| `ga_vargas`     | 30 vargas × ~25 categories (position/dignity/deity/harmonics)  | `chart_divisionals`| ~78,750 rows        |
| `ga_dashas`     | 7 dasha systems, 4-level Sukshma, KP sub-dimension             | `ganita_dashas`    | ~2.5–3M rows        |
| `ga_strength`   | (GA8 extends) T1 structural: yogas/doshas/aspects/karakatva/argala | `chart_facts`  | ~11,000 (combined)  |
| `ga_sade_sati`  | Sade Sati cycles, phases, overlays, concurrent dashas          | `chart_facts`      | ~875 rows           |

**L2 tables** created by GA3 as **empty DDL only** (L2 Bodha writes them, not L1):
`l25_msr_signals`, `l25_cdlm_cells`, `l25_cgm_nodes`, `l25_cgm_edges`, `l25_rm_resonances`, `l25_ucn_digests`.

---

## §C — FORENSIC Grounding Gate (hard correctness gate)

Every writer asserts the engine's output for the native against these anchors BEFORE any row is
committed. A miss = **halt + CONDUCTOR_HALT_LOG.md + escalate**.

| Anchor | Required value |
|---|---|
| Sun sign | Capricorn (Makara) |
| Moon nakshatra | Purva Bhadrapada (lord Jupiter) |
| Lagna sign | **Aries (Mesha)** — *NOT Scorpio, a known trap* |
| Tithi | Shukla Tritiya |
| Vara | Ravivara |
| Yoga | Shiva |
| Karana | Garaja |

---

## §D — Context-Decay Protection (Conductor instructions for heavy writers)

GA6 (~78K rows) and GA7 (~2.5–3M rows) exceed a single sub-agent context window. For these:

1. **Incremental writes**: GA6 writes one varga at a time; GA7 writes one dasha system at a time.
2. **Idempotent writes**: Each batch is idempotent — a re-kick skips already-written rows (ON
   CONFLICT DO NOTHING, or DELETE WHERE chart_id+system+ayanamsha before re-insert).
3. **Build-state persistence**: After each batch the writer updates `asset_throughput` with the
   running row count so the cockpit bar moves incrementally.
4. **Sub-agent CONTEXT_BUDGET**: If a sub-agent cannot complete a writer in one context window,
   it returns `status: CONTEXT_BUDGET` (partial). The Conductor re-spawns a fresh sub-agent with
   the instruction "resume from last persisted batch". The new agent reads `asset_throughput` to
   find the last completed batch and continues. It does **NOT** restart.
5. **Log tracking**: Each batch completion is appended to `CONDUCTOR_LOG.md` so that a re-paste
   of the kickoff prompt resumes cleanly from the last confirmed batch.

---

## §E — Agent Gate-Validators (run after every writer session)

The Conductor (Sūtradhāra) runs all 6 validators against **PROD** for the canonical chart_id
before marking any session `passed`:

| Validator | What it checks |
|---|---|
| **Pramāṇa** | `SELECT verification_pass_status, count(*) GROUP BY 1` — zero `divergent_flagged`; two-pass categories have zero `single` |
| **FORENSIC** | The 7 §C anchors hold in the written rows |
| **Sambandha** | `constituent_facts_array` / FK refs resolve; no `…_not_computed` sentinels; every dependency-satisfied asset actually has rows |
| **atomic_grain** | Sample JSONB columns — no blob holds a value a `WHERE` should match; each JSONB use is one of the brief's sanctioned-irreducible cases |
| **Darpaṇa** | No-narration linter GREEN (zero `indicates\|suggests\|implies\|means\|denotes`); `drift_detector` GREEN; `G7_only_facts` gate GREEN |
| **Vimarśaka** | (Wave-close only) Full IS.8(b) red-team — no class-1 findings; class-2 carry remediation plans |

**Failure protocol**: Failed validator → mark session `failed` → append to `CONDUCTOR_HALT_LOG.md`
with specific failure → re-spawn sub-agent (up to `max_fix_attempts: 5`). On exhaustion → HALT.

---

## §F — Tables Already on Prod (Phase 0, main HEAD c78c0d45)

Migration 204 created `chart_facts` (18 columns). Migration 205 created the `ga_1_pyjhora_service`
asset entry. The following tables were created prior to Phase 0 and are on prod:
`ganita_positions`, `ganita_dashas`, `chart_divisionals`.

Each GA writer must **verify the target table's DDL matches its spec** before writing; if Phase 0's
version diverges, the writer authors a corrective migration first.

---

## §G — Aspirational Targets (informational — NOT gates)

Floors set in `asset_registry.target_floor` = the REAL achieved count so the cockpit reads 100%.
The numbers below are the "aspired M" in `volume_explanation`.

| Asset      | Table              | Aspirational row count  | Structural driver                              |
|---|---|---|---|
| ga_positions   | ganita_positions   | 50+ (core); ~230+ full | 5 ay × 10 bodies core → extend to 23 bodies    |
| ga_strength    | chart_facts        | ~11,000                 | shadbala 7×7 + ashtakavarga 96 cells + bhava  |
| ga_panchanga   | chart_facts        | ~600–800                | ~33 A4 categories × INVARIANT + 5-ay partials |
| ga_sensitive   | chart_facts        | ~13,000                 | 30 A5 categories × 5 ay                        |
| ga_vargas      | chart_divisionals  | ~78,750                 | 30 vargas × 25 bodies × 5 ay + categories      |
| ga_dashas      | ganita_dashas      | ~2.5–3M                 | 7 systems × 4-level Sukshma, 1950–2100         |
| ga_strength    | chart_facts        | ~11,000 (combined w/GA3)| GA8 extends; no double-count                   |
| ga_sade_sati   | chart_facts        | ~875                    | ~15 categories × cycles/phases × 5 ay          |

---

## §H — Open Questions (resolved at campaign kickoff 2026-06-10)

| Question | Resolution |
|---|---|
| Autonomy | AUTONOMOUS_MODE — no human gates between GA3 and wave-close |
| WS2 disposition | Port WS2 computation depth into the registry spine; discard A1–A22 numbering |
| `forensic` asset | 0-row stub; out of this campaign's scope (follow-on) |
| Scope ceiling | L1 only; L0-tail follow-ons in separate session |

---

*End of L1_GANITA_BUILD_CAMPAIGN_v1_0.md. Exec-mode doc — derived from HANDOFF v1.0 (2026-06-09).
Background rationale: L1_GANITA_BUILD_CAMPAIGN_HANDOFF_v1_0.md.*
