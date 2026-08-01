"""
brahmagyan.l0_class_lifetime_counts — `bg_class_lifetime_counts` L0 global seed.

N_e: the expected lifetime count of each `brahma_event_ontology` event class over a
100-year modelled timeline from birth. This is λ⁰_e, the CHART-INDEPENDENT structural
baseline of the Kāla Kṣetra hazard field (KALA_W2_FIELD_DESIGN §5.1 C-1).

Governing ruling: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md` § ADJUDICATION-2 item 2. Conventions
mirror `l0_class_priors.py` (literal reviewable table + one seed function; APPEND-ONLY
— do not reorder or edit existing rows).

════════════════════════════════════════════════════════════════════════════════
WHAT MAY AND MAY NOT BE A SOURCE (the ruling, in force)
════════════════════════════════════════════════════════════════════════════════

TIER N-i — the ONLY tier that may produce a seeded value. A published demographic /
actuarial / epidemiological statistic carrying ALL SIX of: publisher · edition or
survey round · year · indicator/table identifier · geography+cohort · retrievable URL
or DOI. Transcribed verbatim here together with the arithmetic converting it to a
per-100-year count.  →  `prior_basis='demographic_structural'`

TIER N-ii — derived identity ONLY. A value obtained from an already-seeded Tier N-i
value by a STATED ARITHMETIC IDENTITY, never by judgement. The identity string is
stored. "A reasonable proportion of" is NOT an identity and is FORBIDDEN.
  →  `prior_basis='derived_identity'`

TIER N-iii — NOT SEEDED. `not_computed`; `ka_kshetra` skips the class honestly with
`no_class_prior_row`. This is a shippable outcome and the default.

FORECLOSED ON DOCTRINAL GROUNDS, not merely unavailable:
  · CLASSICAL-TEXT COUNTS. Every śāstric statement about counts (two marriages from a
    dual-sign 7th lord; progeny from Saptāṃśa) is CHART-CONDITIONAL — exactly the
    evidence `P_e`, the noisy-OR promise prior, already carries. Routing it here too
    would double-count the same evidence inside a multiplicative hazard and would seat
    an interpretation in the base-rate slot (B.1 inversion). λ⁰_e is chart-INDEPENDENT
    by construction. A builder may not seed any N_e from a classical rule.
  · COHORT- OR LEL-DERIVED COUNTS. `bg_cohort`'s 10k synthetic charts carry no outcome
    data. The only real event record is the LEL, and the CIRCULARITY GUARD is absolute:
    the field never reads the LEL. Fitting λ⁰ from the same LEL the time-rescaling GOF
    scores against destroys the honest empirical test. THIS MODULE NEVER QUERIES,
    IMPORTS, OR REFERENCES THE LEL — and, per the ruling's anti-circularity guard on
    CLASS SELECTION, *which* classes appear below was decided by SOURCE AVAILABILITY
    ALONE and explicitly not by which classes the native's LEL happens to contain.

════════════════════════════════════════════════════════════════════════════════
ARITHMETIC CONVENTION (binding — so two lanes cannot disagree)
════════════════════════════════════════════════════════════════════════════════
  · N_e = expected count of qualifying events over a 100-year modelled timeline from
    birth, ASSUMING SURVIVAL — no mortality discount, because H is the chart's
    100-year horizon and λ⁰ is flat over it.
  · Per-person-year incidence r        →  N_e = 100 · r
  · Lifetime prevalence p, at-most-once →  N_e = p            (never > 1)
  · Repeatable class                    →  N_e = p · E[count | ≥1], BOTH figures cited
                                            separately in `conversion_arithmetic`.
  · Round to 3 significant figures. Store the RAW source figure AND the conversion
    string (`raw_figure` / `conversion_arithmetic` below).
  · The sourced statistic's INCLUSION CRITERIA must match the class's
    `magnitude_floor` and `evidence_requirements`. Where the published criteria are
    broader and cannot be restricted, DO NOT SEED.
  · `CHECK (class_prior > 0)` is respected by NOT SEEDING, never by flooring to
    epsilon.
  · REFERENCE POPULATION is a property of the L0 row, not of the chart. India, birth
    cohorts ~1955–1985. The same row serves every chart, so a future non-Indian chart
    inherits a LABELLED population mismatch that is served, never hidden (Law 4) —
    which is why `reference_population` is a required, non-empty field on every row.

════════════════════════════════════════════════════════════════════════════════
VERSIONING
════════════════════════════════════════════════════════════════════════════════
`PRIOR_VERSION = 'ne_v01'` — ZERO-PADDED, MANDATORY. `ka_kshetra` selects
`ORDER BY prior_version DESC LIMIT 1`, a STRING sort: unpadded `ne_v10` would sort
below `ne_v2`. A revision is a NEW `ne_v02` row set, never an in-place edit;
retracting a value = seeding `ne_v02` without it, and the class reverts to honest-skip
automatically.
"""
from __future__ import annotations

import logging
from typing import Any, NamedTuple

logger = logging.getLogger(__name__)

# ZERO-PADDED. See the module docstring — this is not cosmetic.
PRIOR_VERSION = "ne_v01"

# The reserved coordinate `ka_kshetra.load_class_lifetime_count` reads.
FACT_KIND = "lifetime_count_per_100y"

RATIFIED_BY = "SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0 §ADJUDICATION-2"

PRIOR_BASIS_DEMOGRAPHIC = "demographic_structural"   # Tier N-i
PRIOR_BASIS_DERIVED = "derived_identity"             # Tier N-ii
VALID_PRIOR_BASES = (PRIOR_BASIS_DEMOGRAPHIC, PRIOR_BASIS_DERIVED)


class LifetimeCountRow(NamedTuple):
    """One N_e row, carrying its full audit trail.

    The six REQUIRED citation elements of Tier N-i map onto fields as:
        publisher            → publisher
        edition/survey round → edition
        year                 → edition_year
        indicator/table id   → indicator_id
        geography + cohort   → reference_population
        retrievable URL/DOI  → source_url
    plus `raw_figure` (the published figure, verbatim) and
    `conversion_arithmetic` (the stated conversion to a per-100-year count), both
    mandated by the ruling's arithmetic convention, and `inclusion_criteria` (what
    the source counts — the field against which the class's `magnitude_floor` match
    is judged).

    Every field is asserted non-empty by `validate_rows()` and by
    `test_l0_class_lifetime_counts.py`. A row that cannot fill one of them is not a
    Tier N-i row and must not be here.
    """
    event_class_id: str
    n_e_per_100y: float
    prior_basis: str
    reference_population: str
    publisher: str
    edition: str
    edition_year: str
    indicator_id: str
    source_url: str
    raw_figure: str
    inclusion_criteria: str
    conversion_arithmetic: str
    ratified_by: str


# ══════════════════════════════════════════════════════════════════════════════
# THE TABLE. Append-only. Every row is Tier N-i or a stated Tier N-ii identity.
# ══════════════════════════════════════════════════════════════════════════════

LIFETIME_COUNT_ROWS: list[LifetimeCountRow] = [

    # ══ childbirth ═══════════════════════════════════════════════════════════
    LifetimeCountRow(
        event_class_id="childbirth",
        n_e_per_100y=3.09,
        prior_basis=PRIOR_BASIS_DEMOGRAPHIC,
        reference_population=(
            "India (national, urban+rural); ALL WOMEN aged 45-49 at survey, i.e. birth "
            "cohorts ~1970-1976"
        ),
        publisher=(
            "International Institute for Population Sciences (IIPS) and ICF, for the "
            "Ministry of Health and Family Welfare, Government of India"
        ),
        edition="National Family Health Survey (NFHS-5), India Report Volume 1, report no. FR375",
        edition_year="2022 (fieldwork 2019-21)",
        indicator_id=(
            "Table 4.5 'Children ever born and living', ALL WOMEN panel, row age 45-49, "
            "column 'Mean number of CEB', p.128"
        ),
        source_url="https://dhsprogram.com/pubs/pdf/FR375/FR375.pdf",
        raw_figure=(
            "3.09 mean children ever born per woman (mean living children 2.84; N=85,264 "
            "women). Same table row, distribution of number of CEB: 3.3% of women aged "
            "45-49 have 0 children ever born"
        ),
        inclusion_criteria=(
            "Live births reported in a full birth history by women aged 45-49, an age at "
            "which childbearing is effectively complete. Matches the class's 'significant' "
            "magnitude_floor and its birth-certificate / hospital-record evidence "
            "requirement: every live birth is a registrable event, so the source counts "
            "neither more nor less than the class does. "
            "POPULATION-BASE MISMATCH, LABELLED NOT HIDDEN (Elevation Law 4): DHS birth "
            "histories are collected from WOMEN ONLY, and no published Indian statistic "
            "gives live births per PERSON or per man. The per-man expectation differs from "
            "this figure by the adult sex ratio and by the male fertility distribution, "
            "neither of which is published for India, so NO adjustment is applied and the "
            "row is served as the per-woman completed-fertility figure it is."
        ),
        conversion_arithmetic=(
            "Completed fertility is ALREADY an expected count per person over a lifetime, "
            "so the per-person-year rule N_e = 100*r does NOT apply here (3.09 is not an "
            "incidence per year). Repeatable-class convention N_e = p * E[count|>=1], with "
            "BOTH figures cited separately and both read off the SAME table row: "
            "p(>=1 birth) = 1 - 0.033 = 0.967; E[count|>=1] = 3.09 / 0.967 = 3.20. "
            "N_e = 0.967 * 3.20 = 3.09 (3 s.f.). Births after age 49 are outside the "
            "survey's window; over the 100-year horizon assuming survival they add nothing "
            "material for women and are unmeasured for men."
        ),
        ratified_by=RATIFIED_BY,
    ),

    # ══ marriage ═════════════════════════════════════════════════════════════
    LifetimeCountRow(
        event_class_id="marriage",
        n_e_per_100y=0.984,
        prior_basis=PRIOR_BASIS_DEMOGRAPHIC,
        reference_population=(
            "India (national, rural+urban, both sexes); persons aged 45-49 at the 2011 "
            "Census, i.e. birth cohorts ~1961-1966"
        ),
        publisher="Office of the Registrar General & Census Commissioner, India (ORGI)",
        edition=(
            "Census of India 2011, Social & Cultural Tables, Table C-2 "
            "(file DDW-0000C-02-fer3-MDDS.xlsx, table code C0402)"
        ),
        edition_year="2011 (reference date 1 March 2011)",
        indicator_id=(
            "Table C-2 'Marital status by age and sex', row INDIA / Total / age 45-49, "
            "columns 'Total: Persons' and 'Never married: Persons'"
        ),
        source_url=(
            "https://censusindia.gov.in/nada/index.php/catalog/10301/download/13413/"
            "DDW-0000C-02-fer3-MDDS.xlsx"
        ),
        raw_figure=(
            "INDIA / Total / age 45-49: total persons 62,318,327; never-married persons "
            "1,002,207 (published counts, both sexes). Never-married share by age: "
            "45-49 1.61%, 50-54 1.52%, 55-59 1.38%"
        ),
        inclusion_criteria=(
            "FIRST marriage only. The census records CURRENT marital status in six mutually "
            "exclusive categories, so 'ever married' = 1 - never-married counts a person "
            "ONCE however many times they marry. Restricting the class to its first "
            "marriage makes it at-most-once BY CONSTRUCTION, which is what licenses the "
            "prevalence convention rather than the repeatable one. "
            "DISCLOSED UNDERCOUNT: E[count|>=1] is UNMEASURED for India — the census "
            "carries no marriage-order variable, and although NFHS-5 collects 'lifetime "
            "number of unions' IIPS publishes no remarriage table for it. N_e is therefore "
            "a LOWER BOUND on total marriage events and the shortfall is exactly the "
            "unpublished remarriage share. Matches the class's 'significant' "
            "magnitude_floor and its marriage-certificate / ceremony-record evidence "
            "requirement."
        ),
        conversion_arithmetic=(
            "Lifetime prevalence p for an at-most-once (restricted-to-first) class -> "
            "N_e = p, never > 1. p = 1 - (never married / total) = "
            "1 - 1,002,207 / 62,318,327 = 1 - 0.016082 = 0.983918 -> 0.984 (3 s.f.). "
            "Age 45-49 is chosen because marriage is essentially complete by then: the "
            "never-married share is flat from 45-49 through 55-59 (1.61% / 1.52% / 1.38%), "
            "so the cohort is uncensored rather than merely young."
        ),
        ratified_by=RATIFIED_BY,
    ),

    # ══ separation ═══════════════════════════════════════════════════════════
    LifetimeCountRow(
        event_class_id="separation",
        n_e_per_100y=0.00806,
        prior_basis=PRIOR_BASIS_DEMOGRAPHIC,
        reference_population=(
            "India (national, rural+urban, both sexes); persons aged 45-49 at the 2011 "
            "Census, i.e. birth cohorts ~1961-1966"
        ),
        publisher="Office of the Registrar General & Census Commissioner, India (ORGI)",
        edition=(
            "Census of India 2011, Social & Cultural Tables, Table C-2 "
            "(file DDW-0000C-02-fer3-MDDS.xlsx, table code C0402)"
        ),
        edition_year="2011 (reference date 1 March 2011)",
        indicator_id=(
            "Table C-2 'Marital status by age and sex', row INDIA / Total / age 45-49, "
            "columns 'Separated: Persons' + 'Divorced: Persons' over 'Total: Persons'"
        ),
        source_url=(
            "https://censusindia.gov.in/nada/index.php/catalog/10301/download/13413/"
            "DDW-0000C-02-fer3-MDDS.xlsx"
        ),
        raw_figure=(
            "INDIA / Total / age 45-49: separated persons 369,587; divorced persons "
            "132,871; total persons 62,318,327 (published counts, both sexes)"
        ),
        inclusion_criteria=(
            "The census 'Separated' and 'Divorced' categories together span both limbs of "
            "the class's chain (physical_separation -> legal_filing -> final_decree) and "
            "match its 'significant' magnitude_floor and its legal-filing / final-decree "
            "evidence requirement. "
            "TWO DISCLOSED UNDERCOUNTS, both in the same direction and neither correctable "
            "from this source: (1) this is POINT PREVALENCE on census day, not "
            "lifetime-ever — a person who separated and later remarried is enumerated as "
            "'Currently married', and one later widowed as 'Widowed'; the age profile of "
            "the category peaks at 35-44 and then falls, which is that artefact showing "
            "itself. (2) Separation is self-reported and stigma-suppressed. The nearest "
            "published CUMULATIVE estimate is 'about 2 per cent of all marriages in India "
            "end in divorce or separation within 20 years of marriage' (Dommaraju 2016, "
            "DLHS-3, DOI 10.1111/j.1728-4457.2016.00127.x, as quoted in Visaria 2022, DOI "
            "10.1007/s42379-022-00117-w) — roughly 2.5x this row. It is deliberately NOT "
            "used: the primary is paywalled (Wiley 403) so only a secondary quotation is "
            "retrievable, and the quantity is per-MARRIAGE over 20 years rather than "
            "per-PERSON over a lifetime. N_e here is a LOWER BOUND."
        ),
        conversion_arithmetic=(
            "Lifetime prevalence p for an at-most-once (restricted-to-first-dissolution) "
            "class -> N_e = p. p = (369,587 + 132,871) / 62,318,327 = 502,458 / 62,318,327 "
            "= 0.0080628 -> 0.00806 (3 s.f.). "
            "Tier N-ii identity check against the marriage row, which is read from the SAME "
            "census table and the SAME row: separation <= marriage, 0.00806 <= 0.984 — "
            "holds."
        ),
        ratified_by=RATIFIED_BY,
    ),

    # ══ relocation ═══════════════════════════════════════════════════════════
    LifetimeCountRow(
        event_class_id="relocation",
        n_e_per_100y=0.376,
        prior_basis=PRIOR_BASIS_DEMOGRAPHIC,
        reference_population=(
            "India (national, rural+urban, both sexes); ALL AGES enumerated at the 2011 "
            "Census. Not cohort-restricted: the published India total row is all-ages, "
            "which for a lifetime-ever measure means younger enumerated persons dilute it "
            "downward relative to a completed 1955-1985 cohort"
        ),
        publisher="Office of the Registrar General & Census Commissioner, India (ORGI)",
        edition=(
            "Census of India 2011, Migration Tables, Table D-2 "
            "(file DS-0000-D02-MDDS.XLSX, table code D0302); denominator from Table C-2 "
            "(file DDW-0000C-02-fer3-MDDS.xlsx), row INDIA / Total / All ages"
        ),
        edition_year="2011 (reference date 1 March 2011)",
        indicator_id=(
            "Table D-2 'Migrants classified by place of last residence, sex and duration of "
            "residence in the place of enumeration - 2011', row INDIA / Total / Total / "
            "Total, column 'Persons'"
        ),
        source_url=(
            "https://censusindia.gov.in/nada/index.php/catalog/10743/download/13855/"
            "DS-0000-D02-MDDS.XLSX"
        ),
        raw_figure=(
            "INDIA total migrants by place of last residence 455,787,621 persons "
            "(277,513,908 elsewhere in the district of enumeration; 118,138,761 other "
            "districts of the state; 54,264,749 inter-state; 5,491,194 last residence "
            "outside India; 379,009 unclassifiable). India total population 1,210,854,977"
        ),
        inclusion_criteria=(
            "The census counts a person as a migrant when their place of LAST residence "
            "differs from the place of enumeration — a durable change of usual residence, "
            "matching the class's 'moderate' magnitude_floor and its address-change-record "
            "evidence requirement. "
            "DISCLOSED UNDERCOUNT — the reason this row is a FIRST-relocation prevalence "
            "and not an event count: the Census D-series, the NSS 64th Round and the PLFS "
            "all classify a migrant by place of LAST residence, SINGULAR. A person who "
            "moved five times is recorded identically to one who moved once. India collects "
            "no repeat-migration or move-count variable at all, so E[count|>=1] is "
            "STRUCTURALLY UNMEASURED, not merely unpublished, and the repeatable-class "
            "convention cannot be applied. Restricting the class to the FIRST relocation "
            "makes it at-most-once by construction and is what licenses the prevalence "
            "convention. N_e is a LOWER BOUND on total relocation events, and for this "
            "class the gap is large. "
            "Cross-check on a different definition, stated not hidden: Census Table D-1 "
            "(place of BIRTH) gives 447,287,419 / 1,210,854,977 = 36.9% ever enumerated "
            "away from birthplace, and the sample surveys on a stricter six-month "
            "usual-residence definition give 28.5% (NSS 64th Round 2007-08, Report 533, "
            "Statement 4.1) and 28.9% (PLFS 2020-21, Statement 1). The four measures "
            "bracket 28.5%-37.6%; the D-2 figure is used because it is a full enumeration "
            "and is the table the governing ruling names."
        ),
        conversion_arithmetic=(
            "Lifetime prevalence p for an at-most-once (restricted-to-first) class -> "
            "N_e = p, never > 1. p = 455,787,621 / 1,210,854,977 = 0.376418 -> 0.376 "
            "(3 s.f.). Numerator from Table D-2, denominator from Table C-2 all-ages total "
            "population; both are the same census, same reference date, same universe."
        ),
        ratified_by=RATIFIED_BY,
    ),

    # ══ foreign_settlement ═══════════════════════════════════════════════════
    LifetimeCountRow(
        event_class_id="foreign_settlement",
        n_e_per_100y=0.0129,
        prior_basis=PRIOR_BASIS_DEMOGRAPHIC,
        reference_population=(
            "India-born persons, all ages, at mid-2020. Not cohort-restricted: the origin "
            "series is published as an all-age stock"
        ),
        publisher=(
            "United Nations, Department of Economic and Social Affairs, Population Division"
        ),
        edition="International Migrant Stock 2020 (POP/DB/MIG/Stock/Rev.2020)",
        edition_year="2020 (stock at mid-year 2020)",
        indicator_id=(
            "Destination-and-origin file, Table 1 'International migrant stock at mid-year "
            "by sex and by region, country or area of destination and origin, 1990-2020', "
            "row destination=WORLD (location code 900) x origin=India (location code 356), "
            "column 2020. Denominator: destination file, Table 2 'Total population at "
            "mid-year by sex and by region, country or area of destination, 1990-2020 "
            "(thousands)', row India (location code 356), column 2020"
        ),
        source_url=(
            "https://www.un.org/development/desa/pd/sites/www.un.org.development.desa.pd/"
            "files/undesa_pd_2020_ims_stock_by_sex_destination_and_origin.xlsx"
        ),
        raw_figure=(
            "17,869,492 India-born international migrants living outside India at mid-2020 "
            "(series 1990-2020: 6,619,431 / 7,153,439 / 7,928,051 / 9,588,533 / 13,221,963 "
            "/ 15,885,657 / 17,869,492). India total population mid-2020 = 1,380,004.385 "
            "thousand = 1,380,004,385"
        ),
        inclusion_criteria=(
            "UN DESA's origin dimension is COUNTRY OF BIRTH, so this counts FIRST-GENERATION "
            "India-born emigrants in durable usual residence abroad. That matches the "
            "class's residency_established irreversibility milestone and its "
            "visa/residency-permit evidence requirement, and its 'significant' "
            "magnitude_floor. "
            "It deliberately EXCLUDES the Ministry of External Affairs 'Overseas Indians' "
            "PIO figure, which counts multi-generational descendants and would overcount a "
            "first-generation settlement event by descent — the exact 'source's inclusion "
            "criteria are broader than the class' failure mode the ruling forbids. "
            "DISCLOSED UNDERCOUNT: this is a STOCK at mid-2020, so a person who settled "
            "abroad and later returned to India is not counted; the class's own ontology "
            "note records that settlement is reversible in principle. N_e is a LOWER BOUND."
        ),
        conversion_arithmetic=(
            "Lifetime prevalence p for an at-most-once class -> N_e = p, never > 1. "
            "Standard emigration-rate convention p = emigrant stock / total resident "
            "population of the origin country = 17,869,492 / 1,380,004,385 = 0.0129489 -> "
            "0.0129 (3 s.f.). Both figures come from the SAME dataset and the SAME mid-2020 "
            "reference date; the denominator file is https://www.un.org/development/desa/pd/"
            "sites/www.un.org.development.desa.pd/files/"
            "undesa_pd_2020_ims_stock_by_sex_and_destination.xlsx . "
            "Denominator sensitivity, stated rather than hidden: using 'India-born persons "
            "alive worldwide' instead (1,380,004,385 - 4,878,704 immigrant stock IN India + "
            "17,869,492 emigrants = 1,392,995,173) gives 0.012828 -> 0.0128, a one-unit "
            "difference in the third significant figure."
        ),
        ratified_by=RATIFIED_BY,
    ),

    # ══ surgery ══════════════════════════════════════════════════════════════
    # SOURCE-SELECTION NOTE (the one place in this table where two published
    # India figures competed, so the choice is recorded rather than left implicit):
    # the widely-cited alternative is 904 per 100,000/year (Weiser et al., Bull
    # World Health Organ 2016;94(3):201-209F, DOI 10.2471/BLT.15.159293, Table 4).
    # It is NOT used, on the ruling's own inclusion-criteria test, for two reasons
    # that both point the same way: (a) India appears only in that paper's Table 4,
    # "…for 128 Member States … with MISSING surgical volume data" — 904 is a
    # regression IMPUTATION from health expenditure per capita, not a measurement;
    # (b) its universe is broader than this class — it counts all operating-theatre
    # procedures under anaesthesia including outpatient ones, whereas the class
    # floor is 'significant'. The figure used below is MEASURED, national, and
    # restricted to "major (those requiring anesthesia)". The two are reconciled by
    # the chosen paper itself, verbatim: "Our national major surgical rate falls
    # much below the modeled rate of 904 per 100 000 people, while the total
    # surgical rate is comparable to the LCoGS estimate." Both figures are recorded
    # in inclusion_criteria so a Verifier can re-adjudicate the choice, not just
    # re-check the arithmetic.
    LifetimeCountRow(
        event_class_id="surgery",
        n_e_per_100y=0.356,
        prior_basis=PRIOR_BASIS_DEMOGRAPHIC,
        reference_population=(
            "India (national), all ages, financial year 2019; aggregated from 737 districts "
            "across 37 states/union territories. Not cohort-restricted: the published "
            "figure is a single cross-sectional national rate"
        ),
        publisher="Wolters Kluwer / IJS Publishing Group — International Journal of Surgery",
        edition=(
            "Zadey S, et al. 'Population-level surgical rates and unmet need in India: a "
            "retrospective analysis of districts and states from 2011 to 2019.' "
            "Int J Surg, vol. 110 no. 3, pp. 1884-1887"
        ),
        edition_year="2024 (published 4 Jan 2024; data financial year 2019)",
        indicator_id=(
            "'major surgical rate' per 100,000 people, Results paragraph 1 and Fig. 1A; "
            "derived from India's Health Management and Information System (HMIS) count "
            "data obtained via the National Data and Analytics Platform (NDAP)"
        ),
        source_url="10.1097/JS9.0000000000001024",
        raw_figure=(
            "VERBATIM: 'In the financial year 2019, total and major surgical rates were "
            "1385.28 and 355.94 per 100 000 people, pointing to the unmet need of 49 "
            "million surgical procedures.' The MAJOR rate, 355.94, is the figure used; "
            "1385.28 (total = major + minor) is not"
        ),
        inclusion_criteria=(
            "The paper's definition, VERBATIM: 'HMIS count data was obtained for major "
            "(those requiring anesthesia), minor, and total surgeries (sum of major and "
            "minor)…'. The MAJOR series is used precisely because 'requiring anaesthesia' "
            "is the discriminator that matches the class's 'significant' magnitude_floor "
            "and its medical/procedure-record evidence requirement; the total series "
            "(1385.28) folds in minor procedures and would be the 'source counts every "
            "minor procedure, off by an order of magnitude' failure the governing ruling "
            "names for health-domain classes. The paper itself notes the divergence is "
            "growing: 'The average annual changes were 9.24 and 4.16% for total and major "
            "surgical rates, pointing to a greater rise in minor procedures.' "
            "THREE DISCLOSURES, none adjusted for, because no Tier N-i India figure exists "
            "to adjust with: "
            "(1) PRIVATE-SECTOR UNDERCOUNT, stated by the authors VERBATIM: 'These "
            "estimates may not be comprehensive due to the limited coverage of private "
            "facilities in HMIS, data completeness, and quality issues.' India's private "
            "sector carries a large share of hospital care, so N_e is a LOWER BOUND. "
            "(2) A HIGHER PUBLISHED ALTERNATIVE EXISTS and is recorded rather than "
            "suppressed: 904 per 100,000/year (Weiser et al. 2016, DOI "
            "10.2471/BLT.15.159293, Table 4), which would give N_e = 0.904. It is not used "
            "because it is imputed for India rather than measured, and because its universe "
            "is broader than this class — see the source-selection note above the row. A "
            "Verifier who re-adjudicates that choice should change this row, not patch it. "
            "(3) TEMPORAL MISMATCH — a single FY2019 cross-sectional rate is applied flat "
            "across the 100-year horizon, per the ruling's own convention that lambda-zero "
            "is flat over H. The paper measures major-surgery rates rising 4.16% per year "
            "over 2011-2019, so the rate a 1955-1985 cohort experienced in its earlier "
            "decades was materially lower."
        ),
        conversion_arithmetic=(
            "Per-person-year incidence r -> N_e = 100 * r. The source is already an event "
            "RATE (major operations per 100,000 population per YEAR), not a prevalence, so "
            "the repeatable-class p * E[count|>=1] decomposition does not apply and is not "
            "needed: a person's second operation is counted as a second event, which is "
            "exactly what N_e means. r = 355.94 / 100,000 = 0.0035594 major operations per "
            "person per year. N_e = 100 * 0.0035594 = 0.35594 -> 0.356 (3 s.f.). No "
            "mortality discount, per the ruling: H is the chart's 100-year horizon assuming "
            "survival."
        ),
        ratified_by=RATIFIED_BY,
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# Validation — run at import time in tests, and again before any write.
# ══════════════════════════════════════════════════════════════════════════════

# Field names that must be a non-empty string on every row. `n_e_per_100y` is
# excluded (it is a float, checked separately) and so is nothing else: the whole
# point of Tier N-i is that ALL six citation elements are present.
REQUIRED_TEXT_FIELDS = (
    "event_class_id", "prior_basis", "reference_population", "publisher",
    "edition", "edition_year", "indicator_id", "source_url", "raw_figure",
    "inclusion_criteria", "conversion_arithmetic", "ratified_by",
)


def validate_rows(rows: list[LifetimeCountRow] | None = None) -> None:
    """Fail LOUDLY on any row that is not a complete, well-formed Tier N-i/N-ii row.

    This is the §N.8 detector for the claim "every seeded value is properly sourced".
    The code paths that make it correctly read FALSE are real and are exercised in
    `test_l0_class_lifetime_counts.py`: a blank citation element, a non-URL
    `source_url`, a `prior_basis` outside the two permitted values, a non-positive
    `n_e_per_100y`, and a duplicate `event_class_id` each raise here.

    It deliberately does NOT claim to verify that the cited source SAYS what the row
    claims, nor that `conversion_arithmetic` is correct. That is the Verifier's
    independent two-pass re-derivation (ADJUDICATION-2 item 7) — self-report is not
    evidence, and this function is self-report.
    """
    rows = LIFETIME_COUNT_ROWS if rows is None else rows

    seen: set[str] = set()
    for row in rows:
        for field in REQUIRED_TEXT_FIELDS:
            value = getattr(row, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"l0_class_lifetime_counts: row {row.event_class_id!r} has an empty or "
                    f"non-string {field!r}. Tier N-i requires ALL SIX citation elements plus "
                    f"the raw figure and conversion string — an incomplete row is not a "
                    f"downgrade, it is not seedable at all (ADJUDICATION-2 source hierarchy)."
                )

        if row.prior_basis not in VALID_PRIOR_BASES:
            raise ValueError(
                f"l0_class_lifetime_counts: row {row.event_class_id!r} has "
                f"prior_basis={row.prior_basis!r}; must be one of {VALID_PRIOR_BASES}. "
                f"The DB CHECK brahma_class_priors_lifetime_basis_ck enforces the same set."
            )

        if not row.source_url.startswith(("http://", "https://", "doi:", "10.")):
            raise ValueError(
                f"l0_class_lifetime_counts: row {row.event_class_id!r} has a source_url "
                f"that is not a retrievable URL or DOI: {row.source_url!r}. "
                f"'Retrievable' is one of the six required citation elements."
            )

        if not isinstance(row.n_e_per_100y, (int, float)) or row.n_e_per_100y <= 0:
            raise ValueError(
                f"l0_class_lifetime_counts: row {row.event_class_id!r} has "
                f"n_e_per_100y={row.n_e_per_100y!r}. brahma_class_priors CHECK "
                f"(class_prior > 0) is respected by NOT SEEDING a class, never by "
                f"flooring to epsilon."
            )

        if row.event_class_id in seen:
            raise ValueError(
                f"l0_class_lifetime_counts: duplicate event_class_id "
                f"{row.event_class_id!r}. The PK would silently collapse the two rows "
                f"into whichever was written last."
            )
        seen.add(row.event_class_id)


def compose_source_ref(row: LifetimeCountRow) -> str:
    """The six-element citation, in the ruling's own order, as one auditable string.

    Stored in `brahma_class_priors.source_ref`, whose NOT-NULL-for-lifetime-rows is
    enforced by `brahma_class_priors_lifetime_basis_ck` (migration 522).
    """
    return (
        f"{row.publisher} · {row.edition} · {row.edition_year} · {row.indicator_id} · "
        f"{row.reference_population} · {row.source_url}"
    )


def compose_citation(row: LifetimeCountRow) -> str:
    """The raw figure, what the source actually counts, and the conversion arithmetic.

    Stored in `brahma_class_priors.citation`. Kept SEPARATE from `source_ref` on
    purpose: `source_ref` answers "where did this come from and can I go read it",
    `citation` answers "what exactly did it say and how did that become this number".
    A Verifier re-deriving the value independently needs both, and needs to be able to
    tell which is which.
    """
    return (
        f"raw_figure: {row.raw_figure} | inclusion_criteria: {row.inclusion_criteria} "
        f"| conversion: {row.conversion_arithmetic}"
    )


# ══════════════════════════════════════════════════════════════════════════════
# The seed function.
# ══════════════════════════════════════════════════════════════════════════════

def seed_class_lifetime_counts(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """Upsert every N_e row into `brahma_class_priors` at the reserved coordinate.

    Returns {"brahma_class_priors": <rows_upserted>,
             "classes_not_seeded": <ontology classes with no Tier N-i source>}.

    `classes_not_seeded` is counted from `brahma_event_ontology` and reported so the
    honest per-class coverage gap is a NUMBER IN THE BUILD LOG, not a silence. It is
    computed with a real query, not asserted (§N.8); when the ontology table is
    unreachable it is reported as -1 rather than as 0, because 0 would read exactly
    like "full coverage".

    autocommit: if False, the caller owns the transaction (the orchestrator passes
    False — §N.2 forbids a writer committing `ctx.db_conn`).
    """
    validate_rows()
    total_expected = len(LIFETIME_COUNT_ROWS)

    if dry_run:
        logger.info(
            "[L0/class_lifetime_counts] dry_run — would upsert %d rows at "
            "fact_kind=%s prior_version=%s",
            total_expected, FACT_KIND, PRIOR_VERSION,
        )
        return {"brahma_class_priors": total_expected, "classes_not_seeded": -1}

    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS count FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='brahma_class_priors' "
            "AND column_name IN ('prior_basis','source_ref')"
        )
        row = cur.fetchone()
        present = row["count"] if isinstance(row, dict) else row[0]
        if present != 2:
            raise RuntimeError(
                "brahma_class_priors is missing prior_basis/source_ref — apply "
                "migration 522 first. Writing N_e rows without them would bypass "
                "brahma_class_priors_lifetime_basis_ck, which is the whole point of "
                "the constraint (ADJUDICATION-2 item 1)."
            )

        upserted = 0
        for r in LIFETIME_COUNT_ROWS:
            cur.execute(
                """
                INSERT INTO brahma_class_priors
                  (prior_version, signal_type_class, fact_kind, source_subsystem,
                   signal_tradition, class_prior, prior_basis, source_ref,
                   citation, ratified_by)
                VALUES (%s, %s, %s, '*', '*', %s, %s, %s, %s, %s)
                ON CONFLICT (prior_version, signal_type_class, fact_kind,
                             source_subsystem, signal_tradition)
                DO UPDATE SET class_prior = EXCLUDED.class_prior,
                              prior_basis = EXCLUDED.prior_basis,
                              source_ref  = EXCLUDED.source_ref,
                              citation    = EXCLUDED.citation,
                              ratified_by = EXCLUDED.ratified_by
                """,
                (
                    PRIOR_VERSION, r.event_class_id, FACT_KIND,
                    r.n_e_per_100y, r.prior_basis, compose_source_ref(r),
                    compose_citation(r), r.ratified_by,
                ),
            )
            upserted += 1

        # ── Honest per-class coverage gap, MEASURED (§N.8) — never assumed ──────
        #
        # WRAPPED IN A SAVEPOINT, and that is load-bearing, not defensive style.
        # This probe is ADVISORY: it must never fail the build, so it is caught. But
        # in Postgres, catching the Python exception is NOT enough — a failed
        # statement puts the whole transaction into `InFailedSqlTransaction` and
        # every subsequent command, including the orchestrator's own work and every
        # LATER writer sharing `ctx.db_conn`, is refused until a rollback. Swallowing
        # the exception without rolling back would convert an advisory probe into a
        # silent poisoning of someone else's transaction. Found by running this
        # against a real Postgres where `brahma_event_ontology` was absent — the
        # exact condition the try/except exists for.
        #
        # A SAVEPOINT is not a commit: §N.2's "never commits or closes ctx.db_conn"
        # is respected. The orchestrator's own per-substep savepoint is unaffected;
        # this one nests inside it and is always released.
        not_seeded = -1
        probe_sp = "ne_coverage_probe"
        try:
            cur.execute(f"SAVEPOINT {probe_sp}")
        except Exception:  # noqa: BLE001 — no transaction to nest in; skip the probe
            probe_sp = ""
        if probe_sp:
            try:
                cur.execute(
                    "SELECT COUNT(*) AS count FROM brahma_event_ontology "
                    "WHERE event_class_id <> ALL(%s)",
                    ([r.event_class_id for r in LIFETIME_COUNT_ROWS] or [""],),
                )
                got = cur.fetchone()
                not_seeded = got["count"] if isinstance(got, dict) else got[0]
                cur.execute(f"RELEASE SAVEPOINT {probe_sp}")
            except Exception:  # noqa: BLE001 — coverage reporting must never fail the build
                cur.execute(f"ROLLBACK TO SAVEPOINT {probe_sp}")
                cur.execute(f"RELEASE SAVEPOINT {probe_sp}")
                logger.warning(
                    "[L0/class_lifetime_counts] could not count unseeded ontology "
                    "classes; reporting -1 (unknown) rather than 0 (which would read as "
                    "full coverage). Transaction rolled back to savepoint — the caller's "
                    "transaction is intact."
                )

    if autocommit:
        conn.commit()

    logger.info(
        "[L0/class_lifetime_counts] upserted %d rows at fact_kind=%s prior_version=%s; "
        "%s ontology class(es) NOT seeded (no Tier N-i source — ka_kshetra skips each "
        "with no_class_prior_row)",
        upserted, FACT_KIND, PRIOR_VERSION,
        "unknown" if not_seeded < 0 else not_seeded,
    )
    return {"brahma_class_priors": upserted, "classes_not_seeded": not_seeded}
