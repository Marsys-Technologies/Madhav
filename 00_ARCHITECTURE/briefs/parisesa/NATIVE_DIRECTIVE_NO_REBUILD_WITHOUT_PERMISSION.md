---
artifact: PARISESA_NATIVE_DIRECTIVE
id: ND-PARISESA-1
issued_by: native (Abhisek Mohanty), via SUTRADHARA conductor, direct chat instruction
issued_at: 2026-08-16 (campaign in-flight)
status: BINDING, supersedes conflicting campaign-default autonomy language
---

# Native directive: no rebuild without explicit permission

**The instruction, verbatim intent:** "Keep running. Don't rebuild without my permission. I would
like to make sure everything is fixed so that the rebuild is correct else the rebuild needs to be
redone."

## Binding rule

Any scoped or full rebuild of chart-derived data (any `build_runs` dispatch, any asset rebuild via
the orchestrator, any action that recomputes and re-persists `chart_facts`/`chart_dashas`/
`chart_divisionals`/`bodha_*`/`kala_*`/`phala_*`/`mimamsa_*` tables for any chart, canonical or
otherwise) requires **explicit native permission relayed through the conductor**, in addition to
(not instead of) any existing PRATINIDHI ruling requirement. This is now a harder gate than the
plan's original "any DB write → PRATINIDHI ruling" standing duty — it is PRATINIDHI ruling **AND**
native permission, always.

**Rationale (native's own framing):** the native wants confirmation that every fix touching a given
set of derived assets is actually landed and correct BEFORE that asset is rebuilt — a rebuild done
too early, before all touching fixes have landed, may need to be redone. Batch the fixes, then
rebuild once, correctly.

## What this means operationally

- **Code merges are NOT gated by this** — INTEGRATOR's normal merge cadence (3-5 VERIFIER-passed
  lanes or every 90 min) continues unchanged. Merging code that WOULD change future rebuild output
  is fine; TRIGGERING an actual data rebuild is what's gated.
- **F-62's in-flight rebuild** (chart 482012f1, ga_structural/ga_vargas/bo_pratijna scoped rebuild,
  dispatched by INTEGRATOR before this directive arrived): STOP if not yet committed; if already
  committed, do not undo, just report state honestly and hold further verification-rebuild work.
- **Live-probe evidence for any lane whose fix requires a rebuild to manifest** stays PENDING —
  honestly reported as such, not skipped or faked — until native permission is given and the
  rebuild actually runs.
- **Streams should keep identifying which findings share rebuild scope** (e.g. multiple findings
  all touching `ga_structural_writer.py`/`ga_vargas_writer.py`/L1 assets) so that when permission IS
  granted, one batched rebuild covers everything rather than several redundant ones.
- Conductor (SŪTRADHĀRA) is the sole channel for relaying this permission when granted — no stream,
  VERIFIER, or INTEGRATOR requests it directly from the native; all such needs route through the
  conductor first.

## Streams affected

Any lane whose remediation is a writer/data-layer fix (as opposed to a pure serving-layer fix) is
implicated: at minimum F-62 (S6), and potentially any other L1/L2/L3 writer-layer finding across
S2-S6 once their fixes land. Streams should flag in their own ledgers which of their lanes will need
a rebuild to verify live, so the eventual batched-permission request is complete.
