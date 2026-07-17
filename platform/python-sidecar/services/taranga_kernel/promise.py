"""
services.taranga_kernel.promise — PROMISE lock formula (L3 Kāla, CR-88).

Doctrine-Waves D-3 / wave/D-3/T-3.

PROMISE = salience × functional_valence × varga_ratification
          × NBRY_deferral_semantics × mechanism_graph_weight

This kills CR-88: today the ONLY signal reaching timing computations
(`services/ka_temporal/date_resolver.py::_proximity_score`,
`pipeline/orchestrator/writers/ka_kalasutra.py:205`,
`services/ka_sangam/engine.py`'s `dignity_score` necessary-condition term) is
a bare `dignity_score`, frequently 0.5-defaulted when the upstream predicate
never populated it. PROMISE replaces that single flat term with a real,
five-factor, chart-grounded product.

SCOPE NOTE (honest, not a stub): this module implements and unit-tests the
formula itself. WIRING it into `date_resolver.py::_proximity_score` (the
actual CR-88 kill site) is OUT OF SCOPE for this lane — that file is not in
wave/D-3/T-3's may_touch list (`services/ka_sangam/**`, the new
taranga_kernel module, `ka_sangam.py`, `ka_taranga.py`, colocated tests only).
A follow-up lane (or the conductor) must do the actual date_resolver.py swap.
Reported here rather than silently expanded out of scope, per the brief's own
instruction to report gaps honestly rather than stub around them.

Each factor's REAL source (never fabricated — B.10 / §N.5):
  salience              — bodha_msr_signals.computed_salience (already a real,
                           chart-scoped [0,1] MSR field; see bo_anveshana.py's
                           use of the same column).
  functional_valence    — chart_vichara.value_num for vichara_family=
                           'valence_pass' rows (ga_vichara_writer.compute_valence,
                           the shared brahmagyan.valence_doctrine — signed,
                           roughly [-1, 1]).
  varga_ratification    — chart_vichara.ratification_factor /.value_num for
                           vichara_family='varga_ratification' rows
                           (ga_vichara_writer.build_varga_ratification_rows,
                           bounded [lo, hi], default [0.6, 1.4] per that
                           writer's own clamp).
  mechanism_graph_weight — the CGM edge_strength term (bo_karanajala.py's
                           DR-7 `_edge_strength_v1`, clamped [0.1, 2.0]) —
                           the D-2 Mechanism/CGM edge-strength field this
                           brief calls the "mechanism graph-weight term".
  NBRY_deferral_semantics — NEW logic (this module): see
                           `nbry_deferral_semantics` below. Sourced from a
                           fired Neecha-Bhanga rule's `supporting_planets`
                           (ga_yoga_writer.py's `nbry_rule_*` finding dicts —
                           the CANCELLER identity), not fabricated.

None of these are re-derived here — every factor is a REQUIRED input the
caller resolves from the real L1/L2 row and passes in (§N.5: this module
REFERENCES, never restates, an L1/L2 computed value).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


# ── NBRY_deferral_semantics ──────────────────────────────────────────────────

def nbry_deferral_semantics(
    chart_id: str,
    cancelled_planet: str,
    canceller_planets: Sequence[str],
    dasha_lord: Optional[str],
    *,
    active_weight: float = 1.0,
    inactive_weight: float = 0.4,
) -> float:
    """
    NBRY (Neecha-Bhanga Raja Yoga) deferral-semantics term of PROMISE.

    Classical point: a cancelled debility's PROMISE does not activate on the
    debilitated planet's own periods the way an ordinary yoga would — the
    cancellation re-times the promise into the CANCELLER's own daśā periods
    (BPHS Ch.39 neecha-bhanga adhyāya: the cancelling graha's strength is what
    "restores" the promise, so its own periods are when the restored promise
    is live). The type specimen the brief names: Venus debilitated in Pisces,
    cancelled by Mercury (e.g. nbry_rule_1_dispositor_kendra firing with
    Mercury as the dispositor-in-kendra) — the PROMISE should re-time toward
    MERCURY's daśā periods, not Venus's.

    chart_id: REQUIRED (CR-87) — never defaulted; this term is meaningless
        without knowing which chart's fired NBRY rule and which chart's daśā
        timeline `dasha_lord` was resolved from. Not used in the arithmetic
        itself (the arithmetic only needs canceller_planets/dasha_lord) but
        required as a positional parameter so this function can never be
        called generically across charts — mirrors the two-chart guard in
        tests/test_cr87_native_chart_context.py.
    cancelled_planet: the debilitated graha (e.g. 'Venus'). Included for
        clarity/logging and as a guard: raises if it appears in
        canceller_planets (a planet cannot cancel its own debility per the
        classical rules this codebase implements — ga_yoga_writer.py's
        nbry_rule_* functions never return the debilitated planet itself as
        a supporting_planet).
    canceller_planets: the fired NBRY rule's `supporting_planets` (from
        ga_yoga_writer.py's `nbry_rule_1_dispositor_kendra` /
        `nbry_rule_2_exaltation_lord_kendra` / `nbry_rule_3_lord_aspect` /
        `nbry_rule_4_conjunct_exaltation_graha` finding dicts) — the REAL
        cancelling graha(s), not invented. Must be non-empty: a bhanga_active
        finding always has >=1 fired rule, each with >=1 supporting_planets
        entry (B.10 — a truthy bhanga_active with no identifiable canceller
        would itself be a data-integrity bug, not something to paper over
        with a default).
    dasha_lord: the daśā lord active at the queried time point (e.g. from
        `taranga_kernel.kernel.dasha_lord_at`), or None if unresolved.

    Returns active_weight (default 1.0) when dasha_lord is one of the
    canceller_planets — the promise is "live" in that period. Returns
    inactive_weight (default 0.4, not 0.0) otherwise: NBRY remains a real
    natal fact even outside the canceller's periods — only its TIMING
    salience shifts, never a hard on/off gate (a 0.0 inactive_weight would
    make PROMISE collapse to exactly 0 for the entire rest of the native's
    life whenever the query falls outside the canceller's daśā, which is not
    what the classical semantics describe — the yoga still "exists", it is
    just not the PEAK activation window).
    """
    if not chart_id:
        raise ValueError("nbry_deferral_semantics: chart_id is required (CR-87)")
    if not canceller_planets:
        raise ValueError(
            "nbry_deferral_semantics: canceller_planets is required and must be "
            "non-empty — a bhanga_active=True finding always names >=1 "
            "supporting_planets (ga_yoga_writer.py nbry_rule_*); an empty list "
            "here indicates a caller bug, not a legitimate 'no canceller' state."
        )
    if cancelled_planet in canceller_planets:
        raise ValueError(
            f"nbry_deferral_semantics: cancelled_planet {cancelled_planet!r} must "
            f"not appear in canceller_planets {list(canceller_planets)!r} — a "
            "planet cannot cancel its own debility under this codebase's "
            "classical NBRY rules."
        )
    if dasha_lord is not None and dasha_lord in canceller_planets:
        return active_weight
    return inactive_weight


# ── compute_promise ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PromiseInputs:
    """Every factor of the PROMISE product, already resolved by the caller
    from the real L1/L2 rows named in this module's docstring. No field here
    is computed inside this dataclass — construction IS the caller's
    derivation-ledger commitment (§B.3: cite the source row for each field)."""
    chart_id: str
    salience: float                  # bodha_msr_signals.computed_salience, [0,1]
    functional_valence: float        # chart_vichara.value_num (valence_pass), signed ~[-1,1]
    varga_ratification: float        # chart_vichara.ratification_factor (varga_ratification), ~[0.6,1.4]
    nbry_deferral: float             # nbry_deferral_semantics(...) output, [inactive_weight, active_weight]
    mechanism_graph_weight: float    # bo_karanajala.py edge_strength, [0.1,2.0]

    def __post_init__(self) -> None:
        if not self.chart_id:
            raise ValueError("PromiseInputs.chart_id is required (CR-87)")


def compute_promise(inputs: PromiseInputs) -> float:
    """
    PROMISE = salience × functional_valence × varga_ratification
              × NBRY_deferral_semantics × mechanism_graph_weight

    A straight product of the five real factors described in this module's
    docstring. `functional_valence` may be negative (a malefic functional
    lordship is a real, signed classical judgment, not noise) — the raw
    product can therefore be negative or exceed 1.0 (mechanism_graph_weight
    alone can reach 2.0). The result is clamped to [0, 1] because PROMISE
    feeds timing computations (`_proximity_score`-shaped consumers) that
    expect a [0,1] weight the same way `dignity_score` did — a negative raw
    product clamps to 0.0 (no promise: the configuration is net-adverse, not
    a "promise" in the classical sense), never inverted or re-signed. This
    clamp is the one normalization decision this function makes; it is not a
    fabricated component (B.10) — it is a range contract on the OUTPUT of a
    real product of real inputs.
    """
    raw = (
        inputs.salience
        * inputs.functional_valence
        * inputs.varga_ratification
        * inputs.nbry_deferral
        * inputs.mechanism_graph_weight
    )
    return max(0.0, min(1.0, raw))


__all__ = [
    "PromiseInputs",
    "compute_promise",
    "nbry_deferral_semantics",
]
