"""
test_l0_ontology.py — Unit tests for brahmagyan.l0_ontology (BRAHMA-BG-0-5)

Tests:
    1. Volume floor: >= 100 total entities
    2. Entity class breakdown: planets, nakshatras, signs, houses, dasha_systems, domains, concepts
    3. Resolve: 'Shani' -> saturn (planet)
    4. Resolve: 'shravana' -> nakshatra (native Sun nakshatra sector)
    5. Resolve: 'purva_bhadrapada' -> nakshatra 25 (native Moon nakshatra)
    6. Resolve: 'chandra' -> moon
    7. Resolve: 'career' -> domain
    8. Resolve: case-insensitive 'SATURN'
    9. Resolve: unknown term -> None
    10. All entities have source_citation
    11. No duplicate canonical_ids within same entity_class
    12. dry_run: returns correct total without DB writes
    13. 27 nakshatras present
    14. 12 signs present
    15. 12 houses present
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest


def _get_module():
    from brahmagyan import l0_ontology as mod
    return mod


class TestVolumeFloor:
    def test_total_entities_gte_100(self):
        mod = _get_module()
        assert len(mod.ENTITIES) >= 100, f"Need >= 100 entities, got {len(mod.ENTITIES)}"

    def test_27_nakshatras(self):
        mod = _get_module()
        naks = [e for e in mod.ENTITIES if e["entity_class"] == "nakshatra"]
        assert len(naks) >= 27, f"Need 27 nakshatras, got {len(naks)}"

    def test_12_signs(self):
        mod = _get_module()
        signs = [e for e in mod.ENTITIES if e["entity_class"] == "sign"]
        assert len(signs) >= 12, f"Need 12 signs, got {len(signs)}"

    def test_12_houses(self):
        mod = _get_module()
        houses = [e for e in mod.ENTITIES if e["entity_class"] == "house"]
        assert len(houses) >= 12, f"Need 12 houses, got {len(houses)}"

    def test_planets_present(self):
        mod = _get_module()
        planets = [e for e in mod.ENTITIES if e["entity_class"] == "planet"]
        assert len(planets) >= 9, f"Need >= 9 planets, got {len(planets)}"

    def test_domains_present(self):
        mod = _get_module()
        domains = [e for e in mod.ENTITIES if e["entity_class"] == "domain"]
        assert len(domains) >= 10, f"Need >= 10 domains, got {len(domains)}"


class TestResolve:
    def test_resolve_shani_to_saturn(self):
        mod = _get_module()
        e = mod.resolve("Shani")
        assert e is not None
        assert e["canonical_id"] == "saturn"
        assert e["entity_class"] == "planet"

    def test_resolve_chandra_to_moon(self):
        mod = _get_module()
        e = mod.resolve("chandra")
        assert e is not None
        assert e["canonical_id"] == "moon"

    def test_resolve_purva_bhadrapada(self):
        """Native Moon nakshatra."""
        mod = _get_module()
        e = mod.resolve("purva_bhadrapada")
        assert e is not None
        assert "bhadrapada" in e["canonical_id"].lower()
        assert e["entity_class"] == "nakshatra"

    def test_resolve_shravana(self):
        """Sun is in Shravana sector (Capricorn) at native birth."""
        mod = _get_module()
        e = mod.resolve("shravana")
        assert e is not None
        assert e["entity_class"] == "nakshatra"

    def test_resolve_career_domain(self):
        mod = _get_module()
        e = mod.resolve("career")
        assert e is not None
        assert e["entity_class"] == "domain"

    def test_resolve_case_insensitive(self):
        mod = _get_module()
        e = mod.resolve("SATURN")
        assert e is not None
        assert e["canonical_id"] == "saturn"

    def test_resolve_unknown_returns_none(self):
        mod = _get_module()
        assert mod.resolve("uranus") is None
        assert mod.resolve("xyzabc123") is None

    def test_resolve_mangal_to_mars(self):
        mod = _get_module()
        e = mod.resolve("mangal")
        assert e is not None
        assert e["canonical_id"] == "mars"

    def test_resolve_guru_to_jupiter(self):
        mod = _get_module()
        e = mod.resolve("guru")
        assert e is not None
        assert e["canonical_id"] == "jupiter"

    def test_resolve_vimshottari(self):
        mod = _get_module()
        e = mod.resolve("vimshottari")
        assert e is not None
        assert e["entity_class"] == "dasha_system"

    def test_resolve_north_node_to_rahu(self):
        mod = _get_module()
        e = mod.resolve("north_node")
        assert e is not None
        assert e["canonical_id"] == "rahu"

    def test_resolve_1h_to_first_house(self):
        mod = _get_module()
        e = mod.resolve("1h")
        assert e is not None
        assert e["entity_class"] == "house"


class TestDataIntegrity:
    def test_all_entities_have_source_citation(self):
        mod = _get_module()
        for e in mod.ENTITIES:
            assert e.get("source_citation"), \
                f"Missing source_citation for {e['entity_class']}/{e['canonical_id']}"

    def test_no_duplicate_canonical_ids_within_class(self):
        mod = _get_module()
        seen: dict[str, set[str]] = {}
        for e in mod.ENTITIES:
            cls = e["entity_class"]
            cid = e["canonical_id"]
            if cls not in seen:
                seen[cls] = set()
            assert cid not in seen[cls], \
                f"Duplicate canonical_id '{cid}' in class '{cls}'"
            seen[cls].add(cid)

    def test_all_entities_have_canonical_name_en(self):
        mod = _get_module()
        for e in mod.ENTITIES:
            assert e.get("canonical_name_en"), \
                f"Missing canonical_name_en for {e['entity_class']}/{e['canonical_id']}"

    def test_all_entities_have_synonyms_list(self):
        mod = _get_module()
        for e in mod.ENTITIES:
            assert isinstance(e.get("synonyms"), list), \
                f"synonyms must be list for {e['canonical_id']}"


class TestDryRun:
    def test_dry_run_total_gte_100(self):
        mod = _get_module()
        result = mod.seed_ontology(conn=None, dry_run=True)
        assert result["total"] >= 100

    def test_dry_run_no_db_writes(self):
        mod = _get_module()
        mock_conn = MagicMock()
        mod.seed_ontology(conn=mock_conn, dry_run=True)
        mock_conn.cursor.assert_not_called()
        mock_conn.commit.assert_not_called()

    def test_dry_run_returns_by_class(self):
        mod = _get_module()
        result = mod.seed_ontology(conn=None, dry_run=True)
        assert "by_class" in result
        assert "planet" in result["by_class"]
        assert "nakshatra" in result["by_class"]
