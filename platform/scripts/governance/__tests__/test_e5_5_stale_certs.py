"""test_e5_5_stale_certs.py — Suvarna E5.5: the stale-certification detector (`nikasha_stale_certs.py`).

The certification currency contract (Track E brief 7, arch 12.16), each clause with its own tests:
  (1) the SEMANTIC ROW FINGERPRINT: rows in natural-key order, canonical JSON of the declared semantic columns,
      volatile columns excluded as declared per asset, embeddings NOT hashed (their source columns + model id are);
      an idempotent rebuild leaves it unchanged; any unreadable input raises (never "not stale");
  (2) certificate generation ids: an upstream whose latest generation is not the one cited, that is itself stale,
      invalidated or not passing, makes the dependent stale — transitively, and ONLY what changed;
  (3) the invalidation WATERMARK: invalidation lines appended to the ledger in a shape E5.1's reader accepts,
      and `watermark_ok` / `current_certificates` refusing a ledger that holds certificates E5.5 has not evaluated;
  (4) bounded RE-WALKS: at most two invalidating walks per layer over the whole ledger; the third raises with the
      findings for Strategic Suvarna and writes nothing.

Offline: tmp ledgers, a fake DB-API cursor, a tmp git repo. No database, no network.
"""
from __future__ import annotations

import copy
import datetime as dt
import decimal
import hashlib
import json
import pathlib
import subprocess
import sys
import types
import itertools
import uuid

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402
import nikasha_stale_certs as sc  # noqa: E402

RUN = "2026-10-01T10:00:00+05:30"
NOW = "2026-10-02T09:00:00+05:30"
COMMIT = "c0ffee0" + "0" * 33


def H(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def shab(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ───────────────────────── harness ─────────────────────────
# Gate certificates are built through E5.1's real write path: the verdict comes from a stamped census FILE committed
# (staged) under the trusted census root of a tmp git repo, writer hashes are computed from writer files committed in
# that repo before the census run (the pattern of test_e5_1_certify.py).

COMMIT_DATE = "2026-09-30T10:00:00+05:30"                  # before RUN: the census postdates every writer commit
TOOL_COMMIT = "a" * 40
CENSUS_DIR_REL = "00_ARCHITECTURE/control/census"
WRITERS_REL = "platform/python-sidecar/pipeline/orchestrator/writers"
DECL_REL = "platform/scripts/governance/asset_declarations.json"
DECL_BYTES = b'{"version": "1.7.0", "assets": {}}\n'
DECL_SHA = hashlib.sha256(DECL_BYTES).hexdigest()
ENV = types.SimpleNamespace(ctrl=None, repo=None, cdir=None)
_N = itertools.count()


def git(repo, *args, date=None):
    e = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
         "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "HOME": str(repo)}
    if date:
        e.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    return subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args], check=True,
                          capture_output=True, env=e).stdout.decode()


@pytest.fixture(scope="session")
def session_repo(tmp_path_factory):
    repo = tmp_path_factory.mktemp("repo")
    git(repo, "init", "-q")
    (repo / CENSUS_DIR_REL).mkdir(parents=True)
    (repo / CENSUS_DIR_REL / ".gitkeep").write_text("")
    (repo / WRITERS_REL).mkdir(parents=True)
    (repo / WRITERS_REL / ".gitkeep").write_text("")
    (repo / DECL_REL).parent.mkdir(parents=True, exist_ok=True)         # E5.1 binds a gate to the committed declarations file
    (repo / DECL_REL).write_bytes(DECL_BYTES)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base", date=COMMIT_DATE)
    return repo


@pytest.fixture(autouse=True)
def env(tmp_path, monkeypatch, session_repo):
    """A tmp control dir, the tmp git repo as asset_census's ROOT (its census dir is the trusted root), no ambient
    overrides."""
    ctrl = tmp_path / "control"
    ctrl.mkdir()
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "ROOT", session_repo)
    monkeypatch.setattr(ac, "SIDECAR", session_repo / "platform" / "python-sidecar")
    monkeypatch.setattr(ac, "WRITERS", session_repo / WRITERS_REL)
    monkeypatch.delenv("NIKASHA_CERTS_LEDGER", raising=False)
    ENV.ctrl, ENV.repo, ENV.cdir = ctrl, session_repo, session_repo / CENSUS_DIR_REL
    return ENV


@pytest.fixture
def ledger(tmp_path):
    p = tmp_path / "asset_certs.jsonl"
    p.write_text(json.dumps({"asset": "_schema", "_doc": "test ledger"}) + "\n", encoding="utf-8")
    return p


def layer_of(asset):
    return {"bg": "L0", "ga": "L1", "bo": "L2", "ka": "L3"}[asset[:2]]


def fp_of(asset, n=0):
    return H(f"fp:{asset}:{n}")


def wnames(asset, files=1):
    """The writer file names of `asset`: the asset itself, then `<asset>_2`, `<asset>_3`, ..."""
    return [asset] + [f"{asset}_{i}" for i in range(2, files + 1)]


def wpath(name):
    return f"{WRITERS_REL}/{name}.py"


def wbytes(name, n=0):
    return f"# writer {name} v{n}\n".encode()


def wh_of(asset, n=0, files=1):
    """The writer hashes of `asset`'s files at version n (put_writer(asset, n, files) commits exactly these bytes)."""
    return {wpath(nm): shab(wbytes(nm, n)) for nm in wnames(asset, files)}


def put_writer(asset, n=0, files=1):
    """Commit the writer files of `asset` at version n (before RUN) unless they already are that version."""
    out = []
    for nm in wnames(asset, files):
        f = ENV.repo / wpath(nm)
        if not (f.exists() and f.read_bytes() == wbytes(nm, n)):
            f.write_bytes(wbytes(nm, n))
            git(ENV.repo, "add", "--", wpath(nm))
            git(ENV.repo, "commit", "-q", "-m", f"{nm} v{n}", date=COMMIT_DATE)
        out.append(wpath(nm))
    return out


def census_file(asset, crit, verdict, *, generated=RUN, cell=True, rec=None, head=None, files=1, cell_extra=None):
    """A stamped census JSON file under the trusted census root, `git add`ed (state: staged)."""
    record = dict(asset_id=asset, layer=layer_of(asset), has_writer=True,
                  writer_files=[f"{nm}.py" for nm in wnames(asset, files)],
                  asset_kind="data", target_columns=None,
                  measurements={crit: dict(v=verdict, measured="m", **(cell_extra or {}))} if cell else {})
    record.update(rec or {})
    c = dict(generated=generated, layer=layer_of(asset), registry_revision=ac.REGISTRY_REVISION,
             registry_fingerprint=ac.registry_fingerprint(), tool_commit=TOOL_COMMIT, declarations_sha256=DECL_SHA,
             declarations_version="1.7.0", assets=[record])
    c.update(head or {})
    p = ENV.cdir / f"census_{next(_N)}.json"
    p.write_text(json.dumps(c), encoding="utf-8")
    git(ENV.repo, "add", "--", str(p))
    return p


def cert(ledger, asset, crit="Build.registered", *, fp=None, n=0, up=(), verdict="PASS", files=1, **over):
    """Certify through E5.1's real writer."""
    wps = put_writer(asset, n, files)
    d = dict(asset=asset, layer=layer_of(asset), criterion=crit, verdict=verdict,
             evidence=dict(census_run_id=RUN, measured="m"), verified_by="t", ledger_path=ledger, verified_on=NOW,
             census_path=census_file(asset, crit, verdict, files=files), upstream_cert_ids=list(up))
    if verdict == "PASS":
        d.update(writer_files=wps, writer_repo=ENV.repo, semantic_fingerprint=fp_of(asset) if fp is None else fp)
    d.update(over)
    return nc.write_certification(**d).record["cert_id"]


def obs(*assets, **over):
    """What the world looks like now: every asset unchanged unless `over[asset]` replaces a field."""
    out = {a: dict(writer_hashes=wh_of(a), writer_paths=list(wh_of(a)), semantic_fingerprint=fp_of(a)) for a in assets}
    for a, o in over.items():
        out[a] = dict(out.get(a, {}), **o)
    return out


def write_chained(p, rows):
    """Write `rows` (schema row first) with a CORRECT seq and prev_sha256 chain, serialised by E5.1's own `_dump`:
    for tests that hand-shape a ledger to exercise E5.5's shape checks past E5.1's chain verification."""
    out, prev = [], None
    for i, r in enumerate(rows):
        r = dict(r)
        if i:
            r["seq"], r["prev_sha256"] = i, prev
        line = nc._dump(r)
        prev = shab(line)
        out.append(line)
    p.write_bytes(b"\n".join(out) + b"\n")


def raw(p):
    return p.read_bytes()


def lines(p):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def run(ledger, observed, **kw):
    kw.setdefault("commit", COMMIT)
    kw.setdefault("now", NOW)
    return sc.invalidate(ledger, observed, **kw)


def chain(ledger):
    """bg_a <- bg_b <- bg_c, plus an unrelated bg_d. Returns the cert ids."""
    a = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a])
    c = cert(ledger, "bg_c", up=[b])
    d = cert(ledger, "bg_d")
    return a, b, c, d


# ═══════════════ (1) the semantic row fingerprint ═══════════════

DECL_V = dict(table="ph_nimitta", scope="chart", natural_key=["nimitta_id"],
              volatile_columns=["id", "created_at", "build_id"])
DECL_S = dict(table="ph_nimitta", scope="chart", natural_key=["nimitta_id"], semantic_columns=["label", "weight"])
ROWS = [
    dict(id=1, created_at="2026-10-01T00:00:00", build_id="b1", nimitta_id="n2", label="two", weight=2),
    dict(id=2, created_at="2026-10-01T00:00:00", build_id="b1", nimitta_id="n1", label="one", weight=1),
]


def fpr(rows, decl=None):
    return sc.fingerprint_rows(rows, sc.validate_declaration(decl or DECL_V))


def test_fingerprint_is_a_sha256_hex_and_deterministic():
    f = fpr(ROWS)
    assert len(f) == 64 and set(f) <= set("0123456789abcdef") and f == fpr(copy.deepcopy(ROWS))


def test_fingerprint_does_not_depend_on_row_order_or_dict_key_order():
    shuffled = [dict(reversed(list(r.items()))) for r in reversed(ROWS)]
    assert fpr(shuffled) == fpr(ROWS)


def test_an_idempotent_rebuild_that_changes_only_volatile_columns_keeps_the_fingerprint():
    rebuilt = [dict(r, id=r["id"] + 100, created_at="2026-12-31T23:59:59", build_id="b2") for r in ROWS]
    assert fpr(rebuilt) == fpr(ROWS)


@pytest.mark.parametrize("change", [
    lambda r: r.update(label="CHANGED"),
    lambda r: r.update(weight=3),
    lambda r: r.update(nimitta_id="n9"),
])
def test_a_semantic_change_moves_the_fingerprint(change):
    rows = copy.deepcopy(ROWS)
    change(rows[0])
    assert fpr(rows) != fpr(ROWS)


def test_adding_or_dropping_a_row_moves_the_fingerprint():
    assert fpr(ROWS[:1]) != fpr(ROWS)
    assert fpr(ROWS + [dict(ROWS[0], nimitta_id="n3")]) != fpr(ROWS)


def test_in_volatile_mode_a_new_non_volatile_column_is_a_material_change():
    assert fpr([dict(r, extra="x") for r in ROWS]) != fpr(ROWS)


def test_semantic_columns_mode_reads_only_the_declared_columns_plus_the_key():
    base = fpr(ROWS, DECL_S)
    assert fpr([dict(r, label=r["label"], id=77, junk="x") for r in ROWS], DECL_S) == base
    assert fpr([dict(r, label="z") for r in ROWS], DECL_S) != base


def test_the_declaration_is_part_of_the_fingerprint():
    other = dict(DECL_S, semantic_columns=["label"])
    assert fpr(ROWS, DECL_S) != fpr(ROWS, other)


def test_the_declaration_distinguishes_even_empty_tables():
    assert fpr([], DECL_V) != fpr([], dict(DECL_V, volatile_columns=["id"]))
    assert fpr([], DECL_S) != fpr([], dict(DECL_S, semantic_columns=["label"]))


def test_an_empty_table_has_a_fingerprint_distinct_from_a_populated_one():
    assert fpr([]) != fpr(ROWS) and len(fpr([])) == 64


EMB_V = dict(column="emb", source_columns=["label"], model_id="text-embedding-3-small@2026-01")
DECL_E = dict(DECL_S, embedding=EMB_V)                                   # semantic mode: label, weight + emb (excluded)
DECL_EV = dict(DECL_V, volatile_columns=["id", "created_at", "build_id"], embedding=EMB_V)


def noisy(vec, scale=1e-7, seed=0):
    import random
    r = random.Random(seed)
    return [x + r.uniform(-scale, scale) for x in vec]


def test_embeddings_are_never_hashed_noise_in_a_vector_changes_nothing():
    import random
    r = random.Random(7)
    base = [dict(nimitta_id=f"n{i}", label=f"l{i}", weight=i, emb=[r.uniform(-1, 1) for _ in range(64)]) for i in range(50)]
    ref = fpr(base, DECL_E)
    for seed in range(5):
        jittered = [dict(x, emb=noisy(x["emb"], 1e-7, seed)) for x in base]       # float32-ish noise on every row
        assert fpr(jittered, DECL_E) == ref
    assert fpr([dict(x, emb=None) for x in base], DECL_E) == ref                  # a NULL embedding is allowed, too
    assert fpr([dict(x, emb="[0.1,0.2]") for x in base], DECL_E) == ref
    assert fpr([dict(x, emb=[float("nan")]) for x in base], DECL_E) == ref        # not read, so not judged


def test_the_embedding_column_is_not_in_the_payload_in_volatile_mode_either():
    rows = [dict(r, emb=[0.1, 0.2]) for r in ROWS]
    noisy_rows = [dict(r, emb=[0.1000001, 0.2]) for r in ROWS]
    null_rows = [dict(r, emb=None) for r in ROWS]
    assert fpr(rows, DECL_EV) == fpr(noisy_rows, DECL_EV) == fpr(null_rows, DECL_EV)
    # without the declaration the column IS content (and a change in it is a material change)
    assert fpr(rows, DECL_V) != fpr(noisy_rows, DECL_V)


def test_an_embedding_is_covered_through_its_source_columns_and_model_id():
    base = [dict(nimitta_id="n1", label="x", weight=1, emb=None)]
    ref = fpr(base, DECL_E)
    assert fpr([dict(base[0], label="CHANGED")], DECL_E) != ref                    # the source text changed
    other_model = dict(DECL_E, embedding=dict(EMB_V, model_id="another-model@2"))
    assert fpr(base, other_model) != ref                                            # the model changed: re-embedded
    assert fpr([], DECL_E) != fpr([], other_model)                                  # ...even for an empty table
    two_src = dict(DECL_E, embedding=dict(EMB_V, source_columns=["label", "weight"]))
    assert fpr([], two_src) != fpr([], DECL_E)


def test_the_embedding_selection_never_reads_the_vector_column():
    assert sc.build_select(sc.validate_declaration(DECL_E)) == \
        'SELECT "nimitta_id", "label", "weight" FROM "ph_nimitta" WHERE "chart_id" = %s'


@pytest.mark.parametrize("patch,why", [
    (dict(embedding=dict(EMB_V, model_id="")), "blank model id"),
    (dict(embedding=dict(EMB_V, model_id="  m ")), "model id with edge whitespace"),
    (dict(embedding=dict(EMB_V, model_id="m" * 201)), "model id too long"),
    (dict(embedding=dict(EMB_V, model_id="a\nb")), "control character"),
    (dict(embedding=dict(EMB_V, model_id=None)), "no model id"),
    (dict(embedding=dict(EMB_V, source_columns=[])), "no source columns"),
    (dict(embedding=dict(EMB_V, source_columns=["nope"])), "source column not semantic"),
    (dict(embedding=dict(EMB_V, column="Emb Col")), "bad column identifier"),
    (dict(embedding=dict(EMB_V, column="nimitta_id")), "column is the key"),
    (dict(embedding=dict(EMB_V, column="label")), "column listed as semantic"),
    (dict(embedding={"column": "emb", "source_columns": ["label"]}), "model_id missing"),
    (dict(embedding=dict(EMB_V, tolerance=0.1)), "unknown embedding key"),
    (dict(embedding=[EMB_V, EMB_V]), "the same column twice"),
    (dict(embedding=[EMB_V, dict(EMB_V, column="emb2", source_columns=["emb"])]), "source is an embedding"),
    (dict(embedding_policy={"emb": {"decimals": 4}}), "the old rounding policy is gone"),
])
def test_bad_embedding_declarations_are_refused(patch, why):
    with pytest.raises(sc.BadDeclaration):
        sc.validate_declaration(dict(DECL_S, **patch))


def test_a_volatile_source_column_or_a_key_embedding_is_refused_in_volatile_mode():
    with pytest.raises(sc.BadDeclaration):
        sc.validate_declaration(dict(DECL_V, embedding=dict(EMB_V, source_columns=["id"])))
    with pytest.raises(sc.BadDeclaration):
        sc.validate_declaration(dict(DECL_V, embedding=dict(EMB_V, column="nimitta_id")))


def test_two_embeddings_are_supported_and_both_excluded():
    decl = dict(DECL_S, embedding=[EMB_V, dict(column="emb2", source_columns=["weight"], model_id="m2")])
    a = [dict(nimitta_id="n1", label="x", weight=1, emb=[1.0], emb2=[2.0])]
    b = [dict(nimitta_id="n1", label="x", weight=1, emb=[9.0], emb2=None)]
    assert fpr(a, decl) == fpr(b, decl)


def test_volatile_mode_needs_the_embedding_source_columns_in_the_rows():
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(id=1, nimitta_id="n1", emb=[1.0])], dict(DECL_V, embedding=dict(EMB_V, source_columns=["label"])))


def test_database_native_value_types_are_canonicalised():
    base = [dict(nimitta_id="n1", label="x", weight=decimal.Decimal("1.50"))]
    same = [dict(nimitta_id="n1", label="x", weight=decimal.Decimal("1.5"))]
    assert fpr(base, DECL_S) == fpr(same, DECL_S)
    u = uuid.UUID("12345678-1234-5678-1234-567812345678")
    t = dt.datetime(2026, 1, 2, 3, 4, 5, tzinfo=dt.timezone.utc)
    d = dict(DECL_S, semantic_columns=["label", "weight"])
    assert fpr([dict(nimitta_id=u, label=t, weight={"b": 1, "a": [1, 2]})], d) == \
        fpr([dict(nimitta_id=str(u), label=t.isoformat(), weight={"a": [1, 2], "b": 1})], d)


def test_a_row_missing_a_declared_column_raises():
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(nimitta_id="n1", label="x")], DECL_S)                              # no `weight`
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(label="x", weight=1)], DECL_S)                                     # no natural key


def test_duplicate_or_null_natural_keys_raise():
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(nimitta_id="n1", label="a", weight=1), dict(nimitta_id="n1", label="b", weight=2)], DECL_S)
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(nimitta_id=None, label="a", weight=1)], DECL_S)


@pytest.mark.parametrize("v", [float("nan"), float("inf"), b"bytes", {1, 2}, object()])
def test_values_with_no_canonical_form_raise(v):
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(nimitta_id="n1", label=v, weight=1)], DECL_S)


def test_a_non_mapping_row_or_non_iterable_rows_raise():
    with pytest.raises(sc.UnreadableInput):
        fpr([("n1", "x", 1)], DECL_S)
    with pytest.raises(sc.UnreadableInput):
        sc.fingerprint_rows(None, sc.validate_declaration(DECL_S))


def test_in_volatile_mode_rows_must_share_one_column_set():
    with pytest.raises(sc.UnreadableInput):
        fpr([dict(ROWS[0]), dict(ROWS[1], extra=1)])


@pytest.mark.parametrize("patch,why", [
    (dict(natural_key=[]), "empty natural key"),
    (dict(natural_key="nimitta_id"), "natural key not a list"),
    (dict(volatile_columns=["id"], semantic_columns=["label"]), "both modes"),
    (dict(volatile_columns=None), "neither mode"),
    (dict(volatile_columns=["nimitta_id"]), "key is volatile"),
    (dict(table='x"; DROP TABLE y; --'), "injection in table"),
    (dict(table="Has Space"), "bad table"),
    (dict(table="UPPER"), "uppercase table"),
    (dict(natural_key=["a b"]), "bad key identifier"),
    (dict(volatile_columns=["id", 'c"d']), "bad volatile identifier"),
    (dict(scope="everywhere"), "bad scope"),
    (dict(scope="chart", scope_column="chart id"), "bad scope column"),
    (dict(naive_utc_columns=["a b"]), "bad naive column"),
    (dict(naive_utc_columns="created_at"), "naive columns not a list"),
    (dict(surprise=1), "unknown declaration key"),
])
def test_bad_declarations_are_refused(patch, why):
    d = dict(DECL_V)
    d.update(patch)
    with pytest.raises(sc.BadDeclaration):
        sc.validate_declaration(d)


def test_declarations_document_validates_every_asset_and_names_the_bad_one():
    ok = sc.validate_declarations({"ph_x": dict(DECL_V), "ph_y": dict(DECL_S)})
    assert set(ok) == {"ph_x", "ph_y"}
    with pytest.raises(sc.BadDeclaration, match="ph_bad"):
        sc.validate_declarations({"ph_ok": dict(DECL_V), "ph_bad": dict(DECL_V, natural_key=[])})
    with pytest.raises(sc.BadDeclaration):
        sc.validate_declarations({"Bad Asset": dict(DECL_V)})
    with pytest.raises(sc.BadDeclaration):
        sc.validate_declarations([])


# ───────────────────────── canonical form of timestamps, zeros, decimals, jsonb, text ─────────────────────────

DECL_T = dict(table="t", scope="chart", natural_key=["k"], semantic_columns=["v"])


def one(v, decl=DECL_T):
    return sc.fingerprint_rows([dict(k=1, v=v)], sc.validate_declaration(decl))


def test_the_same_instant_in_any_zone_is_the_same_value():
    utc = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc)
    ist = utc.astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    est = utc.astimezone(dt.timezone(dt.timedelta(hours=-5)))
    assert ist.isoformat() != utc.isoformat()
    assert one(utc) == one(ist) == one(est)
    assert one(utc) != one(utc + dt.timedelta(microseconds=1))               # a different instant is a different value


def test_a_naive_datetime_is_refused_unless_the_column_is_declared_naive_utc():
    naive = dt.datetime(2026, 1, 1, 12, 0)
    with pytest.raises(sc.UnreadableInput):
        one(naive)
    declared = dict(DECL_T, naive_utc_columns=["v"])
    assert one(naive, declared) == one(dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.timezone.utc), declared)
    assert one(naive, declared) == one(dt.datetime(2026, 1, 1, 17, 30, tzinfo=dt.timezone(dt.timedelta(hours=5, minutes=30))), declared)


def test_the_naive_declaration_is_per_column_and_covers_key_columns_too():
    naive = dt.datetime(2026, 1, 1, 12, 0)
    decl = dict(table="t", scope="chart", natural_key=["at"], semantic_columns=["v"], naive_utc_columns=["at"])
    assert sc.fingerprint_rows([dict(at=naive, v=1)], sc.validate_declaration(decl))
    with pytest.raises(sc.UnreadableInput):
        sc.fingerprint_rows([dict(at=naive, v=dt.datetime(2026, 1, 1))], sc.validate_declaration(decl))   # v is not declared
    with pytest.raises(sc.UnreadableInput):
        sc.fingerprint_rows([dict(at=naive, v=1)], sc.validate_declaration(dict(decl, naive_utc_columns=[])))


def test_a_time_of_day_needs_the_naive_declaration_and_a_zoned_time_is_refused():
    with pytest.raises(sc.UnreadableInput):
        one(dt.time(1, 2, 3))
    assert one(dt.time(1, 2, 3), dict(DECL_T, naive_utc_columns=["v"]))
    with pytest.raises(sc.UnreadableInput):
        one(dt.time(1, 2, 3, tzinfo=dt.timezone.utc), dict(DECL_T, naive_utc_columns=["v"]))
    assert one(dt.date(2026, 1, 2)) != one(dt.date(2026, 1, 3))


def test_negative_zero_is_zero_for_floats_and_decimals():
    assert one(0.0) == one(-0.0)
    assert one(decimal.Decimal("0")) == one(decimal.Decimal("-0")) == one(decimal.Decimal("0.000"))
    assert one([0.0, {"a": -0.0}]) == one([-0.0, {"a": 0.0}])
    assert one(0.0) != one(1.0) and one(decimal.Decimal("0")) != one(decimal.Decimal("1"))


def test_decimals_are_exact_beyond_28_digits():
    a, b = decimal.Decimal("1.0000000000000000000000000001"), decimal.Decimal("1.0000000000000000000000000002")
    big1, big2 = decimal.Decimal("12345678901234567890123456789012"), decimal.Decimal("12345678901234567890123456789013")
    assert one(a) != one(b) and one(big1) != one(big2)
    assert one(decimal.Decimal("1.50")) == one(decimal.Decimal("1.5")) == one(decimal.Decimal("15E-1"))
    assert one(decimal.Decimal("100")) == one(decimal.Decimal("1E+2")) != one(decimal.Decimal("10"))
    assert one(decimal.Decimal("-1.5")) != one(decimal.Decimal("1.5"))
    huge = decimal.Decimal("9" * 200 + "." + "1" * 200)
    assert one(huge) == one(decimal.Decimal(str(huge))) and one(huge) != one(decimal.Decimal("9" * 200 + "." + "1" * 199 + "2"))


def test_a_jsonb_object_that_looks_like_our_decimal_marker_cannot_collide():
    assert one(decimal.Decimal("1")) != one({"$decimal": "1E0"})
    assert one({"$decimal": "1E0"}) != one({"$obj": {"$decimal": "1E0"}})
    assert one({"$x": 1}) != one({"$obj": {"$x": 1}})
    assert one({"$obj": {"a": 1}}) != one({"a": 1})
    assert one({"a": 1, "b": 2}) == one({"b": 2, "a": 1})


def test_text_with_an_unpaired_surrogate_is_a_refusal_not_a_crash():
    for bad in ("\ud800", "ok\udfff", ["x", "\ud800"], {"k\ud800": 1}, {"k": "\ud800"}):
        with pytest.raises(sc.UnreadableInput):
            one(bad)
    assert one("héllo \U0001f600") != one("hello")


def test_integers_booleans_and_floats_stay_distinct():
    assert one(True) != one(1) and one(1) != one(1.0) and one(None) != one(0)


# ───────────────────────── the header hashes the declaration ─────────────────────────

BASE_H = dict(table="ph_x", scope="chart", natural_key=["a", "b"], semantic_columns=["c", "d"])


def hdr(**over):
    return sc.fingerprint_rows([], sc.validate_declaration(dict(BASE_H, **over)))


@pytest.mark.parametrize("over,why", [
    (dict(table="ph_y"), "table"),
    (dict(scope="global"), "scope"),
    (dict(scope_column="subject_chart"), "scope column"),
    (dict(natural_key=["b", "a"]), "natural key ORDER"),
    (dict(natural_key=["a"], semantic_columns=["b", "c", "d"]), "key vs semantic split"),
    (dict(semantic_columns=["c"]), "semantic columns"),
    (dict(semantic_columns=None, volatile_columns=["c", "d"]), "mode, same listed columns"),
    (dict(naive_utc_columns=["c"]), "naive columns"),
    (dict(embedding=dict(column="e", source_columns=["c"], model_id="m1")), "embedding declared"),
])
def test_every_part_of_the_declaration_is_in_the_header_even_for_an_empty_table(over, why):
    assert hdr(**over) != hdr(), why


def test_two_embedding_declarations_that_differ_only_in_model_or_sources_differ():
    e1 = dict(column="e", source_columns=["c"], model_id="m1")
    assert hdr(embedding=e1) != hdr(embedding=dict(e1, model_id="m2"))
    assert hdr(embedding=e1) != hdr(embedding=dict(e1, source_columns=["c", "d"]))
    assert hdr(embedding=e1) != hdr(embedding=dict(e1, column="e2"))


def test_a_global_asset_does_not_hash_a_scope_column():
    assert hdr(scope="global") == hdr(scope="global", scope_column="whatever")


def test_the_header_is_not_a_prefix_of_row_data(tmp_path):
    # a declaration change must not be maskable by row content: same rows, different table => different fingerprint
    rows = [dict(a=1, b=2, c=3, d=4)]
    assert (sc.fingerprint_rows(rows, sc.validate_declaration(BASE_H))
            != sc.fingerprint_rows(rows, sc.validate_declaration(dict(BASE_H, table="ph_y"))))


# ───────────────────────── the read-only loader ─────────────────────────

class FakeCursor:
    def __init__(self, cols, rows, fail=None, chunk=2):
        self.description = [(c,) for c in cols]
        self.rows, self.fail, self.chunk = list(rows), fail, chunk
        self.executed = []
        self.closed = False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self.fail:
            raise self.fail

    def fetchmany(self, n):
        out, self.rows = self.rows[:min(n, self.chunk)], self.rows[min(n, self.chunk):]
        return out

    def close(self):
        self.closed = True


class FakeConn:
    def __init__(self, cur):
        self.cur, self.committed, self.rolled_back, self.cursor_name = cur, False, False, None

    def cursor(self, name=None):
        self.cursor_name = name
        return self.cur

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_the_select_is_one_of_three_fixed_shapes_with_quoted_validated_identifiers():
    assert sc.build_select(sc.validate_declaration(DECL_S)) == \
        'SELECT "nimitta_id", "label", "weight" FROM "ph_nimitta" WHERE "chart_id" = %s'
    assert sc.build_select(sc.validate_declaration(DECL_V)) == 'SELECT * FROM "ph_nimitta" WHERE "chart_id" = %s'
    g = sc.validate_declaration(dict(DECL_V, scope="global", table="brahma_ontology"))
    assert sc.build_select(g) == 'SELECT * FROM "brahma_ontology"'
    c = sc.validate_declaration(dict(DECL_S, scope_column="subject_chart"))
    assert sc.build_select(c).endswith('WHERE "subject_chart" = %s')


def test_load_rows_executes_exactly_one_parameterised_select_and_returns_dicts():
    cur = FakeCursor(["id", "created_at", "build_id", "nimitta_id", "label", "weight"],
                     [tuple(r[k] for k in ("id", "created_at", "build_id", "nimitta_id", "label", "weight")) for r in ROWS])
    conn = FakeConn(cur)
    rows = sc.load_rows(conn, sc.validate_declaration(DECL_V), chart_id="482012f1-710e-4a25-994a-93821f5871aa")
    assert rows == ROWS
    assert cur.executed == [('SELECT * FROM "ph_nimitta" WHERE "chart_id" = %s', ("482012f1-710e-4a25-994a-93821f5871aa",))]
    assert cur.executed[0][0].startswith("SELECT ") and not conn.committed


def test_the_chart_id_is_only_ever_a_bound_parameter_never_part_of_the_sql():
    cur = FakeCursor(["nimitta_id", "label", "weight"], [])
    sc.load_rows(FakeConn(cur), sc.validate_declaration(DECL_S), chart_id="x'; DROP TABLE t; --")
    sql, params = cur.executed[0]
    assert "DROP" not in sql and params == ("x'; DROP TABLE t; --",)


def test_scope_and_chart_id_must_agree():
    cur = FakeCursor([], [])
    with pytest.raises(sc.UnreadableInput):
        sc.load_rows(FakeConn(cur), sc.validate_declaration(DECL_V))                                  # chart scope, no id
    with pytest.raises(sc.UnreadableInput):
        sc.load_rows(FakeConn(cur), sc.validate_declaration(dict(DECL_V, scope="global")), chart_id="x")
    assert cur.executed == []


def test_load_rows_never_commits_nor_rolls_back_and_closes_only_its_cursor():
    cols = ["nimitta_id", "label", "weight"]
    ok = FakeConn(FakeCursor(cols, [("n1", "x", 1)]))
    sc.load_rows(ok, sc.validate_declaration(DECL_S), chart_id="c")
    assert not ok.committed and not ok.rolled_back and ok.cur.closed
    bad = FakeConn(FakeCursor([], [], fail=RuntimeError("boom")))
    with pytest.raises(sc.UnreadableInput):
        sc.load_rows(bad, sc.validate_declaration(DECL_S), chart_id="c")
    assert not bad.committed and not bad.rolled_back and bad.cur.closed         # the caller owns the transaction


def test_load_rows_refuses_a_table_larger_than_the_guard_and_names_the_streaming_option():
    cols = ["nimitta_id", "label", "weight"]
    rows = [(f"n{i}", "x", i) for i in range(11)]
    with pytest.raises(sc.UnreadableInput, match="max_rows"):
        sc.load_rows(FakeConn(FakeCursor(cols, rows, chunk=4)), sc.validate_declaration(DECL_S), chart_id="c", max_rows=10)
    assert len(sc.load_rows(FakeConn(FakeCursor(cols, rows, chunk=4)), sc.validate_declaration(DECL_S), chart_id="c",
                            max_rows=11)) == 11
    for bad in (0, -1, True, "5", None):
        with pytest.raises(sc.UnreadableInput):
            sc.load_rows(FakeConn(FakeCursor(cols, rows)), sc.validate_declaration(DECL_S), chart_id="c", max_rows=bad)


def test_a_named_server_side_cursor_is_used_when_asked():
    cols = ["nimitta_id", "label", "weight"]
    c = FakeConn(FakeCursor(cols, [("n1", "x", 1)]))
    sc.load_rows(c, sc.validate_declaration(DECL_S), chart_id="c", cursor_name="fp_stream")
    assert c.cursor_name == "fp_stream"
    c2 = FakeConn(FakeCursor(cols, [("n1", "x", 1)]))
    sc.table_fingerprint(c2, sc.validate_declaration(DECL_S), chart_id="c", cursor_name="s2")
    assert c2.cursor_name == "s2"


def test_load_rows_reads_every_chunk():
    cols = ["nimitta_id", "label", "weight"]
    rows = [(f"n{i}", "x", i) for i in range(7)]
    got = sc.load_rows(FakeConn(FakeCursor(cols, rows, chunk=3)), sc.validate_declaration(DECL_S), chart_id="c")
    assert len(got) == 7 and got[6]["nimitta_id"] == "n6"


def test_a_database_error_is_unreadable_input_never_an_empty_table():
    cur = FakeCursor([], [], fail=RuntimeError("connection reset"))
    with pytest.raises(sc.UnreadableInput):
        sc.load_rows(FakeConn(cur), sc.validate_declaration(DECL_S), chart_id="c")
    with pytest.raises(sc.UnreadableInput):
        sc.table_fingerprint(FakeConn(cur), sc.validate_declaration(DECL_S), chart_id="c")


def test_a_cursor_with_no_description_is_unreadable():
    cur = FakeCursor(["a"], [(1,)])
    cur.description = None
    with pytest.raises(sc.UnreadableInput):
        sc.load_rows(FakeConn(cur), sc.validate_declaration(DECL_S), chart_id="c")


def test_table_fingerprint_equals_fingerprint_rows_of_the_same_rows():
    cols = ["id", "created_at", "build_id", "nimitta_id", "label", "weight"]
    cur = FakeCursor(cols, [tuple(r[k] for k in cols) for r in ROWS])
    decl = sc.validate_declaration(DECL_V)
    assert sc.table_fingerprint(FakeConn(cur), decl, chart_id="c") == sc.fingerprint_rows(ROWS, decl)


# ───────────────────────── parity with E5.1's private grammar (copied here, pinned here) ─────────────────────────

def test_the_cert_id_grammar_and_relpath_check_are_copies_of_e51s():
    assert sc._CERT_ID.pattern == nc._CERT_ID.pattern
    for p in ("a/b.py", "", "/abs", "a//b", "a/../b", "..", "a\\b", "a/./b", "x" * 300, "ok.py", None, 5, "a/b/"):
        assert sc._check_relpath(p) == nc._check_relpath(p), p
    for u in ("bg_a|gate|Build.registered@1", "bg_a|addition|D-TIME@12", "bg_a|gate|x@0", "bg_A|gate|x@1", "a|b|c@1", ""):
        assert bool(sc._CERT_ID.fullmatch(u)) == bool(nc._CERT_ID.fullmatch(u)), u


# ═══════════════ (2) detection: three comparisons, transitivity, only what changed ═══════════════

def test_nothing_changed_nothing_is_stale(ledger):
    a, b, c, d = chain(ledger)
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert ev.stale == {} and sorted(ev.current) == sorted([a, b, c, d])


def test_a_changed_writer_hash_makes_that_asset_stale_and_names_the_path(ledger):
    a, b, c, d = chain(ledger)
    o = obs("bg_a", "bg_b", "bg_c", "bg_d", bg_d=dict(writer_hashes=wh_of("bg_d", 1)))
    ev = sc.evaluate(raw(ledger), o)
    assert set(ev.stale) == {d}
    r = ev.stale[d][0]
    assert r["code"] == "writer_hash" and r["path"] == wpath("bg_d")
    assert r["recorded"] == wh_of("bg_d")[wpath("bg_d")] and r["observed"] == wh_of("bg_d", 1)[wpath("bg_d")]


def test_a_changed_semantic_fingerprint_makes_that_asset_stale(ledger):
    a, b, c, d = chain(ledger)
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", "bg_d", bg_d=dict(semantic_fingerprint=fp_of("bg_d", 1))))
    assert set(ev.stale) == {d} and ev.stale[d][0]["code"] == "semantic_fingerprint"
    assert ev.stale[d][0]["recorded"] == fp_of("bg_d") and ev.stale[d][0]["observed"] == fp_of("bg_d", 1)


def test_a_dependent_citing_a_superseded_upstream_generation_is_stale(ledger):
    a = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a])
    a2 = cert(ledger, "bg_a", fp=fp_of("bg_a", 1))                               # bg_a re-certified: generation 2
    assert a2.endswith("@2")
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    assert set(ev.stale) == {b}
    r = ev.stale[b][0]
    assert r["code"] == "upstream_generation" and r["upstream"] == a and r["cited"] == 1 and r["latest"] == 2


def test_staleness_propagates_transitively_and_only_to_dependents(ledger):
    a, b, c, d = chain(ledger)
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    assert set(ev.stale) == {a, b, c}, "A changed: B rests on A and C on B; D is unrelated"
    assert [x["code"] for x in ev.stale[a]] == ["semantic_fingerprint"]
    assert ev.stale[b][0]["code"] == "upstream_stale" and ev.stale[b][0]["upstream"] == a
    assert ev.stale[c][0]["code"] == "upstream_stale" and ev.stale[c][0]["upstream"] == b
    assert ev.current == [d]


def test_an_idempotent_rebuild_invalidates_nothing_downstream_end_to_end(ledger):
    # the asset is rebuilt: every volatile column changes, the semantic fingerprint does not
    before = fpr(ROWS)
    rebuilt = fpr([dict(r, id=r["id"] + 9, created_at="2027-01-01", build_id="b9") for r in ROWS])
    assert before == rebuilt
    a = cert(ledger, "bg_a", fp=before)
    b = cert(ledger, "bg_b", up=[a])
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", bg_a=dict(semantic_fingerprint=rebuilt)))
    assert ev.stale == {} and sorted(ev.current) == sorted([a, b])


def test_a_material_rebuild_invalidates_the_asset_and_its_dependents(ledger):
    before = fpr(ROWS)
    changed = fpr([dict(ROWS[0], label="different"), ROWS[1]])
    a = cert(ledger, "bg_a", fp=before)
    b = cert(ledger, "bg_b", up=[a])
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", bg_a=dict(semantic_fingerprint=changed)))
    assert set(ev.stale) == {a, b}


def test_a_stale_dependent_does_not_make_its_upstream_stale(ledger):
    a, b, c, d = chain(ledger)
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", "bg_d", bg_c=dict(writer_hashes=wh_of("bg_c", 1))))
    assert set(ev.stale) == {c}


def test_invalidation_is_remembered_when_the_world_reverts(ledger):
    a, b, c, d = chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    # the world reverts to what was certified, but A@1 stays invalidated: the ledger remembers
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert ev.stale == {} and ev.current == [d] and set(ev.invalidated) == {a, b, c}


def test_a_certificate_resting_on_an_already_invalidated_upstream_is_stale_though_everything_observed_matches(ledger):
    a = cert(ledger, "bg_a")
    run(ledger, obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))            # A@1 invalidated
    b = cert(ledger, "bg_b", up=[a])                                                       # E5.1 cannot know; E5.5 does
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b"))
    assert set(ev.stale) == {b}
    assert ev.stale[b][0]["code"] == "upstream_stale" and ev.stale[b][0]["upstream"] == a
    assert ev.stale[b][0]["why"] == "invalidated"


def test_two_independent_reasons_are_both_reported(ledger):
    a, b, c, d = chain(ledger)
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", "bg_d",
                                      bg_d=dict(writer_hashes=wh_of("bg_d", 1), semantic_fingerprint=fp_of("bg_d", 1))))
    assert sorted(r["code"] for r in ev.stale[d]) == ["semantic_fingerprint", "writer_hash"]


def test_a_pass_citing_a_non_passing_upstream_is_stale(ledger):
    # E5.1 refuses to write this; the detector must still not call a hand-edited ledger current
    a = cert(ledger, "bg_a", verdict="FAIL")
    b = cert(ledger, "bg_b")
    rec = dict(lines(ledger)[-1], upstream_cert_ids=[a])
    write_chained(ledger, lines(ledger)[:-1] + [rec])
    ev = sc.evaluate(raw(ledger), obs("bg_b"))
    assert set(ev.stale) == {b} and ev.stale[b][0]["code"] == "upstream_not_passing"


def reg(assets, **over):
    return dict(dict(revision=ac.REGISTRY_REVISION, fingerprint=ac.registry_fingerprint(), assets=list(assets)), **over)


def test_the_registry_check_applies_only_to_the_assets_the_caller_names(ledger):
    a, b = cert(ledger, "bg_a"), cert(ledger, "bg_b")
    o = obs("bg_a", "bg_b")
    bumped = dict(revision=ac.REGISTRY_REVISION + 1)
    assert sc.evaluate(raw(ledger), o, registry=reg(["bg_a"])).stale == {}
    assert sc.evaluate(raw(ledger), o).stale == {}
    ev = sc.evaluate(raw(ledger), o, registry=reg(["bg_a"], **bumped))
    assert set(ev.stale) == {a} and ev.stale[a][0]["code"] == "registry"          # b is NOT invalidated by a bump
    ev = sc.evaluate(raw(ledger), o, registry=reg(["bg_a", "bg_b"], fingerprint="f" * 64))
    assert set(ev.stale) == {a, b}
    assert sc.evaluate(raw(ledger), o, registry=reg(["bg_zzz"], **bumped)).stale == {}     # names no certified asset


def test_a_registry_observation_without_assets_is_refused_not_applied_to_everything(ledger):
    cert(ledger, "bg_a")
    for bad in (dict(revision=1, fingerprint="f" * 64), dict(revision=1, fingerprint="f" * 64, assets=[]),
                dict(revision=1, fingerprint="f" * 64, assets="bg_a"), dict(revision=1, fingerprint="f" * 64, assets=["Bg A"]),
                dict(revision=True, fingerprint="f" * 64, assets=["bg_a"]), dict(revision=1, assets=["bg_a"]), "x", []):
        with pytest.raises(sc.UnreadableInput):
            sc.evaluate(raw(ledger), obs("bg_a"), registry=bad)
    before = raw(ledger)
    with pytest.raises(sc.UnreadableInput):
        run(ledger, obs("bg_a"), registry=dict(revision=1, fingerprint="f" * 64))
    assert raw(ledger) == before


def test_the_registry_check_never_applies_to_additions(ledger):
    add = nc.write_certification(asset="bg_a", layer="L0", kind="addition", criterion="D-GROUNDING", criterion_version=1,
                                 detector="grounding_probe.py", verdict="PASS", evidence=dict(census_run_id=RUN),
                                 verified_by="t", ledger_path=ledger, verified_on=NOW, writer_files=put_writer("bg_a"),
                                 writer_repo=ENV.repo, semantic_fingerprint=fp_of("bg_a")).record["cert_id"]
    ev = sc.evaluate(raw(ledger), obs("bg_a"), registry=reg(["bg_a"], revision=ac.REGISTRY_REVISION + 7))
    assert ev.stale == {} and ev.current == [add]


def test_only_the_latest_generation_of_a_key_is_evaluated(ledger):
    a1 = cert(ledger, "bg_a")
    a2 = cert(ledger, "bg_a", fp=fp_of("bg_a", 1), n=1)
    ev = sc.evaluate(raw(ledger), obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1), writer_hashes=wh_of("bg_a", 1))))
    assert ev.stale == {} and ev.current == [a2] and a1 not in ev.current


def test_non_passing_records_are_not_certificates_and_need_no_observation(ledger):
    f = cert(ledger, "bg_a", verdict="FAIL")
    ev = sc.evaluate(raw(ledger), {})
    assert ev.stale == {} and ev.current == [] and f in ev.not_certificates


def test_a_computed_n_a_with_no_hashes_or_fingerprint_needs_no_observation_and_is_never_stale_by_itself(ledger, monkeypatch):
    rid = "Ldgr.source_presence#columns_any"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {rid: "N-22.t"})
    n = nc.write_certification(asset="bg_a", layer="L0", criterion="Ldgr.source_presence", verdict="N/A",
                               na_rule_id=rid, evidence=dict(census_run_id=RUN), verified_by="t", ledger_path=ledger,
                               verified_on=NOW,
                               census_path=census_file("bg_a", "Ldgr.source_presence", "N/A", cell=False,
                                                       rec=dict(target_columns=["id"]))).record["cert_id"]
    ev = sc.evaluate(raw(ledger), {})
    assert ev.stale == {} and ev.current == [n]


# ───────────────────────── writer files: changed, added, removed (two files) ─────────────────────────

def test_a_change_in_the_second_of_two_writer_files_makes_the_asset_stale(ledger):
    a = cert(ledger, "bg_a", files=2)
    assert len(lines(ledger)[1]["writer_hashes"]) == 2
    o = obs("bg_a")
    o["bg_a"] = dict(writer_hashes=wh_of("bg_a", 0, 2), writer_paths=list(wh_of("bg_a", 0, 2)),
                     semantic_fingerprint=fp_of("bg_a"))
    assert sc.evaluate(raw(ledger), o).stale == {}
    second = wpath("bg_a_2")
    o["bg_a"]["writer_hashes"] = dict(o["bg_a"]["writer_hashes"], **{second: H("changed")})
    ev = sc.evaluate(raw(ledger), o)
    assert set(ev.stale) == {a} and [(r["code"], r["path"]) for r in ev.stale[a]] == [("writer_hash", second)]
    first = wpath("bg_a")                                                       # and the first, symmetrically
    o2 = dict(bg_a=dict(o["bg_a"], writer_hashes=dict(wh_of("bg_a", 0, 2), **{first: H("changed")})))
    assert [(r["code"], r["path"]) for r in sc.evaluate(raw(ledger), o2).stale[a]] == [("writer_hash", first)]


def test_a_writer_file_added_to_the_asset_since_is_stale(ledger):
    a = cert(ledger, "bg_a")
    added = wpath("bg_a_new")
    o = obs("bg_a")
    o["bg_a"]["writer_paths"] = list(wh_of("bg_a")) + [added]                      # the registry now lists a second file
    ev = sc.evaluate(raw(ledger), o)
    assert set(ev.stale) == {a} and ev.stale[a] == [dict(code="writer_file_added", path=added)]


def test_a_writer_file_removed_from_the_asset_since_is_stale_and_needs_no_hash_for_it(ledger):
    a = cert(ledger, "bg_a", files=2)
    o = {"bg_a": dict(writer_hashes={wpath("bg_a"): wh_of("bg_a")[wpath("bg_a")]}, writer_paths=[wpath("bg_a")],
                      semantic_fingerprint=fp_of("bg_a"))}
    ev = sc.evaluate(raw(ledger), o)
    assert set(ev.stale) == {a} and ev.stale[a] == [dict(code="writer_file_removed", path=wpath("bg_a_2"))]


def test_a_writer_set_renamed_in_place_is_added_and_removed(ledger):
    a = cert(ledger, "bg_a")
    o = {"bg_a": dict(writer_hashes={wpath("bg_other"): H("x")}, writer_paths=[wpath("bg_other")],
                      semantic_fingerprint=fp_of("bg_a"))}
    ev = sc.evaluate(raw(ledger), o)
    assert [r["code"] for r in ev.stale[a]] == ["writer_file_added", "writer_file_removed"]


def test_the_full_writer_path_set_must_be_observed_and_well_formed(ledger):
    cert(ledger, "bg_a")
    with pytest.raises(sc.MissingObservation):
        sc.evaluate(raw(ledger), {"bg_a": dict(writer_hashes=wh_of("bg_a"), semantic_fingerprint=fp_of("bg_a"))})
    for bad in ("x", None, [wpath("bg_a"), wpath("bg_a")], ["/abs.py"], ["a/../b.py"], [5], {"a": 1}):
        with pytest.raises(sc.UnreadableInput):
            sc.evaluate(raw(ledger), obs("bg_a", bg_a=dict(writer_paths=bad)))


def test_a_recorded_writer_file_that_is_still_listed_but_has_no_observed_hash_raises(ledger):
    cert(ledger, "bg_a", files=2)
    o = {"bg_a": dict(writer_hashes={wpath("bg_a"): wh_of("bg_a")[wpath("bg_a")]},          # no hash for bg_a_2
                      writer_paths=[wpath("bg_a"), wpath("bg_a_2")], semantic_fingerprint=fp_of("bg_a"))}
    with pytest.raises(sc.MissingObservation):
        sc.evaluate(raw(ledger), o)


def test_a_certificate_that_recorded_no_writer_hashes_still_sees_an_added_writer_file(ledger):
    a = cert(ledger, "bg_a")
    rows = lines(ledger)
    rows[1].update(writer_hashes={}, writer_hashes_reason="service_no_writer")
    write_chained(ledger, rows)
    o = {"bg_a": dict(semantic_fingerprint=fp_of("bg_a"), writer_paths=[])}
    assert sc.evaluate(raw(ledger), o).stale == {}
    o["bg_a"]["writer_paths"] = [wpath("bg_a")]                                       # the asset has a writer file now
    assert sc.evaluate(raw(ledger), o).stale[a] == [dict(code="writer_file_added", path=wpath("bg_a"))]


# ───────────────────────── an upstream generation bump with identical output invalidates nothing ─────────────────────────

def test_an_upstream_recertified_with_the_same_semantic_fingerprint_does_not_stale_its_dependents(ledger):
    a1 = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a1])
    a2 = cert(ledger, "bg_a", n=1)                         # writer file changed: E5.1 mints generation 2, same output
    assert a2.endswith("@2") and lines(ledger)[-1]["semantic_fingerprint"] == fp_of("bg_a")
    o = obs("bg_a", "bg_b", bg_a=dict(writer_hashes=wh_of("bg_a", 1), writer_paths=list(wh_of("bg_a", 1))))
    ev = sc.evaluate(raw(ledger), o)
    assert ev.stale == {} and sorted(ev.current) == sorted([a2, b])


def test_an_upstream_generation_bump_with_a_different_fingerprint_still_stales_dependents(ledger):
    a1 = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a1])
    cert(ledger, "bg_a", fp=fp_of("bg_a", 1))
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    assert set(ev.stale) == {b} and ev.stale[b][0]["code"] == "upstream_generation"
    assert (ev.stale[b][0]["cited"], ev.stale[b][0]["latest"]) == (1, 2)


@pytest.mark.skipif(not hasattr(nc, "CITATION_STATES"), reason="needs E5.1 record_version 2 (citation_state): rebase onto it")
def test_a_same_output_bump_that_changes_the_citation_state_is_not_identical_output(ledger):
    # E5.1 record_version 2: Ldgr.source_presence / Carr.D1 records carry citation_state, read from the census cell. A
    # generation bump that changes it is a currency change a dependent must see; one that does not change it is not.
    cols = ["id", "source_citation"]

    def ldgr(asset, state, n=0, up=()):
        cf = census_file(asset, "Ldgr.source_presence", "PASS", rec=dict(target_columns=cols),
                         cell_extra=dict(citation_state=state))
        return cert(ledger, asset, "Ldgr.source_presence", n=n, up=up, census_path=cf)

    a1 = ldgr("bg_a", "sourced")
    b = cert(ledger, "bg_b", up=[a1])
    a2 = ldgr("bg_a", "sourced", n=1)                                              # writer changed, same output, same state
    assert a2.endswith("@2")
    o = obs("bg_a", "bg_b", bg_a=dict(writer_hashes=wh_of("bg_a", 1), writer_paths=list(wh_of("bg_a", 1))))
    assert sc.evaluate(raw(ledger), o).stale == {}                                  # control: identical output, nothing stale
    a3 = ldgr("bg_a", "sourced_ocr_unverified", n=1)                                # the state changed under the same rows
    assert a3.endswith("@3") and lines(ledger)[-1]["citation_state"] == "sourced_ocr_unverified"
    ev = sc.evaluate(raw(ledger), o)
    assert set(ev.stale) == {b} and ev.stale[b][0]["code"] == "upstream_generation"
    assert ev.stale[b][0]["cited"] == 1 and ev.stale[b][0]["latest"] == 3


def test_a_same_output_bump_whose_latest_generation_is_itself_stale_stales_the_dependents(ledger):
    a1 = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a1])
    a2 = cert(ledger, "bg_a", n=1)
    o = obs("bg_a", "bg_b", bg_a=dict(writer_hashes=wh_of("bg_a", 1), writer_paths=list(wh_of("bg_a", 1)),
                                     semantic_fingerprint=fp_of("bg_a", 9)))        # the rows changed since
    ev = sc.evaluate(raw(ledger), o)
    assert set(ev.stale) == {a2, b}
    assert ev.stale[b] == [dict(code="upstream_stale", upstream=a2, why="stale", cited=a1,
                                via="generation_bump_same_output")]


def test_a_same_output_bump_whose_latest_generation_is_invalidated_stales_the_dependents(ledger):
    a1 = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a1])
    a2 = cert(ledger, "bg_a", n=1)
    run(ledger, obs("bg_a", "bg_b", bg_a=dict(writer_hashes=wh_of("bg_a", 1), writer_paths=list(wh_of("bg_a", 1)),
                                              semantic_fingerprint=fp_of("bg_a", 9))))        # invalidates a2 (and b)
    cert(ledger, "bg_c", up=[a2])
    ev = sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c", bg_a=dict(writer_hashes=wh_of("bg_a", 1),
                                                                         writer_paths=list(wh_of("bg_a", 1)))))
    assert b in ev.invalidated and a2 in ev.invalidated and [x for x in ev.stale] == ["bg_c|gate|Build.registered@1"]


def test_a_same_output_bump_to_a_non_passing_latest_generation_stales_the_dependents(ledger):
    a1 = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a1])
    cert(ledger, "bg_a", verdict="FAIL")                    # generation 2 FAILS: no fingerprint to equal
    ev = sc.evaluate(raw(ledger), obs("bg_b"))
    assert set(ev.stale) == {b} and ev.stale[b][0]["code"] == "upstream_generation"
    rows = lines(ledger)                                    # even with a (hand-shaped) equal fingerprint on the FAIL
    rows[-1]["semantic_fingerprint"] = fp_of("bg_a")
    write_chained(ledger, rows)
    ev = sc.evaluate(raw(ledger), obs("bg_b"))
    assert ev.stale[b][0]["code"] == "upstream_not_passing" and ev.stale[b][0]["via"] == "generation_bump_same_output"


def test_a_chain_through_a_same_output_bump_is_followed_all_the_way(ledger):
    a1 = cert(ledger, "bg_a")
    b1 = cert(ledger, "bg_b", up=[a1])
    c = cert(ledger, "bg_c", up=[b1])
    cert(ledger, "bg_a", n=1)
    cert(ledger, "bg_b", n=1, up=[f"bg_a|gate|Build.registered@2"])                   # b re-certified on the bumped a
    o = obs("bg_a", "bg_b", "bg_c", bg_a=dict(writer_hashes=wh_of("bg_a", 1), writer_paths=list(wh_of("bg_a", 1))),
            bg_b=dict(writer_hashes=wh_of("bg_b", 1), writer_paths=list(wh_of("bg_b", 1))))
    assert sc.evaluate(raw(ledger), o).stale == {}                                    # c still cites b@1: same output
    o["bg_b"]["semantic_fingerprint"] = fp_of("bg_b", 5)
    assert c in sc.evaluate(raw(ledger), o).stale


# ───────────────────────── a citation cycle has no verdict ─────────────────────────

def test_a_citation_cycle_through_a_same_output_bump_is_a_refusal_not_a_recursion_error(ledger):
    a1 = cert(ledger, "bg_a")
    b1 = cert(ledger, "bg_b", up=[a1])
    a2 = cert(ledger, "bg_a", n=1, up=[b1])             # E5.1 accepts it: b@1 is the latest of its key, and passes
    assert a2.endswith("@2")
    with pytest.raises(sc.StaleCertsError) as ei:
        sc.evaluate(raw(ledger), obs("bg_a", "bg_b", bg_a=dict(writer_hashes=wh_of("bg_a", 1),
                                                                writer_paths=list(wh_of("bg_a", 1)))))
    assert ei.value.code == "upstream_cycle" and not isinstance(ei.value, RecursionError)
    before = raw(ledger)
    with pytest.raises(sc.StaleCertsError):
        run(ledger, obs("bg_a", "bg_b", bg_a=dict(writer_hashes=wh_of("bg_a", 1), writer_paths=list(wh_of("bg_a", 1)))))
    assert raw(ledger) == before


def test_a_very_deep_bump_chain_is_refused_not_a_raw_recursion_error(ledger):
    # resolution recurses only through same-output generation bumps (the latest generation of an upstream lies LATER in
    # the file than the cert that cites an older one). Build k such links: Y_k@1 cites Y_{k-1}@1, whose latest is Y_{k-1}@2,
    # which cites Y_{k-2}@1, whose latest is Y_{k-2}@2, ...
    k = 20
    ids = [cert(ledger, "bg_y0")]
    for i in range(1, k + 1):
        ids.append(cert(ledger, f"bg_y{i}", up=[ids[-1]]))
    for i in range(k - 1, -1, -1):                                              # descending: each cites the @1 below it
        cert(ledger, f"bg_y{i}", n=1, up=([f"bg_y{i - 1}|gate|Build.registered@1"] if i else []))
    names = [f"bg_y{i}" for i in range(k + 1)]
    o = {a: dict(writer_hashes=wh_of(a, 1), writer_paths=list(wh_of(a, 1)), semantic_fingerprint=fp_of(a)) for a in names}
    o[f"bg_y{k}"] = dict(writer_hashes=wh_of(f"bg_y{k}", 0), writer_paths=list(wh_of(f"bg_y{k}", 0)),
                         semantic_fingerprint=fp_of(f"bg_y{k}"))
    assert sc.evaluate(raw(ledger), o).stale == {}                              # fine at the normal recursion limit
    import inspect
    import sys as _sys
    old = _sys.getrecursionlimit()
    _sys.setrecursionlimit(len(inspect.stack()) + 12)
    try:
        with pytest.raises(sc.StaleCertsError) as ei:
            sc.evaluate(raw(ledger), o)
        assert ei.value.code == "upstream_chain_too_deep"
    finally:
        _sys.setrecursionlimit(old)


def test_a_datetime_at_the_calendar_edge_is_a_refusal_not_an_overflow():
    ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    west = dt.timezone(dt.timedelta(hours=-5))
    for v in (dt.datetime.min.replace(tzinfo=ist), dt.datetime.max.replace(tzinfo=west)):
        with pytest.raises(sc.UnreadableInput):
            one(v)
    assert one(dt.datetime(1, 1, 2, tzinfo=ist))                     # one day in from the edge is fine


# ───────────────────────── honest nulls: unreadable input never reads "not stale" ─────────────────────────

def test_a_missing_observation_for_a_certified_asset_raises(ledger):
    chain(ledger)
    with pytest.raises(sc.MissingObservation):
        sc.evaluate(raw(ledger), obs("bg_a", "bg_b", "bg_c"))                       # bg_d absent


def test_a_missing_fingerprint_or_writer_path_raises(ledger):
    cert(ledger, "bg_a")
    with pytest.raises(sc.MissingObservation):
        sc.evaluate(raw(ledger), {"bg_a": dict(writer_hashes=wh_of("bg_a"))})
    with pytest.raises(sc.MissingObservation):
        sc.evaluate(raw(ledger), {"bg_a": dict(semantic_fingerprint=fp_of("bg_a"))})
    with pytest.raises(sc.MissingObservation):
        sc.evaluate(raw(ledger), {"bg_a": dict(writer_hashes={f"{WRITERS_REL}/other.py": H("x")}, semantic_fingerprint=fp_of("bg_a"))})


@pytest.mark.parametrize("bad", [
    dict(semantic_fingerprint="nothex"), dict(semantic_fingerprint=None), dict(semantic_fingerprint="A" * 64),
    dict(semantic_fingerprint=123), dict(writer_hashes={wpath("bg_a"): "short"}), dict(writer_hashes=[wpath("bg_a")]),
])
def test_a_malformed_observation_raises_it_is_never_read_as_unchanged(ledger, bad):
    cert(ledger, "bg_a")
    with pytest.raises(sc.UnreadableInput):
        sc.evaluate(raw(ledger), obs("bg_a", bg_a=bad))


def test_observed_must_be_a_mapping(ledger):
    cert(ledger, "bg_a")
    for bad in (None, [], "x"):
        with pytest.raises(sc.UnreadableInput):
            sc.evaluate(raw(ledger), bad)


def test_a_missing_observation_writes_nothing(ledger):
    chain(ledger)
    before = raw(ledger)
    with pytest.raises(sc.MissingObservation):
        run(ledger, obs("bg_a"))
    assert raw(ledger) == before


# ───────────────────────── ledger shape ─────────────────────────

def test_a_ledger_that_e51_would_refuse_is_refused_here(ledger):
    cert(ledger, "bg_a")
    ledger.write_text(ledger.read_text() + "{not json\n")
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a"))


def test_an_unknown_certificate_kind_or_event_type_raises(ledger):
    cert(ledger, "bg_a")
    rows = lines(ledger)
    write_chained(ledger, rows + [dict(rows[1], kind="mystery", cert_key="bg_a|mystery|x", cert_id="bg_a|mystery|x@1")])
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a"))
    write_chained(ledger, rows + [dict(type="mystery", asset="bg_a", note="x")])
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a"))
    # an event can never carry a cert_key (E5.1 would then read it as a certificate and refuse it as malformed)
    write_chained(ledger, rows + [dict(type="invalidation", asset="bg_a", cert_key="bg_a|invalidation|x")])
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a"))


def test_a_repeated_invalidation_of_one_certificate_is_tolerated_and_counted_once(ledger):
    # two racing runs may both append the same invalidation: the first wins, the walk id is shared, nothing breaks
    a = cert(ledger, "bg_a")
    run(ledger, obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    rows = lines(ledger)
    inv = next(x for x in rows if x.get("type") == "invalidation")
    write_chained(ledger, rows[:-1] + [dict(inv)] + rows[-1:])
    lg = sc.parse_events(raw(ledger))
    assert len(lg.invs) == 2 and list(lg.inv_targets) == [a]
    assert sc.rewalk_counts(raw(ledger)) == {"L0": 1}
    assert sc.evaluate(raw(ledger), obs("bg_a")).invalidated == [a]


def test_a_certificate_citing_a_later_line_or_a_missing_cert_raises(ledger):
    a = cert(ledger, "bg_a")
    b = cert(ledger, "bg_b", up=[a])
    rows = lines(ledger)
    write_chained(ledger, [rows[0], rows[2], rows[1]])         # swap: b before a
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a", "bg_b"))
    write_chained(ledger, [rows[0], rows[2]])                 # a removed
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_b"))


# ═══════════════ (3) invalidation lines and the watermark ═══════════════

def test_invalidate_appends_one_line_per_stale_cert_then_a_watermark_in_the_documented_shape(ledger):
    a, b, c, d = chain(ledger)
    r = run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    rows = lines(ledger)
    inv, wm = rows[-4:-1], rows[-1]
    assert [x["invalidates"] for x in inv] == [a, b, c]                       # file order = dependency order
    x = inv[0]
    assert x["type"] == "invalidation" and x["asset"] == "bg_a" and x["layer"] == "L0"
    assert "cert_key" not in x and "generation" not in x and "verdict" not in x          # an EVENT, not a certificate
    assert x["walk"] == 1 and "epoch" not in x
    assert x["reason"][0]["code"] == "semantic_fingerprint" and x["detected_on"] == NOW
    assert x["detected_by"] == "nikasha_stale_certs.py" and x["record_version"] == 1
    assert [y["seq"] for y in inv] == [5, 6, 7] and wm["seq"] == 8            # E5.1's numbering continues
    assert inv[1]["reason"][0]["code"] == "upstream_stale" and inv[1]["reason"][0]["upstream"] == a
    assert wm["type"] == "watermark" and wm["asset"] == "_ledger" and "cert_key" not in wm
    assert wm["covers_seq"] == 4 and wm["certs_processed"] == 4 and wm["last_cert_id"] == d
    assert wm["commit"] == COMMIT and wm["evaluated_on"] == NOW and wm["record_version"] == 1
    assert r.status == "appended" and r.walk == 1 and sorted(r.invalidated) == sorted([a, b, c])


def test_the_ledger_stays_readable_by_e51_and_certifying_again_still_works(ledger):
    a, b, c, d = chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    by_key = nc.read_ledger(ledger)                                            # E5.1's strict reader accepts E5.5's lines
    assert set(by_key) == {f"{x}|gate|Build.registered" for x in ("bg_a", "bg_b", "bg_c", "bg_d")}   # events: not certs
    recs = nc.read_records(ledger)
    assert [x.get("type") for x in recs].count("invalidation") == 3 and recs[-1]["type"] == "watermark"
    assert cert(ledger, "bg_a", fp=fp_of("bg_a", 1)).endswith("@2")                # E5.1 still appends generation 2


def test_invalidate_is_idempotent_a_second_identical_run_appends_nothing_and_uses_no_walk(ledger):
    chain(ledger)
    o = obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1)))
    run(ledger, o)
    snap = raw(ledger)
    r = run(ledger, o)
    assert r.status == "unchanged" and r.invalidated == [] and raw(ledger) == snap
    assert sc.rewalk_counts(raw(ledger)) == {"L0": 1}


def test_a_clean_ledger_gets_a_watermark_once_and_nothing_after(ledger):
    chain(ledger)
    o = obs("bg_a", "bg_b", "bg_c", "bg_d")
    r1 = run(ledger, o)
    assert r1.status == "appended" and r1.invalidated == [] and r1.walk is None
    assert [x["type"] for x in lines(ledger)[-1:]] == ["watermark"]
    snap = raw(ledger)
    assert run(ledger, o).status == "unchanged" and raw(ledger) == snap


def test_invalidate_is_append_only(ledger):
    chain(ledger)
    before = raw(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    assert raw(ledger).startswith(before) and len(raw(ledger)) > len(before)


def test_recertifying_makes_a_key_current_again_and_current_certificates_excludes_the_invalidated(ledger):
    a, b, c, d = chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    # watermark is current but only D stands
    cur = sc.current_certificates(raw(ledger))
    assert [v["cert_id"] for v in cur.values()] == [d]
    a2 = cert(ledger, "bg_a", fp=fp_of("bg_a", 1))
    assert a2.endswith("@2")
    with pytest.raises(sc.WatermarkBehind):                                    # a new certificate E5.5 has not seen
        sc.current_certificates(raw(ledger))
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    assert sorted(v["cert_id"] for v in sc.current_certificates(raw(ledger)).values()) == sorted([a2, d])


def test_invalidate_waits_for_the_ledger_lock(ledger):
    import fcntl, threading, time
    chain(ledger)
    out = []
    with open(ledger, "rb") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        t = threading.Thread(target=lambda: out.append(run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d")).status))
        t.start()
        time.sleep(0.4)
        blocked = t.is_alive() and not out
        fcntl.flock(held, fcntl.LOCK_UN)
    t.join(5)
    assert blocked and out == ["appended"]


# ───────────────────────── the hash chain (E5.1: prev_sha256 on every record) ─────────────────────────

def raw_lines(p):
    return [x for x in p.read_bytes().split(b"\n") if x.strip()]


def tamper_line(p, idx, **changes):
    """Edit line `idx` IN PLACE without re-chaining (what an attacker or a bug would do)."""
    ls = p.read_bytes().split(b"\n")
    r = json.loads(ls[idx])
    r.update(changes)
    ls[idx] = json.dumps(r, ensure_ascii=False).encode()
    p.write_bytes(b"\n".join(ls))


def test_every_line_invalidate_appends_is_chained_from_the_line_before_it(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    ls = raw_lines(ledger)
    assert len(ls) == 1 + 4 + 3 + 1                               # schema, 4 certs, 3 invalidations, 1 watermark
    for i in range(1, len(ls)):
        assert json.loads(ls[i])["prev_sha256"] == shab(ls[i - 1]), f"line {i} is not chained from line {i - 1}"
        assert json.loads(ls[i])["seq"] == i, f"line {i} is not numbered {i}"
    cert(ledger, "bg_e")                                          # E5.1 appends after E5.5's lines: chain holds on
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", "bg_e"))
    ls = raw_lines(ledger)
    assert all(json.loads(ls[i])["prev_sha256"] == shab(ls[i - 1]) for i in range(1, len(ls)))
    nc.read_ledger(ledger)                                         # and E5.1's own verifier accepts the whole file


def test_an_invalidation_line_with_a_wrong_prev_sha256_is_refused_on_read(ledger):
    a = cert(ledger, "bg_a")
    run(ledger, obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    ls = raw_lines(ledger)
    inv_idx = next(i for i, x in enumerate(ls) if json.loads(x).get("type") == "invalidation")
    r = json.loads(ls[inv_idx])
    r["prev_sha256"] = "0" * 64
    ls[inv_idx] = json.dumps(r, ensure_ascii=False).encode()
    ledger.write_bytes(b"\n".join(ls) + b"\n")
    for call in (lambda: sc.evaluate(raw(ledger), obs("bg_a")), lambda: sc.watermark_ok(raw(ledger)),
                 lambda: sc.current_certificates(raw(ledger)), lambda: sc.rewalk_counts(raw(ledger))):
        with pytest.raises(sc.LedgerShapeError) as ei:
            call()
        assert ei.value.code == "bad_ledger" and "chain" in ei.value.message
    with pytest.raises(nc.CertificationRefused):                   # E5.1's reader refuses the same ledger
        nc.read_ledger(ledger)


def test_a_hand_appended_unchained_invalidation_line_is_refused(ledger):
    a = cert(ledger, "bg_a")
    bad = dict(type="invalidation", asset="bg_a", layer="L0", invalidates=a, reason=[dict(code="writer_hash")], walk=1,
               detected_by="x", detected_on=NOW, record_version=1)
    head = b"\n".join(raw_lines(ledger)[:2]) + b"\n"
    good_seq = json.loads(raw_lines(ledger)[1])["seq"] + 1
    for extra in ({}, {"seq": good_seq}, {"seq": good_seq, "prev_sha256": "f" * 64}, {"prev_sha256": shab(raw_lines(ledger)[1])},
                  {"seq": good_seq + 5, "prev_sha256": shab(raw_lines(ledger)[1])}):
        ledger.write_bytes(head + json.dumps(dict(bad, **extra)).encode() + b"\n")
        with pytest.raises(sc.LedgerShapeError):
            sc.evaluate(raw(ledger), obs("bg_a"))
    ok = dict(bad, seq=good_seq, prev_sha256=shab(raw_lines(ledger)[1]))                     # control: correctly chained
    ledger.write_bytes(head + json.dumps(ok).encode() + b"\n")
    assert sc.evaluate(raw(ledger), obs("bg_a")).invalidated == [a]


def test_a_tampered_earlier_record_makes_current_certificates_raise(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert len(sc.current_certificates(raw(ledger))) == 4
    tamper_line(ledger, 1, verdict="PASS", semantic_fingerprint="e" * 64)         # edit an earlier certificate in place
    with pytest.raises(sc.LedgerShapeError) as ei:
        sc.current_certificates(raw(ledger))
    assert ei.value.code == "bad_ledger"
    with pytest.raises(sc.LedgerShapeError):
        sc.current_certificates(raw(ledger), require_watermark=False)
    with pytest.raises(sc.LedgerShapeError):
        sc.watermark_ok(raw(ledger))


def test_a_deleted_or_reordered_line_breaks_the_chain(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    ls = raw_lines(ledger)
    ledger.write_bytes(b"\n".join(ls[:2] + ls[3:]) + b"\n")                       # line 2 deleted
    with pytest.raises(sc.LedgerShapeError):
        sc.current_certificates(raw(ledger))
    ledger.write_bytes(b"\n".join([ls[0], ls[2], ls[1]] + ls[3:]) + b"\n")        # lines 1 and 2 swapped
    with pytest.raises(sc.LedgerShapeError):
        sc.current_certificates(raw(ledger))


def test_invalidate_refuses_a_ledger_whose_chain_is_broken_and_writes_nothing(ledger):
    chain(ledger)
    tamper_line(ledger, 1, verified_by="someone-else")
    before = raw(ledger)
    with pytest.raises(sc.LedgerShapeError):
        run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert raw(ledger) == before


def test_a_torn_last_line_is_refused_with_its_code_and_never_extended(ledger):
    chain(ledger)
    ledger.write_bytes(raw(ledger) + b'{"asset": "bg_z", "kind": "gate"')           # a partial write, no newline
    before = raw(ledger)
    with pytest.raises(sc.LedgerShapeError) as ei:
        sc.evaluate(before, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert ei.value.code == "torn_ledger"
    with pytest.raises(sc.LedgerShapeError):
        run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert raw(ledger) == before


def test_a_valid_last_line_with_no_newline_is_extended_on_a_new_line_and_still_chains(ledger):
    chain(ledger)
    ledger.write_bytes(raw(ledger).rstrip(b"\n"))
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    ls = raw_lines(ledger)
    assert json.loads(ls[-1])["type"] == "watermark" and json.loads(ls[-1])["prev_sha256"] == shab(ls[-2])
    nc.read_ledger(ledger)


def test_a_symlinked_ledger_is_refused_and_not_followed(ledger, tmp_path):
    chain(ledger)
    link = tmp_path / "link.jsonl"
    link.symlink_to(ledger)
    before = raw(ledger)
    with pytest.raises(sc.UnreadableInput) as ei:
        run(link, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert ei.value.code == "bad_ledger_path" and raw(ledger) == before


def test_a_committed_ledger_with_a_broken_chain_raises_at_the_ref(tmp_path):
    repo = tmp_path / "r"
    (repo / "ctl").mkdir(parents=True)
    led = repo / "ctl" / "asset_certs.jsonl"
    led.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    _git(repo, "init", "-q")
    cert(led, "bg_a")
    cert(led, "bg_b")
    run(led, obs("bg_a", "bg_b"))
    tamper_line(led, 1, verified_by="x")
    _git(repo, "add", "ctl/asset_certs.jsonl")
    _git(repo, "commit", "-q", "-m", "tampered")
    with pytest.raises(sc.LedgerShapeError):
        sc.watermark_ok_at_ref("HEAD", repo, "ctl/asset_certs.jsonl")


# ───────────────────────── E5.1's new record fields: read, never dropped, flagged ─────────────────────────

def test_a_record_citing_a_staged_census_is_current_and_flagged_not_dropped(ledger):
    a = cert(ledger, "bg_a")
    rec = lines(ledger)[1]
    assert rec["evidence"]["census_git"] == "staged" and rec["evidence"]["census_tool_commit"] == TOOL_COMMIT
    assert rec["cross_checked"] is True and "registry_binding" not in rec
    run(ledger, obs("bg_a"))
    cur = sc.current_certificates(raw(ledger))
    assert list(cur) == ["bg_a|gate|Build.registered"] and cur["bg_a|gate|Build.registered"]["cert_id"] == a
    assert cur.flags == {"bg_a|gate|Build.registered": ["census_not_committed"]}
    assert sc.evaluate(raw(ledger), obs("bg_a")).flags == {a: ["census_not_committed"]}


def test_a_record_citing_a_committed_census_carries_no_census_flag(ledger):
    cf = census_file("bg_a", "Build.registered", "PASS")
    git(ENV.repo, "commit", "-q", "-m", "census", date=COMMIT_DATE)                       # now at HEAD, not just staged
    cert(ledger, "bg_a", census_path=cf)
    assert lines(ledger)[1]["evidence"]["census_git"] == "committed"
    run(ledger, obs("bg_a"))
    cur = sc.current_certificates(raw(ledger))
    assert list(cur) == ["bg_a|gate|Build.registered"] and cur.flags == {}


def test_every_flag_on_a_hand_shaped_record_is_reported_and_none_drops_the_certificate(ledger):
    cert(ledger, "bg_a")
    rows = lines(ledger)
    rows[1].update(writer_hashes_verified=False, transitive_only=True, cross_checked=False, inconclusive=True,
                   basis="declaration")
    write_chained(ledger, rows)
    run(ledger, obs("bg_a"))
    cur = sc.current_certificates(raw(ledger))
    assert len(cur) == 1
    assert cur.flags["bg_a|gate|Build.registered"] == ["census_not_committed", "writer_hashes_unverified",
                                                       "not_cross_checked", "transitive_only", "inconclusive",
                                                       "basis_declaration"]


def test_certificate_flags_on_a_clean_record_and_on_an_addition():
    clean = dict(kind="gate", evidence=dict(census_git="committed"), writer_hashes=wh_of("bg_a"),
                 writer_hashes_verified=True, cross_checked=True, transitive_only=False, inconclusive=False, basis=None)
    assert sc.certificate_flags(clean) == []
    add = dict(kind="addition", evidence={}, writer_hashes={}, writer_hashes_verified=False,
               cross_checked=False, transitive_only=False, inconclusive=False, basis=None)
    assert sc.certificate_flags(add) == []                                   # additions are not census cross-checked


def test_staleness_detection_is_unchanged_by_the_new_fields(ledger):
    # a record whose writer hashes were NOT verified is still compared (and flagged), not exempted
    a = cert(ledger, "bg_a")
    rows = lines(ledger)
    rows[1]["writer_hashes_verified"] = False
    write_chained(ledger, rows)
    ev = sc.evaluate(raw(ledger), obs("bg_a", bg_a=dict(writer_hashes=wh_of("bg_a", 1))))
    assert set(ev.stale) == {a} and ev.stale[a][0]["code"] == "writer_hash"


# ───────────────────────── the watermark ─────────────────────────

def test_a_ledger_with_no_watermark_is_not_ok(ledger):
    chain(ledger)
    assert sc.watermark_ok(raw(ledger)) is False
    st = sc.watermark_status(raw(ledger))
    assert st["ok"] is False and st["watermark"] is None and st["unevaluated"] == 4


def test_a_schema_only_ledger_has_nothing_unevaluated_but_still_needs_a_watermark(ledger):
    assert sc.watermark_ok(raw(ledger)) is False
    run(ledger, {})
    assert sc.watermark_ok(raw(ledger)) is True and lines(ledger)[-1]["certs_processed"] == 0 and lines(ledger)[-1]["covers_seq"] == 0


def test_the_watermark_is_ok_exactly_when_no_certificate_follows_it(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert sc.watermark_ok(raw(ledger)) is True
    cert(ledger, "bg_e")
    assert sc.watermark_ok(raw(ledger)) is False
    assert sc.watermark_status(raw(ledger))["unevaluated"] == 1
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", "bg_e"))
    assert sc.watermark_ok(raw(ledger)) is True
    assert [x["covers_seq"] for x in lines(ledger) if x.get("type") == "watermark"] == [4, 6]


def test_a_watermark_that_miscounts_the_certificates_it_covers_is_a_lie_and_raises(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    good = lines(ledger)
    own_seq = good[-1]["seq"]
    for patch in (dict(certs_processed=99), dict(covers_seq=own_seq), dict(last_cert_id="bg_zzz|gate|Build.registered@1"), dict(last_cert_id=None),
                  dict(covers_seq=3), dict(covers_seq=0), dict(covers_seq=-1), dict(covers_seq=999),
                  dict(covers_seq="4"), dict(commit=""), dict(asset="bg_a")):
        rows = [dict(x) for x in good]
        rows[-1].update(patch)
        write_chained(ledger, rows)
        with pytest.raises(sc.LedgerShapeError):
            sc.watermark_ok(raw(ledger))
    write_chained(ledger, good)
    assert sc.watermark_ok(raw(ledger)) is True


def test_two_racing_runs_cannot_brick_the_ledger_a_late_smaller_watermark_is_harmless(ledger):
    # run A reads at head 3; a certificate lands (seq 4); run B reads at head 4 and appends a watermark covering 4;
    # run A then appends ITS watermark, which covers only 3. E5.1 accepts that line; this module must too.
    a, b, c = cert(ledger, "bg_a"), cert(ledger, "bg_b"), cert(ledger, "bg_c")
    head_a, _ = nc.chain_head(raw(ledger))
    assert head_a == 3
    d = cert(ledger, "bg_d")                                                        # lands after A's read
    rb = run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))                           # B: covers seq 4 (watermark seq 5)
    assert rb.watermark["covers_seq"] == 4
    late = dict(type="watermark", asset="_ledger", covers_seq=head_a, certs_processed=3, last_cert_id=c, commit=COMMIT,
                evaluated_on=NOW, record_version=1)
    assert nc.append_records(ledger, [late]) == 1                                   # A's append (E5.1 accepts it)
    ws = [x for x in lines(ledger) if x.get("type") == "watermark"]
    assert [w["covers_seq"] for w in ws] == [4, 3]
    # the ledger is still fully readable and the watermark reads as what it is: 4 certificates covered
    assert sc.watermark_ok(raw(ledger)) is True
    st = sc.watermark_status(raw(ledger))
    assert st["ok"] is True and st["watermark"]["covers_seq"] == 4 and st["unevaluated"] == 0
    assert sorted(v["cert_id"] for v in sc.current_certificates(raw(ledger)).values()) == sorted([a, b, c, d])
    snap = raw(ledger)
    assert run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d")).status == "unchanged" and raw(ledger) == snap
    assert sc.read_ledger_file(ledger).last_seq == 6
    # and later work goes on normally
    e = cert(ledger, "bg_e")
    assert sc.watermark_ok(raw(ledger)) is False
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", "bg_e"))
    assert sc.watermark_ok(raw(ledger)) is True and e in [x["cert_id"] for x in sc.current_certificates(raw(ledger)).values()]


def test_a_late_smaller_watermark_never_takes_coverage_away(ledger):
    cert(ledger, "bg_a")
    cert(ledger, "bg_b")
    run(ledger, obs("bg_a", "bg_b"))                                                # covers 2
    first = lines(ledger)[-1]
    nc.append_records(ledger, [dict(type="watermark", asset="_ledger", covers_seq=1, certs_processed=1,
                                    last_cert_id=lines(ledger)[1]["cert_id"], commit=COMMIT, evaluated_on=NOW,
                                    record_version=1)])
    assert sc.watermark_status(raw(ledger))["ok"] is True
    assert sc.watermark_status(raw(ledger))["watermark"]["seq"] == first["seq"]


def test_every_watermark_is_still_judged_on_its_own_truth_even_when_late(ledger):
    cert(ledger, "bg_a")
    cert(ledger, "bg_b")
    run(ledger, obs("bg_a", "bg_b"))
    for bad in (dict(covers_seq=1, certs_processed=2, last_cert_id=lines(ledger)[2]["cert_id"]),     # miscounts its own range
                dict(covers_seq=1, certs_processed=1, last_cert_id="bg_zzz|gate|Build.registered@1"),
                dict(covers_seq=999, certs_processed=2, last_cert_id=lines(ledger)[2]["cert_id"])):
        rows = lines(ledger) + [dict(type="watermark", asset="_ledger", commit=COMMIT, evaluated_on=NOW, record_version=1,
                                     **bad)]
        write_chained(ledger, [dict(r) for r in rows])
        with pytest.raises(sc.LedgerShapeError):
            sc.watermark_ok(raw(ledger))
        write_chained(ledger, lines(ledger)[:-1])


def test_a_certificate_appended_between_the_read_and_the_append_reads_as_behind_never_as_evaluated(ledger):
    # E5.5 reads (shared lock) and appends (exclusive lock) as two E5.1 calls; a certificate landing in between must
    # not be covered by the watermark. Simulate: the watermark covers seq 1, a certificate sits at seq 2 before it.
    cert(ledger, "bg_a")
    cert(ledger, "bg_b")
    rows = lines(ledger)
    wm = dict(type="watermark", asset="_ledger", covers_seq=1, certs_processed=1, last_cert_id=rows[1]["cert_id"],
              commit=COMMIT, evaluated_on=NOW, record_version=1)
    write_chained(ledger, rows + [wm])
    st = sc.watermark_status(raw(ledger))
    assert st["ok"] is False and st["unevaluated"] == 1
    with pytest.raises(sc.WatermarkBehind):
        sc.current_certificates(raw(ledger))


def test_current_certificates_refuses_a_ledger_behind_its_watermark_unless_told_otherwise(ledger):
    chain(ledger)
    with pytest.raises(sc.WatermarkBehind) as ei:
        sc.current_certificates(raw(ledger))
    assert ei.value.code == "watermark_behind"
    assert len(sc.current_certificates(raw(ledger), require_watermark=False)) == 4


def test_invalidation_lines_for_unknown_or_later_certs_raise(ledger):
    a = cert(ledger, "bg_a")
    run(ledger, obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))
    rows = lines(ledger)
    bad = [dict(x, invalidates="bg_nobody|gate|Build.registered@1") if x.get("type") == "invalidation" else x for x in rows]
    write_chained(ledger, bad)
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a"))
    inv = next(x for x in rows if x.get("type") == "invalidation")
    reordered = [rows[0], inv] + [x for x in rows[1:] if x is not inv]
    write_chained(ledger, reordered)
    with pytest.raises(sc.LedgerShapeError):
        sc.evaluate(raw(ledger), obs("bg_a"))


def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True,
                          env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                               "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
                               "HOME": str(repo)}).stdout


def test_watermark_ok_at_ref_reads_the_committed_ledger_not_the_working_tree(tmp_path):
    repo = tmp_path / "r"
    (repo / "ctl").mkdir(parents=True)
    led = repo / "ctl" / "asset_certs.jsonl"
    led.write_text(json.dumps({"asset": "_schema", "_doc": "t"}) + "\n")
    _git(repo, "init", "-q")
    cert(led, "bg_a")
    run(led, obs("bg_a"))
    _git(repo, "add", "ctl/asset_certs.jsonl")
    _git(repo, "commit", "-q", "-m", "ledger evaluated")
    good = _git(repo, "rev-parse", "HEAD").strip()
    cert(led, "bg_b")                                                         # dirty working tree: a cert E5.5 has not seen
    assert sc.watermark_ok(raw(led)) is False
    assert sc.watermark_ok_at_ref(good, repo, "ctl/asset_certs.jsonl") is True      # the committed ref is what counts
    _git(repo, "add", "ctl/asset_certs.jsonl")
    _git(repo, "commit", "-q", "-m", "cert without evaluation")
    assert sc.watermark_ok_at_ref("HEAD", repo, "ctl/asset_certs.jsonl") is False
    assert sc.watermark_ok_at_ref(good, repo, "ctl/asset_certs.jsonl") is True


def test_a_hostile_ref_or_path_is_refused_before_git_is_ever_run(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("git must not be invoked for an invalid ref/path")
    monkeypatch.setattr(sc.subprocess, "run", boom)
    for ref, path in (("--output=/tmp/x", "a/b"), ("-x", "a/b"), ("", "a/b"), ("HEAD", "/etc/passwd"), ("HEAD", "../x"),
                      ("HEAD", "a//b"), ("HEAD", "")):
        with pytest.raises(sc.UnreadableInput):
            sc.read_ledger_at_ref(ref, tmp_path, path)


def test_a_ref_that_cannot_be_read_raises_never_ok(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q")
    with pytest.raises(sc.UnreadableInput):
        sc.watermark_ok_at_ref("HEAD", repo, "ctl/asset_certs.jsonl")
    with pytest.raises(sc.UnreadableInput):
        sc.watermark_ok_at_ref("--output=/tmp/x", repo, "ctl/asset_certs.jsonl")              # option-shaped ref refused
    with pytest.raises(sc.UnreadableInput):
        sc.watermark_ok_at_ref("HEAD", repo, "/etc/passwd")
    with pytest.raises(sc.UnreadableInput):
        sc.watermark_ok_at_ref("HEAD", repo, "../x")


# ═══════════════ (4) bounded re-walks: counted per layer over the whole ledger ═══════════════

def churn(ledger, n, asset="bg_a"):
    """Recertify `asset` at fingerprint n-1, then change the world to n: the next walk finds it stale."""
    return cert(ledger, asset, fp=fp_of(asset, n - 1), n=0)


def walk_once(ledger, n, asset="bg_a", **kw):
    return run(ledger, obs(asset, **{asset: dict(semantic_fingerprint=fp_of(asset, n))}), **kw)


def three_walks_setup(ledger):
    cert(ledger, "bg_a")
    assert walk_once(ledger, 1).walk == 1
    churn(ledger, 2)
    assert walk_once(ledger, 2).walk == 2
    churn(ledger, 3)


def test_two_invalidating_walks_per_layer_are_allowed_and_the_third_is_refused_with_nothing_written(ledger):
    three_walks_setup(ledger)
    before = raw(ledger)
    with pytest.raises(sc.RewalkLimitExceeded) as ei:
        walk_once(ledger, 3)
    e = ei.value
    assert e.code == "rewalk_limit" and e.layer == "L0" and e.walks == 2 and e.limit == 2
    assert [x[0] for x in e.stale.items()] == ["bg_a|gate|Build.registered@3"]
    assert "new-epoch" in e.message
    assert raw(ledger) == before, "a refused third walk must not write an invalidation OR a watermark"
    assert sc.watermark_ok(raw(ledger)) is False                     # the ledger stays unserviceable until SS reviews


def test_there_is_no_free_argument_that_raises_or_resets_the_limit(ledger):
    three_walks_setup(ledger)
    before = raw(ledger)
    for kw_ in (dict(epoch="E2"), dict(max_rewalks=99), dict(epoch="E2", max_rewalks=3)):
        with pytest.raises(TypeError):
            walk_once(ledger, 3, **kw_)
    assert sc.MAX_REWALKS == 2
    with pytest.raises(sc.RewalkLimitExceeded):
        walk_once(ledger, 3)
    assert raw(ledger) == before
    import inspect
    assert set(inspect.signature(sc.invalidate).parameters) == {"ledger_path", "observed", "commit", "registry", "now",
                                                                "observed_at_seq"}


def test_counts_are_per_layer_over_the_whole_ledger(ledger):
    cert(ledger, "bg_a")
    walk_once(ledger, 1)
    churn(ledger, 2)
    walk_once(ledger, 2)
    cert(ledger, "bo_x")                                              # a different layer is not capped by L0's walks
    r = run(ledger, obs("bg_a", "bo_x", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 2)),
                        bo_x=dict(semantic_fingerprint=fp_of("bo_x", 1))))
    assert r.invalidated == ["bo_x|gate|Build.registered@1"] and r.walk == 3
    assert sc.rewalk_counts(raw(ledger)) == {"L0": 2, "L2": 1}


def test_a_walk_that_touches_a_capped_layer_through_propagation_is_also_refused(ledger):
    cert(ledger, "bg_a")
    walk_once(ledger, 1)
    churn(ledger, 2)
    walk_once(ledger, 2)
    a3 = churn(ledger, 3)
    b = cert(ledger, "bo_b", up=[a3])                                 # an L2 dependent on an L0 asset
    with pytest.raises(sc.RewalkLimitExceeded) as ei:
        run(ledger, obs("bg_a", "bo_b", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 3))))
    assert ei.value.layer == "L0" and set(ei.value.stale) == {a3, b}


def test_a_walk_that_invalidates_nothing_does_not_count(ledger):
    cert(ledger, "bg_a")
    for _ in range(5):
        run(ledger, obs("bg_a"))
    assert sc.rewalk_counts(raw(ledger)) == {}


def test_walk_ids_run_over_the_whole_ledger_not_over_the_number_of_lines(ledger):
    chain(ledger)
    r1 = run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))   # 3 lines
    assert r1.walk == 1 and len(r1.invalidated) == 3
    cert(ledger, "bg_d", fp=fp_of("bg_d", 0), n=1)
    r2 = run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d", bg_d=dict(writer_hashes=wh_of("bg_d", 2),
                                                                    writer_paths=list(wh_of("bg_d", 2)))))
    assert r2.walk == 2 and sc.rewalk_counts(raw(ledger)) == {"L0": 2}


def test_commit_is_required_text(ledger):
    cert(ledger, "bg_a")
    for bad in ("", "  ", None, 3):
        with pytest.raises(sc.StaleCertsError):
            run(ledger, obs("bg_a"), commit=bad)
    assert len(lines(ledger)) == 2


def test_a_missing_ledger_is_refused_and_not_created(tmp_path):
    with pytest.raises(sc.UnreadableInput) as ei:
        run(tmp_path / "nope.jsonl", {})
    assert ei.value.code == "ledger_missing" and not (tmp_path / "nope.jsonl").exists()


# ───────────────────────── new-epoch: the only reset, an explicit event ─────────────────────────

def test_new_epoch_appends_an_epoch_reset_event_and_restarts_only_that_layer(ledger):
    three_walks_setup(ledger)
    cert(ledger, "bo_x")
    run(ledger, obs("bg_a", "bo_x", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 2)),
                    bo_x=dict(semantic_fingerprint=fp_of("bo_x", 1))))
    assert sc.rewalk_counts(raw(ledger)) == {"L0": 2, "L2": 1}
    ev = sc.new_epoch(ledger, "L0", "N-28", now=NOW)
    assert ev == dict(type="epoch_reset", asset="_ledger", layer="L0", decision="N-28", reset_on=NOW, record_version=1)
    last = lines(ledger)[-1]
    assert last["type"] == "epoch_reset" and "cert_key" not in last and last["seq"] == len(lines(ledger)) - 1
    assert sc.rewalk_counts(raw(ledger)) == {"L2": 1}                          # L0 restarted, L2 untouched
    nc.read_ledger(ledger)                                                      # E5.1's strict reader accepts it
    r = walk_once(ledger, 3)                                                    # the third walk now goes through
    assert r.invalidated == ["bg_a|gate|Build.registered@3"] and sc.rewalk_counts(raw(ledger)) == {"L0": 1, "L2": 1}


def test_after_a_reset_the_limit_applies_again_to_the_new_count(ledger):
    three_walks_setup(ledger)
    sc.new_epoch(ledger, "L0", "N-28")
    walk_once(ledger, 3)
    churn(ledger, 4)
    walk_once(ledger, 4)
    churn(ledger, 5)
    before = raw(ledger)
    with pytest.raises(sc.RewalkLimitExceeded):
        walk_once(ledger, 5)
    assert raw(ledger) == before and sc.rewalk_counts(raw(ledger)) == {"L0": 2}


def two_layers_at_the_edge(ledger):
    three_walks_setup(ledger)                                         # L0: two walks, a third pending
    cert(ledger, "bo_x")
    run(ledger, obs("bg_a", "bo_x", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 2)),
                    bo_x=dict(semantic_fingerprint=fp_of("bo_x", 1))))            # L2: one walk


def test_a_reset_for_one_layer_never_resets_another(ledger):
    two_layers_at_the_edge(ledger)
    sc.new_epoch(ledger, "L2", "N-28")
    with pytest.raises(sc.RewalkLimitExceeded):
        walk_once(ledger, 3)


def test_a_reset_only_restarts_walks_before_it_not_after(ledger):
    two_layers_at_the_edge(ledger)
    sc.new_epoch(ledger, "L0", "N-28")
    walk_once(ledger, 3)
    sc.new_epoch(ledger, "L2", "N-29")                                           # a later reset of ANOTHER layer
    assert sc.rewalk_counts(raw(ledger)) == {"L0": 1}


def test_new_epoch_for_a_layer_with_no_walks_is_refused_and_writes_nothing(ledger):
    cert(ledger, "bg_a")
    for layer in ("L0", "L3"):                                                   # never walked
        before = raw(ledger)
        with pytest.raises(sc.StaleCertsError) as ei:
            sc.new_epoch(ledger, layer, "N-28")
        assert ei.value.code == "no_walks_to_reset" and raw(ledger) == before
    three_walks_setup(ledger)
    sc.new_epoch(ledger, "L0", "N-28")                                           # reset once...
    with pytest.raises(sc.StaleCertsError) as ei:
        sc.new_epoch(ledger, "L0", "N-29")                                       # ...nothing left to reset
    assert ei.value.code == "no_walks_to_reset"


def test_new_epoch_needs_a_tz_aware_timestamp(ledger):
    three_walks_setup(ledger)
    before = raw(ledger)
    for bad in ("2026-10-01T10:00:00", "yesterday", 5):
        with pytest.raises(sc.StaleCertsError) as ei:
            sc.new_epoch(ledger, "L0", "N-28", now=bad)
        assert ei.value.code == "bad_timestamp" and raw(ledger) == before


@pytest.mark.parametrize("layer,decision", [("L9", "N-28"), ("l0", "N-28"), ("", "N-28"), (None, "N-28"), ("L0", ""),
                                            ("L0", "28"), ("L0", "N-"), ("L0", "n-28"), ("L0", None), ("L0", "N-28 x"),
                                            ("L0", "N-28\n{}"), ("L0", "N-" + "9" * 40)])
def test_new_epoch_refuses_a_bad_layer_or_decision_id_and_writes_nothing(ledger, layer, decision):
    cert(ledger, "bg_a")
    before = raw(ledger)
    with pytest.raises(sc.StaleCertsError):
        sc.new_epoch(ledger, layer, decision)
    assert raw(ledger) == before


def test_new_epoch_on_a_missing_ledger_is_refused(tmp_path):
    with pytest.raises(sc.UnreadableInput):
        sc.new_epoch(tmp_path / "nope.jsonl", "L0", "N-28")
    assert not (tmp_path / "nope.jsonl").exists()


def test_a_malformed_epoch_reset_in_the_ledger_is_refused_on_read(ledger):
    cert(ledger, "bg_a")
    rows = lines(ledger)
    ok = dict(type="epoch_reset", asset="_ledger", layer="L0", decision="N-28", reset_on=NOW, record_version=1)
    write_chained(ledger, rows + [ok])
    assert sc.rewalk_counts(raw(ledger)) == {}                                    # control: a well-formed one reads
    for bad in (dict(ok, layer="L9"), dict(ok, decision="whatever"), dict(ok, asset="bg_a"),
                {k: v for k, v in ok.items() if k != "layer"},
                {k: v for k, v in ok.items() if k != "reset_on"},
                dict(ok, reset_on="2026-10-01T10:00:00"), dict(ok, reset_on="soon"), dict(ok, reset_on=5),
                dict(ok, reset_on=None)):
        write_chained(ledger, rows + [bad])
        with pytest.raises(sc.LedgerShapeError):
            sc.rewalk_counts(raw(ledger))


# ───────────────────────── observed_at_seq: what one run claims to have covered ─────────────────────────

def test_observed_at_seq_caps_what_is_evaluated_and_what_the_watermark_covers(ledger):
    cert(ledger, "bg_a")
    head, _ = nc.chain_head(raw(ledger))
    cert(ledger, "bg_b")                                    # certified AFTER the observations were taken
    r = run(ledger, obs("bg_a"), observed_at_seq=head)       # bg_b is not observed: it must not be judged, nor required
    assert r.status == "appended" and r.watermark["covers_seq"] == head and r.watermark["certs_processed"] == 1
    st = sc.watermark_status(raw(ledger))
    assert st["ok"] is False and st["unevaluated"] == 1       # bg_b reads as behind, not as evaluated
    with pytest.raises(sc.WatermarkBehind):
        sc.current_certificates(raw(ledger))


def test_without_observed_at_seq_the_head_as_read_is_used(ledger):
    chain(ledger)
    head, _ = nc.chain_head(raw(ledger))
    r = run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    assert r.watermark["covers_seq"] == head


@pytest.mark.parametrize("bad", [-1, 99, True, "3", 1.5])
def test_observed_at_seq_outside_the_ledger_is_refused_and_writes_nothing(ledger, bad):
    chain(ledger)
    before = raw(ledger)
    with pytest.raises(sc.StaleCertsError) as ei:
        run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"), observed_at_seq=bad)
    assert ei.value.code == "bad_observed_at_seq" and raw(ledger) == before


def test_observed_at_seq_behind_the_existing_watermark_is_refused(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    before = raw(ledger)
    with pytest.raises(sc.StaleCertsError) as ei:
        run(ledger, obs("bg_a"), observed_at_seq=1)
    assert ei.value.code == "bad_observed_at_seq" and raw(ledger) == before


def test_a_capped_run_does_not_judge_certificates_written_after_the_cap(ledger):
    cert(ledger, "bg_a")
    head, _ = nc.chain_head(raw(ledger))
    cert(ledger, "bg_b", fp=fp_of("bg_b", 3))               # its premises do not match the (older) observations
    r = run(ledger, obs("bg_a"), observed_at_seq=head)       # nothing about bg_b can be concluded from them
    assert r.invalidated == [] and [x for x in lines(ledger) if x.get("type") == "invalidation"] == []
    run(ledger, obs("bg_a", "bg_b", bg_b=dict(semantic_fingerprint=fp_of("bg_b", 3))))
    assert sc.watermark_ok(raw(ledger)) is True


def test_an_invalidation_appended_after_the_cap_is_not_appended_again(ledger):
    # run 1 invalidates a stale certificate; a second run whose observations were taken BEFORE run 1's lines (cap below
    # them) must still see that invalidation, not mint a duplicate and burn a walk
    cert(ledger, "bg_a")
    head, _ = nc.chain_head(raw(ledger))
    o = obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1)))
    assert run(ledger, o).walk == 1
    snap = raw(ledger)
    r = run(ledger, o, observed_at_seq=head)
    assert r.status == "unchanged" and raw(ledger) == snap
    assert sc.rewalk_counts(raw(ledger)) == {"L0": 1}


def test_a_capped_run_is_unchanged_when_the_watermark_already_covers_the_cap(ledger):
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    head, _ = nc.chain_head(raw(ledger))
    snap = raw(ledger)
    assert run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"), observed_at_seq=head).status == "unchanged"
    assert raw(ledger) == snap


# ───────────────────────── CLI ─────────────────────────

SCRIPT = HERE.parent / "nikasha_stale_certs.py"


def cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_cli_invalidate_then_watermark_ok(ledger, tmp_path):
    a = cert(ledger, "bg_a")
    of = tmp_path / "obs.json"
    of.write_text(json.dumps(dict(assets=obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 1))))))
    p = cli("watermark-ok", "--ledger", str(ledger))
    assert p.returncode == 2
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["status"] == "appended" and out["invalidated"] == [a] and out["walk"] == 1
    assert cli("watermark-ok", "--ledger", str(ledger)).returncode == 0


def test_cli_has_no_epoch_or_max_rewalks_flag(ledger, tmp_path):
    cert(ledger, "bg_a")
    of = tmp_path / "obs.json"
    of.write_text(json.dumps(dict(assets=obs("bg_a"))))
    before = raw(ledger)
    for flag in (("--epoch", "E2"), ("--max-rewalks", "99")):
        p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT, *flag)
        assert p.returncode == 2 and "unrecognized arguments" in p.stderr
    assert raw(ledger) == before


def test_cli_rewalk_limit_exits_3_names_the_layer_and_new_epoch_is_the_way_out(ledger, tmp_path):
    cert(ledger, "bg_a")
    for n in (1, 2):
        walk_once(ledger, n)
        churn(ledger, n + 1)
    of = tmp_path / "obs.json"
    of.write_text(json.dumps(dict(assets=obs("bg_a", bg_a=dict(semantic_fingerprint=fp_of("bg_a", 3))))))
    before = raw(ledger)
    args = ("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT)
    p = cli(*args)
    assert p.returncode == 3 and "rewalk_limit" in p.stderr and "L0" in p.stderr and "new-epoch" in p.stderr
    assert raw(ledger) == before
    q = cli("new-epoch", "--ledger", str(ledger), "--layer", "L0", "--decision", "N-28")
    assert q.returncode == 0, q.stderr
    assert json.loads(q.stdout) == dict(status="appended", layer="L0", decision="N-28")
    assert cli(*args).returncode == 0


def test_cli_new_epoch_refuses_a_bad_decision(ledger):
    cert(ledger, "bg_a")
    before = raw(ledger)
    p = cli("new-epoch", "--ledger", str(ledger), "--layer", "L0", "--decision", "because")
    assert p.returncode == 2 and "bad_decision" in p.stderr and raw(ledger) == before
    p = cli("new-epoch", "--ledger", str(ledger), "--layer", "L8", "--decision", "N-28")
    assert p.returncode == 2 and "bad_layer" in p.stderr and raw(ledger) == before


def test_cli_new_epoch_for_a_layer_with_no_walks_is_refused(ledger):
    cert(ledger, "bg_a")
    before = raw(ledger)
    p = cli("new-epoch", "--ledger", str(ledger), "--layer", "L0", "--decision", "N-28")
    assert p.returncode == 2 and "no_walks_to_reset" in p.stderr and raw(ledger) == before


def test_cli_missing_observation_exits_2_and_writes_nothing(ledger, tmp_path):
    cert(ledger, "bg_a")
    of = tmp_path / "obs.json"
    of.write_text(json.dumps(dict(assets={})))
    before = raw(ledger)
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT)
    assert p.returncode == 2 and "missing_observation" in p.stderr and raw(ledger) == before


def test_cli_registry_needs_registry_assets(ledger, tmp_path):
    a = cert(ledger, "bg_a")
    of = tmp_path / "obs.json"
    of.write_text(json.dumps(dict(assets=obs("bg_a"), registry=dict(revision=ac.REGISTRY_REVISION + 1,
                                                                     fingerprint=ac.registry_fingerprint()))))
    before = raw(ledger)
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT)
    assert p.returncode == 2 and "unreadable_input" in p.stderr and raw(ledger) == before
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT, "--registry-assets", "bg_a")
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)["invalidated"] == [a]
    # --registry-assets without a registry in the file is refused
    of.write_text(json.dumps(dict(assets=obs("bg_a"))))
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT, "--registry-assets", "bg_a")
    assert p.returncode == 2 and "bad_registry" in p.stderr


def test_cli_observed_at_seq_is_honoured(ledger, tmp_path):
    cert(ledger, "bg_a")
    head, _ = nc.chain_head(raw(ledger))
    cert(ledger, "bg_b")
    of = tmp_path / "obs.json"
    of.write_text(json.dumps(dict(assets=obs("bg_a"))))
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(of), "--commit", COMMIT,
            "--observed-at-seq", str(head))
    assert p.returncode == 0, p.stderr
    assert lines(ledger)[-1]["covers_seq"] == head


def test_cli_watermark_ok_reads_through_the_e51_shared_lock_reader(ledger, monkeypatch):
    # the CLI path must not do a plain read: prove main() goes through nc.read_records
    calls = []
    real = nc.read_records
    monkeypatch.setattr(nc, "read_records", lambda p: calls.append(p) or real(p))
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    calls.clear()
    assert sc.main(["watermark-ok", "--ledger", str(ledger)]) == 0
    assert calls == [ledger]


def test_cli_watermark_ok_waits_for_an_exclusive_lock_holder(ledger):
    import fcntl, threading, time
    chain(ledger)
    run(ledger, obs("bg_a", "bg_b", "bg_c", "bg_d"))
    out = []
    with open(ledger, "rb") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        t = threading.Thread(target=lambda: out.append(sc.main(["watermark-ok", "--ledger", str(ledger)])))
        t.start()
        time.sleep(0.4)
        blocked = t.is_alive() and not out
        fcntl.flock(held, fcntl.LOCK_UN)
    t.join(5)
    assert blocked and out == [0]


def test_cli_script_error_exits_5(ledger, tmp_path):
    p = cli("invalidate", "--ledger", str(ledger), "--observed", str(tmp_path / "absent.json"), "--commit", COMMIT)
    assert p.returncode == 5


def test_cli_fingerprint_reads_rows_json_with_a_declaration(tmp_path):
    rf, df = tmp_path / "rows.json", tmp_path / "decl.json"
    rf.write_text(json.dumps(ROWS))
    df.write_text(json.dumps({"ph_nimitta": DECL_V}))
    p = cli("fingerprint", "--declarations", str(df), "--asset", "ph_nimitta", "--rows", str(rf))
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout) == {"asset": "ph_nimitta", "semantic_fingerprint": fpr(ROWS)}
