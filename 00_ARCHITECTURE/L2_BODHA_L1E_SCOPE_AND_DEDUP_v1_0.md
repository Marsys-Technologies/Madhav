---
artifact: L2_BODHA_L1E_SCOPE_AND_DEDUP_v1_0.md
canonical_id: L2_BODHA_L1E_SCOPE_AND_DEDUP
version: 1.0
status: PLAN_FOR_NATIVE_REVIEW
authored_by: Cowork (planning) 2026-06-16
companion_to: L2_BODHA_MASTER_PLAN_v3_0.md (expands §2 L1-E + adds the dedup design)
native_decisions_encoded:
  - "DEDUP PRINCIPLE: capture-once-reference-many. Every fact has exactly ONE owner; everything else
     references it by fact_id, never re-stores it."
  - "DERIVED-RELATIONSHIP TAIL: derive ALL structurally-valid relationships, store strength as a column,
     NEVER drop (no-threshold-drop). Dedup removes only TRUE restatements of an already-owned value."
  - "Never lose a signal; do not blindly duplicate. Optimize via ownership + reference, not via dropping."
---

# L1-E Scope + De-duplication Design v1.0

## §1 — The de-duplication design (capture-once, reference-many)

### Ownership rules (these decide who stores what — no ambiguity)
1. **A raw value is owned by the asset that computes it.** Saturn shadbala=0.4 → owned by `ga_strength`,
   ONE fact_id, forever. Nothing else re-stores the number.
2. **A relationship is owned by `ga_structural`.** A row is a relationship ONLY if it expresses a tie
   between ≥2 elements. "Saturn aspects 10th-lord" = relationship (stored). "Saturn is weak" = a property,
   already owned by ga_strength (NOT re-stored; referenced).
3. **A signal is owned by `bo_laksana` (MSR)** and is a PROJECTION, never a new fact. It references its
   L1 fact_id(s) via `constituent_facts_array`.

### The Trap-1 guardrail = the dedup rule at L1
When ga_structural ingests another asset's fact, it emits a row **only if that row is a NEW relationship**.
If what it would emit is a restatement of one source fact's value, it emits NOTHING — it references the
source fact_id in the derivation provenance of whatever relationship consumed it. **One truth → one
fact_id.** This makes the anti-drift spine trivially true and prevents the duplicate at its origin.

### The dedup rule at MSR (the real risk point — MSR reads BOTH ga_structural and the individual assets)
- A magnitude signal (from ga_strength) and a relationship signal (from enriched ga_structural that USED
  that magnitude) are **NOT duplicates** — different `fact_kind`, different fact. Both kept. (This is the
  completeness you want.)
- Two signals are DUPLICATES iff: **same `fact_kind` AND same `constituent_facts_array` AND same
  `configuration`**. Enforce via a dedup check at insert (or a unique index on the natural key). Collapse
  those; keep everything else.
- A weak-but-real relationship is NEVER a duplicate of anything → always kept (no-threshold-drop).

### Why this is efficient (not just correct)
Relationship rows carry POINTERS to the magnitudes they used, not copies → storage stays lean; the spine
can never be ambiguous (one fact_id per truth); and at query time the LLM can follow a relationship
signal's pointer to its exact quantitative basis — getting the relationship AND its numbers without
storing the number twice.

### Derived-relationship tail policy (native decision)
Derive EVERY structurally-valid relationship; store its strength/salience as a COLUMN; NEVER drop. Dedup
removes only true restatements, never weak-but-real relationships. Max completeness, ranked, none lost.

---

## §2 — L1-E scope: exactly what NEW relationships each ingested asset yields
For each asset: what ga_structural INGESTS (reads), what NEW RELATIONSHIPS it derives (stores, citing
source fact_ids), and what it must NOT do (the dedup/Trap-1 line). "Genuine tie" = the two elements stand
in a defined classical relation (aspect / conjunction / lordship / dispositor / argala / co-tenancy /
significator); strength is then a column on that tie, not a gate.

### 2.1 — ga_strength (shadbala, ashtakavarga, bhava-bala, ishta/kashta, vimsopaka)
**Ingest:** per-graha shadbala totals + components, per-house ashtakavarga bindus, bhava-bala, ishta/kashta
phala, vimsopaka.
**New relationships derived (each cites the strength fact_id + the structural fact_id of the tie):**
- **Strength-weighted aspect/conjunction:** for every EXISTING aspect/conjunction in ga_structural, a
  derived row "graha A (shadbala s_A) aspects/conjoins graha B (shadbala s_B)" with a tie-strength column
  = f(existing orb/aspect strength, s_A, s_B). (Tie already exists; we annotate it with the strength
  relation — NOT a new pair, an enrichment edge referencing both the aspect fact_id and the two strength
  fact_ids.)
- **Ashtakavarga-supported vs starved house occupancy:** "graha in house H, H has B bindus" → relationship
  graha↔house-support (tie = occupancy, already structural; enrich with bindu relation).
- **Strength-modulated yoga participation:** for each fired yoga, "participant graha's shadbala
  contribution to the yoga" (tie = yoga membership; enrich).
- **Relative-strength ordering ties:** "graha A stronger than graha B" pairwise where it changes a
  dispositor/lordship consequence (a genuine comparative tie that affects outcomes).
**Must NOT:** re-store the bare shadbala number as a structural row (ga_strength owns it). The magnitude
becomes a SIGNAL at MSR by projecting ga_strength directly — not by ga_structural restating it.

### 2.2 — ga_sensitive (non-ingested part: KP significators, arudha padas, swamsa, karakamsa)
*(chara-karaka + upagraha already ingested today.)*
**Ingest:** arudha padas (12), karakamsa, swamsa, KP cuspal significators, KP ruling planets.
**New relationships derived:**
- **Arudha↔graha / arudha↔house ties:** "AL (arudha lagna) in sign S, graha G aspects AL" (genuine
  aspect tie to a derived point).
- **Karakamsa significator ties:** "karakamsa in sign S; its lord / occupants / aspects" (the classical
  karakamsa-reading relationships).
- **Swamsa ties:** swamsa-to-graha aspect/occupancy relationships.
- **KP significator chains:** "cusp C's significator chain → graha → star-lord → sub-lord" (KP's defining
  relational structure — genuinely relational, currently un-projected).
**Must NOT:** re-store the bare arudha/karakamsa POSITION as a structural row (ga_sensitive owns it);
derive only the TIES involving it.

### 2.3 — ga_sade_sati (cycles, phases, quarters, overlays)
**Ingest:** sade-sati cycle/phase/quarter rows, modifier overlays, retrograde subsets, cancellation checks,
concurrent-dasha overlays.
**New relationships derived (STRUCTURAL tie only; temporal ACTIVATION is L3 Kāla, not here):**
- **Sade-sati-affected natal relationships:** "Saturn's transit over Moon's 12th/1st/2nd structurally
  ties to natal Moon-significations" — the STRUCTURAL tie (Saturn↔Moon-house), flagged
  `sade_sati_relevant=true`. The WHEN (which dates) is L3; here only the structural tie + the flag.
- **Cancellation-relationship:** where a sade-sati cancellation rule depends on a structural config, store
  the tie (config↔cancellation), citing the sade-sati fact_id.
**Must NOT:** store the time-windows/phases as structural rows (ga_sade_sati owns them; they project to
MSR as `fact_kind=time_window` signals directly). Do NOT compute temporal activation (that's L3).

### 2.4 — ga_panchanga (tithi, vara, yoga, karana, nakshatra, hora, choghadiya, agni-vasa, etc.)
**Ingest:** birth-moment panchanga facts.
**New relationships derived (birth-moment structural ties):**
- **Panchanga-yoga ↔ graha ties:** the yoga's lord/significator relationships to natal grahas.
- **Tithi/vara lord ↔ chart ties:** "vara-lord (e.g. Sun for Ravivara) — its natal house/strength tie."
- **Nakshatra-lord ties:** Moon's nakshatra-lord → its placement/aspect relationships.
**Must NOT:** re-store the bare tithi/vara/yoga VALUE as a structural row (ga_panchanga owns it; projects
to MSR as `fact_kind=birth_moment` directly). Only the relational ties.

---

## §3 — What MSR ends up with (the completeness picture, de-duplicated)
Per (chart, ayanamsha), MSR signals = the UNION of:
- **relationship signals** ← enriched ga_structural (incl. all the new derived ties above), `fact_kind=relationship`
- **magnitude signals** ← ga_strength projected directly, `fact_kind=magnitude`
- **position signals** ← ga_sensitive/ga_positions projected directly, `fact_kind=position`
- **time_window signals** ← ga_sade_sati projected directly, `fact_kind=time_window`
- **birth_moment signals** ← ga_panchanga projected directly, `fact_kind=birth_moment`
Each references its owning L1 fact_id(s); no value restated twice; relationship signals point to the
magnitudes/positions they used. Dedup collapses only same-kind+same-constituents+same-config rows.
**Result: every signal type captured at its own grain, every relationship captured, zero true duplicates.**

---

## §4 — Acceptance additions (on top of master plan)
- **L1-E dedup proof [verify-against: prod]:** no ga_structural row restates a single source asset's bare
  value (every new row has ≥2 constituent elements OR is an enrichment edge citing the source fact_id);
  spot-check 10 derived rows resolve their cited source fact_ids.
- **MSR dedup proof:** zero signals share (fact_kind, constituent_facts_array, configuration); a deliberately
  duplicated input collapses to one row (proving the dedup works); weak-but-real relationship signals are present.
- **No-loss proof:** count of distinct L1 fact_ids referenced across all MSR signals == count of projectable
  L1 fact_ids (every L1 fact is represented by ≥1 signal; relationships add MORE signals, never fewer).

---
*End of L2_BODHA_L1E_SCOPE_AND_DEDUP v1.0. Dedup by ownership (capture-once-reference-many): raw values
owned by their computing asset, relationships owned by ga_structural (≥2-element ties only, citing source
fact_ids), signals owned by MSR (projections referencing L1 fact_ids). Derived-relationship tail: derive
all real ties, rank by strength column, never drop. No signal lost; no value stored twice; the only
collapse is same-kind+same-constituents+same-config. Per-asset L1-E scope enumerated for native approval.*
