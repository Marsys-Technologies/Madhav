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

# Same BPHS Ch.26 graha-drishti doctrine as GRAHA_DRISHTI_BPHS_26 above, but
# naming the RASI DRISHTI (whole-sign aspect) rendering specifically -- BPHS
# Ch.26's own base doctrine is sign-counted ("the planet aspects the Nth sign
# from its own"), with degree-point contact (`GRAHA_DRISHTI_BPHS_26`'s
# `SPECIAL_DRISHTI_DEG` usage) a finer refinement of the same rule for
# point/graha-anchored targets. Distinguished here (D-5 RED-D fix,
# 2026-07-20) so a reviewer can tell, from the citation string alone, which
# geometry a `drishti_contact` sentence actually used -- a whole-sign span
# (bhava target, no target_longitude_deg) vs. an exact-degree contact.
GRAHA_DRISHTI_RASI_BPHS_26 = (
    "BPHS Ch.26 — Graha Drishti, rasi drishti rendering (whole-sign special "
    "aspect: planet aspects specific SIGNS counted from its own occupied "
    "sign, not a degree point -- the base doctrine's natural application to "
    "a bhava/span target)"
)

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

# ── Jupiter–Saturn double transit: RETIRED (switched off), attribution only ───
# The former constant here (DOUBLE_GOCHARA_PHALADEEPIKA_26, "Phaladeepika Ch.26
# §double-gochara ...") was copied from migration 397's seed rows; the passage it
# named does not exist in the corpus (migration 565 records the CORPUS_GAP; three
# independent reviews 2026-09-29 and the sealed Pravāha v3.0 doctrine label the
# rule modern K.N. Rao practice, `uncited_extension`). Struck under the provenance
# audit DOUBLE-TRANSIT-PROVENANCE-20261027; the rule itself (permission generator
# #10, composition operator, kernel path P4, the seven bg_transit_rules rows) is
# SWITCHED OFF under the panel closure FOURQ-CLOSURE-20261027: status
# `retired_pending_reauthor`, nothing served, nothing scored, re-admission only via
# a panel-verified classical citation and a forward-only test. The attribution
# string is what the seven retired rows carry in place of the struck citation (the
# migration's text is byte-identical to it); it is never a `classical_citation` in
# code because it cites no classical locus (B.10 / §N.7.6). None of these are in
# __all__: they are not citation strings and must not enter the W2.9 catalog.
DOUBLE_TRANSIT_COMMENTARIAL_ATTRIBUTION = (
    "Modern practice (K.N. Rao school, 20th c.); no page-anchored classical "
    "statement in corpus (migration 565 CORPUS_GAP); sole joint precedent claimed: "
    "Phaladīpikā XVII.12 — unverified"
)
DOUBLE_TRANSIT_RULING_REF = "DOUBLE-TRANSIT-PROVENANCE-20261027"   # the provenance audit
FOURQ_CLOSURE_RULING_REF = "FOURQ-CLOSURE-20261027"                # the panel closure: switched off
STATUS_RETIRED_PENDING_REAUTHOR = "retired_pending_reauthor"
#: the seven bg_transit_rules double_transit rows START with this (migration 1412) -- the table has no status column,
#: so the status rides as a citation prefix (the precedent: node vedha rows start with UNSOURCED, migration 1320);
#: every consumer that reads bg_transit_rules for serving skips a row whose citation starts with it
RETIRED_CITATION_PREFIX = "RETIRED_PENDING_REAUTHOR"
DOUBLE_TRANSIT_RETIRED_REASON = (
    f"{STATUS_RETIRED_PENDING_REAUTHOR}: the Jupiter–Saturn double transit is switched off "
    f"(ruling {FOURQ_CLOSURE_RULING_REF}; provenance {DOUBLE_TRANSIT_RULING_REF}) — not evaluated, "
    "not served, not scored; re-admission only via a panel-verified classical citation and a forward-only test"
)

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
    "GRAHA_DRISHTI_RASI_BPHS_26",
    "VAKRA_RETROGRADE_BPHS_27",
    "KAKSHYA_BPHS_66",
    "ASHTAKAVARGA_AV_GATES",
    "ASHTAKAVARGA_BPHS_26",
    "TARA_BALA_MUHURTA_CHINTAMANI",
    "SADE_SATI_BPHS_71",
    "SARVATOBHADRA_MUHURTA_CHINTAMANI",
    "SARVATOBHADRA_VEDHA_PRASNA_MARGA",
]
