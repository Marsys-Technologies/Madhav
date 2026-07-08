---
canonical_id: R5_JUDGMENT_LEDGER
version: 1.0
status: LIVE — JL-001, JL-002 (W0a punchlist lane), JL-003 (W0a perf lane), JL-004 (W0b-envelope
lane), JL-005 (W0b-codegen lane), JL-006 (W1 address-resolver lane), JL-007 (W1 chart_query lane),
  JL-008 (W1 dasha_query lane), JL-009 (W1 signals_query/synthesis_query lane), JL-010
  (W1 Ring-1 reconciliation, r5/w1-reconcile), JL-011 (W2 corpus lane, r5/w2-corpus-citations),
  JL-012 (W2 traverse_chart_graph lane), JL-013 (W2 frame-facet lane), JL-014 (W2 paradigm-facet
  lane) recorded
created: 2026-07-08
author: Claude Code (executing CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md Phase-0)
program: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md v1.6 (governing law)
---

# R5 JUDGMENT LEDGER

Every question, ambiguity, confirmation, or judgment call routed to Pratinidhi-R (the authority swarm;
see brief §1) during the R5 run lands here as an entry — never resolved silently by an implementation
lane, never routed back to the native mid-run. Append-only; entries are never edited after being
recorded, only superseded by a later entry that cites the one it revises.

Pratinidhi-R's constitution (strict precedence, per the brief): (1) design doc v1.6 as governing law;
(2) pillar order when in tension — ASTROLOGY > answer-correctness > honesty > latency/tokens > code
convenience; (3) classical citation required for any astrological call (canonical-or-floor — no
uncited substitute, floor with reason given); (4) mainstream-with-contested-flag for genuinely disputed
points. Every ruling here carries native retrospective veto (brief `ratification` clause) — the native
may overturn any entry after the fact; that does not retroactively invalidate work already gated on it,
but does obligate a follow-up entry recording the reversal.

## Entry schema

Each entry is a level-3 heading `### JL-<NNN> — <short title>` with these fields:

- **id** — `JL-<NNN>`, monotonically increasing across the whole R5 run (continues from this file's
  last entry; does not restart per wave).
- **question** — the exact ambiguity, conflict, or decision point a lane or verifier raised.
- **ruling** — Pratinidhi-R's decision, stated as an instruction an implementation lane can act on
  without further clarification.
- **basis** — which constitution tier resolved it (design doc §-citation; pillar-order tiebreak;
  classical citation; or mainstream-with-contested-flag), plus the specific evidence (dossier section,
  audit transcript, live probe result) that grounded the ruling.
- **reversibility** — one of: `reversible` (a later wave can undo this without re-litigating prior
  work), `hard-to-reverse` (undoing it means redoing shipped work), `irreversible` (a prod-visible
  contract change, e.g. an envelope shape or a response_format default flip). Ledger entries with
  `hard-to-reverse` or `irreversible` reversibility get flagged for explicit native attention in the
  next checkpoint report, even though the run does not wait for a reply.

No entries yet — this ledger opens empty at Phase-0 close. The first entry lands when W0a's first lane
raises its first question to Pratinidhi-R.

---

### JL-001 — P5 phala serving-code fix depth: rewrite read paths only, leave writer paths untouched

**question:** §20's fix-class for P5 says "Rewrite serving SQL against mig-330 schema" for
`anchors.py`/`mitigation.py`, but both files contain BOTH read functions (`fetch_anchors`/
`event_anchors` in anchors.py; `mitigation_map` in mitigation.py — the actual live paths behind
`phala_outlook_get` and the FastAPI `/api/compute/phala/event_anchors` route) AND writer functions
(`build_mitigation_rows`/`upsert_mitigation_rows` in mitigation.py, which INSERT into
`phala_mitigation`). The design doc doesn't say whether "rewrite serving SQL" extends to the writer
functions those files also contain. The brief's `must_not_touch` says "orchestrator/planner + ALL
writers (build plane is sealed)."

**ruling:** Fix only the READ functions that are the live serving path (confirmed by tracing
`phala_outlook_get` → `outlook.py::_fetch_anchors`/`_fetch_mitigations` → `anchors.py::event_anchors`/
`mitigation.py::mitigation_map`, and the FastAPI route `POST /api/compute/phala/event_anchors` →
`anchors.py::event_anchors` directly). Both were querying columns (`id`, `theme`, single `confidence`,
`contributing_dashas`/`contributing_signals`, `prediction_state`/`outcome_note` on phala_anchors;
`anchor_id`/`theme`/`mitigation_type` on phala_mitigation) that do not exist on the deployed schema
(migrations 330 + 398 for phala_anchors; 332 for phala_mitigation) — confirmed root cause of the
probe's leaked `column "id" does not exist` / `column "anchor_id" does not exist` errors. Rewrote both
against the real, deployed columns. Left `mitigation.py::fetch_anchors` (used only by the sealed
writer path `build_mitigation_rows`) and `upsert_mitigation_rows` completely untouched — those belong
to the build plane. No new migration required: mig-330 already DROP+recreated phala_anchors with the
correct UUID `anchor_id`; the TEXT-typed `anchor_id` the design doc's "type conflict" note refers to
lives only in the superseded, unapplied `platform/migrations/brahma_phala_anchors.sql` /
`brahma_phala_mitigation.sql` (the "Two-174 trap" — L4 migrations that never landed in the applied
`supabase/migrations/` root). `prediction_state` (anchors) and `mitigation_type` (mitigations) params
are retained as validated-but-not-applied no-ops (documented in both docstrings + the response
provenance envelope) rather than silently dropped or fabricated against a nonexistent column.

**basis:** design doc §20 fix-class for P5 (rewrite serving SQL) + brief `must_not_touch` (writers
sealed) + live schema verification against `platform/supabase/migrations/330_phala_anchors_and_drop_
kala_timeline.sql`, `332_phala_mitigation.sql`, `398_phala_anchors_posterior.sql` (read directly, not
assumed) + code-trace confirmation that `query_remedy_program.ts` (the TS-side capability, already
correct) is a DIFFERENT live path than `mitigation_map` in mitigation.py (which R5_RUN_LEDGER's P5
probe evidence shows is still broken pre-fix).

**reversibility:** hard-to-reverse — the response field renames (`theme`→`domain`/`event_type`,
`confidence`→`posterior`+`confidence_band`, `contributing_dashas`/`contributing_signals`→
`derivation_ledger`/`causal_chain`, mitigation's full field set) are a response-shape change on two
live tool surfaces (`event_anchors`, `mitigation_map` via `phala_outlook_get`). Flagged for native
attention per the reversibility rule.

---

### JL-002 — P8 empty-with-reason: pg_trgm `similarity()` as the "nearest indexed term" mechanism

**question:** E-3's example fix for silent-empty citation lookups ("nearest indexed terms:
[neechabhanga_rules, dignity_cancellation]") implies some notion of lexical nearness, but the design
doc doesn't specify a mechanism. B.10 forbids fabricating a computed value. Is using Postgres
`pg_trgm` trigram `similarity()` against the corpus's own `topics` tags acceptable "real computation,"
or does it need a heavier NLP mechanism, or should the feature be floored/deferred instead?

**ruling:** Use `pg_trgm` `similarity()` against the corpus's own `classical_text_chunks.topics`
values — this is a real, already-precedented computation over live data (pg_trgm is already enabled
DB-wide per migration 067, used for `conversation_messages`/`conversations` search), not a fabricated
score. Wrapped in try/catch: if the extension or query is unavailable in some environment, degrade to
a reason-only empty response (no suggestions) rather than erroring the whole call — never silently
invent a similarity number, never let the enrichment attempt take down the primary result.

**basis:** B.10 (no fabricated computation — pg_trgm similarity IS a real, deterministic, cited
mechanism against live corpus data, not an invented number) + §16 E-3 (empty-with-reason is the
contract; a reason without suggestions is still a legal degraded form) + existing precedent
(migration 067 `pg_trgm` usage elsewhere in the codebase).

**reversibility:** reversible — a later wave can replace the trigram heuristic with a stronger
lexical/semantic nearest-neighbor mechanism (e.g. embedding-based) without changing the response
contract (`empty_reason` + `nearest_indexed_topics` fields are stable regardless of the underlying
computation).

---

### JL-003 — S3 dual-output text-suppression size threshold

**question:** Design §21/S3 prescribes "structuredContent-only above a size threshold" for the MCP
dual-output helper (`dualOutput`/`errorOutput` in `registry_bridge.ts` and the four `register_p1_*.ts`
files) but does not name the threshold. Below what payload size should the text-fallback duplicate
still be sent, and above it suppressed?

**ruling:** 50,000 UTF-8 bytes (`Buffer.byteLength`, compact `JSON.stringify`, no pretty-print). Below
this, dual output (structuredContent + full compact-JSON text) is retained — small/typical responses
keep the MCP provider-spec text fallback for clients that don't consume structuredContent. At or above
it, the text fallback is replaced with a short pointer string and only structuredContent carries the
payload, eliminating the redundant second serialization for the responses where it costs the most
(the 174KB `ganita_yogas_get` case from the P3 probe would have transmitted a pretty-printed dual
payload materially larger than 174KB under the old code; now ~174KB structuredContent-only, no
duplicate text).

**basis:** Pillar order tiebreak (design doc names the mechanism, not the number) — this is a
latency/tokens vs. code-convenience question with no astrological content, so it resolves at tier (2)
without needing classical citation. 50KB was chosen as: (a) comfortably above the vast majority of
per-chart tool responses observed in the Phase-0 probe run (the healthy baseline responses were in the
sub-5KB to ~1KB range; only the known-oversized P3/P5 cases exceed it), so the common case is
unaffected; (b) well below the H-12 1.5MB hard truncation guard already present in `query_signals.ts`,
so it only engages the "large payload" path for genuinely large responses, not routine ones.

---

### JL-004 — W0b unified envelope: `ganita_yogas_get` v3 verdict basis when `yoga_fires`/`dosha_fires` are empty

**question:** Design §10.2/§20 (P3) requires the yogas instrument's envelope `verdict`/`grounding` to
be POPULATED, not hollow. `get_yoga_dosha.ts`'s default category set is
`['yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag']`. Live DB
inspection of the canonical chart (`482012f1-…`, all five ayanamshas) shows `yoga_fires` and
`dosha_fires` return **zero rows** in every ayanamsha — only `yoga_label` (82 rows/ayanamsha) and
`dosha_label` (22 rows/ayanamsha) carry data, plus `bhadra_flag` (1) and `panchaka_flag` (2). Is it
safe to treat `yoga_label`/`dosha_label` row-presence as the "fired" verdict (B.10 — no fabricated
computation), given the category names imply `*_fires` is the activation signal and `*_label` might
be read as a mere catalog?

**ruling:** Yes — treat `yoga_label`/`dosha_label` ROW PRESENCE (per this response's own served rows)
as the fired-count basis, with the verdict's own `note` field stating explicitly that these are
"rows served in this page" counts, not a cross-response total. This is not a fabricated computation:
it counts real rows chart_facts already returned in the SAME response (no new query, no invented
number), exactly the "compute live from this response's own rows" pattern already ratified for
`query_signals.ts`'s DEFECT-001 orphan-rate note and signature_tier distribution (R5 W0a, P4/E-2). The
apparent naming mismatch (`*_fires` vs `*_label`) is a genuine open question about the L1 writer's
category semantics — flagged here, NOT silently resolved by assuming `*_fires` is "the truth" and
`*_label` is "just a catalog." Both readings remain visible: the verdict's `category_counts` field
reports the raw per-category counts (including the empty `yoga_fires`/`dosha_fires` buckets when they
appear in a page) so no information is hidden either way.

**basis:** B.10 (real computation over already-served rows, not invention) + Trap-1 precedent (P4/E-2
freshness-contract pattern: compute honesty notes live rather than assume a stale/uncited fact) +
honesty pillar (ranked above code-convenience) — stating the aggregation basis explicitly in the
verdict's own `note` lets the endpoint LLM (and any acharya reviewer) judge the semantics rather than
silently trusting an assumed label meaning.

**reversibility:** reversible — if a later data-plane audit confirms `yoga_fires`/`dosha_fires` are a
genuinely separate (currently unpopulated) signal rather than a naming variant of `*_label`, the
verdict's `yogas_fired`/`doshas_fired` fields can be repointed without changing the envelope contract
(field names stay stable; only the counting source changes). Flagged for the data-plane audit /
R5_PUNCHLIST, not resolved here as a data-quality finding.

**reversibility:** reversible — a pure serving-layer constant; no envelope shape change, no persisted
state. A later wave can retune the threshold or drop the pointer-string convention without redoing any
other shipped work.

---

### JL-005 — W0b-codegen: base-branch dependency resolution + registry-shim generation scope

**question (a):** The W0b-codegen lane brief specifies starting from `origin/r5/w0b` (base
04b802ad) and closing the §19 hand-mirror violation at `platform-mcp/src/lib/envelope.ts`. But
neither the canonical `platform/src/lib/retrieval/envelope.ts` nor its hand-mirror exist at
04b802ad — they were authored on the sibling `r5/w0b-envelope` lane (commit 4588cc7c, already
pushed to origin, already verifier-reviewed) and are not yet merged into `r5/w0b`. Is it correct
to merge `origin/r5/w0b-envelope` into the codegen lane's working branch before starting, or
should the codegen lane wait / stub out the missing files?

**ruling (a):** Merge `origin/r5/w0b-envelope` in (fast-forward, no conflicts — confirmed via
`git merge --no-edit`, 8 files changed, 0 conflicts). The codegen lane's entire mandate is to
replace a hand-mirror that only exists on that sibling lane; treating it as a required
dependency (not an optional stub) is the only reading consistent with the task brief's own
description of what the lane must do. This is a strangler-pattern stacking of two W0b sub-lanes,
not a scope violation — both lanes are the same wave (W0b), the envelope lane is already
verifier-approved, and `may_touch` for this lane already covers every file the merge brings in
(`platform/src/lib/retrieval/**`, `platform-mcp/src/**`, `00_ARCHITECTURE` run ledgers).

**question (b):** The registry CapabilityDescriptor's `input_schema` (the single source the
codegen script parses) carries no numeric-bounds metadata (min/max) for fields like `limit` —
only the handwritten MCP shim's hand-typed zod schema adds `.min(1).max(25000)`. Should the
generator fabricate bounds to achieve a tighter parity match with the handwritten shim, or
should it honestly reflect only what the descriptor declares?

**ruling (b):** Generate only what the descriptor declares; do not invent bounds. Per B.10 (no
fabricated computation, generalized to no fabricated CONTRACT metadata) — inventing a min/max
that isn't in the single source of truth would itself be a new, uncited hand-authored fact bolted
onto a "generated" artifact, defeating the purpose of codegen. The parity-gate test's corpus
excludes out-of-range numeric values from the comparison (documented inline in both the generator
and the test) rather than silently asserting a false equivalence. Widening the descriptor to
carry bounds metadata (so a future codegen wave can derive `.min()/.max()` faithfully) is flagged
as a real, separate follow-up — not resolved here.

**basis:** Pillar order (§1 constitution) — both questions are engineering/tooling judgment calls
with no astrological content, resolving at tier (4) code-convenience / tier (3) honesty without
needing classical citation, per the JL-003 precedent (W0a perf lane, same tier reasoning).

**reversibility:** (a) fully reversible — a normal git merge; no schema/data change. (b)
reversible — if the registry descriptor type is later amended (D1 amendment procedure,
`registry/types.ts`) to carry bounds metadata, the generator can be extended to emit `.min()/
.max()` and the parity corpus's excluded cases can be reinstated without touching any shipped
contract shape.

---

### JL-006 — W1 address resolver: dispositor source (classical table vs L2 CGM edges) + karaka-school row disambiguation

**question (a):** Design §27.2 says the address resolver is "backed by chart_facts + the CGM's
dispositor edges — the data exists." `bodha_cgm_edges` does carry a `dispositor` `edge_type`
(L2 Bodha layer). Should `dispositor_of(...)` resolve sign rulership from that L2 graph edge, or
from a hardcoded classical fixed-rulership table?

**ruling (a):** Classical fixed table (`SIGN_LORDS` in `address_resolver.ts`), not the CGM edge.
Three reasons, in priority order per the constitution: (1) ASTROLOGY — sign rulership is a fixed
BPHS constant, true for every chart under every school; it is not something that needs to be
"computed" per chart, and citing a graph edge for it would dress a classical fact up as a
derived one; (2) correctness/robustness — `bodha_cgm_edges` is an L2 Bodha campaign artifact that
may not exist for a chart where L2 hasn't been built yet (L2 is "BUILT" for the two canonical
charts today, but the resolver is meant to be a foundational, chart-build-stage-agnostic
primitive per its own module contract); depending on it would make `dispositor_of` fail for any
chart stopped at L1. (3) B.1 (facts/interpretation separation) — an L1-adjacent primitive utility
should not depend on L2 derivations for its own basic correctness. Cross-checked: the classical
table matches every `chart_facts.sign_lord` fact (written by L1 `ga_*` writers) observed on both
canonical charts with zero divergence — so no information is lost by preferring it. The CGM
`dispositor` edge remains available to a future caller wanting graph-context (betweenness,
cross-subsystem mapping) layered ON TOP of this resolver's output; it is not the resolver's
correctness dependency.

**question (b):** `chart_facts.karaka_chara_position` value-rows (`assigned_graha`/`house_d1`/
`sign`) carry no per-row `karaka_school` tag — only separate `karaka_school` rows do, with no
shared row id to join the two together in the EAV shape as built. Should `karaka(...)` resolution
silently assume the schools agree, or should it throw / require an upstream schema change before
resolving at all?

**ruling (b):** Read the value rows directly and document the assumption in code, rather than
either silently hiding it or blocking the whole `karaka()` address type on a schema change outside
this lane's `may_touch` (chart data / L0-L5 tables are read-only for W1; a schema fix there is a
different lane's scope). Verified via direct SQL against both canonical charts: `parashari_
rahu_excluded` and `kn_rao_rahu_included` agree exactly on `assigned_graha`/`house_d1`/`sign` for
all 7 karakas the two schemes share; the 8th karaka (`STRIKARAKA`) exists only under
`kn_rao_rahu_included` and the resolver defaults the school accordingly for that one code. The
`school` field is still carried on both the `AddressExpression` input and the `ResolvedKaraka`
output so a caller's audit trail is honest about which school was requested/assumed even though
today's data doesn't yet distinguish the rows physically. Flagged as a real upstream data-model
gap (no per-row school key) for a future L1/L2 schema-owning lane — not resolved here, only
worked around safely with an explicit, verified assumption.

**basis:** Pillar order (§1 constitution) — ASTROLOGY (fixed classical rulership must not be
demoted to a "computed" graph fact) > correctness (resolver must work without an L2 build
dependency; karaka schools verified to agree before relying on it) > honesty (school field
preserved on the resolved output even where the physical row can't yet distinguish it) >
code-convenience. No disputed-point contested-flag needed — sign rulership and the 7-karaka
Parashari scheme are both textbook-uncontested (BPHS).

**reversibility:** fully reversible on both counts. (a) if a future chart needs a non-Parashari
custom rulership scheme (e.g. KP sub-lord addressing, already out of scope per design §27.4
`paradigm` facet being a later wave), a `paradigm`-aware rulership table can be added alongside
`SIGN_LORDS` without changing `dispositor_of`'s call shape. (b) if L1/L2 ever adds a per-row
school key to `karaka_chara_position`, `fetchKarakaRow` can filter on it directly — the resolver's
public `AddressExpression`/`ResolvedKaraka` shapes need no change, only the internal SQL.

---

No further entries — this ledger reopens for W1+ waves.
### JL-007 — W1 chart_query lane: NF-1 fix approach, dead-param removal, and inline `about` resolver scope

**question (a):** `marsys://tool/L1/chart_facts_query` (NF-1, confirmed still-broken by the W0a
Ring-2 re-audit) 404s because its handler calls a Python sidecar route
(`/api/ganita/chart_facts/query`) that does not exist anywhere in the codebase. The platform
process already owns a live pg pool and every sibling L1 handler (`get_yoga_dosha.ts`,
`get_positions.ts`) reads `chart_facts` directly with no sidecar hop. Should the fix restore/build
the missing sidecar route, or remove the sidecar hop entirely and query Postgres in-process?

**ruling (a):** Query Postgres directly, matching the established sibling pattern. There is no
design mandate anywhere in RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md for a Python-sidecar
hop on a plain relational read of `chart_facts` — §3's SQL idiom says facets "compile to
parameterized SQL inside the existing handlers ... Postgres does the work it was built for." The
sidecar route was never implemented (not merely broken); building it now would introduce a new
network hop §22/§23 explicitly warns against (S1/S5 sinks) for zero benefit over the pattern
every other L1 handler already uses. Lower latency, matches precedent, no design change.

**question (b):** The old descriptor declared `as_of_date`/`from_date`/`to_date` filter params.
`chart_facts` has no `validity_start`/`validity_end` (or any temporal-validity) columns
(confirmed via `information_schema.columns`) — these params could never have filtered anything,
even when the sidecar route existed (nothing in the repo ever defined its contract). Keep them as
harmless no-ops for backward-compatible-looking signature, or remove them?

**ruling (b):** Remove them. Per B.10 (no fabricated computation, generalized here to no
fabricated CONTRACT surface) and the design's honesty mandate (§1: "an agent that can't
distinguish [empty/error/ungranted] makes wrong fallbacks") — a parameter that silently accepts a
value and does nothing is worse than no parameter at all; it teaches the calling LLM a false
affordance. Since the tool 404'd unconditionally in prod, no live caller could have depended on
these params' (nonexistent) behavior, so removal breaks nothing observable. Chart-facts is a
point-in-time computed snapshot per chart_id, not a temporal table — genuine "as of" semantics
belong to `dasha_query`/`kala_query` (already covered by chart_dashas' real date-range columns),
not `chart_query`.

**question (c):** Design §27.2 calls for ONE shared address resolver serving `about` across all
16 instruments. The W1 brief names a sibling lane (`r5/w1-address-resolver`) as the owner of that
shared module, but it did not exist on this lane's base branch at implementation time (parallel
lanes). Should chart_query (a) block/wait for the sibling lane, (b) skip the `about` facet
entirely this wave, or (c) implement a narrow inline resolver scoped to exactly what chart_query
needs?

**ruling (c):** Implement (c) — a minimal inline resolver
(`platform/src/lib/retrieval/registry/layers/L1_ganita/chart_query_about.ts`) covering only
graha-name normalization, bhava (house) addressing, and house-lord indirection (the exact cases
the W1 brief's gate names — lagna, "10th lord"). Blocking on a sibling lane in a parallel-lanes
wave defeats the wave structure; skipping `about` entirely would leave the lane's stated
deliverable unmet. The module is explicitly scoped and commented as a stopgap with a named
reconciliation point (Ring-1, against `r5/w1-address-resolver`'s eventual module) rather than
presented as the permanent shared resolver — this avoids the two-hand-maintained-copies trap
§19 exists to prevent, by making the intended supersession explicit in the code itself. The
house-lord rashi computation uses whole-sign houses (confirmed against both charts' own
`graha_position.house_d1` values — e.g. native chart: Jupiter/Venus in Sagittarius = house 9 from
an Aries lagna, consistent with equal/whole-sign reckoning) and BPHS ch.3's classical rashi
lordships (undisputed across every Vedic paradigm) — cited inline in the resolver module, no
computation invented beyond arithmetic already implied by data already in `chart_facts`.

**basis:** (a)/(b) code-convenience/honesty tier, no astrological content, same tier reasoning as
JL-003/JL-005. (c) touches astrology (classical rashi lordship, whole-sign house convention) —
resolved via cited classical method (BPHS ch.3) per constitution item 3 ("adopt a CITED classical
method"), not an invented rule; the process/scope question (inline-vs-wait) resolves at the
code-convenience tier once the astrological content is settled.

**reversibility:** (a) reversible — a pure serving-layer implementation change; no schema/data
change, no envelope shape change. (b) reversible in the loose sense that params can be re-added
if a future migration ever adds real temporal-validity columns to `chart_facts`, but the current
removal is a genuine contract simplification, not a placeholder. (c) fully reversible — the
inline resolver is three narrow pure functions with no persisted state; Ring-1 can delete it in
favor of the sibling lane's shared resolver, or fold it in as a special case, without touching any
shipped response shape (the `about_resolution` field's shape — `{requested, subjects, chain}` —
is designed to be resolver-implementation-agnostic).
### JL-008 — W1 dasha_query gate: what "≤1KB, ONE call" measures, and the default projection needed to hit it

**question:** Brief §W1 GATE requires "current-dasha lookup ≤1KB in ONE call." A raw `chart_dashas`
row carries ~40 columns (citation strings, verification metadata, jsonb sandhi/concurrent-lord
blobs) — a single unprojected row already serializes to ~2KB, busting the gate before any facet
logic runs. Two sub-questions: (a) does "≤1KB" bind the tool's actual data payload (the capability's
`content` / the MCP `structuredContent`), or the full wire bytes including the dual-output text
duplicate (S3, JL-003) that low-size responses still carry below the 50KB threshold? (b) is adding
a field-projection facet in-scope for a lane whose named facets are system/level/window?

**ruling:** (a) "≤1KB" binds the data payload dimension the facets actually control —
`content`/`structuredContent` — not the S3 dual-output text duplicate. That duplicate is a
distinct, already-identified and already-partially-fixed (JL-003, W0a S3) mechanical serialization
tax orthogonal to faceting; re-litigating it here would conflate two different defects. Measured:
compact-projected single-row current-dasha response = 833B (capability `content`) / 860B
(`structuredContent`) — both ≤1KB; full raw dual-output wire bytes (structuredContent + duplicated
compact-JSON text, per the existing <50KB-keeps-both-copies rule) = ~1.8KB, which is expected and
out of this lane's scope to change. (b) YES — a default `fields=compact` projection is in-scope and
necessary: design §3's general SQL-idiom grammar already names `select: [fields...]` as "projection
— the 63KB killer" for every SQL-idiom instrument (dasha_query is explicitly one, §21 W1 line),
so trimming chart_dashas's verbose/internal columns by default (with `fields=all` or a custom
column list as opt-out) is the same mechanism applied to this instrument, not scope creep. The
compact set keeps `citation_ref` + `verification_pass_status` (B.3 derivation-ledger fields) so
groundedness is not sacrificed for size.

**basis:** Pillar order (§1 constitution) — no astrological content in either sub-question, so
both resolve at tier (4) code-convenience / tier (2) latency-tokens, per the JL-003 precedent
(same tier reasoning, same lane-family). Design doc §3 (line ~116) and §21 (W1 scope line) are the
direct textual basis for treating `select`/projection as already-in-scope machinery, not a new
facet invented outside the brief.

**reversibility:** reversible — `fields` defaults to `compact`; any caller needing the full row
(e.g. a future v3-envelope grounding block wanting every citation field) passes `fields=all` with
no schema/data change required. The default itself could be flipped to `all` later without breaking
the facet's existence, only its default value.

---

No further entries — this ledger reopens for W2+ waves.

### JL-009 — W1 signals_query/synthesis_query lane: E-6 aggregation entity key, envelope wiring site, and two latent serving bugs fixed in-flight

**question (a):** Design §E-6 requires the orient surface (`query_ucd.ts` / `get_chart_orientation`
/ "synthesis_query") to consume the same ranking pipeline as its drill surface
(`query_signals.ts` / `get_signals`) AND apply "hierarchical aggregation" ("one composite
Saturn-AV profile row, never twenty atoms"). Neither the design doc nor the brief specifies the
aggregation KEY. What entity should atomic MSR signals be grouped by?

**ruling (a):** Group by primary graha (the same `extractPrimaryGraha` extraction
`composite_ranker.ts`'s `intrinsicStrength`/`topicRelevance`/`temporalActivation` sub-scorers
already use, read from `configuration_jsonb`), with an `unattributed` bucket for signals that
carry no resolvable graha. This is the only entity dimension already load-bearing in the existing
composite-ranking pipeline (B.10 — no new classification invented); the design doc's own worked
example ("Saturn-AV profile") is graha-keyed; and grouping by graha, not domain or signal_type_class,
keeps `entity_profiles` genuinely useful at the orient (pre-domain) stage — domain-scoped
aggregation is already query_signals.ts's `domain` facet + composite ranking at the drill stage,
so re-deriving domain groups at the orient stage would duplicate rather than complement it.

**question (b):** `query_ucd.ts`'s candidate pool for composite ranking — how wide should it be,
given query_signals.ts uses 500 (CANDIDATE_FETCH_SIZE) plus a dual-pool class-forced merge for
domain-scoped calls?

**ruling (b):** 300, single-pool (no dual-pool class-forcing). The orient surface is
domain-agnostic (composite ranking runs with `domain=null`), so query_signals.ts's dual-pool
rationale (yoga-class signals under-represented in a single top-500-by-salience pool for a
SPECIFIC domain) does not transfer directly — there is no domain to under-represent against.
300 is a judgment-call middle ground (wide enough that hierarchical aggregation has enough atoms
per entity group to be meaningful; narrower than query_signals.ts's page-serving pool because
query_ucd's output is aggregated down to ≤30 entity rows, not a full atomic page) rather than a
measured optimum — flagged as a tuning parameter for the W4 battery to revisit, not a frozen
constant.

**question (c):** In implementing the envelope-wiring + E-6 work, two pre-existing serving bugs
surfaced in `registry_bridge.ts` unrelated to the assigned lane's primary ask: (1) `get_signals`
forwarded its `limit` param as `{ limit: ... }` to `query_signals.ts`, which only reads
`args['top_k']` — the facet was silently ignored (design §18's "diverging param names" premise,
`top_k` vs `limit`); `cursor` was accepted but never forwarded/consumed at all. (2)
`get_chart_orientation` read fields directly off `callRegistryCapability()`'s return value
(`responseData['chart_id']`, `['msr_signal_count']`, etc.) without unwrapping the `.content` layer
that `{content, is_error}`-shaped capability handlers actually return — every one of those field
reads was silently `undefined`, while `get_domain_reading` (three tools above it in the same file)
already does the correct unwrap. Should these be fixed in this lane, or flagged and left for a
separate lane/session given they're not literally "wire the envelope"?

**ruling (c):** Fix both, in this lane. Design §17 states every W1+ wave's acceptance now includes
facet-conformance (E-5 — "a declared-but-ignored parameter... is the worst contract violation in
the estate") and this is exactly that failure class, discovered while touching the exact two
functions this lane owns; deferring a known, already-diagnosed correctness bug in a file this
lane is editing anyway (to fix it "later, elsewhere") would itself violate the pillar order
(answer-correctness > code convenience) for no honesty or latency benefit. Both fixes are
narrowly scoped (parameter plumbing + one unwrap pattern already established one function away in
the same file) and do not touch any other lane's files.

**basis:** B.10 (aggregation/grouping only reuses already-computed extraction logic, never invents
a new classification) + E-5 (facet conformance, "worse than absence, because the endpoint TRUSTS
it") + E-6 (ranking-governed orient surface) + pillar order (answer-correctness over code
convenience, at tier below astrology/honesty — none of (a)/(b)/(c) are astrological calls requiring
classical citation).

**reversibility:** (a) reversible — `entity_type`/`entity` are stable field names; the grouping key
could be widened to a composite (graha × dominant domain) later without an envelope-shape break.
(b) fully reversible — a single constant, easily retuned once the W4 battery has entity-profile
coverage data to measure against. (c) reversible in the trivial sense that it's a bug fix, not a
design decision — but note the FIX ITSELF is not reversible-without-cost: any caller that was
silently depending on `get_chart_orientation`'s previously-`undefined` digest fields (unlikely,
since they were undefined) or on `get_signals`'s previously-ignored `limit`/`cursor` params
resolving to the hardcoded default regardless of input, would see different (correct) values now.

---

### JL-010 — W1 Ring-1 reconciliation (`r5/w1-reconcile`): retiring the chart_query `about` stopgap, folding it into the canonical address resolver, and the dasha `ayanamsha_id` default question

**question (a):** Per JL-007(c)'s own instruction, the chart_query lane's inline stopgap
resolver (`chart_query_about.ts`) must be reconciled into the canonical address resolver
(`address_resolver.ts`) now that both exist on `r5/w1`. The stopgap's graha-name normalizer
(`normalizeGrahaName`) supported Sanskrit aliases (shani, surya, chandra, mangala, kuja, budha,
guru, brihaspati, shukra) that the canonical resolver's `grahaCodeOf`/`GRAHA_ALIASES` did not
yet have (canonical only had 2-letter shorthand + English names). Folding the call site over
naively would silently drop Sanskrit-name support chart_query's own shipped test suite already
covered. Should the canonical module gain these aliases (single table, extended), or should a
second, thinner Sanskrit-alias layer sit in front of it at the chart_query call site?

**ruling (a):** Extend the canonical `GRAHA_ALIASES` table in `address_resolver.ts` itself.
Per design §19's single-source mandate — the exact principle this reconciliation task exists to
enforce — a second alias layer anywhere, however thin, recreates the problem being fixed. These
are standard, undisputed Sanskrit graha names (BPHS/classical nomenclature, no school disputes
them), so adding them is a safe, citable, B.10-compliant addition to the one shared table, and it
makes every other future caller of `grahaCodeOf`/`resolveAddress` benefit from the same coverage
chart_query already had. Cross-checked: no alias collides with an existing key (shani/surya/
chandra/mangala/kuja/budha/guru/brihaspati/shukra were previously entirely absent from
`GRAHA_ALIASES`).

**question (b):** The stopgap's `house_lord`/`bhava_lord` facet served a resolution `chain` as
an array of structured `{step, input, output, basis}` objects (its own bespoke shape); the
canonical resolver's `lord_of` address type produces `ResolvedAddress.chain` as an array of
human-readable strings (its own, differently-shaped, already-shipped design). Folding
`chart_query_about`'s `house_lord` case over to call `resolveAddress(..., {type:'lord_of', ...})`
means the served `about_resolution.chain` shape changes for existing callers of
`chart_facts_query`. Preserve the old object shape (requiring a translation layer that
re-derives `{step,output}` from the string chain), or accept the string-array shape as the new
contract?

**ruling (b):** Accept the string-array shape; update the lane's own integration test
accordingly (done — see `chart_query.integration.test.ts`). Building a translation layer back to
the old object shape would mean maintaining a second parsing/formatting concern purely to
preserve a one-wave-old, never-externally-documented response shape from a resolver that was
itself only a temporary stopgap (JL-007(c) is explicit that the stopgap was never meant to be a
stable contract). No external caller depends on `about_resolution.chain`'s exact shape yet (W1 is
still pre-Ring-2/pre-ship); the string chain is equally informative and is the one the design
doc's own worked examples use for `resolveAddress`. Reversibility below reflects this is a
response-shape change, not a silent behavior change.

**question (c):** The dasha_query verifier finding (see brief item 2) is that `get_dashas.ts`
applies no server-side default for `ayanamsha_id` (unlike `system`/`level`/`window`, which all
default), so omitting it returns all 5 ayanamshas and busts the ≤1KB current-dasha gate. Should
this reconciliation pass ALSO add a server-side default (`ayanamsha_id` defaults to
`lahiri_chitrapaksha` the same way `system` defaults to `vimshottari`), closing the defect at the
source instead of only documenting it?

**ruling (c):** Document only in this pass; do not add a server-side default. Reasoning: (1) the
brief's item 2 scope is explicitly "gate documentation + regression test," not a behavior change
— adding a default is a genuine, additional design decision (does a caller who wants all 5
ayanamshas still have an easy way to ask for that? what's the "all" sentinel, mirroring
`system="all"`?) that deserves its own judgment call and its own wave, not a drive-by fix bundled
into a docs-and-tests task. (2) Unlike `system`, which already has a documented "all" opt-out
convention (`system: 'all'`), `ayanamsha_id` has no such convention today — an unannounced default
would silently change the result set for any existing caller who omits `ayanamsha_id` expecting
all 5 rows back (unlikely usage, but not verifiably absent, unlike the NF-1 sidecar-404 case in
JL-007(a) where the tool was provably unreachable). (3) The fix that IS safe and in-scope —
fixing what an endpoint LLM is told to expect (docstring + input_schema description + the P1-alias
shim's schema override in `register_p1_aliases.ts`) — was made in this pass; that alone should
prevent essentially all real-world gate-busting occurrences, since it was a documentation gap, not
a broken filter. Flagged forward (recorded in `get_dashas.ts`'s own doc comment) for a future wave
to consider the server-side default + its "all" opt-out convention as a deliberate, reviewed
change.

**basis:** (a) design §19 single-source mandate (direct textual basis — this IS the reconciliation
task) + B.10 (Sanskrit graha names are classical constants, no computation, safe to hardcode).
(b) pillar order — none of (a)/(b)/(c) are astrological calls requiring classical citation or
contested-point flagging; resolved at tier (4) code-convenience given no correctness or honesty
cost either way, per the same tier reasoning JL-003/JL-008 used for shape/format judgment calls.
(c) B.10 generalized (§N.4 "no fabricated computation," here extended to "no silent contract
change") + pillar order (a scope-expanding behavior change is lower priority than the literal
brief ask, and risks a new, unreviewed defect class if done as a drive-by).

**reversibility:** (a) reversible — aliases are additive; removing one later only affects callers
using that specific spelling, easily caught by a test. (b) hard-to-reverse in the sense that any
caller who started depending on the new string-array `chain` shape during W1-era testing would
need to re-adapt if a future wave reverted to object-shaped steps — but no such caller exists yet
(pre-Ring-2), so practically reversible today. (c) fully reversible — the documentation-only
choice leaves the server-side default question completely open for a future wave to decide either
way with no sunk cost from this pass.

---

### JL-012 (W2 traverse_chart_graph lane) — three rulings: about-seed DSL requires the resolver's
function-call form (not bare graha names); path endpoints take the resolver's first-listed entity
on multi-entity resolutions; and the valence vocabulary fix scope

**NOTE on numbering:** `address_resolver.ts`'s own header comment cites a `JL-011` (dispositor
resolution — classical fixed-rulership table vs CGM dispositor edges) that does not appear in this
ledger file as committed on this lane's base (`origin/r5/w2`) — likely a sibling W1/W2 lane's entry
not yet merged into this copy (a W2 frame-facet lane appears to have independently claimed JL-011
for a different ruling around the same time this entry was authored). Per the brief's own
numbering-collision precedent (W0b/W1), using `JL-012` here rather than risking a second, different
JL-011; flag for Ring-1 renumbering reconciliation.

**context:** Extended `traverse_chart_graph` (L2 Bodha CGM traversal) per design §21/§30 ("EXTEND
traverse_chart_graph — path patterns, direction facet, strength floors") for the W2 gate: a
"10th-lord→Moon" path resolving in ONE tool call. Three judgment calls surfaced while wiring the
shared address resolver (`resolveAddress`/`address_resolver.ts` — NOT reimplemented, per the lane
brief's explicit instruction) into the graph capability's new `about_from`/`about_to`/`about` params.

**(a) about-seed DSL form.** The design's §27.1 `about` facet examples read informally (e.g.
`about:{graha:'Saturn'}`), which could be misread as accepting a bare graha name string like
`"Moon"` in the `about` array. The resolver's actual DSL grammar (`parseAddressExpression`) requires
either a structured `AddressExpression` object (`{type:'graha', graha:'Moon'}`) or its function-call
DSL string (`"graha(Moon)"`) — a bare `"Moon"` throws `AddressResolutionError` (verified live against
the native chart during this lane's own gate-test authoring: the first draft used a bare string and
failed exactly this way). **Ruling:** document the correct forms in the capability's `input_schema`
description rather than adding a second bare-string-tolerant parsing layer on top of the resolver —
that second layer would be exactly the "duplicate resolver logic" trap the lane brief explicitly
warned against repeating (W1 already hit and fixed it once). The fix is docs-only; the resolver's
grammar is the single source of truth for what strings are valid addresses.

**(b) path endpoints on multi-entity resolutions.** Some address expressions (`occupants_of(...)`)
can resolve to more than one graha entity, but a `paths` query needs exactly one concrete start/end
node. **Ruling:** take the first-listed entity and say so plainly in the returned resolution chain,
rather than erroring or silently averaging/picking arbitrarily. This is not classically arbitrary —
`occupants_of` already returns its graha list in a stable, deterministic order (not shuffled), so
"first-listed" is a reproducible, auditable choice, not noise; a caller who wants a specific occupant
as the endpoint should address it directly (`graha(<name>)`) rather than via `occupants_of`.

**(c) valence vocabulary fix scope.** Verified live against `bodha_cgm_edges` on both canonical
charts (`SELECT DISTINCT valence`) that the real vocabulary is `harmonious`/`antagonistic` only —
the D4-era `benefic`/`malefic`/`mixed`/`neutral` enum the file shipped with never matches a single
live row (the design doc's §21 "valence vocabulary drift... reconcile in W0" caveat was never
actually reconciled, despite the run brief v1.2 changelog describing that caveat as "REPLACED by
the real finding" [native-chart staleness] — the vocabulary drift itself is a SEPARATE, still-live
bug, not superseded by the staleness finding). **Ruling:** fix the enum to the real vocabulary and
accept the legacy D4 terms as normalized aliases (`benefic`→`harmonious`, `malefic`→`antagonistic`,
`mixed`→`neutral`) so no in-flight caller silently breaks, rather than leaving a `valence_filter` that
silently matches zero rows on live data (a strength/floors accuracy conflict — an unfiltered facet is
strictly worse than a filter nobody can use). In scope for this lane because it's the exact file/
exact field this wave's brief instructed to extend for "strength floors," and leaving a known-broken
adjacent filter unfixed while adding new filters next to it would be inconsistent, not scope discipline.

**basis:** (a)+(b) design §19 single-source mandate (do not duplicate the address resolver's
parsing/entity-selection logic) + B.10 (no silent fabrication — a first-of-many-entities choice is
disclosed, not hidden). (c) ASTROLOGY > correctness (a silently-broken valence filter degrades
astrological signal quality — antagonistic/harmonious drishti and yoga distinctions the tradition
cares about) > code-convenience (fixing an adjacent broken enum in the same file/wave is not scope
creep, it's finishing what "extend traverse_chart_graph" already touches).

**reversibility:** (a) fully reversible — pure documentation, no behavior change to the resolver or
its grammar. (b) reversible — a future caller needing "all occupants as separate path endpoints" can
be added as a new `about_from_all`-style param without disturbing this default. (c) reversible —
alias table is additive; a future wave can drop the legacy aliases once no caller depends on them
(easily verified by log/telemetry, per the pattern JL-007/JL-010 used for similar deprecations).

---

### JL-014 — W2 paradigm-facet lane: paradigm vocabulary scope, query_signals default-filter behavior, and the concrete backing for kp/tajika addressing

**note on numbering:** this lane authored JL-011 against its own `origin/r5/w2` base (last entry
on disk was JL-010). A sibling W2 lane (frame-facet) may have independently claimed JL-011 too —
per the W2 brief this is an expected parallel-lane collision, resolved by sequential renumbering
at Ring-1 (the same pattern JL-010 itself documents from W1). Reported clearly here for that pass.

**question (a):** Design §27.4 names exactly 4 paradigms: `parashari (default) | jaimini | kp |
tajika`. Live data (`bodha_msr_signals.signal_tradition` on the canonical chart) actually carries
6 distinct values: the 4 named plus `esoteric` (624 rows) and `lal_kitab` (10 rows). Should the
`paradigm` facet's vocabulary follow the design doc literally (4 values), or expose all 6 values
the data actually supports?

**ruling (a):** Literal 4-value vocabulary from design §27.4 (`parashari`, `jaimini`, `kp`,
`tajika`); `esoteric`/`lal_kitab` are NOT exposed through the facet's enum. Design §27.4 is
explicit and enumerated ("switches the COHERENT interpretive frame: jaimini activates …; kp
activates …; tajika activates …") — it defines the facet as a closed classical vocabulary, not
"whatever signal_tradition happens to contain." `esoteric` and `lal_kitab` are real traditions in
the data but the design doc does not describe what "coherent interpretive frame" either one
activates (no equivalent of "kp activates sub-lord/cusp addressing" is given for either) — adding
them as first-class paradigm values would be inventing design scope, not implementing it. Both
remain queryable via `query_signals`'s existing `source_subsystem`/raw filtering; only the
enumerated 4 are exposed as `paradigm`.

**question (b):** Design §27.4 literally says `paradigm: parashari (default) | ...` — i.e. a
default value. `query_signals` (the L2 Bodha drill surface holding `signal_tradition`) is also
the substrate the whole-chart-read discipline (B.11) and query_ucd's cross-tradition convergence
scoring depend on. Should the default (paradigm omitted) narrow results to `signal_tradition =
'parashari'` per the design's literal default, or return every tradition unfiltered (today's
existing, shipped behavior)?

**ruling (b):** No default filter — paradigm omitted returns every tradition, each row still
individually tagged via its own `signal_tradition` column (never blended into one unattributed
value). Reasons, in pillar order: (1) ASTROLOGY / correctness — B.11 (CLAUDE.md, PROJECT_ARCHITECTURE
§H.4) requires whole-chart reads to route through MSR+CDLM+CGM+RM synthesis BEFORE producing a
domain answer; silently narrowing the default drill surface to one tradition would remove signals
an acharya-grade read needs by default, for every caller who doesn't know to ask for a specific
`paradigm`. (2) honesty — this would be an undisclosed, breaking behavior change to an already-
shipped W1 capability (`query_signals` predates this lane), narrowing what every existing caller
gets back with no opt-out documented anywhere yet. (3) `paradigm` is explicitly presented in the
tool's own description as an OPT-IN ("pass this when you specifically need ONE tradition's clean
signal set") for exactly the design's stated purpose — "gives the triangulation register (A7) its
clean per-paradigm inputs" (§27.4) — not as a universal default-scoping mechanism. The "mixing
paradigms mid-answer" sin §27.4 warns against is a different failure (treating multi-tradition
signals as if they were one coherent, unattributed method) than surfacing multiple individually-
tagged traditions side by side, which `bodha_convergence.cross_tradition_count` shows is a
deliberately-tracked FEATURE of the L2 synthesis layer, not a defect to filter away.

**question (c):** Design §27.4 says "kp activates sub-lord/cusp addressing" and "tajika activates
varshaphala/saham" as things the address resolver should support once paradigm-aware. `chart_facts`
has real backing for kp sub-lord/cusp addressing (`cusp_kp_lords`: prana_lord/star_lord/sub_lord/
sub_sub_lord per CUSP_01..12) and for tajika sāham addressing (`saham_position`: 16+ named sāhams
with sign/house/nakshatra/sign_lord), but has NO varshaphala (annual/Tajika year-chart) data
anywhere — no L1 asset builds an annual chart. Should this lane (a) build only the two address
types with real backing (`sub_lord_of` for kp, `saham` for tajika) and leave varshaphala
unaddressed, (b) block the whole tajika paradigm on varshaphala not existing, or (c) fabricate a
varshaphala placeholder?

**ruling (c):** (a) — build only what has real backing. B.10 (no fabricated computation) rules
out option (c) outright. Blocking the entire tajika paradigm (option b) throws away real,
already-built `saham_position` data over an unrelated missing asset — sāham addressing is itself
a complete, citable tajika practice, not a stub. Ship `saham` (backed, real) now; `varshaphala`
addressing is out of scope until an L1 writer materializes an annual chart — flagged in this
lane's module-header comment and this ledger entry for whichever future wave builds that asset,
so it is not silently forgotten. This mirrors the exact reasoning JL-006(b) used for the karaka
school gap: work with what is verified to exist, document what is deferred, never invent.

**basis:** ASTROLOGY (design §27.4's own enumerated vocabulary and per-paradigm activation list
are the direct textual basis for (a) and (c); no disputed-point flag needed — the 4 named
paradigms and their described addressing schemes are textbook-uncontested) > correctness (B.11
whole-chart-read discipline directly drives (b); (c)'s "only build what chart_facts actually
backs" is a correctness/B.10 call) > honesty ((b)'s no-silent-behavior-change reasoning; (c)'s
explicit deferral note rather than a silent gap) > code-convenience.

**reversibility:** (a) reversible — if a future wave wants `esoteric`/`lal_kitab` exposed as
paradigm values, the enum is additive; no data or shape change needed elsewhere. (b) reversible —
a later wave could add an explicit opt-in default-narrowing mode (e.g. a `strict_paradigm: true`
flag) without breaking today's shipped no-filter default; the underlying data/columns are
unchanged either way. (c) reversible in the strong sense: `sub_lord_of`/`saham` are pure additive
`AddressExpression` variants; a future `varshaphala`-backed address type slots in beside them with
no change to either's contract.

No further entries — this ledger reopens for W2+ waves.

---

### JL-011 — W2 corpus lane (`r5/w2-corpus-citations`): reusing `query_classical_texts` as the `vector_search` target instead of building a new capability, and the hybrid-weighting/top_k defaults

**question (a):** P7's 401 turned out to be two independent bugs stacked: (1) `register_p1_aliases.ts`'s
own `callPlatformPrim` helper — never touched by the W0a punchlist fix, which only fixed
`registry_bridge.ts`'s separate copy of the same helper — was still sending only the Layer-1
internal token, missing `X-MCP-User`/`X-MCP-Key-Id`; (2) even with auth fixed, the retrieval-tool
name `vector_search` had NO entry in `TOOL_NAME_TO_URI` (confirmed live: `getToolByName
('vector_search')` returns `undefined`, so the primitives route would 500 with "Retrieval tool not
found in registry" the moment auth stopped being the blocker). For (2): should `vector_search`
get its own new capability/handler (a dedicated `ref_search`/vector-search implementation), or
should it resolve to the SAME capability `classical_text_search`/`search_classical_texts`/
`read_classical_text` already use (`marsys://tool/L0/query_classical_texts`)?

**ruling (a):** Reuse the existing capability — map `vector_search` onto
`marsys://tool/L0/query_classical_texts` in `TOOL_NAME_TO_URI`, and upgrade that ONE handler to
genuine hybrid ranking, rather than standing up a second corpus-search implementation. This is
the exact "parallel resolver" trap the brief names explicitly (W1 already hit it once with the
`chart_query_about` stopgap vs. the canonical address resolver, reconciled in JL-010(a)) — a
second corpus-search code path would immediately diverge on ranking, param names, or citation
shape from the one already serving `read_classical_text`/`search_classical_texts`/
`classical_text_search`, and there is no design-doc signal that `vector_search` is meant to be
functionally distinct from those (design §3 CORPUS idiom / instrument #13 `ref_search` explicitly
frames `vector_search`, `classical_citation`, and "all ref_* lookups" as ONE consolidated corpus
idiom, with estate consolidation itself deferred to W3 — reusing the handler now is consistent
with where W3 is headed, without pre-building W3's renaming).

**question (b):** Three MCP-facing entry points (`registry_bridge.ts`'s bare `vector_search` tool,
`register_p1_aliases.ts`'s `ref_vector_search` alias, and the existing `find_verses_about` tool)
each use a different parameter name for "the free-text search string" (`query_text`, `query`,
`topic` respectively) and none matches `query_classical_texts`'s pre-existing `keyword` (exact-
phrase ILIKE) parameter. Normalize all three into the one handler (accepting any of
`query_text`/`query`/`topic` as aliases for the same free-text field), or require callers to
adapt to one canonical name and update the three call sites instead?

**ruling (b):** Normalize inside the handler (accept all three names), leave the three call sites'
own schemas untouched. The call sites' param names are each already load-bearing for a DIFFERENT
existing MCP tool identity (`ref_vector_search`'s `query`, `find_verses_about`'s `topic`) that
external/prior-session callers may already be using; renaming them is a breaking-change surface
for zero benefit, whereas accepting all three in the one shared handler costs nothing and is the
same "aliases are additive, canonicalize centrally" pattern JL-010(a) used for the Sanskrit graha
aliases.

**question (c):** No existing design-doc number pins (i) the hybrid vector/keyword weighting split,
or (ii) the default `top_k` for the new free-text/interpretation-intent path (as opposed to the
legacy `keyword`/list path's existing default of 20). Design §3 only says "hybrid keyword/vector +
rerank" and the design's own audit prose (§20/§31) says "top-k≈5 verses in hand" for the
interpretation-intent framing, without a numeric weight split. What values to pick?

**ruling (c):** (i) 0.65 vector / 0.35 keyword. Reasoning: pg_trgm `similarity()` degrades as the
length gap between a short query and a long verse-translation grows (this is a property of
trigram overlap ratios, not a chart/astrology fact — no classical citation applies), so keyword
alone under-ranks true semantic matches on long verses; embedding similarity carries most of the
signal for meaning-level queries, but keyword still needs real weight to catch exact technical
terms an embedding can blur across near-synonyms (e.g. "neecha bhanga" — the literal P8/JL-002
example already in this corpus). (ii) top_k defaults to 5 for the free-text path specifically,
directly citing the design doc's own "top-k≈5 verses in hand" language (§20/§31 audit prose) as
the numeric anchor, while leaving the legacy `keyword`/list path's default of 20 untouched (that
path is exact-phrase/browse behavior, not the interpretation-intent framing the "5 verses" language
is about). Both (i) and (ii) are code-convenience-tier judgment calls, not astrology calls — no
classical citation or contested-point flag applies to either.

**basis:** (a) brief's own explicit "don't repeat the parallel-resolver trap" instruction (direct
textual basis) + design §3/§5 instrument grouping (vector_search is framed as absorbed into corpus
idiom #13, not a standalone). (b) reversibility/no-regression preference — extending a shared
handler's accepted param names is strictly additive; renaming three live MCP tool schemas is not.
(c) pillar order — neither the weighting constant nor the top_k default is an astrological claim;
resolved at tier (4) code-convenience the same way JL-003/JL-008 resolved shape/format calls, with
(ii) additionally citing a concrete design-doc number rather than an arbitrary pick.

**reversibility:** (a) reversible — the `TOOL_NAME_TO_URI['vector_search']` mapping is a one-line
pointer; repointing it at a dedicated capability later (if W3's estate consolidation decides
`ref_search` needs handler-level differences from `query_classical_texts`) does not require
touching any MCP-facing call site, since all three already call by tool name, not by URI. (b)
fully reversible — accepted-alias param names are additive; dropping one later only breaks a
caller using that specific alias, easily caught by the integration test added this pass. (c)
reversible — both are named constants (`VECTOR_WEIGHT`/`KEYWORD_WEIGHT`/`DEFAULT_INTERPRETATION_TOP_K`)
in one file, trivially re-tuned by a future wave with real eval-battery data (§7) once R5's natural-
question battery runs against this path and produces an actual quality signal to tune against.

---

### JL-013 — W2 frame-facet lane: scope of `frame` on get_strength/query_signals (annotate vs. recompute) + reuse of the internal frame-sign resolver

**context:** R5 W2 (lane `r5/w2-frame-facet`, design §27.3) asks for a `frame` facet on
"positional/strength/signal surfaces." `get_positions.ts` is the clean case: `house_d1` is a
stored lagna-relative number, and re-basing it onto another frame (chandra/surya/arudha/
karakamsha) is a pure re-derivation of the SAME underlying fact (the graha's sign), so serving
`house_from_frame` alongside the stored `house_d1` is uncontroversial. Two questions were less
obvious and needed a ruling before touching `get_strength.ts` (L1) and `query_signals.ts` (L2):

**question (a):** `graha_in_house_composite_strength` and similar strength categories store a
FULL 12-row table per graha (`<GRAHA>_IN_HOUSE_1`..`_12`) — build-time formula output, not a
single "current house" value. Does `frame` mean (i) recompute the strength NUMBERS for the
graha's frame-relative house, or (ii) just tell the caller WHICH of the 12 already-served rows
is the graha's actual house under that frame, leaving the numbers untouched?

**question (b):** `bodha_msr_signals` (L2, query_signals) carries `computed_salience`,
`house_weight_multiplier`, and other multi-factor composite-ranking fields. Does `frame` filter
or re-rank these signals for a non-lagna frame, or does it only add context?

**question (c):** Should the query surfaces call the exported `resolveAddress`/
`parseAddressExpression` DSL, or should they use a lighter direct entry point into the same
frame-sign resolution the address resolver already does internally?

**ruling:**
(a) **(ii) — annotate, never recompute.** Strength numbers (Shadbala, Vimsopaka, Ishta/Kashta,
the house-composite table, etc.) are build-time formula output and are explicitly
`must_not_touch` per the R5 brief ("salience/priors/formula constants frozen"). `get_strength.ts`
now returns a `frame_context.active_house_by_graha` map (each graha's real house counted from the
requested frame) so the caller can pick out the correct `<GRAHA>_IN_HOUSE_<N>` row from the SAME
response — the classical judgment ("read Jupiter's in-house strength from Moon") becomes
answerable in one call without inventing a second, frame-conditioned strength formula that no
writer has ever computed or classically defined at build time.

(b) **Annotate only, same reasoning.** `query_signals.ts` now accepts `frame` and, when
non-lagna, returns a `frame_context` block (reference sign + each graha's frame-relative house)
alongside the UNCHANGED signal rows and UNCHANGED `computed_salience`/composite-ranking output.
A signal (e.g. a yoga, a dosha, a composite state) is a classical fact about the chart that does
not stop being true under a different counting frame — what changes is only how its BHAVA
relevance is judged, which the frame_context gives the caller the arithmetic for. Recomputing
salience per-frame would require a second, frame-conditioned formula variant that does not exist
in the frozen salience/priors surface and was explicitly out of this lane's scope.

(c) **Direct entry point — added `resolveFrameReferenceSign` (a public wrapper over the existing
internal `resolveFrameSign`) and a new pure-arithmetic export `houseCountedFrom` (the exact
inverse of the already-exported `signAtHouseOffset`) to `address_resolver.ts`, rather than
routing through the `AddressExpression`/DSL layer.** The DSL (`bhava_from`, `occupants_of`, etc.)
is built for per-address queries where the caller names ONE house/graha at a time; `get_positions`
/`get_strength`/`query_signals` need to re-base MANY rows returned from a single bulk query in one
pass. Building N `bhava_from` calls (one per row) would mean N extra round-trips into the
resolver's own DB reads, when the frame's reference sign only needs to be resolved ONCE per
response and the rest is index arithmetic already available from data already in-hand (the
`sign` column of the very rows being served). Exporting the two small primitives keeps a single
source of truth for "frame → reference sign" and "sign → house-from-reference" (the DESIGN
§27.2 resolver already owns and is tested for both directions) while avoiding a second resolver
implementation — the exact duplication trap W1 hit and fixed once already (per this brief's
explicit warning).

**basis:** (a)/(b) B.10 ("no fabricated computation," generalized here to "no fabricated
per-frame formula variant") + the R5 brief's explicit `must_not_touch` on salience/priors/formula
constants — a correctness/honesty-tier call, not a code-convenience one: recomputing these
numbers per-frame would be presenting a number nothing in the build pipeline ever computed. (c)
design §19 single-source mandate (direct textual basis) + pillar order — reuse over rebuild is
listed ahead of code-convenience in the authority dossier, and the brief names this exact
duplication trap as something W1 already paid down once.

**reversibility:** (a)/(b) fully reversible and additive — `frame_context` is a new field on an
otherwise-unchanged response shape; removing it later (or later adding a genuinely-computed
per-frame formula on top of it) affects no existing caller. (c) fully reversible — both new
exports are pure, side-effect-free wrappers/arithmetic; a future wave replacing them with a
`bhava_from`-based bulk path would only need to swap the internal call site, not any caller-facing
contract.

**standalone value if halted here:** `get_positions` frame facet alone (question (a)'s cousin,
already fully implemented and gate-verified against both canonical charts) independently
satisfies the W2 "from-Moon in ONE call" gate — the strength/signal annotations are additive
value on top, not prerequisites for the gate to pass.

---

### JL-015 — W3 `graha_portrait` lane: two real hollow-field defects found and fixed in the L1 tools it synthesizes over, plus the yoga-participation honesty scope

**context:** Building `graha_portrait` (design §28.2 — the graha-question mirror recipe) as a
synthesis over already-built L1/L2 capability handlers (get_positions, get_dignity, get_strength,
get_avasthas, get_yoga_dosha, get_dashas, query_signals, traverse_chart_graph — no new SQL against
chart_facts/bodha_msr_signals/bodha_cgm_* beyond what those handlers already run) surfaced two real,
previously-undiscovered P3-class hollow-field defects in the L1 tools themselves, live against both
canonical charts, before this portrait could be honestly populated. Both are fixed at the source
file rather than filtered around in the portrait, since every OTHER caller of these tools had the
same silent-empty exposure.

**(a) `get_strength`'s `graha_key` filter matched the wrong column.** The filter was
`fact_key ILIKE '${graha_key}%'` — but `fact_key` is a GENERIC component name shared by every graha
in a category (`"rupa"`, `"score"`, `"bphs_weighted"`); the graha's identity lives in
`fact_subject` (`"SAT"`, `"SAT_IN_HOUSE_5"`, etc. — verified live: `graha_key ILIKE 'SAT%'` against
`fact_key` returns 0 rows for every category on both canonical charts). **Ruling:** fix the filter
to match `fact_subject` (exact, varga-prefix, and house-suffix forms — the same three shapes
`subjectMatchesGraha` in the portrait itself has to recognize across categories), rather than
working around the broken param by re-fetching all rows and filtering client-side in the portrait
only. Any other in-flight or future caller passing `graha_key` had the identical silent-zero-rows
bug; leaving it unfixed while building a new consumer next to it would repeat the exact defect
class (P1/P3) this run has spent three waves hunting.

**(b) `get_dignity`, `get_avasthas`, `get_strength`, and `get_yoga_dosha` never SELECTed
`fact_subject` at all.** Confirmed live: all four handlers' SQL selects
`fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num, fact_value_text, fact_value_jsonb,
unit, verification_pass_status, citation_ref` — omitting `fact_subject` entirely. This means every
row these four tools have EVER returned is anonymous with respect to which graha/entity it
describes (a `dignity_state = "exalted"` row with no way to know which graha is exalted). This is
more severe than (a): it isn't a broken filter, it's a missing column that makes the returned data
structurally unusable for any graha-scoped question — the graha_portrait's three most
design-critical sections (dignity chain, avasthas, functional nature) would have been served
completely hollow (fact_subject undefined on every row) without this fix, the textbook P3 failure
shape. **Ruling:** add `fact_subject` to all four SELECT lists. Purely additive (a new field on an
otherwise-unchanged row shape) — no existing caller's field access breaks; caller code that never
looked at `fact_subject` is unaffected, and any caller who silently depended on the CURRENT
behavior of "cannot tell which graha a row belongs to" was depending on a bug, not a feature.

**(c) yoga/dosha participation is honestly scoped to what's actually populated, not what design
§28.2 asks for verbatim.** §28.2 lists "yogas it participates in" as a portrait field. Live
verification found: L1 `yoga_fires`/`dosha_fires` are 0 rows for both canonical charts (JL-004,
restated rather than re-litigated — this is a requires_pass CATALOG, not confirmed firings); the L2
`bodha_msr_signals` `yoga`/`dosha` `signal_type_class` rows carry the IDENTICAL catalog/
`fire_reason: requires_pass` shape (verified live — same non-finding, different table). The one
MSR `signal_type_class` that IS genuinely chart-specific and graha-attributed is `parivartana`
(structural planetary exchanges, real `planet_a`/`planet_b` pairs, verified populated — 8 matches
for Saturn on the native chart, including a real D33 Venus↔Saturn exchange). **Ruling:** serve
`parivartana` matches as real data, serve `yoga`/`dosha` `signal_type_class` matches too but
labeled `catalog_yoga_matches`/`catalog_dosha_matches` with an explicit "not confirmed firings"
caveat, and state the L1 emptiness with its JL-004 reason rather than either (i) omitting the
section (which would look like a portrait bug) or (ii) padding it with catalog rows presented as
findings (which would be new fabrication on top of an old defect). This is E-3 empty-with-reason
applied at the section level, not a workaround for a data gap this lane can't close (writers are
must_not_touch/frozen; the yoga_fires emptiness is a build-plane issue, not a serving-plane one).

**(d) `chart_dashas.lord_graha` stores full classical names, not codes.** Verified live:
`SELECT DISTINCT lord_graha FROM chart_dashas` returns `"Saturn"`, `"Jupiter"`, etc. — not `"SAT"`/
`"JUP"`. The portrait's dasha section passes `grahaName` (not `grahaCode`) to `get_dashas`'s
`lord_graha` filter for this reason; noted here because it's the same class of naming-convention
inconsistency as (a)/(b) even though `get_dashas.ts` itself needed no fix — the caller (portrait)
just has to know which of its two normalized forms (code vs. name) each downstream tool actually
stores.

**basis:** ASTROLOGY > correctness (a) rejects a filter that silently returns nothing over one that
plainly errors or actually works — Jyotish output must be genuinely case-derived, not accidentally
empty. (b) is a correctness-tier fix, not a code-convenience one: an unscoped-by-entity dignity/
avastha/yoga row is not a smaller version of the right answer, it's an unusable one. (c) honesty >
completeness-for-its-own-sake — the design's field list is a target, not license to fabricate
population where the underlying data doesn't support it (B.10 — no fabricated computation,
generalized to "no fabricated findings"). All four are within this lane's `may_touch` scope
(`platform/src/lib/retrieval/**`) and are exactly the files/columns the W3 brief's own instruction
("reuse existing query functions... rather than re-deriving their data") requires working
correctly, not routing around.

**reversibility:** (a) fully reversible — the WHERE clause change only affects rows returned when
`graha_key` is passed; omitting it is unaffected (matches prior behavior for the common case). (b)
fully reversible and additive — a new column in the SELECT list, no removed/renamed fields, no
behavior change for any caller not reading `fact_subject`. (c) fully reversible — purely a labeling/
note choice in the new capability's own output; changing L1's yoga_fires build state later
automatically improves this section without any portrait-side change. (d) not applicable (no code
changed at the site; a documentation/comment note only).

**standalone value if halted here:** every section of `graha_portrait` is independently useful and
already gate-verified with real, non-hollow data (position, dignity, functional_nature, strength,
avasthas, yogas, dashas, cgm_neighborhood) on both canonical charts — a halt after this lane loses
no partially-built capability; the tool is complete and shippable as specified in design §28.2,
modulo the honestly-scoped yoga/dosha caveat in (c) which is a data-maturity fact, not an
implementation gap.

No further entries — this ledger reopens for W3+ waves.
