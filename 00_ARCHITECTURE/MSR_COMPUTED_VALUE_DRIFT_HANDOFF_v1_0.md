---
canonical_id: MSR_COMPUTED_VALUE_DRIFT_HANDOFF
version: 1.0
status: HANDOFF — context transfer for a new conversation
authored_on: 2026-05-20
author: Claude (analysis stream)
purpose: Give a fresh conversation the full context to scope + run the MSR computed-value-drift audit + architectural fix
two_stream_branch: analysis stream (recreate analysis/backend-data-pipeline-perf-audit-N from main when starting)
---

# MSR Computed-Value Drift — Conversation Handoff

## §0 What this document is

A self-contained context transfer. A fresh Cowork/Claude conversation should be able to read CLAUDE.md (mandatory per §C) + this file and pick up the investigation without needing the originating thread. The work it sets up is an analysis-stream campaign: a data-integrity audit of the MSR signal store + an architectural fix to prevent the bug class from recurring.

## §1 The triggering finding — SIG.MSR.377 Muntha corruption

A native query about the current-year Muntha (Varshaphala progressed point) returned a **wrong** answer from the MARSYS-JIS chat UI. Investigation traced it to a corrupt signal.

**Canonical truth (L1, authoritative)** — `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md §22`:

```
VRS.MUNTHA.SIGN  = Libra (7th House)
VRS.MUNTHA.LORD  = Venus
VRS.VALIDITY     = 2026-02-05 to 2027-02-05
```

This is astronomically correct: native lagna = Aries; Muntha advances one house/year from the 1st house at birth; at age 42 (year starting 2026-02-05) the Muntha is in the 7th house = Libra, lord Venus.

**The corrupt signal — `SIG.MSR.377`** in `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` (the production-loaded version; same bug in v3_0 and v4_0). It is internally inconsistent across **five** fields, and none match the canonical L1:

| Field | Asserts | House |
|---|---|---|
| `signal_name` (title) | "Muntha in Gemini 3H = UL/Spouse-Domain" | 3rd |
| `supporting_rules` + `falsifier` (body) | "Muntha = Virgo 6H" | 6th |
| `entities_involved` | `[JMN.UL, HSE.3, HSE.1]` | 3rd |
| `v6_ids_consumed` | `[HSE.6, HSE.1, PLN.MERCURY]` | 6th |
| `domains_affected` | `[health, career, wealth]` | 6th-flavored |
| **CANONICAL (FORENSIC §22)** | **Libra, 7th, Venus** | **7th** |

Three compounded authoring errors:

1. **Title** conflated the Muntha with the **Upapada Lagna** (UL). The UL sits in Gemini 3H; the title grabbed the UL's house and labeled it "Muntha." UL ≠ Muntha — a category error.
2. **Body** committed an off-by-one: it states the correct formula `(Age mod 12) + 1H = Muntha sign`, then drops the `+1` — `(42 mod 12) = 6 → "Virgo 6H"` instead of `6 + 1 = 7th → Libra`. The signal contradicts its **own** formula.
3. The **correct** value (per the signal's own formula AND FORENSIC) — Libra 7H, Venus — is never stated anywhere in the signal.

The corrected reading shifts the 2026-27 annual emphasis from "3rd-house self-enterprise / 6th-house difficulty" to the **7th-house partnership axis (Venus-ruled)** — a materially different interpretation.

## §2 The process-difference insight (the load-bearing realization)

The native observed: **the MARSYS-JIS chat UI gave the WRONG Muntha, but Anthropic Claude chat, given the same underlying data, gave the CORRECT Muntha.** Why?

Because the two systems have fundamentally different relationships to the data:

- **Claude-direct** reasons holistically over the canonical chart. It either reads FORENSIC §22 (Libra 7H) or computes the year-of-life arithmetic correctly. Nothing biases it toward the corrupt signal — there is no retrieval step elevating SIG.MSR.377 above the canonical fact.

- **MARSYS-JIS** runs a RAG pipeline, and that pipeline has the **relevance trap**: for a query about "Muntha at age 42," the retriever ranks SIG.MSR.377 as *the single most relevant artifact* (its title is literally that). Synthesis anchors on the top-ranked signal's title. The correct FORENSIC §22 value is either not retrieved or retrieved at lower prominence. **The most retrievable artifact won — even though it was corrupt — because MARSYS synthesis has no rule that says "when an L1 fact and an L2.5 signal disagree, L1 wins."**

One-sentence root cause: **retrievability is not authority, and MARSYS lacks an authority-precedence rule to break L1-vs-L2.5 conflicts in favor of the canonical layer.** Claude-direct never faced the conflict because it was not retrieval-ranked.

This is the **same root pattern** as the dasha hallucination fixed in Phase 5 (`project_phase_5_dasha_campaign` memory): a *derived/computed value living in synthesis-reachable text* (a signal, prose) rather than in an authoritative deterministic source. Two presentations of one disease:
- Dasha: synthesis hand-computed the sequence and drifted ("Saturn MD next" instead of "Ketu MD next").
- Muntha: a signal hand-computed the position, drifted, and then out-ranked the truth.

## §3 The audit surface — measured, real, ~100-130 signals

`025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` has **573 signals** (production-loaded via `platform/src/scripts/etl/msr_loader.ts` into the `msr_signals` table). A grep sweep found:

- **72 signals (~13%)** embed arithmetic / computation markers (`mod`, "compute", "advances by", "per year", degree math) → B.10 hand-computation drift risk
- **90 signals (~16%)** duplicate an L1 positional value (Muntha, Lagna+house, dasha dates, year-lord, Bhrigu Bindu) → cross-layer consistency risk

These overlap, so roughly **100-130 signals** carry computed or positional values that could silently disagree with the canonical L1. SIG.MSR.377 is one confirmed instance. The rest are unaudited.

(The exact sweep that produced these counts: split `MSR_v5_0.md` on `^SIG\.MSR\.\d+:`, regex each block for computation markers and positional-duplicate markers. Reproduce against the latest MSR before scoping.)

## §4 The four-check audit methodology (how to pre-emptively find the rest)

Each check is mechanical, offline, deterministic (no LLM), and CI-gateable:

1. **Cross-layer consistency** (the SIG.MSR.377 class). For every L2.5 signal asserting a value also present in L1, the signal value must equal the L1 value. Mismatch = bug. The ~90 positional-duplicate signals are the priority set. Requires a value-extraction + L1-lookup harness (FORENSIC §22 for Muntha, §5.1 for dasha, FORENSIC planet/house tables for placements, etc.).

2. **Derivation-ledger integrity** (project principle B.3). Every L2.5 positional/computed claim must cite the L1 fact ID it derives from, and the cited fact must support the claim. SIG.MSR.377 cites `HSE.3` for a claim its body computes as 6th and FORENSIC records as 7th — three inconsistent IDs. Flag signals asserting computed values with no valid derivation link, or a link contradicting the claim.

3. **Internal consistency.** Within one signal, `signal_name` / body / `falsifier` / `entities_involved` / `domains_affected` must reference the same house/sign. Extract every house/sign mention per signal; assert agreement. This check alone catches SIG.MSR.377 (3H title vs 6H body vs HSE.3 entities vs HSE.6 v6_ids).

4. **Computed-value provenance** (project principle B.10). Any signal embedding arithmetic (~72) is a hand-computation that should not exist in signal text. Flag for migration to engine-sourcing.

Checks 1-3 are pure data-integrity validators runnable against the MSR file today and re-runnable as a pre-merge CI gate. Check 4 drives the architectural migration.

## §5 The architectural fix (prevents recurrence, not just cleanup)

Correcting SIG.MSR.377 fixes one signal; it does not fix the disease. The disease is that MARSYS treats L2.5 signals as authoritative for computed values and has no precedence rule. Three changes close it:

**A. Authority precedence at synthesis.** Generalize the Phase-5 `DASHA_DISCIPLINE_GATE` pattern: any positional/computed value (Muntha, dasha, degree, house, lagna, varga placement) MUST be sourced from L1 or a deterministic engine, never from L2.5 signal text. When a retrieved signal asserts such a value, synthesis verifies against the L1/engine source; L1 wins on conflict. This is the rule that would make MARSYS behave like Claude-direct.

**B. Engine-sourced computed values.** Move computations into tested engines. The dasha and ephemeris engines already exist (see §6). Muntha should move into `query_varshaphala` (deterministic: `house = (years_elapsed mod 12)+1`, `sign = (lagna_idx + years_elapsed) mod 12`, `lord = sign ruler` — works for ALL years, not just the 2026-27 FORENSIC hardcode). MSR signals then become *interpretive overlays* that reference the engine value and never embed it.

**C. CI validation gate.** Checks 1-3 run pre-merge. A signal whose internal houses disagree, or whose positional claim contradicts L1, cannot land. The next SIG.MSR.377 is blocked at authoring time.

## §6 Canonical references + engine inventory (what exists today)

- **L1 facts**: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` — §22 (Varshaphal/Muntha), §5.1 (Vimshottari dasha 50 rows), §5.2 (Yogini), §5.3 (Chara), planet/house/cusp tables, special lagnas, sahams.
- **L1 structured**: `01_FACTS_LAYER/STRUCTURED/CHART_FACTS_EXTRACTION_v1_0.yaml` → `chart_facts` table. NOTE: has dasha_vimshottari (50), dasha_yogini (17), dasha_chara (144) rows, but **ZERO Muntha/varshphal entries** — Muntha is not in chart_facts at all.
- **L2.5 signals**: `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md` (CURRENT per CAPABILITY_MANIFEST) → `msr_signals` table via `platform/src/scripts/etl/msr_loader.ts`. 573 signals.
- **Retrieval engines that exist** (all planner-reachable, 30 tools total as of 2026-05-19):
  - `query_ephemeris` — date-indexed planet positions + derived (dignity, combust, vargottama, sign_ingress, whole_sign_house, bhava_chalit_house, graha_yuddha). 660,726 rows, 1900-2100.
  - `query_panchanga` — sunrise-anchored tithi/vara/nakshatra/yoga/karana, Bhubaneswar observer.
  - `query_transit_event` — ingress/station/aspect/conjunction search.
  - `query_dasha_periods` — Vimshottari/Yogini/Chara schedule lookup (the Phase-5 dasha-correctness tool).
  - `query_varshaphala` — annual Tajika chart: solar return + ascendant + 9-graha positions. **Explicitly EXCLUDES Muntha + Varshesha** (code comment: "they live at the synthesis layer"). This is the gap to close for Muntha.
- **Synthesis gates** (in `platform/src/lib/prompts/templates/shared.ts`): `B11_EXPLICIT_LAYER_GATE`, `CALIBRATION_LANGUAGE_GATE`, `PRESCRIPTIVE_CITATION_GATE`, `DASHA_DISCIPLINE_GATE` (Phase 5B — the pattern to generalize), `DIVISIONAL_INTEGRATION_GATE`.
- **Validators / checkpoints**: `platform/src/lib/checkpoints/` — `checkpoint_4_5`, `checkpoint_5_5`, `checkpoint_8_5`, `checkpoint_dasha` (Phase 5C — the deterministic-validator pattern to reuse).

## §7 Project principles this bug violates

- **B.1 — Facts/Interpretation separation.** L1 facts are authoritative; L2.5 are interpretations. SIG.MSR.377 (L2.5) overrode FORENSIC §22 (L1) at synthesis time — a layer-authority inversion.
- **B.3 — Derivation-ledger mandate.** Every L2.5 claim must cite the L1 fact IDs it consumes. SIG.MSR.377's cited entities don't match its own claim.
- **B.10 — No fabricated computation.** Computed values requiring a specialist engine must not be invented. SIG.MSR.377 embeds a hand-computed Muntha, computed wrong.

(Principles are in `00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md §B`.)

## §8 Precedent — the campaign discipline + the dasha worked example

This project runs analysis-stream campaigns via a repeatable discipline (see recent memory files):
1. **Research dossier** (root-cause + locked decisions) — e.g., `DASHA_CORRECTNESS_RESEARCH_v1_0.md`, `EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md`
2. **Master plan** with §B state tracker + §D resume protocol
3. **Per-sub-phase brief** (self-contained, Claude-Code-executable)
4. **Executor closes** sub-phase + reports; Cowork records to memory
5. **Sealing artifact** (PHASE_N_CLOSE) at campaign close

The **dasha-correctness campaign (Phase 5)** is the direct precedent and worked example for this work:
- 5A: `query_dasha_periods` tool + R-DA planner rule (made data reachable)
- 5B: `DASHA_DISCIPLINE_GATE` in all 4 synthesis templates (mandated citation)
- 5C: `checkpoint_dasha.ts` deterministic post-synthesis validator (caught violations)
- Follow-up: Yogini/Chara extension

The MSR computed-value-drift campaign is the **generalization** of Phase 5: instead of one value class (dasha), it covers all ~100 computed/positional values, and it adds the authority-precedence + CI-validation layers Phase 5 didn't need.

## §9 Two-stream branch policy (operational)

Per `feedback_two_stream_branch_policy` (declared 2026-05-17): the analysis stream OWNS `analysis/backend-data-pipeline-perf-audit` (recreate from main as `analysis/...-N` when opening a new campaign). The Chat V2 stream owns `chat-v2/*` + `fix/chat-v2-*` branches. Never cross-contaminate. Every Claude Code prompt starts with an explicit `git checkout` to the analysis branch. Parallel sessions use separate git worktrees (`git worktree add ../Madhav-<stream> <branch>`).

Recent state (as of 2026-05-20): main is the production worktree; Phase 4 (ephemeris) + Phase 5 (dasha) campaigns are CLOSED and live in production (`amjis-web-00230-9jx`); the synthesis-templates fix (PR #98) + Bhava-Chalit extension (PR #99) merged. 30 retrieval tools live. The analysis-stream feat/worktrees were cleaned up; recreate as needed.

## §10 Proposed next steps (two options)

**Option 1 — Run the four checks now, produce the findings list.** Turn "could be wrong" into "here are the N signals that ARE wrong or internally inconsistent." This is the direct, highest-value answer to "how do we pre-emptively identify what will be wrong." Output: a findings table (signal_id, check failed, signal-value vs L1-value, severity). This sizes the real problem before any fix is scoped.

**Option 2 — Author the research dossier** (`MSR_COMPUTED_VALUE_DRIFT_RESEARCH_v1_0.md`) formalizing the problem class + the four-check methodology + the phased fix (validators → authority-precedence rule → engine-sourcing migration → correct the findings), with locked-decision questions for the native.

Recommended order: **Option 1 first** (findings list grounds everything), then Option 2 (dossier scoped from real findings), then the campaign.

## §11 Immediate also-do (independent of the campaign)

`SIG.MSR.377` is a confirmed production-affecting bug. Whether or not the broader campaign runs, the signal should be corrected to match FORENSIC §22 (Libra 7H, Venus) across `MSR_v3_0/v4_0/v5_0.md` (v5 is loaded; priority), with a paired re-load via `msr_loader.ts` and an MSR version bump. This can ship as a standalone fix OR as the first worked example inside the campaign.

---

*End of MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0. A new conversation should read CLAUDE.md §C mandatory set first, then this file, then choose Option 1 or 2 in §10.*
