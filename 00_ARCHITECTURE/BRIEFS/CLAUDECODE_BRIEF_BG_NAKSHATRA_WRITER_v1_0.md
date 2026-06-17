---
artifact: CLAUDECODE_BRIEF_BG_NAKSHATRA_WRITER_v1_0.md
canonical_id: BG_NAKSHATRA_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous, orchestrator-native)
campaign: Nakshatra Subsystem — Tier 1, Phase 1 (the L0 global reference; ga_nakshatra depends on it)
delivery_model: 1 branch, plan-then-execute, no human gate
design_source: 00_ARCHITECTURE/NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md (§2 + §7.1 all decisions LOCKED)
---

# bg_nakshatra — L0 Global Nakshatra Reference — Execution Brief v1.0

## §0 — Read first + the locked decisions

Read `NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md` — §2 (the full L0 scope) + §7.1 (all 8 decisions RESOLVED;
do NOT re-ask). Key locked facts: 3-grain table split; full 36-guna Ashtakuta tables; Abhijit as flagged
28th; reopen L0 additively (new global asset, NOT a bg_reference rebuild); multi-tradition variants → into
bg_texts with tradition_scope + citation.

## §1 — What this is

`bg_nakshatra` is a NEW L0 global asset: the fully-enriched, chart-agnostic nakshatra + pada reference —
EVERY classical static nakshatra datum + all relational matrices. It supersedes the thin existing nakshatra
data inside `l0_reference.py` (`reference_nakshatras`, 27 rows, ~9 attrs). It is the AUTHORITY for static
nakshatra attributes; `ga_nakshatra` (L1) will JOIN it, never restate it.

**Deterministic + cited only. No LLM-generated content. No narrative** (gana IS a fact; "rakshasa gana means
aggressive" is NOT — that's serve-time). Every attribute carries a classical_source citation.

## §2 — Reality reconciliation

- The existing `reference_nakshatras` (27 rows) lives inside `bg_reference`/`l0_reference.py`. bg_nakshatra
  is a SEPARATE, richer asset. **Decide at build:** either (a) bg_nakshatra OWNS the enriched nakshatra
  tables and `reference_nakshatras` is migrated/deprecated into it, or (b) bg_nakshatra's tables supersede
  and `bg_reference` stops emitting nakshatra rows. Prefer (a) — one authority. Report the choice; don't
  leave two nakshatra sources.
- L0 writer pattern: `@register('bg_nakshatra') class NakshatraReferenceWriter(WriterBase)` mirroring
  `pipeline/orchestrator/writers/bg_reference.py`. `scope: global`, ON-CONFLICT idempotency (L0 pattern —
  [[feedback-idempotency-pattern-per-layer]]; global, no chart_id). Orchestrator-native (run(ctx)→WriterResult).
- Underscore id `bg_nakshatra`. Surgical migration only.

## §3 — Storage: 3-grain split (decision §7.1.5)

Three tables, FK'd:
1. **`reference_nakshatra` (27 + Abhijit 28th)** — per-nakshatra attributes (§4).
2. **`reference_nakshatra_pada` (108)** — per-pada attributes (§5), FK → nakshatra.
3. **`reference_nakshatra_matrix`** — the relational matrices as rows (§6).
Each row: the attribute columns + `tradition_scope` (default 'classical'/BPHS; variants tagged) +
`classical_source` (citation, ideally a bg_texts verse_ref) + standard L0 provenance.

## §4 — Per-nakshatra attributes (27 + Abhijit) — implement ALL (master §2.1)

Identity+span: number (1–27; Abhijit=28 flagged), name_sa (IAST + Devanagari), name_en, alt_names,
start_longitude, end_longitude, span (13°20′), rashi(s)_spanned, degree_in_rashi_ranges.
Rulership: vimshottari_lord, presiding_deity + secondary_deities, ruling_planet (vs deity).
**Compatibility/nature axes (the critical gap):** gana (Deva/Manuṣya/Rākṣasa), nadi (Ādi/Madhya/Antya),
yoni (14-animal) + yoni_sex (M/F), varna, tatva/element (Agni/Prithvi/Vayu/Jala/Akasha), guna
(Sattva/Rajas/Tamas), pakshi/bird, nakshatra_gender.
Muhurta classification: type (Chara/Dhruva/Mishra/Ugra/Mridu/Tikshna/Kshipra/Laghu), disha, favorable_acts,
prohibited_acts.
Symbolism+theology: symbol, **shakti + basis_above + basis_below + net_result** (Nakshatra Shakti verses),
motivation (dharma/artha/kama/moksha), body_part (Kalapurusha).
Longevity/maturity: paramayus, **naisargika_maturity_age**.
**deity_domain** (§7) + group memberships (§8) + sound layer (§5 pada-level).

## §5 — Per-pada (108) — implement ALL (master §2.2)

pada_number (1–4), pada_lord (navamsa-sign lord), **pada_navamsa_sign** (static map), pada_degree_range
(3°20′), **pada_akshara** (naming syllable), pada_deity_nuance, pada_element/dosha_shading, vimshottari
sub-lord seed, **pada→navamsa cross-map** (the deterministic nakshatra-pada ↔ D9 link). Sound: bija/sound
correspondence + nakshatra→mantra mapping per pada (feeds L4 Upaya).

## §6 — Relational matrices (master §2.3) — the full 36-guna + timing substrate

Store as rows in `reference_nakshatra_matrix` (matrix_type, from_key, to_key, relation_value, citation):
- **The 8 Ashtakuta kuta tables (full 36-guna set, decision §7.1.2):** Varna, Vashya, Tara (27×27), Yoni
  (14×14 friend/enemy/neutral + clash pairs), Graha-Maitri, Gana (3×3), Bhakoot, Nadi (3-way clash). Each
  with its classical point-value (the 1/2/3/.../8 guna weights).
- **Timing/vedha:** rajju (aroha/avaroha + 5 body-part rajjus), vedha pairs (Sarvatobhadra obstruction),
  mahendra, stree-deergha.

## §7 — Deity→domain map (master §2.5)
Each presiding deity → life-DOMAIN (Yama→death/discipline, Ashwins→healing, Agni→fire/digestion,
Brahma→creation, …). Structured so "planet in Yama's nakshatra" connects to a domain. Cited.

## §8 — Group memberships + cycle definitions (master §2.3/§2.6)
Per-nakshatra static flags: gaṇḍānta nakshatras, mūla-sangya/difficult nakshatras, abhukta-mūla range,
panchaka (last 5), Sarvatobhadra-chakra position, Kalachakra groupings, Nadi/Yogini/sub-tara cycle SEED
definitions (chart-position is L1). Gauri-Panchang/Chandra-Tara-Vela tables.

## §9 — Abhijit (decision §7.1.1)
28th reference row, `tradition_scope='abhijit_28fold'`, span ~6°40′ around Uttarashadha-end→Shravana-start
(~Capricorn — confirm exact arc vs source). INCLUDED where muhurta/some-longevity use it; EXCLUDED from
27-fold dasha math. Make the exclusion explicit so downstream 27-fold consumers skip it.

## §10 — Multi-tradition variants → bg_texts (decision §7.1.7) — DO THIS CAREFULLY
Where texts disagree on an attribute (gana/yoni/etc.), store the variant as an additional row/value with
`tradition_scope` (e.g. 'nadi', 'muhurta') + a `classical_source` citation into **bg_texts**.
**Step A — check first:** what nakshatra-coverage texts are ALREADY in bg_texts (13 texts, 8,193 chunks)?
Grep the text registry. Source-gap ONLY the missing.
**Step B — source the gaps** via the existing `l0_texts.py` GCS→chunk ingestion path: a comprehensive
Nakṣatra compendium (attribute tables), Muhūrta Cintāmaṇi / Kālaprakāśikā (muhurta + Abhijit), Nadi corpus
(Nadiamsa + variants). Confirm exact editions; ingest as new bg_texts rows (this REOPENS bg_texts additively
— deterministic clear-and-rebuild per its build contract; coordinate so the rebuild includes the new texts).
**Step C — cite:** every variant attribute's `classical_source` resolves to a bg_texts verse_ref. This makes
variants grounded + auditable + inheriting the retrieval/grounding machinery.

## §11 — Registration + cockpit
Register `bg_nakshatra` in `asset_registry_seed.ts` + a seed migration: layer brahmagyan/L0, scope global,
asset_type data, catalog_status CURRENT, count_sql = SUM of the 3 tables' rows, target_floor = achieved
count (floors-aspirational). Mirror the `bg_reference` registry entry shape. The cockpit shows it as an L0
data tile.

## §12 — Acceptance (all `[verify-against: prod]`)
1. 3 tables created; all 27 (+Abhijit 28th flagged) nakshatra rows with EVERY §4 attribute populated; 108
   pada rows with every §5 attribute; matrices complete (8 kuta + rajju/vedha/mahendra/stree-deergha).
2. Every row cited (classical_source non-null; variants resolve to bg_texts verse_refs).
3. Variants checked-then-gap-sourced into bg_texts; no duplicate nakshatra source left (reference_nakshatras
   reconciled per §2).
4. Deterministic (re-run → identical; ON-CONFLICT idempotent); no LLM-generated content; no-narration linter green.
5. FORENSIC sanity: the native's Moon nakshatra Purva Bhadrapada row carries correct lord (Jupiter), gana,
   nadi, yoni, deity (Aja Ekapad), shakti — spot-verify against classical source.
6. Registered; orchestrator builds it (global); cockpit tile lit; count_sql/target_floor correct.
7. CI green; merge-verify.

## §13 — Rails
Deterministic-cited-only (no LLM); only-facts; atomic grain (matrices as rows); L0 ON-CONFLICT idempotency;
orchestrator-native (frozen contract); additive L0 (new asset, not a bg_reference/bg_texts rebuild beyond the
additive text ingestion); surgical migrations; merge-verify. bg_nakshatra is the static-attribute AUTHORITY.
Halt-and-report if a classical attribute can't be sourced/cited (floor it as null+marked; never fabricate an
attribute value — an uncited gana is worse than a missing one).

---

*End. bg_nakshatra: the complete chart-agnostic nakshatra reference — 27/28 + 108 padas + full matrices,
every attribute cited, variants grounded in bg_texts. The static foundation ga_nakshatra joins.*
