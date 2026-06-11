---
artifact: CLAUDECODE_BRIEF_GA_TAJAKA_VARSHAPHAL_WRITER_v1_0.md
canonical_id: GA_TAJAKA_VARSHAPHAL_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN — ga_tajaka activation (the one parked L1 asset)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators)
governing_principle: deterministic accuracy over volume; floors aspirational, not gates
design_sources: A17_A21_SUPPLEMENTARY_SPEC_v1_0.md §5 (l1_tajik_varsha_year_lords table) + A7_DASHAS_SPEC §3/Q4 (Mudda hybrid) + SOURCE_INVENTORY_TAJAKA_v1_0.md (corpus)
depends_on: GA3 (chart_facts schema), GA5 (tajik_hadda_lord, tajik_triraashipathi, Sahams — already built), GA7 (ga_dashas Mudda system — already built), GA8 (aspect_tajik 5 Tajik aspects — already built), bg_texts (Tajaka Neelakanthi corpus), bg_ephemeris (solar-return instants)
---

# GA-Tajaka — Varṣaphal Annual-Chart Writer — Antigravity Execution Brief v1.0

## §0 — What this is (and is NOT)

`ga_tajaka` (Tājaka / Varṣaphal) is the ONE L1 asset deliberately parked: `is_active=false`, `target_table=null`, no writer. This brief activates it. Native ratified building it (2026-06-10) with **A7 hybrid storage**.

**Critical scope distinction — do not conflate two different "Tajik" things:**
- **Already built (do NOT rebuild):** the Mudda / Tajik *annual DASHA* (per-varsha sub-period timing) is System 6 in the GA7 `ga_dashas` writer — inside the 536,471 `chart_dashas` rows. The per-chart Tajik *points* (`tajik_hadda_lord`, `tajik_triraashipathi` year-lord, 70+ Sahams) were built by GA5; the 5 Tajik *aspects* (Ithasala/Eesarpha/Nakta/Yamaya/Manaau) by GA8.
- **This brief builds:** the **Varṣaphal annual CHART** — one solar-return chart per varsha (birthday-to-birthday year): Muntha position, Varṣeśa (year-lord) per varsha with candidate scoring, the applicable Tajik yogas per year, and the annual-chart frame. This is the per-year layer that consumes the already-built Tajik primitives.

## §1 — Reality reconciliation (apply over the older specs)

- **Engine = PyJHora** (`pyjhora_adapter`) for the solar-return instant + annual-chart positions; `bg_ephemeris` / `panchanga_engine` for the exact Sun-return moment per varsha. NO JH-parity oracle; verify by internal consistency + FORENSIC.
- **Asset id = `ga_tajaka`**, layer ganita/L1, sort_order 8. Target table = **`l1_tajik_varsha_year_lords`** (DDL in A17_A21 §5 — create it; it does not exist yet).
- **Postgres-direct. No audience tier. Floors aspirational.**
- **Idempotency: use the L1 pattern** ([[feedback-idempotency-pattern-per-layer]]) — add a `replace_prior_tajik_varsha` helper to `ga_writers/_idempotency.py` scoped to `(chart_id, ayanamsha_id, varsha_year)` and call it before insert. NOT the L0 ON-CONFLICT style.

## §2 — Branch + topology

- Branch `feature/ga-tajaka-varshaphal-writer` off `main` (HEAD `d74aa487`). One PR when green.
- Target chart = **`482012f1-710e-4a25-994a-93821f5871aa`** (canonical). Parameterize; `362f9f17` is the dead phantom.
- Writer lives at `platform/python-sidecar/ga_writers/ga_tajaka_writer.py`; register in `build_runner.py` (and add a `skip_tajaka` flag, consistent with the other writers' argparse).

## §3 — Storage: create `l1_tajik_varsha_year_lords` (A17_A21 §5)

Migration `platform/supabase/migrations/<NEXT>_create_tajik_varsha.sql`:
```sql
CREATE TABLE IF NOT EXISTS l1_tajik_varsha_year_lords (
  varsha_id UUID PRIMARY KEY,
  chart_id UUID NOT NULL, ayanamsha_id TEXT NOT NULL, build_id UUID NOT NULL,
  varsha_year INT NOT NULL,                  -- birth-year-relative (1..N)
  varsha_start_iso TIMESTAMPTZ NOT NULL,     -- exact solar return (Sun returns to natal longitude)
  varsha_end_iso TIMESTAMPTZ NOT NULL,
  year_lord_method TEXT NOT NULL,            -- 'tajik_classical' | 'panchavargiya'
  year_lord TEXT NOT NULL,                   -- Varṣeśa for this varsha
  candidate_lord_jsonb JSONB,                -- 5 candidate lords (Lagnesa/Munthesa/Janma-Lagnesa/Tri-Rashi-pati/Dinaratri-pati) + Panchavargeeya scores
  muntha_position_jsonb JSONB,               -- {sign, house, lord, degree} for this varsha
  applicable_tajik_yogas_array TEXT[],       -- Ithasala/Ishrafa/Nakta/Kambula/Dutthottha fired this year
  classical_source_citation TEXT NOT NULL,
  ephemeris_audit_jsonb JSONB,
  verification_pass_status TEXT NOT NULL,
  citation_ref TEXT NOT NULL, citation_human TEXT NOT NULL, computed_at TIMESTAMPTZ NOT NULL,
  UNIQUE (chart_id, ayanamsha_id, build_id, varsha_year)
);
CREATE INDEX IF NOT EXISTS tajik_varsha_chart_idx ON l1_tajik_varsha_year_lords (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS tajik_varsha_year_idx  ON l1_tajik_varsha_year_lords (chart_id, ayanamsha_id, varsha_year);
```
Reversible down-block; idempotent; `[verify-against: prod]`.

**Atomic-grain note:** the per-varsha row legitimately uses JSONB for the genuinely-composite fields (`candidate_lord_jsonb`, `muntha_position_jsonb`, `candidate scores`) — these are irreducible composites per the atomic-grain rule. `year_lord`, `varsha_year`, `varsha_start/end_iso`, `year_lord_method` are atomic columns (queryable). The atomic-grain gate should accept the JSONB here as sanctioned (document why in code).

## §4 — Hybrid storage (A7 Q4 — the native's chosen model)

Do NOT precompute all 150 varshas. Per the A7 hybrid decision:
- **Precompute: past + current + next 5 years.** For the native (born 1984), current varsha is ~age 42 (2026–27). Precompute roughly birth-year → current+5 (i.e. varsha 1 through ~varsha 47), OR a tighter window if that's heavy — at minimum the **past-to-present + next 5**. Record which window was materialized in the build summary.
- **Rest on-demand:** the retrieval tool computes a missing varsha live when queried (writer exposes a `compute_varsha(chart_id, ayanamsha_id, varsha_year)` callable the tool can invoke). Mark the storage strategy in `volume_explanation`.

Row count: ~1 row per (varsha_year × ayanamsha). Precomputed window ~47 × 5 = ~235 rows. Aspirational, not a gate.

## §5 — What each varsha row computes (the annual chart)

Per varsha, per ayanamsha:
1. **Solar return instant** — the exact moment Sun returns to its natal sidereal longitude in that year (PyJHora / ephemeris root-find). `varsha_start_iso`; `varsha_end_iso` = next year's return.
2. **Muntha** — natal-Lagna + 1 sign per completed year (Muntha advances one sign/year from Lagna). `muntha_position_jsonb` = {sign, house-from-varsha-Lagna, lord, degree}. **This is the FORENSIC-gated value (§7).**
3. **Varṣeśa (year-lord)** — both methods (`year_lord_method`): `tajik_classical` (the strongest of the 5 candidate office-bearers: Lagneśa, Muntheśa, Janma-Lagneśa, Tri-Rāśi-pati, Dina-Rātri-pati) AND `panchavargiya` (Panchavargeeya Bala five-fold strength winner). Emit the candidate set + scores in `candidate_lord_jsonb`; the winning `year_lord` is the atomic column. If the two methods disagree, store both and note it (don't halt — school divergence is data).
4. **Applicable Tajik yogas** — which of Ithasala / Ishrafa / Nakta / Kambula / Dutthottha fire in the annual chart (consume the GA8 `aspect_tajik` logic against the annual positions). `applicable_tajik_yogas_array`.
5. **Citation** — dual form per GA3 §8; `classical_source_citation` cites the Tajaka Neelakanthi corpus (bg_texts; the 333-entry structured corpus per SOURCE_INVENTORY_TAJAKA — chapters 3–4 Varṣeśa/Muntha, 5–6 yogas).

## §6 — Consume what's already built (do not recompute)

- GA5 `tajik_triraashipathi` (Tri-Rāśi year-lord candidate), `tajik_hadda_lord`, Sahams — read from `chart_facts`.
- GA8 `aspect_tajik` (the 5 Tajik aspect computations) — reuse for yoga firing.
- GA7 `ga_dashas` Mudda system — the annual *dasha* is already there; this writer references it for the year-lord cross-check (`varsha_year_lord` field on the Mudda rows), does not recompute it.
- bg_ephemeris — solar-return root-finding.

## §7 — FORENSIC grounding gate (HARD — and closes a known integrity gap)

FORENSIC §22 fixes the native's Varṣaphal anchor: **Muntha = Libra (7th house), Muntha-lord = Venus** for the 2026–27 varsha. The writer's Muntha computation for that varsha MUST reproduce `sign=Libra, house=7, lord=Venus`. Any miss → halt + `CONDUCTOR_HALT_LOG`.

This matters beyond a gate: AUDIT_REPORT_v1_0 documents L2 docs (HEATMAP_VARSHPHAL) *fabricating* "Muntha Taurus/Gemini approximately" against this L1 fact. Building `ga_tajaka` deterministically with the FORENSIC gate **closes that fabrication gap** — the annual chart becomes a computed fact, not a guess.

## §8 — Two-pass verification

`two_pass_verified` minimum: Muntha (sign-advance arithmetic vs independent re-derivation); year-lord (5-candidate scoring vs Panchavargeeya independent calc — both emitted); solar-return instant (root-find vs ephemeris cross-check ±1 min). `divergent_flagged` → halt.

## §9 — Registry activation + count_sql + target_floor

Migration to flip `ga_tajaka`: `is_active=true`, `target_table='l1_tajik_varsha_year_lords'`, `count_sql='SELECT count(*) FROM l1_tajik_varsha_year_lords WHERE chart_id=$1'`, and after build set `target_floor` = achieved canonical count (per the floors=achieved-count rule, like the other 8 — set it in a follow-up UPDATE once the count is known, OR in the same migration if you run the build first). Patch `asset_registry_seed.ts` to match. This makes the cockpit tile go live with a filling bar.

## §10 — Build-state + cockpit

On success update `asset_throughput` for `ga_tajaka` (canonical chart_id) via the shared `_telemetry.py` (the reconciled telemetry path — NOT the old pre-redesign columns). Cockpit tile transitions inactive→lit. Verify on localhost the Gaṇita layer now shows 9 active data assets (ga_tajaka filling) + ga_pyjhora_engine service.

## §11 — Acceptance criteria (all `[verify-against: prod]`)

1. `l1_tajik_varsha_year_lords` created on prod, DDL matches §3. `[\d]`
2. `ga_tajaka` flipped is_active=true with target_table + count_sql; seed patched. `[psql + grep seed]`
3. Varṣaphal rows written for the hybrid window (past→present+5) × 5 ayanamshas for `482012f1`; atomic columns populated, JSONB composites justified. `[psql count + sample]`
4. **FORENSIC: 2026–27 Muntha = Libra 7H, lord Venus** — exact. `[assertion]`
5. Year-lord emitted by BOTH methods (tajik_classical + panchavargiya); divergence stored not halted. `[sample]`
6. Tajik yogas fired per varsha from GA8 aspect_tajik (no recompute). `[sample]`
7. Every row two_pass_verified (zero divergent_flagged). `[GROUP BY verification_pass_status]`
8. Idempotency: `_idempotency.replace_prior_tajik_varsha` added + called; double-run yields single set (add to the idempotency test suite). `[test + prod re-run]`
9. count_sql returns non-zero; target_floor set = achieved count; cockpit tile lit + bar fills. `[localhost cockpit]`
10. CI green; merge-verify (`gh pr view N --json mergeCommit,state`); seed + migration on main.

## §12 — Rails

PyJHora + Postgres-direct; no JH-parity; no tier; atomic-grain (JSONB only for the sanctioned composites); L1 idempotency pattern; floors=achieved-count aspirational; only `482012f1`; surgical migration only; merge-verify before done. Halt on FORENSIC Muntha miss, two-pass divergence, or solar-return root-find failure.

---

*End of GA-Tajaka brief v1.0. Activates the one parked L1 asset: the Varṣaphal annual chart (Muntha/Varṣeśa/Tajik yogas), A7 hybrid storage, FORENSIC Muntha=Libra/Venus gate — closing a documented L2 fabrication gap.*
