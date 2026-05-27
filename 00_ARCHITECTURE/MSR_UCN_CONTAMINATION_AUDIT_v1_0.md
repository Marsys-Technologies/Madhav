---
artifact: MSR_UCN_CONTAMINATION_AUDIT_v1_0.md
status: DRAFT
version: 1.0
authored_by: Claude (Cowork session) — forensic read of the live corpus, 2026-05-27
authored_on: 2026-05-27
audience: native (Abhisek Mohanty)
disposition: >
  Findings report. Reconstructs the methodology by which MSR signals and UCN were
  built, and assesses the extent to which interpretation (and authoring judgment)
  contaminated what should be a deterministic factual base. Companion/feeder to the
  provenance-tiering decision. PENDING NATIVE REVIEW — does not modify any artifact.
parent_brief: 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md
sibling_artifacts:
  - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
  - 00_ARCHITECTURE/PANEL_MODE_TOOL_SPEC_v1_0.md
evidence_base:
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md (v5.1, 573 signals — read in full structure + sampled bodies)
  - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md (v4.1)
  - scripts/clean_msr.py
  - 00_ARCHITECTURE/MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md
  - 00_ARCHITECTURE/MSR_CITATION_SCAFFOLDS_v1_0.md
method_note: >
  Quantitative distributions computed by grep/awk over the live MSR file. Line numbers
  cite MSR_v5_0.md as read on 2026-05-27. Verify against current file before acting —
  the corpus mutates.
---

# MSR / UCN Interpretation-Contamination Audit

## §0 — Bottom line

The factual base is contaminated, but **not primarily by Anthropic-flavoured bias** (the
native's stated non-worry). It is contaminated by a deeper, structural issue: **MSR
presents model judgment in the costume of data.** Hand-authored scores, a silently
pre-filtered signal pool, in-line deliberation, interpretive claims inside "fact" fields,
and at least one authoring error that reached production all live inside a register whose
YAML-with-derivation-ledger form makes them *look* computed. UCN is a separate, simpler
case: it is interpretation by design and only mislabelled, not subtly contaminated.

The native's two instincts are both correct and are vindicated by the evidence:
(1) **never drop data** — the drop already happened, invisibly, and is the single most
consequential contamination; (2) **a signal's coefficient should be retained, not gated** —
and, this audit adds, the coefficient should be *decomposed*, because it currently fuses a
computable quantity with a model opinion.

---

## §1 — How MSR was actually built (reconstructed methodology)

**Hand-authored across sessions, by a model, with no scoring formula.** The completeness
certificate (SIG.MSR.420) records "SESSIONS USED: Session 12 (primary build)"; the
frontmatter changelog shows successive expansions — v2.0 (signals 421–443), v3.1 VARGA-ETL
(D12 cross-varga, 500–514), v4.0 (Nadi/BNN, 515–543), v5.0 (Yogini + Tajika, 544–573).
Each signal is a hand-written YAML block.

**The scores are model judgment, not computation.** The only MSR script in the repo,
`scripts/clean_msr.py`, is a **text-scrubber** — it strips correction-commentary from v2.0
(regex removals of "CORRECTED", "INVALIDATED", "reconciliation:"). There is **no generator
and no scorer**. `strength_score` and `confidence` were assigned by the authoring model's
judgment. This is the central fact of the whole audit.

**The two scores mean different things — documented only sporadically.** Sampling shows
`confidence` tracks *derivation/verification certainty* — e.g. SIG (≈line 13016): "this
signal's confidence is moderate because (a) the lagna nakshatra is used here (not the
Janma/Moon nakshatra), and (b) the exact classical list requires text verification." Whereas
`strength_score` tracks *effect/configuration magnitude*. The distinction is real but
**implicit and inconsistently applied** — there is no schema statement defining either.

**Grounding was added retroactively, and is double-booked.** `derivation_ledger`
grounding was backfilled by the DAR workstream (`grounding_status: GROUNDED`, 567/573,
dated 2026-05-25). But the *top-level* `forensic_ref` citation field is far less covered:
`MSR_CITATION_SCAFFOLDS_v1_0.md` records "Signals with forensic_ref before UDA-4-S1: 0",
adds 50, and then **disagrees with itself** on the remainder ("419/573 … lack forensic_ref"
in the purpose block vs. "Remaining signals without forensic_ref: 523" in the table). The
grounding metadata itself has drift.

## §2 — How UCN was built

UCN is a **narrative synthesis authored on top of** MSR/CDLM/RM/CGM/FORENSIC
(`parent_lineage` in its frontmatter), merged across v1.0–v4.1. Its own opening declares
its nature: *"A chart is not a list of planets in houses. It is an argument."* It is
organised around named frames ("The Mercury Seven-System Convergence", "Foundation
Signature 1"), states verdicts ("This is the chart's primary finding"; "This is not a
wealth-maximizing chart"), and prescribes ("The native who resists this Mercurian calling
… is working against the chart's grain"). It cites MSR signal IDs inline (e.g. "MSR.413,
confidence 0.98"). **UCN is ~95% interpretation by construction — and that is fine for what
it is.** Its only defect is the `canonical` label and the RAG leak, both already addressed
by the provenance-tiering brief.

---

## §3 — Contamination taxonomy (ordered by subtlety, not severity)

### C1 — Model scores presented as data `[the core issue]`
`strength_score` / `confidence` are hand-assigned opinions wearing a numeric, data-shaped
wrapper. The problem is not that the numbers are wrong — it is that their **provenance
(model judgment) is invisible** behind YAML. Any consumer, human or LLM, reads `0.92` as if
it were measured. *Severity: high. Subtlety: high.*

### C2 — The silent drop / missing candidate pool `[the native's specific worry — CONFIRMED]`
The distribution is the fingerprint. Of 572 scored signals: mean 0.79, median 0.82, and
**87% score ≥ 0.70** (273 in 0.70–0.85, 226 ≥ 0.85; only 18 below 0.50). A *complete*
observational substrate would have a long flat tail down into weak, wide-orb,
single-source configurations. Instead almost everything is strong — because **weak
configurations were never written down.** There is no candidate pool, no "considered and
scored 0.3" record, no audit trail of the drop. **You cannot audit a drop that left no
trace, and this register left none.** This is the most consequential contamination for the
"never drop data" principle precisely because it is invisible by construction. *Severity:
high. Subtlety: maximal.*

### C3 — Deliberation committed into the factual base
Falsifier and supporting_rules fields contain model reasoning-in-progress, not settled
fact. Examples (MSR_v5_0.md): line 11537 "Wait: Venus = 19°15'… But wait, we have 7
planets…"; line 11897 a multi-hundred-word argument over Jaimini rashi-drishti adjacency —
"This requires care. Standard rule:… Re-reading:… different authorities state different
adjacency exceptions… Corrected: Ketu (Scorpio 8H) aspects 1H+4H+10H." A clean factual base
**states the settled value**; it does not show the work mid-stream, and it certainly does
not leave a "Corrected:" inside the field that is supposed to be the fact. *Severity:
medium. Subtlety: high — it hides inside legitimate-looking fields.*

### C4 — Interpretive claims inside "fact" fields
`signal_name`, `supporting_rules`, and `domains_affected` routinely carry meaning, not
structure: "NBRY = promotes native above own station over time" (SIG.MSR.002);
"warrior-king quality of Kalpadruma is consistent with MSR.015… multiple royal-authority
signals converge" (SIG.MSR.421). `domains_affected: [career, wealth, relationships, mind]`
is itself a judgment mapping. These are T2 interpretation living in fields that look T1.
*Severity: medium. Subtlety: medium.*

### C5 — Authoring-error drift `[the proof case]`
Because MSR was hand-authored rather than computed, it can carry values that are simply
**wrong** and drift from L1 — and the fact-shaped format hides the error until it surfaces
in a bad answer. `SIG.MSR.377` (per `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md`) was
internally inconsistent across **five fields**, conflated the Muntha with the Upapada
Lagna, committed an **off-by-one against its own stated formula** ((42 mod 12)=6 → "Virgo
6H", dropping the +1 that yields Libra 7H), never stated the correct value anywhere, and
**returned a wrong Muntha to the native through the chat UI.** The canonical L1 value
(FORENSIC §22: Libra, 7th, Venus) is deterministic — `(age mod 12)+1 house` — and a
computed structural-fact layer would *never* have produced this error. This single signal
is the strongest possible argument for the native's thesis: configurations that should be
deterministic were left to authoring, and authoring went wrong. *Severity: high
(production impact). Subtlety: high until it broke.*

### C6 — Partial, inconsistent grounding (see §1)
Two grounding systems (`derivation_ledger.grounding_status` at 567/573 vs top-level
`forensic_ref` at 50/573) with self-disagreeing remainder counts. The factual anchoring is
better than it was (DAR closed the big gap) but is not uniform and its own metadata drifts.
*Severity: low–medium. Subtlety: medium.*

---

## §4 — The diagnosis, in one sentence
MSR is a **feature-engineering layer with model-authored labels that masquerades as a
measurement layer** — and the masquerade is the contamination, because it hides the three
things a clean base must expose: which configurations were *not* recorded (C2), which
numbers are *opinions* (C1), and which claims are *meaning* rather than structure (C3–C4).

---

## §5 — Recommendation: decompose the coefficient, and never drop

### §5.1 — Does the multi-LLM coefficient idea remove bias?
**No — it makes bias visible and comparable, which is a real gain, but it leaves two
problems unsolved.** Voting Gemini + DeepSeek + Claude coefficients onto a signal (a) still
votes on a *fused* number that mixes a computable quantity with an opinion, and (b) still
inherits whatever the *signal selection* already dropped (C2) — three models voting on a
curated list is still a curated list. Transparency improves; the substrate does not.

### §5.2 — The structurally smarter move: split the coefficient into three
A signal's "weight" is currently one fused number. Decompose it:

1. **Deterministic strength (T1 — computed, not voted).** Derivable from facts: aspect orb
   tightness, shadbala of the involved planet(s), dignity state, count of independent
   classical sources naming the configuration, divisional-corroboration count. This
   *replaces* the hand-assigned `strength_score` with a computed value, and is identical
   across all models because it is arithmetic.
2. **Verification certainty (T1-ish — rule-checkable).** Is the underlying L1 value
   confirmed? Does the classical-rule application have textual support? This formalises
   what `confidence` was gesturing at (the line-13016 sense) and is auditable rather than
   felt.
3. **Interpretive salience / valence (T2/T3 — the ONLY place the panel votes).** "How much
   does this matter for *this* life," benefic/malefic-*for-this-native*. Here, and only
   here, attach per-model coefficients (Claude/Gemini/DeepSeek), let divergence be a logged
   signal, and let the judge reconcile. This is where the multi-LLM idea genuinely pays.

### §5.3 — Never drop (make the register complete)
Every observable configuration gets a row — including wide-orb, single-source, low-strength
ones. The deterministic-strength column (§5.2.1) becomes the **coefficient, not the gate.**
A consumer that wants only strong signals filters on the column; a consumer doing research
sees the full distribution, including the weak tail that the current register erased. This
is the data-engineering realisation of the native's principle, and it also re-exposes the
candidate pool that C2 hid.

### §5.4 — Relationship to the structural fact layer
§5.2.1 (deterministic strength) is **not new work** — it is exactly the output of
`STRUCTURAL_FACT_LAYER_SPEC_v1_0.md` (shadbala, orb, dignity, source-count). Build that
layer and the deterministic component of every MSR coefficient becomes computable. MSR then
shrinks to what only a model can supply: the interpretive-salience residual (§5.2.3),
clearly labelled as such. The two workstreams converge.

---

## §6 — What this audit does NOT claim
- It does not claim MSR's *content* is mostly wrong. The sampled signals are substantive and
  often excellent. The contamination is about **provenance and completeness**, not accuracy.
- It does not claim UCN should be deleted. UCN is a fine reading; it should be relabelled
  and de-RAG'd, per the parent brief.
- It does not quantify C3/C4 exhaustively — those are characterised from sampling, not a
  full census. A full census (every falsifier field flagged for deliberation-residue, every
  supporting_rule flagged for interpretive content) is a candidate follow-on if the native
  wants the exact extent rather than the shape.

---

## §7 — Provenance of this audit
Model-authored (Claude, Cowork), from a direct read of the live corpus. DRAFT, for native
review. It modifies nothing. Per CLAUDE.md §L, any remediation (recompute scores, retain
dropped signals, split coefficients, relabel UCN) requires native approval + version bumps
on the affected artifacts.
