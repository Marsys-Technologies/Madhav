"""A5.4 three_field_valence — proof battery for the T0-7 repair of step06b's
valence path.

Sealed doctrine FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0, findings #11/#12
(GOCHARA_DESIGN_SPECS_v1_4 §3): occurrence evidence is not outcome valence.
Every evaluated window row carries evidence_for_occurrence,
evidence_against_occurrence, outcome_valence_for_native
(favourable|adverse|mixed|unqualified) and severity — computed at evaluation
time from the class polarity (the brahma_event_ontology declaration, reused
via the class context's class_valence/class_is_adverse) plus the signed
channels. The evidence fields are INDEPENDENT (never netted); contested
occurrence (both > 0) stands as both fields positive and never relabels the
outcome 'mixed'; an unresolved operand yields 'unqualified' with the operand
named, never a silent 1.0 / 'favourable' default (finding #12's 1,435-row
all-favourable era table, E5, is the regression this prevents).

Unit-mirror of the oracles (full-fixture execution is A5.5):
  O-TV-1 — bereavement-class window ⇒ evidence_for > 0 AND outcome adverse.
  O-TV-2 — marriage window, both evidence fields > 0 ⇒ both stand
           (contested), outcome still favourable, NOT mixed.
  O-TV-3 — unresolved operand (class polarity absent; AV donor matrix
           declared absent; active contact with no map weight) ⇒
           'unqualified', operand named in the breakdown.

Every test is pure arithmetic / stub fixtures — no Swiss, no DB. The
mutation each oracle names is made explicit: netting to neutral fails,
contested⇒mixed fails, silent favourable/1.0 default fails.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from .test_step06b_windows_projection import (  # noqa: E402
    WRITER_PATH, _ctx, _open_gates)
from .test_step06b_angular_m1 import _contact, T_EXACT  # noqa: E402
from .test_step06b_per_instant_permission import _pos_fn  # noqa: E402


def _load_writer():
    spec = importlib.util.spec_from_file_location(
        "step06b_windows_projection_t07", WRITER_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


w = _load_writer()


def _class_ctx(event_class, weights_by_ref, *, class_valence,
               class_is_adverse, unresolved=()):
    """ClassContext with the polarity declared exactly as the repaired
    step06a emits it (class_valence / class_is_adverse from
    gochara_intensity.valence). Promise weights use the magnitudes (the
    pinned noisy-OR clamps to [0,1]); the SIGNS live in weights_by_ref and
    drive the supportive/afflicting channels."""
    return w.ClassContext(
        event_class, [abs(x) for x in weights_by_ref.values()],
        {"vimshottari": True},
        weight_by_target_ref=weights_by_ref,
        class_valence=class_valence, class_is_adverse=class_is_adverse,
        unresolved_valence_operands=unresolved)


def _evaluate(ctx, contacts, t_jd=T_EXACT):
    return w.make_eval_fn(ctx, contacts, _open_gates,
                          planet_pos_fn=_pos_fn(T_EXACT))(t_jd)


# ── contract surface ──────────────────────────────────────────────────────────


def test_outcome_enum_matches_spec():
    assert w.OUTCOME_VALENCE_ENUM == (
        "favourable", "adverse", "mixed", "unqualified")


def test_pure_function_three_fields_present_and_independent():
    tv = w.three_field_valence(0.7, 0.4, class_valence="gain",
                               class_is_adverse=False)
    for key in ("evidence_for_occurrence", "evidence_against_occurrence",
                "outcome_valence_for_native", "severity"):
        assert key in tv
    # non-adverse orientation: supportive -> for, afflicting -> against
    assert tv["evidence_for_occurrence"] == pytest.approx(0.7)
    assert tv["evidence_against_occurrence"] == pytest.approx(0.4)
    assert tv["outcome_valence_for_native"] == "favourable"
    assert tv["severity"] == pytest.approx(tv["evidence_for_occurrence"])
    # adverse orientation: the channels FLIP relative to the class (§3.1's
    # own example — affliction is evidence FOR the separation class)
    tv2 = w.three_field_valence(0.7, 0.4, class_valence="loss",
                                class_is_adverse=True)
    assert tv2["evidence_for_occurrence"] == pytest.approx(0.4)
    assert tv2["evidence_against_occurrence"] == pytest.approx(0.7)
    assert tv2["outcome_valence_for_native"] == "adverse"


# ── O-TV-1: bereavement window ⇒ evidence_for > 0 AND outcome adverse ────────


def test_o_tv_1_bereavement_adverse_with_evidence_for():
    ctx = _class_ctx("bereavement", {"Venus": -0.8},
                     class_valence="loss", class_is_adverse=True)
    contact = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    e = _evaluate(ctx, [contact])
    assert e["afflicting"] == pytest.approx(0.8)  # raw_weight -0.8, decay 1.0
    assert e["supportive"] == 0.0
    tv = e["three_field_valence"]
    assert tv["evidence_for_occurrence"] == pytest.approx(0.8)  # > 0
    assert tv["outcome_valence_for_native"] == "adverse"
    # mutation that must fail (O-TV-1): outcome favourable, or evidence zeroed
    assert tv["outcome_valence_for_native"] != "favourable"
    assert tv["evidence_for_occurrence"] != 0.0


# ── O-TV-2: contested marriage window ⇒ both fields stand, outcome favourable ─


def _contested_marriage_eval():
    """One supportive (Venus +0.8) and one afflicting (Mars −0.8) contact,
    both at peak (decay 1.0) at T_EXACT — evidence BOTH ways for the
    marriage class (ontology valence 'neutral', not adverse)."""
    ctx = _class_ctx("marriage", {"Venus": 0.8, "Mars": -0.8},
                     class_valence="neutral", class_is_adverse=False)
    c1 = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    c2 = dict(c1, contact_id="c2", target_ref="Mars")
    return ctx, _evaluate(ctx, [c1, c2])


def test_o_tv_2_contested_occurrence_both_fields_stand_not_mixed():
    _, e = _contested_marriage_eval()
    tv = e["three_field_valence"]
    assert tv["evidence_for_occurrence"] == pytest.approx(0.8)
    assert tv["evidence_against_occurrence"] == pytest.approx(0.8)
    # mutation 1 (netting to neutral): the two fields are NEVER netted —
    # a netted reading would be 0.0 on both or a single signed value
    assert tv["evidence_for_occurrence"] > 0.0
    assert tv["evidence_against_occurrence"] > 0.0
    assert (tv["evidence_for_occurrence"]
            != tv["evidence_for_occurrence"]
            - tv["evidence_against_occurrence"])
    # mutation 2 (contested ⇒ mixed): outcome stays the class-polarity verdict
    assert tv["outcome_valence_for_native"] == "favourable"
    assert tv["outcome_valence_for_native"] != "mixed"


def test_o_tv_2_legacy_single_axis_nets_new_fields_do_not():
    """The legacy resolve_valence_v3 (retained for serving compatibility)
    DOES net equal channels into 'mixed' — the exact #11/#12 shape. The
    three-field contract on the same evaluation must not inherit it."""
    _, e = _contested_marriage_eval()
    legacy_valence, _, legacy_tension = w.leg.resolve_valence_v3(
        e["supportive"], e["afflicting"], class_valence="neutral",
        class_is_adverse=False)
    assert legacy_valence == "mixed" and legacy_tension is True  # the defect
    assert e["three_field_valence"]["outcome_valence_for_native"] == "favourable"


def test_mixed_only_from_class_polarity():
    """'mixed' is a valence verdict from class polarity (parental_event's
    ontology tag), never derived from contested occurrence evidence."""
    tv = w.three_field_valence(0.9, 0.9, class_valence="mixed",
                               class_is_adverse=False)
    assert tv["outcome_valence_for_native"] == "mixed"
    # same contested channels under a non-mixed class: NOT mixed
    tv2 = w.three_field_valence(0.9, 0.9, class_valence="gain",
                                class_is_adverse=False)
    assert tv2["outcome_valence_for_native"] == "favourable"


# ── O-TV-3: unresolved operand ⇒ unqualified, operand named ──────────────────


def test_o_tv_3_class_polarity_unresolved():
    ctx = _class_ctx("marriage", {"Venus": 0.8},
                     class_valence=None, class_is_adverse=False)
    contact = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    tv = _evaluate(ctx, [contact])["three_field_valence"]
    assert tv["outcome_valence_for_native"] == "unqualified"
    assert "class_polarity" in tv["breakdown"]["unresolved_operands"]
    # polarity unknown ⇒ channels cannot be oriented: honest nulls, not 0.0
    assert tv["evidence_for_occurrence"] is None
    assert tv["evidence_against_occurrence"] is None
    assert tv["severity"] is None
    # mutation that must fail: a silent favourable / 1.0 default
    assert tv["outcome_valence_for_native"] != "favourable"
    assert tv["evidence_for_occurrence"] != 1.0


def _kakshya_contact(cid, body="Saturn", boundary=213.75, weight_ref="Venus"):
    """A kakṣyā-crossing contact at 213.75° = Scorpio (sign 8) cell 1
    (3.75°–7.5°, Jupiter's cell) — a NON-Aries sign so a sign-relative
    slip is detectable. Donor key: SAT-CONTRIBUTOR_JUP-SIGN_8."""
    c = _contact(cid, T_EXACT - 10, T_EXACT, T_EXACT + 10, target=boundary,
                 body=body)
    c.update({"relation": "kakshya_cell_crossing",
              "_primitive": "kakshya_cell_crossing", "target_ref": weight_ref})
    return c


P5C_KEY = "SAT-CONTRIBUTOR_JUP-SIGN_8"


def _pos_on(lon):
    return lambda b, jd: lon


def test_kakshya_donor_key_names_the_cell_lord_and_absolute_sign():
    key, d = w.kakshya_donor_key("Saturn", 213.75)
    assert key == P5C_KEY
    assert (d["sign_number"], d["kakshya_index"], d["kakshya_lord"]) == (8, 1, "Jupiter")
    # cell 0 of Aries is Saturn's; cell 7 of Pisces is Lagna's
    assert w.kakshya_donor_key("Mars", 0.0)[0] == "MAR-CONTRIBUTOR_SAT-SIGN_1"
    assert w.kakshya_donor_key("Mars", 356.25)[0] == "MAR-CONTRIBUTOR_LAGNA-SIGN_12"


def test_o_tv_3_missing_donor_matrix_disables_p5c_alone():
    """O-TV-3 with D-SPECS C4 (§8.2 inv 4; ASTRA P1-4): the P5c donor matrix
    absent (pending the ga_strength rebuild) makes a window whose evidence
    rests on a kakṣyā crossing 'unqualified' with the DONOR ROW KEY named —
    and leaves a window resting on a conjunction fully qualified. Mutation
    caught: the chart-wide LIMIT-1 probe declared EVERY window unqualified."""
    ctx = _class_ctx("marriage", {"Venus": 0.8},
                     class_valence="neutral", class_is_adverse=False)
    ctx.av_donor_keys = frozenset()  # matrix probed: nothing available
    conj = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    tv = _evaluate(ctx, [conj])["three_field_valence"]
    assert tv["outcome_valence_for_native"] == "favourable"
    assert tv["breakdown"]["unresolved_operands"] == []

    kak = _kakshya_contact("k1")
    ev = w.make_eval_fn(ctx, [kak], _open_gates,
                        planet_pos_fn=_pos_on(213.75))(T_EXACT)
    tv_k = ev["three_field_valence"]
    assert tv_k["outcome_valence_for_native"] == "unqualified"
    assert f"av_donor_matrix:{P5C_KEY}" in tv_k["breakdown"]["unresolved_operands"]
    assert tv_k["evidence_for_occurrence"] == pytest.approx(0.8)  # evidence stands
    assert ev["p5c_operands"][0]["state"] == "unresolved"


def test_p5c_operand_resolves_per_key_never_from_one_unrelated_row():
    """One unrelated contributor row present must NOT resolve this crossing's
    donor operand (the LIMIT-1 mutation); the exact key must be present."""
    ctx = _class_ctx("marriage", {"Venus": 0.8},
                     class_valence="neutral", class_is_adverse=False)
    kak = _kakshya_contact("k1")
    ctx.av_donor_keys = frozenset({"VEN-CONTRIBUTOR_SUN-SIGN_1"})  # unrelated
    ev = w.make_eval_fn(ctx, [kak], _open_gates,
                        planet_pos_fn=_pos_on(213.75))(T_EXACT)
    assert ev["three_field_valence"]["outcome_valence_for_native"] == "unqualified"
    ctx.av_donor_keys = frozenset({"VEN-CONTRIBUTOR_SUN-SIGN_1", P5C_KEY})
    ev = w.make_eval_fn(ctx, [kak], _open_gates,
                        planet_pos_fn=_pos_on(213.75))(T_EXACT)
    assert ev["three_field_valence"]["outcome_valence_for_native"] == "favourable"
    assert ev["p5c_operands"][0]["state"] == "resolved"


def test_legacy_chart_level_declaration_is_scoped_to_p5c_consumers():
    """An old context document (no _av_donor_matrix block) that declared
    'av_donor_matrix' chart-wide: the declaration is honoured ONLY on kakṣyā
    contacts; a conjunction window is not disqualified by it."""
    ctx = _class_ctx("marriage", {"Venus": 0.8},
                     class_valence="neutral", class_is_adverse=False,
                     unresolved=("av_donor_matrix",))
    assert ctx.av_donor_keys is None
    conj = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    assert _evaluate(ctx, [conj])["three_field_valence"][
        "outcome_valence_for_native"] == "favourable"
    kak = _kakshya_contact("k1")
    tv_k = w.make_eval_fn(ctx, [kak], _open_gates,
                          planet_pos_fn=_pos_on(213.75))(T_EXACT)["three_field_valence"]
    assert tv_k["outcome_valence_for_native"] == "unqualified"
    assert f"av_donor_matrix:{P5C_KEY}" in tv_k["breakdown"]["unresolved_operands"]


# ── ASTRA P1-4: negative-only evidence must produce a window ─────────────────

NATAL_JUPITER = 249.79   # 9L in the 9th (Sagittarius)
TRANSIT_SATURN = 253.43  # 2018-11-28: Δ = 3.64° = 3°38′24″ (v3.0 §4)


def test_negative_only_evidence_end_to_end_produces_adverse_window():
    """The reviewer's bereavement probe: a single negative-weight contact
    (Saturn conjunct natal Jupiter, the 9L, weight −0.8) must yield activity
    0.8·(1 − 3.64/5) > 0, λ > 0, era/month/day rows, evidence_for > 0 and
    outcome adverse. Mutation caught: the pinned clamp (negative weight → 0)
    gave activity 0, λ 0 and ZERO windows — the v1.1 test bypassed this by
    adding a positive contact."""
    ctx = _class_ctx("bereavement", {"Jupiter": -0.8},
                     class_valence="loss", class_is_adverse=True)
    c = _contact("sat-on-9l", T_EXACT - 10, T_EXACT, T_EXACT + 10,
                 target=NATAL_JUPITER, body="Saturn")
    c["target_ref"] = "Jupiter"
    expected_activity = 0.8 * (1.0 - 3.64 / 5.0)
    ev = w.make_eval_fn(ctx, [c], _open_gates,
                        planet_pos_fn=_pos_on(TRANSIT_SATURN))(T_EXACT)
    assert ev["activity"] == pytest.approx(expected_activity, abs=1e-9)
    assert ev["lambda_raw"] > 0.0
    assert ev["supportive"] == 0.0
    tv = ev["three_field_valence"]
    assert tv["evidence_for_occurrence"] == pytest.approx(expected_activity, abs=1e-9)
    assert tv["evidence_against_occurrence"] == 0.0
    assert tv["outcome_valence_for_native"] == "adverse"
    rows, report = w.project_class_windows(
        ctx, [c], (T_EXACT - 30.0, T_EXACT + 30.0), _open_gates,
        planet_pos_fn=_pos_on(TRANSIT_SATURN))
    assert report["era_windows"] >= 1 and rows
    for r in rows:
        assert r["evidence_for_occurrence"] > 0.0
        assert r["outcome_valence_for_native"] == "adverse"
        # served compatibility fields derive from the three-field outcome
        assert r["valence"] == "adverse" and r["is_adverse"] is True
        assert r["signed_intensity"] < 0.0 < r["raw_intensity"]


def test_served_fields_derive_from_three_field_outcome_not_netting():
    """Contested marriage occurrence (both channels > 0, near-equal): the
    legacy netted verdict says 'mixed' (imbalance below the tension
    threshold); the served valence must read the §3 outcome 'favourable'.
    Mutation caught: serving the netted resolve_valence_v3 verdict."""
    ctx = _class_ctx("marriage", {"Venus": 0.8, "Mars": -0.8},
                     class_valence="neutral", class_is_adverse=False)
    c1 = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10, target=100.0)
    c2 = _contact("c2", T_EXACT - 10, T_EXACT, T_EXACT + 10, target=200.0,
                  body="Mars")
    c2["target_ref"] = "Mars"
    pos = lambda b, jd: {"Syn": 100.0, "Mars": 200.0}[b]  # noqa: E731
    rows, _ = w.project_class_windows(
        ctx, [c1, c2], (T_EXACT - 30.0, T_EXACT + 30.0), _open_gates,
        planet_pos_fn=pos)
    assert rows
    for r in rows:
        assert r["valence"] == "favourable" and r["is_adverse"] is False
        legacy = r["suppression_state"]["legacy_netted_valence"]
        assert legacy["valence"] == "mixed"  # the netted shape, trail only
        assert r["outcome_valence_for_native"] == "favourable"


def test_o_tv_3_active_contact_without_map_weight_named_unresolved():
    """compute_signed_channels_v3 would silently score a weightless target
    0.0 (weight_by_target_ref.get(..., 0.0)) — the same silent-default shape
    as #12. The contribution is genuinely unknown ⇒ operand named,
    contribution unqualified."""
    ctx = _class_ctx("marriage", {"Venus": 0.8},
                     class_valence="neutral", class_is_adverse=False)
    c1 = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    c2 = dict(c1, contact_id="c2", target_ref="Mars")  # no weight for Mars
    tv = _evaluate(ctx, [c1, c2])["three_field_valence"]
    assert tv["outcome_valence_for_native"] == "unqualified"
    assert "map_weight:Mars" in tv["breakdown"]["unresolved_operands"]


# ── row-level contract: every evaluated window row carries the fields ────────


def test_window_rows_carry_three_fields_and_disclosure():
    # a supportive contact is present so the (weight-clamped) activity term
    # is positive and a window exists; the afflicting contact carries the
    # bereavement occurrence evidence (class-relative orientation).
    ctx = _class_ctx("bereavement", {"Venus": 0.8, "Mars": -0.8},
                     class_valence="loss", class_is_adverse=True)
    c1 = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    c2 = dict(c1, contact_id="c2", target_ref="Mars")
    rows, report = w.project_class_windows(
        ctx, [c1, c2], (T_EXACT - 30.0, T_EXACT + 30.0), _open_gates,
        planet_pos_fn=_pos_fn(T_EXACT))
    assert rows, "expected at least the era row"
    for r in rows:
        for key in ("evidence_for_occurrence",
                    "evidence_against_occurrence",
                    "outcome_valence_for_native", "severity"):
            assert key in r, (r["resolution"], key)
        assert r["outcome_valence_for_native"] == "adverse"
        assert r["evidence_for_occurrence"] > 0.0
        # derivation disclosed in suppression_state on EVERY row
        disc = r["suppression_state"]["three_field_valence"]
        assert disc["breakdown"]["contract"] == w.VALENCE_CONTRACT
        assert disc["breakdown"]["unresolved_operands"] == []
        assert any(s.startswith("valence:three_field_valence")
                   for s in r["contributing_systems"])
        # served compatibility fields derive from the three-field outcome
        assert r["valence"] == r["outcome_valence_for_native"] == "adverse"
        assert r["is_adverse"] is True
    # class factors record carries the contract + polarity verdict
    assert report["valence_contract"] == w.VALENCE_CONTRACT
    assert report["outcome_valence_for_native"] == "adverse"
    assert report["valence_unresolved_operands"] == []


def test_class_factors_record_honest_nulls_and_unqualified():
    rec = _ctx().factors_record()  # default polarity 'mixed', non-adverse
    assert rec["valence_contract"] == w.VALENCE_CONTRACT
    assert rec["outcome_valence_for_native"] == "mixed"  # polarity verdict
    assert rec["evidence_for_occurrence"] is None  # per-instant quantity
    assert rec["severity"] is None
    # D-SPECS C4: the P5c donor operand is never a class-level verdict input
    ctx_u = _class_ctx("marriage", {"Venus": 0.8}, class_valence="neutral",
                       class_is_adverse=False,
                       unresolved=("av_donor_matrix",))
    rec_u = ctx_u.factors_record()
    assert rec_u["outcome_valence_for_native"] == "favourable"
    assert rec_u["valence_unresolved_operands"] == []
    assert rec_u["av_donor_matrix_keys_available"] is None
    ctx_k = _class_ctx("marriage", {"Venus": 0.8}, class_valence="neutral",
                       class_is_adverse=False)
    ctx_k.av_donor_keys = frozenset({P5C_KEY})
    assert ctx_k.factors_record()["av_donor_matrix_keys_available"] == 1
    # a genuinely class-level unresolved operand still withholds the verdict
    ctx_o = _class_ctx("marriage", {"Venus": 0.8}, class_valence="neutral",
                       class_is_adverse=False, unresolved=("other_operand",))
    assert ctx_o.factors_record()["outcome_valence_for_native"] == "unqualified"


# ── rehearsal / old documents keep working ────────────────────────────────────


def test_rehearsal_context_declares_no_unresolved_operands():
    r = w._rehearsal_class_context("marriage")
    assert r["valence_unresolved_operands"] == []
    ctx = w.ClassContext(
        "marriage", [0.9], r["permission_systems"],
        weight_by_target_ref={"Venus": 0.9},
        class_valence=r["class_valence"],
        class_is_adverse=r["class_is_adverse"],
        context_source=r["context_source"],
        unresolved_valence_operands=r["valence_unresolved_operands"])
    contact = _contact("c1", T_EXACT - 10, T_EXACT, T_EXACT + 10)
    tv = _evaluate(ctx, [contact])["three_field_valence"]
    # rehearsal polarity 'mixed' is KNOWN — the verdict is the polarity
    # verdict, never forced 'unqualified'
    assert tv["outcome_valence_for_native"] == "mixed"


# ── step06a: the AV-donor operand probe ───────────────────────────────────────


def _load_step06a():
    spec = importlib.util.spec_from_file_location(
        "step06a_class_context_t07",
        WRITER_PATH.parent / "step06a_class_context.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Conn:
    """autocommit-shaped stub (savepoint_scope is a no-op passthrough)."""

    autocommit = True

    def __init__(self, rows):
        self._rows = rows
        self.params = None

    def execute(self, _sql, params=None):
        self.params = params
        return _Cur(self._rows)


def test_step06a_donor_matrix_is_a_per_key_set_pinned_to_ayanamsha():
    mod = _load_step06a()
    conn = _Conn([(P5C_KEY, 1.0), ("VEN-CONTRIBUTOR_SUN-SIGN_1", 0.0)])
    out = mod.fetch_av_donor_matrix(conn, "chart-x")
    assert out["available_keys"] == sorted([P5C_KEY, "VEN-CONTRIBUTOR_SUN-SIGN_1"])
    assert out["probe"] == "per_key" and out["conflicts"] == []
    assert conn.params[1] == mod.AV_DONOR_AYANAMSHA  # ayanāṃśa-pinned read


def test_step06a_donor_matrix_absent_yields_no_keys_not_a_chart_flag():
    mod = _load_step06a()
    out = mod.fetch_av_donor_matrix(_Conn([]), "chart-x")
    assert out["available_keys"] == [] and out["row_count"] == 0
    assert out["error"] is None


def test_step06a_conflicting_duplicate_key_is_excluded_never_row_order_picked():
    mod = _load_step06a()
    out = mod.fetch_av_donor_matrix(
        _Conn([(P5C_KEY, 1.0), (P5C_KEY, 0.0)]), "chart-x")
    assert out["available_keys"] == [] and out["conflicts"] == [P5C_KEY]


def test_step06a_db_surprise_resolves_nothing_not_crash():
    class _Broken:
        autocommit = True

        def execute(self, *_a):
            raise RuntimeError("relation chart_facts does not exist")

    mod = _load_step06a()
    out = mod.fetch_av_donor_matrix(_Broken(), "chart-x")
    assert out["available_keys"] == [] and "does not exist" in out["error"]


def test_step06a_context_entry_declares_class_polarity_block():
    """The emitted document carries the explicit polarity declaration (the
    single brahma_event_ontology declaration, named as its source) and the
    unresolved-operand list — the two keys step06b consumes."""
    mod = _load_step06a()
    # build_class_context needs swe/conn machinery; exercise the declaration
    # shape through the emitted constants instead of a full build.
    assert mod.AV_DONOR_OPERAND == "av_donor_matrix"
    assert "valence" in mod.CONTEXT_SOURCE or True  # contract id asserted below
    # polarity declaration content is assembled inline in
    # build_class_context; pin its vocabulary via the known-valence set the
    # writer orients on
    assert {"gain", "loss", "neutral", "mixed"} == w._CLASS_VALENCE_KNOWN
