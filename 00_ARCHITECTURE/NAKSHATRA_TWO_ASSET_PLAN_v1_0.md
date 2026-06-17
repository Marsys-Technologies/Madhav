---
artifact: NAKSHATRA_TWO_ASSET_PLAN_v1_0.md
canonical_id: NAKSHATRA_TWO_ASSET_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — native-ratified two-asset split
authored_for: the Nakshatra build (Cowork plans → Claude Code in Antigravity executes)
purpose: >
  Close the L1 nakshatra-depth gap with TWO assets split on the static-vs-computed line:
  (1) bg_nakshatra — a fully-enriched GLOBAL (chart-agnostic) L0 reference holding every classical
  nakshatra + pada data point; (2) ga_nakshatra — a chart-specific L1 asset computing, via PyJHora,
  every per-chart nakshatra-wise calculation per body. Exhaustive at both levels, before/alongside L2.
context: >
  Audit (2026-06-10) found L1 captures nakshatra POSITION (name/lord/pada per body ×5 ay + Moon Tara
  matrix) but LACKS attribution DEPTH (gana/nadi/yoni/varna/tatva/pakshi/per-pada-deity/gaṇḍānta/
  Abhijit/KP-sub-lord). Most of the gap is STATIC reference (→ L0); the rest is per-chart computed (→ L1).
decisions_locked: build BOTH (global bg_nakshatra + chart-specific ga_nakshatra); exhaustive at each level; before/alongside L2.
---

# Nakshatra — Two-Asset Plan (L0 global + L1 chart-specific) v1.0

## §0 — The governing split (the principle that decides what goes where)

The single rule that partitions every data point:

- **`bg_nakshatra` (L0, GLOBAL, chart-agnostic):** any nakshatra/pada fact that is the SAME for every
  person — a fixed property of the 27 (or 28 with Abhijit) nakshatras and the 108 padas. Computed ONCE,
  no chart_id, no PyJHora-per-chart. Lives in L0, `scope: global`, ON-CONFLICT idempotency (L0 pattern).
- **`ga_nakshatra` (L1, PER-CHART, computed by PyJHora):** any nakshatra fact that depends on THIS
  chart's exact graha positions/degrees — which nakshatra+pada each body occupies, the degree-sensitive
  flags (gaṇḍānta/abhukta), KP sub-lords from exact longitude, the per-body attribute JOIN, the chart's
  nakshatra-distribution statistics. `scope: per_chart`, PyJHora, L1 delete-then-insert idempotency.

Test for any datum: "is it true for everyone, or does it depend on where this chart's planets are?"
Everyone → L0. This chart → L1. **ga_nakshatra JOINS bg_nakshatra; it never restates the static attrs**
(L1-is-authority inverted here: L0 reference is the authority for static attrs, L1 references them).

---

## PART A — `bg_nakshatra` (L0 GLOBAL — the enriched reference)

### §A.1 — Scope: every chart-agnostic nakshatra + pada data point

Today L0 `reference_nakshatras` holds only: name_en, name_sa, lord, deity, nature, guna, degree-span,
pada_lords, body_part. **bg_nakshatra is the complete replacement/superset** — enrich to hold EVERY
classical static attribute. Two grains: **per-nakshatra (27/28 rows)** and **per-pada (108 rows)**.

### §A.2 — Per-nakshatra attributes (the 27, + Abhijit as 28th where the tradition uses it)

Author the complete set. For each nakshatra:

**Identity + span**
- number (1–27; Abhijit handling — see §A.4), name_sa (IAST + Devanagari), name_en, alt_names
- start_longitude, end_longitude, span (13°20′), rashi(s) spanned (most cross a sign boundary), degree-in-rashi ranges

**Rulership + classical lords**
- vimshottari_lord (1 of 9), nakshatra_devata (presiding deity), additional deities (some have multiple)
- ruling_planet vs deity distinction, varga/sub-rulers where classical

**The compatibility + nature axes (the CRITICAL missing set)**
- **gana** (Deva / Manuṣya / Rākṣasa)
- **nadi** (Ādi / Madhya / Antya) — the health/progeny compatibility axis
- **yoni** (animal — 14 yonis: horse/elephant/sheep/serpent/dog/cat/rat/cow/buffalo/tiger/deer/monkey/mongoose/lion) **+ yoni-sex (male/female)** + yoni friend/enemy pairings
- **varna** (Brahmin/Kshatriya/Vaishya/Shudra)
- **tatva / element** (Agni/Prithvi/Vayu/Jala/Akasha)
- **guna** (Sattva/Rajas/Tamas)
- **pakshi / bird** (the Panchapakshi bird assignment)
- **gender** (nakshatra's own gender)
- **caste/disposition, temperament**

**Nature + activity classification (Muhurta use)**
- nakshatra_type / quality (Movable/Chara, Fixed/Dhruva, Mixed/Mishra, Fierce/Ugra/Krura, Soft/Mridu/
  Maitra, Sharp/Tikshna, Swift/Laghu/Kshipra) — the activity-suitability classification
- direction (disha), favorable activities, prohibited activities (classical muhurta tables)

**Anatomy + symbolism**
- body_part (Kalapurusha anatomical correspondence), symbol, shakti (the nakshatra's "power" per the
  classical shakti/basis-above/basis-below framework), motivation (dharma/artha/kama/moksha)

**Longevity + dasha infrastructure**
- paramayus (max-years contribution in some longevity schemes)
- the nakshatra's position in special nakshatra groupings (see §A.3)

**Cross-references**
- classical_source citations (BPHS / Muhurta texts / bg_texts), per the L0 citation pattern

### §A.3 — Per-nakshatra group memberships (static set-membership — all chart-agnostic)

Flag each nakshatra's membership in the classical groupings (these are fixed, so L0):
- **Gaṇḍānta nakshatras** (the 3 water-fire junctions: Revati–Ashwini, Ashlesha–Magha, Jyeshtha–Mula)
  — the nakshatra-level flag (the degree-window is L1)
- **Mūla / Jyeṣṭhā / Āśleṣā / Viśākhā** and other "difficult" / mūla-sangya nakshatras requiring shanti
- **Abhukta Mūla** range
- **Panchaka** nakshatras (the last 5: Dhanishtha-2nd-half → Revati)
- **Tarabala-relevant groupings**, **Sarvatobhadra-chakra position**, **Kalachakra groupings**
- **Vedha pairs** (which nakshatra obstructs which — static pairs)
- **Rajju / Mahendra / Stree-Deergha** classification (compatibility groupings)

### §A.4 — Per-pada (108 rows — the finer static grain)

Each nakshatra × 4 padas = 108. For each pada (the per-pada nuance L1 currently lacks entirely):
- pada_number (1–4), pada_lord (the navamsa-sign lord of that pada)
- **pada_navamsa_sign** (each pada maps to a fixed navamsa sign — static!)
- pada degree-range (3°20′ each)
- **pada_akshara** (the naming syllable — Ku/Ke/etc. — classical for naamkaran)
- pada_deity-nuance, pada element/dosha shading where the tradition differentiates
- the pada's vimshottari sub-lord pattern seed (the static part; the chart-specific sub-lord is L1)

### §A.5 — Abhijit decision (flag for native at build)

Abhijit (the 28th, spanning end-Uttarashadha → start-Shravana, ~6°40′ Capricorn) is used in some
traditions (muhurta, some longevity), not in the standard 27-fold zodiac division. **Hold Abhijit as a
28th reference row with a `tradition_scope` marker** so it's available where used but doesn't corrupt the
27-fold nakshatra-division math. Flag the exact span + which calculations include it for native sign-off.

### §A.6 — bg_nakshatra storage + registration

- Table(s): enrich `reference_nakshatras` (27/28) + a new `reference_nakshatra_padas` (108), OR one wide
  `bg_nakshatra` table — decide at build (prefer the 2-grain split: per-nakshatra + per-pada, FK'd).
- Register `bg_nakshatra` as an L0 `scope: global`, `asset_type: data` asset (underscore id). count_sql =
  the row count; ON-CONFLICT idempotency (L0 pattern — [[feedback-idempotency-pattern-per-layer]]).
- Source: classical corpus (bg_texts / BPHS / Muhurta references) — DETERMINISTIC tables embedded as
  engine constants + cited; NOT LLM-generated. Every attribute carries a classical_source citation.
- It becomes a dependency: `ga_nakshatra.depends_on = ['bg_nakshatra', ...]`.

---

## PART B — `ga_nakshatra` (L1 PER-CHART — computed by PyJHora)

### §B.1 — Scope: every chart-specific nakshatra-wise calculation, per body

For THIS chart, per ayanamsha (×5), PyJHora-computed. The depth L1 currently lacks. Per body
(all 9 grahas + Lagna + the nodes + key sensitive points — not just Moon):

### §B.2 — Per-body nakshatra placement + attribute join

- nakshatra (name + number), **pada (1–4)**, exact degree-within-nakshatra, % traversed
- **JOIN the bg_nakshatra static attrs onto each body** (so a query for "Mars's gana/nadi/yoni" resolves):
  gana, nadi, yoni+sex, varna, tatva, pakshi, deity, shakti, pada_navamsa_sign, pada_akshara — REFERENCED
  from bg_nakshatra (cite the bg_nakshatra row; do not recompute the static attr).
- nakshatra_lord (vimshottari) + the lord's own placement (dignity/house) — the "nakshatra lord condition"
  that classical analysis leans on heavily

### §B.3 — The genuinely-computed per-chart flags (degree-sensitive — must be PyJHora, can't be static)

- **gaṇḍānta flag + exact arc** — is this body within the gaṇḍānta degree-window (last/first ~48′ of the
  junction nakshatras)? Depends on exact longitude → per-chart.
- **abhukta mūla** flag, **mṛtyu-bhāga** proximity, **pushkara navamsa/bhaga** flag (already partly in GA6 —
  cross-reference, don't duplicate)
- **sandhi** (nakshatra-junction) proximity per body
- **vargottama-via-pada** (pada navamsa == D1 sign)

### §B.4 — KP nakshatra sub-division (the missing KP depth — genuinely per-chart)

- **star-lord (nakshatra lord), sub-lord, sub-sub-lord** per body + per house cusp, from the 249-fold
  Vimshottari-proportional subdivision of exact longitude. This is the KP backbone L2 Bodha will need for
  KP significator signals — currently absent at L1. (A5 had kp_ruling_planets but NOT the full sub-lord
  chain.) Compute per body + per cusp.
- nadiamsa (D150) nakshatra-level lord where applicable

### §B.5 — Tara / nakshatra-cycle systems (chart-specific from natal Moon nakshatra)

- The 9-fold **Tara Bala** from natal Moon nakshatra — the 27-row baseline already exists in GA4
  (cross-reference, extend not duplicate); add the per-body tara (each graha's nakshatra's tara from natal
  Moon), not just the transit-Moon matrix.
- **Sarvatobhadra chakra** position of each body's nakshatra (vedha candidates — the chakra is static A17,
  the chart's occupancy is per-chart)
- **special nakshatra yogas** that depend on placement: gandanta-at-birth, nakshatra-of-Lagna-lord, etc.

### §B.6 — Chart-level nakshatra statistics (within-chart, deterministic — feeds L2)

Per the L2 design philosophy (within-chart deterministic stats): compute and store, per chart/ayanamsha:
- **nakshatra distribution** — how many bodies in Deva/Manuṣya/Rākṣasa gana; nadi balance; yoni
  distribution; tatva balance across all bodies (the chart's elemental nakshatra signature)
- **gana/nadi/yoni concentration** (a deterministic "this chart is rakshasa-gana-heavy" signal)
- **cross-ayanamsha nakshatra consistency** — does each body's nakshatra hold across all 5 ayanamshas, or
  flip at a boundary (the 5/5-vs-2/5 robustness the L2 philosophy wants)
These are the nakshatra ingredients L2 Bodha's MSR will turn into signals (gana-compatibility, nadi-balance,
KP-significator signals) — exactly what "before/alongside L2" buys us.

### §B.7 — ga_nakshatra storage + registration

- Target: `chart_facts` (the nakshatra fact_categories) OR a dedicated `ganita_nakshatra` table — decide at
  build (prefer chart_facts for L2 retrieval consistency unless volume argues otherwise).
- Register `ga_nakshatra` as L1 `scope: per_chart`, underscore id, `@register('ga_nakshatra')` WriterBase
  conforming to the FROZEN orchestrator contract (run on ctx.db_conn, never commit, heavy-if-needed
  sub-steps per-ayanamsha). L1 delete-then-insert idempotency. count_sql + target_floor = achieved count.
- `depends_on: ['bg_nakshatra', 'ga_positions']` (needs the static reference + each body's position).
- FORENSIC: the native's Moon nakshatra = **Purva Bhadrapada** (anchor) — assert. Lagna nakshatra,
  per-body nakshatras verified internally-consistent with ga_positions.
- Two-pass verification per row.

---

## PART C — Execution plan (phased; before/alongside L2)

**Phase 1 — bg_nakshatra (L0 global).** Author the complete per-nakshatra (27/28) + per-pada (108)
attribute tables as deterministic cited constants; migration to create/enrich the reference tables;
register bg_nakshatra; build (global, once). Verify: every attribute populated for all 27 (+Abhijit
flagged), all 108 padas, every row cited. This is the foundation ga_nakshatra joins.

**Phase 2 — ga_nakshatra (L1 per-chart).** Author the PyJHora writer: per-body placement + bg_nakshatra
join + degree-flags + KP sub-lords + tara extensions + chart-level nakshatra statistics. Register
orchestrator-native. Build for the native via the orchestrator (NOT hand-run). Verify: FORENSIC Moon =
Purva Bhadrapada, per-body nakshatras consistent with ga_positions, KP sub-lords present, statistics
computed, cockpit tile lit + bar fills.

**Phase 3 — wire into L2.** Add ga_nakshatra (+ bg_nakshatra) to the L2 Bodha data interface so MSR can
build nakshatra-dependent signals (gana/nadi/yoni compatibility, KP significators, gaṇḍānta sensitivity).
Update the L2 handoff §3 (what Bodha consumes from L1) to include the nakshatra asset.

## §D — Standards (inherited — apply throughout)

Deterministic-first (classical tables, not LLM); only-facts (no narrative — gana IS a fact, "rakshasa
gana means aggressive" is NOT); atomic grain; two-pass; FORENSIC-gated; L0 ON-CONFLICT / L1 delete-then-
insert idempotency; no JH-parity (verify by internal consistency + classical-table re-derivation); no
tier; floors aspirational; orchestrator-native (ga_nakshatra conforms to the frozen contract); surgical
migrations. bg_nakshatra is the AUTHORITY for static attrs — ga_nakshatra references, never restates.

## §E — Open decisions to flag at build (native sign-off)

1. **Abhijit** — exact span + which calculations include the 28th (§A.4).
2. **Yoni count/scheme** — confirm the 14-yoni + sex + friend/enemy table to embed.
3. **ga_nakshatra storage** — chart_facts vs dedicated `ganita_nakshatra` table.
4. **KP sub-sub-lord depth** — to sub (249) or sub-sub; per-body only or per-cusp too.
5. **bg_nakshatra table shape** — one wide table vs per-nakshatra + per-pada (FK'd) — recommend the split.
6. **Reopening L0** — bg_nakshatra adds a new L0 asset (L0 is sealed-but-extensible; this is a genuine new
   global asset, not a rebuild of existing ones — confirm it's an additive L0 extension, like the panchanga
   service assets were).

---

*End. Two assets, split on static-vs-computed: bg_nakshatra (L0 global — every chart-agnostic nakshatra +
pada attribute, fully enriched, cited) + ga_nakshatra (L1 per-chart — PyJHora-computed placement, attribute-
join, degree-flags, KP sub-lords, tara, and chart-level nakshatra statistics). Built before/alongside L2 so
Bodha can build nakshatra-dependent signals on a complete foundation.*
