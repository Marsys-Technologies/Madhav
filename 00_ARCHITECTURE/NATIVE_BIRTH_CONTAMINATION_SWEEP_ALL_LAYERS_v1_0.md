---
artifact: NATIVE_BIRTH_CONTAMINATION_SWEEP_ALL_LAYERS_v1_0.md
canonical_id: NATIVE_BIRTH_CONTAMINATION_SWEEP_ALL_LAYERS
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-26
severity: HIGH — the gate that earns "code is correct, regenerate once"
purpose: >
  Exhaustive audit of the NATIVE_BIRTH / hardcoded-native chart-identity contamination class across
  ALL layers L0–L5 + shared compute, not just L0/L1. Classify every source file that can compute a
  chart from native defaults; fix every vulnerable one; add a structural guard so the class cannot
  recur. This must PASS before the regenerate-everything (all layers, all charts) run.
audience: Claude Code (Antigravity)
related: feedback-sync-freeze-before-data-generation, project-ak-divergence-and-positions-contamination
---

# NATIVE_BIRTH contamination sweep — ALL LAYERS

## §0 — The bug class (what we are hunting)
The pattern that wrote the native's positions into a non-native chart:
- `bp = birth_params or NATIVE_BIRTH` (silent native fallback when params are missing/empty), and/or
- a function signature defaulting `chart_id: str = CANONICAL_CHART_ID` (a missing chart_id silently
  builds the native), and/or
- a hardcoded `NATIVE_BIRTH` / `1984-02-05` / `NATIVE_CHART_ID` used as a runtime computation input for
  any chart other than the native.
Confirmed instances already fixed: ga_positions (731661e0), ga_sensitive writer (B5). Confirmed
present elsewhere: l4_anchors.py (native-hardcoded module; C2-002 LEL leak just fixed). The fact that
it recurred in L1→L4 means we must assume it lurks in any layer until each is audited.

DOCTRINE (the correct pattern, from the ga_positions fix): explicit birth_params always win; a
hardcoded native default is permitted ONLY when `chart_id == CANONICAL_CHART_ID`; a non-native chart
with no birth_params is a LOUD HALT (raise), never a silent native build. The orchestrator already
fetches per-chart params via `pipeline/orchestrator/birth_params.py fetch_birth_params` (returns None
only for the native) — writers must consume that, not a constant.

## §1 — SCOPE: the actual source files to audit (grep-confirmed, all layers, tests excluded)
Audit EACH of these (the live grep hit ~45 non-test source files). Group by layer:

**L0 (Brahmagyan):** brahmagyan/l0_ephemeris.py, brahmagyan/ephemeris_routes.py,
brahmagyan/ganita/engine.py, build_ephemeris_1900_2150.py.
**Shared compute (used by all layers):** pyjhora_adapter/compute.py, pipeline/writers/panchanga_writer.py,
routers/pyhora.py, pipeline/orchestrator/birth_params.py (the helper — verify it's correct, it's the
fix everyone should use).
**L1 (Gaṇita):** ga_writers/*.py — ga_positions_writer, ga_sensitive_writer (both fixed — confirm),
ga_dashas_writer, ga_strength_writer, ga_structural_writer, ga_vargas_writer, ga_panchanga_writer,
ga_nakshatra (writer + orchestrator adapter), ga_condition_writer, ga_sade_sati_writer,
ga_tajaka_writer, ga_medical_writer, ga_vastu_writer, ga_yoga_writer, ga_prashna_cast,
ga_transit_anchors, build_runner.py; + orchestrator adapters pipeline/orchestrator/writers/ga_*.py.
**L2 (Bodha):** brahmagyan/bodha/bo22.py (+ any other bodha writer hitting the pattern).
**L3 (Kāla):** services/ka_dasha_kala/writer.py, services/ka_muhurta_seva/writer.py + service.py,
pipeline/orchestrator/writers/ka_graha_sancara.py, ka_dasha_kala, and any ka_* writer.
**L4 (Phala):** brahmagyan/phala/l4_anchors.py, rectification.py, l4_rectification.py, outlook.py,
muhurta.py, mitigation.py; services/ph_rectification/engine.py;
pipeline/orchestrator/writers/ph_rectification/.
**L5 (Mīmāṃsā):** brahmagyan/mimamsa/concordance_writer.py (+ any mi_* writer).

(Re-run the grep at execution to catch any file added since: 
`grep -rlE "NATIVE_BIRTH|birth_params or |CANONICAL_CHART_ID|NATIVE_CHART_ID|1984-02-05" platform/python-sidecar --include=*.py | grep -vE "venv|__pycache__|/tests?/|/test_|_test"`)

## §2 — Per-file classification (the audit)
For EACH source file, determine and record ONE classification:
1. **CHART-INDEPENDENT** — does not compute a per-chart result from birth params (e.g. l0_ephemeris is
   a date-range ephemeris, not a birth chart; reference-data writers). The NATIVE_BIRTH/date hit is
   incidental (a comment, a test anchor, an unrelated constant). → SAFE, note why.
2. **NATIVE-ONLY-BY-DESIGN** — a module that legitimately only ever runs for the native (e.g.
   l4_anchors.py is a hardcoded native fixture). → SAFE for contamination (can't leak to others) BUT
   flag it as a [[de-native candidate]] for the parked architecture work, and ensure it can NEVER be
   invoked for a non-native chart_id (add a guard/assert if it takes chart_id).
3. **CORRECTLY-GUARDED** — already consumes per-chart birth_params and refuses native fallback for
   non-native (like the fixed ga_positions/ga_sensitive). → SAFE, confirm the guard text.
4. **VULNERABLE** — can run for a non-native chart AND can fall back to NATIVE_BIRTH / native default /
   hardcoded birth. → MUST FIX (§3). This is the contamination bug.
The deciding question for each: "If the orchestrator dispatched this for a NON-native chart with
birth_params unset/empty, would it compute the NATIVE's chart?" If yes → VULNERABLE.

## §3 — FIX every VULNERABLE file (uniform doctrine)
Apply the same 3-way guard the ga_positions fix used:
```
if birth_params is None:                 # (or: not birth_params, if empty-dict is also wrong)
    if chart_id == CANONICAL_CHART_ID:
        birth_params = NATIVE_BIRTH
    else:
        raise <Error>(f"non-native chart {chart_id} has no birth_params — refusing NATIVE_BIRTH fallback")
```
- Remove any `chart_id: str = CANONICAL_CHART_ID` default → make chart_id REQUIRED.
- Ensure the writer/adapter actually RECEIVES per-chart params: the orchestrator adapter must pass
  `birth_params=ctx.config.get('birth_params')` (the ga_positions adapter bug). Check each orchestrator
  writer adapter passes it (ga_sensitive/strength/structural/vargas/tajaka/nakshatra already do; verify
  the rest — ka_*, ph_*, bo_*, mi_*).
- Decide the `None` vs `{}` semantics consistently: B1 showed the native passed `{}` not `None` and
  slipped a guard. Guard on "no usable birth params" (None OR empty), not strict `is None`, where a
  non-native could otherwise sneak through.
- Per fix: a regression test — non-native chart_id + no birth_params ⇒ RAISES (never silently builds
  native); native chart_id + no params ⇒ uses NATIVE_BIRTH; non-native + real params ⇒ uses them and
  produces output DIFFERENT from the native.

## §4 — STRUCTURAL guard (make the class non-recurrable)
Beyond per-file fixes, add ONE shared mechanism so a future writer can't reintroduce this:
- Preferred: a single `resolve_birth_params(chart_id, birth_params)` helper (extend
  `pipeline/orchestrator/birth_params.py`) that encapsulates the 3-way guard, and make every writer
  call it instead of touching NATIVE_BIRTH directly. Then `NATIVE_BIRTH` has exactly ONE legitimate
  reference site.
- Add a CI/lint check (or a unit test that greps the writer tree) that FAILS if any writer references
  `NATIVE_BIRTH` / `CANONICAL_CHART_ID` as a birth-param default outside the one helper. This is the
  guard that means we never have to run this sweep again.

## §5 — Deliverables + gate
DELIVER: a per-file classification table (file → layer → CHART-INDEPENDENT / NATIVE-ONLY-BY-DESIGN /
CORRECTLY-GUARDED / VULNERABLE → evidence); the fixes for every VULNERABLE file (diff + regression
test); the structural guard (helper + the CI/grep test); and a final assertion that ZERO writer can
compute the native for a non-native chart_id. Commit(s) on main, green CI, then rebuild the Cloud Run
job image so the sweep fixes are live.
GATE: this sweep PASSING (zero VULNERABLE remaining + structural guard in place + job image carries it)
is the precondition for the regenerate-everything run. Do not generate data until then.

## §6 — Guardrails + notes
- Parked (do NOT do here): the full "remove runtime native concept" refactor — native deferred this.
  This sweep makes the class SAFE (guards + raises) without removing the native concept; the
  de-native-ization is a later architecture decision. Tag NATIVE-ONLY-BY-DESIGN files as de-native
  candidates for that future work, don't refactor them now.
- No data generation in this brief — code + tests + job-image only.
- Read-only audit first (§2 full classification table) → STOP and report the table → then fix (§3–4)
  after the native sees how many VULNERABLE files there are. A surprisingly large VULNERABLE count may
  itself argue for bringing the de-native refactor forward — native's call.
- L0 ephemeris is almost certainly CHART-INDEPENDENT (date-range, not birth) — confirm, don't assume.
- The shared compute layer (pyjhora_adapter/compute.py, panchanga_writer) is the highest-leverage: a
  vulnerability there affects every layer. Audit it first.
