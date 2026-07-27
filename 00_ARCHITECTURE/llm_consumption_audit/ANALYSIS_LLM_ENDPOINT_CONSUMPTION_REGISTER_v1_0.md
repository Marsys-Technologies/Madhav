# Analysis — LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0
### Cross-validated against this session's independent live consumption of the same chart (2026-07-26)

*Analyst context: this Cowork session independently exercised the same product surface (claude.ai
MARSYS-JIS connector → amjis-mcp Cloud Run) on the same chart (482012f1) across the same days,
including full 2-page dossier paging to 100% for wealth AND career, judgment_query on 4 domains,
the discovery engine, remedies, and the assess_* family. That gives this analysis something the
register alone cannot have: a second, independent endpoint's measurements to test each claim
against. Verdicts below: **CONFIRMED** (reproduced here), **CONTRADICTED** (my session observed
the opposite), **NUANCED**, or **NOT TESTED**.*

---

## 0 · The single most important meta-finding: two surfaces, two truths

Before item-level triage, one thing must be resolved first because it changes the meaning of
half the register:

**The register's session ran on `marsys-jis-direct`; mine ran on the claude.ai `MARSYS-JIS`
connector. On several load-bearing items we observed *opposite* behavior on the same chart and
the same underlying data** (Bodha build `42720d15…` appears in both sessions' payloads):

| Claim (register) | My session's observation |
|---|---|
| MC-012/013: dossier pages are ~22KB catalog-string dumps, 3.2% coverage/page, 4 pages/domain, auto-hydration "blocked-on-α", receipts don't persist | dossier at `budget_kb: 64` paged **89.2% on page 1, 100% on page 2**, `synthesis_gate: OPEN (coverage_100pct)`, `page_units[].values` carried **real chart-specific hydrated substance** (dignities, SAV bindus, special lagnas, yoga strengths), composition_scaffold served |
| MC-008: D10/D2/D11 "not_computed_at_l1"; assessors fall back to D1 | `judgment_query` returned **`varga_confirmed: D10✓`** (career, composite 4.58) and **`D2✓`** (wealth, 2.38) with full per-varga dignity + D2/D10 aṣṭakavarga piṇḍa rows |
| MC-007: assess_career reading[] 13/13 empty | career slice served **12,455 of 13,825 units**, honest-empty only 1,364 |

Two hypotheses, in order of likelihood: **(a)** `marsys-jis-direct` runs an older server build
(pre-SATYA-ŚEṢA/W7, pre-Ω5-hydration) against the same database — the register's own MC-018
flags the dual identity without resolving it; **(b)** the register's dossier calls omitted
`budget_kb` and got the small default page, making the catalog-heavy pages an artifact of page
size, not server state. Either way: **remediation triage must begin by pinning which revision
`marsys-jis-direct` serves and either upgrading it or retiring it.** Otherwise the register
mixes measurements of the *current* product with measurements of a stale deployment, and fixes
will be misattributed. (Recommend: `mcp_server_info` on both surfaces, compare
`catalog_version`; add revision + build ids to every envelope so this class of confusion is
structurally impossible — extends MC-001's recommendation (b).)

**Important caveat the other way:** several register items are *definitely not* stale-server
artifacts, because my session reproduced them on the current deployment. Those are the ones to
trust unconditionally — listed next.

---

## 1 · Confirmed live on the current deployment (highest-confidence items)

These reproduced in my session on the claude.ai connector, so they are real, current, and
should anchor the P0 list:

- **MC-004 — envelope overflow. CONFIRMED.** `assess_career` returned 146KB in my session (their
  155KB), overflowed the MCP cap, spilled to disk; the raw `dossier` pages at 64KB *also*
  overflow a single response. An endpoint without a shell cannot consume these tools. This is
  the #1 accessibility defect and it is live.
- **MC-005 / MC-023 — trimmer inverts §N.6. CONFIRMED.** In my `assess_career`,
  `completeness_directive` was truncated **mid-sentence** and `coverage_map` came back `[]`
  while thousands of fact_id array entries survived. This is precisely the D3 defect the
  SATYA-ŚEṢA W7.4 hardFloor work was written to close. **On the evidence of both sessions,
  W7.4's hardFloor set is incomplete in production** — the directive/coverage fields (and
  judgment clause prose) are still trimmable. This item should be treated as a **regression
  check against a supposedly-closed campaign item**, not a new finding.
- **MC-015 — discovery duplication across ayanāṃśas. CONFIRMED.** My wealth-scoped
  `bodha_discoveries_get` pull: 53 "discoveries" collapsing to ~2 real motifs × ayanāṃśa
  variants × house variants. The recommendation (collapse to one finding + cross-ayanāṃśa
  agreement score) matches exactly what I had to do by hand.
- **MC-025 — remedy ranking flat + contradictory. CONFIRMED (both halves).** My session saw
  the same 0.49–0.53 resonance band, everything `high`; and my wealth deep-dive agent
  reported **Saturn as "weakest-rank 2 by resonance despite exaltation"** while
  `bodha_chart_digest_get` names **Venus** weakest by shaḍbala. Two L2 surfaces disagree on
  the single most remedy-relevant fact; my sessions adjudicated to Venus (L1 shaḍbala) just as
  the register author did. The normalization-bug hypothesis is plausible: a 0.04 spread over
  9 grahas is the fingerprint of a squashed feature.
- **MC-016 — the flat `constituent_planets` schema invites the Mars error. CONFIRMED — by me
  committing a variant of it.** My own first four-domain reading document stated "Mars in
  Libra (7th, debilitated)" in the chart header. Mars is *neutral* in Libra (debilitation is
  Cancer); the true statements are debilitated-in-D2 (Cancer horā), debilitated-in-D6, and
  the D9-debilitation ledger belonging to *Venus and Saturn*, not Mars. My later career
  deep-dive corrected it ("Mars H7 Libra, neutral, 5.57") but the error shipped in the first
  document. **Two independent endpoints, same error, same schema pressure** — that upgrades
  MC-016 from anecdote to pattern, and the fix (separate `debilitated_planets` /
  `rescuer_planets` fields) from nice-to-have to necessary. I flag and own my instance here;
  the reading document should be corrected.

---

## 2 · Root-cause clustering: 34 symptoms, six diseases

The register is item-rich but cause-poor by design (it logs from the consumer's seat). Grouped,
every item lands in one of six roots — and four of the six are *re-discoveries of laws the
elevation arc already proved*, which is powerful convergent validation:

**R1 — Build-coherence has no invariant.** MC-001 (82.9% orphaned fact_ids after L1 rebuild),
MC-002 (bundle sub-tools erroring, almost certainly downstream of R1), MC-025's
weakest-graha disagreement, MC-003 (provenance citing a deleted artifact). One discipline
fixes all four: derived layers must carry the L1 build-hash they were built against, serving
must compare live, and any mismatch must surface as a top-level freshness flag on *every*
response — not only inside `bodha_quality_get`. Note MC-001's sharpest sub-finding: the
stored `unresolved_constituent_facts_count: 0` contradicting the live 82.9% is a
**stored-vs-derived registry disagreement** — the same GA.1 class the arc has hit before.
Stored aggregates that can disagree with live derivation should be deleted, not fixed.

**R2 — Envelope economics are inverted (§N.6 violated in production).** MC-004/005/006/007,
MC-023's duplicated verdict blocks, MC-014's counterfactual firehoses, MC-021's 245-row
hadda dump. The register's formulation is exact: *the densest layer is trimmed first, the
cheapest-per-byte layer survives.* The remedy is already designed (density contract +
hardFloor); the finding is that it is **inconsistently applied** — W7 fixed the flagship
path, but judgment_query, assess_marriage, tajaka, sade_sati, strength all still violate it.
Recommend a **battery, not per-tool patches**: a regression test that calls every serving
tool at minimum budget and asserts (1) prose/verdict fields untruncated, (2) response fits
the MCP envelope, (3) no field served twice.

**R3 — Status vocabulary conflates "not served" with "doesn't exist" with "negative finding."**
MC-008/MC-017 (`not_computed_at_l1` actually meaning "curated block absent, raw rows exist"),
MC-009 (empty vs not-computed indistinguishable), and — the sharpest and most dangerous —
MC-010 (**"Marriage: denied" language on n_support=0 structural priors**). This is the
S4-03/EL-54 failure class again: this exact conflation caused the false LEL-doesn't-exist
finding in my session, and here it nearly caused the endpoint to broadcast "childbirth:
denied" to a human. **MC-010 is the one item with genuine harm potential and should ship
first regardless of all other priorities.** The fix is a word: `not_yet_assessed
(structural prior, no evidence rows)`. Reserve denial-language for evidenced negatives.

**R4 — Salience monoculture; the completeness contract is unaffordable, so it is bypassed.**
MC-028/030/031/034 + MC-022 + MC-026. This is **the Offer Law, proof #4** — and the most
instructive instance yet, because this time the optional step *was the completeness gate
itself*: the dossier said "Do NOT compose yet," and the endpoint composed anyway because
honoring the gate cost ~88KB of catalog strings. The arc's own law predicts exactly this:
any architecture that makes correctness optional-and-expensive gets incorrectness. The two
concrete casualties are damning: **Mars-in-Puṣkara — the only pushkara firing on the chart,
sitting on the lagneśa/Indu-lord — surfaced in NO ranked surface across ~25 calls**
(MC-030), and **the KP wealth chain was computed, two-pass-verified, tagged wealth… and
floored to the bottom-10% dissent tail** (MC-031). Fixes, in order of leverage:
  1. Make the gate cheap: a compact completeness receipt (coverage % + per-family states +
     gate boolean, ~2KB) decoupled from the concept-catalog dump (MC-012's recommendation —
     and note my session proves the *hydrated* dossier already exists on the current
     deployment, so the affordable-gate work may be mostly done; verify before building).
  2. Salience prior boost for **fired** sensitive-degree facts (pushkara/gandanta/
     mrityu-bhāga firings are rare, high-information events — a fired state should never
     rank below a "dignity: neutral" descriptor row, cf. MC-022's neutral-rows-in-top-20).
  3. A served **domain-reading checklist** (the MC-028 list: bhāva/bhāveśa from Lagna+Moon,
     kārakas, operative vargas, AV, special lagnas, sensitive degrees, KP cusp chain,
     yogi/avayogi, all daśā levels, gochara sweep, tājaka) with a receipt naming which boxes
     were served — so a reading without the receipt self-discloses as "salience-sampled."

**R5 — Computed-but-unreachable, or simply missing.** MC-021/024 (current varṣa-phala
unreachable — filter ignored under two names, silently; 48 verified rows exist), MC-032
(Sūkṣma L4 computed, 536k rows, capped to ≤3 and never advertised), MC-033 (gochara plane
never joined to the financial reading), MC-029 (**yogi/avayogi genuinely absent from L1** —
the only *new computation* the register demands, and the native independently verified the
arithmetic: Yogi=Mercury=current MD lord, Avayogi=Mars=Indu-lord — both consultation-
critical for this chart). WL-4/5/6 extend this root. Note MC-024's process finding is
bigger than tajaka: **inconsistent validation posture** — `dossier` rejects unknown params
loudly (zod), `tajaka` swallows them silently. One strict-schema policy, portal-wide.

**R6 — Schema shapes that invite consumer error.** MC-016 (proven twice, §1), MC-011,
MC-018 (dual identity — see §0), MC-024's silent swallow. Cheap fixes, outsized
trust-protection.

---

## 3 · What the register gets *wrong* or overstates (honest pushback)

- **MC-008/MC-012/MC-013 as stated are partially stale** (see §0). The claim "the deepest
  layer the instrument advertises is exactly the layer that returned empty" was true of the
  surface that session consumed, but the current deployment serves D2✓/D10✓ confirmations and
  a fully hydrated, 2-page, gate-opening dossier. The remediation ticket should be re-scoped
  from "materialize the varga blocks" to "make `marsys-jis-direct` serve what amjis-mcp
  already serves — or retire it."
- **MC-007's "near-zero interpretive yield"** conflates the assess_* *curated reading blocks*
  (which were empty on their surface) with the judgment/dossier path (which carries the
  substance). Real defect, wrong blast radius.
- **MC-020 and the preserve-list are load-bearing, not garnish.** The register is ~85%
  deficiency by volume, but its own evidence shows the six-layer read *was* achievable and
  the honesty scaffolding (`trim_report`, `judgment_flags`, `n_support`, `sub_tools_errored`)
  is what made every single defect *detectable*. Two register items (MC-002, MC-010) were
  only caught because the envelope disclosed its own degradation. Any remediation that
  trades honesty fields for compactness is a net regression — worth stating as a rail.
- **WL-7 needs a cross-reference before anyone builds it.** It asks for native-supplied
  dated financial events "→ LEL enrichment." The LEL already exists — v1.7, CLOSED, 65
  events, wired into l5_lel_intake/calibration/retrodiction — a fact the register's session
  couldn't see because its `bodha_bundle_get` LEL sub-tool errored (MC-002) and its lineage
  (POST_REMEDIATION/REMEDIATION_PLAN_v3_0) differs from the elevation arc's. WL-7 should be
  re-scoped to: *audit which of the 65 events carry financial tags; enrich only the gap.*
  Otherwise a remediation session will solicit data the repo already holds — the exact
  S4-03-shaped mistake this session almost made with the same file.

---

## 4 · Cross-register reconciliation (avoid double-work)

Several MC items are re-observations of already-registered elevation items. The remediation
session should link, not re-open:

| Register item | Existing item / campaign artifact | Status implication |
|---|---|---|
| MC-005/023 trimmer inversion | EL-36/EL-46 class; SATYA-ŚEṢA W7 §1-D3, W7.4 | **Regression** — W7.4 hardFloor set incomplete; reopen with evidence from both sessions |
| MC-028/034 Offer Law | EL-02/EL-14 + the W5 register amendment | 4th proof; extend the amendment: *completeness contracts must be affordable or enforced* |
| MC-017/008 status-label conflation | EL-54 reframe (serving-path vs data) | Same class; one shared fix (status vocabulary) |
| MC-012 dossier paging economics | My session's product-test report §5 | Independently observed on BOTH surfaces; the compact-receipt fix serves both |
| MC-010 "denied" on empty priors | S4-03 false-confidence veto class | Safety-priority instance of the class UAT-DARPANA existed to catch |
| MC-015/026 dedup failures | (new, but one shared pattern) | One family-collapse utility; kala_windows_get already does it right — copy it |

Genuinely **new** and not previously registered anywhere, by my reading: **MC-001/002 (build
coherence — the biggest new correctness finding), MC-010's specific wording hazard, MC-016's
schema split, MC-021/024 (tajaka), MC-025 (remedy flatness + contradiction), MC-029
(yogi/avayogi — the only missing L1 asset), MC-030/031 (salience floors on pushkara/KP),
MC-032 (L4 cap), MC-027 (muhūrta not consuming its own tārā baselines — a quietly excellent
catch: the engine ranked a Vadha-tārā window #2 for this native).**

---

## 5 · Recommended priority order (if a remediation campaign is cut from this)

**P0 — truth & safety (ship regardless of anything else)**
1. MC-010: kill "denied" on n_support=0. One wording change; prevents broadcast harm.
2. MC-001 + MC-002: build-coherence invariant + honest `status: degraded` on bundles. The
   provenance promise (§N.5) is currently false for 82.9% of Bodha; that's a foundation crack.
3. §0 triage: pin/retire `marsys-jis-direct` divergence so future measurements mean one thing.
4. MC-025: one authority for weakest-graha (L1 shaḍbala); root-cause the flat resonance.

**P1 — reachability & the affordable gate**
5. MC-004/005/006 + MC-023: envelope battery + hardFloor sweep across ALL serving tools
   (this is finishing W7.4, with a regression test so it stays finished).
6. MC-021/024: honor `varsha_year`, current-year-first default, strict schemas portal-wide.
7. MC-012-fix + MC-028 contract: compact completeness receipt + served domain-checklist
   with receipt. (Verify against current deployment first — half may exist post-W7.)

**P2 — depth completions**
8. MC-029 yogi/avayogi L1 writer (new asset; two-pass verify).
9. MC-030/031: salience boost for fired sensitive-degrees; KP block in wealth/career checklist.
10. MC-032/033: advertise + serve L4; gochara sweep joined into domain readings.
11. MC-027: tārā/chandra-bala overlay in muhūrta scoring + intra-day cuts.

**P3 — ergonomics** — MC-014 defaults, MC-015/026 dedup, MC-016 schema split (cheap — could
also ride P0 as trust-protection), MC-022 domain filter, MC-003 provenance sweep.

**Breadth (native-supplied):** WL-7 *re-scoped per §3* (audit existing 65 LEL events first),
then WL-8. These convert structural verdicts to calibrated ones — highest leverage per hour
of the native's time of anything in this document.

---

## 6 · One paragraph of appraisal

This is the best consumption-side artifact the project has produced: blunt, specific,
evidence-linked, self-implicating where the endpoint erred (§E is a model of honest error
attribution), and — in §I — it captures the thing no internal test had yet quantified: a
domain expert (the native) auditing a "deepest possible" reading and enumerating exactly what
a complete pass should have contained. Its central lesson is not any single defect but the
composite one MC-034 names: **the system's completeness machinery and its serving economics
are currently enemies** — the gate that guarantees depth is the surface most expensive to
honor, so every rational consumer defects to salience-sampling, and salience provably floors
rare-but-decisive facts (pushkara, KP, yogi). Reconciling those two — completeness that costs
what a consultation can afford — is the arc's next real campaign. Everything else in the
register is a work item; that is the thesis.
