---
artifact: STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md
brief_id: STREAM_F_SCOPING
version: 1.0
status: SUPERSEDED — DO NOT EXECUTE
superseded_by: CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md
superseded_reason: >
  This brief assumed forensic_writer produces structured chart_facts rows. That was wrong.
  The schema (migration 131 chart_documents + EXPECTED_ROW_COUNTS pratyaksha→chart_facts
  already seeded) shows forensic_render is a markdown DOCUMENT renderer, and the render
  infrastructure (ForensicRenderer + 13 section renderers + linter) already exists. Use the
  executable brief, not this one.
authored_at: 2026-06-01
authored_by: cowork-planner
follows: CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md (PR #184 — engine swap, merged)
why: >
  PR #184 swapped the engine to PyJHora and was reported as closing the forensic stub.
  It did not. forensic_writer.py on main is still an explicit 0-row stub whose own header
  says "Real implementation: Stream F sessions F-01 through F-14." This brief scopes that
  still-open primary target. It is a SCOPING brief, not a ready-to-run executor brief,
  because the F-01..F-14 decomposition does not yet exist as a spec.
prime_directive: only computed facts. no narrative, no opinion, no judgement.
hard_bans:
  - No Anthropic models (native standing order)
  - No JH-parity oracle. Internal-consistency verification only ([[no-jh-parity-anywhere]])
---

# Stream F — forensic render writer (scoping)

## 1 · The gap, stated plainly

`platform/python-sidecar/pipeline/writers/forensic_writer.py` (asset
`A2_forensic_render`, label "FORENSIC.md Render") is a stub:

```python
def write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra=None) -> int:
    logger.info("[STUB] ...")
    return 0   # writes no data
```

It emits a build event and returns `rows_written = 0`. The production native build
(2026-06-01) confirmed: every other writer populated `chart_facts`, but the forensic
asset is empty. The implementation brief named this writer the arc's **primary target**
and AC6 promised it "no longer returns the 0-row stub." That promise is unmet — it was
satisfied only at the panchanga spot-check level, not for the forensic asset itself.

This is **not a regression** (the stub predates PR #184) and **not a blocker** for the
v1.3 partition unblock (those rows come from the other writers). It is the arc's
remaining real work.

## 2 · What "forensic render" must produce — open question for the native

Before a single executor session opens, three things need a decision. The render writer
turns the per-build `chart_output` into FORENSIC-schema rows in `chart_facts`. The
canonical reference for what those facts are is
`01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (canonical_id FORENSIC). But:

- **Q1 — target shape.** Does `A2_forensic_render` write structured `chart_facts` rows
  (one row per forensic datum, queryable), or does it render a FORENSIC-schema **markdown
  document** as a provenance artifact (closer to the deferred F1 "JSONL → FORENSIC-schema
  markdown renderer" from the implementation brief's follow-ups)? The asset label says
  "FORENSIC.md Render" — implying a document — but the data plane is `chart_facts` rows.
  These are different deliverables. **The implementation brief explicitly deferred the
  markdown renderer (F1) and said "chart_facts DB rows are the source of truth."** So the
  most consistent reading is: A2 writes structured forensic rows, and the markdown render
  is a separate later projection. Native confirms.
- **Q2 — does FORENSIC v8.0 become a comparison oracle?** It must not, per
  `[[no-jh-parity-anywhere]]` and handoff §4.2 ("never against FORENSIC v8.0 as a parity
  oracle"). The render writer **derives** forensic facts from the live PyJHora
  `chart_output`; it does not copy or diff against v8.0. v8.0 is the *schema* reference
  (which fields exist), not the *value* reference. The native chart will, by construction,
  reproduce v8.0's values because both come from the same birth event — but the test
  asserts internal structure, not equality to v8.0.
- **Q3 — is the F-01..F-14 decomposition real?** The stub header asserts 14 sessions but
  no F-session spec exists in `00_ARCHITECTURE/`. Either it was aspirational shorthand or
  a plan that was never written. This brief proposes a decomposition in §4; native
  confirms or replaces it.

## 3 · Verification contract (unchanged from the project standard)

Internal consistency only. For the forensic render: row counts vs
`00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml` (a forensic row count must be added
there), schema compliance, structural invariants (every forensic fact resolves to an L1
graha/bhava/varga that exists in the same build), cross-asset FK integrity (forensic rows
reference the same `chart_id`/`build_id`/`ayanamsha_id` as their source L1 rows),
determinism (rebuild = byte-identical forensic payload). **No category 7. No FORENSIC v8.0
value-diff.**

## 4 · Proposed F-01..F-14 decomposition (native confirms before execution)

A working decomposition, grouped so each session is one PR-sized unit with its own
internal-consistency test. Adjust counts as the native sees fit.

| Session | Scope | Internal-consistency test |
|---|---|---|
| F-01 | Forensic row schema + `EXPECTED_ROW_COUNTS.yaml` entry + writer skeleton (replaces stub `return 0` with real upsert path, still gated to one section) | writer emits >0 rows for one section; schema NOT NULL/FK pass |
| F-02 | Lagna + bhava section (ascendant, 12 bhava madhyas, bhava lords) | Lagna ↔ house-1 sign consistency invariant |
| F-03 | Graha section (9 grahas: sign, house, nakshatra, pada, dignity, retro, combust) | each graha resolves to a positions-writer row in the same build |
| F-04 | Rahu/Ketu + upagraha section | Rahu ↔ Ketu 180° invariant |
| F-05 | Varga section (D1..D60 placements per the 16-varga set) | each varga placement consistent with D1 sign arithmetic |
| F-06 | Dignity + avastha + bala summary | dignity values ∈ enum; bala columns sum within rounding |
| F-07 | Dasha section (Vimshottari balance + mahadasha sequence) | mahadashas sum to 120 years |
| F-08 | Jaimini / Chara dasha + karakas | karaka assignment is a permutation of grahas |
| F-09 | Panchanga + sensitive points (tithi/vara/nakshatra/yoga/karana + Gulika/Mandi/Arudha) | all angas non-empty; matches the A2-panchanga writer rows |
| F-10 | Yoga detection section (classical yogas present) | each yoga's constituent grahas/bhavas exist in this build |
| F-11 | Cross-section reconciliation row (forensic ↔ L1 writer agreement audit) | forensic facts ⊆ L1 facts for the build |
| F-12 | Multi-ayanamsha coverage — render for all 5 ayanamshas via `per_ayanamsha` | 5 ayanamsha sets present; deltas arithmetic-only |
| F-13 | Determinism + idempotency hardening (rebuild = identical md5; idempotency guard checks the forensic write target) | rebuild byte-identical; re-run inserts 0 duplicate rows |
| F-14 | Pariksha integration: register forensic asset with Pramana's row-count + structural-invariant battery + EXPECTED_ROW_COUNTS finalised | Pramana run on native chart shows forensic GREEN |

These can collapse into fewer sessions if the native prefers a smaller arc. The grouping
is by structural-invariant boundary, so each session is independently verifiable.

## 5 · Suggested execution shape

One branch `feature/stream-f-forensic-render`, one worktree
(`/Users/Dev/Vibe-Coding/Apps/MadhavStreamF`), Conductor-driven if the native wants the
14 sessions autonomous (the queue pattern already exists under
`00_ARCHITECTURE/CONDUCTOR/`). `may_touch`: `forensic_writer.py`, a new
`forensic_render/` helper module under `pyjhora_adapter/` if the derivation needs its own
home, `tests/test_pyjhora_adapter/test_forensic_render.py`,
`00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml`. `must_not_touch`: migrations,
frontend, the other writers (read-only from their `chart_facts` rows).

## 6 · Out of scope

- The FORENSIC-schema **markdown** renderer (implementation-brief F1) — separate projection.
- Any FORENSIC v8.0 value-parity gate — banned.
- Schema migrations beyond `chart_facts` rows (the table already exists).

## 7 · Decision needed from the native before this becomes an executor brief

1. Q1 — structured rows vs markdown render (recommend: structured rows; markdown is F1).
2. Q3 — confirm/replace the 14-session decomposition in §4.
3. Conductor-autonomous or single hand-driven arc.

Once those are answered, I convert this into a `CLAUDECODE_BRIEF_*` with frontmatter
`may_touch`/`must_not_touch`/`hard_bans` and a per-session queue, paste-ready for
Antigravity.

---

*End of STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md*
