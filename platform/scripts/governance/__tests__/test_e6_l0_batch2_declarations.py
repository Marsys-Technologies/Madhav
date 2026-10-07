"""test_e6_l0_batch2_declarations.py: L0-WAVE batch 2 (planet-keyed classical seeds), declarations (the minor bump of this PR).

Five existing entries of asset_declarations.json gain reviewed declarations, each resting on a fact this file asserts against the source it cites (file:line), with a
mutation test beside every guard that makes the declaration refusable:

  * `vocab_alias` {class planet, identity_only} on bg_dignity_reference (graha), bg_transit_engine (graha), bg_transit_rules (graha), bg_vastu_directions
    (ruling_graha) and bg_kp_sublord_division (star_lord);
  * `prose_fields` [] (evidence_kind writer, no prose_coupling) on bg_transit_engine and bg_kp_sublord_division ONLY.

Strategist ruling: N-94 is general. A Narr [] is honest only for source text stored as loaded (R03) or coupled to a passing D1. bg_dignity_reference (notes, variant_traditions),
bg_vastu_directions (remedy_description) and bg_transit_rules (phala, rule_notes) hold hand-typed classical-claim text with no detector behind it: their prose_fields stay
UNDECLARED (Narr NO_DETECTOR). Case handling is DECLARED in each vocab_alias `why` (the S3 validator has no closed place for a field; adding one is an engine change).
Nothing else moves: no Ldgr, Null, Carr, Dens, Earn or Build declaration is added, and no asset outside the five changes.

Offline: no database. The planet class is read from the ontology SEED (brahmagyan/l0_ontology.py) by syntax tree; the production table is the lead's dry-run read
(DATA_FACTS.sql). The Vocab.alias detector is driven through its own declared-check function with the two database reads replaced by seed-derived data.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _decl_version as _dv  # noqa: E402
import _narr_writer_checks as nw  # noqa: E402

ROOT = ac.ROOT
SC = "platform/python-sidecar/"
BG = SC + "brahmagyan/"
WR = SC + "pipeline/orchestrator/writers/"
PASS, FAIL, NO_DET, NA = ac.PASS, ac.FAIL, ac.NO_DET, ac.NA

DECL = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
ASSETS = DECL["assets"]

VOCAB_ASSETS = {          # asset -> (vocab_column, table)
    "bg_dignity_reference": ("graha", "bg_dignity_reference"),
    "bg_transit_engine": ("graha", "bg_transit_engine"),
    "bg_transit_rules": ("graha", "bg_transit_rules"),
    "bg_vastu_directions": ("ruling_graha", "bg_vastu_directions"),
    "bg_kp_sublord_division": ("star_lord", "bg_kp_sublord_division"),
}
EMPTY_ASSETS = ("bg_transit_engine", "bg_kp_sublord_division")
HELD_NARR_N94 = ("bg_transit_rules", "bg_dignity_reference", "bg_vastu_directions")      # N-94 general: hand-typed classical-claim text, no detector behind it (the batch-2 sentence names all three)
FORMGAP_RELEASED = ("bg_vastu_directions", "bg_transit_rules", "bg_dignity_reference")      # SS N-191 / N-192 (declarations 1.45.0 on): the checked forms (per-key seed vocabularies, curated_corpus) now stand behind the sentences: declared, no longer held
HELD_NARR = tuple(a for a in HELD_NARR_N94 if a not in FORMGAP_RELEASED)
PENDING = "bg_transit_rules"
EARLIER_EMPTY = ("bg_doshas", "bg_ontology", "bg_phaladeepika_latta", "bg_yogas", "bo_laksana_rerank")

# the target tables' columns as the fresh census (REGISTRY_REVISION 16, main adb0db29d) read them from the catalog (census_L0.json target_columns); the alias-like test is
# applied to these, and mutated below
COLUMNS = {
    "bg_dignity_reference": ["classical_citation", "debilitation_degree", "debilitation_sign", "exaltation_degree", "exaltation_sign", "graha", "id", "moolatrikona_from",
                             "moolatrikona_sign", "moolatrikona_to", "notes", "own_signs", "variant_traditions"],
    "bg_transit_engine": ["avg_daily_motion_deg", "classical_citation", "graha", "id", "sign_residence_days", "zodiac_period_days"],
    "bg_transit_rules": ["classical_citation", "graha", "id", "phala", "primary_house", "rule_notes", "rule_type", "vedha_house"],
    "bg_vastu_directions": ["classical_citation", "direction", "direction_deg", "element", "favorable_color", "id", "ruling_graha", "secondary_graha"],
    "bg_kp_sublord_division": ["created_at", "division_index", "end_longitude_deg", "nakshatra_number", "pada_at_end", "pada_at_start", "sign_number", "source_citation",
                               "span_arcmin", "split_by_sign_boundary", "star_lord", "start_longitude_deg", "sub_lord", "table_version"],
}
# registry writer files and count_sql tables (census_L0.json writer_files / count_sql_tables)
WRITER_FILES = {"bg_dignity_reference": ["bg_dignity_reference.py"], "bg_transit_engine": ["bg_transit_rules.py"], "bg_transit_rules": ["bg_transit_rules.py"],
                "bg_vastu_directions": ["bg_vastu_directions.py"], "bg_kp_sublord_division": ["bg_kp_sublord_division.py"]}
OWNED_TABLES = {
    "bg_dignity_reference": ["bg_dignity_reference", "bg_avastha_schemes", "bg_combustion_orbs", "bg_graha_naisargika_friendship", "bg_motion_state_thresholds"],
    "bg_transit_engine": ["bg_transit_engine"], "bg_transit_rules": ["bg_transit_rules"],
    "bg_vastu_directions": ["bg_vastu_directions", "bg_vastu_direction_remedials"], "bg_kp_sublord_division": ["bg_kp_sublord_division"]}


def _src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _line(cite: str) -> str:
    path, n = cite.rsplit(":", 1)
    return _src(path).splitlines()[int(n) - 1]


def _doc(mutate, aid):
    d = copy.deepcopy(DECL)
    mutate(d["assets"][aid])
    return d


def _refused(mutate, aid, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(mutate, aid))


# ───────────────────────── Part 1: the committed entries ─────────────────────────

def test_the_file_version_is_well_formed_and_the_validator_accepts_every_entry():
    assert DECL["version"] == _dv.CURRENT
    ac.validate_declarations(DECL)
    sentence = DECL["description"].split("(L0-WAVE batch 2, planet-keyed classical seeds)", 1)[1]
    for aid in VOCAB_ASSETS:
        assert aid in sentence, aid
    assert "N-94 is general" in sentence and "No other asset or structure changed" in sentence
    for aid in HELD_NARR_N94:
        assert aid in sentence
    for word in ("verbatim", "accurate", "exact"):               # the latta tests pin this vocabulary out of every later sentence
        assert word not in sentence.lower()


L0_FILL_NO_ALIAS_CLASS = ["bg_kota_chakra_rings", "bg_texts", "bg_vedha_malefic_scale", "bg_vidhi_primitives", "bo_drishti", "bo_pramana_mapa"]      # E5.7 L0 fills: `na: no_alias_class`, schema-checked


RESIDUAL_NO_ALIAS = ["bg_ephemeris_engine", "bg_panchanga"]      # residual declaration batch (POST-#3176 item 2)
FORMGAP_PROSE_NONE = ["ga_dashas", "ga_transit_anchors", "bg_sarvatobhadra_grid", "bg_concordance", "bg_text_index", "bg_muhurta_lattice", "bg_nakshatra", "bg_vastu_directions", "bg_transit_rules", "bg_dignity_reference"]      # FORM-GAP (SS N-191, declarations 1.39.0 / 1.40.0)
RESIDUAL_PROSE_NONE = ["bg_class_lifetime_counts", "bg_class_priors", "bg_formula_constants", "bg_ghatana", "bg_gochara_citation_resolution", "bg_kota_chakra_rings", "bg_medical_mappings", "bg_nakshatra_medical", "bg_parihara_rules", "bg_prashna_rules", "bg_sign_medical", "bg_texts", "bg_vidhi_floors", "bg_vidhi_primitives"]      # residual declaration batch (POST-#3176 item 1); bg_dasha_systems, bg_nakshatra and bg_reference left it in the SS audit of 2026-10-06 (their prose_none could not be shown true)


def test_exactly_these_assets_declare_vocab_alias_and_prose_empty_and_nothing_else_of_the_s3_s1_s2_family_moves():
    assert sorted(a for a, e in ASSETS.items() if e.get("vocab_alias")) == sorted(["bg_phaladeepika_latta", *VOCAB_ASSETS, *L0_FILL_NO_ALIAS_CLASS, *RESIDUAL_NO_ALIAS, "bo_upaya"])   # + bo_upaya: planet identity-only form (E5.7 L2 fill)
    assert sorted(a for a, e in ASSETS.items() if e.get("prose_fields") == []) == sorted([*EARLIER_EMPTY, *EMPTY_ASSETS, "bg_ephemeris", "bg_gochara_arcs", *RESIDUAL_PROSE_NONE, "bo_samvada", "bo_drishti", *FORMGAP_PROSE_NONE])   # + bo_samvada: checked prose_none (E5.7 L2 fill); + the FORM-GAP declarations (N-191)
    for aid in VOCAB_ASSETS:                                      # no Ldgr / Null / Carr / coupling declaration is added for these five
        e = ASSETS[aid]
        for key in ("ldgr_source", "null_convention", "prose_coupling"):
            assert key not in e, (aid, key)
        car = e.get("carriage") or {}
        assert car.get("nature") in (None, *ac.CEILING_NATURES) and car.get("spec") is None, aid          # N-156: a declared ceiling (D1 unverified transcription / D3 single derivation) is the only carriage these may declare, never a spec
    assert [a for a, e in ASSETS.items() if "ldgr_source" in e] == ["bg_phaladeepika_latta"]
    assert [a for a, e in ASSETS.items() if "null_convention" in e] == ["bg_phaladeepika_latta"]
    assert [a for a, e in ASSETS.items() if "prose_coupling" in e] == ["bg_phaladeepika_latta"]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_the_vocab_alias_entry_is_the_planet_identity_only_form_on_the_named_column(aid):
    va = ASSETS[aid]["vocab_alias"]
    col, _table = VOCAB_ASSETS[aid]
    assert va["class"] == "planet" and va["vocab_column"] == col and va["identity_only"] is True
    assert set(va) == {"class", "vocab_column", "identity_only", "identity_only_why", "why", "evidence"}
    assert "alias" not in {k for k in va if k == "alias_column"}
    assert "no alias or synonym column" in va["identity_only_why"] and "only identity is measurable" in va["identity_only_why"]
    assert ac._s3_text_problem(va["why"], min_chars=15, min_words=3) is None and ac._s3_evidence_problem(va["evidence"], allow_unverified=False) is None


@pytest.mark.parametrize("aid", EMPTY_ASSETS)
def test_the_prose_empty_entry_is_a_writer_evidenced_positive_claim(aid):
    e = ASSETS[aid]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    ev = e["evidence"]["prose_fields"]
    assert ev.startswith("[] = no generated narration under the SS definition of 2026-10-01")
    cites = ac._EVIDENCE_ANY_CITE_RE.findall(ev)
    assert cites and not ac._EVIDENCE_TEST_PATH_RE.search(ev) and not ac._EVIDENCE_SQL_LINE_RE.search(ev)
    assert "prose_coupling" not in e                              # none of the four declares a carriage: nothing to couple to


@pytest.mark.parametrize("aid", HELD_NARR_N94)
def test_the_held_narr_assets_keep_prose_fields_undeclared_unless_the_checked_forms_released_them(aid):
    e = ASSETS[aid]
    assert e["vocab_alias"]["vocab_column"] == VOCAB_ASSETS[aid][0]            # its Vocab cell is declared either way
    if aid in FORMGAP_RELEASED:
        assert e["prose_fields"] == [] and ac.prose_none_problem(e) is None and e.get("evidence_kind") == "writer"          # released: declared through the checked prose_none forms (SS N-191 / N-192)
    else:
        assert e["prose_fields"] is None and e["evidence"]["prose_fields"] is None and e.get("evidence_kind") is None


# ───────────────────────── Part 2: every cited line really holds what the declaration says ─────────────────────────

VOCAB_DDL = {            # asset -> (migration, line, the table whose CREATE TABLE must enclose the line)
    "bg_dignity_reference": ("platform/migrations/250_bg_dignity_reference.sql", 27, "bg_dignity_reference"),
    "bg_transit_engine": ("platform/migrations/266_bg_transit_tables.sql", 23, "bg_transit_engine"),
    "bg_transit_rules": ("platform/migrations/266_bg_transit_tables.sql", 41, "bg_transit_rules"),
    "bg_vastu_directions": ("platform/migrations/284_bg_vastu_directions.sql", 14, "bg_vastu_directions"),
    "bg_kp_sublord_division": ("platform/supabase/migrations/535_bg_kp_sublord_division.sql", 114, "bg_kp_sublord_division"),
}


@pytest.mark.parametrize("aid", sorted(VOCAB_DDL))
def test_the_vocab_evidence_line_is_the_vocabulary_column_of_that_tables_create_table(aid):
    mig, n, table = VOCAB_DDL[aid]
    assert ASSETS[aid]["vocab_alias"]["evidence"] == f"{mig}:{n}"
    col = VOCAB_ASSETS[aid][0]
    lines = _src(mig).splitlines()
    assert re.match(rf"\s*{col}\s+TEXT\b", lines[n - 1]), lines[n - 1]
    opener = next(i for i in range(n - 1, -1, -1) if re.search(r"CREATE TABLE", lines[i]))
    assert re.search(rf"\b{table}\b", lines[opener]), lines[opener]
    assert "NOT NULL" in lines[n - 1]                             # a vocabulary column that is never empty by DDL


PROSE_NEEDLES = {          # asset -> {(path, line): the text that line must hold}
    "bg_transit_engine": {
        (BG + "l0_transit.py", 1077): "INSERT INTO bg_transit_engine",
        (BG + "l0_transit.py", 96): "BG_TRANSIT_ENGINE: list",
        (BG + "l0_transit.py", 35): 'BPHS_CH22 = "BPHS Ch.22',
        (BG + "l0_transit.py", 970): "{BPHS_CH28}; {PD_CH26}",
        (BG + "l0_transit.py", 964): "BG_TRANSIT_MOORTI: list",
        (WR + "bg_transit_rules.py", 29): "def run(self, ctx"},
    "bg_kp_sublord_division": {
        (BG + "l0_kp_sublord_division.py", 179): "star_lord = PLANET_CYCLE[",
        (BG + "l0_kp_sublord_division.py", 183): "sub_lord = PLANET_CYCLE[",
        (BG + "l0_kp_sublord_division.py", 140): "SOURCE_CITATION = (",
        (BG + "l0_kp_sublord_division.py", 428): "cur.execute(_INSERT_SQL",
        (WR + "bg_kp_sublord_division.py", 57): "f\"bg_kp_sublord_division: {total} divisions"},
}


@pytest.mark.parametrize("aid", EMPTY_ASSETS)
def test_every_cite_in_the_prose_evidence_is_a_line_that_holds_what_is_said_and_no_cite_is_unchecked(aid):
    ev = ASSETS[aid]["evidence"]["prose_fields"]
    cited = {(m.group(1), int(m.group(2))) for m in re.finditer(r"(platform/[A-Za-z0-9_./-]+\.py):([0-9]+)", ev)}
    assert cited == set(PROSE_NEEDLES[aid]), cited ^ set(PROSE_NEEDLES[aid])
    for (path, n), needle in PROSE_NEEDLES[aid].items():
        assert needle in _src(path).splitlines()[n - 1], (path, n)


def _planet_forms():
    """The planet-class entities of the ontology SEED, read by syntax tree: [{canonical_id, canonical_name_en, synonyms}]."""
    tree = ast.parse(_src(BG + "l0_ontology.py"))
    out = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_e" and len(n.args) >= 5
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == "planet"):
            out.append(dict(canonical_id=n.args[1].value, canonical_name_en=n.args[2].value, synonyms=[ast.literal_eval(n.args[4])][0]))
    return out


def _dict_values(rel, key, listname):
    """Every constant string value of `key` in the dict literals under the module-level assignment `listname` (a seed corpus), in order."""
    tree = ast.parse(_src(rel))
    node = next(s for s in tree.body if isinstance(s, ast.AnnAssign if isinstance(s, ast.AnnAssign) else ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == listname for t in ([s.target] if isinstance(s, ast.AnnAssign) else s.targets)))
    out = []
    for d in ast.walk(node):
        if isinstance(d, ast.Dict):
            for k, v in zip(d.keys, d.values):
                if isinstance(k, ast.Constant) and k.value == key and isinstance(v, ast.Constant) and isinstance(v.value, str):
                    out.append(v.value)
    return out


def _migration_397_graha():
    sql = _src("platform/supabase/migrations/397_bg_transit_av_gates.sql")
    block = sql.split("INSERT INTO bg_transit_rules", 1)[1].split("ON CONFLICT", 1)[0]
    return re.findall(r"\('double_transit',\s*'([A-Za-z]+)'", block)


SEED_VALUES = {
    "bg_dignity_reference": lambda: _dict_values(BG + "l0_dignity_reference.py", "graha", "DIGNITY_REFERENCE"),
    "bg_transit_engine": lambda: _dict_values(BG + "l0_transit.py", "graha", "BG_TRANSIT_ENGINE"),
    "bg_transit_rules": lambda: _dict_values(BG + "l0_transit.py", "graha", "BG_TRANSIT_RULES") + _migration_397_graha(),
    "bg_vastu_directions": lambda: _dict_values(BG + "l0_vastu_directions.py", "ruling_graha", "VASTU_DIRECTIONS"),
    "bg_kp_sublord_division": lambda: ast.literal_eval(next(s.value for s in ast.parse(_src(BG + "l0_kp_sublord_division.py")).body
                                                            if isinstance(s, ast.AnnAssign) and getattr(s.target, "id", "") == "PLANET_CYCLE")),
}
GRAHAS9 = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]


def test_the_ontology_seed_holds_the_eleven_planet_class_entities_including_both_nodes():
    forms = _planet_forms()
    assert [f["canonical_id"] for f in forms] == GRAHAS9 + ["ascendant", "midheaven"]
    assert {f["canonical_name_en"] for f in forms} >= {x.title() for x in GRAHAS9}


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_the_seeded_vocabulary_values_are_the_declared_set_and_each_resolves_to_one_planet_entity(aid):
    vals = SEED_VALUES[aid]()
    assert vals, aid
    assert sorted({v.casefold() for v in vals}) == sorted(g for g in GRAHAS9 if aid != "bg_vastu_directions" or g in
                                                         {"mercury", "mars", "sun", "saturn", "jupiter", "venus", "moon", "rahu"})
    spec = _spec(aid)
    pairs = [dict(v=v, n=vals.count(v)) for v in dict.fromkeys(vals)]
    got = ac.grade_vocab_alias(spec, _planet_forms(), pairs)
    assert got["v"] == PASS and got["alias"]["unresolved"] == {}, got["measured"]


def test_the_seeded_value_sets_per_asset_are_pinned():
    assert sorted(SEED_VALUES["bg_dignity_reference"]()) == sorted(x.title() for x in GRAHAS9)
    assert sorted(SEED_VALUES["bg_transit_engine"]()) == sorted(GRAHAS9)
    rules = SEED_VALUES["bg_transit_rules"]()
    assert sorted(set(rules) - set(GRAHAS9)) == ["Jupiter", "Saturn"] and _migration_397_graha().count("Jupiter") == 5 and _migration_397_graha().count("Saturn") == 2
    assert sorted(SEED_VALUES["bg_vastu_directions"]()) == sorted(["Mercury", "Mars", "Sun", "Saturn", "Jupiter", "Venus", "Moon", "Rahu"])
    assert SEED_VALUES["bg_kp_sublord_division"]() == ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]


# ───────────────────────── Part 3: Vocab.alias, the real declared check, offline, with a mutation per guard ─────────────────────────

def _spec(aid):
    va = ASSETS[aid]["vocab_alias"]
    return {"class": va["class"], "vocab_column": va["vocab_column"], "alias_column": va.get("alias_column"), "table": VOCAB_ASSETS[aid][1],
            "identity_only": va.get("identity_only") is True, "identity_only_why": va.get("identity_only_why")}


@pytest.fixture
def offline_reads(monkeypatch):
    """Replace the two database reads of the declared Vocab.alias check with seed-derived data; returns the dict a test mutates."""
    state = dict(forms=_planet_forms(), values=None)

    def fetch_values(table, vcol, acol):
        return [dict(v=v, n=1, a=None) for v in state["values"]]
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda cls: state["forms"])
    monkeypatch.setattr(ac, "alias_fetch_values", fetch_values)
    return state


def _measure(aid, state, *, cols=None, values=None, va=None):
    state["values"] = list(SEED_VALUES[aid]()) if values is None else values
    return ac.vocab_alias_declared_check(aid, va or ASSETS[aid]["vocab_alias"], VOCAB_ASSETS[aid][1], COLUMNS[aid] if cols is None else cols)["Vocab.alias"]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_the_declared_check_reads_pass_on_the_seeded_values(aid, offline_reads):
    got = _measure(aid, offline_reads)
    assert got["v"] == PASS and got["declared"] is True and "identity_only declared" in got["measured"], got["measured"]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_no_catalog_column_of_the_five_tables_is_alias_like(aid):
    assert ac.alias_like_columns(COLUMNS[aid]) == []
    assert VOCAB_ASSETS[aid][0] in COLUMNS[aid]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_mutation_one_stored_value_respelled_to_a_non_ontology_form_fails(aid, offline_reads):
    vals = list(SEED_VALUES[aid]())
    for bad, why in (("Surya", "only an ontology synonym"), ("Uranus", "no match")):
        got = _measure(aid, offline_reads, values=vals + [bad])
        assert got["v"] == FAIL and bad in got["alias"]["unresolved"] and why in got["alias"]["unresolved"][bad]["why"], got["measured"]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_mutation_a_null_value_and_an_empty_table_are_not_a_pass(aid, offline_reads):
    assert _measure(aid, offline_reads, values=list(SEED_VALUES[aid]()) + [None])["v"] == FAIL
    assert _measure(aid, offline_reads, values=[])["v"] == NO_DET


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_mutation_the_vocab_column_naming_a_column_the_table_lacks_fails(aid, offline_reads):
    col = VOCAB_ASSETS[aid][0]
    got = _measure(aid, offline_reads, cols=[c for c in COLUMNS[aid] if c != col])
    assert got["v"] == FAIL and col in got["measured"] and "not columns of" in got["measured"]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
@pytest.mark.parametrize("extra", ["synonyms", "aliases", "alt_name", "also_known_as", "aka"])
def test_mutation_a_table_gaining_an_alias_like_column_refuses_the_identity_only_declaration(aid, extra, offline_reads):
    got = _measure(aid, offline_reads, cols=COLUMNS[aid] + [extra])
    assert got["v"] == NO_DET and got["declaration_disagreements"][0]["field"] == "vocab_alias.alias_column" and extra in got["measured"]


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_mutation_an_empty_planet_class_and_unknown_columns_read_no_detector(aid, offline_reads):
    offline_reads["forms"] = []
    assert _measure(aid, offline_reads)["v"] == NO_DET
    offline_reads["forms"] = _planet_forms()
    assert _measure(aid, offline_reads, cols=[])["v"] == NO_DET                       # the table's columns unknown: not measured, never PASS


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_mutation_without_identity_only_the_same_clean_reading_is_only_partial(aid, offline_reads):
    va = {k: v for k, v in ASSETS[aid]["vocab_alias"].items() if k not in ("identity_only", "identity_only_why")}
    assert _measure(aid, offline_reads, va=va)["v"] == ac.PARTIAL                       # the declared word is what earns PASS, and only for a table with no alias set


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
@pytest.mark.parametrize("mutate, match", [
    (lambda e: e["vocab_alias"].__setitem__("class", "nakshatra"), "must declare na"),
    (lambda e: e["vocab_alias"].__setitem__("vocab_column", "graha; DROP"), "must be a column name"),
    (lambda e: e["vocab_alias"].__setitem__("vocab_column", None), "must be a column name"),
    (lambda e: e["vocab_alias"].__setitem__("alias_column", "synonyms"), "contradicts a declared alias_column"),
    (lambda e: e["vocab_alias"].pop("identity_only_why"), "identity_only_why"),
    (lambda e: e["vocab_alias"].__setitem__("identity_only_why", "n/a"), "identity_only_why"),
    (lambda e: e["vocab_alias"].__setitem__("identity_only", False), "identity_only must be true or absent"),
    (lambda e: e["vocab_alias"].__setitem__("why", "TBD once the reviewer has read it"), "placeholder word"),
    (lambda e: e["vocab_alias"].__setitem__("why", "too short"), "too short"),
    (lambda e: e["vocab_alias"].__setitem__("evidence", "platform/migrations/no_such_file.sql:3"), "not an existing repo-relative file"),
    (lambda e: e["vocab_alias"].__setitem__("evidence", "platform/migrations/284_bg_vastu_directions.sql:99999"), "file has"),
    (lambda e: e["vocab_alias"].__setitem__("na", "no_alias_class"), "declares no alias class"),
    (lambda e: e["vocab_alias"].__setitem__("extra", "x"), "unknown field"),
])
def test_mutation_the_validator_refuses_a_malformed_or_weak_vocab_alias(aid, mutate, match):
    _refused(mutate, aid, match)


# ───────────────────────── Part 4: Narr [] (R03), the real writer scope, the real prose vocabulary ─────────────────────────

EXPECTED_WRITTEN = {
    "bg_dignity_reference": {
        "bg_dignity_reference": ["classical_citation", "debilitation_degree", "debilitation_sign", "exaltation_degree", "exaltation_sign", "graha", "moolatrikona_from",
                                 "moolatrikona_sign", "moolatrikona_to", "notes", "own_signs", "variant_traditions"],
        "bg_graha_naisargika_friendship": ["classical_citation", "graha", "other_graha", "relation"],
        "bg_avastha_schemes": ["classical_citation", "determination_rule", "notes", "scheme_name", "state_name", "state_order"],
        "bg_motion_state_thresholds": ["classical_citation", "graha", "motion_state", "notes", "speed_threshold_high", "speed_threshold_low", "threshold_type",
                                       "typical_speed_dps"],
        "bg_combustion_orbs": ["classical_citation", "deep_orb_degrees", "graha", "orb_degrees", "retrograde_note"]},
    "bg_transit_engine": {"bg_transit_engine": ["avg_daily_motion_deg", "classical_citation", "graha", "sign_residence_days", "zodiac_period_days"]},
    "bg_transit_rules": {"bg_transit_rules": ["classical_citation", "graha", "phala", "primary_house", "rule_notes", "rule_type", "vedha_house"]},
    "bg_vastu_directions": {
        "bg_vastu_directions": ["classical_citation", "direction", "direction_deg", "element", "favorable_color", "ruling_graha", "secondary_graha"],
        "bg_vastu_direction_remedials": ["classical_citation", "direction", "remedy_description", "remedy_type"]},
    "bg_kp_sublord_division": {"bg_kp_sublord_division": ["division_index", "end_longitude_deg", "nakshatra_number", "pada_at_end", "pada_at_start", "sign_number",
                                                          "source_citation", "span_arcmin", "split_by_sign_boundary", "star_lord", "start_longitude_deg", "sub_lord",
                                                          "table_version"]},
}


def _written(aid):
    units, _beyond = ac._delegation_scope(aid, WRITER_FILES[aid])
    return ac.written_columns(units, [VOCAB_ASSETS[aid][1]] + OWNED_TABLES[aid])


def _scoped_vocab():
    """The per-asset vocabulary: every declared prose column scoped to the tables of the assets that declare it, tables read from the committed rev-25 census records of all three layers."""
    census = ROOT / "00_ARCHITECTURE" / "control" / "census"
    tabs = {}
    for ts, L in (("193639", "L0"), ("194909", "L1"), ("195251", "L2")):
        doc = json.loads((census / f"asset_census_2026-10-04T{ts}+0530.json").read_text(encoding="utf-8"))[L]
        for a in doc["assets"]:
            tabs[a["asset_id"]] = {t for t in ([a["target_table"]] if a.get("target_table") else []) + list(a.get("count_sql_tables") or [])}
    return ac.prose_vocabulary(ASSETS, tabs)


def _ctx(aid, written="real", vocabulary=None):
    return dict(table=VOCAB_ASSETS[aid][1], own={}, tests=(), counts=None, paths=[],
                vocabulary=ac.prose_vocabulary(ASSETS) if vocabulary is None else vocabulary, written=_written(aid) if written == "real" else written)


@pytest.mark.parametrize("aid", sorted(EXPECTED_WRITTEN))
def test_the_writer_scope_is_readable_and_writes_exactly_the_pinned_columns_none_of_them_a_declared_prose_column(aid):
    got = _written(aid)
    assert got is not None and {t: sorted(c) for t, c in got.items()} == EXPECTED_WRITTEN[aid]
    assert ac.prose_reverse_leg(got, _scoped_vocab()) == []      # E5.7 (SS 2026-10-06): per-asset scoping; the GLOBAL name match would hit `notes` (bo_pramana_mapa declares it, three L0 writers also write a column of that name)


@pytest.mark.parametrize("aid", EMPTY_ASSETS)
def test_a_bare_empty_prose_fields_reads_no_detector_on_every_narr_and_null_check_with_no_grandfather(aid):
    bare = {k: v for k, v in ASSETS[aid].items() if k != "prose_none"}                    # E5.7 fills converted this asset to a checked prose_none (test_n150_prose_none): the bare form is no release
    out = ac.prose_checks(aid, bare, _ctx(aid))
    for c in ac.NARR_CHECKS + ac.NULL_CHECKS:
        assert out[c]["v"] == ac.NO_DET and "cause" not in out[c] and "prose_none" in out[c]["measured"], (c, out[c])
    cells = ac.rollup_asset("L0", {**out, "Vocab.identity": dict(v=PASS, measured="m")}, ac.facts_for_asset(dict(asset_id=aid, layer="L0"), {**ac.load_asset_declarations(), aid: bare}))
    assert cells["Narr"]["v"] == NO_DET and cells["Null"]["v"] == NO_DET and cells["Carr"]["v"] == NO_DET and cells["Ldgr"]["v"] == NO_DET


@pytest.mark.parametrize("aid", EMPTY_ASSETS)
def test_mutation_a_write_to_a_column_the_declarations_treat_as_narration_fails_narr_agree(aid):
    tbl = VOCAB_ASSETS[aid][1]
    written = {t: set(c) for t, c in _written(aid).items()}
    written[tbl].add("significance")
    out = ac.prose_checks(aid, ASSETS[aid], _ctx(aid, written=written))
    assert out["Narr.agree"]["v"] == FAIL and f"{tbl}.significance" in out["Narr.agree"]["measured"]
    assert all(out[c]["v"] == NO_DET for c in ("Narr.checkable", "Narr.fidelity_test", "Narr.lint"))


@pytest.mark.parametrize("aid", EMPTY_ASSETS)
@pytest.mark.parametrize("written", [None, {}])
def test_mutation_an_unreadable_or_empty_write_scan_reads_no_detector_never_na(aid, written):
    out = ac.prose_checks(aid, ASSETS[aid], _ctx(aid, written=written))
    assert all(out[c]["v"] == NO_DET for c in ac.NARR_CHECKS + ac.NULL_CHECKS)


@pytest.mark.parametrize("aid", HELD_NARR_N94)
def test_a_held_narr_asset_is_not_released_while_prose_fields_is_undeclared(aid):
    if aid in FORMGAP_RELEASED:
        assert ASSETS[aid]["prose_fields"] == []                                 # released by the checked forms: its cells are judged by the FORM-GAP tests, not held here
        return
    out = ac.prose_checks(aid, ASSETS[aid], _ctx(aid))
    assert all(out[c]["v"] == NO_DET and "undeclared" in out[c]["measured"] for c in ac.NARR_CHECKS + ac.NULL_CHECKS)


@pytest.mark.parametrize("aid", EMPTY_ASSETS)
@pytest.mark.parametrize("mutate, match", [
    (lambda e: e["evidence"].__setitem__("prose_fields", None), "evidence.prose_fields must carry a non-blank pointer"),
    (lambda e: e["evidence"].__setitem__("prose_fields", "   "), "non-blank pointer"),
    (lambda e: e["evidence"].__setitem__("prose_fields", "writes no prose, trust the reviewer"), "must cite writer code"),
    (lambda e: e["evidence"].__setitem__("prose_fields", "[] see platform/migrations/250_bg_dignity_reference.sql:27"), "must cite writer code|not writer code"),
    (lambda e: e["evidence"].__setitem__("prose_fields", "[] see platform/scripts/governance/__tests__/test_e6_l0_batch2_declarations.py:1"), "not writer code"),
    (lambda e: e.__setitem__("evidence_kind", "ddl"), "claim about writer code|needs the migration"),
])
def test_mutation_the_validator_refuses_a_prose_empty_claim_without_real_writer_evidence(aid, mutate, match):
    _refused(mutate, aid, match)


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_these_assets_cannot_be_coupled_because_none_declares_a_d1_transcription_carriage(aid):
    e = copy.deepcopy(ASSETS[aid])
    e["prose_fields"] = []
    e["prose_coupling"] = dict(to="carriage_d1", columns=["notes"], why="restates passage clauses as typed transcription checked by Carr.D1 transcription",
                               evidence="platform/scripts/governance/carriage_d1.py:398")
    assert ac.prose_coupling_problem(e) is not None
    assert PENDING in VOCAB_ASSETS and ASSETS[PENDING]["carriage"].get("nature") == "unverified_transcription" and ASSETS[PENDING]["carriage"].get("spec") is None      # why bg_transit_rules waits: no D1 matcher to couple to (N-156: it declares the ceiling, not a spec)


# ───────────────────────── Part 5: the code really builds no narration (syntax-tree proofs with mutants) ─────────────────────────

EXPECTED_INVENTORY = {         # (kind, source) of every text-building expression in the module: pinned, so a new one must be decided
    WR + "bg_transit_rules.py": [("fstr", "f\"bg_transit_engine={counts.get('bg_transit_engine', 0)}; bg_transit_rules={counts.get('bg_transit_rules', 0)}\"")],
    BG + "l0_transit.py": [
        ("binop", "engine_count + rules_count"), ("binop", "engine_count + rules_count + moorti_count"),
        ("binop", "len(BG_TRANSIT_ENGINE) + len(BG_TRANSIT_RULES)"), ("binop", "len(BG_TRANSIT_ENGINE) + len(BG_TRANSIT_RULES) + len(BG_TRANSIT_MOORTI)"),
        ("fstr", "f'{BPHS_CH28}; {PD_CH26}'")],
    BG + "l0_kp_sublord_division.py": [
        ("binop", "(lon - Fraction(1, 10 ** 9)) % NAK_SPAN_DEG"), ("binop", "(start_idx + i) % len(PLANET_CYCLE)"),
        ("binop", "Fraction(longitude_deg).limit_denominator(10 ** 12) % 360"), ("binop", "int(a / RASHI_SPAN_DEG) + 1"),
        ("binop", "int(pos / PADA_SPAN_DEG) + 1"), ("binop", "lon % NAK_SPAN_DEG"), ("binop", "longitude % 360"), ("binop", "nak0 % len(PLANET_CYCLE)"),
        ("binop", "nak0 + 1"), ("binop", "nak_start + cursor"), ("binop", "nak_start + cursor"), ("binop", "nak_start + cursor + span"), ("binop", "start_idx + i"),
        ("fstr", "f\"HALT: bg_kp_sublord_division holds no rows for table_version={table_version!r} — the L0 KP boundary authority must be built before any L1 KP projection\""),
        ("fstr", "f'KP sub-lord division not found for longitude {longitude_deg} — the division table does not tile [0, 360). This is a halt-worthy bug.'"),
        ("fstr", "f\"division {d['division_index']} (nakshatra {d['nakshatra_number']}): derived star_lord={d['star_lord']} but reference_nakshatra says {expected}\""),
        ("fstr", "f\"HALT: bg_kp_sublord_division requires a two_pass_verified star-lord cross-check against the L0 nakshatra authority (reference_nakshatra); received {verdict['status']}: {verdict['mismatches'][:5]}\""),
        ("fstr", "f'bg_kp_sublord_division exact postflight failed: expected ({len(rows)},1,{len(rows)},1,360.0), got {values}'")],
}


def _inventory(src):
    return sorted((k, s) for _ln, k, s in nw.composed_inventory(ast.parse(src)))


@pytest.mark.parametrize("rel", sorted(EXPECTED_INVENTORY))
def test_the_text_building_expressions_of_each_writer_module_are_exactly_the_pinned_ones(rel):
    expected = sorted(EXPECTED_INVENTORY[rel])
    got = _inventory(_src(rel))
    if rel.endswith("l0_kp_sublord_division.py"):                  # the f-string wording is pinned by kind and by the three stored-column facts below
        assert [k for k, _ in got] == [k for k, _ in expected]
    else:
        assert got == expected, rel


def test_the_only_f_string_of_the_transit_seeder_sits_inside_the_moorti_corpus_not_this_assets_tables():
    tree = ast.parse(_src(BG + "l0_transit.py"))
    fs = [n for n in ast.walk(tree) if isinstance(n, ast.JoinedStr)]
    assert len(fs) == 1
    moorti = next(s for s in tree.body if isinstance(s, ast.AnnAssign) and getattr(s.target, "id", "") == "BG_TRANSIT_MOORTI")
    assert fs[0] in set(ast.walk(moorti))


_OK_PARAM = (ast.Name, ast.Constant, ast.Tuple, ast.List, ast.Subscript, ast.Attribute, ast.Load, ast.Index if hasattr(ast, "Index") else ast.Load)


def insert_param_problems(src: str, func: str, table: str, allowed_names: set) -> list:
    """Inside `func`, every execute/executemany of an INSERT INTO `table` must bind parameters that only READ a corpus value: a bare name of `allowed_names` (a module-level
    corpus, or the loop variable over one), a tuple/dict-comprehension of plain reads. Anything that builds text (a `+`/`%`, an f-string, `.format`, `.join`, any call but
    `.get`) is returned as a problem. Also returns a problem when no such INSERT is found (a scan that saw nothing proves nothing)."""
    tree = ast.parse(src)
    module_sql = {t.id: s.value.value for s in tree.body if isinstance(s, ast.Assign) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)
                  for t in s.targets if isinstance(t, ast.Name)}
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func), None)
    if fn is None:
        return [f"function {func} not found"]
    seen, problems = 0, []
    for call in (c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in ("execute", "executemany")):
        sql = call.args[0] if call.args else None
        text = sql.value if isinstance(sql, ast.Constant) and isinstance(sql.value, str) else module_sql.get(getattr(sql, "id", ""), "")
        if not re.search(rf"INSERT\s+INTO\s+{table}\b", text or ""):
            continue
        seen += 1
        params = call.args[1] if len(call.args) > 1 else None
        if isinstance(params, ast.Name):
            if params.id not in allowed_names:
                problems.append(f"line {call.lineno}: parameter {params.id!r} is not a declared corpus name")
            continue
        nodes = [x for x in ast.walk(params)] if params is not None else []
        for x in nodes:
            if isinstance(x, (ast.JoinedStr, ast.BinOp)):
                problems.append(f"line {x.lineno}: text building ({type(x).__name__}) on a bound parameter")
            elif isinstance(x, ast.Call) and not (isinstance(x.func, ast.Attribute) and x.func.attr in ("get", "items", "startswith")):
                problems.append(f"line {x.lineno}: call on a bound parameter")
    if not seen:
        problems.append(f"{func} has no INSERT INTO {table}")
    return problems


INSERT_CASES = [      # (module, function, table, allowed bound names)
    (BG + "l0_transit.py", "seed_transit_rules", "bg_transit_engine", set()),
    (BG + "l0_kp_sublord_division.py", "seed_kp_sublord_division", "bg_kp_sublord_division", set()),
]


@pytest.mark.parametrize("rel, func, table, names", INSERT_CASES)
def test_every_insert_of_the_four_assets_binds_a_corpus_read_and_builds_no_text(rel, func, table, names):
    assert insert_param_problems(_src(rel), func, table, names) == []


class _Compose(ast.NodeTransformer):
    """Mutant: the parameters of every execute/executemany of an INSERT INTO `table` become a text-building expression over the original parameters."""
    def __init__(self, table):
        self.table, self.hit = table, 0

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("execute", "executemany") and len(node.args) > 1:
            sql = node.args[0]
            text = sql.value if isinstance(sql, ast.Constant) and isinstance(sql.value, str) else None
            if text is None and isinstance(sql, ast.Name):
                text = "INSERT INTO " + self.table if sql.id.endswith("INSERT_SQL") else None
            if text and re.search(rf"INSERT\s+INTO\s+{self.table}\b", text):
                node.args[1] = ast.BinOp(left=ast.Constant(value="x"), op=ast.Add(), right=node.args[1])
                self.hit += 1
        return node


@pytest.mark.parametrize("rel, func, table, names", INSERT_CASES)
def test_mutation_the_param_checker_kills_text_building_and_a_missing_insert(rel, func, table, names):
    src = _src(rel)
    assert insert_param_problems(src, "bg_no_such_function", table, names)
    assert insert_param_problems(src, func, "bg_no_such_table", names)
    tr = _Compose(table)
    mutated = ast.unparse(tr.visit(ast.parse(src)))
    assert tr.hit >= 1
    assert insert_param_problems(mutated, func, table, names), "a text-building expression on the bound parameters must be reported"


_SYN = ("ROWS = [('a', 1)]\n"
        "def seed(cur):\n"
        "    for row in ROWS:\n"
        "        cur.execute(\"INSERT INTO t (a, b) VALUES (%s, %s)\", PARAMS)\n")


def test_synthetic_param_checker_cases():
    ok = _SYN.replace("PARAMS", "row")
    assert insert_param_problems(ok, "seed", "t", {"row"}) == []
    assert insert_param_problems(ok.replace("PARAMS", "row"), "seed", "t", set())                    # a name outside the corpus set
    assert insert_param_problems(_SYN.replace("PARAMS", "(row[0], row[1])"), "seed", "t", set()) == []
    for bad in ("(row[0] + 'x', row[1])", "(f'{row[0]}', row[1])", "(row[0] % 1, row[1])", "(str(row[0]), row[1])", "(','.join(row), row[1])", "(row[0].upper(), row[1])"):
        assert insert_param_problems(_SYN.replace("PARAMS", bad), "seed", "t", set()), bad
    assert insert_param_problems(_SYN.replace("PARAMS", "{k: v for k, v in row.items() if not k.startswith('_')}"), "seed", "t", set()) == []
    assert insert_param_problems(_SYN.replace("PARAMS", "{k: v + 'x' for k, v in row.items()}"), "seed", "t", set())


def _module_level_name(src, name):
    tree = ast.parse(src)
    return [s for s in tree.body if isinstance(s, (ast.Assign, ast.AnnAssign))
            and any(isinstance(t, ast.Name) and t.id == name for t in (s.targets if isinstance(s, ast.Assign) else [s.target]))]


CORPORA = [(BG + "l0_transit.py", "BG_TRANSIT_ENGINE"), (BG + "l0_kp_sublord_division.py", "PLANET_CYCLE")]


@pytest.mark.parametrize("rel, name", CORPORA)
def test_each_seed_corpus_is_one_literal_defined_once_and_never_mutated_or_built_from_text(rel, name):
    assert nw.module_level_composition(_src(rel), name) == []


@pytest.mark.parametrize("rel, name", CORPORA)
def test_mutation_a_composed_value_in_a_corpus_literal_or_a_later_mutation_is_caught(rel, name):
    src = _src(rel)
    assert nw.module_level_composition(src + f"\n{name}.append(('x',))\n", name)
    assert nw.module_level_composition(src + f"\n{name} += []\n", name)
    s = _module_level_name(src, name)[0]
    first_str = next(n for n in ast.walk(s.value) if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) > 2)
    lines = src.splitlines()
    ln = first_str.lineno - 1
    old = lines[ln]
    quote = old[first_str.col_offset]
    assert quote in "\"'"
    seg_end = first_str.end_col_offset
    lines[ln] = old[:first_str.col_offset] + f"({old[first_str.col_offset:seg_end]} + {quote}x{quote})" + old[seg_end:]
    assert nw.module_level_composition("\n".join(lines), name), (rel, name)


def test_mutation_the_module_inventory_catches_an_injected_f_string_in_a_bound_column():
    src = _src(BG + "l0_transit.py")
    mutated = src.replace('"classical_citation": BPHS_CH22,', '"classical_citation": f"{BPHS_CH22} (Graha Gati)",', 1)
    assert mutated != src and len(_inventory(mutated)) == len(_inventory(src)) + 1
    mutated = src.replace('"classical_citation": BPHS_CH22,', '"classical_citation": BPHS_CH22 + " x",', 1)
    assert len(_inventory(mutated)) == len(_inventory(src)) + 1


# ───────────────────────── Part 6: the stored text columns of bg_kp_sublord_division are constants or index picks ─────────────────────────

def test_kp_stored_text_columns_are_a_constant_citation_a_constant_version_and_two_index_picks_from_the_literal_cycle():
    src = _src(BG + "l0_kp_sublord_division.py")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_divisions")
    ret = next(n for n in ast.walk(fn) if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "source_citation" for k in n.keys))
    vals = {k.value: v for k, v in zip(ret.keys, ret.values) if isinstance(k, ast.Constant)}
    assert isinstance(vals["source_citation"], ast.Name) and vals["source_citation"].id == "SOURCE_CITATION"
    assert isinstance(vals["table_version"], ast.Name) and vals["table_version"].id == "table_version"
    assert ast.unparse(vals["star_lord"]) == "r['star_lord']" and ast.unparse(vals["sub_lord"]) == "r['sub_lord']"
    cons = next(s for s in tree.body if isinstance(s, ast.Assign) and any(getattr(t, "id", "") == "SOURCE_CITATION" for t in s.targets))
    assert isinstance(cons.value, ast.Constant) and isinstance(cons.value.value, str)               # implicit concatenation folds to one string constant
    seg = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_sub_segments")
    sl = [n for n in ast.walk(seg) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("star_lord", "sub_lord") for t in n.targets)]
    assert sorted(ast.unparse(n.value) for n in sl) == ["PLANET_CYCLE[(start_idx + i) % len(PLANET_CYCLE)]", "PLANET_CYCLE[nak0 % len(PLANET_CYCLE)]"]
    assert not [n for n in ast.walk(seg) if isinstance(n, (ast.JoinedStr,))] and not [n for n in ast.walk(fn) if isinstance(n, ast.JoinedStr)]


def test_mutation_the_kp_proof_fails_when_a_stored_column_is_built_from_text():
    src = _src(BG + "l0_kp_sublord_division.py")
    mutated = src.replace('"source_citation": SOURCE_CITATION,', '"source_citation": SOURCE_CITATION + " " + table_version,', 1)
    assert mutated != src
    tree = ast.parse(mutated)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_divisions")
    ret = next(n for n in ast.walk(fn) if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "source_citation" for k in n.keys))
    vals = {k.value: v for k, v in zip(ret.keys, ret.values) if isinstance(k, ast.Constant)}
    assert not isinstance(vals["source_citation"], ast.Name)                                         # the structural assertion above would fail
    assert len(_inventory(mutated)) == len(_inventory(src)) + 2                                      # and the pinned inventory would grow by the two new `+`


# ───────────────────────── Part 7: case handling is DECLARED, not silent (strategist ruling) ─────────────────────────
# The S3 validator has a closed field set for `vocab_alias`; a `case_insensitive` / `mixed_case_rows` field would be an engine change (asset_census.py, REGISTRY revision), so the
# declaration states it in `why`. The detector compares with _norm_form (NFKC + casefold), i.e. case-insensitively, whatever the declaration says.

MIG397 = "platform/supabase/migrations/397_bg_transit_av_gates.sql"


def _mixed_case_rows():
    """[(line, graha, rule_type, primary_house)] of the migration-397 double_transit rows (title-case graha), read from the migration text."""
    out = []
    for n, line in enumerate(_src(MIG397).splitlines(), start=1):
        m = re.match(r"\s*\('double_transit',\s*'([A-Za-z]+)',\s*([0-9]+),", line)
        if m:
            out.append((n, m.group(1), "double_transit", int(m.group(2))))
    return out


def _canonical_spellings():
    f = _planet_forms()
    return {x["canonical_id"] for x in f} | {x["canonical_name_en"] for x in f}


def case_declaration_problems(why: str, aid: str, rows, spellings=None, values=None) -> list:
    """Why `why` does not declare the case handling of `aid`: it must say the comparison is case-insensitive; every seeded value must be an exact canonical spelling (else the
    declaration would rest on casefolding it does not state); and for the rows whose spelling differs from the table's other rows (`rows`: (line, graha, rule_type, house)) it
    must name each by natural key, cite the migration range that holds them, and name no key that is not one of them."""
    problems = []
    low = why.lower()
    if "compares case-insensitively" not in low:
        problems.append("the why does not say the detector compares case-insensitively")
    spell = _canonical_spellings() if spellings is None else spellings
    vals = SEED_VALUES[aid]() if values is None else values
    off = sorted({v for v in vals if v not in spell})
    if off:
        problems.append(f"values that are not an exact canonical id or display name (resolved only by casefolding): {off}")
    if rows:
        lo, hi = min(r[0] for r in rows), max(r[0] for r in rows)
        if f"{MIG397}:{lo}-{hi}" not in why:
            problems.append(f"the why does not cite {MIG397}:{lo}-{hi}")
        named = {(g, t, int(h)) for g, t, h in re.findall(r"\(([A-Za-z]+), (double_transit), ([0-9]+)\)", why)}
        want = {(r[1], r[2], r[3]) for r in rows}
        if named != want:
            problems.append(f"named natural keys differ from the mixed-case rows: missing {sorted(want - named)}, not mixed-case {sorted(named - want)}")
        if "Track I" not in why:
            problems.append("the why does not route case normalisation to Track I")
    elif "mixed" in low or "title-case" in low:
        problems.append("the why names mixed-case rows the table does not hold")
    return problems


def test_the_mixed_case_rows_of_bg_transit_rules_are_exactly_the_seven_migration_397_double_transit_rows():
    rows = _mixed_case_rows()
    assert [(g, h) for _, g, _, h in rows] == [("Jupiter", 2), ("Jupiter", 5), ("Jupiter", 7), ("Jupiter", 9), ("Jupiter", 11), ("Saturn", 4), ("Saturn", 8)]
    assert (rows[0][0], rows[-1][0]) == (57, 82)
    writer = SEED_VALUES["bg_transit_rules"]()[:-7]
    assert all(v == v.lower() for v in writer) and sorted(set(writer)) == sorted(GRAHAS9)           # the writer rows are all lowercase: the only title-case rows are the migration's


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_every_vocab_alias_declares_its_case_handling(aid):
    rows = _mixed_case_rows() if aid == "bg_transit_rules" else []
    assert case_declaration_problems(ASSETS[aid]["vocab_alias"]["why"], aid, rows) == []
    assert ac._s3_text_problem(ASSETS[aid]["vocab_alias"]["why"], min_chars=15, min_words=3) is None


def test_only_bg_transit_rules_mixes_spellings_and_the_other_four_rest_on_no_casefolding():
    spell = _canonical_spellings()
    for aid in VOCAB_ASSETS:
        assert all(v in spell for v in SEED_VALUES[aid]()), aid          # every seeded value is an exact canonical id or display name in all five tables
    for aid in VOCAB_ASSETS:
        vals = set(SEED_VALUES[aid]())
        assert (len({v.casefold() for v in vals}) != len(vals)) == (aid == "bg_transit_rules"), aid


def test_mutation_a_missing_or_wrong_case_declaration_is_reported():
    rows = _mixed_case_rows()
    why = ASSETS["bg_transit_rules"]["vocab_alias"]["why"]
    assert case_declaration_problems(why.replace("case-insensitively", "carefully"), "bg_transit_rules", rows)
    assert case_declaration_problems(why.replace("(Jupiter, double_transit, 5), ", ""), "bg_transit_rules", rows)            # a mixed-case row left unnamed
    assert case_declaration_problems(why.replace("(Saturn, double_transit, 8)", "(Saturn, double_transit, 8), (Mars, double_transit, 3)"), "bg_transit_rules", rows)   # a row that is not mixed-case
    assert case_declaration_problems(why.replace("397_bg_transit_av_gates.sql:57-82", "397_bg_transit_av_gates.sql:57-80"), "bg_transit_rules", rows)
    assert case_declaration_problems(why.replace("Track I", "later"), "bg_transit_rules", rows)
    assert case_declaration_problems(why, "bg_transit_rules", rows[:-1])                                                    # the migration gained or lost a row: the named set no longer matches
    assert case_declaration_problems(why, "bg_transit_rules", rows, values=SEED_VALUES["bg_transit_rules"]() + ["JUPITER"])  # a value resolved only by casefolding
    assert case_declaration_problems(ASSETS["bg_kp_sublord_division"]["vocab_alias"]["why"] + " (Jupiter, double_transit, 5) title-case", "bg_kp_sublord_division", [])
    assert case_declaration_problems(ASSETS["bg_kp_sublord_division"]["vocab_alias"]["why"].replace("case-insensitively", "carelessly"), "bg_kp_sublord_division", [])
    assert case_declaration_problems(ASSETS["bg_kp_sublord_division"]["vocab_alias"]["why"], "bg_kp_sublord_division", [], values=["Ketu", "VENUS"])


# ───────────────────────── Part 8: the strengthened "no stored text is built" guard for the two remaining Narr [] assets ─────────────────────────
# bg_transit_engine and bg_kp_sublord_division. Review (MEDIUM-1): a bare-name parameter check and an f-string / `+` / `%` / .format / .join inventory miss
# `[dict(r, col=r[col].replace(..)) for r in CORPUS]`, `.title()` on a column, `repr()` / `str(len())` / `json.dumps` stored in a column, and an extra
# `UPDATE <table> SET col = col || %s`. This guard closes them by SHAPE: (1) the seed loop iterates a BARE corpus Name, (2) the INSERT parameters are pinned
# expression by expression (a subscript read of the loop variable, nothing else), (3) the Calls of the seed/build functions are a pinned whitelist (no str / repr /
# json.dumps / replace / title / upper / lower ...), (4) EVERY executed SQL text in the writer scope must be a string constant (no dynamic SQL), and the statements that
# name the table are exactly one strict-shape INSERT (placeholders only in VALUES, `col = EXCLUDED.col` only in SET) plus reads/deletes: `||`, `format(`, `concat`,
# `replace(` and any other UPDATE are refused, (5) the corpus is never mutated at run time. It lives in this test file: no engine change.
# Narr scope: each [] covers the asset's OWN table only.

_TEXT_FN = re.compile(r"\|\||\bformat\s*\(|\bconcat\s*\(|\breplace\s*\(|\binitcap\s*\(|\bupper\s*\(|\blower\s*\(|\bregexp_|\bsubstr|\bleft\s*\(|\bright\s*\(|\btranslate\s*\(", re.I)


def _norm_sql(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip()


def _sql_statements(tree):
    """[(lineno, text or None)] of every execute/executemany of the module: text is the constant SQL (a str Constant, or a module-level str-constant Name); None = dynamic."""
    consts = {t.id: s.value.value for s in tree.body if isinstance(s, ast.Assign) and isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)
              for t in s.targets if isinstance(t, ast.Name)}
    out = []
    for c in ast.walk(tree):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr in ("execute", "executemany") and c.args:
            a = c.args[0]
            text = a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else consts.get(a.id) if isinstance(a, ast.Name) else None
            out.append((c.lineno, text))
    return out


def _insert_shape_problem(text: str, table: str, params: str):
    """None when `text` is a strict seed INSERT of `table`: columns list, VALUES of placeholders only (`params`: 'pct_s' for %s, 'named' for %(x)s), ON CONFLICT (...) DO UPDATE
    SET with only `col = EXCLUDED.col`."""
    n = _norm_sql(text)
    m = re.fullmatch(rf"INSERT INTO {table} \(([\w, ]+)\) VALUES \(((?:%s|%\(\w+\)s|[ ,])*)\) ON CONFLICT \(([\w, ]+)\) DO UPDATE SET (.+)", n)
    if not m:
        return "not a strict INSERT ... VALUES (placeholders) ON CONFLICT (...) DO UPDATE SET col = EXCLUDED.col"
    cols = [c.strip() for c in m.group(1).split(",")]
    vals = [v.strip() for v in m.group(2).split(",")]
    ph = r"%s" if params == "pct_s" else r"%\(\w+\)s"
    if len(vals) != len(cols) or not all(re.fullmatch(ph, v) for v in vals):
        return "VALUES holds something other than one placeholder per column"
    sets = [x.strip() for x in m.group(4).split(",")]
    if not all((mm := re.fullmatch(r"(\w+) = EXCLUDED\.(\w+)", x)) and mm.group(1) == mm.group(2) for x in sets):
        return "SET holds something other than col = EXCLUDED.col"
    return None


def _statement_problems(tree, table: str, insert_params: str, expect_inserts: int = 1) -> list:
    problems, inserts = [], 0
    for ln, text in _sql_statements(tree):
        if text is None:
            problems.append(f"line {ln}: dynamic SQL (the executed text is not a string constant)")
            continue
        if not re.search(rf"\b{table}\b", text, re.I):
            continue
        n = _norm_sql(text)
        if _TEXT_FN.search(n):
            problems.append(f"line {ln}: SQL naming {table} holds a text operator or function (|| / format / concat / replace / upper / lower ...)")
        verb = n.split(" ", 1)[0].upper()
        if verb == "INSERT":
            inserts += 1
            bad = _insert_shape_problem(text, table, insert_params)
            if bad:
                problems.append(f"line {ln}: {bad}")
        elif verb == "DELETE":
            if not re.fullmatch(rf"DELETE FROM {table} WHERE [^;]*", n):
                problems.append(f"line {ln}: DELETE of an unexpected shape")
        elif verb == "SELECT" or n.upper().startswith("WITH"):
            pass
        else:
            problems.append(f"line {ln}: a {verb} statement on {table} (only the seed INSERT, DELETE and reads are allowed)")
    if inserts != expect_inserts:
        problems.append(f"{inserts} INSERT statements on {table} ({expect_inserts} allowed)")
    return problems


def _func(tree, name):
    return next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name), None)


def _call_names(fn) -> set:
    return {c.func.id if isinstance(c.func, ast.Name) else ast.unparse(c.func) for c in ast.walk(fn) if isinstance(c, ast.Call)}


def _corpus_problems(tree, name: str, allowed_name_values: set) -> list:
    """The module-level corpus literal `name`: no Call / BinOp / f-string anywhere in it, values are str/number constants or the named str-constant names; and it is only ever
    READ in the module (a for-loop iterable or the argument of len), never rebound, indexed, mutated or passed on."""
    problems = []
    defs = [s for s in tree.body if isinstance(s, (ast.Assign, ast.AnnAssign)) and any(getattr(t, "id", None) == name for t in (s.targets if isinstance(s, ast.Assign) else [s.target]))]
    if len(defs) != 1:
        return [f"{name} is not defined exactly once at module level"]
    for n in ast.walk(defs[0].value):
        if isinstance(n, (ast.Call, ast.BinOp, ast.JoinedStr)):
            problems.append(f"line {n.lineno}: {name} literal holds a {type(n).__name__}")
        elif isinstance(n, ast.Name) and n.id not in allowed_name_values and n.id not in ("None", "True", "False"):
            problems.append(f"line {n.lineno}: {name} literal reads the name {n.id!r}")
    parents = {id(c): p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id == name and n is not (defs[0].target if isinstance(defs[0], ast.AnnAssign) else None):
            p = parents.get(id(n))
            if isinstance(n.ctx, ast.Store):
                if p is not defs[0]:
                    problems.append(f"line {n.lineno}: {name} is rebound")
            elif isinstance(p, ast.For) and p.iter is n:
                pass
            elif isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id == "len":
                pass
            else:
                problems.append(f"line {n.lineno}: {name} is used other than as a bare loop iterable or len() argument")
    return problems


def _const_str_name_problem(tree, name: str):
    s = [s for s in tree.body if isinstance(s, ast.Assign) and any(getattr(t, "id", None) == name for t in s.targets)]
    if len(s) != 1 or not (isinstance(s[0].value, ast.Constant) and isinstance(s[0].value.value, str)):
        return f"{name} is not one plain string constant defined once at module level"
    return None


ENGINE_PARAMS = ["row['graha']", "row['avg_daily_motion_deg']", "row['zodiac_period_days']", "row['sign_residence_days']", "row['classical_citation']"]


def engine_guard_problems(l0_src: str, writer_src: str) -> list:
    """bg_transit_engine: the engine half of the shared transit seeder builds no stored text."""
    l0, wr = ast.parse(l0_src), ast.parse(writer_src)
    problems = _statement_problems(l0, "bg_transit_engine", "pct_s") + _statement_problems(wr, "bg_transit_engine", "pct_s", 0)
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("execute", "executemany") for n in ast.walk(wr)):
        problems.append("the writer module executes SQL itself (it must only call the seeder)")
    fn = _func(l0, "seed_transit_rules")
    if fn is None:
        return problems + ["seed_transit_rules not found"]
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For) and ast.unparse(n.iter) != "BG_TRANSIT_RULES" and any(
        isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "execute" and c.args and isinstance(c.args[0], ast.Constant)
        and "INSERT INTO bg_transit_engine" in _norm_sql(str(c.args[0].value)) for c in ast.walk(n))]
    if len(loops) != 1:
        return problems + [f"{len(loops)} loops insert into bg_transit_engine (exactly one expected)"]
    loop = loops[0]
    if not (isinstance(loop.iter, ast.Name) and loop.iter.id == "BG_TRANSIT_ENGINE"):
        problems.append(f"the seed loop iterates {ast.unparse(loop.iter)!r}, not the bare corpus name BG_TRANSIT_ENGINE")
    if not (isinstance(loop.target, ast.Name) and loop.target.id == "row"):
        problems.append("the loop variable is not the bare name `row`")
    if [type(b).__name__ for b in loop.body] != ["Expr", "AugAssign"]:
        problems.append("the loop body is not exactly one execute and one counter increment")
    calls = [c for b in loop.body for c in ast.walk(b) if isinstance(c, ast.Call)]
    if [ast.unparse(c.func) for c in calls] != ["cur.execute"]:
        problems.append(f"calls inside the seed loop other than cur.execute: {sorted(ast.unparse(c.func) for c in calls)}")
    ex = next((c for c in calls if ast.unparse(c.func) == "cur.execute"), None)
    if ex is not None:
        got = [ast.unparse(e) for e in ex.args[1].elts] if len(ex.args) > 1 and isinstance(ex.args[1], ast.Tuple) else None
        if got != ENGINE_PARAMS:
            problems.append(f"INSERT parameters are {got}, expected the plain subscript reads {ENGINE_PARAMS}")
    problems += _corpus_problems(l0, "BG_TRANSIT_ENGINE", {"BPHS_CH22"})
    bad = _const_str_name_problem(l0, "BPHS_CH22")
    if bad:
        problems.append(bad)
    return problems


KP_SEED_CALLS = {"RuntimeError", "abs", "build_divisions", "conn.commit", "conn.cursor", "cur.execute", "cur.fetchone", "float", "isinstance", "k.startswith", "len", "logger.info",
                 "r.items", "verify_star_lords_against_reference"}
KP_SEGMENT_CALLS = {"Fraction", "PLANET_CYCLE.index", "_sub_span_deg", "len", "range", "segments.append"}
KP_DIVISION_CALLS = {"_pada_at", "bool", "build_sub_segments", "enumerate", "float", "int", "out.append", "range", "rows.append", "rows.sort", "zip"}
KP_ROW_DICT = {"table_version": "table_version", "division_index": "idx", "start_longitude_deg": "float(r['start_deg'])", "end_longitude_deg": "float(r['end_deg'])",
               "span_arcmin": "float(span_arcmin)", "nakshatra_number": "r['nakshatra_number']", "star_lord": "r['star_lord']", "sub_lord": "r['sub_lord']",
               "sign_number": "r['sign_number']", "pada_at_start": "r['pada_at_start']", "pada_at_end": "r['pada_at_end']", "split_by_sign_boundary": "r['split_by_sign_boundary']",
               "source_citation": "SOURCE_CITATION", "_start_exact": "r['start_deg']", "_end_exact": "r['end_deg']"}
KP_SEG_DICT = {"start": "nak_start + cursor", "end": "nak_start + cursor + span", "nakshatra_number": "nak0 + 1", "star_lord": "star_lord", "sub_lord": "sub_lord"}
KP_PARAMS = "{k: v for k, v in r.items() if not k.startswith('_')}"


def _dict_with_key(fn, key):
    for d in ast.walk(fn):
        if isinstance(d, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == key for k in d.keys):
            return {k.value: ast.unparse(v) for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant)}
    return None


def kp_guard_problems(l0_src: str, writer_src: str) -> list:
    """bg_kp_sublord_division: the divisions are built and stored without any text being built."""
    l0, wr = ast.parse(l0_src), ast.parse(writer_src)
    problems = _statement_problems(l0, "bg_kp_sublord_division", "named") + _statement_problems(wr, "bg_kp_sublord_division", "named", 0)
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("execute", "executemany") for n in ast.walk(wr)):
        problems.append("the writer module executes SQL itself (it must only call the seeder)")
    for fname, allowed in (("build_sub_segments", KP_SEGMENT_CALLS), ("build_divisions", KP_DIVISION_CALLS), ("seed_kp_sublord_division", KP_SEED_CALLS)):
        fn = _func(l0, fname)
        if fn is None:
            problems.append(f"{fname} not found")
            continue
        extra = _call_names(fn) - allowed
        if extra:
            problems.append(f"{fname} calls outside the pinned whitelist: {sorted(extra)}")
    seg, div, seed = _func(l0, "build_sub_segments"), _func(l0, "build_divisions"), _func(l0, "seed_kp_sublord_division")
    if seg is not None and _dict_with_key(seg, "star_lord") != KP_SEG_DICT:
        problems.append(f"the segment dict is not the pinned expression set: {_dict_with_key(seg, 'star_lord')}")
    if div is not None and _dict_with_key(div, "source_citation") != KP_ROW_DICT:
        problems.append(f"the stored row dict is not the pinned expression set: {_dict_with_key(div, 'source_citation')}")
    if seg is not None:
        picks = sorted(ast.unparse(n.value) for n in ast.walk(seg) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") in ("star_lord", "sub_lord") for t in n.targets))
        if picks != ["PLANET_CYCLE[(start_idx + i) % len(PLANET_CYCLE)]", "PLANET_CYCLE[nak0 % len(PLANET_CYCLE)]"]:
            problems.append(f"star_lord / sub_lord are not the two pinned index picks: {picks}")
    if seed is not None:
        assigns = [n for n in ast.walk(seed) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "rows" for t in n.targets)]
        if [ast.unparse(a.value) for a in assigns] != ["build_divisions()"]:
            problems.append("`rows` is not assigned exactly once, from build_divisions()")
        loops = [n for n in ast.walk(seed) if isinstance(n, ast.For) and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "execute"
                                                                              and c.args and ast.unparse(c.args[0]) == "_INSERT_SQL" for c in ast.walk(n))]
        if len(loops) != 1:
            problems.append(f"{len(loops)} loops execute _INSERT_SQL (exactly one expected)")
        else:
            lp = loops[0]
            if not (isinstance(lp.iter, ast.Name) and lp.iter.id == "rows"):
                problems.append(f"the seed loop iterates {ast.unparse(lp.iter)!r}, not the bare name `rows`")
            if [type(b).__name__ for b in lp.body] != ["Expr"]:
                problems.append("the loop body is not exactly one execute")
            else:
                call = lp.body[0].value
                if ast.unparse(call.func) != "cur.execute" or len(call.args) != 2 or ast.unparse(call.args[1]) != KP_PARAMS:
                    problems.append(f"the INSERT parameters are not {KP_PARAMS}")
    for name in ("SOURCE_CITATION", "TABLE_VERSION"):
        bad = _const_str_name_problem(l0, name)
        if bad:
            problems.append(bad)
    pc = [s for s in l0.body if isinstance(s, ast.AnnAssign) and getattr(s.target, "id", "") == "PLANET_CYCLE"]
    if len(pc) != 1 or not (isinstance(pc[0].value, ast.List) and all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in pc[0].value.elts)):
        problems.append("PLANET_CYCLE is not one literal list of string constants")
    problems += [p for p in _corpus_problems(l0, "PLANET_CYCLE", set()) if "bare loop iterable" not in p and "other than" not in p]
    return problems


L0T, WRT = _src(BG + "l0_transit.py"), _src(WR + "bg_transit_rules.py")
L0K, WRK = _src(BG + "l0_kp_sublord_division.py"), _src(WR + "bg_kp_sublord_division.py")


def test_the_two_remaining_narr_empty_assets_pass_the_strengthened_guard():
    assert engine_guard_problems(L0T, WRT) == []
    assert kp_guard_problems(L0K, WRK) == []


def _mut(src: str, old: str, new: str) -> str:
    assert src.count(old) >= 1, old
    return src.replace(old, new, 1)


ENGINE_LOOP = "    for row in BG_TRANSIT_ENGINE:\n"
ENGINE_MUTANTS = {
    "comprehension that rewrites a column (reviewer mutant 1)": lambda s: _mut(s, ENGINE_LOOP, '    for row in [dict(r, classical_citation=r["classical_citation"].replace("Ch.22", "Ch.23")) for r in BG_TRANSIT_ENGINE]:\n'),
    "comprehension that only renames a corpus (bare-name rule)": lambda s: _mut(s, ENGINE_LOOP, "    for row in [r for r in BG_TRANSIT_ENGINE]:\n"),
    ".title() on a column (reviewer mutant 2)": lambda s: _mut(s, '                row["classical_citation"],\n            ),\n        )\n        engine_count', '                row["classical_citation"].title(),\n            ),\n        )\n        engine_count'),
    "str(len()) stored in a column (reviewer mutant 3)": lambda s: _mut(s, '                row["graha"],\n                row["avg_daily', '                str(len(row["graha"])),\n                row["avg_daily'),
    "repr() stored in a column": lambda s: _mut(s, '                row["graha"],\n                row["avg_daily', '                repr(row["graha"]),\n                row["avg_daily'),
    "json.dumps stored in a column": lambda s: _mut(s, '                row["graha"],\n                row["avg_daily', '                json.dumps(row["graha"]),\n                row["avg_daily'),
    "an extra UPDATE with || in the shared writer (reviewer mutant 4)": lambda s: _mut(s, "    # ── Insert bg_transit_rules rows ─", '    cur.execute("UPDATE bg_transit_engine SET classical_citation = classical_citation || %s", ("x",))\n    # ── Insert bg_transit_rules rows ─'),
    "an extra UPDATE built as dynamic SQL": lambda s: _mut(s, "    # ── Insert bg_transit_rules rows ─", '    cur.execute("UPDATE bg_transit_" + "engine SET graha = graha", ())\n    # ── Insert bg_transit_rules rows ─'),
    "a text function in the INSERT VALUES": lambda s: _mut(s, "VALUES (%s, %s, %s, %s, %s)\n            ON CONFLICT (graha) DO UPDATE SET\n                avg_daily", "VALUES (%s, %s, %s, %s, upper(%s))\n            ON CONFLICT (graha) DO UPDATE SET\n                avg_daily"),
    "a text operator in the upsert SET": lambda s: _mut(s, "classical_citation   = EXCLUDED.classical_citation\n            \"\"\",\n            (\n                row[\"graha\"],\n                row[\"avg_daily", "classical_citation   = EXCLUDED.classical_citation || 'x'\n            \"\"\",\n            (\n                row[\"graha\"],\n                row[\"avg_daily"),
    "a call in the corpus literal": lambda s: _mut(s, '"graha": "sun",\n        "avg_daily_motion_deg": 0.9856', '"graha": "SUN".lower(),\n        "avg_daily_motion_deg": 0.9856'),
    "a run-time mutation of the corpus": lambda s: _mut(s, "    cur = conn.cursor()\n", '    cur = conn.cursor()\n    BG_TRANSIT_ENGINE[0]["classical_citation"] = "x"\n'),
    "a second pass over the corpus": lambda s: _mut(s, "    # ── Insert bg_transit_rules rows ─", '    for row in BG_TRANSIT_ENGINE:\n        cur.execute("INSERT INTO bg_transit_engine (graha) VALUES (%s)", (row["graha"],))\n    # ── Insert bg_transit_rules rows ─'),
}


@pytest.mark.parametrize("name", sorted(ENGINE_MUTANTS))
def test_mutation_the_engine_guard_kills_each_surviving_mutant(name):
    mutated = ENGINE_MUTANTS[name](L0T)
    assert mutated != L0T
    assert engine_guard_problems(mutated, WRT), name


def test_mutation_the_engine_guard_kills_a_writer_module_that_executes_sql():
    assert engine_guard_problems(L0T, WRT + "\n\ndef x(cur):\n    cur.execute('UPDATE bg_transit_engine SET graha = graha')\n")


KP_LOOP = "        for r in rows:\n"
KP_MUTANTS = {
    "comprehension that rewrites a column (reviewer mutant 1)": (L0K, lambda s: _mut(s, KP_LOOP, '        for r in [dict(r, star_lord=r["star_lord"].title()) for r in rows]:\n')),
    "comprehension that only renames the corpus": (L0K, lambda s: _mut(s, KP_LOOP, "        for r in [x for x in rows]:\n")),
    ".title() on a stored column in build_divisions (reviewer mutant 2)": (L0K, lambda s: _mut(s, '"star_lord": r["star_lord"],\n            "sub_lord"', '"star_lord": r["star_lord"].title(),\n            "sub_lord"')),
    ".title() in the INSERT parameter comprehension": (L0K, lambda s: _mut(s, "{k: v for k, v in r.items() if not k.startswith(\"_\")}", "{k: v.title() if isinstance(v, str) else v for k, v in r.items() if not k.startswith(\"_\")}")),
    "str(len()) stored in a column (reviewer mutant 3)": (L0K, lambda s: _mut(s, '"source_citation": SOURCE_CITATION,', '"source_citation": str(len(SOURCE_CITATION)),')),
    "repr() stored in a column": (L0K, lambda s: _mut(s, '"source_citation": SOURCE_CITATION,', '"source_citation": repr(SOURCE_CITATION),')),
    "json.dumps stored in a column": (L0K, lambda s: _mut(s, '"source_citation": SOURCE_CITATION,', '"source_citation": json.dumps(SOURCE_CITATION),')),
    "concatenation in a stored column": (L0K, lambda s: _mut(s, '"source_citation": SOURCE_CITATION,', '"source_citation": SOURCE_CITATION + " x",')),
    ".upper() on the star lord pick": (L0K, lambda s: _mut(s, "star_lord = PLANET_CYCLE[nak0 % len(PLANET_CYCLE)]", "star_lord = PLANET_CYCLE[nak0 % len(PLANET_CYCLE)].upper()")),
    "an extra UPDATE with || (reviewer mutant 4)": (L0K, lambda s: _mut(s, "        postflight = cur.fetchone()", '        cur.execute("UPDATE bg_kp_sublord_division SET source_citation = source_citation || %s", ("x",))\n        postflight = cur.fetchone()')),
    "an extra UPDATE built as dynamic SQL": (L0K, lambda s: _mut(s, "        postflight = cur.fetchone()", '        cur.execute("UPDATE bg_kp_" + "sublord_division SET star_lord = star_lord")\n        postflight = cur.fetchone()')),
    "a text operator in the upsert SET": (L0K, lambda s: _mut(s, "    source_citation        = EXCLUDED.source_citation\n", "    source_citation        = EXCLUDED.source_citation || 'x'\n")),
    "a text function in the INSERT VALUES": (L0K, lambda s: _mut(s, "%(split_by_sign_boundary)s, %(source_citation)s\n)", "%(split_by_sign_boundary)s, upper(%(source_citation)s)\n)")),
    "source citation built instead of constant": (L0K, lambda s: _mut(s, 'SOURCE_CITATION = (\n    "[TIER-III]', 'SOURCE_CITATION = TABLE_VERSION + (\n    "[TIER-III]')),
    "a second pass over the rows": (L0K, lambda s: _mut(s, "        postflight = cur.fetchone()", '        for r in rows:\n            cur.execute(_INSERT_SQL, {k: v for k, v in r.items() if not k.startswith("_")})\n        postflight = cur.fetchone()')),
}


@pytest.mark.parametrize("name", sorted(KP_MUTANTS))
def test_mutation_the_kp_guard_kills_each_surviving_mutant(name):
    src, mut = KP_MUTANTS[name]
    mutated = mut(src)
    assert mutated != src
    assert kp_guard_problems(mutated, WRK), name


def test_mutation_the_kp_guard_kills_a_writer_module_that_executes_sql():
    assert kp_guard_problems(L0K, WRK + "\n\ndef x(cur):\n    cur.execute('UPDATE bg_kp_sublord_division SET sub_lord = sub_lord')\n")


# ───────────────────────── Part 9: scope, wording and tripwire facts the declarations state ─────────────────────────

def test_the_reverse_leg_uses_the_global_declared_prose_vocabulary_so_another_lane_declaring_a_matching_column_flips_these_assets_from_na_to_fail():
    """TRIPWIRE (intended): `prose_reverse_leg` compares the writer's INSERT columns with the prose vocabulary declared by ANY asset (40 names today), not with a per-asset list.
    If another lane declares a column that these writers also write (here the hypothetical `classical_citation`), Narr.agree for bg_transit_engine / bg_kp_sublord_division reads
    FAIL, not N/A, until the overlap is decided. The names declared today do not overlap what they write (test_the_writer_scope_is_readable...)."""
    vocab = ac.prose_vocabulary(ASSETS)
    assert len(vocab) == 41      # E5.7 L1/L2 fill: bo_cgm_paths adds path_label_human; the L2 fill adds embedding_input_summary (bo_samskara), derivation_chain / grounding_evidence_jsonb (bo_grounding) and the nine bo_chart_gestalt jsonb columns, notes (bo_pramana_mapa); bg_vedha_malefic_scale adds effect_description (SS 2026-10-05)
    for aid, col in (("bg_transit_engine", "classical_citation"), ("bg_kp_sublord_division", "source_citation")):
        out = ac.prose_checks(aid, ASSETS[aid], _ctx(aid, vocabulary=vocab | {col}))
        assert out["Narr.agree"]["v"] == FAIL and col in out["Narr.agree"]["measured"], aid
        assert all(out[c]["v"] == NO_DET for c in ("Narr.checkable", "Narr.fidelity_test", "Narr.lint"))


def test_the_transit_rules_case_split_is_stated_with_its_counts_consumers_and_ownership_note():
    why = ASSETS["bg_transit_rules"]["vocab_alias"]["why"]
    tree = ast.parse(L0T)
    node = next(s for s in tree.body if isinstance(s, ast.AnnAssign) and getattr(s.target, "id", "") == "BG_TRANSIT_RULES")
    from collections import Counter
    c = Counter(v.value for d in ast.walk(node) if isinstance(d, ast.Dict) for k, v in zip(d.keys, d.values) if isinstance(k, ast.Constant) and k.value == "graha")
    assert sum(c.values()) == 69 and c["jupiter"] == 7 and c["saturn"] == 6
    mig = Counter(r[1] for r in _mixed_case_rows())
    assert mig == {"Jupiter": 5, "Saturn": 2}
    for needle in ("69 writer rows", "jupiter x7", "saturn x6", "Jupiter x5", "Saturn x2", "canonical lowercase", "case-insensitively",
                   "register_p1_reference.ts:637", "l0_transit.py:990-997", "Track I", "graha of this table only", "on purpose"):
        assert needle in why, needle
    assert "canonical lowercase graha name" in _line("platform/migrations/266_bg_transit_tables.sql:41")
    assert "LOWER(graha) = LOWER(" in _line("platform-mcp/src/tools/register_p1_reference.ts:637")
    lines = _src(BG + "l0_transit.py").splitlines()
    assert "case-sensitive" in " ".join(lines[989:997]) and lines[989].lstrip().startswith("# that")
    ident = ASSETS["bg_transit_rules"]["vocab_alias"]["identity_only_why"]
    assert "two spellings" in ident and "one canonical name per row" not in ident
    assert "exact" in why and "canonical id" in why and "canonical display name" in why     # both spellings are exact canonical spellings: no casefold is needed to resolve either


SCOPE_PHRASES = {
    "bg_dignity_reference": "graha of bg_dignity_reference only; graha and other_graha of the four sibling tables",
    "bg_transit_engine": "graha of bg_transit_engine only",
    "bg_transit_rules": "graha of this table only",
    "bg_vastu_directions": "ruling_graha of bg_vastu_directions only; secondary_graha and the remedials table are not measured",
    "bg_kp_sublord_division": "star_lord of bg_kp_sublord_division only; sub_lord is not measured",
}


@pytest.mark.parametrize("aid", sorted(VOCAB_ASSETS))
def test_each_vocab_why_discloses_which_column_and_table_it_measures(aid):
    assert SCOPE_PHRASES[aid] in ASSETS[aid]["vocab_alias"]["why"]


def test_the_narr_evidence_states_its_scope_and_what_is_not_claimed():
    ev = ASSETS["bg_transit_engine"]["evidence"]["prose_fields"]
    assert "bg_transit_engine's own table only" in ev and "bg_transit_moorti" in ev and "conditional expression" in ev and "f-string" in ev and "held bg_transit_rules" in ev
    ek = ASSETS["bg_kp_sublord_division"]["evidence"]["prose_fields"]
    assert "bg_kp_sublord_division's own table only" in ek
    for aid in EMPTY_ASSETS:
        assert "hand-typed statements of classical positions" not in ASSETS[aid]["evidence"]["prose_fields"], aid
    assert "hand-typed statements of classical positions" not in json.dumps(ASSETS)
