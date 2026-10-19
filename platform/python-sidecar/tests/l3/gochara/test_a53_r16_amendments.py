"""A5.3 — round 16 (prepared): F-R16-6 (the natal sentence names the exact stored ayanamsha id; one tier read), G6 (a single, pinned daśā build — writer
AND verifier), and (d) the verifier's ABSOLUTE ephemeris probe against a pinned constant."""
from __future__ import annotations

import threading

import pytest

# G8: this suite is NOT about the class census; it opts out BY NAME (see conftest.g8_census_opt_out and the guard in test_g8_class_census.py).
G8_CENSUS_OPT_OUT_REASON = "exercises the R16 amendments (verifier identity and input pins) on a deliberate one-class marriage world"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")

from services.gochara_kernel import dasha_read
from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import inventory_verifier as inv
from services.gochara_kernel import seal_brief as sb

from .conftest import EPHE_PATH, requires_swieph  # noqa: F401
from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import built, rworld  # noqa: F401
from .test_a53_r11_seal_brief import _verified  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401


# ── F-R16-6 ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_natal_sentence_names_the_exact_stored_ayanamsha_id_and_both_wordings_do():
    assert "longitude_sidereal, lahiri_chitrapaksha)" in sb.NATAL_SINGLE_TIER_DISCLOSURE
    assert "lahiri)" not in sb.NATAL_SINGLE_TIER_DISCLOSURE
    assert "lahiri_chitrapaksha" in sb.natal_disclosure({"MOON": ["two_pass_verified"]})
    # the id it names is the id the context reads and the vector pins
    from services.gochara_kernel.chart_context import CANONICAL_AYANAMSHA
    assert CANONICAL_AYANAMSHA == "lahiri_chitrapaksha"


def test_the_tiers_are_read_once_and_feed_both_the_disclosure_and_the_observed_field(built, monkeypatch):
    w = built
    _verified(w)
    calls = []
    real = sb.natal_input_tiers
    monkeypatch.setattr(sb, "natal_input_tiers", lambda *a, **k: calls.append(1) or real(*a, **k))
    d = sb.build_payload(w.conn, CHART_ID, GEN, sealing_commit="abcdef1")["disclosures"]
    assert len(calls) == 1 and d["natal_inputs"] == sb.natal_disclosure(d["natal_input_tiers"])


# ── G6: one build, and the pinned one ───────────────────────────────────────────────────────────────────────────────

ANOTHER = "22222222-2222-4222-8222-222222222222"


def _second_build_row(w, tier="single"):
    w.conn.execute(
        "INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha, start_iso, end_iso,"
        " build_id, verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, NULL, lord_graha, start_iso, end_iso,"
        " %s::uuid, %s FROM public.chart_dashas WHERE system_id = 'vimshottari' AND level_n = 1 LIMIT 1", (ANOTHER, tier))


def test_a_clean_single_pinned_build_is_accepted_by_both_sides(built):
    w = built
    assert dasha_read.assert_single_pinned_build(w.conn, CHART_ID) == ["7377833e-5d3b-4e70-8bef-1318904f470e"]
    _verified(w)
    assert inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN)["consumed"] > 0


@pytest.mark.parametrize("tier", ["two_pass_verified", "single", "classical_match"])
def test_a_second_build_of_any_tier_refuses_the_writer_and_the_verifier_by_name(built, tier):
    w = built
    _verified(w)                                                                      # the world was built and verified on one build
    _second_build_row(w, tier)                                                       # …then an L1 rebuild leaves a MIX
    with pytest.raises(dasha_read.DashaBuildRefused, match="settled_build_ambiguous") as exc:
        dasha_read.load_pinned_vimshottari(w.conn, CHART_ID)
    assert exc.value.code == "settled_build_ambiguous" and isinstance(exc.value, dasha_read.DD.DashaReadConflict)
    with pytest.raises(RuntimeError, match="settled_build_ambiguous"):          # G12: the verifier's INDEPENDENT derivation runs at CAPTURE (against live L1)
        inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN, against_live=True)
    inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN)        # ... and the built generation, owning its copy, still verifies


def test_a_null_build_id_counts_as_a_second_build(built):
    w = built
    w.conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso, end_iso,"
                   " build_id, verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso,"
                   " end_iso, NULL, 'single' FROM public.chart_dashas WHERE level_n = 1 LIMIT 1")
    with pytest.raises(dasha_read.DashaBuildRefused, match="settled_build_ambiguous.*NULL"):
        dasha_read.assert_single_pinned_build(w.conn, CHART_ID)


def test_an_ungoverned_rebuilt_population_refuses_and_stales_the_old_snapshot(built):
    w = built
    _verified(w)
    w.conn.execute("UPDATE public.chart_dashas SET build_id = %s::uuid", (ANOTHER,))
    with pytest.raises(dasha_read.DashaBuildRefused, match="settled_build_absent"):
        dasha_read.load_pinned_vimshottari(w.conn, CHART_ID)
    with pytest.raises(RuntimeError, match="settled_build_absent"):
        inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN, against_live=True)
    inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN)        # the generation's own copy is unaffected by a later rebuild
    # Verification never relabels the snapshot that consumed the previous build.
    stored, live = w.conn.execute(
        "SELECT dasha_digest, public.ka_gochara_search_dasha_digest(chart_id, consumed_dasha_row_ids)"
        " FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
        (CHART_ID, GEN)).fetchone()
    assert live != stored


def test_other_systems_and_other_ayanamshas_do_not_count_as_builds(built):
    w = built
    w.conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso, end_iso,"
                   " build_id, verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, 'yogini', 1, lord_graha, start_iso, end_iso,"
                   " %s::uuid, 'single' FROM public.chart_dashas WHERE level_n = 1 LIMIT 1", (ANOTHER,))
    assert dasha_read.assert_single_pinned_build(w.conn, CHART_ID) == ["7377833e-5d3b-4e70-8bef-1318904f470e"]


# ── (d) the absolute probe ──────────────────────────────────────────────────────────────────────────────────────────

def test_the_pinned_reference_is_the_agreed_constant_for_the_sun_at_the_j2000_instant():
    assert ivv.ABSOLUTE_PROBE_JD == 2451545.0 and ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG == 256.5156961838706
    assert ivv.ABSOLUTE_PROBE_TOLERANCE_DEG == 1e-9


@requires_swieph
def test_the_real_probe_reproduces_the_constant_on_the_pinned_corpus_from_the_main_thread_and_from_fresh_threads():
    got = ivv.derive_absolute_probe(EPHE_PATH)
    assert abs(got - ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG) <= ivv.ABSOLUTE_PROBE_TOLERANCE_DEG, got
    box = {}
    t = threading.Thread(target=lambda: box.update(v=ivv.derive_absolute_probe(EPHE_PATH)))
    t.start()
    t.join()
    assert abs(box["v"] - ivv.ABSOLUTE_PROBE_SUN_LAHIRI_DEG) <= ivv.ABSOLUTE_PROBE_TOLERANCE_DEG, box   # a fresh thread (per-thread state on Linux)


# ── J-4p: both independently implemented sides accept the chart's settled build ─────────────────────────────────────

@pytest.mark.parametrize("build", [
    "7377833e-5d3b-4e70-8bef-1318904f470e",
])
def test_reader_and_independent_verifier_accept_the_same_single_build(build):
    from datetime import datetime, timezone
    a, b = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    row = {"dasha_row_id": "11111111-1111-4111-8111-111111111111", "level_n": 1,
           "parent_row_id": None, "lord_graha": "Saturn", "start_iso": a, "end_iso": b,
           "build_id": build, "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha",
           "verification_pass_status": "two_pass_verified"}
    assert dasha_read.select_dasha_read_contract(CHART_ID, [row])["build_id"] == build
    assert inv.check_dasha_population([row], [row], chart_id=CHART_ID,
                                      horizon=(a, b), consumed_ids=[row["dasha_row_id"]]) == []


def test_historical_reference_rows_keep_their_own_build_provenance():
    from services.gochara_rules import permission
    # The historical literal rows must not be relabelled as the selected live build.
    assert permission.REFERENCE_DASHA_BUILD_ID == "75524b3e-102a-43ec-8cee-3f57fee752c3"
    assert "build_id" not in permission.DASHA_READ_CONTRACT
