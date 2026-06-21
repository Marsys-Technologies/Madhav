---
artifact: CLAUDECODE_BRIEF_GA7_DASHAS_WRITER_v1_0.md
canonical_id: GA7_DASHAS_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous conductor sub-agent)
campaign: L1_GANITA_BUILD_CAMPAIGN_v1_0 (Wave 3, asset ga_dashas — largest by absolute row count)
delivery_model: 1 branch, plan-then-execute, no human gate (agent gate-validators per campaign §E)
governing_principle: deterministic accuracy over volume; floors are aspirational targets, not gates
design_source: 00_ARCHITECTURE/A7_DASHAS_SPEC_v1_0.md (LOCKED — system + schema authority)
depends_on: GA3 (chart_dashas schema), G15 dasha-system rule library, G24 Vimshottari starting-lord, G2 ephemeris (transit overlays), G12 yoga library
---

# GA7 — Dashas Writer — Antigravity Execution Brief v1.0

## §0 — Read first (authoritative design sources)

- `00_ARCHITECTURE/A7_DASHAS_SPEC_v1_0.md` — **the system + schema authority.** 7 acharya-selected systems (§3), chart_dashas row schema + 13 additions (§4), KP sub-divisions (§5), calculation window 1950–2100 (§6), per-system two-pass methodology (§7), dual citations (§8), row counts (§9), tool contract (§10), no MVs (§11).
- `00_ARCHITECTURE/GA3_CHART_FACTS_WRITER_v1_0.md` — `chart_dashas` table (A3 §8) + atomic grain + prime directive + FORENSIC gate.
- `00_ARCHITECTURE/L1_GANITA_BUILD_CAMPAIGN_v1_0.md` — §D conductor (context-decay protection is critical — millions of rows), §E gate-validators.

## §1 — Reality reconciliation (TWO binding overrides + naming/engine)

A7 LOCKED 2026-05-29, before the engine decision AND before the depth decision. **Apply these — they override the spec:**

1. **DEPTH = 4-level Sukshma, NOT the spec's 5-level Prana.** A7 §1/§13 says Prana (5 levels: Maha→Antar→Pratyantar→Sookshma→Prana). **The campaign + native ratified 4-level Sukshma** (Maha→Antar→Pratyantar→Sookshma; `level_n` 1–4). Drop the L5 Prana level. The `chart_dashas` table still supports `level_n` up to 5 (don't alter the schema) — the writer simply stops at `level_n=4`. This is the single most important override: it cuts the row count from the spec's ~5.4M toward the campaign target **~2.5–3M per chart**.
2. **KP = a SEPARATE `kp_sublevel` dimension, NOT extra `level_n=6/7` rows.** A7 §5 models KP sub/sub-sub as `level_n=6/7`. The campaign decision (native-ratified) is KP as its **own dimension** — emit KP sub-period rows under Vimshottari keyed by a distinct `kp_sublevel` marker (sub / sub-sub), not by inflating `level_n`. Keep KP queryable independently of the Vimshottari 4-level hierarchy. Confirm the `chart_dashas` columns support this (a `kp_sub_lord`/`kp_sub_sub_lord` pair + a dimension flag); add via migration if GA3 didn't.
3. **Engine = PyJHora** (`pyjhora_adapter`) for nakshatra-elapsed + graha longitudes + Jaimini sign-progression, not `natal_engine`. **No JH-parity oracle** — two-pass is engine-vs-independent-classical-re-derivation + algebraic invariants (sums: Vimshottari=120y, Yogini=36y, Ashtottari=108y, Naisargika=120y).
4. **Asset id = `ga_dashas`.** Target table = **`ganita_dashas`** (the campaign storage map). Verify its columns match A3 §8 + A7 §4 additions; extend via migration if needed. (A3 §8 names the table `chart_dashas`; the campaign uses `ganita_dashas` — confirm which exists on prod and target that one; if both/neither, halt-and-report.)
5. **Postgres-direct. No audience tier. Floors aspirational** — the ~2.5–3M target is chased with genuine deterministic timeline rows; never fabricate periods to hit a count.

## §2 — Branch + topology

- Branch `feature/ga7-dashas-writer` off `main` **after GA3 merges**. One PR when green.
- Target chart_id = **`482012f1-710e-4a25-994a-93821f5871aa`** (canonical; keyed). Parameterize. `362f9f17` dead — specs' examples are placeholders.
- **Largest writer by absolute rows (~2.5–3M).** Conductor context-decay protection (campaign §D) is mandatory: build **one system at a time** across sub-agent re-kicks; persist per-system completion to build-state; write incrementally + idempotently so a re-kick resumes mid-campaign. Never hold a full system's timeline in one context window.

## §3 — The 7 systems (A7 §3 — all 7, none added/dropped)

`vimshottari` (120y, 9 lords — universal default, + KP sub-dimension), `yogini` (36y, 8 yoginis), `ashtottari` (108y, 8 lords), `chara_karaka` (Jaimini sign-based), `naisargika` (age-based, 120y brackets), `mudda` (Tajik annual — hybrid storage: past+current+next-5y precomputed, rest on demand per A7 Q4), `kalachakra` (BPHS Ch.53, paramayush-anchored).

## §4 — Row schema (A7 §4 — base + 13 additions)

Use the `ganita_dashas`/chart_dashas A3 §8 base fields + the A7 §4 additions for the **13 included** row-enrichments (A,B,C,D,E,F,G,H,I,J,K,Q — M/N/O/P skipped):
- Lord natal context inline (A): `lord_natal_house_d1`, `_sign`, `_nakshatra`, `_dignity_d1`, `_shadbala_total`.
- Sandhi-next (B): `sandhi_with_next_dasha_lord`, `next_dasha_start_iso`. Sandhi flag default 5% (A7 Q8).
- Cross-system concurrency (C+D): `concurrent_system_lords_jsonb`, `convergence_count_at_start` — **post-pass** after all 7 systems computed.
- Applicability (E): `applies_to_this_chart_flag` (e.g., Ashtottari conditional).
- Period deity/marker (F): `period_deity_or_marker` (Yogini named yoginis, Kalachakra markers).
- Antar-to-Maha relationship (G): `lord_to_parent_relationship`.
- Tajik year-lord (H): `varsha_year_lord` (Mudda rows only).
- Kalachakra solar-return (I): `anchored_solar_return_iso` (Kalachakra only).
- Triggered yogas (J): `triggered_yogas_jsonb_atomic` (deterministic G12 predicate firing — jsonb_atomic, an irreducible list, allowed).
- Lord transit at start (K): `lord_transit_at_period_start_jsonb` (single cheap G2 lookup, stored).
- Karaka activation (Q): `karakas_active_during_period TEXT[]`.

Note `concurrent_system_lords_jsonb`, `triggered_yogas_jsonb_atomic`, `lord_transit_..._jsonb` are the **sanctioned JSONB exceptions** (genuinely irreducible composites per atomic-grain rule) — everything else atomic.

## §5 — Calculation window (A7 §6)

Every row: `start_iso ≥ 1950-01-01` AND `end_iso ≤ 2100-12-31`; periods crossing a boundary truncated to the window. Native born 1984 (in-window) → backdate cycles to 1950 via backward-cycle walk from Moon-nakshatra-elapsed at birth (Moon in Purva Bhadrapada).

## §6 — Atomic grain + the 4-level reconciliation

Each period (Maha/Antar/Pratyantar/Sookshma) = its own row with `level_n` 1–4 and `parent_row_id` self-FK. KP sub-periods = their own rows under Vimshottari, marked by `kp_sublevel` dimension (NOT level_n=6/7). Stop the hierarchy at Sukshma (level 4) for all 7 systems — do NOT emit Prana (level 5). Two-pass precision: ±1 day at L4 Sukshma per system (the spec's ±10 sec Prana tolerance no longer applies — Prana isn't emitted).

## §7 — Two-pass verification (A7 §7 — MANDATORY every row)

`verification_pass_status ∈ {two_pass_verified, classical_match}`; `divergent_flagged` → halt. Per-system primary/secondary/tertiary in A7 §7 verbatim (Vimshottari: nakshatra-elapsed vs pada×cycle-table vs BPHS Ch.47 worked example; algebraic invariants for the cycle sums; Chara: Jaimini sign-progression vs Jaimini Sutram Ch.2 vs KN Rao example; Kalachakra: paramayush + deha/jeeva vs BPHS Ch.53). Tolerance ±1 day at L4 (±5 days Kalachakra). **No JH-parity** — all secondary passes are classical-rule reconstructions, never "match JH".

## §8 — FORENSIC grounding gate

Built on a chart that passed the 7 anchors. Additionally: the **Vimshottari starting lord** (from Moon in Purva Bhadrapada, lord Jupiter — G24) MUST match the classical mapping; the Mahadasha sequence MUST be internally consistent (sum of Maha periods = 120y, lords in correct order from the birth Moon-nakshatra lord). If the starting lord or first Maha boundary is wrong → halt + `CONDUCTOR_HALT_LOG.md`. Do NOT copy A7's illustrative dates (e.g., "Saturn Maha 2003→2022") uncritically — verify against the engine for `482012f1`.

## §9 — Citations (A7 §8)

Both forms per row; real engine version; `chart=482012f1`. Human form e.g.: "Vimshottari Saturn Mahadasha (Lahiri): <start> → <end>." / "Saturn-Sun Antardasha (Lahiri): <start> → <end>." / KP sub form references the `kp_sublevel` dimension, not a level_n=6 row.

## §10 — No materialized views (A7 §11)

`ganita_dashas` IS the precomputed timeline. Direct indexed queries (A3 §8 indexes: temporal_lookup, lord_lookup, parent) are single-ms. No MV. (The earlier `mv_chart_dasha_at_date` was correctly removed — it was parametric on query_date = time-varying.)

## §11 — Build-state wiring

On success update `asset_throughput` for `ga_dashas` (chart_id `482012f1`): row count + state transition. Update **per-system incrementally** so the cockpit bar advances across the long build, not only at the end. chart_id targeted = keyed.

## §12 — Acceptance criteria (all `[verify-against: prod]`)

1. `ganita_dashas` (or chart_dashas — whichever is canonical on prod) schema matches A3 §8 + A7 §4 additions + KP `kp_sublevel` dimension. `[verify: \d]`
2. All 7 systems populated for the native, ×5 ayanamsha, window 1950–2100, **depth capped at level_n=4 (zero level_n=5 rows)**. `[verify: psql GROUP BY system_id, level_n]`
3. KP sub-periods present under Vimshottari via `kp_sublevel` dimension (zero level_n=6/7 rows). `[verify: psql]`
4. **Every row `two_pass_verified` or `classical_match`** (zero `single`, zero `divergent_flagged`). `[verify: psql GROUP BY verification_pass_status]`
5. Algebraic invariants hold (Vimshottari sum=120y, Yogini=36y, Ashtottari=108y, Naisargika=120y). `[verify: psql SUM(duration) per L1 cycle]`
6. 13 additions populated correctly; concurrency/convergence computed in post-pass; only the 3 sanctioned JSONB fields hold composites (rest atomic). `[verify: column audit]`
7. FORENSIC: Vimshottari starting lord correct from Moon=Purva Bhadrapada; Maha sequence consistent. `[verify: assertion]`
8. Mudda hybrid storage: past+current+next-5y precomputed, not full 150y. `[verify: psql year range for mudda]`
9. Total row count in the ~2.5–3M target band (aspirational — not a gate; report actual). `[verify: psql count]`
10. `asset_throughput` ga_dashas updated per-system incrementally, keyed to `482012f1`; cockpit bar advances. `[verify: cockpit + psql]`
11. No MVs created for dashas. CI green; merge-verify before done.

## §13 — Rails

Reversibility, verify-before-promote, merge-verify, no JH-parity, Postgres-only, atomic-grain (3 sanctioned JSONB exceptions), two-pass-every-row, **4-level Sukshma cap (NOT Prana)**, **KP as kp_sublevel dimension (NOT level_n 6/7)**, deterministic accuracy over volume, floors aspirational, **per-system incremental idempotent writes (resumable under context-decay re-kick)**. Halt on starting-lord mismatch, invariant breach, two-pass divergence, ambiguous target table.

---

*End of GA7 brief v1.0. Largest by row count (~2.5–3M): 7 systems × 4-level Sukshma × 5 ayanamsha into ganita_dashas. KP is its own dimension; Prana is dropped.*
