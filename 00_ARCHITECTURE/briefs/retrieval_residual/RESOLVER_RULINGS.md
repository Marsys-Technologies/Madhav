---
artifact: RESOLVER_RULINGS.md
canonical_id: RETRIEVAL_RESIDUAL_RESOLVER_RULINGS
version: 1.0
status: LIVE (append-only ledger)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §D.5
---

# Native-Proxy Resolver — Ruling Ledger

Every ruling made under `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §D.5's Native-Proxy
Resolver authority is recorded here with its policy citation, per §D.5's own requirement
("Every Resolver ruling is recorded in `retrieval_residual/RESOLVER_RULINGS.md` with its
policy citation and is itself subject to verifier review."). Append-only; new lanes add new
entries, never edit prior ones except to correct a factual error (noted as such).

---

## Ruling RC-09-001 — 51/51 W1 dark tables, terminal five-state disposition confirmed

**Date:** 2026-07-22
**Residual:** RC-09 (R-8) — Cluster 4, `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E
**Resolver authority cited:** §D.5(iv) — "disposition dark tables using the native's
already-ruled five-state taxonomy (SERVED-DIRECT / SERVED-VIA / OPERATIONAL / GATED /
RETIRED, default-bias SERVE)."

**Ruling:** All 51 tables that were `NEEDS-OWNER` in the W1 census
(`TABLE_CONCEPT_DISPOSITIONS_v1_0.md`) are confirmed to carry a terminal five-state
disposition on current `main` (HEAD at ruling time: `2df42b61`). No table required a new
disposition to be assigned by this ruling — every one already had a hand-verified
disposition recorded in `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §6/§9/§10/§11 (W1-addendum +
W2/W2b lanes, 2026-07-20). This ruling's substantive act is **independent re-verification**,
not re-derivation: confirming that document's claimed wiring is genuinely merged to `main`
(not merely documented), by (a) listing every claimed capability file on disk at the ruling
commit, (b) confirming layer-`index.ts` registration for a representative sample, (c)
re-running the full L0-L5 registry test suite fresh (987 passed / 125 skipped, 0 failed),
(d) grepping the full registry/tools/resources surface for the 4 GATED mimamsa tables to
confirm zero live serving queries exist against them. Full per-table detail:
`DARK_TABLE_DISPOSITIONS_v3_0.md`.

**Disposition counts:** SERVED-DIRECT 40, SERVED-VIA 1, OPERATIONAL 4, GATED 4, RETIRED 2.
Total 51. NEEDS-OWNER: 0.

**Policy citation for the taxonomy itself:** `RULINGS_ADOPTED.md` §F gate ruling
(2026-07-19/20, native), amending `RETRIEVAL_STRATEGY_v1_0.md` §5.2 — "Default bias is
SERVE: the burden of proof is on withholding." No table in the 51 was defaulted to a
withholding disposition (GATED/OPERATIONAL/RETIRED) without cited evidence per-row (see
`DARK_TABLE_DISPOSITIONS_v3_0.md` §2 Evidence column); every non-SERVE disposition traces to
a concrete non-astrological-content finding (bookkeeping/access-control/QA-harness table),
a dead/unreachable writer path, or the pre-ruled L5 calibration-seal reason — never to
"avoid the work of checking."

**Code changes:** none. All 36 genuine SERVE-gap flips required by this ruling's evidence
were already implemented, tested, and merged to `main` in the W2b lane
(`TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §11, 2026-07-20) prior to this residual opening. This
ruling is a documentation/verification closure, not an implementation lane.

**Subject to verifier review:** yes, per §D.5's standing requirement. This ruling's evidence
is independently checkable by re-running the same three commands recorded in
`DARK_TABLE_DISPOSITIONS_v3_0.md` §4 against the merge commit.

---

## Ruling RC-09-002 — `mimamsa_convergence_adjustment` / `mimamsa_anchor_adjustment` GATED (doctrine-extension), re-confirmed

**Date:** 2026-07-22
**Residual:** RC-09 (R-8)
**Resolver authority cited:** §D.5(iii)/(iv) — ruling substitutions/dispositions "using the
doctrine already on record."

**Ruling:** `mimamsa_convergence_adjustment` and `mimamsa_anchor_adjustment` are confirmed
**GATED**, extending the native's pre-ruled GATED disposition for their schema-identical
siblings `mimamsa_fact_adjustment`/`mimamsa_signal_adjustment`. This is not a new ruling —
it is a re-confirmation of the extension `TABLE_CONCEPT_DISPOSITIONS_v2_0.md` §3 already
made on 2026-07-20, on the native's own stated principle: "Only a table requiring a
genuinely NEW gate reason not already grounded in doctrine (A-19/L5-seal/D-14) returns to
the native" (`RULINGS_ADOPTED.md` §F item 2). Both tables share byte-identical schema
(`multiplier`, `raw_multiplier`, `applied_bound`, `evidence_n`, `leakage_status`,
`applies_to_reading`, `derived_from_pramana_ids`) with the two pre-ruled tables, are written
by the same `mi_adhilepa.py` writer pass, and share the same public-face aggregate
(`mimamsa_calibration_get`) and the same revisit condition. No new gate reason is invoked.

**`mimamsa_load_bearing` explicitly excluded** from this extension (confirmed, not
re-litigated): it lacks the `leakage_status`/`applies_to_reading` columns the four GATED
tables share, is written by a different code path shape, and was deliberately wired
SERVED-DIRECT instead — its own file header documents the distinction
(`query_load_bearing.ts`).

**Revisit condition (both extended tables, matching the two pre-ruled tables verbatim):**
"calibration-loop maturity or a Samīkṣā drill requirement" — `RULINGS_ADOPTED.md` §F item 3.

---

## Ruling RC-09-003 — Standing native ruling on the two large L5 calibration ledgers, formally recorded verbatim

**Date:** 2026-07-22
**Residual:** RC-09 (R-8)
**Resolver authority cited:** N/A — this is not a Resolver ruling; it is the **formal
recording** of a native ruling already on record, per the brief's own instruction ("the two
large L5 (mimamsa) calibration ledgers = GATED per the native's 2026-07-22 ruling already on
record").

**Ruling text, as found at its source of record** (`RULINGS_ADOPTED.md` §F item 3, native
ruling 2026-07-19/20 — the brief's dating of this as a "2026-07-22" standing ruling refers to
the residual-closure brief's own re-affirmation of it, not a second, later native act; no
independent 2026-07-22-dated ruling document exists elsewhere in the repo under that exact
date, and no such document should be fabricated to match the date more precisely — the
verbatim ruling text below is the authoritative record regardless of which date it is
indexed under):

> `mimamsa_fact_adjustment` + `mimamsa_signal_adjustment` = **GATED** (reason: L5 STRUCTURAL
> seal + NO-LEAKAGE; public face: `mimamsa_calibration_get`; revisit: calibration-loop
> maturity or a Samīkṣā drill requirement).

**Cross-reference confirming this is the intended "2026-07-22" ruling the brief points to:**
`CLAUDE.md` §E's L5 row — "sealed in **STRUCTURAL mode** — empirical calibration values fill
in as prediction→outcome data accrues (this is by design, not unfinished work)" — is the
same structural-seal doctrine, consistent in substance with the brief's phrasing. No
contradicting or superseding ruling was found anywhere in `CURRENT_STATE_v1_0.md`,
`STATE.md`, or any session note searched this session.

**Disposition:** recorded verbatim, not modified. Both tables remain GATED with the revisit
condition above. See Ruling RC-09-001/002 for the two schema-identical siblings this
principle was extended to.

---

---

## Ruling RC-10-001 — `ganita_structural_get` DEFERRED (facet-multiplexed dispatcher, not a mechanical bridge entry)

**Date:** 2026-07-22
**Residual:** RC-10 (R-9) — Cluster 4, `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E
**Resolver authority cited:** §D.5's residual-disposition authority ("Resolver-disposition each
un-bridged tool with rationale", RC-10's own DONE bar), applying the same evidence-first
discipline RC-09's dark-table rulings established (per-item concrete finding, not a default
withholding).

**Ruling:** `ganita_structural_get` remains unmapped in `LIVE_TOOL_TO_RETRIEVAL`, DEFERRED, not
force-mapped. Evidence: it is a 13-facet dispatcher (`STRUCTURAL_FACET_URI` in
`register_p1_ganita.ts`) routing to a DIFFERENT registry URI per facet, and the Vidhi floor
primitives that declare this `live_tool` do not uniformly carry a `facet` in `tool_args` (e.g.
`bhava_condition`'s is `{chart_id, house}` — no facet at all, with its own `fallback_face`
documenting a different intended capability, `ganita_chart_facts_get(category=bhava)`). A single
static URI mapping would silently serve the wrong data for most callers — the exact
anti-laundering failure §N.6/B.10 forbid, and the precise class of bug `register_p1_ganita.ts`'s
own R-17 serve-time assertion exists to catch on the MCP side. Full evidence:
`NAMESPACE_COVERAGE_v2_0.md` §5 (RC-10-001).

**Disposition:** DEFERRED, honestly reported via `unmappedPrimitives` (never dropped silently,
never force-mapped to a plausible-looking but wrong URI). **Revisit condition:** a future lane
adds facet-aware resolution to `compileFloorForPlan` (deriving the correct facet per
`primitive_id` and selecting the matching `STRUCTURAL_FACET_URI` entry) — real compiler
engineering, out of a bridge-extension's mechanical scope.

## Ruling RC-10-002 — `kala_temporal_bundle` DEFERRED (no registry capability exists; standing documented gap)

**Date:** 2026-07-22
**Residual:** RC-10 (R-9)
**Resolver authority cited:** §D.5's residual-disposition authority, citing doctrine already on
record (per §D.5's requirement that a WONTFIX/DEFERRED disposition cite existing doctrine, not
invent a new reason).

**Ruling:** `kala_temporal_bundle` remains unmapped, DEFERRED. This is not a new finding — it is
the formal recording of a gap already documented verbatim in the codebase at TWO independent
sites: `platform-mcp/src/server.ts:83-84` ("KEYSTONE REQUEST: kala_temporal_bundle... has no
registry primitive. REQUEST to retrieval fork: expose 'kala_temporal_bundle' capability.") and
`platform-mcp/src/tools/register_p1_aliases.ts`'s header "DOCUMENTED DEFERRALS" list, item 6
("kala_temporal_bundle → kala_bundle_get [kala sidecar composite — multi-subsystem gather]").
No retrieval-registry capability of this shape (a composite gather across timeline/convergence/
obstruction/snapshot) exists anywhere in `platform/src/lib/retrieval/registry/layers/**` — this
is a sidecar-only MCP capability by original design, not a bridging oversight.

**Disposition:** DEFERRED, honestly reported via `unmappedPrimitives`. **Revisit condition:** the
retrieval-registry fork builds the requested composite L3 Kāla capability — new-capability
construction, out of a residual bridge-extension's scope; belongs to the registry build track.

**Code changes this ruling accompanies:** 10 of the original 12 unmapped `live_tool` names (all
EXCEPT these two) were mechanically bridged in `compiled_floor_adapter.ts`'s
`LIVE_TOOL_TO_RETRIEVAL` map, each verified as a genuine 1:1 concept match (5 of the 10
independently confirmed by reading the corresponding MCP tool's own handler body to confirm it
calls the identical registry URI). Full per-tool evidence: `NAMESPACE_COVERAGE_v2_0.md`.
Coverage: 11/23 → 21/23 mechanically bridged; 23/23 accounted for (2 DEFERRED with rationale,
zero silent gaps).

> **Correction (2026-07-23, noted per this ledger's own correction-of-factual-error allowance):**
> the "10 of the original 12" / "21/23" figures above counted `ganita_condition_get` as one of the
> 10 genuine 1:1 matches. Independent verification (`VERIFY_RC-10.md`) found this was NOT a
> genuine 1:1 match — see Ruling RC-10-003 below, which DEFERS `ganita_condition_get` alongside
> `ganita_structural_get`. Corrected figures: **9** of the original 12 bridged, **20/23**
> mechanically bridged, **3 DEFERRED** (not 2). This paragraph's original text is left unedited
> above per the ledger's append-only discipline; RC-10-003 is the authoritative correction.

## Ruling RC-10-003 — `ganita_condition_get` DEFERRED (facet-multiplexed dispatcher, identical case to RC-10-001; corrects a REJECTED bridge entry)

**Date:** 2026-07-23
**Residual:** RC-10 (R-9) — Cluster 4, `RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md` §E
**Resolver authority cited:** §D.5's residual-disposition authority ("Resolver-disposition each
un-bridged tool with rationale"), applying the same evidence-first discipline RC-09's dark-table
rulings and RC-10-001 already established (per-item concrete finding, not a default withholding).

**Context:** the RC-10 close originally force-mapped `ganita_condition_get` to
`marsys://tool/L1/get_condition_composite` in `LIVE_TOOL_TO_RETRIEVAL`, on the mistaken premise
that the MCP tool "talks to the same L1 condition-composite writer output." An independent
verifier (`VERIFY_RC-10.md`, 2026-07-23) REJECTED this as a wrong-data laundering defect. This
ruling formally corrects the disposition to DEFERRED, matching RC-10-001's treatment of the
structurally identical `ganita_structural_get`.

**Ruling:** `ganita_condition_get` is DEFERRED, not force-mapped. Evidence (full detail:
`VERIFY_RC-10.md`, `NAMESPACE_COVERAGE_v2_0.md` §4/§5):

1. The MCP handler (`platform-mcp/src/tools/register_p1_ganita.ts` ~L663) is a **3-facet
   dispatcher** over `CONDITION_FACET_URI` (`dignity → get_dignity`, `avasthas → get_avasthas`,
   `karakas → get_karakas`, default facet `dignity`) — it never calls `get_condition_composite`.
2. `get_condition_composite.ts`'s own header states verbatim that `ganita_condition_get`'s facets
   "all read chart_facts directly, not this composite" — direct source-documentation contradiction
   of the rejected mapping.
3. Six Vidhi floor primitives declare this `live_tool` (`bhavesha_condition`, `karaka_condition`,
   `chara_karaka_read`, `dignity_scan`, `arudha_read`, `karakamsa_read` — `registry_data.ts`
   L47/59/107/230/350/472); `ga_condition_composite`'s columns contain no karaka assignment, no
   arudha, and no karakamsa data, so 4 of the 6 (`karaka_condition`, `chara_karaka_read`,
   `arudha_read`, `karakamsa_read`) compiled onto the web door would silently return rows that do
   not contain the concept the primitive asked for — the anti-laundering failure §N.6/B.10 forbid.

A single static URI mapping cannot be correct here — the Vidhi modes
(lord/karaka/chara_karaka/dignity/arudha/karakamsa) do not even correspond 1:1 to the tool's own
3-facet enum, let alone to `get_condition_composite`'s schema. This is the identical failure
shape RC-10-001 already ruled DEFERRED for `ganita_structural_get`; treating the two differently
was the defect this ruling corrects.

**Disposition:** DEFERRED, honestly reported via `unmappedPrimitives` (never dropped silently,
never force-mapped to a plausible-looking but wrong URI). **Revisit condition:** identical to
RC-10-001 — a future lane adds facet/mode-aware resolution to `compileFloorForPlan` (deriving the
correct facet per `primitive_id` and selecting the matching `CONDITION_FACET_URI` entry, noting
the Vidhi modes do not currently map onto the tool's facet enum, so a correct 1:1 does not exist
yet) — real compiler engineering, out of a bridge-extension's mechanical scope.

**Code changes this ruling accompanies:** the `ganita_condition_get: 'marsys://tool/L1/
get_condition_composite'` entry was removed from `LIVE_TOOL_TO_RETRIEVAL` in
`compiled_floor_adapter.ts`; the comment block there and `NAMESPACE_COVERAGE_v2_0.md` (now v2.1)
were corrected throughout. **Coverage corrected: 21/23 → 20/23 mechanically bridged; 23/23
accounted for (3 DEFERRED — structural, temporal_bundle, condition — zero silent gaps).**

**Subject to verifier review:** yes, per §D.5's standing requirement — this ruling is itself the
record of a verifier-driven correction and remains open to further review.

---

## Ruling RC-02-001 — DONE bar narrowed to shared-condition gate-flag parity + measured floor-coverage improvement; full receipt-schema/item-set equality WONTFIX (architectural, not a defect)

**Date:** 2026-07-23
**Residual:** RC-02 (§H.1 crit-6) — Cluster 1
**Resolver authority cited:** §D.5's residual-disposition authority, exercised by the
conductor directly per the RC-02 v2 report's own §6 recommendation (the implementer
correctly declined to self-rule, deferring to "the conductor/Resolver's call").

**Ruling:** RC-02's literal DONE bar text ("the two responses carry the same floor item
set + same gate flags... the deterministic floor/receipt/gates must match") is narrowed
to: (a) for any condition both doors are doctrinally required to enforce identically
(e.g. the NO-LEAKAGE strip), both doors emit the SAME literal flag vocabulary — now true,
fixed and regression-tested this session; (b) floor coverage on the web door is measured,
disclosed, and improving, not silently stagnant or fabricated — now true (2/16 → 8/16,
a direct measured consequence of RC-11's chart_id fix, independently re-verified).

**WONTFIX (architectural, not deferred-as-defect):** literal floor-ITEM-SET equality and
full receipt-SCHEMA unification between `/api/chat/consult` (web, floor-primitive-keyed
receipts via `compileFloorForPlan`) and `prashna_ask` (MCP, tool-name-keyed receipts) is
NOT pursued. Rationale: these are two intentionally different serving architectures for
two intentionally different doors (Paripraśna web chat vs MCP tool-call protocol), not a
parity bug — RC-02's own v1 investigation already established this as a "legitimate
architectural difference the brief doesn't require collapsing" (echoed in the v2 fix
task's own instructions: "Do NOT attempt to unify the receipt SCHEMA itself"). The
remaining floor-coverage gap (8/16, not higher) is not a new open-ended commitment — the
un-bridged capabilities are the same ones RC-10 already measured and DEFERRED with cited
rationale (RC-10-001/002/003: facet-dispatcher primitives with no single correct URI, or
capabilities that are MCP-only by original design). RC-02 does not re-litigate or expand
that already-ruled scope.

**Disposition: RC-02 CLOSES** on the narrowed bar above. Both legs (a) and (b) are
code-complete, independently verified (`VERIFY_RC-02.md`, this branch), and — per the
report's own honest flag — awaiting one deploy-gated live re-confirmation post-deploy,
identical in kind to RC-11/CR-118's own accepted carry-condition. This is not treated as
blocking closure (RC-11 was not held open for its own post-deploy re-probe either); the
conductor performs that live re-confirmation as part of Wave R-C's deploy-verification
step per brief §I, and will record the result here if it diverges from the pre-deploy
evidence.

**Subject to verifier review:** yes, per §D.5's standing requirement.

*End of RESOLVER_RULINGS.md (RC-09/RC-10/RC-02 entries). Next lane appends below this line.*
