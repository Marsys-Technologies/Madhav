"""Golden-value narration fidelity test for bg_vedha_malefic_scale.effect_description (brahmagyan.l0_phaladeepika_vedha.seed_vedha_malefic_scale).

Phaladeepika Adh. XXVI PG353 (battle / muhurta context) pairs the malefic count 1..5 with the grades fear, failure, killing (blood-shed), death, ignominy. The seeded sentence for a row
is the template 'Vedha caused by <count in words> malefic(s): <grade>.' followed by the project's own editorial note that names the scale and distinguishes it from the PG349:C1 scale.
The expected strings are stated by hand from that rule and the passage's pairing, never read from the builder. A fake connection records the upsert parameters (no database).
"""
from __future__ import annotations

from brahmagyan.l0_phaladeepika_vedha import seed_vedha_malefic_scale

_NOTE = (
    " (This is the PG353 scale — explicitly a battle/muhurta-context vedha scale — distinct from the "
    "OTHER 1-5 malefic-count scale Adh. XXVI also carries, at PG349:C1: agitation, fear, loss, "
    "disease, death, a general-transit context. bg_vedha_malefic_scale seeds PG353 only.)"
)


class _Cursor:
    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self._conn.upserts.append(params)


class _Conn:
    def __init__(self):
        self.upserts = []

    def cursor(self):
        return _Cursor(self)

    def commit(self):
        return None


def test_vedha_scale_effect_description_pairs_each_malefic_count_with_its_grade():
    conn = _Conn()
    seed_vedha_malefic_scale(conn)
    by_count = {p[1]: p for p in conn.upserts}
    assert sorted(by_count) == [1, 2, 3, 4, 5]
    effect_description = by_count[1][3]
    assert effect_description == "Vedha caused by one malefic: fear." + _NOTE
    effect_description = by_count[3][3]
    assert effect_description == "Vedha caused by three malefics: killing (blood-shed)." + _NOTE
    effect_description = by_count[5][3]
    assert effect_description == "Vedha caused by five malefics: ignominy." + _NOTE
