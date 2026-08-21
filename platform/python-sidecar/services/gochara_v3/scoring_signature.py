"""Scoring-mechanism signature for gochara_v3 — PARIŚEṢA F-52 (unblocks F-21).

THE DEFECT THIS CLOSES
----------------------
`ka_gochara_v3_century_materialize.compute_substep_fingerprint` decides whether
an authorized rebuild may be skipped as a no-op. Before this module, its hashed
payload covered:

    (event_class, era_slice_key, ENGINE_VERSION, resonance_targets,
     STAGING_ROW_SCHEMA_COLUMNS, ROW_SCHEMA_COLUMNS)

PARIṢKĀRA MR-38 added the last two — the writer's column LISTS, parsed live out
of the INSERT templates — and its own SCOPE note stated the remaining gap in
plain language:

    "the row_schema_* fold covers ROW SHAPE (which columns exist) only. It does
     NOT cover VALUE-COMPUTATION changes … those remain covered ONLY by the
     ENGINE_VERSION standing rule."

PARIŚEṢA F-52/F-21 is that exact gap, realised in production. `w23_tara_bala`
(W2.3) and `w30_nodal_drishti` (W3.0 — the later-tradition Rahu/Ketu 5/7/9
special-aspect compensator, enabled by default) were both wired into
`engine.py`'s production lambda_v3 product:

    raw_lambda = promise * permission * activity * tara_modifier
                 * w30_modifier * quality_gates

That change moves the VALUE of `lambda_v3` and rewrites the `term_breakdown`
`formula` string, but it adds, removes and renames NO column — so MR-38's fold
sees nothing, `ENGINE_VERSION` was not bumped for it, every stored fingerprint
still matched, the delta-skip fired, and already-materialised windows stayed
frozen at their pre-mechanism values. The served evidence confirms it: every
window's `term_breakdown` on the canonical chart carries the OLD formula string
and zero occurrences of `tara_modifier` / `w30_modifier`.

This is a §N.8 Earned-Signal defect. "fingerprint unchanged → skip" asserts
*nothing that affects this window's score has changed*, but the detector behind
it only ever measured inputs and column lists — never the set of scoring
mechanisms actually multiplied into the score.

THE FIX
-------
`scoring_signature()` derives, LIVE from the engine module itself, a
machine-comparable statement of the production scoring mechanism set:

  * `lambda_formula` / `term_breakdown_formula` — the engine's own canonical
    formula constants (`engine.LAMBDA_V3_FORMULA`,
    `engine.TERM_BREAKDOWN_FORMULA`), i.e. the very strings emitted onto served
    rows. Adding or removing a factor from the product changes these.
  * one entry per mechanism module the engine actually imports, discovered by
    walking the engine module's namespace for objects living under
    `services.gochara_v3.mechanisms.*` — never a hand-maintained list in the
    writer that could drift from what the engine really calls. Each entry
    carries:
      - `mechanism_id`   — the module's declared MECHANISM_ID.
      - `enabled`        — the engine's own toggle for that mechanism,
                           resolved by the engine's naming convention
                           `_{MECHANISM_ID.upper()}_ENABLED`
                           (`w30_nodal_drishti` → `_W30_NODAL_DRISHTI_ENABLED`).
                           `None` when no such flag exists (itself a distinct,
                           signature-changing state — never silently "True").
      - `compute_digest` — a digest of `inspect.getsource(module.compute)`,
                           the actual executed scoring body.

`scoring_signature_digest()` is the stable MD5 of that structure, folded by
`compute_substep_fingerprint` into every substep's fingerprint.

WHAT THIS DOES AND DOES NOT CATCH (honest scope)
------------------------------------------------
CATCHES, with no human remembering to bump anything:
  * a mechanism added to (or removed from) the engine's production path — the
    literal F-52/F-21 scenario;
  * a mechanism's default toggle flipped on or off;
  * a factor added to or removed from the lambda_v3 / term_breakdown formula;
  * an edit to a mechanism's own `compute()` body (a modifier schedule
    changing 0.70 → 0.65, an aspect offset corrected, an honest-skip branch
    added).

DOES NOT CATCH:
  * a value-computation change in `engine.py` OUTSIDE any mechanism's
    `compute()` and outside the formula constants (e.g. re-tuning
    `_ACTIVITY_MAX_ORB_DEG`, or rewriting `_compute_activity_v3`'s internals).
    The `ENGINE_VERSION` standing rule remains load-bearing for that class of
    change. F-52 narrows that rule's surface substantially; it does not
    eliminate it, and claiming otherwise would be exactly the overstatement
    PARĪKṢAKA F-3 corrected in MR-38.
  * a mechanism whose behaviour is driven by data outside its source (a YAML
    weight file, a DB-resident schedule). Those need their own fold.

DELIBERATE OVER-INVALIDATION: a docstring-only edit inside a `compute()` body
changes the digest and forces a recompute. That is the safe direction — an
unnecessary rebuild costs time; a silently-skipped one serves a stale classical
judgment as current, which is the defect F-52 exists to close.

REBUILD REQUIREMENT: this module changes the fingerprint every subsequent build
computes. It does not, and cannot, alter rows already sitting in
`kala_gochara_windows` / `kala_gochara_windows_v2`. Already-materialised windows
carry their stale pre-mechanism scores until `ka_gochara_v3_century_materialize`
is re-run for the affected charts — at which point the delta-skip correctly
declines to fire and the windows are re-scored.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import types
from typing import Any

# The package prefix every gochara_v3 scoring mechanism module lives under.
MECHANISM_PACKAGE_PREFIX = "services.gochara_v3.mechanisms."

# The engine's convention for a mechanism's production toggle flag:
#   MECHANISM_ID 'w30_nodal_drishti' -> '_W30_NODAL_DRISHTI_ENABLED'
_TOGGLE_FLAG_TEMPLATE = "_{}_ENABLED"

# Sentinel recorded when a discovered mechanism module exposes no `compute`
# callable to digest. Distinct from any real digest, so its appearance or
# disappearance is itself a signature change.
_NO_COMPUTE = "no-compute-callable"


def toggle_flag_name(mechanism_id: str) -> str:
    """Return the engine-module flag name that toggles ``mechanism_id``.

    Pure naming convention, stated once here so the engine and this module
    cannot disagree about it.
    """
    return _TOGGLE_FLAG_TEMPLATE.format(mechanism_id.upper())


def _source_digest(fn: Any) -> str:
    """Digest the source text of ``fn``.

    Returns a sentinel (never a fabricated-clean value) when the source cannot
    be read — e.g. a C extension or a dynamically-constructed callable. An
    unreadable source is recorded honestly as unreadable, so the state is
    visible in the signature rather than masquerading as a stable digest.
    """
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        return "source-unavailable"
    return hashlib.md5(src.encode("utf-8")).hexdigest()


def discover_engine_mechanisms(engine_module: types.ModuleType | None = None) -> list[dict[str, Any]]:
    """Discover the scoring mechanisms the gochara_v3 engine actually imports.

    Walks ``engine_module``'s namespace (default: ``services.gochara_v3.engine``)
    for module objects whose ``__name__`` starts with
    ``services.gochara_v3.mechanisms.``. This is the fold's whole point: the set
    is read off the engine that does the scoring, so a mechanism wired into the
    engine cannot fail to appear here, and one never wired in cannot appear.

    Returns a list of dicts sorted by ``mechanism_id``.
    """
    if engine_module is None:
        from services.gochara_v3 import engine as engine_module  # local: avoid import cycle

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    for value in vars(engine_module).values():
        if not isinstance(value, types.ModuleType):
            continue
        mod_name = getattr(value, "__name__", "")
        if not mod_name.startswith(MECHANISM_PACKAGE_PREFIX):
            continue

        mechanism_id = getattr(value, "MECHANISM_ID", None) or mod_name.rsplit(".", 1)[-1]
        if mechanism_id in seen:
            continue
        seen.add(mechanism_id)

        flag_name = toggle_flag_name(mechanism_id)
        # `None` when the engine declares no flag for this mechanism — an
        # honest "no toggle found", never an assumed-True default (§N.7 item 6).
        enabled = getattr(engine_module, flag_name, None)

        compute_fn = getattr(value, "compute", None)
        compute_digest = _source_digest(compute_fn) if callable(compute_fn) else _NO_COMPUTE

        entries.append(
            {
                "mechanism_id": mechanism_id,
                "module": mod_name,
                "toggle_flag": flag_name,
                "enabled": enabled,
                "compute_digest": compute_digest,
            }
        )

    entries.sort(key=lambda e: e["mechanism_id"])
    return entries


def scoring_signature(engine_module: types.ModuleType | None = None) -> dict[str, Any]:
    """Return the live scoring-mechanism signature for the gochara_v3 engine.

    The returned structure is stable across unrelated refactors and changes
    exactly when the production scoring mechanism set, its toggles, its
    ``compute()`` bodies, or the lambda_v3 formula strings change.
    """
    if engine_module is None:
        from services.gochara_v3 import engine as engine_module  # local: avoid import cycle

    return {
        "signature_version": 1,
        "lambda_formula": getattr(engine_module, "LAMBDA_V3_FORMULA", None),
        "term_breakdown_formula": getattr(engine_module, "TERM_BREAKDOWN_FORMULA", None),
        "mechanisms": discover_engine_mechanisms(engine_module),
    }


def scoring_signature_digest(engine_module: types.ModuleType | None = None) -> str:
    """32-character MD5 hex digest of :func:`scoring_signature`.

    This is what the century materializer folds into every substep fingerprint.
    """
    payload = json.dumps(scoring_signature(engine_module), sort_keys=True, default=str)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


__all__ = [
    "MECHANISM_PACKAGE_PREFIX",
    "discover_engine_mechanisms",
    "scoring_signature",
    "scoring_signature_digest",
    "toggle_flag_name",
]
