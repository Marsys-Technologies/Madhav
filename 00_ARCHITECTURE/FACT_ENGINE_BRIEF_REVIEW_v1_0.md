---
artifact: FACT_ENGINE_BRIEF_REVIEW_v1_0.md
document: Engineering Review & Amendments — FACT_ENGINE_PYJHORA_BRIEF v1.0
status: DRAFT (review — pending native approval; modifies nothing canonical)
version: 1.0
date: 2026-05-27
reviews: 00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md
relates_to:
  - 00_ARCHITECTURE/BRIEFS/JYOTISH_ENGINE_SCOPE_CATALOGUE_v1_0.md
  - 01_FACTS_LAYER/SOURCES/JHORA_TRANSCRIPTION_v8_0_SOURCE.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md
verdict: "Brief spine ADOPTED. Seven amendments required before implementation. R1 is load-bearing."
expose_to_chat: false
---

# Engineering Review — FACT_ENGINE_PYJHORA_BRIEF v1.0

## Verdict

The brief's spine is correct and should be kept verbatim: JSONL-in-between (auditable,
diffable, content-addressed, gated before serving); wrap-don't-trust with a per-function
typed adapter + unit tests; integers/decimal-strings not floats; modular-replacement on
PyJHora module failure; Phase-0 ayanamsha gate. The amendments below correct an oracle-design
flaw (R1, load-bearing) and tighten precision on validation, isolation, and generality.

---

## R1 — [LOAD-BEARING] FORENSIC v8.0 is a dual-engine reconciliation, not pure JH. Fix the oracle.

**Finding.** The brief uses FORENSIC v8.0 as the regression oracle and says "diff field-by-field
against FORENSIC" (§4.1). FORENSIC's own frontmatter declares a `dual_engine_policy`, and in
three sections it deliberately chose FORENSIC-engine values over JH and recorded *both*:

- **§5.1 Vimshottari dates** (GAP.09): FORENSIC dates canonical, **+7 to +9 days later than JH**.
- **§6.2 Shadbala** (GAP.07): JH *ranking* authoritative; the rupa/virupa *columns* are FORENSIC-engine.
- **§7.1 Moon BAV** (GAP.08): FORENSIC BAV canonical; JH differs in 4 signs (carried as `AVG.BAV.MOON.JH`).

A PyJHora engine models JH, so it will reproduce the JH values and **systematically "fail" the
FORENSIC diff in exactly these sections — not because of a bug, but by policy.**

**Fix.** Primary oracle = `JHORA_TRANSCRIPTION_v8_0_SOURCE.md`. Where a field also exists in
FORENSIC, gate against the **JH-side of FORENSIC's dual columns**, never the FORENSIC-canonical
value in reconciled sections. Build an explicit `oracle_map`: per FORENSIC field → which value
is the JH target. FORENSIC remains a useful oracle *only* for fields where FORENSIC == JH.

**Downstream decision for the native (not the executor).** Strict JH authority moves every
Vimshottari boundary 7–9 days earlier. The LEL retrodictive calibration (GAP.09: Sessions
16–25 fit life-events to the *FORENSIC* dates) was tuned to the later dates. Choose one:
(a) re-fit LEL against JH dates, or (b) keep FORENSIC dates as a **declared override** of the
JH-authority rule for dasha timing only. Document whichever, so it is not silent drift.

---

## R2 — Triangulation is NOT independent on the ayanamsha axis.

**Finding.** §4.2 claims PyJHora + pyswisseph agreeing = absolute confidence. Both call the same
Swiss Ephemeris ayanamsha tables, so on the ayanamsha *constant* they are not independent —
they will agree with each other and both can still differ from JH-desktop's 23°37′09.78″.

**Fix.** The ayanamsha gate is against the **JH transcription value**, not the PyJHora↔pyswisseph
agreement. Triangulation remains valid and valuable for positions, ascendant, cusps, and
adapter-reading (index vs name) — state its scope honestly.

---

## R3 — "Absolute accuracy via triangulation" is a category error for Tier 3.

**Finding.** pyswisseph computes astronomy, not Shadbala, Ayurdaya haranas, or Nadiamsa. Tier-3
derived quantities have no independent second engine.

**Fix.** Declare Tier-3 as **single-oracle JH-parity** (match JH; where JH's formula is
under-documented, reverse-engineer from JH outputs and record the residual). Direct the extra
JH reference charts (R5) specifically at the no-cross-check Tier-3 modules and at stress
geometries (high latitude, clear day vs night birth, near-cusp ascendant, retrograde-heavy,
vargottama edges). Single-chart validation can pass by luck.

---

## R4 — "Clean parallel build" vs "same tables, schema unchanged" collide. Make isolation explicit.

**Finding.** Frontmatter `build_mode: clean parallel build — leaves current corpus intact`, but
§1.2 writes into the same Postgres tables with the same schema. For the same `chart_id` that is
not parallel — it overwrites.

**Fix.** Land the parallel build in an isolated namespace (separate schema, or a distinct
`chart_id`/`build_id`), validate, then perform a **deliberate cutover**. Apply existing scar
tissue: enumerate ALL FK dependents before any swap; idempotency guard checks the actual write
target (not a sibling/staging table). Retrieval-tool read-compat is verified against the
isolated namespace before cutover.

---

## R5 — Multi-chart golden set: use the native's additional JH exports deliberately.

**Finding.** §4.3 wants "2–3 reference charts" but understates sourcing. Native has agreed to
produce more JH exports.

**Fix.** Make the golden set = Abhisek + native-supplied JH exports chosen as **stress charts**
(see R3 list). Snapshot each as golden-master JSONL; any engine/library bump diffs against all.

---

## R6 — Input contract must generalize beyond IST.

**Finding.** §0/§1.3 hardcode `datetime_IST`. The engine is "for all future clients."

**Fix.** Input = local civil time + **IANA timezone** (or explicit UTC offset), resolved through
a historical tz database (LMT/DST/half-hour-zone trap). Carry `tz` in provenance. Indian-only
today, but the schema must not assume it.

---

## R7 — The JSONL→L1.md renderer is unwritten (second projection).

**Finding.** Brief covers JSONL→DB loader; the native's chosen output contract was
"canonical JSON + renderer." The human-readable L1.md regeneration is missing.

**Fix.** Add a **renderer** as a second deterministic projection off the same JSONL, parallel to
the loader: JSONL → FORENSIC-schema `.md` (stable IDs MET.*/PLN.*/…). Same source, two
projections (DB + markdown); neither is a source of truth.

---

## R8 — Reproducibility assertions (additive to §3.2).

- Assert the **actual ephemeris source used** per run (swe returns it); fail hard if the Moshier
  analytical fallback silently activates because de440/de431 files are absent in the container.
- Per-section **ayanamsha is a config table, not a constant**: Lahiri (pinned to JH's epoch
  value) default; **Krishnamurti for the KP section** (the FORENSIC §4 12°29′19″ vs JH D1
  12°25′21.62″ gap evidences it) + Placidus cusps for KP only.

---

## Sequencing impact

Phase 0 deliverable is sharper: not "an ayanamsha" but **(a)** the exact `swe` sidereal flag +
custom delta reproducing JH's 23°37′09.78″ at native epoch, **(b)** the per-section ayanamsha
map, **(c)** the `oracle_map` (R1). Phases 1–6 otherwise stand. Add R4 isolation as a gate
before Phase 4 (loader) and R7 renderer alongside Phase 4.
