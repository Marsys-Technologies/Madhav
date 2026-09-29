---
artifact: REVIEW_PACKET_DESIGN_SPECS
canonical_id: REVIEW_PACKET_DESIGN_SPECS
version: "1.0"
status: CURRENT
date: 2026-09-29
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
reviewers: "Kimi K3 (max effort) · Codex gpt-6-astra (max effort) — independent, in parallel, neither sees the other's review"
precedent: "sealed/REVIEW_PACKET_GOCHARA_ASTRO_v1_0.md (the v2.0 doctrine review packet) — same ground rules, same evidence discipline"
---

# Review packet — Gochara design specs v1.0 (B3.5)

You are one of two independent reviewers of the **design specs** for the Gochara elevation. The
doctrine itself (`FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md`) is SEALED after your predecessors'
reviews; you are **not** asked to re-review the doctrine. You are asked whether these specs
**faithfully and completely operationalise** the sealed doctrine — whether a competent engineer
can build against them without asking a question, and whether an ācārya finds no doctrine smuggled
in or leaked out.

## 1. Read, in this order

1. `sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md` — the sealed doctrine (sha256
   `5bd6c51e…182392`). This is the ground truth the specs must express. Its §7 ruling requests
   are all **ruled** (see item 4) — treat them as settled, not open.
2. `design/GOCHARA_DESIGN_SPECS_v1_0.md` — **the reviewed document** (sha256
   `1f4110b7…75fd6a`). Eleven sections; each has schema, invariants, test oracles.
3. `design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md` (sha256 `bb5bc981…f4fd804f`) — how the ratified
   engineering plan v2.1 and the ruling sheets reconcile with v3.0; which rulings stand, which
   packets survive, the tier→item map.
4. `design/L3_FAMILY_COORDINATION_v1_0.md` (sha256 `2476f2cc…04f9d9d9`) — the Kṣetra/Saṅgam
   consumer contract.
5. `NATIVE_DECISION_PACKET_v1_0.md` (sha256 `89263ffd…4f0b0c`) — the ten rulings of 2026-09-29
   (D-RQ1…D-RQ8, D-P4, D-PADMIT) verbatim, plus the six earlier decisions.
6. `design/CORPUS_READS_v1_0.md` — the corpus reads that were `[U]` at seal time (if present;
   if absent, treat the `[U]` items it would settle per v3.0 §8 as open and say what the specs
   must therefore not assert).
7. `sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md` (sha256 `05ce2f0d…04ff20`) — every production
   figure with its SQL. You may **not** query production; figures are taken on this appendix's
   authority.

All paths are relative to `/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/`.

## 2. Ground rules (same as the doctrine review)

- **Read-only.** Do not edit any file. Your output is your review text, nothing else.
- **Verify what you can.** File:line citations against the repo (branch `campaign/pravaha`);
  arithmetic in the oracles (recompute the longitudes → signs → houses yourself; the miscounted
  house is campaign law: no rule number without the count behind it).
- **Label every claim**: `[D]` served-corpus doctrine · `[S]` source you read · `[L]` evidence
  appendix figure · `[P]` practice · `[J]` judgment · `UNVERIFIABLE_HERE` where the packet does
  not let you settle it — never guess.
- **Do not reopen ruled items** (the lane M/N rulings and the ten D-rulings). If a ruling looks
  wrong to you, say so explicitly as a note for the native — that is welcome and is not a veto.
- **No DB access, no production access.** Absence claims about the corpus are the author's to
  make with count(*); you may challenge the predicate, not run your own.

## 3. What we ask of you

**A. Conformance sweep.** For each of the sealed v3.0's load-bearing elements, state whether the
specs carry it, lose it, or distort it: the union-of-source-qualified-paths admissibility (§2.2);
the relationship record (§2.3); the admitted path catalogue P1–P6 with its source statuses
(§2.4); three-field valence and class-relative polarity (§2.5, #11/#12); the Tier-0 defect
repairs (#1–#27, N1–N9 — each must be guarded by at least one oracle or spec invariant); the
implementation contract §6 (substrate, pruning, lazy refinement, interval sweep, day-on-demand,
re-solve vs re-score); the §7 rulings as ruled (D-RQ1…8); the §8 corpus register's constraints
(nothing `[U]` enters a score).

**B. Defect hunt.** Find what is wrong, missing, or over-specified in the specs themselves:
invariants that cannot be tested; oracles that cannot fail (§N.8 violations); schemas with
ambiguity an implementer would have to guess at; arithmetic errors in the worked examples;
doctrine asserted beyond the sealed text or its rulings; places where a `[P]` element enters
without its ruling ref; places where "uncomputed" could still read as "empty".

**C. The freeze question.** B3.6 will freeze these specs under D-SPECS; Stream A then builds
migrations and a writer against them. Answer directly: **FROZEN / FREEZE_WITH_AMENDMENTS /
REWORK**, with ranked amendments — the amendments that must land before freeze, in order, each
with its evidence.

**D. Notes for the native** (optional): any ruled item that looks wrong on the evidence here,
stated as a note, not a veto.

## 4. Format of your review

1. Verdict line (C above).
2. Conformance table: sealed element → carried / lost / distorted (with spec §).
3. Findings, each: severity (blocking / should-fix / note) · claim · evidence (file:line,
   arithmetic, or label) · requested change.
4. Ranked amendment list.
5. Disclosure: what you could not verify and what would settle it.

Your review will be stored **unedited** under `design/reviews/` and reconciled finding-by-finding
at B3.6 (accepted / amended / refuted with evidence / deferred).
