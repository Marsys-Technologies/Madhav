---
artifact: L1_ENRICHMENT_AMENDMENTS_v1_0.md
canonical_id: L1_ENRICHMENT_AMENDMENTS
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-17
authored_for: the L1 closure pass — Phase-3 enrichment of ga_strength / ga_condition / ga_sensitive
governing_memory: feedback-l1-per-varga-strength-dignity, feedback-canonical-or-floor-rule, feedback-l1e-full-relationship-graph
purpose: >
  Three native-ratified L1 asset expansions decided 2026-06-17 after the "does across-all-30-vargas add value?"
  analysis. These are NOT a separate workstream — they are the enrichment (Phase 3) of the L1 closure pass,
  executed AFTER the empirical data baseline (DATA_INVESTIGATION_PROMPT_v1_1) confirms current varga-coverage.
prerequisite: Run DATA_INVESTIGATION_PROMPT_v1_1 FIRST. The three ⭐ sizing answers (Q3 strength varga-coverage,
  Q4 sensitive-points present/missing diff, Q6 dignity varga-coverage) size each amendment against the real data.
---

# L1 Enrichment Amendments v1.0 — per-varga strength, per-varga dignity, classical sensitive-point completeness

## §0 — The reasoning that produced these three rulings

The native asked, of strength / sensitive-points / dignity / condition-composite: **"does computing it across
all 30 divisional charts add value, or is it meaningless mechanical projection?"** The principle that resolved
it: **"across all vargas" adds value where the TECHNIQUE is classically defined across vargas, and is
meaningless where it isn't.** Applied:

- **Strength → YES.** Vimsopaka Bala *is* strength-across-vargas (classical core). A planet strong in D1 but
  weak across the Shodasavarga is genuinely weaker. So per-varga strength is real classical depth, not "beyond
  astrology." **Build it.**
- **Sensitive points → MOSTLY NO.** A sensitive point is a longitude; you *can* project it into D9/D10, but the
  tradition uses sensitive points overwhelmingly in D1, with only a few CITED varga cases (Karakamsa=AK-in-D9,
  Arudha-in-D9). Projecting all ~30 points into all 30 vargas = ~900 mostly-meaningless rows = maximal VOLUME,
  minimal MEANING — fails the gate's spirit. **Drop the varga projection; instead complete the CLASSICAL set
  (the real gap is missing classical points, not missing varga copies) + a labeled cross-tradition shelf.**
- **Dignity → YES (sub-component only).** Dignity is varga-defined (a planet has a dignity in each divisional
  chart — that's what Vimsopaka aggregates). But the FULL condition composite also holds combustion / motion /
  avastha, which are D1-only concepts (no "combustion in D9"). **So varga-spanning belongs ONLY in the dignity
  sub-component; the rest of the composite stays D1.**

The unifying gate (whole program): **exhaust the computable+citable space, never fabricate; an uncited or
non-canonical value is worse than a missing one** ([[feedback-canonical-or-floor-rule]]).

---

## §A — AMENDMENT 1: ga_strength → FULL SHADBALA PER VARGA (D1–D30)

**Ruling (native, maximal):** compute all **six Shadbala components** — Sthāna-bala, Dig-bala, Kāla-bala,
Cheṣṭā-bala, Naisargika-bala, Dṛk-bala — in **every divisional chart D1–D30**, kept available for
varga-specific analysis. This is the granular per-varga layer BENEATH the existing Vimsopaka aggregate.

**HONEST-FLOOR RAIL (the integrity spine — non-negotiable):** some components are arguably D1-only concepts —
**Kāla-bala** (day/night, paksha, ayana, tribhaga, hora, abda/masa/vara — tied to real birth time) and
**Cheṣṭā-bala** (retrogradation/motional state — a real-position concept). For these, per varga either:
  (a) compute the component IF a classically-cited per-varga method exists, OR
  (b) **FLOOR it NULL with a stored reason** (`floored: no_canonical_per_varga_method`) — **NEVER fabricate a
     plausible per-varga value.** Sthāna-bala (incl. the saptavargaja/varga-dignity element) and Naisargika-bala
     are cleanly per-varga; Dig-bala and Dṛk-bala compute per-varga from that varga's house/aspect geometry.

**Labeling:** per-varga Shadbala is a **COMPUTED EXTENSION**, explicitly labeled — NOT a canonical cited value
(the canonical Shadbala is the D1 / standard-varga-group computation). Store `computation_tier:
computed_extension` so downstream never mistakes it for a canonical figure ([[feedback-canonical-or-floor-rule]]).

**Storage:** varga-dimensioned (a `varga` column or `fact_subject` component naming D1…D30). Watch row-count:
6 components × 9 grahas × 30 vargas ≈ 1,620 rows/chart before floors — acceptable, log the achieved count as
target_floor ([[feedback-floors-are-aspirational-not-gates]]). Reopens **ga_strength as the 2nd L1 asset in
L1-E** ([[feedback-l1e-full-relationship-graph]]) — ga_strength-per-varga, THEN ga_structural.

**Sized by:** Q3 of the data investigation (current shadbala/Vimsopaka/Ashtakavarga varga-coverage). If Q3 shows
shadbala already partly per-varga, this extends it; if D1-only, this is a full build.

---

## §B — AMENDMENT 2: ga_condition → PER-VARGA DIGNITY (dignity sub-component only)

**Ruling (native):** compute the **dignity sub-component** (exaltation / debilitation / own-sign / friend /
enemy / moolatrikona, and the avastha-relevant dignity states) in **all 30 vargas**, stored as a
varga-dimensioned **dignity spread**. Keep it available for the same reason as strength: varga-specific work
needs varga-specific dignity.

**Scope boundary (strict):** the rest of the condition composite — **combustion, motion-state, the avasthas
that depend on real position (Baladi/Jagradadi by D1 longitude, Deeptadi by D1 dignity already covered,
combustion-dependent states)** — STAYS D1. These are not varga concepts. Only the dignity axis spans vargas.
Document this boundary in the composite so a reader knows dignity is per-varga but combustion/motion are D1.

**Trap-1 guardrail:** the per-varga dignity REFERENCES the varga position fact_id from ga_vargas / chart_
divisionals — it does NOT recompute the varga placement (L1-is-authority; never restate a computed value
[[feedback-canonical-or-floor-rule]] / the MSR drift handoff). It reads "graha X is in sign Y in varga Z"
from the authoritative varga asset, then applies the cited dignity rule to (X, Y).

**Sized by:** Q6 of the data investigation (does the dignity component already span vargas, or is the whole
composite D1?).

---

## §C — AMENDMENT 3: ga_sensitive → DROP varga projection; ADD classical completeness + cross-tradition shelf

**Ruling (native):** do NOT extend sensitive points to all 30 vargas (the dropped mechanical projection).
INSTEAD make the asset complete in two clearly-separated tiers:

**Tier 1 — CLASSICAL JYOTISH COMPLETENESS (core, gated, cited).** Add every missing classically-cited point.
The target universe to diff against (Q4 produces the PRESENT/MISSING table; build the MISSING + citable):
- **Upagrahas:** Gulika/Mandi + the 5 sub-Rahu kala-velas (Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu) +
  the Sun-derived set (Kala, Mrityu, Artha-Prahara, Yamaghantaka).
- **Special lagnas:** Hora Lagna, Ghati Lagna, Bhava Lagna, Vighati Lagna, Pranapada.
- **Sphuta family:** Beeja-sphuta, Kshetra-sphuta (fertility pair), Tri-sphuta, Chatu-sphuta, Panch-sphuta,
  Sookshma-Tri-sphuta.
- **Jaimini points:** Karakamsa & Swamsa (the cited varga cases — keep these), the bhava-Arudhas (12) +
  Upapada (UL) + A7/A10 if not already present.
- **Yogi points:** Yogi & Avayogi point, Yogi-graha/Avayogi-graha, Yogi/Dagdha rashi.
- **Bhrigu Bindu** (Moon–Rahu midpoint).
- **Sahams:** the full Tajik Saham set (~36: Punya, Yasha, Vidya, Jivana, Karma, Roga, Mrityu, …). **CHECK THE
  BOUNDARY** — Sahams may belong in ga_tajaka (Varshaphal) rather than ga_sensitive; Q4 reports where they live.
  Do NOT duplicate; place them in the correct asset.

Each: deterministically computed + cited to its classical source; uncited → floor NULL+reason, never fabricate.

**Tier 2 — CROSS-TRADITION SHELF (separately labeled, non-canonical, never mixed into core).** A clearly-marked
`tradition_scope: cross_system` / `non_canonical` shelf for the modern/esoteric points the native wants
available for research but NOT treated as Jyotish facts: Part of Fortune (note: maps to a Sphuta / Arabic Lot),
the other Western Lots, Vertex, Black Moon Lilith, the major asteroids. **These NEVER enter the core Jyotish
fact stream** — they live behind the cross-system label so retrieval can include-or-exclude them explicitly.
This satisfies "are we missing anything across the whole plane" without contaminating the canonical base.

**Varga rule:** Tier-1 points are D1 (their classical home), EXCEPT the cited varga cases already noted
(Karakamsa = AK-in-D9, Arudha-in-D9) which carry their cited varga. No blanket varga projection.

**Sized by:** Q4 of the data investigation (the PRESENT/MISSING diff is the literal build-list).

---

## §D — How this executes (method + sequence)

1. **Empirical baseline FIRST** — run `DATA_INVESTIGATION_PROMPT_v1_1`. It returns the three ⭐ sizing answers.
   Do NOT author writer-briefs before this; size against reality, not assumption.
2. **These amendments ARE Phase-3 enrichment of the L1 closure pass** — when the L1 closure pass runs (the
   sibling of the L0 closure pass, `L0_BRAHMAGYAN_CLOSURE_PASS_v1_0.md` template), its enrichment phase
   executes A + B + C as the high-value computable+citable gaps to build. They are NOT a standalone build.
3. **Orchestrator-native:** each is a change to the existing `@register('ga_strength')` /
   `@register('ga_condition')` / `@register('ga_sensitive')` writers under the FROZEN contract — reopening the
   asset additively (delete-then-insert per L1 idempotency), NOT a new orchestrator path. If any seems to need a
   contract change → HALT and raise.
4. **Standards inherited:** computed-and-cited HARD GATE; canonical-or-floor (per-varga shadbala =
   computed_extension label, D1-only components floored not fabricated); L1 delete-then-insert idempotency;
   seed-consistency (registry change → seed patch); no silent failures (logger.warning); target_floor =
   achieved count; only 482012f1 for native-anchored verification; FORENSIC anchors hold.
5. **L1 closes once, at the end** (after these + every other enrichment land) — never a premature seal
   ([[project-subsystem-program]] build strategy).

---

*End. Three native-ratified L1 enrichments — per-varga FULL Shadbala (honest-floored, computed-extension
labeled), per-varga dignity (dignity sub-component only, combustion/avastha stay D1), and classical
sensitive-point completeness + a labeled cross-tradition shelf (no blanket varga projection). All gated by the
empirical data baseline, all executed as Phase-3 enrichment of the L1 closure pass, all under the
computed-and-cited / canonical-or-floor spine.*
