"""Rule-registry binding (Pravāha A5.3, step `rule_binding`) — persistence of
the P1–P5 rule catalogue into migration 1154's tables.

The catalogue DATA is Stream B's (`services/gochara_rules/registry.py`,
rule_version "1.0.0", GOCHARA_DESIGN_SPECS_v1_4 §2). This module is the
WRITER-side binding: it encodes that catalogue into 1154's typed schema
(frame_kind/frame_arg, JSONB agent/relation vocab arrays, structured
object_selector, composite version-bound membership, the F3 seal) and
persists it under the Gochara-5 GLOBAL family key (the tables' write-guard
triggers take the lock; the caller's transaction must NOT hold the chart
family key — global EXCLUSIVE and chart keys are mutually exclusive, N13).

Encoding decisions (each folds into the frozen specs' v1.5 at the A5.5 Codex
gate; flagged to the steward on the tracker):

  E1. `frame`: P1 → dasha_lord, P2 → moon, P3/P4/P5 → lagna (spec §2.2
      verbatim). P3's bereavement bhavat_bhavam:9 variation is class-level
      object resolution (P3_TRUTH_TABLE), not the path frame.
  E2. `agent_set`: P1/P2/P3/P5 = all nine grahas (the period-lord agent set
      of P1 is any graha in its period role — spec §2.1 exhaustive agent
      set); P4 = [jupiter, saturn].
  E3. `object_selector`: the full (agent × relation × object_role) cross over
      the path's agent_set × relation_set × its role inventory — spec §2.1
      "no other exclusion" (the truth table bounds houses, not roles). Role
      inventories: P1 {period_lord, signature_house, lord, occupant,
      dispositor, maraka_of_house}; P2 {signature_house} (the residence house
      from janma-rāśi); P3 {signature_house, lord, occupant, karaka,
      maraka_of_house}; P4 {signature_house, lord} (R3-S02's infl(g));
      P5 {signature_house} (per-sign residence with AV operands).
  E4. `direction`: the DB CHECK is binary (higher_stronger|lower_stronger)
      where Stream B's rows carry prose. Doctrine-ordered categoricals bind
      as higher_stronger with `doctrine_ordering` listed WEAKEST → STRONGEST
      (dignity: debility…exaltation per the virupa anchor; agent_nature:
      malefic→benefic; moon_paksa: waning→waxing; mercury_affiliation:
      joined→unaffiliated; maitri: extreme_enemy…extreme_friend). combustion
      binds lower_stronger. O-RP-7's sign/channel lives in `effect`.
  E5. dignity_of_transit_sign's virupa ordering_anchor rides as
      `category_mapping` (an uncalibrated row MAY carry an authored default
      mapping, F6); calibration_status stays uncalibrated_default.
  E6. Predicate operands name selectors in predicates.py's own operator
      vocabulary (no free prose, §2.1): evaluation-time resolution is the
      window_evaluator's job; the binding only declares them.

Deferrals (NOT bound in this step, reported to the steward):
  D1. **P6** — its frame ("per the admitting path's objects") is no value of
      ka_gochara_frame_ok; P6 is the EPHEMERAL day tier (pin 6) and binds
      with the `day_on_demand` step.
  D2. **sad_bala_summary** — its units ("rupas") violate kgf_units_ck and its
      declared range [0,1] contradicts rupa magnitudes; a spec-level fold for
      v1.5, never a silent re-unit (fix the data, not the detector —
      ADK-0026).

Idempotency discipline (matches SkyEventStore): every row is
insert-if-absent; an existing row with ANY different field is a loud
RegistryDivergenceError, never a silent reuse. Seal order within one
transaction: path row → membership rows → seal row (a seal committed first
refuses later membership, F3/N5).
"""
from __future__ import annotations

import json

from services.gochara_rules import registry as rules_registry

RULE_VERSION = rules_registry.RULE_VERSION

NINE_GRAHAS = (
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
    "rahu", "ketu",
)
TRANSIT_RELATIONS = ("residence", "aspect", "conjunction")
NATAL_RELATIONS = (
    "dispositorship", "association", "ownership", "occupancy", "period_running",
)

# Paths bound in this step (D1: P6 rides day_on_demand).
BOUND_PATHS = ("P1", "P2", "P3", "P4", "P5")

_PATH_FRAME = {
    "P1": ("dasha_lord", None),
    "P2": ("moon", None),
    "P3": ("lagna", None),
    "P4": ("lagna", None),
    "P5": ("lagna", None),
}
_PATH_AGENTS = {
    "P1": NINE_GRAHAS,
    "P2": NINE_GRAHAS,
    "P3": NINE_GRAHAS,
    "P4": ("jupiter", "saturn"),
    "P5": NINE_GRAHAS,
}
_PATH_RELATIONS = {
    "P1": TRANSIT_RELATIONS + NATAL_RELATIONS,
    "P2": ("residence",),
    "P3": TRANSIT_RELATIONS,
    "P4": TRANSIT_RELATIONS,
    "P5": ("residence",),
}
_PATH_ROLES = {
    "P1": ("period_lord", "signature_house", "lord", "occupant",
           "dispositor", "maraka_of_house"),
    "P2": ("signature_house",),
    "P3": ("signature_house", "lord", "occupant", "karaka", "maraka_of_house"),
    "P4": ("signature_house", "lord"),
    "P5": ("signature_house",),
}

# E4/E5: factor binding overrides keyed by factor_id. Anything not overridden
# binds straight from Stream B's row.
_FACTOR_DIRECTION = {
    "dignity_of_transit_sign": "higher_stronger",
    "combustion": "lower_stronger",
    "activity_kernel": "higher_stronger",
    "graduated_drishti": "higher_stronger",
    "vedha_attenuation": "higher_stronger",
    "yoga_strength": "higher_stronger",
    "promise_condition": "higher_stronger",
    "agent_nature": "higher_stronger",
    "moon_paksa": "higher_stronger",
    "mercury_affiliation": "higher_stronger",
    "maitri_compound": "higher_stronger",
}
_FACTOR_DOCTRINE_ORDERING = {
    "dignity_of_transit_sign": ["debility", "inimical", "neutral", "friendly",
                                "own", "exaltation"],
    "agent_nature": ["malefic", "benefic"],
    "moon_paksa": ["waning", "waxing"],
    "mercury_affiliation": ["joined_to_malefic", "unaffiliated"],
    "maitri_compound": ["extreme_enemy", "enemy", "neutral", "friend",
                        "extreme_friend"],
}
_FACTOR_OPERAND_TOKEN = {
    "dignity_of_transit_sign": "dignity:transit_sign_for_period_lord",
    "combustion": "state:combustion_of_period_lord",
    "activity_kernel": "geometry:delta_lambda_to_exact",
    "graduated_drishti": "geometry:aspect_house_offset",
    "vedha_attenuation": "overlay:vedha_interval_state",
    "yoga_strength": "yoga:declared_strength",
    "promise_condition": "promise:condition_predicate",
    "agent_nature": "nature:agent_benefic_malefic",
    "moon_paksa": "moon:sun_moon_elongation",
    "mercury_affiliation": "mercury:joined_to_malefic",
    "maitri_compound": "maitri:pancadha_compound",
}
# Factors bound in this step (D2: sad_bala_summary deferred — units conflict).
BOUND_FACTORS = tuple(_FACTOR_DIRECTION)

# E6: predicate declarations (id → (operator, operands)).
PREDICATES: dict[str, tuple[str, dict]] = {
    "period_running_at": (
        "period_running_at",
        {"rows": "l1:dasha_periods", "t": "eval:instant"},
    ),
    "natal_bhava_relationship": (
        "declaration_exists",
        {"declarations": "chart:natal_bhava_relationship",
         "key": "eval:class_period_lord"},
    ),
    "transit_relation": (
        "declaration_exists",
        {"declarations": "gochara:contacts", "key": "eval:agent_relation_object"},
    ),
    "house_from_moon": (
        "house_from",
        {"house": "eval:house_from_janma_rashi", "set": ["p2:adverse_house_set"]},
    ),
    "p3_contact_house_or_lord": (
        "declaration_exists",
        {"declarations": "gochara:contacts", "key": "p3:house_or_lord"},
    ),
    "p4_double_transit": (
        "declaration_exists",
        {"declarations": "eval:p4_influence", "key": "eval:class"},
    ),
    "av_polarity_declaration_exists": (
        "declaration_exists",
        {"declarations": "gochara:av_polarity_declaration",
         "key": "eval:agent_sign"},
    ),
    "admitted_window_exists": (
        "declaration_exists",
        {"declarations": "gochara:eval_window", "key": "eval:class_day"},
    ),
}


class RegistryDivergenceError(RuntimeError):
    """An existing registry row differs in ANY field from the declared
    catalogue — loud failure, never a silent reuse (fix the data, not the
    detector, ADK-0026)."""


def object_selector_for(path_id: str) -> list[dict]:
    """E3: the full (agent × relation × object_role) cross for the path."""
    return [
        {"agent": agent, "relation": relation, "object_role": role}
        for agent in _PATH_AGENTS[path_id]
        for relation in _PATH_RELATIONS[path_id]
        for role in _PATH_ROLES[path_id]
    ]


def predicate_rows() -> list[dict]:
    return [
        {"predicate_id": pid, "rule_version": RULE_VERSION,
         "operator": op, "operands": operands}
        for pid, (op, operands) in PREDICATES.items()
    ]


def factor_rows() -> list[dict]:
    """Stream B's FACTORS bound per E4/E5 (sad_bala_summary deferred, D2)."""
    rows = []
    for fid in BOUND_FACTORS:
        src = rules_registry.FACTORS[(fid, RULE_VERSION)]
        units = src["units"]
        if units not in ("degrees", "days", "count", "unitless"):
            raise RegistryDivergenceError(
                f"factor {fid}: units {units!r} outside kgf_units_ck — "
                "deferred factors must be excluded upstream (D2)"
            )
        rows.append({
            "factor_id": fid,
            "rule_version": RULE_VERSION,
            "operand_selector": {"operand": _FACTOR_OPERAND_TOKEN[fid]},
            "direction": _FACTOR_DIRECTION[fid],
            "function": src["function"],
            "range_lower": float(src["range"][0]),
            "range_upper": float(src["range"][1]),
            "units": units,
            "calibration_status": src["calibration_status"],
            "doctrine_ordering": _FACTOR_DOCTRINE_ORDERING.get(fid),
            "category_mapping": (src.get("ordering_anchor")
                                 if fid == "dignity_of_transit_sign" else None),
            "null_state": src["null_state"],
            "effect": src["effect"],
        })
    return rows


def path_rows() -> list[dict]:
    rows = []
    for pid in BOUND_PATHS:
        src = rules_registry.RULE_PATHS[(pid, RULE_VERSION)]
        frame_kind, frame_arg = _PATH_FRAME[pid]
        rows.append({
            "path_id": pid,
            "rule_version": RULE_VERSION,
            "frame_kind": frame_kind,
            "frame_arg": frame_arg,
            "agent_set": list(_PATH_AGENTS[pid]),
            "relation_set": list(_PATH_RELATIONS[pid]),
            "object_selector": object_selector_for(pid),
            "provenance": src["provenance"],
            "operator_role": src["operator_role"],
            "ruling_ref": src.get("ruling_ref"),
            "score_rule": src["score_rule"],
        })
    return rows


def prerequisite_rows() -> list[dict]:
    rows = []
    for pid in BOUND_PATHS:
        src = rules_registry.RULE_PATHS[(pid, RULE_VERSION)]
        for ordinal, (pred_id, pred_version) in enumerate(
            src["prerequisites"], start=1
        ):
            rows.append({
                "path_id": pid, "rule_version": RULE_VERSION,
                "ordinal": ordinal, "predicate_id": pred_id,
                "predicate_rule_version": pred_version,
            })
    return rows


def soft_factor_rows() -> list[dict]:
    rows = []
    for pid in BOUND_PATHS:
        src = rules_registry.RULE_PATHS[(pid, RULE_VERSION)]
        for factor_id, factor_version in src["soft_factors"]:
            rows.append({
                "path_id": pid, "rule_version": RULE_VERSION,
                "factor_id": factor_id,
                "factor_rule_version": factor_version,
            })
    return rows


def _membership_consistent() -> None:
    """Write-time guard: every composite reference in the path catalogue
    resolves to a row this binding declares (a bare or dangling reference is
    rejected before any SQL — §2.1)."""
    declared_predicates = set(PREDICATES)
    declared_factors = set(BOUND_FACTORS)
    for pid in BOUND_PATHS:
        src = rules_registry.RULE_PATHS[(pid, RULE_VERSION)]
        for pred_id, pred_version in src["prerequisites"]:
            if pred_id not in declared_predicates or pred_version != RULE_VERSION:
                raise ValueError(
                    f"{pid}: prerequisite ({pred_id}, {pred_version}) not bound"
                )
        for factor_id, factor_version in src["soft_factors"]:
            if factor_id not in declared_factors or factor_version != RULE_VERSION:
                raise ValueError(
                    f"{pid}: soft factor ({factor_id}, {factor_version}) not bound"
                )


class RuleRegistryStore:
    """Persistence over migration 1154's rule-path registry tables.

    Insert-if-absent with a full-field equality check; any divergence is a
    loud RegistryDivergenceError. The tables are insert-only under the
    Gochara-5 GLOBAL family key (write-guard triggers take the lock) — the
    caller's transaction must NOT hold the chart family key (N13). No commit,
    rollback or close here: the connection is the orchestrator's.
    """

    def __init__(self, conn):
        self.conn = conn

    # ── generic insert-if-absent ─────────────────────────────────────────

    def _bind(self, table: str, pk: tuple[str, ...], row: dict) -> str:
        cols = list(row)
        where = " AND ".join(f"{c} = %s" for c in pk)
        existing = self.conn.execute(
            f"SELECT {', '.join(cols)} FROM public.{table} WHERE {where}",
            tuple(_adapt(row[c]) for c in pk),
        ).fetchone()
        if existing is not None:
            stored = dict(zip(cols, existing))
            declared = {c: _adapt(row[c]) for c in cols}
            normalised = {c: _normalise(stored[c]) for c in cols}
            if normalised != {c: _normalise(declared[c]) for c in cols}:
                raise RegistryDivergenceError(
                    f"{table} {tuple(row[c] for c in pk)}: stored row diverges "
                    f"from the declared catalogue — stored {stored} vs "
                    f"declared {declared}"
                )
            return "reused"
        self.conn.execute(
            f"INSERT INTO public.{table} ({', '.join(cols)})"
            f" VALUES ({', '.join(['%s'] * len(cols))})"
            f" ON CONFLICT ({', '.join(pk)}) DO NOTHING",
            tuple(_adapt(row[c]) for c in cols),
        )
        return "inserted"

    # ── seed ─────────────────────────────────────────────────────────────

    def seed(self) -> dict[str, int]:
        """Bind the full catalogue in dependency order, then seal every bound
        path version (F3). Idempotent: a re-run of a completed seed reuses
        every row; a partial earlier run resumes where it stopped."""
        _membership_consistent()
        counts = {"predicates": 0, "factors": 0, "paths": 0,
                  "prerequisites": 0, "soft_factors": 0, "seals": 0,
                  "reused": 0}

        def tally(outcome: str, key: str) -> None:
            if outcome == "inserted":
                counts[key] += 1
            else:
                counts["reused"] += 1

        for row in predicate_rows():
            tally(self._bind("ka_gochara_predicate",
                             ("predicate_id", "rule_version"), row), "predicates")
        for row in factor_rows():
            tally(self._bind("ka_gochara_factor",
                             ("factor_id", "rule_version"), row), "factors")
        for row in path_rows():
            tally(self._bind("ka_gochara_rule_path",
                             ("path_id", "rule_version"), row), "paths")
        for row in prerequisite_rows():
            tally(self._bind("ka_gochara_rule_path_prerequisite",
                             ("path_id", "rule_version", "ordinal"), row),
                  "prerequisites")
        for row in soft_factor_rows():
            tally(self._bind("ka_gochara_rule_path_soft_factor",
                             ("path_id", "rule_version", "factor_id",
                              "factor_rule_version"), row), "soft_factors")
        for pid in BOUND_PATHS:
            tally(self._bind("ka_gochara_rule_path_seal",
                             ("path_id", "rule_version"),
                             {"path_id": pid, "rule_version": RULE_VERSION}),
                  "seals")
        return counts


def _adapt(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return value


def _normalise(value):
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            return value
        if isinstance(parsed, (dict, list)):
            return parsed
        return value
    return value


__all__ = [
    "BOUND_FACTORS",
    "BOUND_PATHS",
    "PREDICATES",
    "RULE_VERSION",
    "RegistryDivergenceError",
    "RuleRegistryStore",
    "factor_rows",
    "object_selector_for",
    "path_rows",
    "predicate_rows",
    "prerequisite_rows",
    "soft_factor_rows",
]
