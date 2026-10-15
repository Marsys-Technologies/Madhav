"""bg_ontology bootstrap dasha_system rows must carry the catalog owner's ids (census run A: bg_ontology wrote 729, live is 728).

l0_ontology seeds five dasha_system rows with ON CONFLICT DO NOTHING (a bootstrap subset for resolver availability); bg_dasha_systems owns the class, deletes every
dasha_system row and re-seeds its 20. A bootstrap id that is not in the catalog is therefore a stray row that exists only between the two builds, which made
bg_ontology record one more row than stays live. Pure Python: no database.
"""
from brahmagyan.l0_dasha_systems import DASHA_SYSTEMS
from brahmagyan.l0_ontology import ENTITIES, resolve


def test_every_bootstrap_dasha_system_id_is_a_catalog_id():
    catalog = {d["canonical_id"] for d in DASHA_SYSTEMS}
    boot = {e["canonical_id"] for e in ENTITIES if e["entity_class"] == "dasha_system"}
    assert boot and boot <= catalog, sorted(boot - catalog)
    assert len(catalog) == 20


def test_the_old_spelling_still_resolves_as_a_synonym():
    assert resolve("jaimini_chara")["canonical_id"] == "chara_jaimini"
    assert resolve("chara_jaimini")["entity_class"] == "dasha_system"


def test_no_dasha_system_id_is_listed_twice():
    ids = [e["canonical_id"] for e in ENTITIES if e["entity_class"] == "dasha_system"]
    assert len(ids) == len(set(ids))
