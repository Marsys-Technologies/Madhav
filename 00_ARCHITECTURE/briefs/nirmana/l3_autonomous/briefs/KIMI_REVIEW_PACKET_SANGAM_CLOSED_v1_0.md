---
title: "KIMI_REVIEW_PACKET_SANGAM_CLOSED_v1_0"
version: "1.0"
status: SENT
role: review_request
owner: "L3 Saṅgam design session (madhav-d9)"
layer: L3
asset: ka_sangam
description: "Adversarial review request sent to Kimi K3 (effort=max, Kimi CLI) on the CLOSED Saṅgam packet — plan v1.0, the seven native rulings as applied, and the author's eight delegated decisions D-1…D-8."
---

# Review request — Saṅgam elevation, CLOSED packet

You reviewed the seven Saṅgam decisions earlier today (`KIMI_K3_RECOMMENDATIONS_SANGAM_DECISIONS_v1_0.md`,
effort=max). Since then the native ruled all seven, then **delegated the residual open items to the
author in writing**. The author decided them as **D-1…D-8**. The packet is now CLOSED.

**This is an adversarial review, not a ratification.** The most valuable thing you can do is find
what is wrong. Two bodies of text have never been reviewed by anyone:

1. **Plan v0.4** — the text plan v1.0 is built from. v0.1 returned REWORK (F-01…F-19). v0.3 returned
   REWORK (RR-01…RR-10). v0.4 was written to answer the second REWORK and **no reviewer has seen it.**
2. **D-1…D-8** — the author's decisions under delegation. On M-6 you deliberately declined to name a
   number ("the number is yours **[NATIVE-RATIFY]**"); the author has now named one. **Attack it.**

## Read these (repo root = the working directory)

- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v1_0.md` — plan v1.0 = v0.4 + §0R (rulings applied). §0R is new; everything below it is v0.4 verbatim.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_RULING_SHEET_v1_0.md` — §CLOSE carries the native's delegation quoted verbatim and **D-1…D-8 with reasoning**; §RULINGS carries the seven; §Corrections carries today's source-verified corrections.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/SANGAM_ALGORITHM_ELEVATION_PLAN_v0_3.md` and `ASTRA_REVIEW_SANGAM_ALGO_PLAN_v0_3.md` — the prior text and the REWORK it had to answer (RR-01…RR-10).
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/evidence_sangam/` — the evidence scripts (S1–S13) and their MANIFEST/RUN_ALL harness.
- Code, if you want to check a claim: `platform/python-sidecar/services/ka_sangam/engine.py`, `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py`.

## Premises established at source today — verify, do not trust

These corrected earlier errors in this packet. Each was measured; re-check any you rely on.

- The ingested corpus is **15 texts** in `classical_text_chunks` (phaladeepika 564 chunks, bphs 1459, …). The earlier "admitted corpus = BPHS, Jaimini Sūtram, KP, KP_Reader" was a **directory listing**, not the corpus, and **no `kp`/`kp_reader` text_id exists in the table at all.**
- **Method rule, learned the hard way:** a corpus-absence claim is made by `count(*)` against the table naming the predicate — never from a directory, never from the search tool (a `top_k=5` search returned zero rows for material with 17 matching rows). Four independent sessions agreed on a false premise for a day because every check ran against another session rather than against the object.
- Vedha admission outcome is now **per `vedha_kind`**: laṭṭā (PG338-339) and the malefic scale (PG353) are corpus-verifiable; house-vedha's 41 `bg_transit_rules` rows are **39× mis-cited to "BPHS Ch.29"** over content verbatim at Phaladīpikā XXVI PG322-323 (→ `applied` on L0 re-citation); sarvatobhadra has a primary source (XXVI śl. 48, PG345-352) but the grid tables are unpopulated.
- **Node dṛṣṭi:** Santhanam Ch.26 names Saturn/Jupiter/Mars only — zero rāhu/ketu/node occurrences in the chapter span (254 in the file). The "BPHS Ch.26" citation behind the live Gochara implementation is **refuted**. `_W30_NODAL_DRISHTI_ENABLED = True` and `w30_modifier` is a live multiplicative term in `raw_lambda` (`gochara_v3/engine.py:107, :632`), so removing it invalidates every stored λ.
- M-2's "Phaladīpikā 23.11" resolves to `phaladeepika:PG299:C1`; **3 and 4 both read "fear"** there, so the 4/≤3 boundary rests on the BPHS bands, not on that śloka.

## The seven rulings as delivered (the native's words, verbatim)

```
M-1: agree — mean node; Placidus-as-stored; retire legacy scan after one generation; no node dṛṣṭi
M-2: agree, but 4 leans adverse; 6/8/12 inversion does not ship
M-3: agree — §4.5 governs; owner = Gochara stream (kernel path if N-7 approved); E3 tier granted
M-7: agree
M-4: agree, but D30 for DOSHA held
M-5: agree
M-6: agree; minimum n = <your number>
```

(M-6's placeholder was never filled; that is why it was delegated.)

## Questions — answer each explicitly

**Q1 — Did v0.4 actually close the v0.3 REWORK?** Walk RR-01…RR-10. For each: closed, partially
closed, or not closed, with the evidence. This has never been checked by anyone.

**Q2 — D-1, the E6 gate numbers. Attack the arithmetic and the design.**
The author set: **n=30** fully-observed non-censored windows per `(domain × route × method_version)`
stratum — your stratum shape — and **n=100** for an instrument-level claim pooled across domain and
route within ONE frozen `method_version`, `method_version` never pooled; below either →
`PROVISIONAL_INSUFFICIENT_N` carrying actual n; thresholds recompute at equal power if the measured
base rate ≠ 0.20.
- Is the claim "n=30 gives ≈80% power to detect 0.20 → 0.40 at α=0.05 one-sided, critical ≥10 hits"
  arithmetically correct? Same for "n=100 → ≈85% for 0.20 → 0.32". Show your working; if either is
  wrong, give the right number.
- **Pooling hazard:** the instrument-level claim pools strata with potentially different base rates
  and different exposures. Is that vulnerable to Simpson's paradox — a pooled lift no stratum has, or
  a real per-stratum lift masked? If so, what is the minimal fix that keeps the gate reachable?
- Was declining to name a number the better answer, and has the author made it worse by naming one?

**Q3 — D-1 vs D-3: is my own gate self-defeating?** D-3 restricts evaluation to **consenting charts
with real outcome records — today two charts**. D-1 demands n=30 *per stratum*. Can two charts
generate 30 fully-observed non-censored windows per `(domain × route × method_version)` in any
realistic horizon? If not, say so plainly: the per-stratum gate may be unreachable by construction,
which would make `EMPIRICALLY_EVALUATED` a gate that can never open — a status with no achievable
detector, which this project's §N.8 forbids.

**Q4 — D-2's 20% censoring ceiling.** Principled or arbitrary? What happens at 19.9%? Is
"`ambiguous` → censored, excluded from n" right, or does censoring-not-scoring itself introduce a
bias (informative censoring: the cases hardest to adjudicate may be systematically the near-misses)?
If informative censoring is the real risk, what does the packet need that it does not have?

**Q5 — D-4, the shape of a HELD ruling.** The native held D30 for DOSHA. The author kept D30
**computed, stored, labelled `secondary_dosha`, excluded from every score path**, with the falsifier
"any D30 term in a DOSHA score path fails the suite." Is that faithful to a *hold*, or a backdoor
adoption of something the native declined? Is the falsifier sufficient to keep it out of scoring, or
is there a path it does not cover?

**Q6 — D-5, the pāda entailment.** The author reasoned: if the served node is L1's `RAH_MEAN`, every
derivation of it — sign, nakṣatra, pāda — follows from it, so Rāhu's pāda for this chart is Rohiṇī
**pāda 3**, with the true-node value (pāda 4) retained as a declared variant and the 177″
disagreement published. **Is the entailment as clean as claimed?** Is there any legitimate classical
practice in which a chart serves the mean node's longitude but reads a nakṣatra/pāda from the true
node — and if so, does the author's inference overreach?

**Q7 — D-6's scope, after correction.** Originally written as "instrument-level doctrine"; corrected,
at the Gochara session's insistence, to bind Saṅgam and state a cross-stream *position*, with the
Gochara family's application left to that stream's own native ruling. Is the corrected scope right,
or is it now too weak to prevent one instrument holding two contradictory doctrines?

**Q8 — The rulings as applied (§0R).** For each of M-1…M-7, does the plan's stated effect actually
follow from the native's words, or does any row smuggle in more than was ruled? Flag any overreach.

**Q9 — What fails at stage 3?** Assume a separate execution session with an independent reviewer
implements this. Name the things most likely to break, in order, and what evidence would catch each
before it breaks.

**Q10 — Anything else.** Including: anything in D-1…D-8 that contradicts one of the seven rulings;
anything in the packet that claims verification without a detector behind it (§N.8); and any place
the author has asserted a fact that you can show is false at source.

## Output format

- Findings as `K2-nn`, each with: severity (**BLOCKER / MAJOR / MINOR / NOTE**), the claim, the
  evidence, and the minimal fix.
- A single verdict: **ACCEPT** · **ACCEPT_WITH_CONDITIONS** (list them) · **REWORK** (list the blockers).
- A closing section separating **what you verified at source** (cite file/line or table/verse) from
  **what you are asserting from knowledge**. Tag doctrine claims [D] verified / [J] judgement /
  [U] unverified, as you did last time.
- Write no files. Advisory only; nothing here authorizes implementation.
