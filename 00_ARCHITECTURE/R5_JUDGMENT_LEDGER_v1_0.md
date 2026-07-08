---
canonical_id: R5_JUDGMENT_LEDGER
version: 1.0
status: LIVE — JL-001, JL-002 (W0a punchlist lane), JL-003 (W0a perf lane), JL-004 (W0b-envelope
  lane), JL-005 (W0b-codegen lane) recorded
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

---

### JL-006 — W1 chart_query lane: NF-1 fix approach, dead-param removal, and inline `about` resolver scope

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

---

No further entries — this ledger reopens for W2+ waves.
