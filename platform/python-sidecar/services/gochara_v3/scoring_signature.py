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
      - `module_source_digest`
                         — a digest of `inspect.getsource(module)`, i.e. the
                           mechanism module's WHOLE source: its `compute()`
                           body AND the module-scope constants that body reads
                           (`ASPECT_OFFSETS`, `ASPECT_MODIFIERS`,
                           `TARA_MODIFIERS`, helper functions …).
      - `compute_digest` — a digest of `inspect.getsource(module.compute)`,
                           the executed scoring entry point. Retained
                           alongside the module digest, not replaced by it:
                           it is the only term that still covers a `compute`
                           bound from some OTHER module (in which case the
                           mechanism module's own source would not contain
                           it), and it keeps the fold sensitive to a
                           `compute` rebound at runtime.

  * `import_scan` — the result of AST-scanning the engine's own source for
    imports under `services.gochara_v3.mechanisms.*`, split into module-style
    and function-style. See "DISCOVERY GUARANTEE" below.

THE MODULE-DIGEST CORRECTION (GA-5 adversarial review of the first F-52 PR)
--------------------------------------------------------------------------
The first cut of this module digested `inspect.getsource(module.compute)` and
nothing else, while this docstring claimed it caught "a modifier schedule
changing 0.70 → 0.65, an aspect offset corrected". Both named examples were
FALSE for the two mechanisms actually wired into the engine, because both keep
their scoring values at MODULE scope, outside `compute()`:

    w30_nodal_drishti.ASPECT_OFFSETS   = (4, 6, 8)      # module scope
    w30_nodal_drishti.ASPECT_MODIFIERS = {4: 1.05, ...} # module scope
    w23_tara_bala.TARA_MODIFIERS       = {"naidhana": 0.70, ...}  # module scope

Proven at runtime by the reviewer: editing `ASPECT_OFFSETS` to `(4, 6, 8, 2)`
and `TARA_MODIFIERS["naidhana"]` to `0.10` on disk, clearing `__pycache__` and
re-deriving in a fresh interpreter produced a BYTE-IDENTICAL signature and
substep fingerprint. The delta-skip would therefore still fire on a retune —
F-52 itself recurring, in the single most likely future edit. Digesting the
whole module closes it; `test_f52_module_level_constant_*` are the gates.

`scoring_signature_digest()` is the stable MD5 of that structure, folded by
`compute_substep_fingerprint` into every substep's fingerprint.

WHAT THIS DOES AND DOES NOT CATCH (honest scope)
------------------------------------------------
CATCHES, with no human remembering to bump anything:
  * a mechanism added to (or removed from) the engine's production path — the
    literal F-52/F-21 scenario;
  * a mechanism's default toggle flipped on or off;
  * a factor added to or removed from the lambda_v3 / term_breakdown formula;
  * ANY edit anywhere in a mechanism module's source — inside `compute()` (an
    honest-skip branch added) or at module scope (a modifier schedule changing
    0.70 → 0.65, an aspect offset corrected, a helper rewritten).

DOES NOT CATCH:
  * a value-computation change in `engine.py` OUTSIDE any mechanism module and
    outside the formula constants (e.g. re-tuning `_ACTIVITY_MAX_ORB_DEG`, or
    rewriting `_compute_activity_v3`'s internals).
    The `ENGINE_VERSION` standing rule remains load-bearing for that class of
    change. F-52 narrows that rule's surface substantially; it does not
    eliminate it, and claiming otherwise would be exactly the overstatement
    PARĪKṢAKA F-3 corrected in MR-38.
  * a mechanism whose behaviour is driven by data outside its source (a YAML
    weight file, a DB-resident schedule). Those need their own fold.

DISCOVERY GUARANTEE (exact, after the GA-5 review)
--------------------------------------------------
`discover_engine_mechanisms` finds a mechanism by TWO independent routes, and
its guarantee is the union of them — not "cannot fail to appear", which was the
first cut's overstatement:

  1. **Module objects** bound in the engine's namespace
     (`from ...mechanisms import w30_nodal_drishti as _w30`) — found by walking
     `vars(engine)` for `types.ModuleType` values under the mechanism package.
  2. **Function-style imports** (`from ...mechanisms.w24_sade_sati import
     compute as _sade`), which bind NO module object and were therefore
     invisible to route 1. Found by AST-scanning the engine's own source for
     `ImportFrom` nodes whose module sits under the mechanism package, then
     resolving the already-imported module out of `sys.modules`.

Route 2 exists because the first cut's claim was unenforced convention. It is
backed by a real detector rather than a promise: `scan_engine_mechanism_imports`
reports the split and its own status, that status is folded into the signature
(so a scan going `source-unavailable` is itself a signature change, never a
silent pass), and `test_f52_function_style_mechanism_import_is_not_invisible`
proves a function-style import is discovered.

DELIBERATE OVER-INVALIDATION: a comment- or docstring-only edit anywhere in a
mechanism module changes the digest and forces a recompute. That is the safe
direction — an unnecessary rebuild costs time; a silently-skipped one serves a
stale classical judgment as current, which is the defect F-52 exists to close.

REBUILD REQUIREMENT: this module changes the fingerprint every subsequent build
computes. It does not, and cannot, alter rows already sitting in
`kala_gochara_windows` / `kala_gochara_windows_v2`. Already-materialised windows
carry their stale pre-mechanism scores until `ka_gochara_v3_century_materialize`
is re-run for the affected charts — at which point the delta-skip correctly
declines to fire and the windows are re-scored.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sys
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


def _source_digest(obj: Any) -> str:
    """Digest the source text of ``obj`` (a module, function or class).

    Returns a sentinel (never a fabricated-clean value) when the source cannot
    be read — e.g. a C extension or a dynamically-constructed callable. An
    unreadable source is recorded honestly as unreadable, so the state is
    visible in the signature rather than masquerading as a stable digest.
    """
    try:
        src = inspect.getsource(obj)
    except (OSError, TypeError):
        return "source-unavailable"
    return hashlib.md5(src.encode("utf-8")).hexdigest()


def scan_engine_mechanism_imports(
    engine_module: types.ModuleType | None = None,
) -> dict[str, Any]:
    """AST-scan the engine's own source for mechanism-package imports.

    This is the real detector behind the discovery guarantee (§N.8): rather
    than asserting that every mechanism is imported module-style, it MEASURES
    which style each import actually uses.

    Returns ``{"status", "module_style", "function_style"}`` where:

      * ``status`` is ``"ok"``, ``"source-unavailable"`` (engine source could
        not be read) or ``"unparseable"`` (source read but not valid Python) —
        an honest failure state, folded into the signature so a scan that stops
        working is itself a change rather than a silent pass;
      * ``module_style`` lists mechanism modules imported as MODULE objects
        (``from ...mechanisms import w30_nodal_drishti as _w30``), which
        ``vars(engine)`` discovery already sees;
      * ``function_style`` lists mechanism modules from which only NAMES are
        imported (``from ...mechanisms.w24_sade_sati import compute``). These
        bind no module object and were invisible to the first cut of this
        module; :func:`discover_engine_mechanisms` now folds them in.
    """
    if engine_module is None:
        from services.gochara_v3 import engine as engine_module  # local: avoid import cycle

    try:
        source = inspect.getsource(engine_module)
    except (OSError, TypeError):
        return {"status": "source-unavailable", "module_style": [], "function_style": []}

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"status": "unparseable", "module_style": [], "function_style": []}

    package = MECHANISM_PACKAGE_PREFIX.rstrip(".")
    module_style: set[str] = set()
    function_style: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module is None or node.level:
                continue
            if node.module == package:
                # `from services.gochara_v3.mechanisms import wNN_x` — each
                # alias names a submodule, bound as a module object.
                for alias in node.names:
                    if alias.name != "*":
                        module_style.add(f"{package}.{alias.name}")
            elif node.module.startswith(MECHANISM_PACKAGE_PREFIX):
                # `from services.gochara_v3.mechanisms.wNN_x import compute`
                # — binds a function, not the module.
                function_style.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(MECHANISM_PACKAGE_PREFIX):
                    module_style.add(alias.name)

    return {
        "status": "ok",
        "module_style": sorted(module_style),
        "function_style": sorted(function_style - module_style),
    }


def _mechanism_entry(
    engine_module: types.ModuleType,
    module: types.ModuleType,
    discovery: str,
) -> dict[str, Any]:
    mod_name = getattr(module, "__name__", "")
    mechanism_id = getattr(module, "MECHANISM_ID", None) or mod_name.rsplit(".", 1)[-1]
    flag_name = toggle_flag_name(mechanism_id)
    # `None` when the engine declares no flag for this mechanism — an honest
    # "no toggle found", never an assumed-True default (§N.7 item 6).
    enabled = getattr(engine_module, flag_name, None)

    compute_fn = getattr(module, "compute", None)
    compute_digest = _source_digest(compute_fn) if callable(compute_fn) else _NO_COMPUTE

    return {
        "mechanism_id": mechanism_id,
        "module": mod_name,
        "discovery": discovery,
        "toggle_flag": flag_name,
        "enabled": enabled,
        # WHOLE-module source: covers compute()'s body AND the module-scope
        # scoring constants it reads (ASPECT_OFFSETS, TARA_MODIFIERS, …), which
        # a compute()-only digest missed entirely (GA-5 review of the first cut).
        "module_source_digest": _source_digest(module),
        # Kept ALONGSIDE the module digest, not replaced by it: the only term
        # that covers a `compute` bound from a different module, or rebound at
        # runtime, where the mechanism module's own source would not contain it.
        "compute_digest": compute_digest,
    }


def discover_engine_mechanisms(engine_module: types.ModuleType | None = None) -> list[dict[str, Any]]:
    """Discover the scoring mechanisms the gochara_v3 engine actually imports.

    Two independent routes, whose UNION is the guarantee (see the module
    docstring's "DISCOVERY GUARANTEE" — this is deliberately not stated as
    "a wired-in mechanism cannot fail to appear", which the first cut claimed
    while only ever implementing route 1):

      1. module objects in ``vars(engine_module)`` under
         ``services.gochara_v3.mechanisms.`` — the module-style import;
      2. modules named by function-style ``from ...mechanisms.wNN_x import
         compute`` statements in the engine's source, resolved out of
         ``sys.modules`` (they are already imported — the engine imported
         them — so nothing new is executed here).

    Either way the set is read off the engine that does the scoring, never a
    hand-maintained list that could drift from it.

    Returns a list of dicts sorted by ``mechanism_id``.
    """
    if engine_module is None:
        from services.gochara_v3 import engine as engine_module  # local: avoid import cycle

    entries: list[dict[str, Any]] = []
    seen_modules: set[str] = set()

    # Route 1 — module objects bound in the engine namespace.
    for value in vars(engine_module).values():
        if not isinstance(value, types.ModuleType):
            continue
        mod_name = getattr(value, "__name__", "")
        if not mod_name.startswith(MECHANISM_PACKAGE_PREFIX):
            continue
        if mod_name in seen_modules:
            continue
        seen_modules.add(mod_name)
        entries.append(_mechanism_entry(engine_module, value, "module_object"))

    # Route 2 — function-style imports, which bind no module object.
    for mod_name in scan_engine_mechanism_imports(engine_module)["function_style"]:
        if mod_name in seen_modules:
            continue
        seen_modules.add(mod_name)
        module = sys.modules.get(mod_name)
        if module is None:
            # Named in the engine's source but not resident: record it
            # honestly rather than dropping it silently.
            entries.append(
                {
                    "mechanism_id": mod_name.rsplit(".", 1)[-1],
                    "module": mod_name,
                    "discovery": "function_style_import_unresolved",
                    "toggle_flag": toggle_flag_name(mod_name.rsplit(".", 1)[-1]),
                    "enabled": None,
                    "module_source_digest": "module-not-loaded",
                    "compute_digest": "module-not-loaded",
                }
            )
            continue
        entries.append(_mechanism_entry(engine_module, module, "function_style_import"))

    entries.sort(key=lambda e: (e["mechanism_id"], e["module"]))
    return entries


def scoring_signature(engine_module: types.ModuleType | None = None) -> dict[str, Any]:
    """Return the live scoring-mechanism signature for the gochara_v3 engine.

    The returned structure changes exactly when the production scoring
    mechanism set, its toggles, any mechanism module's SOURCE (``compute()``
    body or module-scope scoring constants alike), or the lambda_v3 formula
    strings change.

    ``signature_version`` is 2 since the GA-5 review: v1 digested
    ``module.compute`` only and was blind to module-scope constant edits.
    """
    if engine_module is None:
        from services.gochara_v3 import engine as engine_module  # local: avoid import cycle

    scan = scan_engine_mechanism_imports(engine_module)
    return {
        "signature_version": 2,
        "lambda_formula": getattr(engine_module, "LAMBDA_V3_FORMULA", None),
        "term_breakdown_formula": getattr(engine_module, "TERM_BREAKDOWN_FORMULA", None),
        # Folded so a scan that degrades to source-unavailable/unparseable, or
        # an import that switches style, is a visible signature change rather
        # than a silent loss of coverage (§N.8).
        "import_scan": scan,
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
    "scan_engine_mechanism_imports",
    "scoring_signature",
    "scoring_signature_digest",
    "toggle_flag_name",
]
