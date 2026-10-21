"""P1 operand sources, step-boundary providers and L0 loaders (SR-OD1 plan §3.3, task P1a).

P1 judges the PERIOD LORD at every instant of a record's support. Its three state factors — dignity of the transit sign, combustion and
(retired from the new rule version by the owner, P1-MAPPING-DECISION Q7 b) the pañcadhā maitrī — are step functions of the sky. This module
supplies, per factor and per period lord:

  * the STATE at t (`LordState`: the effective rung, the L1 combustion state, the natural friendship) — computed by CALLING L1's pure rules
    through the strict `gochara_rules.p1_inputs` wrappers (CLAUDE.md §N.5: the rule authority is L1; this module re-implements none), over
    L0 rows handed in by the loaders below (no fallback loader, no literal default);
  * an `OperandSource` (`window_sweep`, W0) whose `boundaries` are the COMPLETE instants at which that factor's state changes inside a
    support, located to a microsecond — the sweep solves the objective piecewise between them (H2);
  * the L0 content digests that bind the three reference tables into the manifest's input vector.

WHAT IS NOT HERE: a value of its own. The category → value rule is DATA handed in: either per-factor `rules` (a rung → value table), or — the
owner's Form B table, D2 — `form_b`, the (natural nature, rung) → (side, value) mapping the path's three Form B rows declare together
(`p1_valence.mapping_from_rows`, the registry's P1@1.3.0). Under `form_b` the lord's side and value per instant are P1b's
(`p1_nature_operands.P1LordValence`), fed THIS module's `combust_at` and `rung_boundaries`; the side is the `agent_nature` source's,
the value the dignity source's, and combustion is the declared neutral element 1.0 (the COMB rung is a cell of the table). With
neither, the source carries no `value_at` and the sweep keeps its named blank `value_mapping_undeclared`.

THE EFFECTIVE RUNG (owner ruling P1-MAPPING-DECISION = ANSWERS.md v2.1 §B.2; the order matters): COMB > EX > MT > OWN > DEB > FR/NEU/INI.
  COMB  the L1 combustion state is combust (Q6; mapping only — SR-Q6-L1: the state and the orbs are L1 facts, inherited, never recomputed);
        the nodes and the Sun are DECLARED not applicable (L1 M-19; BPHS 7.28-29 translator's note PG99:C1);
  EX/MT/OWN/DEB  from L1's `dignity_d1_from_sign` over the validated L0 `bg_dignity_reference` row. L1 tests the mūlatrikoṇa range BEFORE
        the exaltation sign; the owner's precedence is EX before MT ("the Moon's Taurus and Mercury's Virgo read as exaltation throughout"),
        so an L1 `moolatrikona` in the exaltation sign is read EX (disclosed by the ruling, [I]);
  FR/NEU/INI  the NATURAL friendship of the PERIOD LORD toward the lord of the sign it occupies, read from the period lord's own table:
        L0 `bg_graha_naisargika_friendship WHERE graha = <period lord> AND other_graha = <sign lord>` (BJ II.16-17 translator's note
        brihat_jataka:PG69:C1: "the particular planet's table and not the table of the ruler of the house where he is in").
        L1's own embedded friend/enemy labels are NOT used: L0 governs (ANSWERS §B.2 step 6).
  Rāhu/Ketu: EX and DEB from L0; their mūlatrikoṇa and own signs are not in L0 (ANSWERS §B.5, open for the L0 owner) — a node in a sign the
        served verse reserves for them (BPHS 47.34-39, bphs:PG573:C2-PG574:C1) is UNQUALIFIED `node_dignity_unclassified`, never a guess;
        the verse's variant own signs (Virgo / Pisces) are classified by friendship and carry the disclosure
        `node_own_sign_variant_unresolved`; a rung that rests on one of the five pairs where L0 and the translator's note
        (bphs:PG40:C1) disagree carries `node_friendship_source_disputed`.

BOUNDARIES (all located by the VMAX-bracketed device of `contact_reconstruct._core` at the STATE floor `STATE_MIN_EXCURSION_SECONDS` (1 s,
SR-H2-1S) — `STATE_NAMED_LIMIT` applies: smooth motion with speed at most `VMAX_DPS`, every state interval of at least 1 s found, a shorter one
not excluded — then bisected to a microsecond, because the device stops at 1 s and the solver needs an exact step. A change instant is the
FIRST microsecond of the new state: the new state owns it, half-open [change, next change), so `state(b - 1 µs)` is the old state and
`state(b)` the new one): sign ingress of the lord; its in-sign mūlatrikoṇa degree edges (N-2); the roots of Sun-lord elongation = orb and
= deep orb; and, for the two grahas L1 gives a retrograde orb (Mercury, Venus), the stations at which the orb regime flips (N-8). The station
instants are the substrate's stored ones, handed in by the store; the retrograde state at t is their parity, anchored by a probe a safe distance
from a station (never by a finite difference AT a station, where the speed is ~0).

L0 DIGESTS (`load_dignity_reference`, `load_combustion_orbs`, `load_naisargika`): each returns the validated rows and `content_digest` =
sha256 of the canonical JSON (sorted keys, no whitespace, UTF-8) of the rows the build CONSUMES, normalised to arrays in a total order:
  bg_dignity_reference               [graha, exaltation_sign, debilitation_sign, moolatrikona_sign|null, moolatrikona_from|null,
                                      moolatrikona_to|null, own_signs[]]            ORDER BY graha
  bg_combustion_orbs                 [graha, orb_degrees, deep_orb_degrees]         ORDER BY graha
  bg_graha_naisargika_friendship     [graha, other_graha, relation]                 ORDER BY graha, other_graha
with every NUMERIC rendered as its plain decimal text without trailing zeros (`15.0` and `15` are one value: `trim_scale(x)::text`). Surrogate
ids, citations and notes are not consumed and do not move the digest.
"""
from __future__ import annotations

import bisect
import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Callable, Iterable, Mapping, Sequence

from services.gochara_rules import p1_inputs as p1
from services.gochara_rules import p1_valence as pv

from . import p1_nature_operands as nat
from .contact_reconstruct import (STATE_MIN_EXCURSION_SECONDS, STATE_NAMED_LIMIT, VMAX_DPS, _angdiff, _cell, _core,
                                  _dist_to_cell_edge)
from .window_sweep import OperandSource, SweepRecord, graha_title

#: the named limit of every boundary list this module produces (verbatim, SR-H2-1S)
NAMED_LIMIT = STATE_NAMED_LIMIT

# ── the vocabulary ───────────────────────────────────────────────────────────────────────────────────────────

RUNGS = ("COMB", "EX", "MT", "OWN", "DEB", "FR", "NEU", "INI")
_FRIENDSHIP_RUNG = {"friend": "FR", "neutral": "NEU", "enemy": "INI"}
_L1_SIGN_RUNG = {"exalted": "EX", "own": "OWN", "debilitated": "DEB"}

FACTOR_DIGNITY = "dignity_of_transit_sign"
FACTOR_COMBUSTION = "combustion"
FACTOR_MAITRI = "maitri_compound"
FACTOR_NATURE = "agent_nature"
SOURCE_FACTORS = (FACTOR_DIGNITY, FACTOR_COMBUSTION, FACTOR_MAITRI)

NODES = ("Rahu", "Ketu")
#: ANSWERS.md v2.1 §B.5 from BPHS 47.34-39 (bphs:PG573:C2-PG574:C1): the signs the served verse gives the nodes as mūlatrikoṇa / own and that L0
#: does not yet hold. A BLANK rule, not a value: while L0 carries no own signs for the node, a node in one of these signs is unclassified.
#: (Ketu's Scorpio is its verse-own sign and its exaltation sign in L0: EX wins by precedence, so it is not listed.)
NODE_RESERVED_SIGNS = {"Rahu": ("Gemini", "Aquarius"), "Ketu": ("Sagittarius",)}
#: the verse's "some learned" variant own signs (Virgo for Rāhu, Pisces for Ketu): an L0 decision, classified by friendship meanwhile
NODE_VARIANT_OWN_SIGNS = {"Rahu": "Virgo", "Ketu": "Pisces"}
#: the five (node, sign-lord) pairs where L0 and the translator's note under BPHS 3.55 (bphs:PG40:C1) disagree
NODE_FRIENDSHIP_DISPUTED = frozenset({("Rahu", "Mercury"), ("Rahu", "Mars"), ("Rahu", "Jupiter"), ("Ketu", "Sun"), ("Ketu", "Moon")})

_STATION_PROBE_DAYS = 2.0          # the direction of motion is read this far from a station (min station spacing is 19.7 d)
_DIRECTION_HALF_WINDOW_DAYS = 0.01
_REFINE_TO = timedelta(microseconds=1)
_MEMO_CAP = 200_000


class RetrogradeUnestablished(p1.StrictInputError):
    """A Mercury/Venus period lord's retrograde state cannot be established (no stored stations handed in): the L1 orb regime is unknown."""

    def __init__(self, detail: str = ""):
        super().__init__("retrograde_state_unestablished", detail)


# ── L0 loaders ───────────────────────────────────────────────────────────────────────────────────────────────

DIGNITY_SQL = ("SELECT graha, exaltation_sign, debilitation_sign, moolatrikona_sign, moolatrikona_from, moolatrikona_to, own_signs"
               " FROM public.bg_dignity_reference ORDER BY graha")
COMBUSTION_SQL = "SELECT graha, orb_degrees, deep_orb_degrees FROM public.bg_combustion_orbs ORDER BY graha"
NAISARGIKA_SQL = ("SELECT graha, other_graha, relation FROM public.bg_graha_naisargika_friendship"
                  " ORDER BY graha, other_graha")
_COLUMNS = {
    "bg_dignity_reference": ("graha", "exaltation_sign", "debilitation_sign", "moolatrikona_sign", "moolatrikona_from",
                             "moolatrikona_to", "own_signs"),
    "bg_combustion_orbs": ("graha", "orb_degrees", "deep_orb_degrees"),
    "bg_graha_naisargika_friendship": ("graha", "other_graha", "relation"),
}


@dataclass(frozen=True)
class L0Table:
    """A consumed L0 authority: its validated rows (dicts) and the content digest that binds it into the input vector."""
    asset: str
    rows: tuple
    content_digest: str


def _dec(x):
    """A NUMERIC as plain decimal text without trailing zeros (None stays None): `15`, `15.0` and Decimal('15.00') are one value."""
    if x is None:
        return None
    d = Decimal(str(x)).normalize()
    return format(d, "f")


def _dicts(asset: str, raw: Iterable) -> list[dict]:
    cols = _COLUMNS[asset]
    out = []
    for r in raw:
        if isinstance(r, Mapping):
            out.append({c: r.get(c) for c in cols})
        else:
            if len(r) != len(cols):
                raise p1.StrictInputError("l0_row_shape", f"{asset}: {len(r)} column(s), expected {cols}")
            out.append(dict(zip(cols, r)))
    return out


def _digest(preimage: list) -> str:
    text = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dignity_reference_from_rows(raw: Iterable) -> L0Table:
    """Validate and bind `bg_dignity_reference`: a complete row for each of the nine grahas, and — for every graha with a mūlatrikoṇa range —
    L0's range EQUAL to the range L1's classifier actually uses (a divergence is refused by `p1.dignity_boundaries`, never reconciled)."""
    rows = _dicts("bg_dignity_reference", raw)
    for g in p1.GRAHAS:
        p1.validated_dignity_row(rows, g)
        p1.dignity_boundaries(g, rows)
    extra = sorted({r["graha"] for r in rows} - set(p1.GRAHAS))
    if extra:
        raise p1.StrictInputError("dignity_row_graha_unknown", f"{extra}")
    pre = [[r["graha"], r["exaltation_sign"], r["debilitation_sign"], r["moolatrikona_sign"], _dec(r["moolatrikona_from"]),
            _dec(r["moolatrikona_to"]), list(r["own_signs"] or [])] for r in sorted(rows, key=lambda r: r["graha"])]
    return L0Table("bg_dignity_reference", tuple(rows), _digest(pre))


def combustion_orbs_from_rows(raw: Iterable) -> L0Table:
    rows = _dicts("bg_combustion_orbs", raw)
    p1.validated_combustion_orbs(rows)
    pre = [[r["graha"], _dec(r["orb_degrees"]), _dec(r["deep_orb_degrees"])] for r in sorted(rows, key=lambda r: r["graha"])]
    return L0Table("bg_combustion_orbs", tuple(rows), _digest(pre))


def naisargika_from_rows(raw: Iterable) -> L0Table:
    rows = _dicts("bg_graha_naisargika_friendship", raw)
    p1.validated_naisargika(rows)
    pre = [[r["graha"], r["other_graha"], r["relation"]] for r in sorted(rows, key=lambda r: (r["graha"], r["other_graha"]))]
    return L0Table("bg_graha_naisargika_friendship", tuple(rows), _digest(pre))


def _load(cursor, sql: str, build):
    cursor.execute(sql)
    return build(cursor.fetchall())


def load_dignity_reference(cursor) -> L0Table:
    """Read through a DB-API cursor (the caller owns the connection and the transaction)."""
    return _load(cursor, DIGNITY_SQL, dignity_reference_from_rows)


def load_combustion_orbs(cursor) -> L0Table:
    return _load(cursor, COMBUSTION_SQL, combustion_orbs_from_rows)


def load_naisargika(cursor) -> L0Table:
    return _load(cursor, NAISARGIKA_SQL, naisargika_from_rows)


@dataclass(frozen=True)
class P1L0:
    """The three L0 authorities P1 consumes, each validated and digested."""
    dignity: L0Table
    combustion: L0Table
    naisargika: L0Table

    def digests(self) -> dict:
        return {t.asset: t.content_digest for t in (self.dignity, self.combustion, self.naisargika)}


def load_p1_l0(cursor) -> P1L0:
    return P1L0(load_dignity_reference(cursor), load_combustion_orbs(cursor), load_naisargika(cursor))


# ── the state of the period lord at an instant ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LordState:
    """What P1's factors read about the period lord at `t`. `rung` is the EFFECTIVE rung (None = undeterminable, with `unknown_reason`);
    `dignity_rung` is the rung ignoring combustion; `combust` is L1's state (None = not applicable or not established, see
    `combustion_applicable` / `combustion_unknown_reason`)."""
    anchor: str
    t: datetime
    sign: str | None = None
    degree: float | None = None
    rung: str | None = None
    dignity_rung: str | None = None
    unknown_reason: str | None = None
    combustion_applicable: bool = True
    combust: bool | None = None
    combustion_unknown_reason: str | None = None
    sign_lord: str | None = None
    friendship: str | None = None
    disclosures: tuple = ()
    maitri: str | None = None            # the pañcadhā category (or `own_sign`); set only for the maitrī source


#: a value rule: the category the factor reads → a value in [0,1] (None = the rule has no value for this state)
ValueRule = Callable[[LordState], "float | None"]


def category_rule(mapping: Mapping, key: Callable[[LordState], object] = lambda s: s.rung) -> ValueRule:
    """A value rule from a `category → value` table. Every value must be a real in [0,1] (checked HERE, at construction); a state whose
    category the table does not name yields None (a named blank), never a default."""
    for k, v in mapping.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0.0 <= float(v) <= 1.0:
            raise ValueError(f"value rule: category {k!r} maps to {v!r}, outside the declared [0,1] range")
    table = {k: float(v) for k, v in mapping.items()}

    def rule(state: LordState):
        k = key(state)
        return None if k is None else table.get(k)
    return rule


def _l1():
    return p1._l1()


class _View:
    """One period lord's sky over a run: position / state memos and the three boundary providers. `stations` = the stored station instants of
    the lord (Mercury / Venus only), sorted; None = not handed in."""

    def __init__(self, ops: "P1Operands", anchor: str, stations: Sequence[datetime] | None):
        self.ops, self.anchor = ops, anchor
        self.stations = None if stations is None else tuple(sorted(stations))
        self._states: dict[datetime, LordState] = {}
        self._retro_probe: dict = {}
        self._bounds: dict = {}

    # ── retrograde (Mercury / Venus) ──
    @property
    def retro_matters(self) -> bool:
        return self.anchor in _l1()._RETROGRADE_COMBUSTION_GRAHAS

    def retrograde_at(self, t: datetime) -> bool:
        if not self.stations:
            raise RetrogradeUnestablished(f"{self.anchor}: no stored stations handed in")
        i = bisect.bisect_right(self.stations, t)
        if i == len(self.stations):
            probe = self.stations[-1] + timedelta(days=_STATION_PROBE_DAYS)
        elif i == 0:
            probe = self.stations[0] - timedelta(days=_STATION_PROBE_DAYS)
        else:
            a, b = self.stations[i - 1], self.stations[i]
            probe = a + min(timedelta(days=_STATION_PROBE_DAYS), (b - a) / 2)
        if probe not in self._retro_probe:
            h = timedelta(days=_DIRECTION_HALF_WINDOW_DAYS)
            d = (self.ops.lon(self.anchor, probe + h) - self.ops.lon(self.anchor, probe - h) + 180.0) % 360.0 - 180.0
            if d == 0.0:
                raise RetrogradeUnestablished(f"{self.anchor}: no motion at the direction probe {probe.isoformat()}")
            self._retro_probe[probe] = d < 0
        return self._retro_probe[probe]

    # ── the state ──
    def state(self, t: datetime) -> LordState:
        s = self._states.get(t)
        if s is None:
            if len(self._states) >= _MEMO_CAP:
                self._states.clear()
            s = self._states[t] = self._compute(t)
        return s

    def _combustion(self, t: datetime):
        """(applicable, is_combust|None, reason|None): L1's combustion state of the lord at t (the Sun and the nodes: declared not applicable)."""
        g = self.anchor
        if g not in p1.COMBUSTIBLE:
            return False, None, None
        try:
            retro = self.retrograde_at(t) if self.retro_matters else False
            return True, p1.combustion_state(g, self.ops.lon(g, t), self.ops.lon("Sun", t), retro, self.ops.l0.combustion.rows)["is_combust"], None
        except p1.StrictInputError as exc:
            return True, None, exc.reason

    def _combust_flag(self, t: datetime):
        return self._combustion(t)[1]

    def _compute(self, t: datetime) -> LordState:
        ops, g = self.ops, self.anchor
        try:
            lon = ops.lon(g, t)
        except p1.StrictInputError as exc:
            return LordState(anchor=g, t=t, unknown_reason=exc.reason, combustion_unknown_reason=exc.reason)
        sign, degree = p1.SIGNS[int(lon // 30.0) % 12], lon % 30.0
        applicable, combust, c_reason = self._combustion(t)
        rung, disclosures, d_reason, lord, rel = None, (), None, None, None
        try:                  # L1's classifier, the owner's precedence, L0's friendship
            rung, disclosures, lord, rel = ops.dignity_rung(g, sign, degree)
        except p1.StrictInputError as exc:
            d_reason = exc.reason
        common = dict(anchor=g, t=t, sign=sign, degree=degree, dignity_rung=rung, combustion_applicable=applicable, combust=combust,
                      sign_lord=lord, friendship=rel, disclosures=disclosures)
        if combust:                                              # COMB overrides every rung below it (XX.30 tail)
            return LordState(rung="COMB", **common)
        if applicable and combust is None:                       # the combustion state is undeterminable ⇒ the effective rung is
            return LordState(rung=None, unknown_reason=c_reason, combustion_unknown_reason=c_reason, **common)
        return LordState(rung=rung, unknown_reason=d_reason, **common)

    # ── boundaries ──
    def _memo(self, kind: str, lo: datetime, hi: datetime, build) -> list[datetime]:
        key = (kind, lo, hi)
        if key not in self._bounds:
            if len(self._bounds) >= _MEMO_CAP:
                self._bounds.clear()
            self._bounds[key] = build() if hi > lo else []
        return self._bounds[key]

    def ingress(self, lo: datetime, hi: datetime) -> list[datetime]:
        return self._memo("ingress", lo, hi, lambda: self.ops.ingress(self.anchor, lo, hi))

    def mt_edges(self, lo: datetime, hi: datetime) -> list[datetime]:
        return self._memo("mt", lo, hi, lambda: self.ops.mt_edges(self.anchor, lo, hi))

    def combustion_changes(self, lo: datetime, hi: datetime) -> list[datetime]:
        def build():
            if self.anchor not in p1.COMBUSTIBLE:
                return []
            found = self.ops.elongation_changes(self.anchor, lo, hi, state_at=self._combust_flag)
            if self.retro_matters and self.stations:
                found = sorted(set(found) | {s for s in self.stations if lo < s < hi})
            return found
        return self._memo("combustion", lo, hi, build)

    def rung_boundaries(self, lo: datetime, hi: datetime) -> list[datetime]:
        return sorted(set(self.ingress(lo, hi)) | set(self.mt_edges(lo, hi)) | set(self.combustion_changes(lo, hi)))

    def maitri_boundaries(self, lo: datetime, hi: datetime) -> list[datetime]:
        """Ingress of the lord and of the lord of the sign it occupies, over each stretch of that sign."""
        own = self.ingress(lo, hi)
        cuts = [lo, *own, hi]
        out = set(own)
        for a, b in zip(cuts, cuts[1:]):
            if b <= a:
                continue
            mid = a + (b - a) / 2
            sign = self.state(mid).sign
            if sign is None:
                raise p1.StrictInputError("position_undeterminable", f"{self.anchor} @ {mid.isoformat()}")
            lord = _l1().SIGN_LORDS[sign]
            out.update(self.ops.view(lord, None).ingress(a, b))
        return sorted(out)

    # ── maitrī (pañcadhā; retired from the new rule version, kept for the factor sets that still carry it) ──
    def maitri(self, t: datetime):
        """(state-like dict, None) or (None, reason): the pañcadhā category of the lord towards its sign lord, by L1's rules. Nodes are
        unqualified (nature.py: node maitrī stays unqualified pending a text-located rule)."""
        g = self.anchor
        if g in NODES:
            return None, "node_maitri_unqualified"
        try:
            sign = self.state(t).sign
            if sign is None:
                return None, "position_undeterminable"
            lord = _l1().SIGN_LORDS[sign]
            lord_sign = self.ops.view(lord, None).state(t).sign
            if lord_sign is None:
                return None, "position_undeterminable"
            return p1.maitri_category(g, sign, lord_sign, self.ops.l0.naisargika.rows), None
        except p1.StrictInputError as exc:
            return None, exc.reason


class P1Operands:
    """P1's operand sources over L0 rows and the pinned ephemeris. `position_at(Title-case graha, t) -> sidereal longitude` is the writer's
    Swiss probe. `rules` = `{factor_id: ValueRule}`; absent ⇒ that factor carries no value (a named blank in the sweep)."""

    def __init__(self, l0: P1L0, position_at: Callable[[str, datetime], float], *, rules: Mapping[str, ValueRule] | None = None,
                 form_b: "pv.SideValueMapping | None" = None):
        if rules and form_b is not None:
            raise ValueError("P1Operands: per-factor value rules and the Form B mapping are two ways to declare one table — pass one")
        self.l0, self._position_at, self.rules, self.form_b = l0, position_at, dict(rules or {}), form_b
        self._lord_rules: dict[str, "pv.LordRungRules"] = {}
        self._lon: dict[tuple, float] = {}
        self._views: dict[tuple, _View] = {}
        self._friend = p1.validated_naisargika(l0.naisargika.rows)
        self._ref = {g: p1.validated_dignity_row(l0.dignity.rows, g) for g in p1.GRAHAS}

    # ── the sky ──
    def lon(self, graha: str, t: datetime) -> float:
        key = (graha, t)
        v = self._lon.get(key)
        if v is None:
            raw = self._position_at(graha, t)
            if raw is None or not isinstance(raw, (int, float)) or isinstance(raw, bool) or raw != raw or raw in (float("inf"), float("-inf")):
                raise p1.StrictInputError("position_undeterminable", f"{graha} @ {t.isoformat()}: {raw!r}")
            if len(self._lon) >= _MEMO_CAP:
                self._lon.clear()
            v = float(raw) % 360.0
            v = self._lon[key] = 0.0 if v >= 360.0 else v                  # (-1e-20) % 360.0 is 360.0 in floating point
        return v

    def view(self, anchor: str, stations: Sequence[datetime] | None) -> _View:
        p1._graha(anchor)
        key = (anchor, id(stations))
        v = self._views.get(key)
        if v is None:
            v = self._views[key] = _View(self, anchor, stations)
            v._source = stations                 # keeps the caller's list alive, so its id() cannot be reused under this key
        return v

    # ── the rung ──
    def dignity_rung(self, graha: str, sign: str, degree: float):
        """(rung, disclosures, sign lord, friendship) by the owner's order EX > MT > OWN > DEB > FR/NEU/INI over L1's classifier."""
        l1 = _l1()
        cat = p1.dignity_category(graha, sign, degree, self.l0.dignity.rows)
        ref = self._ref[graha]
        lord = l1.SIGN_LORDS[sign]
        if cat == "moolatrikona":
            return ("EX" if sign == ref["exaltation_sign"] else "MT"), (), lord, None
        if cat in _L1_SIGN_RUNG:
            return _L1_SIGN_RUNG[cat], (), lord, None
        disclosures = ()
        if graha in NODES:
            if not ref["own_signs"] and sign in NODE_RESERVED_SIGNS[graha]:
                raise p1.StrictInputError("node_dignity_unclassified", f"{graha} in {sign}: the verse's mūlatrikoṇa/own sign, not in L0")
            if sign == NODE_VARIANT_OWN_SIGNS[graha]:
                disclosures += ("node_own_sign_variant_unresolved",)
            if (graha, lord) in NODE_FRIENDSHIP_DISPUTED:
                disclosures += ("node_friendship_source_disputed",)
        if lord == graha:
            raise p1.StrictInputError("sign_lord_is_anchor_outside_own_signs", f"{graha} in {sign}")
        rel = self._friend[(graha, lord)]                       # THE PERIOD LORD'S OWN TABLE: graha = lord, other_graha = sign lord
        return _FRIENDSHIP_RUNG[rel], disclosures, lord, rel

    # ── boundary devices ──
    def _refine(self, state_at, a: datetime, b: datetime) -> datetime:
        """The first microsecond at which `state_at` differs from its value at `a` (`state_at(a) != state_at(b)` on entry)."""
        base = state_at(a)
        while b - a > _REFINE_TO:
            m = a + (b - a) / 2
            if m == a:
                break
            if state_at(m) == base:
                a = m
            else:
                b = m
        return b

    def _exact(self, state_at, edge_distance, vmax: float, lo: datetime, hi: datetime) -> list[datetime]:
        out = []
        for b in _core(state_at, edge_distance, vmax, lo, hi, min_excursion_seconds=STATE_MIN_EXCURSION_SECONDS):
            a = max(lo, b - timedelta(seconds=1.001))
            out.append(self._refine(state_at, a, b) if state_at(a) != state_at(b) else b)
        return out

    def ingress(self, graha: str, lo: datetime, hi: datetime) -> list[datetime]:
        return self._exact(lambda t: _cell(self.lon(graha, t), 30.0), lambda t: _dist_to_cell_edge(self.lon(graha, t), 30.0),
                           VMAX_DPS[graha.lower()], lo, hi)

    def mt_edges(self, graha: str, lo: datetime, hi: datetime) -> list[datetime]:
        ref = self._ref[graha]
        if ref.get("moolatrikona_sign") is None:
            return []
        base = p1.SIGNS.index(ref["moolatrikona_sign"]) * 30.0
        a, b = base + ref["moolatrikona_from"], base + ref["moolatrikona_to"]
        inside = lambda t: (self.lon(graha, t) - a) % 360.0 < (b - a)                       # noqa: E731
        edge = lambda t: min(_angdiff(self.lon(graha, t), a), _angdiff(self.lon(graha, t), b % 360.0))     # noqa: E731
        return self._exact(inside, edge, VMAX_DPS[graha.lower()], lo, hi)

    def elongation_changes(self, graha: str, lo: datetime, hi: datetime, *, state_at) -> list[datetime]:
        """Changes of the L1 combustion state: roots of the Sun-lord arc = orb and = deep orb (an arc is at most 180°; speeds add)."""
        orbs = p1.validated_combustion_orbs(self.l0.combustion.rows)[graha]
        l1 = _l1()
        arc = lambda t: l1.compute_combustion_arc(self.lon(graha, t), self.lon("Sun", t))      # noqa: E731
        edge = lambda t: min(abs(arc(t) - orbs["orb"]), abs(arc(t) - orbs["deep"]))              # noqa: E731
        return self._exact(state_at, edge, VMAX_DPS[graha.lower()] + VMAX_DPS["sun"], lo, hi)

    @staticmethod
    def needs_stations(anchor: str) -> bool:
        """Does the period lord's combustion depend on its retrograde regime (Mercury, Venus: L1's retrograde orb)?"""
        return anchor in _l1()._RETROGRADE_COMBUSTION_GRAHAS

    # ── the OperandSources ──
    def _form_b_sources(self, anchor: str, v: "_View", done: bool, event_class: str | None) -> dict[str, OperandSource]:
        """The Form B sources (D2): side and value per instant from P1b's `P1LordValence`, over THIS module's combustion state and rung
        boundaries. Complete only when the store's coverage says so (the nature list's completeness is P1b's own, under its named limit)."""
        if event_class is None:
            raise p1.StrictInputError("event_class_missing", "the Form B side is class-relative (spec §3.1): the grain's event_class is needed")
        rules = self._lord_rules.get(anchor)
        if rules is None:
            rules = self._lord_rules[anchor] = pv.LordRungRules(anchor, self.l0.dignity.rows, self.l0.naisargika.rows)

        def pos(body, t):
            try:
                return self.lon(body, t)
            except p1.StrictInputError:
                return None                       # undeterminable: P1b names it, never a default
        if getattr(self._position_at, "cache_key", None) is not None:
            pos.cache_key = self._position_at.cache_key        # lets P1b memoise its nature search across lords of one run
        valence = nat.P1LordValence(
            graha=anchor, event_class=event_class, mapping=self.form_b, rules=rules, nature=nat.NatureOperands(anchor, pos), position_at=pos,
            combust_at=None if anchor in p1.NEVER_COMBUST else v._combust_flag, rung_boundaries=v.rung_boundaries)
        gate = lambda src: dataclasses.replace(src, complete=bool(src.complete and done))           # noqa: E731
        return {
            FACTOR_NATURE: gate(valence.agent_nature_source()),
            FACTOR_DIGNITY: gate(valence.dignity_value_source()),
            # combustion is a rung of the table (COMB); the factor contributes the neutral element — or, for the Sun and the nodes, is
            # DECLARED not applicable (L1 M-19), which is a different statement from "1.0"
            FACTOR_COMBUSTION: (OperandSource(not_applicable=True) if anchor in p1.NEVER_COMBUST else nat.declared_neutral_source()),
        }

    def sources_for(self, anchor: str, *, complete: bool, stations: Sequence[datetime] | None = None,
                    event_class: str | None = None) -> dict[str, OperandSource]:
        """Per-factor sources for one period lord. `complete` = the store's assertion that the search behind the boundary lists covered every
        support (its coverage check); for Mercury / Venus it also needs the stored stations (the retrograde regime flips there).
        `event_class` is needed (and used) only under the Form B mapping, whose side is class-relative."""
        v = self.view(anchor, stations)
        done = bool(complete) and (not v.retro_matters or bool(v.stations))
        if self.form_b is not None:
            return self._form_b_sources(anchor, v, done, event_class)
        rules = self.rules

        def _value(factor: str, state_of, reason_of):
            rule = rules.get(factor)
            if rule is None:
                return None, None

            def value_at(t):
                s = state_of(t)
                return None if s is None else rule(s)

            def unknown(t):
                s = state_of(t)
                return reason_of(t) if s is None else (None if rule(s) is not None else f"{factor}_category_unmapped")
            return value_at, unknown

        def dignity_state(t):
            s = v.state(t)
            return s if s.rung is not None else None
        d_val, d_unk = _value(FACTOR_DIGNITY, dignity_state, lambda t: v.state(t).unknown_reason)

        def combustion_state(t):
            s = v.state(t)
            return s if s.combustion_applicable and s.combust is not None else None
        c_val, c_unk = _value(FACTOR_COMBUSTION, combustion_state, lambda t: v.state(t).combustion_unknown_reason)

        def maitri_state(t):
            res, _ = v.maitri(t)
            return None if res is None else dataclasses.replace(v.state(t), maitri=res["category"] if res["applicable"] else "own_sign")
        m_val, m_unk = _value(FACTOR_MAITRI, maitri_state, lambda t: v.maitri(t)[1])

        return {
            FACTOR_DIGNITY: OperandSource(boundaries=v.rung_boundaries, complete=done, value_at=d_val, unknown_reason=d_unk),
            FACTOR_COMBUSTION: OperandSource(boundaries=v.combustion_changes, complete=done, value_at=c_val, unknown_reason=c_unk,
                                             not_applicable=anchor not in p1.COMBUSTIBLE),
            FACTOR_MAITRI: OperandSource(boundaries=v.maitri_boundaries, complete=done, value_at=m_val, unknown_reason=m_unk),
        }

    def attach(self, rec: SweepRecord, *, complete: bool, stations: Sequence[datetime] | None = None,
               event_class: str | None = None) -> SweepRecord:
        """`rec` with P1's sources added for ITS PERIOD ANCHOR — the record's `period_anchor_lord`, else its own agent (the lord's own transit).
        A delivery form (Sun / Jupiter through another lord's exaltation sign) is judged by the ANCHOR's sky, not the transiting agent's."""
        if rec.path_id != "P1":
            return rec
        anchor = graha_title(rec.period_anchor_lord or rec.agent)
        return dataclasses.replace(rec, operand_sources={**rec.operand_sources,
                                                         **self.sources_for(anchor, complete=complete, stations=stations,
                                                                                     event_class=event_class)})


def form_b_mapping(factor_rows) -> "pv.SideValueMapping | None":
    """The Form B table the path's factor rows declare, or None when they declare none (the 1.0.0 rows: nothing changes for them)."""
    return pv.mapping_from_rows(factor_rows) if pv.has_form_b(factor_rows) else None


__all__ = ["FACTOR_COMBUSTION", "FACTOR_DIGNITY", "FACTOR_MAITRI", "FACTOR_NATURE", "form_b_mapping", "L0Table", "LordState", "NAMED_LIMIT", "NODE_FRIENDSHIP_DISPUTED", "NODE_RESERVED_SIGNS",
           "NODE_VARIANT_OWN_SIGNS", "P1L0", "P1Operands", "RUNGS", "RetrogradeUnestablished", "SOURCE_FACTORS", "ValueRule",
           "category_rule", "combustion_orbs_from_rows", "dignity_reference_from_rows", "load_combustion_orbs", "load_dignity_reference",
           "load_naisargika", "load_p1_l0", "naisargika_from_rows"]
