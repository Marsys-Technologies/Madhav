---
artifact: L1_ENRICHMENT_AMENDMENTS_v2_0.md
canonical_id: L1_ENRICHMENT_AMENDMENTS
version: 2.0
status: CURRENT
supersedes: L1_ENRICHMENT_AMENDMENTS_v1_0.md
authored_by: Cowork (planning) 2026-06-17
authored_for: the L1 closure pass — Phase-3 enrichment of ga_strength / ga_condition / ga_sensitive
grounded_in: L0_L1_DATA_INVESTIGATION_v1_0.md (empirical baseline, ran 2026-06-17 against prod 482012f1)
governing_memory: feedback-l1-per-varga-strength-dignity, feedback-canonical-or-floor-rule, feedback-l1e-full-relationship-graph
purpose: >
  v2.0 REVISES the three L1 enrichment amendments against ACTUAL prod data. The investigation overturned two of
  three v1.0 assumptions: dignity-per-varga is ALREADY complete (1,350 rows, all 30 vargas) and shadbala already
  has a partial varga substrate. Scope is now data-grounded, narrower, and more precise. This IS Phase-3
  enrichment of the L1 closure pass.
---

# L1 Enrichment Amendments v2.0 — DATA-GROUNDED scope

## §0 — What the data changed (vs v1.0)

The empirical baseline (`L0_L1_DATA_INVESTIGATION_v1_0.md`) overturned two of three v1.0 assumptions. This is
the value of "find from the data, not the docs":

| v1.0 assumption | What the data actually shows | Revised scope |
|---|---|---|
| Dignity is D1-only → build per-varga | `graha_dignity_per_varga` = **1,350 rows, ALL 30 vargas** × 9 grahas × 5 ayanamshas. ALREADY DONE — most varga-complete dataset in L1. | **Amendment 2 is moot as written.** Real gap = **avasthas** are D1-only. |
| Shadbala is D1-only → build full per-varga, all 30 | Partial varga substrate EXISTS: saptavargaja-bala for 7 Saptavarga vargas + Vimsopaka per-varga contribution for 16 Shodasavarga vargas (both in `chart_divisionals`). Shadbala in `chart_facts` = D1 rolled-up. | **Narrower.** Extend positional components to gap-vargas; Ashtakavarga per-varga is the clean win. |
| Sensitive points: complete the classical set | Confirmed ALL D1-only. Inventory shows MORE present than assumed; exact small missing-list. | **Tight build-list** (below). |

The honest-floor rail (v1.0) is now **vindicated by data, not just anticipated**: Kala/Cheshta-bala genuinely
have no per-varga canonical method — confirmed D1 concepts.

---

## §A — AMENDMENT 1 (REVISED): ga_strength — targeted varga extension, NOT "all 30 shadbala"

**Data baseline (Q3):** Shadbala in `chart_facts` is D1-only rolled-up (`rupa` per component per graha per
ayanamsha). BUT a partial per-varga substrate already exists in `chart_divisionals`: `varga_saptavargaja_bala_
component` for the 7 Saptavarga vargas (D1/D2/D3/D9/D12/D30/D60), and `varga_vimsopaka_contribution` for the 16
Shodasavarga vargas. Ashtakavarga is D1-only.

**Revised build (three parts, in value order):**

1. **⭐ Per-varga Ashtakavarga (BAV/SAV) — the clean win.** Ashtakavarga is currently D1-only. Computing BAV
   (and SAV) for the key vargas — at minimum **D9** (the most classically consulted), ideally the Shodasavarga
   set — is fully deterministic, classically meaningful (varga-strength via bindu count), and CITABLE. This is
   the highest-value strength enrichment the data reveals. Build it.

2. **Positional Shadbala components to gap-vargas.** Extend the **positionally-derived** components —
   **Sthana-bala** (incl. the saptavargaja element, already partial), **Dig-bala**, **Drik-bala** — to the
   vargas that currently lack a contribution row (the non-Shodasavarga vargas: D5, D6, D8, D11, D14, D15, D21,
   etc.). These are computable from that varga's own house/aspect geometry. Labeled `computation_tier:
   computed_extension`.

3. **Kala-bala & Cheshta-bala — FLOOR per varga, do NOT fabricate.** CONFIRMED by data as D1-only concepts
   (Kala = birth-time-derived; Cheshta = real-motion-derived). No canonical per-varga method exists → store
   `floored: no_canonical_per_varga_method` per varga, never a plausible substitute
   ([[feedback-canonical-or-floor-rule]]). The honest-floor rail, vindicated.

**Sized:** much narrower than v1.0's "full Shadbala × 30." The real deliverable is per-varga Ashtakavarga +
positional-component extension. Reopens ga_strength as the 2nd L1 asset in L1-E
([[feedback-l1e-full-relationship-graph]]).

---

## §B — AMENDMENT 2 (REVISED): dignity-per-varga is DONE → the real gap is per-varga AVASTHAS

**Data baseline (Q6):** `graha_dignity_per_varga` ALREADY covers all 30 vargas (1,350 rows). **There is nothing
to build for dignity-per-varga.** The investigation found the condition composite is assembled from 9
`chart_facts` categories (no `ga_condition_composite` table); the avastha categories
(`graha_avastha_baladi/deepta/jagrad/sayanadi/lajjitadi`) are **D1-only (45 rows each)**.

**Revised build — per-varga avasthas, split by computability (the dignity-vs-combustion logic, applied to
avasthas):**
- **Varga-COMPUTABLE avasthas → build per varga:** **Baladi** (infant/youth/old — derived from the graha's
  longitude-position-in-sign, which exists per varga) and **Deeptadi** (Deepta/Svastha/… — derived from dignity,
  and dignity already spans all 30 vargas, so this is directly computable from the existing
  `graha_dignity_per_varga`). These have a real per-varga meaning.
- **Intrinsically-D1 avasthas → leave D1, store reason:** **Jagradadi** (waking/dreaming — a single-state
  concept), **Sayanadi** (the 12 sleeping/posture states), **Lajjitadi** (depend on D1 conjunction/aspect
  context). No canonical per-varga method → floor with reason, do not fabricate.

**Boundary note:** combustion is encoded in `graha_position.combustion_state` (D1, correct — no combustion in
D9). Motion-state likewise D1. So the per-varga axis for the composite = dignity (done) + the two computable
avasthas (Baladi, Deeptadi) — everything else stays D1 by classical correctness.

**Trap-1 guardrail:** per-varga Deeptadi READS the existing `graha_dignity_per_varga` fact (references the
fact_id), never recomputes dignity. L1-is-authority.

---

## §C — AMENDMENT 3 (REVISED): ga_sensitive — the EXACT missing-list (small, high-confidence)

**Data baseline (Q4):** ALL sensitive points are D1-only today (confirmed — varga projection correctly
dropped). Inventory is richer than v1.0 assumed. The exact diff:

**Already present (do NOT rebuild):** 5 Rahu-derived upagrahas (Dhuma/Indrachapa/Parivesha/Upaketu/Vyatipata),
Bhrigu Bindu + 8 Bhrigu Chakra points, all 12 Bhava Arudhas + A7/A10 + 7 graha arudhas, Karakamsa + 8 chara
karakas, Pranapada, 70 Sahams, Tri/Chatu/Pancha/Mrityu/Trikona-dasha sphuta, Yogi & Avayogi points, KP lords,
1,080 midpoints, Tajik hadda/triraashipathi data. Also note `aprakasha_position` holds DHWAJA/KANDANGA/PATALA/
PIDAA/VIGHNI (the 5 aprakasha grahas — DISTINCT from the Sun-derived upagrahas; do not conflate).

**GENUINELY MISSING — the Tier-1 classical build-list (all D1, all deterministic, all citable):**
1. **Gulika/Mandi POSITIONAL** — only `panchanga_gulika_kalam` (the Kalam time-window, 3 rows) is stored; the
   **positional longitude + sign + house of Gulika and Mandi** as sensitive points is absent. High value
   (Gulika is heavily used classically). Build the placement.
2. **Sun-derived upagrahas:** **Kala, Mrityu, Artha-Prahara, Yamaghantaka** — absent from both `upagraha_
   position` and `aprakasha_position`. Compute from the standard day-portion divisions, cited.
3. **Special lagnas:** **Hora Lagna, Ghati Lagna, Vighati Lagna, Bhava Lagna** — absent from `chart_facts`
   (only D9-lagna-special exists in chart_divisionals). Compute from birth time + ascendant, cited.
4. **Sphuta family completion:** **Beeja Sphuta & Kshetra Sphuta** (the fertility/reproductive pair) — absent
   (the other sphutas are present). Compute, cited.
5. **Yogi system completion:** **Yogi Graha** (the lord of the Yogi nakshatra) and **Dagdha Rashi** — the Yogi/
   Avayogi *points* exist but these two derived records are absent. Compute, cited.

**Tier-2 cross-tradition shelf (separately labeled, non-canonical, NEVER mixed into core):** Part of Fortune
(note: relates to a sphuta/Arabic Lot), other Western Lots, Vertex, Black Moon Lilith, major asteroids. Stored
behind `tradition_scope: cross_system` so retrieval includes/excludes explicitly. Satisfies "are we missing
anything across the whole plane" without contaminating the canonical base.

**Saham cross-check (non-blocking):** 70 Sahams present; a per-saham audit vs the standard ~36 Tajik set can
confirm none of the classical core is missing — log as a verification task, not a build.

---

## §D — How this executes

1. **Data baseline = DONE** (`L0_L1_DATA_INVESTIGATION_v1_0.md`). Scope above is grounded in it.
2. **These ARE Phase-3 enrichment of the L1 closure pass** (the sibling of the L0 closure pass). They execute
   as that pass's enrichment build — not a standalone workstream.
3. **Orchestrator-native:** changes to the existing `@register('ga_strength')` / `@register('ga_condition')` /
   `@register('ga_sensitive')` writers under the FROZEN contract; additive, delete-then-insert idempotency. If
   any needs a contract change → HALT and raise.
4. **Standards:** computed-and-cited HARD GATE; canonical-or-floor (computed-extension labels on per-varga
   strength/avastha; Kala/Cheshta + intrinsically-D1 avasthas floored-with-reason, never fabricated);
   L1-is-authority (per-varga Deeptadi references `graha_dignity_per_varga`, never recomputes); seed-consistency
   (registry change → seed patch); no silent failures (logger.warning); target_floor = achieved count; only
   482012f1; FORENSIC anchors hold.
5. **L1 closes once, at the end** — after these + all other enrichment land.

---

## §E — Net scope summary (the actual build, post-data)

| Amendment | v1.0 said | v2.0 (data-grounded) |
|---|---|---|
| 1. Strength | Full Shadbala × 30 vargas | **Per-varga Ashtakavarga (D9+) [clean win]** + positional components (Sthana/Dig/Drik) to gap-vargas + Kala/Cheshta floored |
| 2. Dignity/condition | Per-varga dignity (all 30) | **MOOT (already done)** → build per-varga **Baladi + Deeptadi** avasthas; other avasthas floored D1 |
| 3. Sensitive points | Complete classical set + shelf | **Exact 5-item build-list:** Gulika/Mandi positional · Sun-upagrahas (Kala/Mrityu/Artha-Prahara/Yamaghantaka) · special lagnas (Hora/Ghati/Vighati/Bhava) · Beeja+Kshetra sphuta · Yogi Graha + Dagdha Rashi · + cross-tradition shelf |

*End v2.0. The data narrowed and sharpened all three — dignity-per-varga was already complete, strength's real
win is per-varga Ashtakavarga, and the sensitive-points gap is a tight 5-item classical build-list plus a
labeled cross-tradition shelf. All under the computed-and-cited / canonical-or-floor spine, all as Phase-3 of
the L1 closure pass.*
