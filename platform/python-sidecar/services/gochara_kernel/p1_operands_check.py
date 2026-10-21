"""P1 verifier-side operand derivation (SR-OD1 plan P1c, plan §3.3; owner ruling P1-MAPPING-DECISION, Form B).

The window verifier reproduces a P1 window's numbers from the stored members and the factor rows. A P1 record is the period
lord in transit, and its value and side are STEP functions of the sky: the dignity of the sign the lord occupies (and, inside
the sign, its mūlatrikoṇa degrees), whether it is combust, and its natural nature (the Moon's pakṣa, Mercury's company). This
module derives those states AGAIN, from scratch, for the verifier:

  * the sky: `position_at(body, t)` only — this module's own sign / degree / elongation / retrograde probes;
  * the reference data: its own L0 SQL (`bg_dignity_reference`, `bg_combustion_orbs`, `bg_graha_naisargika_friendship`);
  * the change instants of each state inside a support: its own bracketed search (`contact_reconstruct._core`, the verifier's
    reconstruction device) — never the builder's stored crossings or its provider;
  * the value table: the factor rows' `category_mapping`, read by this module's own strict parser.

It imports nothing from `window_sweep`, `window_solver` or `p1_operands` (the builder). What it SHARES with the builder, by
design (CLAUDE.md §N.5 — L1 is the authority, a transit rule carries no second convention) are the pure rule functions behind
`gochara_rules.p1_inputs` (combustion arc and orb rule, the strict L0 row validators, the mūlatrikoṇa-range authority check)
and `gochara_rules.nature` (BPHS 3.11 natural nature, Moon pakṣa).

THE RULE IT IMPLEMENTS (ANSWERS.md v2.1 §B.2–B.5, confirmed OWNER-DOCTRINE-CONFIRMED-20261021). The period lord's EFFECTIVE RUNG
at t, in this order (debility is tested before the sign-lord's friendship, or it is never reached):
    COMB  the L1 combustion state is "combust"            (Q6; overrides every rung below)
    EX    in its exaltation sign                          (L0)
    MT    inside its mūlatrikoṇa degrees                  (L0; EX › MT › OWN inside one sign)
    OWN   in its own sign                                 (L0)
    DEB   in its debility sign                            (L0)
    FR / NEU / INI  by the NATURAL friendship of the period lord TOWARD the lord of the sign it occupies — the period lord's own
                    row: `bg_graha_naisargika_friendship WHERE graha = <period lord> AND other_graha = <sign lord>`
                    (BPHS 3.55 / Bṛhat Jātaka II.16-17 and the translator's note at PG69:C1; the relation is not symmetric).
and its natural NATURE (BPHS 3.11: Sun, Mars, Saturn, waning Moon, Rāhu, Ketu malefic; Jupiter, Venus, waxing Moon benefic;
Mercury malefic iff in the same sign as a malefic — "joined" = same sign, Q4). Side and magnitude are then the Form B table
(ANSWERS.md §B.3): the nature gives the default side; the dignity rung — or combustion — overrides it.

THE SIDE RULE (SR-B1-Q3C-JOB; ANSWERS.md v2.1 §B.4, Q3 c), written HERE from the spec text and imported from nowhere — `spec_side` below:
the natural nature sets the DEFAULT side (benefic favourable, malefic adverse); a BENEFIC lord goes ADVERSE "in an inimical sign, in
debility, or combust"; a MALEFIC lord goes FAVOURABLE "in exaltation, mūlatrikoṇa or own sign"; nothing else changes a side. It is the
verifier's own decider, and the factor rows' declared table is CHECKED against it: a table whose side contradicts the rule (a Q3(a)
nature-only table, say) is refused by name, so the verifier is not a rubber stamp for the builder's data. Defined for rule version 1.3.0 only.

NODES (ANSWERS.md §B.5). Rāhu's and Ketu's exaltation and debility come from L0 as seeded. Their mūlatrikoṇa and own signs are
NOT in L0, and the verse puts them in Gemini and Aquarius (Rāhu) and Sagittarius (Ketu): a node there is UNDETERMINED
(`node_dignity_unclassified`), never classified from friendship. The rule lifts for a sign L0 comes to hold as the node's own
sign. Combustion is not applicable to a node (L1 M-19).

WHAT THE VALUE TABLE LOOKS LIKE (I) INTERPRETATION — nothing in the repository fixes the shape of the P1 `category_mapping` yet
(the data PR D2 writes it): this reader accepts, and refuses anything else by name,
    agent_nature            {"benefic": CELL, "malefic": CELL}                       the default side; magnitude 1 by declaration
    dignity_of_transit_sign {"<benefic|malefic>/<EX|MT|OWN|FR|NEU|INI|DEB>": CELL}   the 14 cells of ANSWERS.md §B.3
    combustion              {"combust": CELL, "not_combust": {"value": v}}           combust = the depression rung, adverse
    CELL = {"side": "favourable" | "adverse", "value": v}  with 0 < v ≤ 1 (spec §2.3 inv. 3: a modifier never removes a window)
The value of a record at t is the product of the three factors' values (a combust lord takes the combustion cell and the dignity
row contributes the neutral element 1); the side is `spec_side` of (nature, effective rung), and every declared side is checked against it.

NAMED LIMITS. (1) The change instants are found under the smooth-motion guarantee of `contact_reconstruct` (an excursion shorter
than `MIN_EXCURSION_SECONDS` is not excluded) and located to `BISECT_SECONDS`; two independent locations of one instant therefore
agree within `PEAK_TOLERANCE_SECONDS`. (2) The retrograde flag is the sign of the longitude change over ±`RETRO_PROBE_SECONDS`
(the verifier has positions, not Swiss speeds); it matters only for Mercury and Venus, whose combustion orb is tighter in
retrograde (L1 M-19), and only when the arc lies between their two orbs at a station.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import NamedTuple

from services.gochara_rules import nature as _nature
from services.gochara_rules import p1_inputs as _p1
from services.gochara_rules.p1_inputs import StrictInputError

from . import contact_reconstruct as _cr

GeometryUnavailable = _cr.GeometryUnavailable

#: the P1 soft factors this module derives; `maitri_compound` is RETIRED from P1 (Q7 b) and has no derivation here
P1_FACTORS = ("dignity_of_transit_sign", "combustion", "agent_nature")
RETIRED_FACTORS = ("maitri_compound",)
MAITRI_RETIRED_REASON = "maitri_compound_retired_not_derivable"
MAPPING_NOT_SUPPLIED_REASON = "p1_derivation_not_supplied"

RUNGS = ("EX", "MT", "OWN", "FR", "NEU", "INI", "DEB")
NATURES = ("benefic", "malefic")
SIDES = ("favourable", "adverse")
#: ANSWERS.md §B.5 — the signs the verse (BPHS 47.34-39) reserves for the nodes' mūlatrikoṇa / own signs, which L0 does not hold
NODE_UNCLASSIFIED_SIGNS = {"Rahu": ("Gemini", "Aquarius"), "Ketu": ("Sagittarius",)}
NODE_DIGNITY_UNCLASSIFIED = "node_dignity_unclassified"

SIDE_RULE_VERSION = "1.3.0"
#: ANSWERS.md v2.1 §B.4, quoted: "Benefic → adverse side in an inimical sign, in debility, or combust. Malefic → favourable side in exaltation,
#: mūlatrikoṇa or own sign." The nature's default is the side the lord's own kind gives: benefic favourable, malefic adverse (BPHS 3.11, §B.2).
_SPEC_DEFAULT_SIDE = {"benefic": "favourable", "malefic": "adverse"}
_SPEC_OVERRIDE = {"benefic": ("adverse", ("INI", "DEB", "COMB")), "malefic": ("favourable", ("EX", "MT", "OWN"))}


def spec_side(nature: str, rung: str) -> str:
    """The side of a period lord of natural `nature` at effective `rung` (an entry of RUNGS or "COMB"), read from the spec text above."""
    if nature not in _SPEC_DEFAULT_SIDE or rung not in RUNGS + ("COMB",):
        raise StrictInputError("side_rule_input_unknown", f"{nature}/{rung}")
    side, rungs = _SPEC_OVERRIDE[nature]
    return side if rung in rungs else _SPEC_DEFAULT_SIDE[nature]


RETRO_PROBE_SECONDS = 60.0
PEAK_TOLERANCE_SECONDS = 2.0 * _cr.BISECT_SECONDS

_SQL_DIGNITY = ("SELECT graha, exaltation_sign, debilitation_sign, moolatrikona_sign, moolatrikona_from, moolatrikona_to,"
                " own_signs FROM public.bg_dignity_reference ORDER BY graha")
_COLS_DIGNITY = ("graha", "exaltation_sign", "debilitation_sign", "moolatrikona_sign", "moolatrikona_from",
                 "moolatrikona_to", "own_signs")
_SQL_ORBS = "SELECT graha, orb_degrees, deep_orb_degrees FROM public.bg_combustion_orbs ORDER BY graha"
_COLS_ORBS = ("graha", "orb_degrees", "deep_orb_degrees")
_SQL_NAIS = ("SELECT graha, other_graha, relation FROM public.bg_graha_naisargika_friendship"
             " ORDER BY graha, other_graha")
_COLS_NAIS = ("graha", "other_graha", "relation")


class P1Unknown(NamedTuple):
    """The operand is undeterminable at this instant for the NAMED reason (never a default value)."""
    reason: str


class Evaluation(NamedTuple):
    side: str            # "favourable" | "adverse"
    value: float         # in (0, 1]
    nature: str          # "benefic" | "malefic"
    rung: str            # an entry of RUNGS, or "COMB"
    combust: bool


def _read(conn, sql: str, cols: tuple) -> list[dict]:
    return [r if isinstance(r, dict) else dict(zip(cols, r)) for r in conn.execute(sql).fetchall()]


def needs_p1_check(factor_rows) -> bool:
    """True iff some P1 soft-factor row declares a `category_mapping` (today none does, so nothing is derived and nothing moves)."""
    return any(r.get("factor_id") in P1_FACTORS + RETIRED_FACTORS and r.get("category_mapping") for r in factor_rows)


def _angdiff(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


class P1Check:
    """The sky, the L0 reference rows and the operand rules — no value table (that is `bind`)."""

    def __init__(self, position_at, *, dignity_rows, orb_rows, naisargika_rows):
        self._pos = position_at
        self._lon_cache: dict = {}
        self._orb_rows = list(orb_rows)
        self._problem: dict = {}                      # ("dignity", graha) | "combustion" | "naisargika" -> reason
        self._dignity: dict[str, dict] = {}
        dignity_rows = list(dignity_rows)
        for g in _p1.GRAHAS:
            try:
                self._dignity[g] = _p1.validated_dignity_row(dignity_rows, g)
                _p1.dignity_boundaries(g, dignity_rows)              # raises when L0's range and L1's classifier diverge
            except StrictInputError as e:
                self._problem[("dignity", g)] = e.reason
        try:
            self._orbs = _p1.validated_combustion_orbs(self._orb_rows)
        except StrictInputError as e:
            self._orbs, self._problem["combustion"] = None, e.reason
        try:
            self._nais = _p1.validated_naisargika(naisargika_rows)
        except StrictInputError as e:
            self._nais, self._problem["naisargika"] = None, e.reason

    @classmethod
    def from_conn(cls, conn, position_at) -> "P1Check":
        """The verifier's OWN L0 reads (nothing is handed over by the builder)."""
        return cls(position_at, dignity_rows=_read(conn, _SQL_DIGNITY, _COLS_DIGNITY),
                   orb_rows=_read(conn, _SQL_ORBS, _COLS_ORBS), naisargika_rows=_read(conn, _SQL_NAIS, _COLS_NAIS))

    # ── the sky ──────────────────────────────────────────────────────────────────────────────────────────────────
    def lon(self, body: str, t: datetime) -> float:
        key = (body, t)
        if key not in self._lon_cache:
            if len(self._lon_cache) > 2_000_000:
                self._lon_cache.clear()
            v = self._pos(body, t)
            if v is None:
                raise GeometryUnavailable(f"{body} position undeterminable at {t.isoformat()}")
            v = float(v) % 360.0
            self._lon_cache[key] = 0.0 if v >= 360.0 else v        # a tiny negative longitude rounds to 360.0 under %
        return self._lon_cache[key]

    def sign_of(self, body: str, t: datetime) -> tuple[str, float]:
        lon = self.lon(body, t)
        return _p1.SIGNS[int(lon // 30.0) % 12], lon % 30.0

    def retrograde(self, body: str, t: datetime) -> bool:
        h = timedelta(seconds=RETRO_PROBE_SECONDS)
        return (self.lon(body, t + h) - self.lon(body, t - h) + 180.0) % 360.0 - 180.0 < 0.0

    # ── the operands at t ────────────────────────────────────────────────────────────────────────────────────────
    def dignity_problem(self, graha: str) -> str | None:
        return self._problem.get(("dignity", graha)) or self._problem.get("naisargika")

    def combustion_problem(self, graha: str) -> str | None:
        return None if graha in _p1.NEVER_COMBUST else self._problem.get("combustion")

    def nature_at(self, graha: str, t: datetime) -> str:
        """'benefic' | 'malefic' (BPHS 3.11)."""
        if graha == "Moon":
            n = _nature.agent_nature("Moon", sun_lon=self.lon("sun", t), moon_lon=self.lon("moon", t))
        elif graha == "Mercury":
            n = _nature.agent_nature("Mercury", joined_to_malefic=self._mercury_joined(t))
        else:
            n = _nature.agent_nature(graha)
        if n not in NATURES:
            raise StrictInputError("agent_nature_unresolved", f"{graha}: {n}")
        return n

    def _mercury_joined(self, t: datetime) -> bool:
        merc = self.sign_of("mercury", t)[0]
        if any(self.sign_of(m.lower(), t)[0] == merc for m in sorted(_nature.NATURAL_MALEFICS)):
            return True
        moon_sign = self.sign_of("moon", t)[0]
        return moon_sign == merc and _nature.moon_paksa(self.lon("sun", t), self.lon("moon", t)) == "waning"

    def rung_at(self, graha: str, t: datetime):
        """The dignity rung (EX/MT/OWN/DEB/FR/NEU/INI) the lord holds at t, or `P1Unknown`. Combustion is `combustion_at`'s."""
        problem = self.dignity_problem(graha)
        if problem:
            return P1Unknown(problem)
        ref = self._dignity[graha]
        sign, deg = self.sign_of(graha.lower(), t)
        if sign == ref["exaltation_sign"]:
            return "EX"
        if ref.get("moolatrikona_sign") == sign and ref["moolatrikona_from"] <= deg < ref["moolatrikona_to"]:
            return "MT"
        if sign in ref["own_signs"]:
            return "OWN"
        if sign == ref["debilitation_sign"]:
            return "DEB"
        if sign in NODE_UNCLASSIFIED_SIGNS.get(graha, ()):
            return P1Unknown(NODE_DIGNITY_UNCLASSIFIED)
        lord = _p1._l1().SIGN_LORDS[sign]
        if lord == graha:                       # its own sign, yet L0's `own_signs` does not list it: the row is the problem
            return P1Unknown("own_sign_not_listed_in_l0")
        return {"friend": "FR", "neutral": "NEU", "enemy": "INI"}[self._nais[(graha, lord)]]

    def combustion_at(self, graha: str, t: datetime):
        """L1's combustion state (p1_inputs.combustion_state) at t, or `P1Unknown`; `{'applicable': False}` for Sun / nodes."""
        if graha in _p1.NEVER_COMBUST:
            return {"applicable": False, "is_combust": False}
        problem = self.combustion_problem(graha)
        if problem:
            return P1Unknown(problem)
        body = graha.lower()
        return _p1.combustion_state(graha, self.lon(body, t), self.lon("sun", t), self.retrograde(body, t), self._orb_rows)

    # ── the change instants of each state inside [lo, hi) ────────────────────────────────────────────────────────
    def _search(self, state_at, edge_distance, vmax_dps: float, lo: datetime, hi: datetime) -> list[datetime]:
        return [] if hi <= lo else _cr._core(state_at, edge_distance, vmax_dps, lo, hi)

    def dignity_boundaries(self, graha: str, lo: datetime, hi: datetime) -> list[datetime]:
        if self.dignity_problem(graha):
            return []
        ref, body = self._dignity[graha], graha.lower()
        edges = [0.0, 30.0] + ([ref["moolatrikona_from"], ref["moolatrikona_to"]] if ref.get("moolatrikona_sign") else [])

        def state(t):
            r = self.rung_at(graha, t)
            return r.reason if isinstance(r, P1Unknown) else r

        def edge(t):
            deg = self.lon(body, t) % 30.0
            return min(abs(deg - e) for e in edges)
        return self._search(state, edge, _cr.VMAX_DPS[body], lo, hi)

    def combustion_boundaries(self, graha: str, lo: datetime, hi: datetime) -> list[datetime]:
        if graha in _p1.NEVER_COMBUST or self.combustion_problem(graha):
            return []
        body, orb = graha.lower(), self._orbs[graha]
        arc_of = _p1._l1().compute_combustion_arc

        def edge(t):
            arc = arc_of(self.lon(body, t), self.lon("sun", t))
            return min(abs(arc - orb["orb"]), abs(arc - orb["deep"]))
        return self._search(lambda t: self.combustion_at(graha, t)["is_combust"], edge,
                            _cr.VMAX_DPS[body] + _cr.VMAX_DPS["sun"], lo, hi)

    def nature_boundaries(self, graha: str, lo: datetime, hi: datetime) -> list[datetime]:
        if graha == "Moon":
            def edge(t):
                el = (self.lon("moon", t) - self.lon("sun", t)) % 360.0
                return min(_angdiff(el, 0.0), _angdiff(el, 180.0))
            return self._search(lambda t: self.nature_at("Moon", t), edge,
                                _cr.VMAX_DPS["moon"] + _cr.VMAX_DPS["sun"], lo, hi)
        if graha != "Mercury":
            return []
        bodies = ["mercury", "moon"] + [m.lower() for m in sorted(_nature.NATURAL_MALEFICS)]

        def edge(t):
            """Time (days) to the nearest state edge of ANY operand, so one speed unit (1 deg/day) bounds them all."""
            days = [min(self.lon(b, t) % 30.0, 30.0 - self.lon(b, t) % 30.0) / _cr.VMAX_DPS[b] for b in bodies]
            el = (self.lon("moon", t) - self.lon("sun", t)) % 360.0
            days.append(min(_angdiff(el, 0.0), _angdiff(el, 180.0)) / (_cr.VMAX_DPS["moon"] + _cr.VMAX_DPS["sun"]))
            return min(days)
        return self._search(lambda t: self._mercury_joined(t), edge, 1.0, lo, hi)

    def boundaries(self, graha: str, lo: datetime, hi: datetime) -> list[datetime]:
        """Every instant in (lo, hi) at which ANY of the three P1 states of the lord changes (a superset of where the value or
        the side changes: an extra cut never changes a piece's value)."""
        out = set(self.dignity_boundaries(graha, lo, hi))
        out.update(self.combustion_boundaries(graha, lo, hi))
        out.update(self.nature_boundaries(graha, lo, hi))
        return sorted(c for c in out if lo < c < hi)

    # ── the value table ──────────────────────────────────────────────────────────────────────────────────────────
    def bind(self, factor_rows, event_class: str) -> "P1Binding":
        return P1Binding(self, factor_rows, event_class)


@dataclass(frozen=True)
class _Cell:
    side: str | None
    value: float


def _cell(c, name: str, *, side: str) -> _Cell:
    """side='required' | 'forbidden'."""
    if not isinstance(c, dict):
        raise StrictInputError("category_mapping_cell_invalid", f"{name}: {c!r}")
    v = c.get("value")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
        raise StrictInputError("category_mapping_cell_invalid", f"{name}: value {v!r}")
    if not 0.0 < float(v) <= 1.0:
        raise StrictInputError("category_mapping_value_out_of_range", f"{name}: {v!r}")
    s = c.get("side")
    if side == "required" and s not in SIDES:
        raise StrictInputError("category_mapping_cell_invalid", f"{name}: side {s!r}")
    if side == "forbidden" and s is not None:
        raise StrictInputError("category_mapping_cell_invalid", f"{name}: a non-combust state cannot carry a side ({s!r})")
    return _Cell(s, float(v))


def _require_keys(mapping, keys, factor: str) -> dict:
    if not isinstance(mapping, dict) or set(mapping) != set(keys):
        raise StrictInputError("category_mapping_incomplete",
                               f"{factor}: expected exactly {sorted(keys)}, got {sorted(mapping) if isinstance(mapping, dict) else mapping!r}")
    return mapping


class P1Binding:
    """The check bound to one path's factor rows and one event class: values, sides, channels, unknown reasons and change
    instants of a stored record (a dict with at least `agent`)."""

    def __init__(self, check: P1Check, factor_rows, event_class: str):
        self.check, self.event_class = check, event_class
        by_id = {r["factor_id"]: r for r in factor_rows if r.get("factor_id") in P1_FACTORS}
        self._row_problem: dict[str, str] = {}
        self._nature = self._dignity = self._comb = None
        for fid, parse in (("agent_nature", self._parse_nature), ("dignity_of_transit_sign", self._parse_dignity),
                           ("combustion", self._parse_combustion)):
            try:
                if fid not in by_id or not by_id[fid].get("category_mapping"):
                    raise StrictInputError("p1_factor_row_without_category_mapping", fid)
                if by_id[fid].get("rule_version") != SIDE_RULE_VERSION:     # the side rule is defined for 1.3.0 only
                    raise StrictInputError("side_rule_undefined_for_version", f"{fid}@{by_id[fid].get('rule_version')!r}")
                parse(by_id[fid]["category_mapping"])
            except StrictInputError as e:
                self._row_problem[fid] = e.reason
        if self._row_problem:      # the three rows are one table (ANSWERS.md §B.2): one unreadable row spoils all three
            first = sorted(self._row_problem.values())[0]
            self._row_problem = {fid: self._row_problem.get(fid, first) for fid in by_id or P1_FACTORS}
        self._eval_cache: dict = {}

    def _parse_nature(self, m):
        m = _require_keys(m, NATURES, "agent_nature")
        self._nature = {n: _cell(m[n], f"agent_nature/{n}", side="required") for n in NATURES}
        for n in NATURES:
            if self._nature[n].side != _SPEC_DEFAULT_SIDE[n]:       # the agent_nature row declares the DEFAULT side
                raise StrictInputError("category_mapping_side_contradicts_q3c", f"agent_nature/{n}: {self._nature[n].side!r}")

    def _parse_dignity(self, m):
        m = _require_keys(m, [f"{n}/{r}" for n in NATURES for r in RUNGS], "dignity_of_transit_sign")
        self._dignity = {k: _cell(v, f"dignity_of_transit_sign/{k}", side="required") for k, v in m.items()}
        for k, cell in self._dignity.items():
            nature, rung = k.split("/")
            if cell.side != spec_side(nature, rung):
                raise StrictInputError("category_mapping_side_contradicts_q3c", f"dignity_of_transit_sign/{k}: {cell.side!r}, the spec says {spec_side(nature, rung)!r}")

    def _parse_combustion(self, m):
        m = _require_keys(m, ("combust", "not_combust"), "combustion")
        self._comb = {"combust": _cell(m["combust"], "combustion/combust", side="required"),
                      "not_combust": _cell(m["not_combust"], "combustion/not_combust", side="forbidden")}
        for n in NATURES:         # one combust cell serves both natures: the spec puts a combust lord on the adverse side whichever its kind
            if self._comb["combust"].side != spec_side(n, "COMB"):
                raise StrictInputError("category_mapping_side_contradicts_q3c", f"combustion/combust: {self._comb['combust'].side!r} for a {n} lord")

    def record_problem(self, factor_id: str, rec: dict) -> str | None:
        """The named reason this factor cannot be derived for this record at all (a mapping the reader refuses, or an L0 row the
        lord needs that is missing / divergent), else None. Static: it does not depend on t."""
        if factor_id in self._row_problem:
            return self._row_problem[factor_id]
        graha = rec["agent"].title()
        if factor_id == "dignity_of_transit_sign":
            return self.check.dignity_problem(graha)
        if factor_id == "combustion":
            return self.check.combustion_problem(graha)
        return None

    def evaluate(self, rec: dict, t: datetime):
        """`Evaluation` of the record at t, or `P1Unknown` (a named per-instant reason)."""
        key = (rec["agent"], t)
        if key not in self._eval_cache:
            if len(self._eval_cache) > 500_000:
                self._eval_cache.clear()
            self._eval_cache[key] = self._evaluate(rec["agent"].title(), t)
        return self._eval_cache[key]

    def _evaluate(self, graha: str, t: datetime):
        chk = self.check
        nat = chk.nature_at(graha, t)
        cell_n = self._nature[nat]
        comb = chk.combustion_at(graha, t)
        if isinstance(comb, P1Unknown):
            return comb
        if comb["applicable"] and comb["is_combust"]:
            cell = self._comb["combust"]
            return Evaluation(spec_side(nat, "COMB"), cell_n.value * cell.value, nat, "COMB", True)
        rung = chk.rung_at(graha, t)
        if isinstance(rung, P1Unknown):
            return rung
        cell = self._dignity[f"{nat}/{rung}"]
        value = cell_n.value * cell.value * (self._comb["not_combust"].value if comb["applicable"] else 1.0)
        return Evaluation(spec_side(nat, rung), value, nat, rung, False)

    def value_at(self, rec: dict, t: datetime):
        e = self.evaluate(rec, t)
        return e if isinstance(e, P1Unknown) else e.value

    def channel_at(self, rec: dict, t: datetime):
        """The verifier's channel name at t (`score.channel_for` of the side and the class), or `P1Unknown`."""
        from services.gochara_rules.score import channel_for
        e = self.evaluate(rec, t)
        return e if isinstance(e, P1Unknown) else channel_for(e.side, self.event_class)

    def unknown_reason(self, rec: dict, t: datetime) -> str | None:
        e = self.evaluate(rec, t)
        return e.reason if isinstance(e, P1Unknown) else None

    def channel_boundaries(self, rec: dict, lo: datetime, hi: datetime) -> list[datetime]:
        """The record's change instants inside [lo, hi): where its value OR side may change (the verifier cuts its pieces here)."""
        return self.check.boundaries(rec["agent"].title(), lo, hi)


__all__ = ["Evaluation", "MAITRI_RETIRED_REASON", "MAPPING_NOT_SUPPLIED_REASON", "NODE_DIGNITY_UNCLASSIFIED", "P1Binding", "P1Check",
           "P1_FACTORS", "P1Unknown", "PEAK_TOLERANCE_SECONDS", "RETIRED_FACTORS", "RUNGS", "SIDE_RULE_VERSION", "needs_p1_check", "spec_side"]
