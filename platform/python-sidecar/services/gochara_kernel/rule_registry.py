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

# R5 (Codex round 6): the binder selects EXPLICIT composite references — never "every row at the global
# RULE_VERSION". A new immutable version (e.g. the AM-13 activity_kernel@1.1.0 / P3,P4,P5@1.1.0 rows) is
# bound ONLY by a deliberate edit to these tuples, after its review gate passes; each prerequisite and soft
# factor keeps ITS OWN version (the path row's composite references). Bumping a global would also disturb
# every unchanged path and predicate.
# Paths bound in this step (D1: P6 rides day_on_demand).
#: ND-H-20261005 (FB-30): the P1/P3/P4 rows at rule_version 1.2.0 — the eight classes' tiers and kārakas.
ND_H_PATH_REFS = tuple((pid, rules_registry.ND_H_VERSION) for pid in ("P1", "P3", "P4"))
BOUND_PATH_REFS = ((("P1", "1.0.0"), ("P2", "1.0.0"), ("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0"))
                   + ND_H_PATH_REFS)
BOUND_PATHS = tuple(dict.fromkeys(pid for pid, _v in BOUND_PATH_REFS))


def bound_path_refs() -> tuple[tuple[str, str], ...]:
    """The CURRENT bound CATALOGUE — every sealed (path, version) — read at call time (a consumer never
    captures the tuple at import)."""
    return tuple(BOUND_PATH_REFS)


# R8-2 (Codex round 8): the bound CATALOGUE is not the SELECTION. `BOUND_PATH_REFS` is every (path, version)
# sealed (each must be accounted for in a class inventory — `registry_unaccounted_path`); the SELECTION is the
# one version of each path a class's search runs under (1206: at most ONE `included` version per class and
# path). The default selection is the 1.0.0 set; a successor is searched only by a deliberate edit of
# `SELECTED_PATH_REFS` (or a per-class override) after its review gate passes. Both are read at call time.
SELECTED_PATH_REFS = (("P1", "1.0.0"), ("P2", "1.0.0"), ("P3", "1.0.0"), ("P4", "1.0.0"), ("P5", "1.0.0"))
# ND-H-20261005 (FB-30): 1.2.0 is selected PER CLASS — the eight ND-H classes run P1/P3/P4 under 1.2.0; every
# other class stays at the default selection, so its obligations, records and digests are byte-identical.
CLASS_SELECTION_OVERRIDES: dict = {           # {(event_class, path_id): version}
    (cls, pid): version
    for cls in sorted(rules_registry.ND_H_CLASSES) for pid, version in ND_H_PATH_REFS}


def selected_versions_for(event_class: str) -> dict[str, str]:
    """{path_id: the ONE version a class's search runs under}: the default selection with the per-class
    overrides applied; refuses a selection that is not sealed in the bound catalogue."""
    selected = dict(SELECTED_PATH_REFS)
    for (cls, pid), version in CLASS_SELECTION_OVERRIDES.items():
        if cls == event_class:
            selected[pid] = version
    for pid, version in selected.items():
        if (pid, version) not in BOUND_PATH_REFS:
            raise ValueError(f"selected {pid}@{version} is not in the bound catalogue")
    return selected


def p2_emits_no_row(event_class: str) -> bool:
    """ND-H-20261005 item 5: P2 emits NO row for a parent class once that class runs under its ND-H rows (the
    native's Moon never evidences the parent, §1.2 inv 6). Read from the CURRENT selection at call time: with the
    class back on its pre-ND-H selection the P2 rows it had are enumerated again (a past generation is replayable)."""
    return (event_class in rules_registry.P2_NO_ROW_CLASSES
            and selected_versions_for(event_class).get("P3") == rules_registry.ND_H_VERSION)


def selected_path_version(event_class: str, path_id: str) -> str:
    """The version `event_class`'s search runs `path_id` under — the one every enumerator, inventory pin and
    record of that class/path must carry (never the global RULE_VERSION, never merely the first bound)."""
    try:
        return selected_versions_for(event_class)[path_id]
    except KeyError:
        raise KeyError(f"path {path_id!r} has no selected version") from None


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
# A role inventory that differs at ONE version is keyed by the composite reference — a sealed row's
# object_selector is never changed by a later version's needs. ND-H K-B: P4's infl() reads the natal
# luminary kāraka target at 1.2.0.
_PATH_ROLES_AT = {("P4", rules_registry.ND_H_VERSION): ("signature_house", "lord", "karaka")}

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
    "karaka_agent": "higher_stronger",
}
_FACTOR_DOCTRINE_ORDERING = {
    "karaka_agent": ["non_karaka", "karaka"],            # WEAKEST → STRONGEST (ND-H: karaka > non_karaka)
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
    "karaka_agent": "karaka:agent_is_class_karaka",
}
# Factors bound in this step (D2: sad_bala_summary deferred — units conflict).
# `karaka_agent` exists from 1.2.0 only (ND-H K-A); every other bound factor stays at its 1.0.0 row.
_FACTOR_FIRST_VERSION = {"karaka_agent": rules_registry.ND_H_VERSION}
BOUND_FACTOR_REFS = tuple((fid, _FACTOR_FIRST_VERSION.get(fid, "1.0.0")) for fid in _FACTOR_DIRECTION)
BOUND_FACTORS = tuple(dict.fromkeys(fid for fid, _v in BOUND_FACTOR_REFS))

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
        # AM-11 pin (c): the operand is the agent's CITED house set (Phaladīpikā XXVI.1-8
        # favourable ∪ the D-RQ5 adverse 12/8/1) — polarity is a valence step, not
        # admission. Renamed from `p2:adverse_house_set`; no '5.0' row exists under the
        # old operand (read-only production check, steward 2026-10-02), so no version bump.
        {"house": "eval:house_from_janma_rashi", "set": ["p2:cited_house_set"]},
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


BOUND_PREDICATE_REFS = tuple((pid, "1.0.0") for pid in PREDICATES)


class RegistryDivergenceError(RuntimeError):
    """An existing registry row differs in ANY field from the declared
    catalogue — loud failure, never a silent reuse (fix the data, not the
    detector, ADK-0026)."""


def object_selector_for(path_id: str, rule_version: str | None = None) -> list[dict]:
    """E3: the full (agent × relation × object_role) cross for the path (at `rule_version`, where a
    version declares its own role inventory)."""
    roles = _PATH_ROLES_AT.get((path_id, rule_version), _PATH_ROLES[path_id])
    return [
        {"agent": agent, "relation": relation, "object_role": role}
        for agent in _PATH_AGENTS[path_id]
        for relation in _PATH_RELATIONS[path_id]
        for role in roles
    ]


def predicate_rows() -> list[dict]:
    return [
        {"predicate_id": pid, "rule_version": version,
         "operator": PREDICATES[pid][0], "operands": PREDICATES[pid][1]}
        for pid, version in BOUND_PREDICATE_REFS
    ]


# ── R5: ONE codec (Codex round 7 [4]) ────────────────────────────────────────
# `services.gochara_rules.flat_selector` is the single codec for a factor's applicability declaration (Stream
# B's; closed key schema, orb ratification invariant, 1154's flat-object shape). This module has NO codec of
# its own: the catalogue row's `operand_selector` (the flat form IS the source of truth) is persisted
# VERBATIM, checked with `flat_problems` / `kernel_flat_problems`, read back flat-to-flat, and the decoded
# nested `applicability` evaluators read must equal the declaration.
from services.gochara_rules import flat_selector as _flat

_DECODE = {"activity_kernel": _flat.decode_kernel, "graduated_drishti": _flat.decode_drishti,
           "vedha_attenuation": _flat.decode_vedha}


def factor_operand_selector(fid: str, src: dict) -> dict:
    """The flat selector to persist: the catalogue row's own (verbatim) when it declares one, else the
    plain operand token of the unchanged 1.0.0 rows."""
    sel = src.get("operand_selector")
    if sel is None:
        return {"operand": _FACTOR_OPERAND_TOKEN[fid]}
    problems = _flat.flat_problems(sel)
    if fid == "activity_kernel":
        problems = _flat.kernel_flat_problems(sel)
    if problems:
        raise RegistryDivergenceError(f"factor {fid}: operand_selector refused: " + "; ".join(problems))
    return dict(sel)


def decode_factor_selector(fid: str, selector: dict) -> dict | None:
    """The nested `applicability` a persisted flat selector DECODES to (None for a factor that declares
    none) — through the one codec."""
    if fid not in _DECODE or set(selector) <= {"operand"}:
        return None
    try:
        return _DECODE[fid](selector)
    except (KeyError, ValueError) as exc:
        raise RegistryDivergenceError(f"factor {fid}: persisted selector does not decode: {exc}") from exc


def factor_rows() -> list[dict]:
    """Stream B's FACTORS bound per E4/E5 at their EXPLICIT references (sad_bala_summary deferred, D2)."""
    rows = []
    for fid, version in BOUND_FACTOR_REFS:
        src = rules_registry.FACTORS[(fid, version)]
        units = src["units"]
        if units not in ("degrees", "days", "count", "unitless"):
            raise RegistryDivergenceError(
                f"factor {fid}: units {units!r} outside kgf_units_ck — "
                "deferred factors must be excluded upstream (D2)"
            )
        rows.append({
            "factor_id": fid,
            "rule_version": version,
            "operand_selector": factor_operand_selector(fid, src),
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
    for pid, version in BOUND_PATH_REFS:
        src = rules_registry.RULE_PATHS[(pid, version)]
        frame_kind, frame_arg = _PATH_FRAME[pid]
        rows.append({
            "path_id": pid,
            "rule_version": version,
            "frame_kind": frame_kind,
            "frame_arg": frame_arg,
            "agent_set": list(_PATH_AGENTS[pid]),
            "relation_set": list(_PATH_RELATIONS[pid]),
            "object_selector": object_selector_for(pid, version),
            "provenance": src["provenance"],
            "operator_role": src["operator_role"],
            "ruling_ref": src.get("ruling_ref"),
            "score_rule": src["score_rule"],
        })
    return rows


def prerequisite_rows() -> list[dict]:
    rows = []
    for pid, version in BOUND_PATH_REFS:
        src = rules_registry.RULE_PATHS[(pid, version)]
        for ordinal, (pred_id, pred_version) in enumerate(src["prerequisites"], start=1):
            rows.append({
                "path_id": pid, "rule_version": version,
                "ordinal": ordinal, "predicate_id": pred_id,
                "predicate_rule_version": pred_version,       # the prerequisite's OWN version
            })
    return rows


def soft_factor_rows() -> list[dict]:
    rows = []
    for pid, version in BOUND_PATH_REFS:
        src = rules_registry.RULE_PATHS[(pid, version)]
        for factor_id, factor_version in src["soft_factors"]:
            rows.append({
                "path_id": pid, "rule_version": version,
                "factor_id": factor_id,
                "factor_rule_version": factor_version,        # the factor's OWN version
            })
    return rows


def _membership_consistent() -> None:
    """Write-time guard: every composite reference in a BOUND path resolves to a row this binding
    declares AT THAT EXACT VERSION (a bare, dangling or wrong-version reference is rejected before
    any SQL — §2.1)."""
    # the selection is one version per path, drawn from the bound catalogue
    seen: set[str] = set()
    for pid, version in SELECTED_PATH_REFS:
        if pid in seen:
            raise ValueError(f"selected path {pid} appears twice — at most one version per path")
        seen.add(pid)
        if (pid, version) not in BOUND_PATH_REFS:
            raise ValueError(f"selected path reference {(pid, version)} is not in the bound catalogue")
    declared_predicates = set(BOUND_PREDICATE_REFS)
    declared_factors = set(BOUND_FACTOR_REFS)
    for ref in BOUND_PATH_REFS:
        if ref not in rules_registry.RULE_PATHS:
            raise ValueError(f"bound path reference {ref} is not in the catalogue")
        src = rules_registry.RULE_PATHS[ref]
        for pred_ref in map(tuple, src["prerequisites"]):
            if pred_ref not in declared_predicates:
                raise ValueError(f"{ref[0]}@{ref[1]}: prerequisite {pred_ref} not bound")
        for factor_ref in map(tuple, src["soft_factors"]):
            if factor_ref not in declared_factors:
                raise ValueError(f"{ref[0]}@{ref[1]}: soft factor {factor_ref} not bound")


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
            stored = dict(zip(cols, _as_tuple(cols, existing)))
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
        # R5: READ BACK what was written and compare it with the declaration — an insert that
        # silently stored something else (or nothing) is a divergence, not a success.
        back = self.conn.execute(
            f"SELECT {', '.join(cols)} FROM public.{table} WHERE {where}",
            tuple(_adapt(row[c]) for c in pk),
        ).fetchone()
        if back is None or ({c: _normalise(v) for c, v in zip(cols, _as_tuple(cols, back))}
                            != {c: _normalise(_adapt(row[c])) for c in cols}):
            raise RegistryDivergenceError(
                f"{table} {tuple(row[c] for c in pk)}: read-back after insert does not equal the "
                f"declaration (stored {back!r})")
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
        for pid, version in BOUND_PATH_REFS:
            tally(self._bind("ka_gochara_rule_path_seal",
                             ("path_id", "rule_version"),
                             {"path_id": pid, "rule_version": version}),
                  "seals")
        return counts

    # ── the bound declaration, read BACK for consumption ─────────────────

    def bound_factor_rows(self, path_id: str, rule_version: str) -> list[dict]:
        """The path-version's soft factors as PERSISTED: membership read from the registry tables
        (each factor at its OWN version), each factor row read back, its flat applicability decoded
        and checked against the declaration; the prose `direction` the against-channel rule reads
        comes from the catalogue row at the SAME exact reference (the DB's direction is binary).
        Evaluators are dispatched by the sweep on these exact membership references."""
        members = self.conn.execute(
            "SELECT factor_id, factor_rule_version FROM public.ka_gochara_rule_path_soft_factor"
            " WHERE path_id = %s AND rule_version = %s ORDER BY factor_id, factor_rule_version",
            (path_id, rule_version)).fetchall()
        if not members:
            raise RegistryDivergenceError(f"no soft-factor membership persisted for {path_id}@{rule_version}")
        declared = {(r["factor_id"], r["rule_version"]): r for r in factor_rows()}
        out = []
        for member in members:
            factor_id, factor_version = _as_tuple(["factor_id", "factor_rule_version"], member)
            ref = (factor_id, factor_version)
            if ref not in declared:
                raise RegistryDivergenceError(f"persisted membership {ref} is not a bound factor reference")
            row = self.conn.execute(
                "SELECT operand_selector, null_state, function, direction FROM public.ka_gochara_factor"
                " WHERE factor_id = %s AND rule_version = %s", ref).fetchone()
            if row is None:
                raise RegistryDivergenceError(f"factor {ref} has persisted membership but no row")
            selector, null_state, function, direction = _as_tuple(
                ["operand_selector", "null_state", "function", "direction"], row)
            selector = _normalise(selector)
            want = declared[ref]
            if (selector != want["operand_selector"] or null_state != want["null_state"]
                    or function != want["function"] or direction != want["direction"]):
                raise RegistryDivergenceError(f"persisted factor {ref} diverges from the declaration")
            src = rules_registry.FACTORS[ref]
            decoded = decode_factor_selector(factor_id, selector)
            declared_app = src.get("applicability")
            if (decoded or None) != (declared_app or None):
                raise RegistryDivergenceError(f"factor {ref}: decoded applicability != the declaration")
            item = {"factor_id": factor_id, "rule_version": factor_version, "null_state": null_state,
                    "function": function, "direction": src["direction"]}
            item["operand_selector"] = selector                    # verbatim, as persisted
            if decoded:
                item["applicability"] = decoded
            out.append(item)
        return out


def _as_tuple(cols: list[str], row) -> tuple:
    """A fetched row as a tuple in `cols` order — the runner hands dict rows, the CLI tuples."""
    if isinstance(row, dict):
        return tuple(row[c] for c in cols)
    return tuple(row)


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
    "BOUND_FACTOR_REFS",
    "BOUND_PATHS",
    "BOUND_PATH_REFS",
    "bound_path_refs",
    "SELECTED_PATH_REFS",
    "CLASS_SELECTION_OVERRIDES",
    "selected_path_version",
    "selected_versions_for",
    "p2_emits_no_row",
    "BOUND_PREDICATE_REFS",
    "decode_factor_selector",
    "factor_operand_selector",
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
