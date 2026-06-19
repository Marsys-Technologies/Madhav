# Prashna — Embed + Implement Across the Layers (paste into Claude Code / Antigravity)

**Read CLAUDE.md §C first + the memory `feedback-prashna-every-query-design` (the GOVERNING design — all native
decisions).** This brief embeds Prashna (horary) across L0→L5 by its layer-roles, per the ratified design. It is
PHASED because one native decision (full horary = ANY querent/subject) COUPLES full activation to the multi-chart
platform, which is NOT yet built (the instrument is single-native, 482012f1). So: build everything that does NOT
require multi-chart now; design + gate the part that does. Do NOT pretend the multi-chart-dependent part can fully
land yet.

## THE DESIGN (ratified — do not re-decide)
Prashna = horary. EXPLICIT user invocation only (not every query). Flow: invoke → VALIDATE it's a genuine
horary/Prashna-type question (reject + tell user if not) → COLLECT location (+ horary inputs) from the user FIRST
→ cast a NEW chart for the question-moment at the querent's location → compute horary judgment → return a
STANDALONE Prashna answer (no natal appendix). Scope = ANY querent, ANY subject (full horary). Boundary: Prashna
is its OWN namespace — natal L2 Bodha NEVER reads ga_prashna. Outcome-tracking DEFERRED to L5.

## STANDING RAILS
computed-and-cited; canonical-or-floor; deterministic-first (the horary JUDGMENT is rule-based/deterministic from
bg_prashna_rules — NOT generative); L1-is-authority; FROZEN orchestrator contract (HALT if a change seems needed
— Prashna is a new CHART-TYPE flowing through the existing pipeline, NOT an orchestrator change); surgical
migrations (≥ next free above 319) + ledger; seed-consistency; endpoint-verify (`?chart_id=`); never fabricate a
horary answer — VALIDATE-and-reject if not a Prashna question.

---

## LAYER MAP (what Prashna is, per layer — the embed targets)
- **L0 Brahmagyan:** GLOBAL horary knowledge = `bg_prashna_rules` (BUILT: 41 rows, 5 sub-tables — Prashna-Lagna
  methods, Ithasala/Eesarpha, significators, fructification, special techniques). Chart-agnostic. ✓ exists.
- **L1 Gaṇita:** DETERMINISTIC facts of the question-moment chart = `ga_prashna` (the horary-judgment writer) +
  the question-moment chart flowing through the normal L1 writers. ← MAIN BUILD-NOW TARGET.
- **L2 Bodha:** a SEPARATE synthesis run scoped to the Prashna chart (NOT the natal bo_* assets). DESIGN-NOW,
  BUILD when natal L2 exists to reuse.
- **L3 Kāla:** Prashna fructification TIMING (Ithasala/Eesarpha applying-aspect timing). DESIGN-NOW, build with L3.
- **L4 Phala:** the Prashna ANSWER (yes/no + timing + significators). Build with L4 (reuses prediction machinery).
- **L5 Mīmāṃsā:** outcome-tracking (was the horary answer right). DEFERRED per native decision.

---

## PHASE 0 — Fix the known blocking bug FIRST (before any Prashna chart is cast)
The `ga_prashna` writer references a table named `ga_positions` directly, but L1 positions live in `chart_facts`
(there is no ga_positions table). If unfixed, ga_prashna produces ZERO rows silently for every Prashna chart (the
silent-failure class). FIX: point the writer at the correct source (`chart_facts` graha_position, the way other
L1 writers read positions — confirm the actual column/category convention against ga_strength/ga_structural).
Verify by casting a test Prashna chart and confirming ga_prashna reads its positions.

## PHASE 1 — L1 Prashna PATH that does NOT need multi-chart (build now, single-querent first)
Build the explicit-invoke → validate → collect → cast → compute → store path, FIRST for the case that works
today (a Prashna chart whose querent is the existing native / a chart_id the pipeline already handles):
1. **Explicit-invoke entry point:** a route/handler (e.g. POST /api/prashna) that accepts a Prashna question +
   question-instant + querent location. (Channel-agnostic: portal + MCP can both call it.)
2. **VALIDATION gate:** classify whether the input is a genuine horary/Prashna-type question (forward-looking /
   yes-no / decision / event). If NOT → return a clear "this isn't a valid Prashna question" message; do NOT
   cast. (Deterministic rules first; an LLM classifier is acceptable HERE for intent-routing — it does not
   generate chart DATA, only routes — but the JUDGMENT stays rule-based. Flag this as the one allowed LLM use.)
3. **COLLECT inputs:** prompt the user for location (lat/lon or place) + any horary inputs the cast needs, BEFORE
   processing.
4. **CAST the question-moment chart:** create a `prashna_charts` row (the schema exists: question_text,
   question_class, prashna_lagna_method, question_instant, question_lat/lon, querent_natal_chart_id, etc.) and
   cast a chart for that instant+place via the SAME ephemeris/PyJHora path the natal pipeline uses.
5. **RUN the L1 writers for the Prashna chart** so its deterministic facts (positions/vargas/etc.) populate, THEN
   `ga_prashna` computes the horary judgment (querent/quesited significators, Ithasala/Eesarpha, fructification
   timing) reading bg_prashna_rules. STORE (delete-then-insert idempotency per chart_id).
6. Endpoint-verify: ga_prashna now produces NON-zero rows for a cast Prashna chart (it stops being dormant);
   prashna outputs stay in their OWN namespace (never written into the native's natal fact stream).

## PHASE 2 — MULTI-CHART coupling (the "any querent" part — GATE, do not force)
Full horary (ANY querent, ANY subject) requires casting a question-chart for an ARBITRARY querent — which needs
the pipeline to handle a NON-native chart_id cleanly. The instrument is currently single-native (482012f1).
- **DESIGN it now** (document what Prashna needs from multi-chart: per-chart isolation, querent identity, a
  Prashna chart_id distinct from the native), but **DO NOT claim full activation until the multi-chart platform
  is present** ([[project-multichart-platform-rebuild]]). If Phase 1 reveals the casting path hard-codes the
  native chart_id anywhere → that's the multi-chart coupling; flag it, build Phase 1 against a single querent,
  and gate the arbitrary-querent generalization on multi-chart.
- HALT-and-flag if completing "any querent" would require the multi-chart rebuild — that's a separate, larger
  workstream, not this brief.

## PHASE 3 — L2-L5 Prashna contribution (DESIGN now, BUILD later)
- L2: a SEPARATE bodha-style synthesis scoped to the Prashna chart (NEVER the natal bo_* path). Design the
  scoping; build when natal L2 exists to reuse the machinery.
- L3: Prashna fructification timing — design; build with L3 Kāla.
- L4: the standalone Prashna ANSWER (yes/no + when + significators) surfaced to the user — design; build with L4.
- L5: outcome-capture — DEFERRED per native decision (no hook reserved now).
Write a short `PRASHNA_LAYER_CONTRIBUTION_DESIGN.md` capturing the L2-L5 design so the later builds inherit it.

---

## DELIVERABLE + VERIFY
- Phase 0 (ga_positions bug) FIXED + verified.
- Phase 1 (single-querent L1 Prashna path) BUILT: explicit-invoke → validate → collect → cast → compute → store;
  ga_prashna produces non-zero rows for a test Prashna chart; namespace-isolated from natal; endpoint-verified.
- Phase 2 multi-chart coupling DESIGNED + the arbitrary-querent part GATED on multi-chart (flagged, not forced).
- Phase 3 L2-L5 contribution DESIGNED (the design doc), not built.
- Migrations ledger-reconciled; FROZEN contract untouched (HALT if it would change); CI green; endpoint-verify.
Report back: the ga_positions fix confirmation, a test Prashna chart cast end-to-end (the row counts ga_prashna
produced + the judgment it computed), the validation-gate behavior (accepts a real question, rejects a lookup),
and the explicit flag on what part is gated behind multi-chart.

**NOTE:** Prashna does NOT gate L2 Bodha (natal). This can run as its own workstream, parallel to or after the
natal L2 work, since it's namespace-isolated.
