---
artifact: TOTAL_AUDIT_PROTOCOL_v1_0
version: 1.0
status: CURRENT (governs all future audit campaigns; supplements ONGOING_HYGIENE_POLICIES red-team cadence)
date: 2026-07-10
author: Cowork (Fable-5)
trigger: >
  Native's question after the 2026-07-10 full-estate audit: the five-agent audit produced 60+ register
  rows yet MISSED the three defects that mattered most — discovery-engine wrongness (childbirth-denied
  vs actual twins), the CGM graha→bhava edge hole, and the KP composition gap — all three found within
  hours by three pointed native questions. Why do extensive audits keep missing the biggest gaps?
---

# TOTAL AUDIT PROTOCOL — why audits miss, and the design that closes the classes

## §1 — The post-mortem, honestly

### §1.1 What the five-lane audit was, epistemically

The 2026-07-10 audit was **surface-enumerative**: enumerate every MCP tool, call each with
reasonable parameters, grade the response — error / empty / oversized / params-ignored /
internally-inconsistent / degenerate. Its oracle was **the system itself**: a response was "bad"
only if it was malformed, self-contradictory, or violated its own contract. That oracle can see
malfunction. It cannot see **mis-design** (a correct-looking answer built on a wrong method) or
**absence** (a composition that should exist and doesn't). All three misses were in those two
classes.

### §1.2 The three misses, each with its exact mechanism

**Miss 1 — Discovery-engine wrongness (D-15/D-16, T-12).** The audit graded anchor payloads for
form (it DID catch duplication, pre-birth windows, size). It never asked "are these claims TRUE?"
because truth requires a ground-truth oracle — the LEL — and no lane held it. The childbirth-DENIED
verdict sat in a well-formed response that passed every form check. *Mechanism: no truth oracle.*

**Miss 2 — CGM graha→bhava edge hole (G-1).** The graph tools returned rich 75KB payloads; the
lane graded them oversized-but-working. Nobody attempted a SPECIFIC traversal with a known-true
answer ("Saturn must reach his own bhava-11"). An edge-type census (5 minutes of work once you
think of it) was never run, because the lane's mandate was "probe the tools," not "verify the
graph implements the design." *Mechanism: no expected-structure model; audit decomposed along the
system's own tool families, so a defect at the L1→L2 projection seam fell between lanes — lane G
saw L1 facts present ✓, lane B saw graph tools responding ✓, and the missing projection between
them belonged to neither.*

**Miss 3 — KP composition gap (KP-1..6).** Worst of the three, because **the answer was already
in the repo**: FORENSIC v6.0 §4 in 99_ARCHIVE contains the exact Mars/Mercury/Rahu 11th-cusp
analysis, and DEEP_ANALYSIS ties Saturn to the earning channel. No lane ever diffed current
output against the legacy corpus. The fake `kp_cuspal_significators` category even returned
well-formed rows — form-perfect, content-fabricated. *Mechanism: no baseline/regression oracle;
the golden answers existed on disk and the audit never treated the archive as an oracle.*

### §1.3 The proof by contrast — what DID catch defects, and why

Every part of this session that had an **external reference** caught its defect class instantly:

| Probe | Oracle used | What it caught |
|---|---|---|
| Concept-completeness lane | Classical canon checklist | ABSENT concepts (K-rows) — the ONE enumerative lane with an ought-model, and the one that found absences |
| Blinded retrodiction test | LEL (lived events) | Wrongness: 0% negative recall, childbirth-denied, single-cycle basis |
| Native question 1 (Parashari chain) | Native-known-true signal | G-1..G-8 — the graph's missing edge classes |
| Native question 2 (KP chain) | Legacy archive + native memory | KP-1..KP-6 — fabricated category, wrong house system, missing ladder |

**The law this reveals: an audit can only find defects its oracle can express.** Tool-sweeps
carry the weakest oracle (the system's own contracts) and therefore find only the weakest defect
class (malfunction). The native's questions carried the strongest oracle — specific, chart-true,
consequence-laden expectations — and found in one shot what 250K tokens of enumeration missed.
The native was, functionally, the only acharya-grade oracle in the loop. The protocol below
exists to encode that oracle so it runs without him.

## §2 — Defect-class × oracle matrix (the coverage model)

| Defect class | Example from this project | Oracle that can see it | Was it applied 2026-07-10? |
|---|---|---|---|
| Malfunction (dead/oversized/param no-op/inconsistent envelope) | R-9, R-1, R-18 | Form oracle (tool sweep + contract checks) | ✅ — caught ~60 rows |
| Missing concept | K-1..K-8 | Canon oracle (external checklist) | ✅ — caught them |
| Wrong served value | D-1 (Shravana), G-7 (house 11 vs 7) | Independent recompute + cross-fact consistency | ⚠️ partial (anchors only) |
| Wrong claim about the native's life | D-15, D-16 | Truth oracle (LEL retrodiction) | ❌ until the dedicated test |
| Missing composition (chains, ladders, joins) | G-1, KP-3, S-1 | Golden-signal oracle + seam conservation laws | ❌ (S-1 was caught only because v1 register already knew it) |
| Wrong method behind well-formed output | KP-1 (whole-sign), KP-2 (fake sub-lords), S-8 | Method audit vs shastra + legacy diff | ❌ except where code audit happened to read the line |
| Regression vs legacy capability | KP-5 (the lost KP lens) | Baseline oracle (archive golden answers) | ❌ — archive never opened |
| Distributional collapse | G-2, D-17, D-18, flat salience | Statistical gates on every scored column | ⚠️ partial (rows, not edges/valence) |
| Silent zero (coded, emits nothing) | D-4 shunya rashis, T-4 kala_activation | Count-floor conservation per category | ⚠️ found by accident |

The 2026-07-10 audit applied 2.5 of 9 oracle classes. That is the whole answer to "why were these
gaps not surfaced."

## §3 — THE TOTAL AUDIT PROTOCOL (TAP)

Nine batteries. Each closes one row of the matrix. Batteries 1, 5, 7, 9 are automatable in CI;
2, 3, 4, 6, 8 run per campaign/regen. No future audit claims completeness without declaring,
per battery, RUN or SKIPPED-WITH-REASON (§4).

**TAP-1 · Form sweep** *(exists — this session's five-lane probe, mechanized)*. Every tool ×
params matrix: error/empty/size/param-echo/envelope-consistency. Automate as the canary battery,
per release. Catches: malfunction.

**TAP-2 · Canon conformance** *(exists — concept lane)*. The classical-concept checklist,
maintained as a versioned data file (not a prompt), graded L0/L1/served per chart class. Re-run
per regeneration. Catches: missing concepts.

**TAP-3 · Truth battery** *(new, keystone)*. Four parts: (a) FORENSIC 7/7 anchors (exists);
(b) **independent recompute sampling** — for every served value class, recompute N samples
directly via PyJHora/Swiss Ephemeris outside the product pipeline and diff (catches D-1/G-7-class
denormalization rot); (c) **blinded LEL retrodiction** per DISCOVERY_ENGINE_ACCURACY_TEST protocol
(Section 10 of the register — now the standing metric); (d) **absurdity gates** — pre-birth claims,
post-death-horizon claims, contradiction pairs (Kemadruma+Gaja-Kesari; denied-class vs LEL event).
Catches: wrongness.

**TAP-4 · Golden-signal regression corpus** *(new — the one that would have caught KP in
minutes)*. Mine EVERY legacy analysis (FORENSIC v6.0/v8.0, DEEP_ANALYSIS v1.2.1 SIG/CVG/CTR,
archived MSR/UCN/CGM markdown, LEL retrodictive_match blocks) + native attestations into
`GOLDEN_SIGNALS_<chart>.yaml`: rows of (question, must-surface atoms, source citation). Examples
already earned: KP.CUSP.11 Mars/Mercury/Rahu cash-flow; Mercury→Saturn(11L)→11H + Mars→Rahu(2H);
Mercury sole-vargottama in any Mercury judgment; Sade Sati cycle-2 in any 2022-25 timing question;
Jupiter-9L-weak grandfather signature. The battery asks each question through the flagship
instruments and FAILS unless the atoms appear in the evidence chain. **The system must be able to
rediscover its own archive.** Catches: missing composition, lost legacy capability, lateral
blindness.

**TAP-5 · Seam conservation laws** *(new, cheap, automatable)*. Machine-checkable invariants at
every layer boundary: every chart_facts category → ≥1 serving tool (S-13, live-derived); every
relational fact class → ≥1 CGM edge type; every graph node type → edge-degree > 0 (would have
caught G-1 in one SQL query); every signal category → explicit _DOMAIN_MAP entry (KP-4); every
stored score column → ≥1 reader (S-15); every asset → nonzero rows for a built chart unless
floored-with-reason (T-4, D-4). Catches: seam defects, silent zeros, unserved computation.

**TAP-6 · Method audit** *(extends the code-audit lane)*. For every computed category, the
implementing function is checked against its cited shastra/spec — specifically hunting the
Approximation/simplified/TODO/hardcoded-default pattern (KP-2's `# Approximation`, S-8's 15°-orb,
Y-1's fall-through were ALL greppable). Standing grep list + human read of hits. Catches: wrong
method behind well-formed output.

**TAP-7 · Distribution gates, universal** *(extends existing guard)*. Every scored, attributed,
or categorical column — rows AND edges AND claims: collapse-to-constant, all-one-valence,
single-basis-cycle, identical-causal-chain, flat-pagerank. Run at build seal AND at serve sampling.
Catches: degeneracy.

**TAP-8 · Adversarial question battery** *(extends the 38-item acceptance battery)*. Real
acharya-grade questions, including deliberately lateral ones ("how will money COME to me" is
KP-lateral; "what breaks this yoga" is bhanga-lateral), graded by rubric against model answers.
The existing battery tests generic capability; add the chart-specific golds from TAP-4. Catches:
synthesis-quality gaps that atomically-correct systems still fail.

**TAP-9 · Audit-of-the-audit (coverage self-declaration)** *(new, meta)*. Every audit report MUST
end with the §2 matrix, marking per oracle class: APPLIED / NOT-APPLIED + reason. An absence of an
oracle is thereby explicit and native-visible, never silent. This one rule would have converted
"full extensive audit ✅" into "full FORM audit; truth/baseline/composition oracles NOT applied" —
and the native would have known exactly what he was and wasn't getting.

## §4 — Standing rules (bind future sessions)

1. **No audit may be titled "full" or "complete" unless all nine batteries ran.** Otherwise it is
   named by its oracle ("form audit", "truth audit") and carries the §3 coverage declaration.
2. **Audit lanes cut ACROSS the architecture, not along it.** Decompose by question/domain/oracle,
   never by the system's own tool families — seam defects live exactly where the system's
   decomposition puts its boundaries.
3. **The archive is an oracle.** 99_ARCHIVE analyses are golden answers until explicitly
   superseded; every capability visible in them is a regression test.
4. **Every fixed defect becomes a permanent probe** (register row → canary/battery item on close).
5. **Native question sessions are oracle-harvesting sessions**: every pointed question the native
   asks — hit or miss — is added to GOLDEN_SIGNALS as a battery row within the same session.

## §5 — Execution plan

- **Immediate (with R6):** TAP-5 conservation SQL/grep suite (days; would have caught G-1, T-4,
  D-4, S-15, KP-4 mechanically); TAP-9 rule adopted now; GOLDEN_SIGNALS_482012f1.yaml seeded from
  this session's five earned golds + a mining pass over FORENSIC v6.0/DEEP_ANALYSIS (one session).
- **With R6 Wave C exit:** TAP-3 full truth battery (the blinded retrodiction re-run is already
  the wave gate).
- **Per release thereafter:** TAP-1 + TAP-5 + TAP-7 in CI; TAP-4 + TAP-8 per campaign close;
  TAP-2 + TAP-6 per regeneration.

*End TOTAL_AUDIT_PROTOCOL v1.0 (2026-07-10). The one-sentence version: our audits checked whether
the machine runs; the native's questions checked whether it tells the truth about a life — and
"catches everything" means running both, plus the seven oracles in between, every time.*
