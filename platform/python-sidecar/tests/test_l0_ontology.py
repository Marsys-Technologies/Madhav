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


class TestVargaEntityClass:
    """ADHIṢṬHĀNA Lane A3 — registry completion.

    brahma_ontology had NO entity_class='varga' before this lane, and existing
    synonyms did not include the storage-format codes actually used in
    chart_facts (e.g. 'MAR', 'RAH_MEAN', 'HOUSE_07', 'D9'). These tests pin
    the reconciled 30-varga set (l0_reference.VARGAS' 19 ∪ ga_vargas_writer's
    ALL_30_VARGAS 30 = the writer's 30, l0_reference's 19 fully contained
    within it) and the storage-code synonym additions for planets/houses.
    """

    EXPECTED_VARGA_NUMBERS = {
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 20, 21, 24, 27, 30,
        32, 33, 40, 45, 50, 54, 60, 108, 150, 2700,
    }

    def test_30_varga_entities_present(self):
        mod = _get_module()
        vargas = [e for e in mod.ENTITIES if e["entity_class"] == "varga"]
        assert len(vargas) == 30, f"Need 30 varga entities, got {len(vargas)}"

    def test_varga_canonical_ids_match_writer_set(self):
        mod = _get_module()
        vargas = [e for e in mod.ENTITIES if e["entity_class"] == "varga"]
        got_ids = {e["canonical_id"] for e in vargas}
        expected_ids = {f"d{n}" for n in self.EXPECTED_VARGA_NUMBERS}
        assert got_ids == expected_ids

    def test_every_varga_has_bare_d_code_synonym(self):
        """Each varga entity must carry its bare 'D<n>' storage code so
        ref_entity_resolve('D9') etc. resolve."""
        mod = _get_module()
        vargas = {e["canonical_id"]: e for e in mod.ENTITIES if e["entity_class"] == "varga"}
        for n in self.EXPECTED_VARGA_NUMBERS:
            e = vargas[f"d{n}"]
            assert f"D{n}" in e["synonyms"], f"d{n} missing bare 'D{n}' synonym"

    def test_every_varga_has_citation(self):
        mod = _get_module()
        vargas = [e for e in mod.ENTITIES if e["entity_class"] == "varga"]
        for e in vargas:
            assert e.get("source_citation"), f"varga {e['canonical_id']} missing source_citation"

    def test_resolve_d9_prefers_varga_class(self):
        """D9 already collides with the pre-existing concept/navamsa row's
        'D9' synonym (additive-only constraint forbids removing that legacy
        synonym) — Python resolve() just needs SOME correct hit; the DB-side
        ORDER BY tie-break (resolve_entity.ts) is what makes 'varga' win
        deterministically at the SQL layer."""
        mod = _get_module()
        e = mod.resolve("D9")
        assert e is not None
        assert e["entity_class"] in ("varga", "concept")

    def test_resolve_d150_to_varga(self):
        """D150 has no pre-existing concept-class collision — must resolve
        cleanly to entity_class='varga'."""
        mod = _get_module()
        e = mod.resolve("D150")
        assert e is not None
        assert e["entity_class"] == "varga"
        assert e["canonical_id"] == "d150"


class TestStorageCodeSynonyms:
    """ADHIṢṬHĀNA Lane A3 — storage-code synonyms for planets/houses that
    actually appear in chart_facts.fact_subject (live-verified against
    482012f1-710e-4a25-994a-93821f5871aa 2026-08-08)."""

    PLANET_STORAGE_CODES = {
        "sun": ["SUN"],
        "moon": ["MOON"],
        "mars": ["MAR", "MARS"],
        "mercury": ["MER", "MERCURY"],
        "jupiter": ["JUP", "JUPITER"],
        "venus": ["VEN", "VENUS"],
        "saturn": ["SAT", "SATURN"],
        "rahu": ["RAH_MEAN", "RAHU"],
        "ketu": ["KET_MEAN", "KETU"],
        "ascendant": ["LAGNA"],
        "midheaven": ["MC"],
    }

    def test_planet_storage_codes_present(self):
        mod = _get_module()
        planets = {e["canonical_id"]: e for e in mod.ENTITIES if e["entity_class"] == "planet"}
        for cid, codes in self.PLANET_STORAGE_CODES.items():
            for code in codes:
                assert code in planets[cid]["synonyms"], \
                    f"planet/{cid} missing storage-code synonym '{code}'"

    def test_resolve_mar_to_mars(self):
        mod = _get_module()
        e = mod.resolve("MAR")
        assert e is not None
        assert e["canonical_id"] == "mars"

    def test_resolve_rah_mean_to_rahu(self):
        mod = _get_module()
        e = mod.resolve("RAH_MEAN")
        assert e is not None
        assert e["canonical_id"] == "rahu"

    def test_house_storage_codes_present(self):
        mod = _get_module()
        houses = {e["canonical_id"]: e for e in mod.ENTITIES if e["entity_class"] == "house"}
        for h in range(1, 13):
            cid = f"house_{h:02d}"
            padded = f"HOUSE_{h:02d}"
            unpadded = f"HOUSE_{h}"
            assert padded in houses[cid]["synonyms"], f"{cid} missing '{padded}'"
            assert unpadded in houses[cid]["synonyms"], f"{cid} missing '{unpadded}'"

    def test_resolve_house_07_to_seventh_house(self):
        mod = _get_module()
        e = mod.resolve("HOUSE_07")
        assert e is not None
        assert e["canonical_id"] == "house_07"

    def test_resolve_house_7_to_seventh_house(self):
        mod = _get_module()
        e = mod.resolve("HOUSE_7")
        assert e is not None
        assert e["canonical_id"] == "house_07"


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
