"""A5.3 — round 16 (prepared): F-R16-6 (the natal sentence names the exact stored ayanamsha id; one tier read), G6 (a single, pinned daśā build — writer
AND verifier), and (d) the verifier's ABSOLUTE ephemeris probe against a pinned constant."""
from __future__ import annotations

import threading

import pytest

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
    assert dasha_read.assert_single_pinned_build(w.conn, CHART_ID) == ["75524b3e-102a-43ec-8cee-3f57fee752c3"]
    _verified(w)
    assert inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN)["consumed"] > 0


@pytest.mark.parametrize("tier", ["two_pass_verified", "single", "classical_match"])
def test_a_second_build_of_any_tier_refuses_the_writer_and_the_verifier_by_name(built, tier):
    w = built
    _verified(w)                                                                      # the world was built and verified on one build
    _second_build_row(w, tier)                                                       # …then an L1 rebuild leaves a MIX
    with pytest.raises(dasha_read.DashaBuildRefused, match="dasha_builds_mixed") as exc:
        dasha_read.load_pinned_vimshottari(w.conn, CHART_ID)
    assert exc.value.code == "dasha_builds_mixed" and isinstance(exc.value, dasha_read.DD.DashaReadConflict)
    with pytest.raises(RuntimeError, match="dasha_builds_mixed"):
        inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN)


def test_a_null_build_id_counts_as_a_second_build(built):
    w = built
    w.conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso, end_iso,"
                   " build_id, verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso,"
                   " end_iso, NULL, 'single' FROM public.chart_dashas WHERE level_n = 1 LIMIT 1")
    with pytest.raises(dasha_read.DashaBuildRefused, match="dasha_builds_mixed.*NULL"):
        dasha_read.assert_single_pinned_build(w.conn, CHART_ID)


def test_a_single_build_that_is_not_the_pinned_one_is_refused_by_both_sides(built):
    w = built
    _verified(w)
    w.conn.execute("UPDATE public.chart_dashas SET build_id = %s::uuid", (ANOTHER,))
    with pytest.raises(dasha_read.DashaBuildRefused, match="dasha_build_not_pinned"):
        dasha_read.load_pinned_vimshottari(w.conn, CHART_ID)
    with pytest.raises(RuntimeError, match="dasha_build_not_pinned"):
        inv.validate_consumed_dasha_population(w.conn, chart_id=CHART_ID, generation=GEN)


def test_other_systems_and_other_ayanamshas_do_not_count_as_builds(built):
    w = built
    w.conn.execute("INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, lord_graha, start_iso, end_iso,"
                   " build_id, verification_pass_status) SELECT gen_random_uuid(), chart_id, ayanamsha_id, 'yogini', 1, lord_graha, start_iso, end_iso,"
                   " %s::uuid, 'single' FROM public.chart_dashas WHERE level_n = 1 LIMIT 1", (ANOTHER,))
    assert dasha_read.assert_single_pinned_build(w.conn, CHART_ID) == ["75524b3e-102a-43ec-8cee-3f57fee752c3"]


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


# ── F-R17-2: the canonical daśā build id is pinned in exactly two governed places, and they can never drift ────────────

def test_the_two_governed_pins_of_the_canonical_dasha_build_are_equal():
    from services.gochara_rules import permission
    assert permission.DASHA_READ_CONTRACT["build_id"] == inv._C_BUILD == "75524b3e-102a-43ec-8cee-3f57fee752c3"


def test_the_canonical_dasha_build_is_pinned_in_no_other_governed_module():
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    hits = sorted(str(p.relative_to(root)) for d in ("services", "pipeline") for p in (root / d).rglob("*.py")
                  if "75524b3e-102a-43ec-8cee-3f57fee752c3" in p.read_text())
    assert hits == ["services/gochara_kernel/inventory_verifier.py", "services/gochara_rules/permission.py"], hits
