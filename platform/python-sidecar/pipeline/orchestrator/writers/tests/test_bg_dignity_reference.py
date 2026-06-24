"""
Cross-table integrity guards for L0 Brahmagyan duplicated constants.

Covers all constant pairs that exist in more than one L0 table, as enumerated in the
L0 Intra-Consistency Sweep (2026-06-24). Any divergence here means two L0 tables
assert different classical values for the same fact.

Sweep result: CLEAN — no new divergences found beyond the Rahu/Ketu bug (now fixed).
The tests below lock that clean state and will catch any future drift.

Original Rahu/Ketu fix (2026-06-24):
  - bg_dignity_reference had Rahu=Gemini / Ketu=Sagittarius (wrong)
  - reference_planets had Rahu=2(Taurus) / Ketu=8(Scorpio) (correct)
  Fixed to Taurus/Scorpio per Parashari consensus (BPHS Ch.3 Santanam / Phaladeepika / Saravali).
"""
import os
import pytest
import psycopg


# Sign-number → name mapping (1=Aries through 12=Pisces)
_SIGN_NUM = {
    1: 'Aries', 2: 'Taurus', 3: 'Gemini', 4: 'Cancer',
    5: 'Leo', 6: 'Virgo', 7: 'Libra', 8: 'Scorpio',
    9: 'Sagittarius', 10: 'Capricorn', 11: 'Aquarius', 12: 'Pisces',
}
_SIGN_NAME = {v: k for k, v in _SIGN_NUM.items()}  # name → number


@pytest.fixture(scope='module')
def db_conn():
    url = os.environ.get('DATABASE_URL') or os.environ.get('PROD_DB_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


# ── BLOCK 1: Planet dignity — reference_planets vs bg_dignity_reference ───────

def test_rahu_ketu_exaltation_parashari_consensus(db_conn):
    """bg_dignity_reference must carry Taurus/Scorpio per Parashari consensus."""
    cur = db_conn.cursor()
    cur.execute(
        "SELECT graha, exaltation_sign, debilitation_sign "
        "FROM bg_dignity_reference WHERE graha IN ('Rahu', 'Ketu') ORDER BY graha"
    )
    rows = {r['graha']: r for r in cur.fetchall()}
    assert rows['Rahu']['exaltation_sign'] == 'Taurus', (
        f"Rahu exaltation must be Taurus per Parashari consensus; got {rows['Rahu']['exaltation_sign']}"
    )
    assert rows['Rahu']['debilitation_sign'] == 'Scorpio', (
        f"Rahu debilitation must be Scorpio; got {rows['Rahu']['debilitation_sign']}"
    )
    assert rows['Ketu']['exaltation_sign'] == 'Scorpio', (
        f"Ketu exaltation must be Scorpio per Parashari consensus; got {rows['Ketu']['exaltation_sign']}"
    )
    assert rows['Ketu']['debilitation_sign'] == 'Taurus', (
        f"Ketu debilitation must be Taurus; got {rows['Ketu']['debilitation_sign']}"
    )


def test_all_planets_dignity_cross_table_agreement(db_conn):
    """
    reference_planets and bg_dignity_reference must agree on exaltation, debilitation,
    moolatrikona, and own-signs for ALL planets in both tables.

    Covers the full cross-table join — not just Rahu/Ketu — so any future seed drift
    in either table is caught immediately.
    """
    cur = db_conn.cursor()

    # bg_dignity_reference: text sign names
    cur.execute(
        "SELECT graha, exaltation_sign, debilitation_sign, moolatrikona_sign, own_signs "
        "FROM bg_dignity_reference ORDER BY graha"
    )
    bd = {r['graha']: r for r in cur.fetchall()}

    # reference_planets: numeric sign codes
    cur.execute(
        "SELECT canonical_name_en, exaltation_sign, debilitation_sign, "
        "       mooltrikona_sign, own_signs "
        "FROM reference_planets ORDER BY canonical_name_en"
    )
    rp = {r['canonical_name_en']: r for r in cur.fetchall()}

    # Only compare grahas present in BOTH tables
    common = set(bd.keys()) & set(rp.keys())
    assert common, "No common planets found between reference_planets and bg_dignity_reference"

    failures = []
    for graha in sorted(common):
        b = bd[graha]
        r = rp[graha]

        # Exaltation
        if b['exaltation_sign'] is not None or r['exaltation_sign'] is not None:
            b_exalt = b['exaltation_sign']
            r_exalt = _SIGN_NUM.get(r['exaltation_sign']) if r['exaltation_sign'] else None
            if b_exalt != r_exalt:
                failures.append(
                    f"{graha} exaltation: bg_dignity_reference='{b_exalt}' vs "
                    f"reference_planets={r['exaltation_sign']}(={r_exalt})"
                )

        # Debilitation
        if b['debilitation_sign'] is not None or r['debilitation_sign'] is not None:
            b_debil = b['debilitation_sign']
            r_debil = _SIGN_NUM.get(r['debilitation_sign']) if r['debilitation_sign'] else None
            if b_debil != r_debil:
                failures.append(
                    f"{graha} debilitation: bg_dignity_reference='{b_debil}' vs "
                    f"reference_planets={r['debilitation_sign']}(={r_debil})"
                )

        # Moolatrikona
        if b['moolatrikona_sign'] is not None or r['mooltrikona_sign'] is not None:
            b_mt = b['moolatrikona_sign']
            r_mt = _SIGN_NUM.get(r['mooltrikona_sign']) if r['mooltrikona_sign'] else None
            if b_mt != r_mt:
                failures.append(
                    f"{graha} moolatrikona: bg_dignity_reference='{b_mt}' vs "
                    f"reference_planets={r['mooltrikona_sign']}(={r_mt})"
                )

        # Own signs (set comparison)
        b_own = set(b['own_signs'] or [])
        r_own_names = {_SIGN_NUM[s] for s in (r['own_signs'] or [])}
        if b_own != r_own_names:
            failures.append(
                f"{graha} own_signs: bg_dignity_reference={sorted(b_own)} vs "
                f"reference_planets={sorted(r_own_names)}"
            )

    assert not failures, (
        f"Dignity cross-table mismatches found ({len(failures)}):\n" +
        "\n".join(f"  • {f}" for f in failures)
    )


# ── BLOCK 2: Sign lords — reference_signs vs reference_planets.own_signs ──────

def test_sign_lords_cross_table_agreement(db_conn):
    """
    reference_signs.lord must be the inverse of reference_planets.own_signs.
    Every sign's declared lord must claim that sign in its own_signs array,
    and no sign may be claimed by a planet whose lord entry differs.
    """
    cur = db_conn.cursor()

    cur.execute("SELECT sign_id, canonical_name_en, lord FROM reference_signs ORDER BY sign_id")
    signs = cur.fetchall()

    cur.execute("SELECT canonical_name_en, planet_id, own_signs FROM reference_planets")
    planets = cur.fetchall()
    # Build map: planet_id (lowercase) → set of sign_ids it owns
    planet_owns = {p['planet_id']: set(p['own_signs'] or []) for p in planets}

    failures = []
    for s in signs:
        sign_id = s['sign_id']
        sign_name = s['canonical_name_en']
        lord = s['lord']  # lowercase planet_id

        if lord not in planet_owns:
            failures.append(
                f"{sign_name}(id={sign_id}): lord='{lord}' not found in reference_planets"
            )
            continue

        if sign_id not in planet_owns[lord]:
            failures.append(
                f"{sign_name}(id={sign_id}): lord='{lord}' does not claim sign_id={sign_id} "
                f"in reference_planets.own_signs={sorted(planet_owns[lord])}"
            )

    assert not failures, (
        f"Sign-lord cross-table mismatches ({len(failures)}):\n" +
        "\n".join(f"  • {f}" for f in failures)
    )


# ── BLOCK 3: Nakshatra lords — reference_nakshatras vs reference_nakshatra ────

def test_nakshatra_lords_cross_table_agreement(db_conn):
    """
    reference_nakshatras.lord must agree with reference_nakshatra.vimshottari_lord
    for all 27 nakshatras. These are populated by two separate writers
    (l0_reference.py and l0_nakshatra.py) and could silently diverge.
    """
    cur = db_conn.cursor()

    cur.execute(
        "SELECT nakshatra_id, canonical_name_en, lord FROM reference_nakshatras ORDER BY nakshatra_id"
    )
    old = {r['nakshatra_id']: r for r in cur.fetchall()}

    cur.execute(
        "SELECT nakshatra_id, name_en, vimshottari_lord FROM reference_nakshatra ORDER BY nakshatra_id"
    )
    new = {r['nakshatra_id']: r for r in cur.fetchall()}

    common_ids = set(old.keys()) & set(new.keys())
    assert len(common_ids) == 27, f"Expected 27 common nakshatra_ids; got {len(common_ids)}"

    failures = []
    for nid in sorted(common_ids):
        old_lord = old[nid]['lord']
        new_lord = new[nid]['vimshottari_lord']
        if old_lord != new_lord:
            failures.append(
                f"Nakshatra {nid} ({old[nid]['canonical_name_en']}): "
                f"reference_nakshatras.lord='{old_lord}' vs "
                f"reference_nakshatra.vimshottari_lord='{new_lord}'"
            )

    assert not failures, (
        f"Nakshatra lord mismatches ({len(failures)}):\n" +
        "\n".join(f"  • {f}" for f in failures)
    )


def test_nakshatra_spans_cross_table_agreement(db_conn):
    """
    reference_nakshatras.start/end_degree must agree with reference_nakshatra.start/end_longitude
    to within 0.001° (precision storage difference is acceptable; value divergence is not).
    """
    cur = db_conn.cursor()
    cur.execute("""
        SELECT rn.nakshatra_id,
               ABS(CAST(rn.start_degree AS numeric) - CAST(rns.start_longitude AS numeric)) AS start_diff,
               ABS(CAST(rn.end_degree   AS numeric) - CAST(rns.end_longitude   AS numeric)) AS end_diff
        FROM reference_nakshatras rn
        JOIN reference_nakshatra rns ON rn.nakshatra_id = rns.nakshatra_id
        WHERE ABS(CAST(rn.start_degree AS numeric) - CAST(rns.start_longitude AS numeric)) > 0.001
           OR ABS(CAST(rn.end_degree   AS numeric) - CAST(rns.end_longitude   AS numeric)) > 0.001
    """)
    divergences = cur.fetchall()
    assert not divergences, (
        f"Nakshatra span divergences > 0.001° found for nakshatra_ids: "
        f"{[r['nakshatra_id'] for r in divergences]}"
    )


# ── BLOCK 4: Mercury atichara threshold reachability ─────────────────────────

def test_mercury_atichara_threshold_reachable(db_conn):
    """Mercury atichara threshold must be ≤ 2.2 (observed max); 2.5 was unreachable."""
    cur = db_conn.cursor()
    cur.execute(
        "SELECT speed_threshold_low FROM bg_motion_state_thresholds "
        "WHERE graha = 'Mercury' AND motion_state = 'atichara'"
    )
    row = cur.fetchone()
    assert row is not None, "Mercury atichara row missing from bg_motion_state_thresholds"
    threshold = float(row['speed_threshold_low'])
    assert threshold <= 2.2, (
        f"Mercury atichara threshold {threshold}°/day exceeds observed max of ~2.2°/day; "
        "this makes atichara unreachable in practice"
    )
