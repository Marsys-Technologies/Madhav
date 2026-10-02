---
artifact: P5_P1_SWEEP_ANSWER
version: "1.0"
status: ANSWER (not a spec version; no code); recommendations marked MINE are not rulings
date: 2026-10-02
author: stream-B (Exec B)
question: steward M20261002T005035-cd7c — what Stream A needs next for the P5 (aṣṭakavarga) and P1 (daśā-lord) window sweeps
sources: >
  S = GOCHARA_DESIGN_SPECS_v1_4 §2.2 P1/P5, §4.0 · O = O-BP-1…5, O-PP-1…3 · R = services/gochara_rules (read this pass) ·
  ST-P5-HOLD-20261001 · AM = amendments draft v0.12 (AM-7, AM-10, AM-13, AM-15, AM-16) · corpus (served): nadi_navamsa_patel:PG2523–2525, yavana_jataka:PG943:C2.
---

# P5 and P1 — what the sweep needs, what exists, what is blocked

## P5 — aṣṭakavarga path (HELD)
* **Status.** `ST-P5-HOLD-20261001`: no P5 database writes until **1204 is applied** and **AM-7's P5 contract has landed**; until then every P5
  pin is `excluded / tier_withheld_by_ruling` (classes seal `searched_scoped`). So there is nothing for A to sweep yet — the answer is the contract A will bind.
* **Evaluators exist (mine, #2871, 76 cases):** `ashtakavarga.p5a/p5b/p5c/p5d/p5e`, `qualify_transit` (per-form states `adverse | favourable | medium |
  unresolved | unqualified | disabled`), `typed_operands`, `consume_declaration` (the O-BP-3 read-back through the 1157 declaration row). Pinned by **O-BP-1…5**.
* **What each form can deliver today (S §2.2 P5):** **P5a** = *known-zero detection only* (a known zero in the transiting graha's own BAV is adverse; any nonzero
  comparison is `unresolved`, operand named — no mean, no invented band). **P5b** = SAV bands >30 favourable / 25–30 medium / <25 adverse (`BPHS2:42332-42335`).
  **P5c disabled** (donor matrix pending the native-authorised `ga_strength` rebuild, #2731). **P5d** needs piṇḍa rows and a daśā gate. **P5e** is substrate-gated and unused.
* **Record semantics (MINE; A must not hard-code):** a P5 record is a sign-residence record (a `sign_span` target ⇒ the AM-13 membership step); its value
  is the kernel step; its **direction** comes from the form (adverse/favourable → channel via `score.channel_for` and class polarity). `medium`, `unresolved`,
  `unqualified` and `disabled` forms produce **no scored contribution** and are reported as obligation states (never as 0 or 1) — a determinate `medium` is neutral, the others are named gaps.
* **To lift the hold (conditions, not work for A now):** 1204 applied; AM-7 landed; a new generation (a sealed one is never reopened); P5c/P5d remain disabled/unqualified until their inputs exist.

## P1 — daśā-lord path (needs the L1 rebuild + three things that do not exist yet)
| Input / factor | State today | Note |
|---|---|---|
| `period_running_at` | **evaluated** (`permission.py`, pinned read `DASHA_READ_CONTRACT`) | **AM-10:** one pinned `build_id`; the L1 rebuild shifts period starts ≈ +6,993 s; the re-pin is a small evidence PR — **draft prepared** (see below); `dasha_digest` ⇒ new `input_digest` ⇒ a NEW generation |
| `natal_bhava_relationship`, `transit_relation` | evaluated / true by construction | house anchor = lagna-inclusive (AM-15) |
| `dignity_of_transit_sign` | **evaluator exists** (`dignity.dignity_of`, BPHS ch.3 śl.49–54) | **design consequence:** categories change *inside* a sign at mūlatrikoṇa degrees (Sun Leo 20°, Mars Aries 12°, Mercury Virgo 15°/20°, Jupiter Sagittarius 10°, Venus Libra 15°, Saturn Aquarius 20°) — the sweep needs **degree-crossing instants**, i.e. new fixed-degree point targets in the kernel; Moon's mūlatrikoṇa span is OCR-degraded (`unverified_ocr`) |
| `agent_nature` | evaluator exists (`nature.agent_nature`, `moon_paksa`) | Mercury's affiliation needs the (time-varying) "joined to a malefic" state |
| `maitri_compound` | **evaluator MISSING** | only `naisargika_relation` (natural friendship, BPHS ch.3 śl.55) exists; the pañcadhā compound needs the *temporary* (tātkālika) relation, which I have not read from the corpus in this pass |
| **`combustion`** | **evaluator MISSING and the degrees are not cited to a Parāśari source** | the served corpus yields a table only in a MEDIUM-provenance modern Nāḍī text (`nadi_navamsa_patel:PG2524:C1`–`PG2525:C1`: Moon 12°, Mars 17°, Mercury 14° / 12° retro, Venus 10° / 8° retro, Jupiter **12°**, Saturn 15°) and a garbled Hellenistic table (`yavana_jataka:PG943:C2`, Jupiter 11°) — **they disagree on Jupiter** and neither is the school the registry cites |

**Consequence (the blocker).** Every P1 factor is `null_state = unqualified`; `combustion` has no evaluator and no ratified degrees, so under §2.1 **every P1 window is
`unqualified` today**, however good the other four factors are. Options (**MINE**, all need the steward/native): **(1)** a native ruling that adopts a combustion table
(named source + its disagreement) = a new decision **ND-COMBUSTION** (added to `decisions/NATIVE_OPEN_DECISIONS_v1_0.md`); **(2)** a new `combustion` factor version declared
`null_state = omit` while uncited, so the factor drops out of the product with `null_states_used = ['omit']` disclosed (a declared change, not a silent 1); **(3)** leave P1 unqualified.
Recommendation: **(1) with (2) as the interim** — the honest disclosure is cheap and P1 is the only path that uses the period lord at all.
Also **combustion is a Sun-conjunction interval**, not a residence span: it needs kernel contact episodes with the Sun at per-graha orbs — a new relation, not `ORB_TABLE`'s.

## Sweep inputs A needs after the L1 rebuild (checklist)
1. the new pinned daśā `build_id` (AM-10 re-pin, evidence-gated); 2. period rows MD/AD/PD with the §4.0 duplicate rules; 3. the lord's residence spans **plus** degree-crossing
instants for dignity (new point targets); 4. Sun/malefic conjunction state for Mercury; 5. a combustion source (ND-COMBUSTION) or the `omit` interim; 6. the pañcadhā compound
(tātkālika rule to be read); 7. `maitri_compound`/`combustion` evaluators (Stream B work, blocked on 5–6).
**Not constrained by the 3.0-vs-controls measurement** — these are factor-availability questions; P1's *breadth* (any graha can be a period lord) is what T-FP will test later.
