"""KV3-B-KYROUTE: kyroute.py routes by rules that ran, and FROZEN_PATHS.txt is refused unless it is whole.

Every tier asserted here comes out of the CLI; each rule row is shown with a path that hits it and one that
does not, and every refusal (exit 3, 64, 66) is shown to print no tier.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parent.parent
REPO = FLEET.parents[3]
KYROUTE = FLEET / "kyroute.py"
MANIFEST = FLEET / "FROZEN_PATHS.txt"
ITEMS = FLEET / "tests" / "fixtures" / "kyroute" / "items.json"
PLAN = REPO / "00_ARCHITECTURE" / "briefs" / "kalayantra" / "KALAYANTRA_RELAUNCH_PLAN_v2_7.md"
GIT = "/usr/bin/git"
O = "platform/python-sidecar/pipeline/orchestrator"
SEED = [O + "/asset_runner.py", O + "/runner.py", O + "/staleness.py", O + "/writers/__init__.py"]
KEYS = ["mode", "decision", "tier", "packet_tier", "computed_tier", "reasons", "frozen", "head"]
SAFE = "platform/src/components/Panel.tsx"

sys.dont_write_bytecode = True
sys.path.insert(0, str(FLEET))
import kyroute  # noqa: E402


def run(*args, env=None):
    e = dict(os.environ)
    e.pop("KY_GIT", None)
    e.update(env or {})
    p = subprocess.run([sys.executable, "-B", str(KYROUTE)] + [str(a) for a in args],
                       capture_output=True, text=True, env=e)
    out = json.loads(p.stdout) if p.stdout.strip() else None
    return p.returncode, out, p.stderr


def git(repo, *args, env=None, data=None):
    e = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1",
             GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
             GIT_AUTHOR_DATE="2026-10-12T00:00:00Z", GIT_COMMITTER_DATE="2026-10-12T00:00:00Z")
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        e.pop(k, None)
    e.update(env or {})
    p = subprocess.run([GIT, "-C", str(repo)] + list(args), capture_output=True, env=e, input=data, check=True)
    return p.stdout.decode("utf-8", "surrogateescape").strip()


@pytest.fixture(scope="module")
def repo(tmp_path_factory):
    r = tmp_path_factory.mktemp("kyroute_repo")
    git(r, "init", "-q", "-b", "main")
    (r / "README.md").write_text("base\n")
    (r / "platform" / "src" / "lib" / "auth").mkdir(parents=True)
    (r / "platform" / "src" / "lib" / "auth" / "old.ts").write_text("export const a = 1;\n")
    (r / "platform" / "src" / "components").mkdir(parents=True)
    (r / "platform" / "src" / "components" / "Old.tsx").write_text("const state = 'lit';\nexport {};\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    return r


def commit(repo, files, parent=None, delete=()):
    """A commit on top of `parent` made with plumbing only: no ref, HEAD, index or work-tree change."""
    parent = parent or git(repo, "rev-parse", "HEAD")
    idx = {"GIT_INDEX_FILE": str(Path(repo) / ".git" / ("idx-%s" % hashlib.sha1(repr((sorted(files.items()), delete, parent)).encode()).hexdigest()))}
    git(repo, "read-tree", parent, env=idx)
    for path, content in files.items():
        blob = git(repo, "hash-object", "-w", "--stdin", data=content if isinstance(content, bytes) else content.encode())
        git(repo, "update-index", "--add", "--cacheinfo", "100644,%s,%s" % (blob, path), env=idx)
    for path in delete:
        git(repo, "update-index", "--force-remove", path, env=idx)
    tree = git(repo, "write-tree", env=idx)
    os.unlink(idx["GIT_INDEX_FILE"])
    return git(repo, "commit-tree", tree, "-p", parent, "-m", "c")


def packet(tmp_path, item_id="X-1", tier="sonnet", d1=None, name="PACKET.md", **extra):
    fm = {"id": item_id, "build_tier": tier}
    if d1 is not None:
        fm["d1_paths"] = d1
    fm.update(extra)
    p = tmp_path / name
    p.write_text("```json\n" + json.dumps(fm, indent=1) + "\n```\n# body\n```json\n{\"id\": \"BODY\"}\n```\n")
    return p


def model(tmp_path, *items):
    p = tmp_path / "plan_model.json"
    p.write_text(json.dumps({"items": [{"id": i, "brief": b} for i, b in items]}))
    return p


def route_packet(tmp_path, brief=None, tier="sonnet", d1=None, repo_dir=None, frozen=None):
    items = [("X-1", brief)] if brief is not None else []
    args = ["packet", "--packet", packet(tmp_path, tier=tier, d1=d1), "--model", model(tmp_path, *items),
            "--repo", repo_dir or tmp_path]
    if frozen is not None:
        args += ["--frozen", frozen]
    return run(*args)


def route_diff(repo, head, built="sonnet", base=None, frozen=None, env=None):
    args = ["diff", "--repo", repo, "--base", base or git(repo, "rev-parse", "HEAD"), "--head", head, "--built-tier", built]
    if frozen is not None:
        args += ["--frozen", frozen]
    return run(*args, env=env)


def rules(out):
    return {r["rule"] for r in out["reasons"]}


def no_tier(out):
    return out is not None and list(out) == KEYS and out["tier"] is None and out["packet_tier"] is None \
        and out["computed_tier"] is None


# --- Contract A: the manifest -------------------------------------------------------------------------------

def test_manifest_seed_is_exactly_the_four_orchestrator_files():
    raw = MANIFEST.read_bytes()
    assert b"\r" not in raw and raw.endswith(b"\n")
    entries = [ln for ln in raw.decode("utf-8").split("\n") if ln and not ln.startswith("#")]
    assert entries == SEED
    assert kyroute.read_manifest(str(MANIFEST)) == SEED


BAD_MANIFESTS = {
    "empty": b"",
    "comments_only": b"# nothing here\n\n",
    "glob": (O + "/*.py\n").encode(),
    "glob_double_star": b"platform/**\n",
    "leading_slash": ("/" + SEED[0] + "\n").encode(),
    "dot_segment": b"platform/./x.py\n",
    "dotdot_segment": b"platform/../x.py\n",
    "leading_dot_slash": b"./platform/x.py\n",
    "inner_space": b"platform/a b.py\n",
    "trailing_space": (SEED[0] + " \n").encode(),
    "blank_looking_line_with_space": (SEED[0] + "\n \n").encode(),
    "indented_comment": (SEED[0] + "\n  # note\n").encode(),
    "tab": (SEED[0] + "\tx\n").encode(),
    "duplicate": (SEED[0] + "\n" + SEED[0] + "\n").encode(),
    "crlf": (SEED[0] + "\r\n").encode(),
    "not_utf8": b"platform/\xff\xfe.py\n",
    "directory_entry": b"platform/python-sidecar/\n",
    "empty_segment": b"platform//x.py\n",
    "nul": b"platform/x\x00.py\n",
}


@pytest.mark.parametrize("name", sorted(BAD_MANIFESTS))
def test_manifest_that_is_not_whole_is_refused_66_in_both_modes(name, tmp_path, repo):
    m = tmp_path / "FROZEN_PATHS.txt"
    m.write_bytes(BAD_MANIFESTS[name])
    rc, out, err = route_packet(tmp_path, d1=[SAFE], frozen=m)
    assert rc == 66 and no_tier(out) and out["decision"] is None and "FROZEN_PATHS" in err
    rc, out, err = route_diff(repo, commit(repo, {SAFE: "x\n"}), frozen=m)
    assert rc == 66 and no_tier(out) and out["decision"] is None


def test_manifest_missing_or_unreadable_is_refused_66(tmp_path, repo):
    head = commit(repo, {SAFE: "x\n"})
    for bad in (tmp_path / "absent.txt", tmp_path):  # absent; a directory cannot be read as a file
        rc, out, _ = route_packet(tmp_path, d1=[SAFE], frozen=bad)
        assert rc == 66 and no_tier(out)
        rc, out, _ = route_diff(repo, head, frozen=bad)
        assert rc == 66 and no_tier(out)
    locked = tmp_path / "locked.txt"
    locked.write_text(SEED[0] + "\n")
    locked.chmod(0)
    if not os.access(locked, os.R_OK):  # root reads anything; the absent and directory cases still stand
        rc, out, _ = route_packet(tmp_path, d1=[SAFE], frozen=locked)
        assert rc == 66 and no_tier(out)
    # the same inputs with a whole manifest do route: the refusals above are the manifest's
    good = tmp_path / "good.txt"
    good.write_text("# c\n\n" + SEED[0] + "\n")
    assert route_packet(tmp_path, d1=[SAFE], frozen=good)[0] == 0
    assert route_diff(repo, head, frozen=good)[0] == 0


# --- fixtures: KA-1e, K1-2, K6-4 ---------------------------------------------------------------------------

SKY = "platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**"
FIXTURE_RULES = {
    "KA-1e": {SKY, "**/*ephemeris*", "prose_entry"},
    "K1-2": {"prose_entry", "migration_metadata", "**/*ephemeris*"},
    "K6-4": {"prose_entry", "migration_metadata", "**/*ephemeris*"},
}


@pytest.mark.parametrize("item_id", sorted(FIXTURE_RULES))
def test_plan_fixture_items_route_to_opus_with_the_rule_that_forced_it(item_id, tmp_path):
    rc, out, _ = run("packet", "--packet", packet(tmp_path, item_id=item_id, tier="sonnet"),
                     "--model", ITEMS, "--repo", REPO)
    assert rc == 0 and list(out) == KEYS
    assert (out["mode"], out["decision"], out["tier"], out["packet_tier"], out["computed_tier"]) == \
        ("packet", "ROUTE", "opus", "sonnet", "opus")
    assert rules(out) == FIXTURE_RULES[item_id]
    assert out["frozen"] == [] and out["head"] is None
    for r in out["reasons"]:
        assert set(r) == {"rule", "path", "detail"}


def test_fixture_rules_are_forced_by_the_expected_entries(tmp_path):
    out = run("packet", "--packet", packet(tmp_path, item_id="KA-1e"), "--model", ITEMS, "--repo", REPO)[1]
    hit = {(r["rule"], r["path"]) for r in out["reasons"]}
    assert (SKY, "platform/python-sidecar/services/kala_core/sky/events.py") in hit
    assert ("**/*ephemeris*", "platform/python-sidecar/services/kala_core/sky/ephemeris.py") in hit
    assert any(rule == "prose_entry" and "gochara_kernel" in path for rule, path in hit)
    out = run("packet", "--packet", packet(tmp_path, item_id="K1-2"), "--model", ITEMS, "--repo", REPO)[1]
    hit = {(r["rule"], r["path"]) for r in out["reasons"]}
    assert ("prose_entry", "one additive migration: kala_avadhi re-shape columns") in hit
    assert any(r["rule"] == "migration_metadata" and "additive" in r["detail"] for r in out["reasons"])


def test_items_fixture_is_a_copy_of_the_pinned_plan_model():
    doc = json.loads(ITEMS.read_text(encoding="utf-8"))
    src = doc["source"]
    assert [i["id"] for i in doc["items"]] == ["KA-1e", "K1-2", "K6-4"]
    live = (REPO / src["path"]).read_bytes()
    if hashlib.sha256(live).hexdigest() != src["sha256"]:
        p = subprocess.run([GIT, "-C", str(REPO), "show", "%s:%s" % (src["revision"], src["path"])], capture_output=True)
        if p.returncode != 0:
            pytest.skip("the plan model has moved on and revision %s is not in this clone" % src["revision"])
        live = p.stdout
    assert hashlib.sha256(live).hexdigest() == src["sha256"]
    briefs = {i["id"]: i["brief"] for i in json.loads(live)["items"]}
    for i in doc["items"]:
        assert i["brief"] == briefs[i["id"]]


# --- the rule table, row by row ----------------------------------------------------------------------------

PS = "platform/python-sidecar"
ROWS = [  # (rule, one expanded alternative's hit, a near miss)
    (PS + "/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**", PS + "/ga_writers/a.py", PS + "/ga_writersx/a.py"),
    (PS + "/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**", PS + "/brahmagyan/ganita/x/a.py", PS + "/brahmagyan/other/a.py"),
    (PS + "/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**", PS + "/pyjhora_adapter/a.py", PS + "/adapter/a.py"),
    (PS + "/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**", PS + "/panchang_engine/a.py", PS + "/panchang/a.py"),
    (SKY, PS + "/services/kala_core/sky/a.py", PS + "/services/kala_core/ground/a.py"),
    (SKY, PS + "/services/gochara_kernel/a/b.py", PS + "/services/gochara/a.py"),
    (O + "/writers/ga_*.py", O + "/writers/ga_sensitive.py", O + "/writers/ka_avadhi.py"),
    (O + "/writers/ga_*.py", O + "/writers/ga_.py", O + "/writers/ga_sensitive.pyi"),
    ("**/*ephemeris*", "docs/a/swiss_Ephemeris_notes.md", "docs/a/ephemeri_s.md"),
    ("**/*ephemeris*", "data/EPHEMERIS_cache/x.bin", "data/ephe/x.bin"),
    ("platform/scripts/temporal/**", "platform/scripts/temporal/a.py", "platform/scripts/temporalx/a.py"),
    ("platform/scripts/migrate.ts", "platform/scripts/migrate.ts", "platform/scripts/migrate.tsx"),
    ("platform/migrations/**", "platform/migrations/README.md", "platform/migration/README.md"),
    ("platform/src/proxy.ts", "platform/src/proxy.ts", "platform/src/proxy.test.ts"),
    ("platform/src/lib/{auth,security,share,limits,mcp}/**", "platform/src/lib/auth/session.ts", "platform/src/lib/authz/session.ts"),
    ("platform/src/lib/{auth,security,share,limits,mcp}/**", "platform/src/lib/security/a.ts", "platform/src/lib/secure/a.ts"),
    ("platform/src/lib/{auth,security,share,limits,mcp}/**", "platform/src/lib/share/a.ts", "platform/src/lib/shared/a.ts"),
    ("platform/src/lib/{auth,security,share,limits,mcp}/**", "platform/src/lib/limits/a.ts", "platform/src/lib/limit/a.ts"),
    ("platform/src/lib/{auth,security,share,limits,mcp}/**", "platform/src/lib/mcp/a/b.ts", "platform/src/lib/mcpx/a.ts"),
    ("platform/src/app/api/{auth,admin,db}/**", "platform/src/app/api/auth/route.ts", "platform/src/app/api/chat/route.ts"),
    ("platform/src/app/api/{auth,admin,db}/**", "platform/src/app/api/admin/x/route.ts", "platform/src/app/admin/page.tsx"),
    ("platform/src/app/api/{auth,admin,db}/**", "platform/src/app/api/db/route.ts", "platform/src/app/api/dbx/route.ts"),
    (".github/workflows/**", ".github/workflows/deploy.yml", ".github/CODEOWNERS"),
    ("infra/**", "infra/terraform/main.tf", "infrastructure/main.tf"),
    ("platform/scripts/governance/**", "platform/scripts/governance/pravaha_tracker/a.py", "platform/scripts/gov/a.py"),
    ("00_ARCHITECTURE/briefs/kalayantra/fleet/**", "00_ARCHITECTURE/briefs/kalayantra/fleet/kyroute.py", "00_ARCHITECTURE/briefs/kalayantra/packets/P.md"),
    ("migration_file", "platform/migrations/1300_x.sql", "platform/db/1300_x.sql"),
    ("migration_file", "platform/supabase/migrations/a/b.sql", "platform/supabase/migrations/a/b.sql.md"),
]


def test_rows_cover_every_rule_row_and_every_brace_alternative():
    assert {r[0] for r in ROWS} == {name for name, _ in kyroute.PATH_RULES}
    for name, globs in kyroute.PATH_RULES:
        covered = [g for g in globs if any(kyroute.overlaps(kyroute.literal(hit), kyroute.pattern(g))
                                           for rule, hit, _ in ROWS if rule == name)]
        assert covered == list(globs), name


@pytest.mark.parametrize("rule,hit,miss", ROWS, ids=["%s@%d" % (r[0], n) for n, r in enumerate(ROWS)])
def test_rule_row_in_packet_mode(rule, hit, miss, tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [hit]})
    assert rc == 0 and out["computed_tier"] == "opus" and out["tier"] == "opus"
    assert {"rule": rule, "path": hit, "detail": "brief.owns"} in out["reasons"]
    rc, out, _ = route_packet(tmp_path, brief={"owns": [miss]})
    assert rc == 0 and out["tier"] == "sonnet" and out["reasons"] == [], miss


def test_rule_rows_in_diff_mode(repo):
    rc, out, _ = route_diff(repo, commit(repo, {hit: "x = 1\n" for _, hit, _ in ROWS}))   # one head, every hit
    assert rc == 1 and out["decision"] == "REQUEUE_OPUS_REWORK"
    for rule, hit, _ in ROWS:
        assert {"rule": rule, "path": hit, "detail": "changed path"} in out["reasons"], hit
    assert {r["path"] for r in out["reasons"]} == {hit for _, hit, _ in ROWS}
    rc, out, _ = route_diff(repo, commit(repo, {miss: "x = 1\n" for _, _, miss in ROWS}))  # and every near miss
    assert rc == 0 and out["tier"] == "sonnet" and out["reasons"] == []
    rule, hit, _ = ROWS[0]
    rc, out, _ = route_diff(repo, commit(repo, {hit: "x = 1\n"}))
    assert rc == 1 and out["reasons"] == [{"rule": rule, "path": hit, "detail": "changed path"}]


def test_rule_table_is_the_plan_excerpt():
    text = PLAN.read_text(encoding="utf-8")
    para = text[text.index("Opus is forced by:"):text.index("Paths in\n`FROZEN_PATHS.txt`")]
    ticks = re.findall(r"`([^`]+)`", para)
    globs = [t for t in ticks if "/" in t or t.startswith("**")]
    assert "platform/scripts/governance/pravaha_tracker/**" in globs  # named as included in the row before it
    globs.remove("platform/scripts/governance/pravaha_tracker/**")
    assert globs == [name for name, _ in kyroute.PATH_RULES if name != "migration_file"]
    assert [t for t in ticks if t not in globs] == ["platform/scripts/governance/pravaha_tracker/**", "'lit'",
                                                   "verification_pass_status", "swisseph", "jhora"]


def test_ephemeris_matches_any_segment_case_insensitively(tmp_path):
    for hit in ("a/Ephemeris/b.py", "EPHEMERIS.md", "a/b/c/swissephemeris.dat"):
        assert "**/*ephemeris*" in rules(route_packet(tmp_path, d1=[hit])[1]), hit
    assert route_packet(tmp_path, d1=["a/ephemeri/s.py"])[1]["tier"] == "sonnet"


# --- entries: normalisation, prose, globs ------------------------------------------------------------------

def test_item_owning_only_components_paths_stays_sonnet(tmp_path, repo):
    brief = {"owns": ["platform/src/components/Panel.tsx", "./platform/src/components/chart/Wheel.tsx",
                      str(tmp_path / "platform/src/components/a/B.test.tsx")],
             "shared": ["platform/src/components/index.ts"], "migration": "NONE", "op": None}
    rc, out, _ = route_packet(tmp_path, brief=brief, d1=["platform/src/components/C.tsx"])
    assert rc == 0 and out == {"mode": "packet", "decision": "ROUTE", "tier": "sonnet", "packet_tier": "sonnet",
                               "computed_tier": "sonnet", "reasons": [], "frozen": [], "head": None}
    head = commit(repo, {"platform/src/components/New.tsx": "export const n = 1;\n",
                         "platform/src/components/a b/Ω.tsx": "export const lit = 'unlit';\n"})
    rc, out, _ = route_diff(repo, head)
    assert rc == 0 and out == {"mode": "diff", "decision": "ROUTE", "tier": "sonnet", "packet_tier": "sonnet",
                               "computed_tier": "sonnet", "reasons": [], "frozen": [], "head": head}


def test_a_packet_may_raise_the_tier_but_never_lower_it(tmp_path, repo):
    rc, out, _ = route_packet(tmp_path, tier="opus", d1=[SAFE])
    assert rc == 0 and (out["tier"], out["packet_tier"], out["computed_tier"]) == ("opus", "opus", "sonnet")
    rc, out, _ = route_packet(tmp_path, tier="sonnet", d1=["infra/x.tf"])
    assert rc == 0 and (out["tier"], out["packet_tier"], out["computed_tier"]) == ("opus", "sonnet", "opus")
    rc, out, _ = route_diff(repo, commit(repo, {SAFE: "x\n"}), built="opus")
    assert rc == 0 and (out["tier"], out["packet_tier"], out["computed_tier"]) == ("opus", "opus", "sonnet")


@pytest.mark.parametrize("entry", [
    "one additive migration",
    "platform/src/components/Panel.tsx (regenerated)",
    "platform/src/components/../lib/auth/x.ts",
    "../outside.ts",
    "/etc/hosts",
    "platform/src/components/\tPanel.tsx",
    "",
    "platform/src/components/{a,b.tsx",
    "platform/src/components/[ab.tsx",
])
def test_a_prose_entry_routes_to_opus(entry, tmp_path):
    for field in ("owns", "shared"):
        rc, out, _ = route_packet(tmp_path, brief={field: [entry, SAFE]})
        assert rc == 0 and out["tier"] == "opus" and out["computed_tier"] == "opus"
        assert out["reasons"] == [{"rule": "prose_entry", "path": entry, "detail": "brief." + field}]
    rc, out, _ = route_packet(tmp_path, d1=[entry, SAFE])
    assert rc == 0 and out["reasons"] == [{"rule": "prose_entry", "path": entry, "detail": "d1_paths"}]


def test_normalisation_makes_entries_repository_relative(tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": ["./platform/src/lib/auth/a.ts", str(tmp_path) + "/infra/x.tf"]})
    assert rc == 0 and [(r["rule"], r["path"]) for r in out["reasons"]] == [
        ("platform/src/lib/{auth,security,share,limits,mcp}/**", "platform/src/lib/auth/a.ts"), ("infra/**", "infra/x.tf")]
    other = tmp_path / "elsewhere"
    other.mkdir()
    rc, out, _ = route_packet(tmp_path, brief={"owns": [str(tmp_path) + "/infra/x.tf"]}, repo_dir=other)
    assert rc == 0 and rules(out) == {"prose_entry"}  # absolute, but not under this --repo
    assert kyroute.normalise("./a/b", "/r") == ("a/b", False)
    assert kyroute.normalise("/r/a/b", "/r") == ("a/b", False)
    assert kyroute.normalise("/rr/a/b", "/r") == ("/rr/a/b", True)
    assert kyroute.normalise("/r", "/r")[1] is True


@pytest.mark.parametrize("entry,rule", [
    ("platform/src/**", "platform/src/proxy.ts"),
    ("platform/src/lib/*/session.ts", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("platform/src/lib/a*/**", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("platform/src/lib/{rag,auth}/x.ts", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("platform/src/lib/[a-b]uth/x.ts", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("platform/src/lib/aut?/x.ts", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("platform/src/lib/auth", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("platform/src/lib/auth/", "platform/src/lib/{auth,security,share,limits,mcp}/**"),
    ("**/*.sql", "migration_file"),
    ("platform/*/migrate.ts", "platform/scripts/migrate.ts"),
    (O + "/writers/*_avadhi.py", O + "/writers/ga_*.py"),
    ("platform/src/components/**", "**/*ephemeris*"),
    ("platform/src/components/*.tsx", "**/*ephemeris*"),
    ("in*/**", "infra/**"),
])
def test_an_owns_glob_that_can_overlap_a_rule_matches_it(entry, rule, tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [entry]})
    assert rc == 0 and out["tier"] == "opus" and rule in rules(out)


@pytest.mark.parametrize("entry", [
    "platform/src/components/Panel*.tsx/x",   # no star spans a slash
    "platform/src/lib/rag/*.ts",
    "platform/src/lib/{rag,chat}/a.ts",
    "platform/src/lib/?uthx/a.ts",
    O + "/writers/ka_*.py",
])
def test_an_owns_glob_that_cannot_overlap_any_rule_adds_no_path_rule(entry, tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [entry]})
    assert rc == 0 and rules(out) <= {"**/*ephemeris*"}  # any star can still spell "ephemeris"
    assert ("**/*ephemeris*" in rules(out)) == ("*" in entry)


def test_an_entry_naming_an_existing_directory_covers_what_is_under_it(tmp_path):
    (tmp_path / "platform" / "src" / "lib" / "auth").mkdir(parents=True)
    (tmp_path / "platform" / "src" / "components").mkdir(parents=True)
    rc, out, _ = route_packet(tmp_path, brief={"owns": ["platform/src/lib"]})
    assert rc == 0 and out["tier"] == "opus" and "platform/src/lib/{auth,security,share,limits,mcp}/**" in rules(out)
    rc, out, _ = route_packet(tmp_path, brief={"owns": ["platform/src/components/Panel.tsx"]})
    assert rc == 0 and out["tier"] == "sonnet"


@pytest.mark.parametrize("field,value,forced", [
    ("migration", "additive", True), ("migration", "none", True), ("migration", " ", True), ("migration", 0, True),
    ("migration", False, True), ("migration", [], True), ("migration", "NONE", False), ("migration", "", False),
    ("migration", None, False), ("op", ["readback_sql"], True), ("op", [], True), ("op", "NONE", False),
    ("op", None, False), ("op", "", False),
])
def test_non_none_migration_metadata_forces_opus(field, value, forced, tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [SAFE], field: value})
    assert rc == 0 and out["tier"] == ("opus" if forced else "sonnet")
    assert [r["rule"] for r in out["reasons"]] == (["migration_metadata"] if forced else [])
    if forced:
        assert out["reasons"][0]["path"] is None and out["reasons"][0]["detail"].startswith("brief.%s = " % field)


def test_absent_migration_metadata_and_no_paths(tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [SAFE]})
    assert rc == 0 and out["tier"] == "sonnet"
    # an item that names no path at all: no path rule ran, so it is not sonnet
    for brief in ({}, {"owns": None}, {"owns": [], "shared": []}):
        rc, out, _ = route_packet(tmp_path, brief=brief)
        assert rc == 0 and out["tier"] == "opus" and rules(out) == {"no_paths"}
    rc, out, _ = route_packet(tmp_path, brief={}, d1=[SAFE])
    assert rc == 0 and out["tier"] == "sonnet"


# --- frozen paths: STOP, exit 3 ----------------------------------------------------------------------------

@pytest.mark.parametrize("path", SEED)
def test_a_seeded_path_in_a_packet_is_not_routed(path, tmp_path):
    for brief, d1 in (({"owns": [SAFE, path]}, None), ({"shared": [path]}, None), ({"owns": ["./" + path]}, None),
                      ({"owns": [str(tmp_path) + "/" + path]}, None), ({}, [path]), (None, [path]),
                      ({"owns": ["infra/x.tf", path], "migration": "additive"}, None)):
        for tier in ("sonnet", "opus"):
            rc, out, _ = route_packet(tmp_path, brief=brief, d1=d1, tier=tier)
            assert rc == 3 and no_tier(out) and out["decision"] == "STOP" and out["frozen"] == [path]
            assert [r["rule"] for r in out["reasons"]] == ["freeze"] and out["reasons"][0]["path"] == path


@pytest.mark.parametrize("path", SEED)
def test_a_seeded_path_in_a_diff_is_not_routed(path, repo):
    for files, delete in (({path: "x = 1\n"}, ()), ({path: "x = 1\n", SAFE: "y\n", "infra/a.tf": "z\n"}, ())):
        head = commit(repo, files)
        for built in ("sonnet", "opus"):
            rc, out, _ = route_diff(repo, head, built=built)
            assert rc == 3 and no_tier(out) and out["decision"] == "STOP" and out["frozen"] == [path]
            assert out["reasons"] == [{"rule": "freeze", "path": path, "detail": "changed path"}] and out["head"] == head
    with_file = commit(repo, {path: "x = 1\n"})
    gone = commit(repo, {}, parent=with_file, delete=[path])
    rc, out, _ = route_diff(repo, gone, base=with_file)  # a deletion is a change
    assert rc == 3 and out["frozen"] == [path]
    moved = commit(repo, {path + ".bak": "x = 1\n"}, parent=with_file, delete=[path])
    rc, out, _ = route_diff(repo, moved, base=with_file, built="opus")  # a rename away is a change (--no-renames)
    assert rc == 3 and out["frozen"] == [path]


def test_all_frozen_hits_are_listed_and_the_manifest_in_use_decides(tmp_path, repo):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [SEED[2], SEED[0]], "shared": [SEED[0]]})
    assert rc == 3 and out["frozen"] == [SEED[0], SEED[2]]
    m = tmp_path / "m.txt"
    m.write_text("# test manifest\n" + SAFE + "\n")
    assert route_packet(tmp_path, d1=[SAFE], frozen=m)[0] == 3
    assert route_packet(tmp_path, d1=[SEED[0]], frozen=m)[0] == 0
    assert route_diff(repo, commit(repo, {SAFE: "x\n"}), frozen=m)[0] == 3


@pytest.mark.parametrize("entry", [O + "/**", O + "/*.py", O + "/writers/*.py", O + "/writers/__init__.p?",
                                   O + "/{runner,x}.py", "platform/**", O + "/writers/"])
def test_a_glob_that_covers_a_frozen_path_is_not_routed(entry, tmp_path):
    rc, out, _ = route_packet(tmp_path, brief={"owns": [entry]})
    assert rc == 3 and no_tier(out) and out["decision"] == "STOP" and out["frozen"]
    assert all(r["rule"] == "freeze" and r["detail"] == "brief.owns: " + entry for r in out["reasons"])


def test_a_new_conforming_writer_is_still_routed(tmp_path, repo):
    for entry in (O + "/writers/ka_new.py", O + "/writers/ka_*.py", O + "/writers/__init__.pyi", O + "/runner_test.py"):
        rc, out, _ = route_packet(tmp_path, brief={"owns": [entry]})
        assert rc == 0 and out["decision"] == "ROUTE" and out["frozen"] == []
    rc, out, _ = route_diff(repo, commit(repo, {O + "/writers/ka_new.py": "x = 1\n"}))
    assert rc == 0 and out["tier"] == "sonnet"
    rc, out, _ = route_diff(repo, commit(repo, {O + "/writers/ga_new.py": "x = 1\n"}))
    assert rc == 1


# --- diff: the Sonnet head is preserved --------------------------------------------------------------------

def snapshot(repo):
    files = {}
    for p in sorted(Path(repo).rglob("*")):
        if p.is_file() and ".git" not in p.relative_to(repo).parts:
            files[str(p.relative_to(repo))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"refs": git(repo, "for-each-ref", "--format=%(refname) %(objectname)"),
            "HEAD": (Path(repo) / ".git" / "HEAD").read_text(), "head_sha": git(repo, "rev-parse", "HEAD"),
            "status": git(repo, "--no-optional-locks", "status", "--porcelain=v1", "--untracked-files=all"),
            "stash": git(repo, "stash", "list"), "files": files,
            "index": hashlib.sha256((Path(repo) / ".git" / "index").read_bytes()).hexdigest()}


def test_a_sonnet_built_auth_diff_exits_1_and_touches_nothing(tmp_path):
    r = tmp_path / "work"
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / "platform" / "src" / "lib" / "auth").mkdir(parents=True)
    (r / "platform" / "src" / "lib" / "auth" / "session.ts").write_text("export const ttl = 1;\n")
    (r / "README.md").write_text("base\n")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "base")
    base = git(r, "rev-parse", "HEAD")
    git(r, "checkout", "-q", "-b", "kalayantra/x-1")
    (r / "platform" / "src" / "lib" / "auth" / "session.ts").write_text("export const ttl = 2;\n")
    git(r, "commit", "-q", "-am", "sonnet work")
    head = git(r, "rev-parse", "HEAD")
    (r / "README.md").write_text("dirty\n")      # uncommitted work and an untracked file must survive too
    (r / "untracked.txt").write_text("u\n")
    before = snapshot(r)
    rc, out, _ = route_diff(r, head, built="sonnet", base=base)
    assert rc == 1 and out == {
        "mode": "diff", "decision": "REQUEUE_OPUS_REWORK", "tier": "opus", "packet_tier": "sonnet",
        "computed_tier": "opus", "frozen": [], "head": head,
        "reasons": [{"rule": "platform/src/lib/{auth,security,share,limits,mcp}/**",
                     "path": "platform/src/lib/auth/session.ts", "detail": "changed path"}]}
    assert snapshot(r) == before and before["head_sha"] == head and git(r, "cat-file", "-t", head) == "commit"
    rc, out, _ = route_diff(r, head, built="opus", base=base)  # the same diff built by Opus is simply routed
    assert rc == 0 and out["decision"] == "ROUTE" and out["tier"] == "opus" and out["head"] == head
    rc, out, _ = route_diff(r, head, built="sonnet", base=base, frozen=None, env={"GIT_DIR": "/nonexistent"})
    assert rc == 1  # --repo governs, not an inherited GIT_DIR
    assert snapshot(r) == before


def test_git_is_only_asked_to_read(repo, tmp_path):
    log = tmp_path / "git.log"
    fake = tmp_path / "git"
    fake.write_text("#!/bin/sh\nprintf '%%s\\n' \"$*\" >> %s\nexec %s \"$@\"\n" % (log, GIT))
    fake.chmod(0o755)
    head = commit(repo, {"platform/src/lib/auth/a.ts": "x\n", SAFE: "const s = 'lit';\n"})
    rc, out, _ = route_diff(repo, head, env={"KY_GIT": str(fake)})
    assert rc == 1
    calls = log.read_text().splitlines()
    assert calls and any("--name-only --no-renames" in c for c in calls)
    for c in calls:
        words = c.split()
        sub = [w for w in words if w in ("diff", "cat-file", "rev-parse", "checkout", "reset", "stash", "clean",
                                         "rm", "commit", "update-ref", "branch", "worktree", "gc", "add", "restore")]
        assert sub and sub[0] in ("diff", "cat-file"), c
        assert "--no-optional-locks" in words, c
    src = KYROUTE.read_text(encoding="utf-8")
    assert not re.search(r"open\([^)]*[\"'][wax+]", src) and "os.remove" not in src and "shutil" not in src


def test_deleted_and_renamed_paths_count(repo):
    base = git(repo, "rev-parse", "HEAD")
    rc, out, _ = route_diff(repo, commit(repo, {}, delete=["platform/src/lib/auth/old.ts"]), base=base)
    assert rc == 1 and out["reasons"][0]["path"] == "platform/src/lib/auth/old.ts"
    moved = commit(repo, {"platform/src/components/moved.ts": "export const a = 1;\n"}, delete=["platform/src/lib/auth/old.ts"])
    rc, out, _ = route_diff(repo, moved, base=base)
    assert rc == 1 and out["reasons"][0]["path"] == "platform/src/lib/auth/old.ts"


def test_diff_paths_are_matched_literally(repo):
    for path, rc_want in (("platform/src/lib/auth/a b.ts", 1), ("platform/src/components/[auth]/*.ts", 0),
                          ("platform/src/components/**", 0), ("platform/src/components/Ω \"q\"\n.tsx", 0),
                          ("infra/ä.tf", 1)):
        rc, out, _ = route_diff(repo, commit(repo, {path: "x\n"}))
        assert rc == rc_want, path
        if rc:
            assert out["reasons"][0]["path"] == path


CONTENT = [
    ("lit_state", "    if row.state == 'lit':", "    if row.state == 'unlit' or lit:"),
    ("lit_state", 'UPDATE asset_throughput SET state = "lit"', "split the literal"),
    ("verification_pass_status", "    row['verification_pass_status'] = tier", "    row['verification_status'] = tier"),
    ("swisseph_jhora_import", "import swisseph as swe", "swisseph is mentioned in a comment"),
    ("swisseph_jhora_import", "from jhora.panchanga import drik", "# important: jhora-free"),
    ("swisseph_jhora_import", "    from os import path; import jhora", "imported = 'from_swisseph'"),
    ("swisseph_jhora_import", "mod = __import__('swisseph')", "swe = load('swisseph')"),
    ("swisseph_jhora_import", "importlib.import_module('jhora.horoscope')", "jhora_reimport = 1"),
]


@pytest.mark.parametrize("rule,hit,miss", CONTENT, ids=["%s@%d" % (c[0], n) for n, c in enumerate(CONTENT)])
def test_content_rules_on_added_and_removed_lines(rule, hit, miss, repo):
    path = "platform/src/components/notes.py"
    with_hit = commit(repo, {path: "a = 1\n" + hit + "\nb = 2\n"})
    with_miss = commit(repo, {path: "a = 1\n" + miss + "\nb = 2\n"})
    base = git(repo, "rev-parse", "HEAD")
    rc, out, _ = route_diff(repo, with_hit, base=base)             # added
    assert rc == 1 and out["reasons"] == [{"rule": rule, "path": path, "detail": "added line 2: " + hit.strip()}]
    plain = commit(repo, {path: "a = 1\nb = 2\n"}, parent=with_hit)
    rc, out, _ = route_diff(repo, plain, base=with_hit)            # removed
    assert rc == 1 and out["reasons"] == [{"rule": rule, "path": path, "detail": "removed line 2: " + hit.strip()}]
    rc, out, _ = route_diff(repo, with_miss, base=base)
    assert rc == 0 and out["tier"] == "sonnet" and out["reasons"] == []
    rc, out, _ = route_diff(repo, with_hit, base=base, built="opus")
    assert rc == 0 and out["tier"] == "opus" and rules(out) == {rule}


def test_content_rules_read_only_changed_lines_and_survive_odd_files(repo):
    path = "platform/src/components/Old.tsx"   # the base already holds a 'lit' line
    rc, out, _ = route_diff(repo, commit(repo, {path: "const state = 'lit';\nexport {};\nexport const n = 1;\n"}))
    assert rc == 0 and out["reasons"] == []      # an untouched context line is not a diff line
    rc, out, _ = route_diff(repo, commit(repo, {path: "const state = 'on';\nexport {};\n"}))
    assert rc == 1 and [r["detail"].split(":")[0] for r in out["reasons"]] == ["removed line 1"]
    blob = b"\x00\x01\x02 state = 'lit' \xff\xfe\n\x00"
    rc, out, _ = route_diff(repo, commit(repo, {"platform/src/components/blob.bin": blob}))
    assert rc == 1 and rules(out) == {"lit_state"}     # a binary file is read as text, not skipped
    tricky = "--- a/x\n+++ b/x\n@@ -1 +1 @@\ndiff --git a/infra/x b/infra/x\n-- 'lit'\nno newline at end"
    rc, out, _ = route_diff(repo, commit(repo, {"platform/src/components/patch.txt": tricky}))
    assert rc == 1 and out["reasons"] == [{"rule": "lit_state", "path": "platform/src/components/patch.txt",
                                           "detail": "added line 5: -- 'lit'"}]
    two = commit(repo, {"platform/src/components/a.py": "import swisseph\n", "platform/src/components/b.py": "ok = 1\n",
                        "platform/src/components/c.py": "x = \"lit\"\nverification_pass_status = 1\n"})
    rc, out, _ = route_diff(repo, two)
    assert rc == 1 and [(r["rule"], r["path"].rsplit("/", 1)[1]) for r in out["reasons"]] == [
        ("swisseph_jhora_import", "a.py"), ("lit_state", "c.py"), ("verification_pass_status", "c.py")]


def test_an_empty_diff_is_not_sonnet(repo):
    base = git(repo, "rev-parse", "HEAD")
    for head in (base, commit(repo, {})):
        rc, out, _ = route_diff(repo, head, base=base)
        assert rc == 1 and rules(out) == {"no_paths"} and out["tier"] == "opus"


# --- escalation --------------------------------------------------------------------------------------------

ESCALATION = [
    ("sonnet", 0, 3, 0, "CONTINUE"), ("sonnet", 2, 3, 0, "CONTINUE"), ("sonnet", 3, 3, 0, "OPUS_REWORK"),
    ("sonnet", 4, 3, 0, "OPUS_REWORK"), ("sonnet", 0, 3, 1, "OPUS_REWORK"), ("sonnet", 0, 3, 2, "OPUS_REWORK"),
    ("sonnet", 3, 3, 1, "OPUS_REWORK"), ("sonnet", 1, 1, 0, "OPUS_REWORK"), ("sonnet", 0, 1, 0, "CONTINUE"),
    ("opus", 0, 3, 0, "CONTINUE"), ("opus", 2, 3, 1, "CONTINUE"), ("opus", 0, 3, 1, "CONTINUE"),
    ("opus", 0, 3, 2, "BLOCK"), ("opus", 0, 3, 3, "BLOCK"), ("opus", 3, 3, 0, "BLOCK"), ("opus", 5, 3, 0, "BLOCK"),
    ("opus", 3, 3, 2, "BLOCK"), ("opus", 2, 3, 0, "CONTINUE"),
]


@pytest.mark.parametrize("tier,red,mx,rej,want", ESCALATION)
def test_escalation_table(tier, red, mx, rej, want):
    rc, out, _ = run("escalate", "--tier", tier, "--red-loops", red, "--max-loops", mx, "--rejected", rej)
    assert rc == 0 and out == {"decision": want}


@pytest.mark.parametrize("args", [
    ["--tier", "haiku", "--red-loops", "0", "--max-loops", "3", "--rejected", "0"],
    ["--tier", "sonnet", "--red-loops", "-1", "--max-loops", "3", "--rejected", "0"],
    ["--tier", "sonnet", "--red-loops", "0", "--max-loops", "0", "--rejected", "0"],
    ["--tier", "sonnet", "--red-loops", "0", "--max-loops", "3", "--rejected", "-1"],
    ["--tier", "sonnet", "--red-loops", "x", "--max-loops", "3", "--rejected", "0"],
    ["--tier", "sonnet", "--red-loops", "1.0", "--max-loops", "3", "--rejected", "0"],
    ["--tier", "sonnet", "--red-loops", "0", "--max-loops", "3"],
    ["--tier", "opus", "--max-loops", "3", "--rejected", "2"],
])
def test_escalate_usage_errors_decide_nothing(args):
    rc, out, err = run("escalate", *args)
    assert rc == 64 and out == {"decision": None} and err.strip()


# --- refusals: 64 and 66 print no tier ---------------------------------------------------------------------

def test_usage_errors_exit_64_without_a_tier(tmp_path, repo):
    p, m = packet(tmp_path, d1=[SAFE]), model(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    cases = [
        [], ["route"], ["packet"], ["packet", "--packet", p, "--model", m],
        ["packet", "--packet", "PACKET.md", "--model", m, "--repo", tmp_path],
        ["packet", "--packet", p, "--model", "plan_model.json", "--repo", tmp_path],
        ["packet", "--packet", p, "--model", m, "--repo", "."],
        ["packet", "--packet", p, "--model", m, "--repo", tmp_path, "--frozen", "FROZEN_PATHS.txt"],
        ["packet", "--packet", p, "--model", m, "--repo", tmp_path, "--built-tier", "sonnet"],
        ["diff", "--repo", repo, "--base", head, "--head", head],
        ["diff", "--repo", repo, "--base", head, "--head", head, "--built-tier", "haiku"],
        ["diff", "--repo", repo, "--base", "HEAD", "--head", head, "--built-tier", "sonnet"],
        ["diff", "--repo", repo, "--base", head, "--head", head[:12], "--built-tier", "sonnet"],
        ["diff", "--repo", repo, "--base", "A" * 40, "--head", head, "--built-tier", "sonnet"],
        ["diff", "--repo", "relative", "--base", head, "--head", head, "--built-tier", "sonnet"],
    ]
    for args in cases:
        rc, out, err = run(*args)
        assert rc == 64 and no_tier(out) and out["decision"] is None and err.strip(), args
    rc, out, err = run("diff", "--repo", repo, "--base", head, "--head", head, "--built-tier", "sonnet", env={"KY_GIT": "git"})
    assert rc == 64 and no_tier(out)


def test_invalid_packet_or_model_exits_66_without_a_tier(tmp_path):
    good_p, good_m = packet(tmp_path, d1=[SAFE]), model(tmp_path, ("X-1", {"owns": [SAFE]}))
    assert run("packet", "--packet", good_p, "--model", good_m, "--repo", tmp_path)[0] == 0
    bad_packets = {
        "no_fence": "id: X-1\n",
        "not_first_line": "\n```json\n{\"id\":\"X-1\",\"build_tier\":\"sonnet\"}\n```\n",
        "unclosed": "```json\n{\"id\":\"X-1\",\"build_tier\":\"sonnet\"}\n",
        "not_json": "```json\n{id: X-1}\n```\n",
        "array": "```json\n[]\n```\n",
        "dup_key": "```json\n{\"id\":\"X-1\",\"build_tier\":\"opus\",\"build_tier\":\"sonnet\"}\n```\n",
        "no_id": "```json\n{\"build_tier\":\"sonnet\"}\n```\n",
        "id_not_string": "```json\n{\"id\":1,\"build_tier\":\"sonnet\"}\n```\n",
        "no_tier": "```json\n{\"id\":\"X-1\"}\n```\n",
        "bad_tier": "```json\n{\"id\":\"X-1\",\"build_tier\":\"haiku\"}\n```\n",
        "null_tier": "```json\n{\"id\":\"X-1\",\"build_tier\":null}\n```\n",
        "d1_not_list": "```json\n{\"id\":\"X-1\",\"build_tier\":\"sonnet\",\"d1_paths\":\"a\"}\n```\n",
        "d1_not_strings": "```json\n{\"id\":\"X-1\",\"build_tier\":\"sonnet\",\"d1_paths\":[1]}\n```\n",
        "nan": "```json\n{\"id\":\"X-1\",\"build_tier\":\"sonnet\",\"max_loops\":NaN}\n```\n",
        "empty": "",
    }
    for name, text in bad_packets.items():
        p = tmp_path / ("bad_%s.md" % name)
        p.write_text(text)
        rc, out, err = run("packet", "--packet", p, "--model", good_m, "--repo", tmp_path)
        assert rc == 66 and no_tier(out) and out["decision"] is None and err.strip(), name
    bad_models = {
        "not_json": "{", "empty": "", "array": "[]", "no_items": "{}", "items_not_list": "{\"items\": {}}",
        "item_not_object": "{\"items\": [1]}",
        "dup_item": json.dumps({"items": [{"id": "X-1", "brief": {}}, {"id": "X-1", "brief": {"owns": [SAFE]}}]}),
        "brief_not_object": json.dumps({"items": [{"id": "X-1", "brief": []}]}),
        "owns_not_list": json.dumps({"items": [{"id": "X-1", "brief": {"owns": SAFE}}]}),
        "owns_not_strings": json.dumps({"items": [{"id": "X-1", "brief": {"owns": [SAFE, 3]}}]}),
        "shared_not_list": json.dumps({"items": [{"id": "X-1", "brief": {"owns": [SAFE], "shared": {}}}]}),
    }
    for name, text in bad_models.items():
        m = tmp_path / ("bad_%s.json" % name)
        m.write_text(text)
        rc, out, err = run("packet", "--packet", good_p, "--model", m, "--repo", tmp_path)
        assert rc == 66 and no_tier(out) and out["decision"] is None and err.strip(), name
    for args in (["--packet", tmp_path / "absent.md", "--model", good_m, "--repo", tmp_path],
                 ["--packet", good_p, "--model", tmp_path / "absent.json", "--repo", tmp_path],
                 ["--packet", tmp_path, "--model", good_m, "--repo", tmp_path],
                 ["--packet", good_p, "--model", good_m, "--repo", tmp_path / "absent"]):
        rc, out, _ = run("packet", *args)
        assert rc == 66 and no_tier(out), args


def test_no_such_item_needs_d1_paths(tmp_path):
    m = model(tmp_path, ("OTHER", {"owns": ["infra/x.tf"]}))
    for d1 in (None, []):
        rc, out, err = run("packet", "--packet", packet(tmp_path, d1=d1), "--model", m, "--repo", tmp_path)
        assert rc == 66 and no_tier(out) and "X-1" in err
    rc, out, _ = run("packet", "--packet", packet(tmp_path, d1=[SAFE]), "--model", m, "--repo", tmp_path)
    assert rc == 0 and out["tier"] == "sonnet"   # the other item's paths are not this packet's
    rc, out, _ = run("packet", "--packet", packet(tmp_path, d1=["infra/x.tf"]), "--model", m, "--repo", tmp_path)
    assert rc == 0 and out["tier"] == "opus"


def test_a_diff_that_cannot_be_read_exits_66_without_a_tier(tmp_path, repo):
    head = git(repo, "rev-parse", "HEAD")
    unknown = "1" * 40
    tree = git(repo, "rev-parse", head + "^{tree}")
    for base, hd in ((unknown, head), (head, unknown), (head, tree)):
        rc, out, err = route_diff(repo, hd, base=base)
        assert rc == 66 and no_tier(out) and out["decision"] is None and err.strip()
    empty = tmp_path / "not_a_repo"
    empty.mkdir()
    env = {"GIT_CEILING_DIRECTORIES": str(tmp_path)}
    assert route_diff(empty, head, base=head, env=env)[0] == 66
    assert route_diff(tmp_path / "absent", head, base=head)[0] == 66
    assert route_diff(repo, head, base=head, env={"KY_GIT": str(tmp_path / "no-git")})[0] == 66
    for n, script in enumerate(("#!/bin/sh\nexit 1\n", "#!/bin/sh\ncase \"$*\" in *cat-file*) exit 0;; esac\nexit 128\n",
                                "#!/bin/sh\ncase \"$*\" in *cat-file*) exit 0;; *name-only*) printf 'platform/src/components/a.tsx\\0'; exit 0;; esac\nexit 2\n",
                                "#!/bin/sh\ncase \"$*\" in *cat-file*) exit 0;; *name-only*) printf 'platform/src/components/a.tsx\\0'; exit 0;; esac\nprintf 'garbage\\n'\n")):
        fake = tmp_path / ("git%d" % n)
        fake.write_text(script)
        fake.chmod(0o755)
        rc, out, _ = route_diff(repo, commit(repo, {SAFE: "x\n"}), env={"KY_GIT": str(fake)})
        assert rc == 66 and no_tier(out), script


def test_an_internal_error_is_never_read_as_a_route_or_a_requeue(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(kyroute, "read_manifest", lambda path: 1 / 0)
    rc = kyroute.main(["packet", "--packet", str(packet(tmp_path, d1=[SAFE])), "--model", str(model(tmp_path)),
                       "--repo", str(tmp_path)])
    out = json.loads(capsys.readouterr().out)
    assert rc == 70 and no_tier(out) and out["decision"] is None


def test_default_manifest_is_the_one_beside_the_script(tmp_path):
    assert kyroute.DEFAULT_MANIFEST == str(MANIFEST)
    rc, out, _ = run("packet", "--packet", packet(tmp_path, d1=[SEED[1]]), "--model", model(tmp_path), "--repo", tmp_path)
    assert rc == 3 and out["frozen"] == [SEED[1]]
