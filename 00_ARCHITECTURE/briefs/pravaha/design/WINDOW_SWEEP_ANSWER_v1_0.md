---
artifact: WINDOW_SWEEP_ANSWER
version: "1.0"
status: ANSWER TO STEWARD QUESTION (not a spec version; no code; recommendations marked MINE are not rulings)
date: 2026-10-02
author: stream-B (Exec B)
question: steward M20261001T235032-17ab — Stream A's window-sweep design (brief "Design v1.5", pravaha/a53-am5-inventory @11e3700fd)
sources: >
  S = GOCHARA_DESIGN_SPECS_v1_4 · O = GOCHARA_TEST_ORACLES_v1_4 · P = EVALUATION_PROTOCOL_v2_3 ·
  AM = GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.9 · 1156 = migration 1156 (applied) ·
  R = services/gochara_rules (registry.py, score.py, valence.py) on main · K = services/gochara_kernel/convention.py ·
  BASE = BASELINE_3_0_v2_3.md. Corpus read this pass (served): brihat_jataka:PG65:C1, uttara_kalamrita:PG40:C2.
---

# Window sweep — answers (≤ 1.5 pages)

**(1) What is stored.** §2.1 gives two quantities: the within-path **product** per record (NK-4, §2.1 within-path score algebra, factors ⊆ [0,1]) and the
**evidence accumulation** `path.c = Σ over roots of the per-root max` (§2.1 evidence accumulation). They are different, and the *applied schema decides*:
1156:256–295 has `score REAL` with CHECK **`score IS NULL OR 0 ≤ score ≤ 1`** (NULL = unqualified), `evidence_for/_against` finite ≥ 0
(unbounded), `severity` finite, nullable. §1.1 (field table) adds that evidence/severity are "rank-only, never a gate; scale set at L5".
**MINE:** per window (one path-version × class — the table has a single `(path_id, rule_version)` FK, so cross-path `max` is a
*serve/measure-time* reduction over windows, not a stored value), at the peak instant t\\*:
`score` = max over the window's admitted records of the within-path product in the for-channel (∈[0,1]; NULL if the path is
`unqualified`); `evidence_for` / `evidence_against` = S's per-channel Σ-over-roots at t\\* (never netted — §3.2 inv 1, O-TV-2, O-RP-1);
`peak_instant`, `outcome_valence_for_native`, `severity`, `record_ids` (membership rows), `coverage_*`, `null_states_used[]`.
P is **silent** on which stored field is its `si` (P:131–150: only "non-negative, descending"). **MINE:** adapter `si := evidence_for`,
not `score` — `score` saturates at 1.0 for any exact-contact record, which is exactly the plateau P §8.3 (≥ 50 % identical si ⇒ T-rank
void) is built to catch. 3.0-vs-controls: constrains this (BASE: era fingerprint 59.8 % ⇒ T-rank VOID).

**(2) Window interval = the connected union of admitted supports.** §2.3 inv 3 (no soft factor zeroes an admitted window), inv 2/4
(pruning only by a false necessary predicate; no clipped curves). The legacy `min_lambda` threshold appears **nowhere** in S/O/AM
(silent) and would be a producer-side filter — O-CF-N5's rule is that such filters live only at serve time. P:§4.2 merges
abutting windows anyway, so the union is what the scorer would form. **Constraint, not a choice:** BASE shows 3.0 fails T-FP on 8/9
adverse classes at 99.87 % and random controls cover 67.9 % vs the model's 68.1 % — coverage alone is not evidence. Budget is 270 d
(n_c = 1) / 540 d (n_c = 2) per adverse class (P:§6.4); a single long residence span can exceed it. That failure must be fixed by
admission (a new rule_version / ruling), **not** by silently narrowing windows. A threshold, if wanted, needs a native ruling.
Peak on a plateau: **MINE** earliest instant of the max (P:§4.2 tie rule is earliest).

**(3) Kernel for a residence record on `span:<sign>`.** S is **silent** (§7.2 inv 3 defines `1 − |Δλ|/orb` only for a point).
Registry facts: **P2 — pure span residence — declares no `activity_kernel`**; P3/P4/P5 declare it but include span residence/aspect-on-span
contacts; the factor row carries **no orb parameter** (4.x used 5.0° "unratified"). §2.1 says a missing operand takes its `null_state`
(`unqualified`) and is "never silently 1" — so read literally every P3/P4/P5 span record is `unqualified`. **MINE:** a span has no
centre or orb in any cited source; angular-to-centre/boundary would fabricate a gradient (§N.7 item 6) and make every house edge depend on
an arbitrary choice. Use a **step: 1.0 inside the span, 0 outside (membership)**, angular kernel only for point/star objects — **but this
must be declared, not hard-coded**: new factor version `activity_kernel@1.1` with applicability by object kind (span ⇒ step) and the orb
as a row parameter. Recorded as **AM-13 candidate** (needs the steward/native). Until then A must not hard-code 1.

**(4) `graduated_drishti`.** Input = inclusive whole-sign **house offset** of the target from the aspecting graha's sign:
¼ at 3/10, ½ at 5/9, ¾ at 4/8, full at 7; specials full (Mars 4/8, Jupiter 5/9, Saturn 3/10); nodes cast none (N-14). Cited, served corpus
(read this pass): **Brihat Jātaka ch. II śl. 13, `brihat_jataka:PG65:C1`** — "all the planets cast a quarter glance at the 3rd and 10th,
half at the 5th and 9th, three-quarters at the 4th and 8th, a full eye at the 7th; Saturn exceedingly powerful at 3/10, Jupiter at 5/9, Mars
at 4/8"; **Uttara Kālāmṛta `uttara_kalamrita:PG40:C2`** (Mars full on 4th/8th, others three-fourths; others half on the 5th/9th — chunk
truncated). S/O cite **BPHS1:16496-16502** (O-CF-DRISHTI) and K cites ch.26 śl.6-8; I did **not** re-read those lines in this pass.
Ownership: K owns the directed *angles* (`SPECIAL_DRISHTI_DEG`); the factor row is in R but **no evaluator exists** (grep: only the registry
row). **I will add `services/gochara_rules/drishti.py: graduated_drishti(agent, offset)`** (pure, table + citations); A reads that, never a
copy (§N.7 item 3). It applies to **aspect** records only — residence/conjunction have no offset (same applicability gap as (3)).

**(5) Valence and severity.** Yes: `valence.compute_valence(class, evidence_for, evidence_against, unresolved_operand)` is the evaluator,
called at the peak instant (§3.2 inv 4), class polarity from the registry; `mixed` is never emitted by default. **Severity is not
defined anywhere** (§1.1 "interpretive, rank-only"; no rule computes it) — and `valence.py` currently defaults it to **0.0**, which is an
invented judgment. **MINE (and my fix, small PR):** severity = **NULL** (named null) when no cited severity rule exists and always for an
`unqualified` window; never 0. 1156 permits NULL.

**Four items A lists still open.** (a) *P1 daśā-lord house anchor:* §2.2 P1 says "frame `dasha_lord` / natal sign positions"; the natal relation is
to the class's signature-house set H, counted **inclusive from the lagna** (P3 table is "lagna frame"; §0 inclusive counting) — see
PREREQUISITE_EVALUATION_ANSWER; no separate anchor is specified (**silent**; MINE = lagna). Oracle: O-PP-1/2 (period), O-RP-3. (b) *`'5.0'` manifest
vector:* S is **silent**; 1206 requires only that the snapshot's vector **equal** the manifest's (AM-5 (b)). 4.x carried method/policy keys
(`activity_shape`, `orb_max_deg`, `nodal_drishti`, …). **MINE:** carry what the snapshot does *not* cover — the registry fingerprints
(`ka_gochara_rule_path/factor/predicate` + seal digest, `bg_transit_rules`, `bg_transit_av_gates`) and the declared kernel/orb version. (c) *Verifier
derives P2/P5:* from the sealed registry row + class applicability alone, never from the writer's output: P2 = agents × `residence` ×
`(graha, house from janma-rāśi)` per class; P5 = forms P5a–e per the missing-input matrix (S §2.2 P5 missing-input text; see PREREQUISITE_EVALUATION_ANSWER), per-form states, gated by the
declaration row (O-BP-2/3). The O-RP-8 qualification-driven rule bounds both. (d) *Writer capability flags:* **silent** in S/AM.
Measurement constraint on all four: none of them is constrained by T-cover/T-FP/T-rank directly; (a)(b) affect admission only via inputs, so
changing them changes `input_digest` (AM-5) and requires a re-search.
