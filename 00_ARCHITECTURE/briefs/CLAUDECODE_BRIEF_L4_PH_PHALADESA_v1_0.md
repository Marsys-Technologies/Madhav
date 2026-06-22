---
artifact: CLAUDECODE_BRIEF_L4_PH_PHALADESA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_PHALADESA
brief_for: ph_phaladesa — Delivered Outlook Dossier (the master-acharya reading; THE FINALE) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D46 elevations; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: DRAFT_CLAUDECODE_BRIEF_L4_PH_PHALADESA_v0_1.md
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D9 composite, D46 elevations, D11 subsystem, B.11 whole-chart-read, deterministic-first)
swarm_coordination:
  wave: W6 (LAST L4 asset — composes all the others)
  blocked_by: [ph_nimitta, ph_muhurta, ph_pratikara, ph_sodhana, ph_suddha_sodhana, ph_sankrama, ph_pramana]
  blocks: []   # the finale
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_phaladesa.py
    - platform/python-sidecar/services/ph_phaladesa/**
    - platform/supabase/migrations/337_phala_outlook.sql
    - platform/scripts/seed/asset_registry_seed.ts    # NEW asset registration (sort_order 8)
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  hard_internal_gate: "B.11 GATE: the dossier MUST read all the available sub-assets for its horizon + record composed_sub_asset_ids; a sub-asset with rows in the horizon that is NOT composed = a Whole-Chart-Read violation (procedural red). + DETERMINISTIC-FIRST gate: the LLM narrates only the fixed deterministic scaffold; a test asserts no claim exists in the narrative that isn't in the composed structure."
---

# CLAUDECODE BRIEF — ph_phaladesa (Delivered Outlook Dossier) — THE FINALE [maximal capacity]

> **Phaladeśa — "the declaration of the fruit."** The native-facing surface where the whole instrument
> stops being a database and becomes a READING. It composes every other L4 asset into one woven,
> prioritized, honest, multi-horizon outlook — anchored to who the native IS and fully traceable — the
> way a master acharya sits you down and walks you through your life. The other 7 assets are the
> ingredients; this is the dish.

## §0 — The gestalt relationship (correctness — do NOT duplicate; D46)
**Code-verified:** `bodha_chart_gestalt` / `vw_chart_digest` (L2) already holds the TIMELESS structural
"who you are" — `headline`, `watch_list`, `central_question`, `domain_verdict_map`, `defining_threads`
(pointer-only, no stored verdicts). **ph_phaladesa CONSUMES this as the framing backdrop — it does NOT
rebuild it.** The gestalt = the timeless person; ph_phaladesa = the time-bound DELIVERED OUTLOOK the
gestalt deliberately lacks. Frame the temporal reading against the structural self.

## §1 — REUSE the prioritizer (D10)
`ka_tulana` (`rank_windows` / `compare` / `attention_map`, native-ratified I-11 weights, `by_domain`)
ranks across all the composed items. ph_phaladesa CALLS it for the apex-item + the prioritized order; it
does not reinvent ranking.

## §2 — The 4 ELEVATIONS (D46)

### PD1 — Narrative WEAVE (not concatenation) — B.11 made legible
Compose a single FLOWING reading that CONNECTS the assets, not 5 separate lists: "Your career window
in 2027 (6 of 7 schools concur, high confidence) will — via the Saturn→Moon bridge — load onto your
health by mid-year; the pre-emptive remedy is [X], best begun on [muhūrta date]; and this all sits
inside your Mercury-to-Ketu life-transition." The weave links prediction (ph_nimitta) → spillover
(ph_sankrama) → mitigation (ph_pratikara) → timing (ph_muhurta) → life-arc (kala_jivana_parva).

### PD2 — The apex "if you read nothing else" item
Surface THE single most important thing right now (via `ka_tulana` I-11 ranking across all items): "the
defining theme of your next 18 months is [X]" — then the supporting structure beneath it. A master gives
you the ONE thing, not 40 equal rows. Store `apex_item_jsonb` + the ranked remainder.

### PD3 — Honest confidence + contradiction framing
Three explicit registers: `confident_jsonb` (high-confidence, multi-method-concurring claims),
`contested_jsonb` (where schools/signals disagree — carry ph_nimitta's contradiction + U4's divergence),
`speculative_jsonb` (low-confidence/distant). The reading SAYS which is which — never a falsely-certain dump.

### PD4 — Multi-horizon + multi-lens + person-anchor + traceability
- **Per horizon:** compose a `near` (5-yr) AND a `lifetime` dossier (using U2's horizon_tier).
- **Per lens:** compose per `bodha_question_lenses` (career / health / relationship / wealth / spiritual
  / …) so "career, lifetime" reads differently from "this year, all domains."
- **Person-anchor:** frame against the `bodha_chart_gestalt` ("for someone with your Jupiter-exalted,
  Saturn-disciplined nature, this window means …").
- **Traceability:** every claim carries its derivation chain pointer (anchor → convergence window →
  signal → L1 fact → classical citation) in `claim_trace_jsonb` so the native / an auditing acharya can
  ask "why do you say that?" and get the full chain. This is what makes it acharya-grade, not oracular.

## §3 — Deterministic-first guard (D46 — the integrity rail for the finale)
ph_phaladesa is the ONE legitimate place for generative LLM synthesis (prose weaving). The rail:
- **Deterministic (stored):** the composition (which asset rows), the `ka_tulana` ranking, the apex
  selection, the confidence/contradiction registers, the per-horizon/per-lens grouping, the
  `claim_trace` pointers. These are computed + stored — reproducible.
- **Generative (serve-time):** ONLY the prose narration over that FIXED scaffold, via Gemini/DeepSeek
  (Anthropic banned). The LLM cannot introduce a claim not in the composed structure — a test asserts
  every narrative claim maps to a composed item + its trace. The LLM narrates; it never fabricates.

## §4 — Schema (migration 337)
`phala_outlook`:
```
outlook_id              uuid PK
chart_id                uuid NOT NULL
horizon_tier            text CHECK (horizon_tier IN ('near','lifetime'))   -- PD4
question_lens           text                  -- PD4 (career|health|...|all)
horizon_start           date
horizon_end             date
apex_item_jsonb         jsonb NOT NULL         -- PD2 (the one thing)
woven_narrative_scaffold_jsonb jsonb NOT NULL  -- PD1 (the deterministic ordered weave: the items + their links, pre-prose)
confident_jsonb         jsonb NOT NULL         -- PD3
contested_jsonb         jsonb NOT NULL         -- PD3
speculative_jsonb       jsonb NOT NULL         -- PD3
person_anchor_jsonb     jsonb                  -- PD4 (the gestalt framing)
composed_sub_asset_ids  text[] NOT NULL        -- B.11 proof (which sub-assets were read)
claim_trace_jsonb       jsonb NOT NULL         -- PD4 (per-claim derivation chain pointers)
prioritization_jsonb    jsonb                  -- the ka_tulana ranking
narrative_text          text                   -- serve-time generated prose (from the scaffold; may be regenerated)
narrative_model         text                   -- which LLM produced it (Gemini/DeepSeek)
derivation_ledger_jsonb jsonb NOT NULL
source_citation         text NOT NULL
computed_at             timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, horizon_tier, question_lens, horizon_start, horizon_end)
```

## §5 — Engine spec (`services/ph_phaladesa/engine.py`)
1. For the requested (horizon, lens): gather the relevant rows from ph_nimitta / ph_sankrama /
   ph_muhurta / ph_pratikara / ph_suddha_sodhana + the `bodha_chart_gestalt` backdrop.
2. Call `ka_tulana` → rank; select the apex (PD2); order the weave (PD1).
3. Partition into confident/contested/speculative (PD3) from the items' confidence + contradiction fields.
4. Build the person_anchor from the gestalt (PD4); build `claim_trace` pointers per item (PD4).
5. Record `composed_sub_asset_ids` (B.11 proof); store the deterministic scaffold.
6. Serve-time: generate `narrative_text` from the scaffold via Gemini/DeepSeek (deterministic-first rail §3).
7. Anti-drift: cite every composed sub-asset id; write ONLY `phala_outlook`.

## §6 — Acceptance criteria [tagged; prod-verified]
1. `[pytest — B.11 GATE]` the dossier composes ALL sub-assets that have rows in the horizon; `composed_sub_asset_ids` lists them; a missing-but-present sub-asset = fail.
2. `[pytest — PD1]` the woven scaffold links items across assets (a career anchor → its spillover → its mitigation → its muhūrta), not a flat per-asset list.
3. `[pytest — PD2]` the apex item is the ka_tulana top-ranked; the remainder is ordered beneath it.
4. `[pytest — PD3]` claims are partitioned into confident/contested/speculative from real confidence + contradiction fields.
5. `[pytest — PD4]` per-horizon (near + lifetime) + per-lens dossiers compose; person_anchor from the gestalt; every claim has a `claim_trace` chain that RESOLVES to real ids.
6. `[pytest — DETERMINISTIC-FIRST GATE]` the scaffold/ranking/registers/traces are deterministic + stored; the narrative is generated from the scaffold; a test asserts NO narrative claim lacks a composed-item + trace (LLM narrates, never fabricates); model = Gemini/DeepSeek (not Anthropic).
7. `[gestalt]` consumes `bodha_chart_gestalt` (does NOT rebuild it).
8. `[anti-drift]` writes only phala_outlook; reads only ph_* + bodha_chart_gestalt + ka_tulana; zero `.commit()/.rollback()`.
9. `[psql_prod + curl_prod]` phala_outlook lit; cockpit Phala panel now shows ALL 8 L4 assets lit; idempotent; FORENSIC 7/7.

## §7 — Asset registration (NEW)
Add `ph_phaladesa` / `Phaladeśa` / `Delivered outlook` / `phala_outlook` / sort_order 8 / depends_on
`['ph_nimitta','ph_muhurta','ph_pratikara','ph_suddha_sodhana','ph_sankrama']` (+ reads
bodha_chart_gestalt, calls ka_tulana) / `$1` count_sql / artifact / delete-then-insert. Serialize seed (CS1).

## §8 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-phaladesa
# the prioritizer + the gestalt backdrop to consume
sed -n '25,145p' platform/python-sidecar/services/ka_tulana/ranker.py
sed -n '970,990p' platform/migrations/325_l2_bodha_enriched_schema.sql
cd platform/python-sidecar && pytest -q services/ph_phaladesa -k "phaladesa or outlook or weave or apex or b11 or deterministic or trace"
```

## §9 — Definition of done
- [ ] Migration 337: phala_outlook created; ph_phaladesa registered (8th L4 asset).
- [ ] PD1 weave + PD2 apex + PD3 honest-registers + PD4 multi-horizon/lens/person-anchor/traceability.
- [ ] Consumes bodha_chart_gestalt (no duplication); B.11 gate + deterministic-first gate passed.
- [ ] Anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit shows ALL 8 L4 assets lit; PR opened.

## §10 — VALUE ADDED BY THIS BRIEF
1. **The surface the native actually reads** — one woven, prioritized, honest, multi-horizon reading
   instead of 7 ingredient tables. Where the layer becomes a PRODUCT.
2. **Reads like a master acharya** — narrative weave + the apex 'one thing' + honest confidence framing
   + framed against who they ARE — not a database dump.
3. **Acharya-grade traceability** — every claim resolves back through the chain to an L1 fact + classical
   citation; the native or an auditor can always ask "why?".
4. **Deterministic-first even for the prose** — the LLM narrates a fixed, reproducible, traceable
   scaffold and cannot fabricate; the integrity rail holds even at the generative surface.
5. **B.11 whole-chart-read enforced structurally** — composes every sub-asset + stores the proof.

## §11 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** lens set = the existing `bodha_question_lenses` domains
  (career/wealth/marriage/health/character/spirituality/education/progeny/longevity) + an `'all'` composite.
- **R2 [RESOLVED — Cowork default locked]:** the deterministic scaffold is the source of truth + stored;
  the prose is generated at serve time, the latest + its model stored, regenerated on demand (e.g. model upgrade).
- **R3 [RESOLVED — Cowork default locked]:** narration model = **Gemini Pro** (critical native-facing
  prose), **DeepSeek fallback**, **never Anthropic** (the model-policy ban holds).

---
*End of CLAUDECODE_BRIEF_L4_PH_PHALADESA v1.0 — CLOSED. The finale at maximal capacity: narrative weave,
the apex item, honest confidence framing, multi-horizon/lens/person-anchor/traceability — the
master-acharya reading, deterministic-first even in its prose. R1–R3 resolved.*
