"""SR-DOCTRINE-H, migration 1401: L0 holds Rahu/Ketu moolatrikona + own signs (BPHS ch.47) and the node-friendship pairs, each with its citation.

Static test (no database): it parses the literal SQL of migration 1401 and pins it to (a) the doctrine, stated here independently of the seed,
(b) the two committed seeds the L0 writer rebuilds from (`brahmagyan/l0_dignity_reference.py`, `pipeline/orchestrator/writers/bg_dignity_reference.py`)
- a migration alone would be undone by the next writer rebuild, so the SQL and the seeds must agree - and (c) the shape of the change (additive,
no degree range invented, Saturn combustion untouched). The apply/replay/rebuild behaviour against a real database is
`scripts/governance/__tests__/test_sr_doctrine_h_node_dignity_1401.py`.

Doctrine, quoted from the SERVED texts as recorded in the owner-doctrine answers (ANSWERS.md v2.1 B.5 and H, REVIEW_OPUS_v2_1.md; B.3 / B.10):
  * BPHS ch.47 (served chunks bphs:PG573:C2 to bphs:PG574:C1): "The Moola trikonas of Rahu and Ketu are Gemini and Sagittarius respectively. The own
    signs of Rahu and Ketu are Aquarius and Scorpio in that order. Some learneds have expressed the view that Virgo is the own sign of Rahu and
    Pisces is the own sign of Ketu."
  * BPHS 3.55 translator note (served chunk bphs:PG40:C1, commentary tier): "Rahu: The Sun, Moon and Mars are his enemies. Jupiter, Venus and Saturn
    are his friends. Mercury is his neutral. Ketu: The luminaries are his enemies. Mars, Venus and Saturn are his friends, while Mercury and
    Jupiter are his neutrals."

The migration file is placed under platform/migrations by the campaign cockpit; until then set L0_MIGRATION_1401_PATH to a copy. The test FAILS
(never skips) when the file cannot be found.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE
from pipeline.orchestrator.writers import bg_dignity_reference as W

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"
MIGRATION_NAME = "1401_l0_node_dignity_friendship.sql"

# ── the doctrine, typed here from the served quotations (independent of the seeds) ───────────────────────────────────────────────
BPHS47_CHUNKS = "bphs:PG573:C2 to bphs:PG574:C1"
BPHS47_MT_OWN_LINE = (
    "The Moola trikonas of Rahu and Ketu are Gemini and Sagittarius respectively. "
    "The own signs of Rahu and Ketu are Aquarius and Scorpio in that order."
)
BPHS47_VARIANT_LINE = (
    "Some learneds have expressed the view that Virgo is the own sign of Rahu and Pisces is the own sign of Ketu."
)
NODE_MT_OWN = {"Rahu": ("Gemini", ["Aquarius"]), "Ketu": ("Sagittarius", ["Scorpio"])}

BPHS355_CHUNK = "bphs:PG40:C1"
BPHS355_NOTE_LINE = {
    "Rahu": "Rahu: The Sun, Moon and Mars are his enemies. Jupiter, Venus and Saturn are his friends. Mercury is his neutral.",
    "Ketu": "Ketu: The luminaries are his enemies. Mars, Venus and Saturn are his friends, while Mercury and Jupiter are his neutrals.",
}
# The note, read sentence by sentence: node -> {other graha: relation}. "The luminaries" = Sun and Moon.
BPHS355_NODE_RELATIONS = {
    "Rahu": {"Sun": "enemy", "Moon": "enemy", "Mars": "enemy", "Jupiter": "friend", "Venus": "friend", "Saturn": "friend", "Mercury": "neutral"},
    "Ketu": {"Sun": "enemy", "Moon": "enemy", "Mars": "friend", "Venus": "friend", "Saturn": "friend", "Mercury": "neutral", "Jupiter": "neutral"},
}
# The five pairs where migration 250 (cited to an unlocated "UK Ch.4") disagreed with the note, with the 250 relation.
DISPUTED_PAIRS_250 = {
    ("Rahu", "Mercury"): "friend",
    ("Rahu", "Mars"): "neutral",
    ("Rahu", "Jupiter"): "neutral",
    ("Ketu", "Sun"): "neutral",
    ("Ketu", "Moon"): "neutral",
}


def _migration_path() -> Path:
    override = os.environ.get("L0_MIGRATION_1401_PATH")
    return Path(override) if override else MIGRATIONS / MIGRATION_NAME


@pytest.fixture(scope="module")
def sql() -> str:
    path = _migration_path()
    assert path.is_file(), f"migration 1401 not found at {path} (place it under platform/migrations or set L0_MIGRATION_1401_PATH)"
    return path.read_text(encoding="utf-8")


def _strip_comments(text: str) -> str:
    return re.sub(r"--[^\n]*", "", text)


def _unquote(tok: str) -> str | None:
    tok = tok.strip()
    return None if tok == "NULL" else tok[1:-1].replace("''", "'")


def _insert_rows(sql: str, table: str) -> list[list[str]]:
    """The VALUES tuples of the `INSERT INTO <table>` statement, each as a list of raw SQL tokens (string literals, NULL, ARRAY[...]::TEXT[])."""
    body = _strip_comments(sql)
    m = re.search(r"INSERT INTO " + re.escape(table) + r"\s*\(.*?\)\s*VALUES\s*(.*?)\nON CONFLICT", body, re.DOTALL)
    assert m, f"no INSERT INTO {table} ... ON CONFLICT in migration 1401"
    rows, depth, cur, tok, i, s = [], 0, [], "", 0, m.group(1)
    in_str = False
    while i < len(s):
        c = s[i]
        if in_str:
            tok += c
            if c == "'":
                if s[i + 1: i + 2] == "'":
                    tok += "'"
                    i += 1
                else:
                    in_str = False
        elif c == "'":
            in_str = True
            tok += c
        elif c in "([":
            depth += 1
            if depth == 1 and c == "(":
                cur, tok = [], ""
            else:
                tok += c
        elif c in ")]":
            depth -= 1
            if depth == 0 and c == ")":
                cur.append(tok.strip())
                rows.append(cur)
                tok = ""
            else:
                tok += c
        elif c == "," and depth == 1:
            cur.append(tok.strip())
            tok = ""
        elif depth >= 1:
            tok += c
        i += 1
    return rows


def _array(tok: str) -> list[str]:
    inner = re.search(r"ARRAY\[(.*?)\]", tok, re.DOTALL).group(1)
    return [x.strip().strip("'") for x in inner.split(",") if x.strip()]


@pytest.fixture(scope="module")
def sql_dignity(sql) -> dict[str, dict]:
    out = {}
    for g, mt, mt_from, mt_to, own, cite, notes in _insert_rows(sql, "bg_dignity_reference"):
        out[_unquote(g)] = {
            "moolatrikona_sign": _unquote(mt), "moolatrikona_from": _unquote(mt_from), "moolatrikona_to": _unquote(mt_to),
            "own_signs": _array(own), "classical_citation": _unquote(cite), "notes": _unquote(notes),
        }
    return out


@pytest.fixture(scope="module")
def sql_friendship(sql) -> dict[tuple[str, str], tuple[str, str]]:
    return {(_unquote(a), _unquote(b)): (_unquote(rel), _unquote(cite)) for a, b, rel, cite in _insert_rows(sql, "bg_graha_naisargika_friendship")}


def _seed_dignity(graha: str) -> dict:
    (row,) = [r for r in DIGNITY_REFERENCE if r["graha"] == graha]
    return row


def _seed_friendship() -> dict[tuple[str, str], tuple[str, str]]:
    return {(a, b): (rel, cite) for a, b, rel, cite in W._NAISARGIKA_FRIENDSHIP}


# ── claim 1: Rahu and Ketu moolatrikona and own signs are the BPHS ch.47 signs, in L0 and in the rebuild seed ─────────────────────
@pytest.mark.parametrize("graha", ["Rahu", "Ketu"])
def test_node_moolatrikona_and_own_signs_are_the_bphs_47_signs_in_the_migration_and_the_seed(graha, sql_dignity):
    mt, own = NODE_MT_OWN[graha]
    assert (sql_dignity[graha]["moolatrikona_sign"], sql_dignity[graha]["own_signs"]) == (mt, own)
    seed = _seed_dignity(graha)
    assert (seed["moolatrikona_sign"], seed["own_signs"]) == (mt, own)


def test_the_migration_writes_exactly_the_two_node_rows(sql_dignity):
    assert sorted(sql_dignity) == ["Ketu", "Rahu"]


# ── claim 2: the verse gives signs only, so no degree range is invented (B.10) ───────────────────────────────────────────────────
@pytest.mark.parametrize("graha", ["Rahu", "Ketu"])
def test_no_moolatrikona_degree_range_is_invented_for_the_nodes(graha, sql_dignity):
    assert (sql_dignity[graha]["moolatrikona_from"], sql_dignity[graha]["moolatrikona_to"]) == (None, None)
    seed = _seed_dignity(graha)
    assert (seed["moolatrikona_from"], seed["moolatrikona_to"]) == (None, None)


# ── claim 3: each node row carries the served verse's chunk ids and quoted line in its citation column ─────────────────────────────
@pytest.mark.parametrize("graha", ["Rahu", "Ketu"])
def test_node_rows_cite_the_served_bphs_47_chunks_and_quote_the_verse(graha, sql_dignity):
    for cite in (sql_dignity[graha]["classical_citation"], _seed_dignity(graha)["classical_citation"]):
        assert "BPHS Ch.47" in cite and BPHS47_CHUNKS in cite and BPHS47_MT_OWN_LINE in cite, cite
        assert "SR-DOCTRINE-H" in cite and "migration 1401" in cite


# ── claim 4: the minority own-sign reading (Virgo / Pisces) is disclosed, not stored as an own sign ─────────────────────────────────
@pytest.mark.parametrize("graha, variant", [("Rahu", "Virgo"), ("Ketu", "Pisces")])
def test_the_variant_own_sign_is_disclosed_in_the_notes_and_not_stored(graha, variant, sql_dignity):
    assert variant not in sql_dignity[graha]["own_signs"] and variant not in _seed_dignity(graha)["own_signs"]
    for notes in (sql_dignity[graha]["notes"], _seed_dignity(graha)["notes"]):
        assert BPHS47_VARIANT_LINE in notes and BPHS47_CHUNKS in notes, notes


# ── claim 5: the SQL and the rebuild seed carry the same node dignity text (a migration alone is undone by the next rebuild) ──────
@pytest.mark.parametrize("graha", ["Rahu", "Ketu"])
def test_the_migration_equals_the_writer_seed_for_the_node_dignity_rows(graha, sql_dignity):
    seed = _seed_dignity(graha)
    for k in ("moolatrikona_sign", "moolatrikona_from", "moolatrikona_to", "own_signs", "classical_citation", "notes"):
        assert sql_dignity[graha][k] == seed[k], (graha, k)


# ── claim 6: the five node-friendship pairs follow the served BPHS 3.55 note, with its chunk id and quoted line ────────────────────
def test_the_migration_corrects_exactly_the_five_disputed_node_pairs(sql_friendship):
    assert sorted(sql_friendship) == sorted(DISPUTED_PAIRS_250)


@pytest.mark.parametrize("pair", sorted(DISPUTED_PAIRS_250))
def test_each_disputed_pair_takes_the_served_relation_and_cites_the_note(pair, sql_friendship):
    node, other = pair
    served = BPHS355_NODE_RELATIONS[node][other]
    assert served != DISPUTED_PAIRS_250[pair], "the pair is only 'disputed' if the served note differs from migration 250"
    for rel, cite in (sql_friendship[pair], _seed_friendship()[pair]):
        assert rel == served, pair
        assert BPHS355_CHUNK in cite and BPHS355_NOTE_LINE[node] in cite and "SR-DOCTRINE-H" in cite, cite


def test_every_node_row_of_the_rebuild_seed_now_agrees_with_the_served_note():
    seed = _seed_friendship()
    for node, rels in BPHS355_NODE_RELATIONS.items():
        for other, served in rels.items():
            assert seed[(node, other)][0] == served, (node, other)


def test_the_migration_equals_the_writer_seed_for_the_friendship_rows(sql_friendship):
    seed = _seed_friendship()
    for pair, value in sql_friendship.items():
        assert seed[pair] == value, pair


def test_rows_the_served_note_does_not_state_are_left_alone(sql_friendship):
    """Rahu<->Ketu and every planet-to-node row are not stated by the note: the migration must not touch them (no invented relation, B.10)."""
    for (graha, other) in sql_friendship:
        assert graha in ("Rahu", "Ketu") and other not in ("Rahu", "Ketu")
    seed = _seed_friendship()
    assert seed[("Rahu", "Ketu")] == ("enemy", W._UK_CH4) and seed[("Ketu", "Rahu")] == ("enemy", W._UK_CH4)
    assert len(seed) == 72


# ── claim 7: the change is additive and idempotent (N.3), data-only, and leaves Saturn combustion alone ──────────────────────────
def test_the_migration_is_additive_data_only_and_idempotent(sql):
    body = _strip_comments(sql)
    assert not re.search(r"\b(DROP|DELETE|TRUNCATE|ALTER|CREATE)\b", body, re.IGNORECASE)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\s*;", body, re.IGNORECASE), "transaction ownership belongs to migrate.ts"
    assert body.count("ON CONFLICT (graha) DO UPDATE") == 1 and body.count("ON CONFLICT (graha, other_graha) DO UPDATE") == 1
    assert re.findall(r"\bINSERT INTO (\w+)", body) == ["bg_dignity_reference", "bg_graha_naisargika_friendship"]
    assert not re.search(r"\bUPDATE\s+\w+\s+SET\b", body, re.IGNORECASE)


def test_saturn_combustion_orb_stays_at_15_degrees_sr_q6_l1():
    (saturn,) = [r for r in W._COMBUSTION_ORBS if r[0] == "Saturn"]
    assert saturn[1] == 15


def test_the_migration_does_not_write_the_combustion_table(sql):
    assert "bg_combustion_orbs" not in _strip_comments(sql)


def test_the_node_seed_rows_still_carry_the_exaltation_and_debilitation_signs_unchanged():
    exp = {"Rahu": ("Taurus", "Scorpio"), "Ketu": ("Scorpio", "Taurus")}
    for g, (ex, de) in exp.items():
        seed = _seed_dignity(g)
        assert (seed["exaltation_sign"], seed["debilitation_sign"]) == (ex, de)
