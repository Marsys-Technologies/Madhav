---
artifact: CLAUDECODE_BRIEF_GA_NAKSHATRA_WRITER_v1_0.md
canonical_id: GA_NAKSHATRA_WRITER_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10
authored_for: Claude Code in Antigravity IDE (autonomous, orchestrator-native)
campaign: Nakshatra Subsystem — Tier 1, Phase 2 (the per-chart parallel nakshatra chart)
delivery_model: 1 branch, plan-then-execute, no human gate
design_source: 00_ARCHITECTURE/NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md (§3 + §7.1 all decisions LOCKED)
depends_on: bg_nakshatra (Phase 1 — MUST land first), ga_positions, ga_vargas (D150 reference)
---

# ga_nakshatra — L1 Per-Chart Parallel Nakshatra Chart — Execution Brief v1.0

## §0 — Read first + locked decisions

Read `NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md` §3 (full L1 scope) + §7.1 (all 8 decisions RESOLVED).
Key locked: storage = **chart_facts** (separate asset, watch row-count); KP = sub+sub-sub+prana per-body
AND per-cusp; D150 already in ga_vargas — REFERENCE it, don't recompute; reopen L1 additively.

## §1 — What this is

`ga_nakshatra` is a NEW L1 per-chart asset: the per-chart **parallel nakshatra chart** computed by PyJHora.
Per ayanamsha (×5), per body (9 grahas + Lagna + nodes + key sensitive points). It JOINS bg_nakshatra's
static attrs (the AUTHORITY — reference, never restate) and computes everything chart-specific. This is the
depth L1 lacked. Target: **`chart_facts`**.

## §2 — Reality reconciliation

- Engine = PyJHora (`pyjhora_adapter`). No JH-parity oracle (internal-consistency + classical re-derivation).
- Orchestrator-native: `@register('ga_nakshatra') class NakshatraWriter(WriterBase)` conforming to the FROZEN
  contract (run on `ctx.db_conn`, never commit; per-ayanamsha sub-steps if heavy — see §9 row-count). L1
  delete-then-insert idempotency via `_idempotency.py` (scoped per chart × ayanamsha × the nakshatra
  fact_categories). Build-state via the orchestrator (no `_telemetry`).
- chart_id + birth_params from `ctx.config`. Canonical native = `482012f1-…`; `362f9f17` is dead phantom.
- `depends_on: ['bg_nakshatra', 'ga_positions']` (+ reads ga_vargas D150). Surgical migration.

## §3 — Placement + attribute join (master §3.1)

Per body, per ayanamsha: nakshatra (name+number), pada (1–4), exact degree-within-nakshatra, % traversed.
**JOIN bg_nakshatra onto each body** — emit per-body fact rows that REFERENCE the bg_nakshatra row for
gana/nadi/yoni+sex/varna/tatva/pakshi/deity/shakti/pada_navamsa/akshara (cite the bg_nakshatra source; do
NOT restate the static value as ga_nakshatra's own truth — L0-is-authority-for-static). nakshatra_lord +
the lord's own placement (its dignity/house from ga_positions — the "nakshatra-lord condition").

## §4 — The PARALLEL NAKSHATRA CHART (master §3.2 — the headline)

Compute the nakshatra-space chart, distinct from the rashi chart:
- **Nakshatra dispositor graph:** each body's nakshatra-lord → that lord's nakshatra-lord → terminus/cycle.
  Emit each edge + each chain + `cycle_detected_at_step_N`.
- **Nakshatra exchange (parivartana):** two bodies in each other's nakshatra-lord's nakshatras.
- **Nakshatra conjunction:** bodies sharing a nakshatra (distinct from sign-conjunction).
- **Nakshatra center-of-gravity:** the body the most nakshatra-chains terminate on (the nakshatra-chart's
  functional king). This is the parallel-witness seed L2 uses against the rashi graph.

## §5 — Sub-nakshatra precision (master §3.3)
- **KP 249: star-lord → sub-lord → sub-sub-lord → prana** per body AND per house cusp (decision §7.1.4) —
  the full KP significator backbone. From exact longitude × Vimshottari-proportional subdivision.
- **Nadiamsa D150 attribution:** ga_vargas/chart_divisionals ALREADY holds each body's D150 SIGN (decision
  §7.1.8). **VERIFY what D150 detail ga_vargas emits, then add ONLY the nakshatra-level Nadiamsa ATTRIBUTION
  (lord/deity/rishi per the 150-fold subdivision) on top, CITING the ga_vargas D150 row.** Do not recompute
  the D150 position.

## §6 — Degree-sensitive flags WITH SEVERITY (master §3.4 — gradients, not booleans)
Per body: gaṇḍānta flag + exact arc-minutes from junction (severity gradient); mṛtyu-bhāga proximity;
abhukta-mūla; rashi-/nakshatra-/pada-sandhi with distance; pushkara navamsa/bhaga (cross-link ga_vargas/GA6,
don't duplicate); deep-exaltation nakshatra-pada; vargottama-via-pada (pada navamsa == D1 sign).

## §7 — Tara / cycle positions (master §3.5)
**Full per-chart Tara matrix** — each body's nakshatra's tara from EVERY other body (extend GA4's transit-
Moon 27-row baseline; cross-reference don't duplicate). Position in each bg_nakshatra cycle def (Yogini-
from-nak, Nadi-cycle, sub-taras). Sarvatobhadra-chakra occupancy per body (chakra def from bg_nakshatra;
occupancy per-chart).

## §8 — Chart-level nakshatra STATISTICS (master §3.6 — within-chart deterministic; feeds L2)
Per chart/ayanamsha: gana distribution across all bodies; nadi balance; yoni distribution; **tatva balance
(elemental nakshatra signature)**; gana/nadi/yoni concentration scores; **cross-ayanamsha nakshatra
consistency per body** (does each body's nakshatra hold 5/5 or flip — the L2-philosophy robustness signal).
These are the nakshatra ingredients L2 MSR turns into signals.

## §9 — Storage + row-count watch (decision §7.1.3)
Target `chart_facts` (nakshatra fact_categories). **MEASURE the total rows at build** — KP-249
(sub+sub-sub+prana) × bodies × cusps × 5 ayanamshas is potentially the largest single chart_facts
contributor. If it's very large (degrading chart_facts query perf), REPORT to native (revisit, not silent).
Use sub-steps (per-ayanamsha) if the writer is heavy. count_sql = chart_facts WHERE chart_id=$1 AND
fact_category IN (the nakshatra categories); target_floor = achieved count.

## §10 — FORENSIC + verification
- FORENSIC: native Moon nakshatra = **Purva Bhadrapada** (lord Jupiter, deity Aja Ekapad) — assert. Lagna
  nakshatra + per-body nakshatras internally consistent with ga_positions (same nakshatra a body has in
  ga_positions). Halt on mismatch.
- Two-pass per row. The attribute-join is verified by resolving to the bg_nakshatra row (FK integrity); the
  KP-249 by independent re-derivation; the dispositor graph by cycle-detection re-walk.

## §11 — Acceptance (all `[verify-against: prod]`)
1. bg_nakshatra present (Phase 1 landed) — halt-clean if absent.
2. Per-body placement + attribute-join emitted ×5 ay; joins RESOLVE to bg_nakshatra rows (FK integrity).
3. Parallel nakshatra chart: dispositor graph + exchanges + conjunctions + center-of-gravity computed.
4. KP-249 (sub/sub-sub/prana) per body + per cusp present; D150 attribution references ga_vargas (no recompute).
5. Severity-gradient flags (gaṇḍānta arc-minutes etc.); per-chart statistics computed.
6. FORENSIC: Moon=Purva Bhadrapada; per-body nakshatras == ga_positions. Two-pass clean.
7. Row-count measured + reported (chart_facts perf healthy, or flagged).
8. Orchestrator-native: `get_writer('ga_nakshatra')` resolves; builds via `POST /api/cockpit/runs`; lit via
   orchestrator (not _telemetry); cockpit tile + bar fill; idempotent double-run = one set.
9. CI green; merge-verify.

## §12 — Rails
PyJHora + chart_facts + orchestrator-native (frozen contract); L1 delete-then-insert idempotency; no
JH-parity; no tier; floors aspirational; two-pass; FORENSIC-gated; surgical migration; only `482012f1`;
**bg_nakshatra is authority for static attrs (reference, never restate); ga_vargas is authority for D150
(reference, never recompute)**; build via orchestrator NOT hand-run. Halt on: bg_nakshatra absent, FORENSIC
miss, ga_positions inconsistency, or chart_facts row-count blowup needing native review.

---

*End. ga_nakshatra: the per-chart parallel nakshatra chart — placement+join, the nakshatra dispositor graph
(parallel witness), KP-249, D150 attribution, severity-gradient flags, and within-chart nakshatra statistics —
into chart_facts, orchestrator-native, FORENSIC-gated. The L1 foundation L2 Bodha's nakshatra signals build on.*
