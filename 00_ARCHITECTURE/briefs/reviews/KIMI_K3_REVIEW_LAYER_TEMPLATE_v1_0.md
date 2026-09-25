---
artifact: KIMI_K3_REVIEW_LAYER_TEMPLATE_v1_0
reviewed: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md @ 657fc6ef4 (worktree branch l3/kala-layer-briefs)
parents: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md · 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md
evidence: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md · 00_ARCHITECTURE/briefs/reviews/REVIEW_L0_STRATEGY_v2_0.md · ELEVATION_DERIVATION_CHAIN_v1_0.md · ASSET_ELEVATION_TEMPLATE_v1_0.md
produced_on: 2026-09-25
mode: independent, adversarial, read-only, fresh context; every checkable figure re-run against production Postgres (read-only session, `default_transaction_read_only=on`, as `amjis_app`) or re-grepped at the pinned commits
verdict: ACCEPT_WITH_CORRECTIONS
---

# Review: LAYER_DEFINITION_AND_STRATEGY_TEMPLATE v1.0

**Verdict: ACCEPT_WITH_CORRECTIONS.** In the template's own scale: not ACCEPT — two parent
contradictions stand open (findings 1, 6) and the core promise, zero-invention derivability, still
fails on the only instance (see Derivability: three inventions remain). Not REJECT — the direction
and the method are sound, and demonstrably so: the template's own rules are what surfaced the
instance's defects (the population rule caught three figure classes; the document/layer distinction
was applied correctly in v2.1; every repaired figure I re-ran at source reproduces). What is wrong
is a set of incomplete repairs and missing enforcement, each with known replacement text, none
touching a native ruling.

**Gates.** Per the template's guard 1, every correction below names its gate. Two are live:
**G-brief** — the first `bg_*` asset brief (already armed by the instance's own §7 C-4), and
**G-L1** — the L1 instance (the chain rules L0 wraps before L1 begins). Findings 1, 2, 3, 8 block
G-brief; all findings block G-L1. Operationally: revise this template to v1.1 before either opens.

**Repair ledger, stated honestly.** The packet and the chain doc say ten template defects were found
by the instance "and were repaired here." Measured: of the instance §6's ten, six are repaired in
the template (items 5, 6, 7, 8, 9, 10) and four are not (1 pin-absence branch, 2 external-inputs,
3 harness-state — partially covered, 4 T1-E/T5 root-layer note). Of the instance review's own nine
"worked around silently" defects (a–i), two are repaired (a in form, i), seven are not (b, c, d, e,
f, g, h). The chain doc's "repaired ten times by its first instance" overstates; the real count is
why this review has findings at all.

Line numbers are the template file's own at 657fc6ef4.

## Findings

**1. BLOCKER — §4.4 (L405–416): the inheritance list omits two of product §16's seven required
elements, and the tier-4 template copies the list row for row.**
Product §16: "Every layer and asset brief states: the P-needs (§2) it serves and the §14 obligations
it is scored on, the relevant Jyotish concepts, the preserved kernel, the exact delta, its
authoritative dependencies, and its manifestation or temporal role." §4.4's ten bullets carry five
of these (P-needs; obligations; exact delta via 3.3; dependencies via 2.3; manifestation/temporal
role). **"Relevant Jyotish concepts" and "the preserved kernel" appear nowhere in the inheritance
path** — not in §4.4, not in §1.1 (which never asks for the kernel, though product §11.1 demands
"The useful kernel to preserve: data, rules, computation, interface, identity, tests and evidence"
of every component), and in the tier-4 template only as §6 brief-authored content, not as an
inherited row. The chain doc states the hook is "written to match, row for row" — verified: §0.1's
ten rows mirror §4.4's ten bullets — so the hole propagates to all 129 briefs. The one derivability
test ever run found exactly this (review, derivability item 7) and it is unrepaired (review defect b).
Replacement — add to §4.4:
```
- its relevant Jyotish concepts (2.4, narrowed to the asset) and its preserved kernel (1.1): the
  data, rules, computation, interface, identity, tests and evidence that survive unchanged —
  product §16 names both, of every brief
```
and add to §1.1's per-asset list (L151–154): "the preserved kernel (product §11.1)". Gate: G-brief.

**2. BLOCKER — §5.2 (L469–473): the criteria→section map is demanded of every instance, but the map
is template-fixed content, and it has holes by construction.**
Text: "Before an instance is called ready, map all 32 criteria to the §4.4 inheritance list … Record
the map; it is the derivability test in tabular form." Three defects. (a) The criteria are fixed
(verified in both tracker files: T1 10, T2 6, T3 6, T4 8, T5 2 = 32) and the sections are fixed by
this template, so the map is derivable **once, here**; requiring six instances to re-derive it is
the invention the chain exists to prevent, and it will produce six divergent maps. (b) Holes no
instance can close: T1-G "efficiency" (tracker regex `efficienc|cost|latency|hotspot`) has no
feeding section, because §4.3 dropped the cost element of DP §13.3 item 7 — the parent reads
"Generation/invalidation, compatibility, retained history, cost and rollback"; the template's §4.3
carries generation, invalidation, rollback. The instance review itself found six criteria unfed in
one place (derivability item 6) and listed nine in another (defect a, counting T5 as two) — the
uncounted criteria are the point: nobody has yet produced the full map, including the reviewer.
(c) The map does not exist today — the instance's §7 C-4 admits it — so the first-brief gate is
armed against an artifact the template should have shipped.
Replacement: ship the map in §5.2 — 32 rows, a "fed by" column filled **in this template**; a
criterion with no feeding section is marked PACKET with the owning section named; each instance
re-verifies the map, never re-derives it. Restore "cost" (one word) to §4.3's title and measured_by
so T1-G has a home. Gate: G-brief.

**3. MAJOR — Part 2 permits exemplary enumeration; §4.4 then inherits per asset.**
§2.2/§2.3/§2.4 are written as prose with picked examples, and the one instance's §2.2 lists tables
in three buckets ("Carried fully / Carried partially / Not carried") that **omit `brahma_ontology`
itself** — so the layer's central asset has no stated presentation fields, and its brief author must
invent them. This was the v2.0 review's derivability invention 2; it is still true in v2.1. A
brief-facing section that enumerates by example silently assigns invention to every asset the
example skipped. Add to Part 2's intro (L232–236): "Sections 2.1–2.4 are per-asset enumerations or
explicit class rules ('all catalog assets carry X'). An example is not an enumeration; an asset not
covered by a row or a rule is a hole in the instance." Gate: G-brief.

**4. MAJOR — §5.4 (L529–537): the verdict's assignment is unspecified, and the one instance
self-assigned. This is the observed decay path.**
The guards assume a verdict exists and try to keep it honest: "A correction with no named gate is
not a correction" (L567) and "It becomes ACCEPT only by re-verifying each correction closed"
(L571–573). Nothing says who assigns the verdict or when. What happened, end to end: v2.1's
frontmatter reads `status: ACCEPT_WITH_CORRECTIONS` while its own §5.4 reads "Derivability test —
pending … Independent review — pending … Status is DRAFT_FOR_INDEPENDENT_REVIEW"; the author
assigned the middle tier to himself with the acceptance tests unrun; and the tier-0 chain doc
recorded the self-assigned verdict the same day ("L0 Brahmagyan instance | ACCEPT_WITH_CORRECTIONS,
six corrections with gates"). The corrections themselves live in the instance's §7 prose table,
which no instrument reads — the tracker consumes `asset_gaps.jsonl`, and no L0 correction is in it
(the file holds its schema line only, verified). So the concrete answer to "how does this scale
decay into accepted-corrections-forgotten" is not hypothetical: it is *author assigns AWC → chain
stamps it → corrections sit in prose nothing reads → time passes*. Two repairs, both cheap:
(a) after "Before an instance is called ready:" add "The verdict is assigned by the independent
reviewer, never the author; before review the instance is DRAFT and nothing below it may cite it.
A pending measurement is a document-level absence, not a correction: an instance that has not run
tests 1–4 has no verdict." (b) Guard 3: "A correction is registered where the tracker reads it
(layer-scope gaps go to the gap ledger); a correction that lives only in prose is not registered."
Note that v2.1's C-4 (the unwritten criteria map) is a document-level absence packaged as a
correction — under the rule in (a), v2.1 reverts to DRAFT until its §5.4 tests run. That costs
nothing: v1.0 remains authoritative until then (`supersedes_on_acceptance`). Gate: G-L1, and
retroactive to the L0 instance's status.

**5. MAJOR — §0.4 (L129–133) contradicts the reference-layer clause; the asset-granularity
completeness rule was never added.**
§0.4: "a section, a contract, an asset, a work packet that cannot name what it serves is **struck,
not kept for completeness.**" — unchanged since the first version (verified by diff against
85bf8f14e). §1.5 (L227–229): "**This rule does not apply to a reference layer:** there, an asset is
retired only for failed fidelity … never for lack of a reader." The reference-layer repair
(c2c781f0d) amended §1.2/§1.5/§5.1 and never reconciled §0.4. The instance review's defect e named
the missing rule and was not folded. When v2.0 left 14 of 40 assets untraced, the correct action was
completing Part 0 — which the instance did, against §0.4's letter, which says strike them. Add to
§0.4: "Every asset in 1.1 appears in a 0.1 row, or 0.1 is incomplete. For a reference layer an
untraced asset is always a Part 0 defect: the asset is the tradition; complete the map, do not
strike the asset." Gate: G-L1.

**6. MAJOR — §2.4 (L287–292): five states against the tier-1 parent's six.**
Template: "applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five
states, never a blank." Product §5.1: "applied, inapplicable with reason, unavailable, unqualified,
contradictory, or still unexplored" — six. The template follows DP §5's compression ("an explicit
unavailable/unqualified/unresolved state") against tier 1 and never says so; "contradictory" and
"still unexplored" disappear, and they are the two states L2 and L5 most need. (The instance
review's defect h recorded this as "adds contradictory"; the exact diff is +2 −1 with a rename —
stated here so the repair is made from the lists, not the characterizations.) Replacement: §2.4
inherits product §5.1's six states verbatim, with one note: "DP §5's 'unresolved' is the tier-2
umbrella over the last two; an instance uses the six." Gate: G-L1.

**7. MAJOR — §1.2 (L160–177): the header commands the measurement the clause forbids; "fidelity"
has no scale; the third state is missing.**
(a) L163: "measured_by: ablation of the single asset against the layer's served reading …" sits
above the clause (L173–177): "Ablation is not the measure." The instance review flagged this
residual; unrepaired. (b) Fidelity is named as four dimensions — "identity correct, source present
and qualified, method boundary stated, provenance carried" — with no verdict vocabulary, no
detectors, no matrix requirement. The one instance immediately drifted: six dimensions, filled by
example, two of them operational-honesty measures; unnamed assets filled by inference ("Assets not
named below pass all six dimensions"); and §1.5's conclusion "Nothing fails fidelity outright"
survives in v2.1 while its own new per-asset table carries four FAILs. A word, not yet a
measurement. (c) The instance's §6 item 3 is unrepaired and is L1's certain case: L1 is
contribution-scored and the harness does not exist (W-L0-7, by the instance's own §4.2). The two
offered states — ablate, or "unmeasurable — not reached" — do not cover "no harness".
Replacement for L163:
```
measured_by: chart-product layer — ablation of the single asset against the layer's served reading;
  no served path: "unmeasurable — not reached" with the six-state position from 1.4; no harness:
  "unmeasurable — no harness", the proxy recorded, the harness a packet in 4.2.
  reference layer — the fidelity matrix below, per asset × dimension.
```
and append to the clause: "Fidelity is scored per asset × per dimension in a full matrix, each cell
PASS / FAIL / PARTIAL / N-A with its detector named. A cell filled by inference from a different
measurement is not a fidelity cell." Gate: G-L1.

**8. MAJOR — §5.3 (L483–491): the certification record is specified worse here than in the ledger
that stores it.**
Template: `asset · criterion · criterion_version · evidence (path or query) · verdict ·
verified_by · verified_on`. The as-run ledger (`00_ARCHITECTURE/control/asset_certs.jsonl`, schema
line, read) carries `detector`, a closed verdict vocabulary (PASS|FAIL|PARTIAL|NO_DETECTOR|N/A),
"ELEVATED requires a current PASS or N/A on every required criterion AND zero open gaps", and
"verified_by is never the party that made the change"; tier-4 §7 matches the ledger. Tier 3, which
defines the record, lacks all four. Two further gaps at every tier: no `measured_at` pin (commit /
DB timestamp), without which "evidence (path or query)" cannot be re-run — the template's own
doctrine ("a figure that cannot be re-run is not measured") applied to the certification ledger
itself; and `criterion_version` has no home — tracker TIERS entries are `(key, label, regex)` with
no version field, so "a revised criterion invalidates only its own records" is undetectable as run.
Replacement record: `asset · criterion · criterion_version · detector · evidence (path, query or
run id) · measured_at (commit / DB timestamp) · verdict (PASS|FAIL|PARTIAL|NO_DETECTOR|N/A) ·
verified_by (never the builder) · verified_on`; "elevated = every required criterion carries a
current PASS-or-N/A record AND zero open gaps"; and one tracker line versioning each criterion.
Gate: G-brief (the first §7 write otherwise starts the ledger on the wrong shape).

**9. MAJOR — the population rule does not bind the template's own lines.**
The preamble rule (L57–67) is good and covers the three named failure modes — verified all three
against production: the join-key failure is real (`brahma_ontology`: 741 rows, 730 distinct
`canonical_id`s, the 11 named duplicates reproduced pairwise); the partition failure is real
(`brahma_class_priors`: 171 under `prior_version='1.0'` + 6 under `ne_v01` = the 177 whole-table
figure); the grep-scope failure is real (L0 capability files: 87 total `.ts`, 47 non-test excluding
`__tests__`, 46 also excluding `index.ts` at 85bf8f14e — and my own two instruments disagreed by one
until the `__tests__` exclusion was stated, a live demonstration). But the template does not model
its own rule: §1.1's measured_by (L147) names five instruments with no path, revision or partition;
and §5.3's inherits line (L514) carries "the t3 lesson — 73 freezes evaporated when the campaign
definition re-froze" — **73 does not reproduce**: `asset_frozen` events by revision are t0 77 /
t1 19 / t2 7 / t3 8, and 90 distinct assets frozen pre-t3 hold no t3 re-freeze. Whatever was
counted, the population was never recorded — in the line that motivates the record's design. Repairs:
the preamble gains "The rule binds every figure in the instance, including the frontmatter and the
three header lines"; §1.1's measured_by is rewritten to show how (the instance's frontmatter
`measured_against` block is the model — promote its pattern into the template); "73" is re-measured
or struck. Gate: G-L1.

**10. MAJOR — no state-once rule; the instance shows the rot twice over.**
Review defect g is unrepaired: §5.1's "A layer scores on the subset its 0.2 row names" (L476–477)
never says 0.2 is the only list. v2.1 patched itself by declaring 0.2 "the definitive list for this
layer … and no others" — the template still permits L1 to publish three sets, as v2.0 did. Same
class for figures: v2.1 carries "46 capability files" (§1.3) against "all 49" (§3.1, §3.3, §4.1);
"~172,330" (§1.1) against "173,219" (§1.3); "All 40 are `lit`" (§1.1) against a measured 39
(`asset_throughput` holds 39 `bg_*` rows, all lit; `bg_gochara_citation_resolution` has no row —
re-run today); "`bg_muhurta_lattice` allowlist 4/9 families" (§3.1, §3.2) against "closed
2026-09-04, all nine" (§1.3 seam 5 — production holds 9 families, 173,219 rows, re-run today). Four
internal contradictions survived a fold whose frontmatter claims "all folded", and survived a
dedicated second sweep (git e827dccb3 "remove two withdrawn claims that survived in §3.1 and
W-L0-1"). The template's per-section measurement demands invite re-statement; nothing forbids it.
Add to the preamble, after the population paragraph: "**State once, cite elsewhere.** A figure lives
in its owning section — the obligation set in 0.2, inventory figures in 1.1; every other section
cites it. The same figure at two values in one instance is a document-level finding at review." And
adopt the review's defect-g sentence verbatim: "0.2 may add an obligation from product §14 with the
reason stated; 3.1 and 5.1 cite 0.2 and never re-list." Gate: G-L1.

**11. MINOR — §2.6 precedes §2.5 (L295 vs L342), copied into the instance in that order.** "Fill
each section in the order written" makes order normative; swap the two sections. Recorded in the
instance review (finding 19), unrepaired.

**12. MINOR — Part 3 subsections and §0.4/§5.4 carry no three-line header** against L46's "Every
section carries three lines before its body." The instance copied the omission, and the sections
where its stale figures survived (§3.1, §3.2) are exactly the unheadered ones — no measured_by line
ever attached to them. Require the three lines on every Part-3 subsection and on 0.4/5.4; it is
where deltas trace. (The alternative — amending L46 to name a weaker real rule — forfeits the one
place the acceptance tests bit.)

**13. MINOR — §5.2 inherits the superseded tracker.** Frontmatter (L15) names
`asset_elevation_tracker.py` "(supersedes kala_brief_tracker.py)"; §5.2's inherits (L482) names
`kala_brief_tracker.py TIERS (as run)`. Both files exist and define the same 32 (verified), so today
it is cosmetic; but "as run" is ambiguous, and the instance's §5.2 remark "today lists only the 22
L3 assets" is true only of `kala_brief_tracker.py`'s ASSETS table — the layer-agnostic tracker has a
LAYERS table (L0 already wired `scoring: "fidelity"`) and no ASSETS. Point §5.2 at the superseding
file.

**14. MINOR — §1.1 demands columns the one instance silently dropped.** L153: "contract fields live,
last build" appear in no v2.1 §1.1 column, with no note (review defect f, unrepaired). Keep
"current code on any live head differs from what is deployed" (it produced a real finding class);
demote the other two: "last build and contract fields live where the asset class makes them
measurable; a dropped column is named in the header, never silent."

**15. MINOR — unrepaired instance §6 items 1, 2, 4.**
(1) §0.3 demands seed/registry/pin reconciliation but has no absence branch; the pin instrument is
L3-only (verified: `asset_registry_seed_dag_parity.test.ts` mentions `bg_*` 12 times, only as
upstream ends of `ka_*` edges; no `bg_*` asset's own `depends_on` is pinned — and v2.1's §0.3 still
reads "does not cover `bg_*`", the un-folded correction from the review's re-run row 23). Add: "if a
source does not exist for this layer, say so — its absence is a finding." (2) §2.3 has no line for a
root layer's external inputs; the instance improvised "external inputs declared as contracts"
(editions, engine files, ratifications) — adopt the line; L1 will need it too (Swiss ephemeris).
(4) T1-E and T5 read differently at a root layer (consumers = code reads, not served readings;
campaign ladder where nothing re-froze) — carry the note in §5.2 or the adaptation table's L0 row.

**16. MINOR — §1.5's Σ is unfalsifiable as arithmetic.** The three terms are measured in three
different units (fidelity verdicts; seam measurements; evidence-state positions); nothing sums them,
and 0.2 is prose, so "layer value = Σ individual + Σ synergistic + Σ cross-layer handoff" can only
ever be a judgement argued from three ledgers. The instance did exactly that and did it well. Keep
the decomposition (ruling 2); drop the pretend sum: "the three terms are recorded each in its own
unit and never summed numerically; the elevation delta is the argued conjunction of their shortfalls
against 0.2." The harness clause itself (L231–233) is an **honest fallback, not an escape hatch** —
demonstrated: the instance used it verbatim ("not computable without ablation, and this instance
will not invent one") and the clause still required naming the harness a packet, which exists
(W-L0-7, with a detector). That requirement is what makes it honest; keep it.

## Derivability

**The question:** does the template produce an instance from which an asset brief is written with
zero inventions? I ran three tests.

**Test A — spec completeness.** §4.4's ten bullets against product §16's seven required elements:
five carried, two missing (finding 1). Tier-4 §0.1 copies §4.4 row for row (verified: ten rows ↔
ten bullets), so a brief written perfectly to spec invents the preserved kernel and the relevant
Jyotish concepts before it measures anything.

**Test B — derive the `bg_ontology` brief from v2.1 + tiers 1–2.** Row by row over §4.4:
*derivable* — P/V rows (0.1, second table, row 1: "all 24" — coarse but present); obligations (0.2's
definitive four, with per-scope rules); correctness rules (2.1); contracts with a named gap (0.3/1.4
DP01 row; declared use honestly packeted to W-L0-2); coverage (2.4 rows 1–2); order (4.1 puts it
first) and baseline (deployed == current, stated globally); disposition and must-add (3.2 P/I/E,
3.3's list); measured terms (1.2's per-asset verdicts now exist — identity FAIL, alias PARTIAL,
source/method-boundary/integrity/count PASS; 1.4's DP01 row).
*Not derivable* — its presentation fields (2.2's three buckets omit `brahma_ontology` itself);
its preserved kernel and relevant Jyotish concepts (absent from §4.4); and the 32-criteria map does
not exist (§7 C-4). **Three inventions remain, down from seven.** The promise is zero. The remaining
failures are template failures (findings 1, 2, 3), not author laziness — which is the strongest
evidence that the repair direction is right and unfinished.

**Test C — thin-fill §4.1.** The template requires the three-way baseline "per asset" (L371–373);
v2.1 states it once globally ("deployed == current code … for L0"). For L0 that is derivable only
because it is universal; for L1 — where the template itself names current-code-minus-deployed the
risk term — a global sentence leaves every brief author inventing per-asset baselines. Rule:
baselines are a column in §1.1's inventory, cited by §4.1. (Folded into finding 3's repair class.)

**Answer:** the §5.2 map repair is necessary and insufficient. Sufficiency is findings 1 + 2 + 3
plus the map actually existing — all cheap, all specified. Today the template still permits an
instance that cannot be derived from; after these, the promise is testable again at the first brief.

## What this template invites

The most valuable evidence is what the one disciplined, honest author did with it in one day:

1. **Self-assigned verdicts.** §5.4 lists tests and verdicts but never says the reviewer assigns
them — so the author stamped his own document ACCEPT_WITH_CORRECTIONS with every acceptance test
pending, and the tier-0 chain recorded it the same day. This is the rot the two guards were built
against, arriving through a door the guards do not watch. (Finding 4.)
2. **Document-level absences laundered as gated corrections.** The document/layer distinction
covers wrong figures (document) and recorded defects (layer), but not *required content never
written* — so the unwritten criteria map and the unrun parity test became "corrections" C-4/C-6
with gates, instead of what they are: the instance not finished. A correction whose fix is an edit
or a run is a document absence; only a fix that is a *build* is layer-level. One sentence would
have forced the distinction.
3. **Figures restated per section, drifting silently.** Four live contradictions in v2.1 (49 vs 46;
4/9 vs 9/9; 40 vs 39; "nothing fails fidelity outright" vs four FAIL rows) survived a complete fold
*and* a dedicated re-sweep (git e827dccb3, 5aa1ae928). Every section demanding its own measurement
makes re-statement the path of least resistance; nothing in the template makes the second statement
of a figure a defect. (Finding 10.)
4. **Confessed-untraced content, kept.** The instance's §1.1 carries a paragraph that confesses "no
Part 0 item and no obligation depends on `sort_order`" — and keeps it, labelled observation. §0.4's
strike rule has no grammar for an author who names the nothing and keeps the content anyway; between
reviews the alignment test is decorative. Enforcement would be: the strike is mechanical (an
untraced paragraph does not survive the reviewer's pass, not the author's), and the traces are
bidirectional — each 0.1 row lists the sections that serve it, so unclaimed rows and untraced
sections both show.
5. **Registry-bounded inventory.** §1.1's instruments are all registry-derived (registry, seed, pin,
throughput): an artifact that exists but is registered nowhere is structurally invisible. The
resource-config slice was found by the instance's reviewer, not by its inventory. The template
invites it by naming no instrument for "what exists but is unregistered" — a directory/module scan
for layer-prefixed artifacts, reconciled against the registry, is the missing fourth instrument.
6. **Measuring the easy term.** The instance measured registry hygiene exquisitely (two `sort_order`
collisions, neither load-bearing) and recorded "not verified / not run" on "traceably transformed"
and "value evaluated" for every contract in §1.4 — the load-bearing states. The per-figure
discipline was satisfied while the dominant term went uninstrumented. The packet mechanism absorbed
it honestly (W-L0-7); the invitation to watch in L1–L5 reviews is inventing the number instead.
7. **Populations stated at the wrong grain.** "40 `bg_*` rows" is a population, and every wrong
figure in v2.0 came from a *restriction* never stated (cross-layer only; one partition of a shared
table; tests excluded or not). The rule and its join corollary cover the mechanics; whether they
bite depends on the reviewer re-running — which is why the chain needs the independent review to be
real, as it was here.

## What does not earn its place

The template is close to minimal; cut without losing a derivation, a measurement or a guard:

- §0.4 duplicates §5.4 test 2 (the alignment test is specified twice, once as rule and once as
  gate). Keep the rule in §0.4, the gate in §5.4, and delete the overlap from one of them.
- §1.3's "The L3 audit measured exactly that" (L194) names no source; the phrase exists nowhere else
  in the repository (grep). Cut the clause; keep the department test.
- §3.4's closing sentence ("This is where the synergistic term (1.3) is either built or found
  missing") duplicates 1.3; the section earns its place only as the input/output/use matrix (DP
  §13.3 item 3). Point it at the matrix and cut the echo. (Evidence the echo propagates: the
  instance's §3.4 restated §1.3/§1.1, and its reviewer recommended striking it.)
- The frontmatter changelog's four entries (~330 words) compress to the parents' one-line-per-change
  form. Saving ~150 words; the repairs above add ~200 that buy a working derivability hook and an
  assignable verdict. Net cost near zero, which is the right shape for this revision.

## What I checked at source

Database — production Postgres, read-only session (`default_transaction_read_only=on`, user
`amjis_app`, via the local Cloud SQL proxy), 2026-09-25:

| # | claim (location) | query | result |
|---|---|---|---|
| 1 | 741 ontology rows, 730 distinct ids, 11 duplicates (instance §1.3; review finding 2) | `select count(*), count(distinct canonical_id) from brahma_ontology` + group-by-having | **741 / 730**, the 11 duplicates reproduced pairwise (ashtakavarga concept+school … vyatipata upagraha+yoga) |
| 2 | 662/741 alias sets populated; all 79 empties are doshas (§2.6 rule 1) | cardinality filters, group by class | 662 populated / 79 empty, all `dosha`; 16 classes; Venus = exactly the 7 aliases quoted |
| 3 | class_priors 171 vs 177 partition error (review finding 8) | `group by prior_version` | `1.0`=171, `ne_v01`=6 (177 whole table) |
| 4 | lattice 9 families, 173,219 rows; "4/9 open" stale (review finding 3) | `count(*)`, `count(distinct factor_family)` | **173,219 rows, 9 families** (agnivasa…vara, per-family counts taken) |
| 5 | remedies 341, 289 unresolved, named values (review finding 4) | non-null count + NOT EXISTS join to ontology | 341/341 non-null; 52 resolve / 289 don't; top values BPHS 193, classical_tradition 80, Phaladeepika 11, Tajaka 3, bphs_jaimini 1, nadi_navamsa_patel 1 |
| 6 | rules 3,002 / 3,002 text / 17 yoga-linked / 14 texts (§1.3 seam 2) | counts on `sutravali_rules` | 3,002 / 3,002 / 17 / `dasha_system_id` 0 / 14 |
| 7 | 15 distinct texts (review finding 16) | `count(distinct text_id) from classical_text_chunks` | 15 |
| 8 | vidhi tables 14 + 409, primitives 60, no provenance columns (review finding 20; instance §2.2) | counts + `information_schema.columns` | 14 / 409 / 60; `vidhi_floor_items` columns are `id, intent, primitive_id, item_order, band, args_override, hard_floor` — no provenance; `vidhi_primitives` has `version` |
| 9 | seam-1 joins over-count (§1.3) | left counts vs join counts | 233→237, 79→84, 20→22; parihāra→doṣa 60→60 |
| 10 | catalogs 233/79/20/60/27/17 (§0.1, §1.1) | counts | exact match, all six |
| 11 | legacy `reference_nakshatras` still present (§1.1) | `to_regclass` | both tables exist |
| 12 | `bg_prashna_rules` target NULL + postgres_table; `bg_vidhi_floors` DRAFT (§1.1) | registry select | confirmed both |
| 13 | `sort_order` collisions 68/69 (§1.1) | group-by-having on registry | 68 = vidhi_primitives + formula_constants; 69 = vidhi_floors + sky_calendar |
| 14 | 37/40 integrity detectors (§1.1) | `integrity_check_sql is not null` | 37/40 |
| 15 | "All 40 are lit" (v2.1 §1.1) vs review's 39 (finding 9) | `asset_throughput` state count + anti-join | **39 rows, 39 lit; `bg_gochara_citation_resolution` has no row — the instance's figure is still wrong today** |
| 16 | `bg_ontology`: 4 declared consumers, all intra-L0; `bg_texts` 8 (§0.3) | `depends_on @> array[...]` | 4, all brahmagyan; 8 |
| 17 | 21/19 cross-layer vs 13/27 all-layer consumer counts (review re-run row 1) | exists-subqueries on the array column | 19 with ≥1 cross-layer / 27 with ≥1 any-layer — both figures reproduce, the restriction is the figure |
| 18 | 40 `asset_frozen` under t0, 0 under t3 (§1.1, §2.5) | ledger, `entity_id like 'bg\_%'` | t0 40, t3 0 |
| 19 | "73 freezes evaporated" (template §5.3 inherits, L514) | ledger by revision: t0 77 / t1 19 / t2 7 / t3 8; distinct pre-t3 without t3 re-freeze | **90 — 73 does not reproduce under any reading I could construct** |

Repository — git at this worktree:

| # | claim | command | result |
|---|---|---|---|
| 20 | template revised three times in place (changelog) | `git log --follow` | 85bf8f14e (first) → 676bd8dde (vocab) → c2c781f0d (reference layers) → 629b88693 (verdict scale + population + map) → 657fc6ef4 (chain) — confirmed |
| 21 | 32 criteria, as run (frontmatter, §5.2) | load both trackers' TIERS | both: T1 10, T2 6, T3 6, T4 8 (incl. `Vocab`), T5 2 = **32** |
| 22 | tracker "lists only the 22 L3 assets" (instance §5.2) | `kala_brief_tracker.py` ASSETS | 22 `ka_*` rows, confirmed; `asset_elevation_tracker.py` is layer-agnostic (LAYERS table, L0 `scoring: fidelity`) |
| 23 | certification record shape (finding 8) | read `asset_certs.jsonl` / `asset_gaps.jsonl` schema lines | ledger carries `detector`, closed verdict vocabulary, zero-open-gaps rule, builder-never-verifier — all absent from template §5.3; both ledgers hold only their schema lines |
| 24 | capability files 46 vs 49 (review finding 17) | `git ls-tree` at 85bf8f14e and HEAD, three exclusion rules | 87 total `.ts`; 47 non-test excl. `__tests__`; **46** also excl. `index.ts` — instance's 46 reproduces; a naive `find` gives 47 (one non-`.test.ts` helper in `__tests__`): the exclusion rule is the figure |
| 25 | `graha_labels.ts` generated from the release, not hand-extracted (review finding 14) | `git show 85bf8f14e:…graha_labels.ts` | L34 imports `l0_semantic_release_v1.json` and builds from `semanticRelease.entities` — confirmed |
| 26 | `resolve_entity.ts` normalization (§2.6 rule 3) | same file at 85bf8f14e | `$1 = ANY(synonyms) OR lower(canonical_name_en) = lower($1) OR lower(canonical_name_sa) = lower($1)` + deterministic `ORDER BY … LIMIT 1` — confirmed; note: the resolver silently picks one row for the 11 duplicate ids |
| 27 | lattice allowlist 9 families since 2026-09-04 (review finding 3) | `query_muhurta_lattice.ts` at 85bf8f14e | `FACTOR_FAMILIES` lists all nine |
| 28 | pin instrument is L3-only-ish (instance §0.3; review row 23) | grep `asset_registry_seed_dag_parity.test.ts` | `bg_*` appears 12 times, only as upstream ends of `ka_*` edges — "pins bg_* only as upstream ends" confirmed; v2.1's "does not cover bg_*" is the un-folded wording |
| 29 | `egate.sql` exists (template §2.5 measured_by) | `git ls-tree` | `platform/scripts/nirmana/egate.sql` — confirmed |
| 30 | resource-config slice exists, unregistered (review finding 11) | `git ls-tree` at 85bf8f14e | `l0_resource_config_slice.py` + `_v1.json` + test — confirmed |
| 31 | §0.4 strike rule unchanged since v1; §5.4 was binary (instance §6 item 10) | `git show 85bf8f14e:…TEMPLATE…` | §0.4 byte-identical then and now; §5.4 test 5 then read "verdict ACCEPT or REJECT" — both confirmed |
| 32 | chain arithmetic "0 of 4,128 criterion cells" (chain doc) | 129 × 32 | 4,128 ✓ |
| 33 | CLAUDE.md §N.6–N.8 exists (template §5.2 inherits) | grep | §N.6 serving density, §N.7 narration fidelity, §N.8 earned signal — confirmed |
| 34 | six DP §4.1 classes claim — "sixteen entity classes" (template §2.6) | DB check 2 + parent §4.1 list | DB's 16 classes match the parent's 16 named classes one-for-one |

## What I could not check

- **"73 freezes"** — unreproduced (check 19); its population and instrument are unrecorded. Listed
  here as well as in finding 9 because it is unverifiable, not merely wrong-looking.
- **"The L3 audit measured exactly that"** (§1.3, L194) — no source named; the phrase occurs nowhere
  else in the repository. Plausible, uncited.
- **The v1.0 L0 instance** — I read it only through its review's account; claims about what v1.0
  carried (e.g., the qualification-state vocabulary, the resource-config slice) are taken on that
  review's evidence, which itself reproduced everywhere I could test it.
- **The production probe** (`kala_brief_tracker.py --env-file`'s `probe_db`) — not run by me; it
  covers the 22 L3 assets only.
- **The four items in the instance frontmatter's `not_measured` block** (e.g., "whether any `bg_*`
  table carries a subject/chart column (not checked)") — the instance says they are unchecked; I did
  not check them either.
- **The writer/serving reader-count figures** (§1.1's per-table columns, §1.4's 24/59/41/31/8) — the
  instance's own review found them exclusion-sensitive (±1–4 depending on glob rules); I verified the
  sensitivity class (check 24) rather than re-running forty table greps.
- **Presentation parity** (§2.2's acceptance test, §5.4 test 4) — never run by anyone; not runnable
  by a read-only review.
- **Whether the named-gate guard fires in practice** — no tier-4 instance exists yet; the guard's
  first real test is the first `bg_*` brief, which findings 1, 2, 3 and 8 now block.

## Where each assigned question is answered

1. Derivable instance — the Derivability section; findings 1, 2, 3.
2. Three-term accounting — finding 16; fallback judged honest because the harness-packet requirement
   held in practice.
3. Reference-layer clause — findings 5 (§0.4 contradiction) and 7 (§1.2 header, fidelity scale);
   consistently applied in §1.5, §5.1 and the adaptation table.
4. Population rule — finding 9; the three failure modes verified real (source checks 1, 3, 24).
5. Alignment test — finding 5; "What this template invites" item 4 (decorative in the instance:
   confessed-untraced content kept).
6. Parent conformance — findings 1 (product §16), 6 (product §5.1), 2 (DP §13.3 item 7's cost);
   §13.3's other elements all carried (item 3's "answer authorities" and item 4's "source rights"
   arrive narrowed — noted, not blocking).
7. Verdict scale guards — finding 4; the decay path is observed fact, not conjecture.
8. Certification per criterion — finding 8.
9. What it invites — the dedicated section.
10. What does not earn its place — the dedicated section.
