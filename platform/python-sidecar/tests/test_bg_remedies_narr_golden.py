"""Narr golden-value test for bg_remedies.prescription_text and charity_action.

Pure generators in brahmagyan.l0_remedy_corpus (no database). Expected sentences are written by
hand from the classical correspondences: Moon -> Monday (rice, milk ...), Mercury -> Wednesday
(green gram), Saturn -> Saturday with the Saturn beej mantra, and the Ashlesha nakshatra
devata Sarpa with its Vimshottari lord Mercury.
"""
from __future__ import annotations

from brahmagyan.l0_remedy_corpus import _gen_nakshatra_mantra_rows, gen_planet_matrix


def _by_id(rows: list[dict]) -> dict[str, dict]:
    return {r["remedy_id"]: r for r in rows}


def test_bg_remedies_charity_row_narrates_item_day_and_planet():
    row = _by_id(gen_planet_matrix())["moon_matrix_charity_rice"]
    assert row["prescription_text"] == (
        "Donate rice to the needy / a temple / a Brahmin on Monday (for Moon propitiation). "
        "Consistent donation on the planet's day pacifies its afflictions."
    )


def test_bg_remedies_charity_action_states_item_and_day():
    row = _by_id(gen_planet_matrix())["moon_matrix_charity_rice"]
    assert row["charity_action"] == "Donate rice on Monday."


def test_bg_remedies_multiword_item_and_two_day_planet():
    rows = _by_id(gen_planet_matrix())
    charity_action = rows["mercury_matrix_charity_green_gram_moong"]["charity_action"]
    assert charity_action == "Donate green gram (moong) on Wednesday."
    charity_action = rows["ketu_matrix_charity_sesame"]["charity_action"]
    assert charity_action == "Donate sesame on Saturday/Tuesday."


def test_bg_remedies_mantra_row_names_saturn_beej_and_saturday():
    prescription_text = _by_id(gen_planet_matrix())["saturn_matrix_mantra"]["prescription_text"]
    assert prescription_text == (
        "Recite the Saturn beej mantra 'Om Praam Preem Praum Sah Shanaischaraya Namah' "
        "108 times daily on Saturday, facing east. "
        "Complete mahadasha-count japa over the dasha period."
    )


def test_bg_remedies_nakshatra_row_names_devata_and_vimshottari_lord():
    prescription_text = _by_id(_gen_nakshatra_mantra_rows())["nakshatra_ashlesha_mantra"]["prescription_text"]
    assert prescription_text == (
        "For birth in Ashlesha nakshatra: recite the nakshatra devata mantra "
        "'Om Sarpebhyo Namah' 108 times daily, especially on the day ruled by Mercury. "
        "The presiding deity is Sarpa (Nagas). This propitiation pacifies afflictions to "
        "the natal Moon/lagna when in this nakshatra. Nakshatra shanti is prescribed in "
        "BPHS Ch.94, which supplies the presiding devata; the 'Om <devata> Namah' "
        "recitation form itself is a constructed nama-mantra, not BPHS text."
    )
