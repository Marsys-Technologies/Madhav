"""SR-OD1 R4 — combustion inheritance (RECONCILIATION.md R-4 / SR-Q6-L1-AMEND).

The ruling, restated precisely: the combustion ORB ROWS (`bg_combustion_orbs`: row ids + content digest, bound in `L0_CONSUMED`) and the L1
combustion function's MODULE DIGEST (`IMPLEMENTATION_MODULES`, `ga_writers.ga_condition_writer`) are inherited by identity. The per-instant
combust STATE is derived at Kāla from the pinned ephemeris by L1's function over exactly those rows, and the derivation records the orb row
ids, their digest and the module digest in every window's qualification provenance. The verifier derives the same record from its own L0 read
and its own hashing, and refuses a window whose record differs. Authority: root CLAUDE.md §N.5 (L1 is the authority over L2+); GPT review B5 /
RECONCILIATION R-4. The orb VALUES themselves are the seed of migration 250 (Saravali ch.6 / BPHS ch.3: Mars 17°, Mercury 14°, Moon 12° ...),
transcribed in `test_od1_p1c_operands_check.ORB_ROWS` (id = the seed's insertion order), never computed by the code under test. No database, no
personal data.

Claims, each with ONE oracle that fails on its single planted reversion (named in the test):

  R1 the builder's record names the orb rows (id per graha), their content digest and L1's module digest         (revert: ids not recorded)
  R2 the recorded digest is the VALUES' identity: an orb value moves it, a surrogate id alone does not           (revert: the id enters the digest)
  R3 the L1 module digest is the digest of the module the process LOADED (code drift moves the record)           (revert: a hard-wired file)
  R4 the state is derived over the SUPPLIED orb rows, never a module constant — the authority wins (§N.5)        (revert: L1's literal orbs)
  R5 only a Form B grain carries the record; the legacy per-factor rules and no operands carry none            (revert: always attach)
  R6 every window of the grain carries it in `qualification`, and a grain given none gains no key              (revert: not copied to the windows)
  R7 the verifier's record comes from its OWN SQL read, equals the builder's over the same rows                (revert: the id column not read)
  R8 an orb mismatch (value, row id, or L1 module digest) is refused, naming the field                          (revert: the record is not compared)
  R9 a window that records no inheritance is refused                                                              (revert: absence accepted)
  R10 an identity is never invented: a row handed in without an id is refused by name, on both sides              (revert: id defaults to 0)
  R11 CHANGED combustion settings: the verifier states the record of the rows IT reads now, and refuses results      (revert: the verifier's record is a
      built from the old rows (the orb-mismatch case the ruling names)                                                 constant of the seed rows, digest or ids)
"""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest

from services.gochara_kernel import p1_operands as P
from services.gochara_kernel import p1_operands_check as p1c
from services.gochara_kernel import window_sweep as ws
from services.gochara_rules import p1_inputs as p1

from services.gochara_kernel.window_sweep import OperandSource

from .test_a53_window_sweep import _draft, _rec
from .test_od1_p1c_operands_check import (DIGNITY_ROWS, NAIS_ROWS, ORB_ROWS, Sky, _check, _d, _jupiter_world, _ProvConn, _ReadConn, _Rows,
                                          _stored, _verify)
from .test_od1_w0_interface import P1_ROWS, _steady

#: the ids the seed (migration 250) gives the eight rows, in its insertion order
SEED_IDS = {"Moon": 1, "Mars": 2, "Mercury": 3, "Jupiter": 4, "Venus": 5, "Saturn": 6, "Rahu": 7, "Ketu": 8}
#: the canonical-JSON preimage of the seed's values, written out by hand (graha order, plain decimal text) — not produced by the code under test
SEED_PREIMAGE = ('[["Jupiter","11","9"],["Ketu","9","7"],["Mars","17","15"],["Mercury","14","12"],["Moon","12","10"],["Rahu","9","7"],'
                 '["Saturn","15","12"],["Venus","10","8"]]')
SEED_DIGEST = hashlib.sha256(SEED_PREIMAGE.encode("utf-8")).hexdigest()
L1_FILE = Path(importlib.import_module(p1.L1_RULE_MODULE).__file__)
L1_DIGEST = hashlib.sha256(L1_FILE.read_bytes()).hexdigest()
FORM_B_ROWS = ws.registry_factor_rows("P1", "1.3.0")


def _l0(orbs=ORB_ROWS) -> P.P1L0:
    return P.P1L0(P.dignity_reference_from_rows(DIGNITY_ROWS), P.combustion_orbs_from_rows(orbs), P.naisargika_from_rows(NAIS_ROWS))


def _ops(orbs=ORB_ROWS, **kw) -> P.P1Operands:
    return P.P1Operands(_l0(orbs), Sky(), **kw)


def _with(graha, **cols):
    return [{**r, **cols} if r["graha"] == graha else r for r in ORB_ROWS]


EXPECTED = {"orb_digest": SEED_DIGEST, "orb_row_ids": dict(sorted(SEED_IDS.items())), "l1_module": p1.L1_RULE_MODULE, "l1_module_digest": L1_DIGEST}


# ══ R1–R3: the builder's record ═════════════════════════════════════════════════════════════════════════════════════════════

def test_r1_the_builders_record_names_the_orb_rows_their_digest_and_the_l1_module():
    """The record is the three identities of the ruling: the rows' ids, the content digest `L0_CONSUMED` binds (hand-written preimage above)
    and the sha256 of L1's source file. Planted reversion: the ids are not recorded ⇒ `orb_row_ids` is empty."""
    assert _ops().combustion_inheritance() == EXPECTED


def test_r2_an_orb_value_moves_the_digest_but_a_surrogate_id_alone_does_not():
    """The digest is the identity of the VALUES consumed (the L0 loaders' rule: ids, citations and notes do not move it); the ids are the
    separate `orb_row_ids` member. Planted reversion: the id enters the digest preimage ⇒ renumbering the rows moves the digest."""
    base = _ops().combustion_inheritance()
    reid = _ops(_with("Mars", id=99)).combustion_inheritance()
    assert reid["orb_digest"] == base["orb_digest"] and reid["orb_row_ids"]["Mars"] == 99
    moved = _ops(_with("Mars", orb_degrees=18)).combustion_inheritance()
    assert moved["orb_digest"] != base["orb_digest"] and moved["orb_row_ids"] == base["orb_row_ids"]


def test_r3_the_module_digest_is_that_of_the_module_the_process_loaded(monkeypatch, tmp_path):
    """Code drift must move the record: with the module the wrapper calls replaced by one loaded from other source, the recorded digest is the
    replacement's. Planted reversion: the digest is taken from a fixed file, whichever module is loaded ⇒ it stays L1_DIGEST."""
    alt = tmp_path / "ga_condition_writer_alt.py"
    alt.write_bytes(L1_FILE.read_bytes() + b"\n# a different combustion function\n")

    class _Alt:
        __file__ = str(alt)
    ops = _ops()
    monkeypatch.setattr(p1, "_l1", lambda: _Alt)
    rec = ops.combustion_inheritance()
    assert rec["l1_module_digest"] == hashlib.sha256(alt.read_bytes()).hexdigest() != L1_DIGEST


# ══ R4: the authority wins over a local constant ═════════════════════════════════════════════════════════════════════════════

def _mars_18_from_the_sun():
    """Mars 18° of arc from the Sun, direct (analytic sky, fixed positions). L1's own literal orb for Mars is 17° (seed row: outer orb 17°)."""
    return Sky(sun=100.0, mars=118.0, moon=250.0, mercury=300.0, jupiter=20.0, venus=330.0, saturn=200.0)


def test_r4_the_state_is_derived_over_the_supplied_orb_rows_not_a_module_constant_builder():
    """A supplied L0 row says Mars' outer orb is 20°: at 18° of arc Mars is combust (L0 governs, §N.5); under the seed's 17° it is not.
    Planted reversion: the builder hands L1 its own literal orbs instead of the supplied rows ⇒ not combust."""
    sky = _mars_18_from_the_sun()
    at = _d(0)
    probe = lambda body, t: sky(body.lower(), t)                    # noqa: E731  — the writer's probe takes Title-case names
    wide = P.P1Operands(_l0(_with("Mars", orb_degrees=20)), probe).view("Mars", None).state(at)
    seed = P.P1Operands(_l0(), probe).view("Mars", None).state(at)
    assert wide.combust is True and wide.rung == "COMB"
    assert seed.combust is False


def test_r4_the_state_is_derived_over_the_supplied_orb_rows_not_a_module_constant_verifier():
    """The same claim for the verifier's own derivation. Planted reversion: the verifier reads L1's literal orbs ⇒ not combust."""
    sky = _mars_18_from_the_sun()
    at = _d(0)
    assert _check(sky, orb_rows=_with("Mars", orb_degrees=20)).combustion_at("Mars", at)["is_combust"] is True
    assert _check(sky).combustion_at("Mars", at)["is_combust"] is False


# ══ R5–R6: what the grain carries ═══════════════════════════════════════════════════════════════════════════════════════════

def test_r5_only_a_form_b_grain_carries_the_record():
    """The verifier derives P1 states only for factor rows that declare a value table (`needs_p1_check`), i.e. the Form B rows; the legacy
    per-factor rules and an unbound grain carry no record (nothing moves for them). Planted reversion: the record is attached to every grain."""
    form_b = P.form_b_mapping(FORM_B_ROWS)
    assert form_b is not None
    assert P.grain_inheritance(_ops(form_b=form_b)) == EXPECTED
    assert P.grain_inheritance(_ops(rules={"dignity_of_transit_sign": lambda s: 1.0})) is None
    assert P.grain_inheritance(None) is None


def test_r6_every_window_of_the_grain_carries_the_record_and_a_grain_given_none_gains_no_key():
    """`qualification` is what the window table persists and the verifier compares. Planted reversion: the record is not copied onto the drafts."""
    later = _rec("c", path="P1", root="R-c", supports=((20, 30),),            # a second, disjoint component ⇒ a second window
                 operand_sources={"agent_nature": OperandSource(value_at=lambda t: 0.4, channel_at=lambda t: ws.CHANNEL_FOR, complete=True,
                                                                boundaries=lambda lo, hi: [])})
    steady = [_steady("a", 0.3), later]
    with_rec, _ = _draft(steady, P1_ROWS, combustion_inheritance=EXPECTED)
    without, _ = _draft(steady, P1_ROWS)
    assert len(with_rec) == len(without) == 2 and all(d.qualification()["combustion_inheritance"] == EXPECTED for d in with_rec)
    assert without and all("combustion_inheritance" not in d.qualification() for d in without)


# ══ R7: the verifier's own record ═══════════════════════════════════════════════════════════════════════════════════════════

def test_r7_the_verifiers_record_comes_from_its_own_sql_and_equals_the_builders_over_the_same_rows():
    """The verifier reads `id` by its own SELECT (the fourth column) and hashes by its own code; over the same rows both sides state one record.
    Planted reversion: the SELECT does not read the id ⇒ the verifier cannot name the rows and refuses."""
    verifier = p1c.P1Check.from_conn(_ReadConn(), Sky()).combustion_inheritance()
    assert verifier == EXPECTED == _ops().combustion_inheritance()


# ══ R8–R9: the verifier compares ════════════════════════════════════════════════════════════════════════════════════════════

def _world(stored_record):
    """The Jupiter world of the P1c suite with the window's persisted provenance carrying `stored_record` (None = no key)."""
    sky, plain, stored = _jupiter_world()
    qualification = {"policy": "window_qualification/1", "unqualified_reason": None, "unresolved": {}, "affected_channels": [], "members": 1,
                     "qualified_members": 1}
    if stored_record is not None:
        qualification["combustion_inheritance"] = stored_record
    window = _stored("w", _d(0), _d(10), _d(5), 0.125, 0.125, None, stored[9], prov=("evidence_for_per_root_sum", 0.125, qualification))
    return sky, _ProvConn([window], plain.records, plain.links)


def test_r8_a_window_recording_the_same_authority_is_verified():
    sky, conn = _world(EXPECTED)
    assert _verify(conn, sky)["numeric_reproduced"] == 1


@pytest.mark.parametrize("field, stored", [
    ("orb_digest", {**EXPECTED, "orb_digest": hashlib.sha256(b"Mercury 15 / 12").hexdigest()}),      # the builder consumed other values
    ("orb_row_ids", {**EXPECTED, "orb_row_ids": {**EXPECTED["orb_row_ids"], "Mars": 22}}),             # …or other rows (re-seeded ids)
    ("l1_module_digest", {**EXPECTED, "l1_module_digest": hashlib.sha256(b"an older combustion function").hexdigest()}),   # …or older L1 code
])
def test_r8_an_orb_mismatch_is_refused_naming_the_field(field, stored):
    """The window says the builder derived from different orb rows (or code) than the verifier reads from L0 now: the authority is L0's rows,
    so the window is refused and the message names what differs. Planted reversion: the record is not compared (the verifier derives none)."""
    sky, conn = _world(stored)
    with pytest.raises(RuntimeError, match=f"combustion inheritance {field}"):
        _verify(conn, sky)


def test_r9_a_window_that_records_no_inheritance_is_refused():
    """Planted reversion: absence is accepted ⇒ a build that never recorded its orb rows verifies."""
    sky, conn = _world(None)
    with pytest.raises(RuntimeError, match="records no combustion inheritance"):
        _verify(conn, sky)


# ══ R10: an identity is never invented ══════════════════════════════════════════════════════════════════════════════════════

def test_r10_a_row_without_an_id_is_refused_by_name_on_both_sides():
    """Planted reversion: a missing id defaults to 0 ⇒ the record names rows that do not exist."""
    no_ids = [{k: v for k, v in r.items() if k != "id"} for r in ORB_ROWS]
    with pytest.raises(p1.StrictInputError) as built:
        _ops(no_ids).combustion_inheritance()
    assert built.value.reason == "l0_row_id_missing"
    with pytest.raises(p1.StrictInputError) as checked:
        _check(orb_rows=no_ids).combustion_inheritance()
    assert checked.value.reason == "l0_row_id_missing"


# ══ R11: changed combustion settings — the checker reads the NEW rows and rejects the old results ═════════════════════════════

class _AlteredOrbsConn(_ReadConn):
    """The verifier's L0 read after `bg_combustion_orbs` was amended: the orb SELECT answers `rows`, the other two relations as the seed."""

    def __init__(self, rows):
        super().__init__()
        self._rows = rows

    def execute(self, sql, params=()):
        if "bg_combustion_orbs" in sql:
            self.sql.append(sql)
            return _Rows([(r["graha"], r["orb_degrees"], r["deep_orb_degrees"], r["id"]) for r in self._rows])
        return super().execute(sql, params)


@pytest.mark.parametrize("field, other, amended", [
    # an L0 amendment of a VALUE (the open Saturn 15° / 16° question, SR-DOCTRINE-H): same rows, other content ⇒ the digest moves, the ids do not
    ("orb_digest", "orb_row_ids", _with("Saturn", orb_degrees=16)),
    # a re-seeded row (new surrogate id, same values) ⇒ the ids move, the digest (the values' identity, R2) does not
    ("orb_row_ids", "orb_digest", _with("Mars", id=99)),
])
def test_r11_changed_combustion_settings_are_read_by_the_checker_and_the_old_results_are_refused(field, other, amended):
    """The ruling's oracle (R-4: "a supplied orb row that differs from a local constant ⇒ provenance refuses"), on the VERIFIER side. The builder's
    windows record the seed rows (EXPECTED); L0 now holds `amended` rows. The checker must (a) state the record of the rows it READ — equal to what a
    builder over those rows would record and different from the seed's in `field` only — and (b) refuse the old window, naming `field`.
    Planted reversions (one per production claim): the verifier's digest is a constant of the seed rows ⇒ the `orb_digest` case is accepted; its
    ids are a constant map ⇒ the `orb_row_ids` case is accepted."""
    checker = p1c.P1Check.from_conn(_AlteredOrbsConn(amended), Sky())
    record = checker.combustion_inheritance()
    assert record == _ops(amended).combustion_inheritance()
    assert record[field] != EXPECTED[field] and record[other] == EXPECTED[other]
    sky, conn = _world(EXPECTED)                       # the window built from the seed rows
    with pytest.raises(RuntimeError, match=f"combustion inheritance {field}"):
        _verify(conn, sky, check=p1c.P1Check.from_conn(_AlteredOrbsConn(amended), sky))
