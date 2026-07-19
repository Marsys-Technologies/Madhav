"""
gochara_grammar.citations — codebase-attested classical citation strings.

B.10 (CLAUDE.md §N + BRIEF_D5 §6): "Claude never invents numerical chart
values" / "never invent a citation string." Every constant below is copied
verbatim from a citation string ALREADY present elsewhere in this codebase
(migration comments, `brahmagyan/l0_reference.py` classical-reference rows,
`ga_*_writer.py` docstrings/citation_human strings) -- not newly authored
chapter/verse attributions. Provenance is recorded per constant so a reviewer
can trace each string back to its source file.

Where NO codebase-attested citation exists for a primitive's technique, the
primitive marks its sentences `uncited_extension=True` instead of reaching
for this module -- see `primitives.py`'s per-family docstring for the
citation-or-uncited decision and reasoning on every one of the 12 families.
"""
from __future__ import annotations

# Source: platform/migrations/266_bg_transit_tables.sql header comment +
# bg_transit_engine/bg_transit_rules table comments.
GOCHARA_PHALA_BPHS_29 = "BPHS Ch.29 — Gochara Phala (transit results)"
GRAHA_GATI_BPHS_22 = "BPHS Ch.22 — Graha Gati (planetary motion parameters)"
PHALADEEPIKA_VEDHA_26 = "Phaladeepika Ch.26 — Gochara Vedha"

# Source: platform/python-sidecar/brahmagyan/l0_reference.py graha_drishti /
# poorna_drishti / ardha_drishti / pada_drishti rows ("source_citation":"BPHS Ch.26").
GRAHA_DRISHTI_BPHS_26 = "BPHS Ch.26 — Graha Drishti (planetary aspects: full/3-quarter/half/quarter by house distance)"

# Source: platform/python-sidecar/brahmagyan/l0_reference.py retrograde row
# ("source_citation":"BPHS Ch.27" — "Apparent backward motion; gives cheshta bala.").
VAKRA_RETROGRADE_BPHS_27 = "BPHS Ch.27 — Vakra (retrogression; cheshta bala)"

# Source: platform/python-sidecar/brahmagyan/l0_reference.py kakshya rows
# ("source_citation":"BPHS Ch.66" / "BPHS Ch.66-72") + ga_strength_writer.py's
# `ashtakavarga_kakshya_boundary` fact_category (8 kaksha sub-arc boundaries
# per lord, real chart_facts rows for chart 482012f1).
KAKSHYA_BPHS_66 = "BPHS Ch.66 — Kakṣyā (Ashtakavarga 1/8-sign sub-division; fine transit strength)"

# Source: platform/supabase/migrations/397_bg_transit_av_gates.sql header +
# COMMENT ON TABLE bg_transit_av_gates ("Source: BPHS ch.66-68 Ashtakavarga;
# Phaladeepika ch.26.") — same migration that seeds the Jupiter+Saturn
# double-transit rows used by the double-transit composition operator.
ASHTAKAVARGA_AV_GATES = "BPHS Ch.66–68 (Ashtakavarga) — bg_transit_av_gates; Phaladeepika Ch.26"

# Source: platform/python-sidecar/ga_writers/ga_strength_writer.py module
# docstring: "sum of all sarva bindus = 337 (classical Parashara constant,
# verified directly from PyJHora's const.ashtaka_varga_dict-driven binna
# computation)" and inline "per BPHS Ch.26 Parasari — this is classically correct".
ASHTAKAVARGA_BPHS_26 = "BPHS Ch.26 — Ashtakavarga (sarvashtakavarga bindu system; 337-bindu Parashara constant)"

# Source: platform/supabase/migrations/397_bg_transit_av_gates.sql double_transit
# rows, e.g. "Phaladeepika ch.26 §double-gochara; Saravali ch.28" /
# "Phaladeepika ch.26 §double-gochara; BPHS ch.29".
DOUBLE_GOCHARA_PHALADEEPIKA_26 = "Phaladeepika Ch.26 §double-gochara (Jupiter+Saturn simultaneous transit); BPHS Ch.29"

# Source: platform/python-sidecar/panchang_engine/tara_bala.py module docstring:
# "Source: Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara;
# Jataka Parijata §Tara Bala computation."
TARA_BALA_MUHURTA_CHINTAMANI = (
    "Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara; "
    "Jataka Parijata §Tara Bala computation"
)

# Source: platform/python-sidecar/ga_writers/ga_sade_sati_writer.py
# PHASE_QUARTER_INTENSITY comment: "per BPHS Ch.71 phase-position rule"
# and CANCELLATION_RULES (8 named rules) computed by that same writer.
SADE_SATI_BPHS_71 = "BPHS Ch.71 — Sade Sati (Saturn's 3-sign transit around natal Moon; phase-position rule)"

# Source: platform/migrations/_archive/140_sarvatobhadra_chakra.sql +
# 144_vedha_extended.sql table comments: "Source: Muhurta Chintamani,
# Jyotish Sara Sangraha." These migrations create l1_sarvatobhadra_positions /
# l1_sarvatobhadra_vedha / l1_vedha_extended but carry NO INSERT rows (schema
# only, confirmed empty at D-5 G-2 build time) -- see sarvatobhadra.py module
# docstring for how this module treats the resulting citation/uncited split.
SARVATOBHADRA_MUHURTA_CHINTAMANI = (
    "Muhurta Chintamani, Jyotish Sara Sangraha (Sarvatobhadra Chakra, 28-nakshatra "
    "9×9 grid; l1_sarvatobhadra_positions/l1_sarvatobhadra_vedha table comments, "
    "platform/migrations/_archive/140_sarvatobhadra_chakra.sql)"
)

# Source: platform/python-sidecar/ga_writers/ga_sensitive_degree_writer.py
# module docstring point 4: "sarvatobhadra_vedha — natal nakshatra vedha in the
# Sarvatobhadra Chakra ... (Prasna Marga / SBC vedha geometry — rekha/kona/vithi
# vedha)."
SARVATOBHADRA_VEDHA_PRASNA_MARGA = (
    "Prasna Marga (Sarvatobhadra Chakra vedha geometry: rekha/kona/vithi vedha); "
    "cf. ga_sensitive_degree_writer.py sarvatobhadra_vedha evidence row"
)

__all__ = [
    "GOCHARA_PHALA_BPHS_29",
    "GRAHA_GATI_BPHS_22",
    "PHALADEEPIKA_VEDHA_26",
    "GRAHA_DRISHTI_BPHS_26",
    "VAKRA_RETROGRADE_BPHS_27",
    "KAKSHYA_BPHS_66",
    "ASHTAKAVARGA_AV_GATES",
    "ASHTAKAVARGA_BPHS_26",
    "DOUBLE_GOCHARA_PHALADEEPIKA_26",
    "TARA_BALA_MUHURTA_CHINTAMANI",
    "SADE_SATI_BPHS_71",
    "SARVATOBHADRA_MUHURTA_CHINTAMANI",
    "SARVATOBHADRA_VEDHA_PRASNA_MARGA",
]
