"""Role cards under plan v3.0 (Amendment A8): the authority header, the byte proxy, record templates against their
schemas, and one check (with its negative) per round-1 review finding of the cards area (C-01, C-02, C-03, N-03 … N-08).
A8 §4 retired the COVERAGE matrices, the token-measurement binding and the cards' restatements of CLAUDE.md §I/§N;
the checks for those are gone and a test guards that they stay gone.

A card is prose, so most checks here read text. Each one names the rule it looks for and has a negative case
that shows the check can fail; none of them proves that a model obeys the rule (that is the rehearsal's job).
Stdlib + pytest only; nothing here starts the real program, a tracker, git or the network."""
import ast
import datetime
import fnmatch
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
sys.path.insert(0, str(FLEET))
import kyschema  # noqa: E402
import kyveto  # noqa: E402

CARDS_DIR = FLEET / "cards"
HEADER = "Authority: plan v3.0 §C; this card carries role-specific instructions only"   # A8: first body line of every card
RETIRED = {"KA": range(8, 17), "PA": range(6, 15), "AD": range(8, 13)}   # A8 §4: the lines that restated CLAUDE.md §I/§N
PLAN = FLEET.parent / "KALAYANTRA_RELAUNCH_PLAN_v2_7.md"
AGENT = REPO / ".claude" / "agents" / "kalayantra-owner-surrogate.md"
PREFIX = {"BOOTSTRAP": "BS", "BOOTSTRAP_REVIEWER": "BR", "FIXTURE_BUILDER": "FB", "FIXTURE_VERIFIER": "FV",
          "OWNER_SURROGATE": "OS"}
CAMPAIGN_PREFIX = {"KARAKA": "KA", "PARIKSAKA": "PA", "ADHIKARIN": "AD"}
ALL_PREFIX = dict(PREFIX, **CAMPAIGN_PREFIX)
CAMPAIGN_BYTE_CAP = 5200  # B-4 job's accepted proxy; bootstrap token measurements remain unchanged.
TOKEN_CAP, BYTE_CAP = 1500, 3500
ID = re.compile(r"\b(BS|BR|FB|FV|OS|KA|PA|AD)-(\d{2})\b")
SCHEMAS = {n: json.loads((FLEET / "schemas" / (n + ".json")).read_text()) for n in ("surrogate_decision", "job_result")}


def card_text(name):
    return (CARDS_DIR / (name + ".md")).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["KARAKA", "PARIKSAKA", "ADHIKARIN", "OWNER_SURROGATE"])
def test_dispatched_job_cards_require_foreground_commands(name):
    text = flat(card_text(name))
    assert "Never run a command in the background" in text
    assert "never end a turn while a command is still running" in text
    assert "foreground with an explicit timeout" in text
    assert "Split long suites" in text


def flat(text):
    return " ".join(text.split())


def line_ids(text):
    """the ids of a card's own rule lines, in order ('- BS-01 …')"""
    return [m.group(1) for m in re.finditer(r"(?m)^- ((?:BS|BR|FB|FV|OS|KA|PA|AD)-\d{2}) ", text)]


def rule_line(text, needle):
    """the one rule line of a card that contains `needle`"""
    hits = [ln for ln in text.splitlines() if ln.startswith("- ") and needle in ln]
    assert len(hits) == 1, "%d rule lines contain %r" % (len(hits), needle)
    return hits[0]


# --------------------------------------------------------------------------------------------------------------
# the card set and its front matter
# --------------------------------------------------------------------------------------------------------------
def test_the_card_set_is_exactly_the_eight_roles():
    found = sorted(p.stem for p in CARDS_DIR.glob("*.md"))
    assert found == sorted(ALL_PREFIX), "only the eight role cards; no coverage matrix (A8 §4)"


@pytest.mark.parametrize("name", sorted(ALL_PREFIX))
def test_front_matter_and_line_ids(name):
    text = card_text(name)
    head = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert head, "no front matter"
    meta = dict(ln.split(": ", 1) for ln in head.group(1).splitlines())
    assert list(meta) == ["card", "version", "role", "model", "effort", "plan", "status"]
    assert meta["card"] == name and meta["version"] == "2.7" and meta["plan"] == PLAN.name
    assert text[head.end():].split("\n", 1)[0] == HEADER, "the A8 authority line is the first body line"
    ids = line_ids(text)
    numbers = [int(i.split("-")[1]) for i in ids]
    assert ids and numbers[0] == 1 and numbers == sorted(set(numbers)), ids
    retired = {"%s-%02d" % (ALL_PREFIX[name], n) for n in RETIRED.get(ALL_PREFIX[name], ())}
    assert not retired & set(ids), "a retired CLAUDE.md-restating line is back: %s" % sorted(retired & set(ids))
    assert {m.group(1) for m in ID.finditer(text)} == {ALL_PREFIX[name]}, "a card cites only its own line ids"


# --------------------------------------------------------------------------------------------------------------
# the byte target (the token-measurement binding to TOKEN_MEASUREMENT.json is retired with the qualification
# machinery, A8 §4; the record stays as history). The A8 header line is not counted against a card's budget.
# --------------------------------------------------------------------------------------------------------------
def card_bytes(name):
    return (CARDS_DIR / (name + ".md")).stat().st_size - len((HEADER + "\n").encode("utf-8"))


@pytest.mark.parametrize("name", sorted(PREFIX))
def test_b_card_is_within_the_byte_target(name):
    size = card_bytes(name)
    cap = 5200 if name == "OWNER_SURROGATE" else BYTE_CAP  # R19a job's explicit surrogate-only limit
    assert size <= cap, "%s is %d bytes" % (name, size)


@pytest.mark.parametrize("name", sorted(CAMPAIGN_PREFIX))
def test_b_campaign_card_is_within_the_accepted_byte_proxy(name):
    assert card_bytes(name) <= CAMPAIGN_BYTE_CAP


def campaign_boundary_problems(text, rule):
    line = rule_line(text, rule)
    if rule == "PA-05":
        command = ("python3 -B -m pytest <packet test paths> -p no:cacheprovider "
                   "--basetemp=<absolute job scratch>/pytest")
        return [] if command in line and "paths written out" in line else ["invalid pytest invocation"]
    # KA-04: the builder has no production access, and no KARAKA line may ask the builder to do the production readback itself
    builder_readback = re.search(r"(?i)(?:perform(?:s)?|run|verify|do) (?:the )?production readback", text)
    return [] if "production access" in line and not builder_readback else [
        "builder production boundary absent or contradictory"]


def test_cr04_campaign_verifier_invokes_pytest_and_rejects_the_broken_command():
    text = card_text("PARIKSAKA")
    assert campaign_boundary_problems(text, "PA-05") == []
    assert campaign_boundary_problems(text.replace("-m pytest ", "", 1), "PA-05")


def test_cr01_builder_has_no_production_access_and_rejects_builder_production_duty():
    text = card_text("KARAKA")
    assert campaign_boundary_problems(text, "KA-04") == []
    line = rule_line(text, "KA-04")
    assert campaign_boundary_problems(text.replace(line, line.replace("production access/", "", 1)), "KA-04")
    assert campaign_boundary_problems(text.replace(line, line + " Perform production readback yourself."), "KA-04")


def test_c_the_coverage_matrices_stay_retired():
    """A8 §4: the COVERAGE matrices and the cards' CLAUDE.md restatements are retired; CLAUDE.md loads in every job."""
    assert not list(CARDS_DIR.glob("COVERAGE*")), "a coverage matrix is back"
    for name, prefix in CAMPAIGN_PREFIX.items():
        assert not {"%s-%02d" % (prefix, n) for n in RETIRED[prefix]} & set(line_ids(card_text(name))), name


# --------------------------------------------------------------------------------------------------------------
# record templates: a tiny parser for the cards' JSON-like shorthand
# --------------------------------------------------------------------------------------------------------------
def _string(s, i):
    j = s.index('"', i + 1)
    return s[i + 1:j], j + 1


def _closing(s, i):
    """index just past the bracket that closes s[i], quotes respected"""
    pairs, stack, quoted = {"{": "}", "[": "]"}, [], False
    for j in range(i, len(s)):
        c = s[j]
        if c == '"':
            quoted = not quoted
        elif not quoted and c in pairs:
            stack.append(pairs[c])
        elif not quoted and stack and c == stack[-1]:
            stack.pop()
            if not stack:
                return j + 1
    raise ValueError("unbalanced template: " + s[i:i + 40])


def _value(s, i):
    if s[i] == '"':
        text, i = _string(s, i)
        return ("str", text), i
    if s[i] == "{":
        return _object(s, i)
    if s[i] == "[":
        end = _closing(s, i)
        if s[i + 1] == "{":
            inner, j = _object(s, i + 1)
            assert j == end - 1, "an array template holds one object"
            return ("arr", inner), end
        return ("free", s[i:end]), end
    j = i
    while s[j] not in ",}":
        j += 1
    return ("raw", s[i:j]), j


def _object(s, i):
    end = _closing(s, i)
    if s[i + 1] != '"':
        return ("free", s[i:end]), end
    keys, i = {}, i + 1
    while True:
        key, i = _string(s, i)
        assert key not in keys, "duplicate key " + key
        if s[i] == ":":
            keys[key], i = _value(s, i + 1)
        else:
            keys[key] = ("bare", None)
        if s[i] == ",":
            i += 1
        else:
            assert s[i] == "}" and i + 1 == end, "unexpected %r in a template" % s[i]
            return ("obj", keys), end


def template(text, opening):
    """the one template in `text` that starts with `opening`, parsed"""
    assert text.count(opening) == 1, "%d templates start with %s" % (text.count(opening), opening)
    node, _ = _object(text, text.index(opening))
    return node


def fill(node, sample):
    """a document with exactly the template's keys and the sample's values (an unknown key gets a filler, so the
    schema — not this test — decides whether the card may carry it)"""
    kind, body = node
    if kind == "obj":
        return {k: fill(v, sample.get(k, "filler") if isinstance(sample, dict) else "filler") for k, v in body.items()}
    if kind == "arr":
        return [fill(body, x) for x in sample]
    return sample


def alternatives(node, key):
    kind, text = node[1][key]
    assert kind == "str"
    return text.split("|")


# --------------------------------------------------------------------------------------------------------------
# (d) the surrogate's decision record line
# --------------------------------------------------------------------------------------------------------------
C, D = "e" * 40, "5" * 64
SD_OPEN = '{"id":"SD-'


def routine():
    return {"id": "SD-20261012T010203Z-1", "awaiting": "AW-20261012T010000Z-worktree-disposition", "class": "routine",
            "state": "EXECUTED", "decision": "remove the two merged copies", "rationale": "both are pushed and merged",
            "evidence": ["/Users/Dev/kalayantra/run/awaiting/AW-20261012T010000Z-worktree-disposition.json"],
            "target": {"paths": ["/x/a", "/x/b"]}, "authority": {"source_commit": C, "entrypoints_digest": D},
            "notification": {"submitted": True, "ts": "2026-10-12T01:02:10Z"}, "veto_deadline": None,
            "effective_at": "2026-10-12T01:02:05Z", "by": "kalayantra-owner-surrogate", "session": "surrogate-1"}


def veto(fingerprint, ts="2026-10-12T01:02:10Z", minutes=30):
    at = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(minutes=minutes)
    return dict(routine(), **{"class": "veto", "state": "PENDING_VETO", "decision": "raise capacity",
                              "target": {"kind": "capacity", "builders": 8, "verifiers": 4, "fingerprint": fingerprint},
                              "notification": {"submitted": True, "ts": ts},
                              "veto_deadline": at.strftime("%Y-%m-%dT%H:%M:%SZ"), "effective_at": None})


def hard_stop():
    return dict(routine(), **{"class": "hard_stop", "state": "PROPOSED", "decision": "not decided: owner-only",
                              "notification": {"submitted": False, "ts": None}, "effective_at": None})


def cli_fingerprint(tmp_path, target):
    """the target fingerprint exactly as the card tells the surrogate to obtain it"""
    card = card_text("OWNER_SURROGATE")
    assert "`python3 <fleet>/kyveto.py fingerprint --target <file>`" in card
    run = tmp_path / "ky" / "run"
    run.mkdir(parents=True, exist_ok=True)
    file = tmp_path / "target.json"
    file.write_text(json.dumps(target))
    r = subprocess.run([sys.executable, "-B", str(FLEET / "kyveto.py"), "fingerprint", "--target", str(file)],
                       capture_output=True, text=True, timeout=60,
                       env={"KY_ROOT": str(tmp_path / "ky"), "KY_RUN": str(run), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)})
    return r.returncode, r.stdout.strip()


def test_d_the_record_line_validates_for_a_routine_a_veto_and_a_hard_stop(tmp_path):
    node = template(card_text("OWNER_SURROGATE"), SD_OPEN)
    schema = SCHEMAS["surrogate_decision"]
    code, fingerprint = cli_fingerprint(tmp_path, {"kind": "capacity", "builders": 8, "verifiers": 4})
    assert code == 0 and re.fullmatch(r"[0-9a-f]{64}", fingerprint)
    for sample in (routine(), veto(fingerprint), hard_stop()):
        doc = fill(node, sample)
        assert doc == sample, "the card's record line and the schema's required keys differ"
        assert kyschema.validate(schema, doc) == [], sample["class"]
    assert alternatives(node, "class") == schema["properties"]["class"]["enum"]
    assert alternatives(node, "state") == schema["properties"]["state"]["enum"]
    assert node[1]["by"] == ("str", "kalayantra-owner-surrogate")
    assert set(node[1]["authority"][1]) == {"source_commit", "entrypoints_digest"}
    assert set(node[1]["notification"][1]) == {"submitted", "ts"}


def test_d_a_record_line_with_a_missing_or_foreign_key_is_refused(tmp_path):
    card, schema = card_text("OWNER_SURROGATE"), SCHEMAS["surrogate_decision"]
    assert card.count(',"session"}') == 1 and card.count('"by":') == 1
    without = fill(template(card.replace(',"session"}', "}"), SD_OPEN), routine())
    assert "session" not in without and kyschema.validate(schema, without), "a record line without `session` must be refused"
    extra = fill(template(card.replace('"by":', '"note","by":'), SD_OPEN), routine())
    assert "note" in extra and kyschema.validate(schema, extra), "a record line with an unknown key must be refused"
    assert kyschema.validate(schema, dict(hard_stop(), state="EFFECTIVE")), "a hard stop is recorded PROPOSED only"
    assert kyschema.validate(schema, dict(veto("7" * 64), target={"kind": "capacity"})), "a veto target needs its fingerprint"
    assert kyschema.validate(schema, dict(routine(), veto_deadline="2026-10-12T01:32:10Z")), "routine carries no deadline"
    assert cli_fingerprint(tmp_path, {"kind": "raise_everything"})[0] == 1, "an unknown target kind gets no fingerprint"


def test_d_the_record_line_keeps_the_agent_files_format():
    card = template(card_text("OWNER_SURROGATE"), SD_OPEN)
    agent = template(AGENT.read_text(encoding="utf-8").replace("\n", ""), SD_OPEN)
    assert list(card[1]) == list(agent[1]), "same keys, same order"
    for key in ("class", "state"):
        assert alternatives(card, key) == alternatives(agent, key)
    for key in ("authority", "notification"):
        assert list(card[1][key][1]) == list(agent[1][key][1])
    assert card[1]["by"] == agent[1]["by"]
    log = "/Users/Dev/kalayantra/run/DECISIONS_SURROGATE.jsonl"
    assert log in card_text("OWNER_SURROGATE") and log in AGENT.read_text(encoding="utf-8")


# --------------------------------------------------------------------------------------------------------------
# (e) the job-result line of every card
# --------------------------------------------------------------------------------------------------------------
JR_OPEN = '{"schema":"ky.job_result/1"'
PUSHES = {"BOOTSTRAP": True, "FIXTURE_BUILDER": True, "BOOTSTRAP_REVIEWER": False, "FIXTURE_VERIFIER": False,
          "OWNER_SURROGATE": False}


def result(status, pushes):
    done = status == "done"
    return {"schema": "ky.job_result/1", "job_id": "J-20261012T010203Z-b1", "item": "KV3-B-KYLOCK", "status": status,
            "branch": "kalayantra/kv3-b-kylock" if pushes else None, "head_sha": "1" * 40 if pushes and done else None,
            "pr_number": 3501 if pushes and done else None,
            "tests": [{"cmd": "python3 -B -m pytest fleet/tests/test_kylock.py -q", "exit": 0 if done else 1,
                       "summary": "14 passed" if done else "2 failed"}],
            "blocked_reason": "freeze: fleet/x.py" if status == "blocked" else None, "notes": "",
            "proposed_verdict": {"verdict": "ACCEPTED", "head": "1" * 40, "findings": []}}


@pytest.mark.parametrize("name", sorted(PREFIX))
def test_e_the_job_result_line_validates(name):
    text, schema = card_text(name), SCHEMAS["job_result"]
    assert "`$JOB_SCRATCH/result.json`" in text
    node = template(text, JR_OPEN)
    assert set(schema["required"]) <= set(node[1]), "the card's result line omits a required key"
    assert alternatives(node, "status") == schema["properties"]["status"]["enum"]
    assert node[1]["schema"] == ("str", schema["properties"]["schema"]["const"])
    for status in ("done", "blocked", "failed"):
        doc = fill(node, result(status, PUSHES[name]))
        assert kyschema.validate(schema, doc) == [], (name, status)
    if not PUSHES[name]:
        assert re.search(r"`head_sha`(?: and `pr_number`)? null", text), "a job that pushes nothing reports head_sha null"
    assert ("proposed_verdict" in node[1]) == (name == "BOOTSTRAP_REVIEWER")


def test_e_a_job_result_line_with_a_missing_or_foreign_key_is_refused():
    text, schema = card_text("BOOTSTRAP"), SCHEMAS["job_result"]
    assert ',"notes"}' in text
    without = fill(template(text.replace(',"notes"}', "}"), JR_OPEN), result("done", True))
    assert kyschema.validate(schema, without)
    extra = fill(template(text.replace(',"notes"}', ',"notes","verdict"}'), JR_OPEN), result("done", True))
    assert kyschema.validate(schema, extra)
    assert kyschema.validate(schema, dict(result("blocked", True), blocked_reason=None)), "blocked needs its reason"


# --------------------------------------------------------------------------------------------------------------
# (f) what no card may contain
# --------------------------------------------------------------------------------------------------------------
def forbidden(text):
    out = []
    if re.search(r"\bL[0-5]\b", text):
        out.append("an internal layer number")
    if re.search(r"(?i)\b(see|per|as in|refer to)\s+(the\s+)?(root\s+)?`?CLAUDE\.md", text):
        out.append("a reference to CLAUDE.md in place of a rule")
    if "/Users/Dev/kalayantra/fleet_live/kynotify.sh" in text:
        out.append("a hard-coded installed notifier path")
    return out


@pytest.mark.parametrize("name", sorted(PREFIX))
def test_f_no_card_carries_forbidden_content(name):
    assert forbidden(card_text(name)) == []


def test_f_the_forbidden_content_check_can_fail():
    assert forbidden("rows of L1 facts") == ["an internal layer number"]
    assert forbidden("Layers L0–L5") == ["an internal layer number"]
    assert forbidden("For the build standards see CLAUDE.md §N.") == ["a reference to CLAUDE.md in place of a rule"]
    assert forbidden("bash /Users/Dev/kalayantra/fleet_live/kynotify.sh x") == ["a hard-coded installed notifier path"]
    assert forbidden("Precedence: root CLAUDE.md §I/§N > owner decisions; KL01 and XL5X are not layers") == []


# --------------------------------------------------------------------------------------------------------------
# C-01 (ruling R1): where the scratch paths come from, and what an unset one means
# --------------------------------------------------------------------------------------------------------------
R1_RULE = ("`JOB_SCRATCH` and `KY_SCRATCH` come from the job environment. If either is unset or not an absolute "
           "path: stop,")
R1_TAIL = "write nothing; never expand an unset variable."


def scratch_rule_problems(text):
    body, out = flat(text), []
    if R1_RULE not in body or R1_TAIL not in body:
        return ["the scratch-path rule of ruling R1 is absent"]
    rule_at = body.index(R1_RULE)
    for use in ("$JOB_SCRATCH", "$KY_SCRATCH"):
        if use in body and body.index(use) < rule_at:
            out.append(use + " is used before the rule that guards it")
    if "blocked" not in body[rule_at:body.index(R1_TAIL, rule_at)]:
        out.append("an unset scratch path is not reported as blocked")
    return out


@pytest.mark.parametrize("name", sorted(PREFIX))
def test_c01_every_card_states_the_scratch_rule_before_its_first_use(name):
    assert scratch_rule_problems(card_text(name)) == []


def test_c01_the_scratch_rule_check_can_fail():
    text = card_text("BOOTSTRAP")
    line = rule_line(text, "come from the job environment")
    assert scratch_rule_problems(text.replace(line + "\n", "")) == ["the scratch-path rule of ruling R1 is absent"]
    moved = text.replace(line + "\n", "") + line + "\n"
    assert "$JOB_SCRATCH is used before the rule that guards it" in scratch_rule_problems(moved)
    assert scratch_rule_problems(text.replace("never expand an unset variable", "do your best")) != []


# --------------------------------------------------------------------------------------------------------------
# C-02 (ruling R3), N-03, N-04: the surrogate's notification, veto window, targets and merges
# --------------------------------------------------------------------------------------------------------------
def test_c02_submitted_is_true_only_on_the_exact_stdout_line_and_the_window_starts_after_it():
    card = flat(card_text("OWNER_SURROGATE"))
    assert "`notification.submitted` is true only when its stdout is exactly `notify=submitted`" in card
    assert "`notification.ts` is the UTC time taken after the call" in card
    minutes = re.search(r"`veto_deadline` = that ts \+ (\d+) min", card)
    assert minutes and int(minutes.group(1)) * 60 == kyveto.VETO_WINDOW_S, "the card's window is the handler's window"
    assert 'bash <notifier> "<SD id>: <one line>"' in card, "the message starts with the SD id"
    assert "the notifier path comes from the job input" in card and "never a hard-coded path" in card


def test_c02_a_record_built_by_the_cards_rule_has_the_handlers_full_window_and_a_shorter_one_does_not():
    def window(doc):
        when = [datetime.datetime.strptime(doc[k] if k == "veto_deadline" else doc["notification"]["ts"],
                                           "%Y-%m-%dT%H:%M:%SZ") for k in ("veto_deadline", "ts")]
        return (when[0] - when[1]).total_seconds()

    assert window(veto("7" * 64)) >= kyveto.VETO_WINDOW_S
    assert window(veto("7" * 64, minutes=29)) < kyveto.VETO_WINDOW_S        # "now + 30 min" taken before the call


def card_reads_submitted(stdout):
    """the card's rule, as code: true only when the notifier's stdout is exactly the line `notify=submitted`"""
    return stdout in ("notify=submitted", "notify=submitted\n")


def test_c02_the_cards_rule_against_the_notifier_on_disk(tmp_path):
    """Only a submitted notification prints the exact line; a dry or failed one (exit 0 all the same) never reads
    as submitted. The notifier is the reviewed staged script; osascript is always an absolute fake."""
    run = tmp_path / "run"
    run.mkdir()
    sd = "SD-20261012T010203Z-1"
    for extra, expected in (({"KY_NOTIFY_DRY": "1"}, "dry"), ({"KY_OSASCRIPT": "/usr/bin/false"}, "failed"),
                            ({"KY_OSASCRIPT": "/usr/bin/true"}, "submitted")):
        env = dict({"KY_ROOT": str(tmp_path), "KY_RUN": str(run), "PATH": "/usr/bin:/bin", "HOME": str(tmp_path)}, **extra)
        r = subprocess.run(["/bin/bash", str(FLEET / "kynotify.sh"), sd + ": capacity 6 → 8"],
                           capture_output=True, text=True, timeout=30, env=env)
        assert r.returncode == 0 and r.stdout == "notify=%s\n" % expected, (extra, r.stdout, r.stderr)
        assert card_reads_submitted(r.stdout) == (expected == "submitted")
        last = (run / "JOURNAL_COCKPIT.md").read_text(encoding="utf-8").splitlines()[-1]
        assert (" %s: " % sd) in last and last.endswith("[notify=%s]" % expected), last
    assert not card_reads_submitted("kynotify: journal=ok notify=submitted\n"), "a line that merely contains it is not it"
    assert not card_reads_submitted("notify=submitted\nnotify=failed\n")


def test_n03_the_card_names_the_handlers_target_kinds_and_records_a_hard_stop_as_proposed():
    card = card_text("OWNER_SURROGATE")
    veto_rule = rule_line(card, "Veto classes")
    kinds = set(re.findall(r"`([a-z_]+)`", veto_rule.split(":")[0])) - {"kind"}
    assert kinds == set(kyveto.REGISTRY), "the card's kinds are exactly the handler's registry"
    assert "`PENDING_VETO`" in veto_rule and "no `ky decide`" in veto_rule and "never by hand" in veto_rule
    stop = rule_line(card, "Hard stops")
    assert "`hard_stop`" in stop and "`PROPOSED`" in stop and "never decide" in stop


def test_n04_the_surrogate_never_merges_itself():
    line = rule_line(card_text("OWNER_SURROGATE"), "`gh pr merge`")
    assert re.search(r"[Nn]ever run `gh pr merge` or any merge yourself", line)
    assert "the deterministic controller executes" in line


# --------------------------------------------------------------------------------------------------------------
# C-03, N-06: the verifier's write list and caches; the fixture isolation variables
# --------------------------------------------------------------------------------------------------------------
def write_list_problems(text):
    line = rule_line(text, "Write only")
    allowed = re.findall(r"`(\$[A-Z_]+)[^`]*`", line.split("Never")[0])
    target = re.search(r"`(\$JOB_SCRATCH/result\.json)`", text)
    if not target:
        return ["no result file path"]
    return [] if any(target.group(1).startswith(root) for root in allowed) else [
        "the result file is outside the write list %s" % allowed]


@pytest.mark.parametrize("name", ["FIXTURE_VERIFIER", "BOOTSTRAP_REVIEWER"])
def test_c03_the_result_file_is_inside_the_permitted_write_list(name):
    assert write_list_problems(card_text(name)) == []


def test_c03_the_round_one_write_list_is_refused():
    old = ("- FV-08 Write only to: the declared evidence path, caches, `$TMPDIR`, your slot database. Never to shared "
           "control state (`$KY_RUN` beyond your evidence, the installed trees, another job's files).\n"
           "- FV-20 Last act: `$JOB_SCRATCH/result.json` = `{}`.\n")
    assert write_list_problems(old) == ["the result file is outside the write list ['$TMPDIR']"]


def test_n06_fixture_cards_name_the_plans_tracker_variables_and_the_verifier_keeps_caches_out():
    b3 = re.search(r"`PRAVAHA_([A-Z_/]+)`", next(ln for ln in PLAN.read_text(encoding="utf-8").splitlines()
                                                 if ln.startswith("| B-3 |")))
    names = ["PRAVAHA_" + part for part in b3.group(1).split("/")]
    assert len(names) == 7
    for card in ("FIXTURE_BUILDER", "FIXTURE_VERIFIER"):
        check = rule_line(card_text(card), "check and record")
        named = set(re.findall(r"`(PRAVAHA_[A-Z_]+)`", check))
        for group in re.findall(r"`PRAVAHA_\{([A-Z_,]+)\}`", check):          # `PRAVAHA_{A,B}` names A and B
            named |= {"PRAVAHA_" + part for part in group.split(",")}
        assert [n for n in names if n not in named] == [], card
        assert "8767" in check and "`$KY_SCRATCH/fixture/`" in check and "`git remote get-url origin`" in check, card
    for card in ("FIXTURE_VERIFIER", "BOOTSTRAP_REVIEWER"):
        text = flat(card_text(card))
        assert "python3 -B -m pytest" in text and "-p no:cacheprovider" in text, card
        assert "--basetemp=$JOB_SCRATCH/pytest" in text, card
        assert "`git status --porcelain`" in text, card


# --------------------------------------------------------------------------------------------------------------
# N-05: a credential check that prints names and never a value
# --------------------------------------------------------------------------------------------------------------
NAMES_ONLY = re.compile(r'`(python3 -c "import os;print\([^`]+)`')
ENV_CHECKERS = ["FIXTURE_BUILDER"]      # the one role no reviewed launcher yet guards (kyjob.sh is a B-1 deliverable)


@pytest.mark.parametrize("name", ENV_CHECKERS)
@pytest.mark.parametrize("shell", ["/bin/sh", "/bin/zsh", "/bin/bash"])
def test_n05_the_credential_check_prints_names_and_never_a_value(name, shell):
    if not os.path.exists(shell):
        pytest.skip(shell + " is not on this host")
    found = NAMES_ONLY.findall(card_text(name))
    assert len(found) == 1, "one names-only command per card"
    base = {"PATH": os.path.dirname(sys.executable) + ":/usr/bin:/bin", "HOME": "/nonexistent", "KY_ROOT": "/x"}
    dirty = dict(base, DATABASE_URL="postgres://value-one", KY_B1_DATABASE_URL="postgres://value-two",
                 PGPASSWORD="fake-three", ANTHROPIC_API_KEY="value-four", NOT_A_DATABASE_URL_NAME="value-five",
                 MULTI_LINE="first\nPGPASSWORD=PLACEHOLDER\nvalue-seven")
    r = subprocess.run([shell, "-c", found[0]], capture_output=True, text=True, timeout=30, env=dirty)
    assert r.returncode == 0, r.stderr
    assert sorted(ast.literal_eval(r.stdout)) == ["ANTHROPIC_API_KEY", "DATABASE_URL", "KY_B1_DATABASE_URL", "PGPASSWORD"]
    assert "value-" not in r.stdout + r.stderr
    assert "fake-" not in r.stdout + r.stderr
    assert "PLACEHOLDER" not in r.stdout + r.stderr
    clean = subprocess.run([shell, "-c", found[0]], capture_output=True, text=True, timeout=30, env=base)
    assert clean.stdout.strip() == "[]"


def test_n05_only_the_cards_that_give_the_names_only_command_ask_for_an_environment_check():
    for name in PREFIX:
        text = card_text(name)
        assert ("credential-in-env" in text) == (name in ENV_CHECKERS) == bool(NAMES_ONLY.search(text)), name


def dump_invitations(text):
    """every mention of a command that lists the environment whose own sentence does not forbid it"""
    out = []
    for line in text.splitlines():
        for m in re.finditer(r"`(env|printenv|set|export -p)`", line):
            sentence = line[:m.start()].rsplit(". ", 1)[-1]
            if not re.search(r"(?i)\bnever\b", sentence):
                out.append(m.group(0))
    return out


def test_n05_a_card_names_an_environment_dump_only_to_forbid_it():
    seen = 0
    for name in PREFIX:
        text = card_text(name)
        seen += len(re.findall(r"`(?:env|printenv|set)`", text))
        assert dump_invitations(text) == [], name
    assert seen >= 9, "three cards name the three commands, each time to forbid them"
    assert dump_invitations("- X-01 Never dump the environment (`env`). Check with `env` or `printenv`.") == ["`env`", "`printenv`"]
    assert dump_invitations("- X-01 If `DATABASE_URL` is set (see `env`), stop.") == ["`env`"]


# --------------------------------------------------------------------------------------------------------------
# R7: the bootstrap reviewer card says what the configuration is, and asks only for commands it permits
# --------------------------------------------------------------------------------------------------------------
def test_r7_the_reviewer_card_states_its_boundary_and_its_duties():
    card = flat(card_text("BOOTSTRAP_REVIEWER"))
    for phrase in ("read-only by configuration, not sandboxed", "the repository", "the installed trees",
                   "`/Users/Dev/kalayantra`", "push", "fetch", "network", "inputs, never evidence",
                   "named mutations yourself", "what code path would have to run — and fail",
                   "never publish", "merge"):
        assert phrase in card, phrase


def bash_rule(rule):
    m = re.fullmatch(r"Bash\((.*)\)", rule)
    return m.group(1) if m else None


def permitted(command, allow, deny):
    """the reviewer configuration's own semantics, as far as a prefix rule goes: an allow rule 'x:*' or 'x*'
    permits commands starting with x; a deny rule is a glob over the whole command and wins"""
    if any(fnmatch.fnmatchcase(command, pattern) for pattern in deny):
        return False
    return any(command == a or command.startswith(a + " ") for a in (re.sub(r"[:]?\*$", "", p).strip() for p in allow))


def test_r7_every_command_the_reviewer_card_asks_for_is_permitted_by_the_reviewer_configuration():
    config = json.loads((FLEET / "templates" / "LAUNCH_CONFIG.bootstrap-reviewer.json").read_text())
    flag = next(f for f in config["extra_flags"] if f.startswith("--allowedTools="))
    allow = [r for r in map(bash_rule, flag.split("=", 1)[1].split(",")) if r]
    deny = [r for r in map(bash_rule, config["disallowed_tools"]) if r]
    commands = [c for c in re.findall(r"`([^`]+)`", card_text("BOOTSTRAP_REVIEWER"))
                if re.match(r"(git|python3|shasum|gh|curl|ky) ", c)]
    assert len(commands) >= 4
    for command in commands:
        assert permitted(command, allow, deny), "the reviewer configuration refuses: " + command
    assert not permitted("git rev-parse HEAD", allow, deny), "the check can fail: rev-parse is not allow-listed"
    assert permitted("git log -1 --format=%H", allow, []) and not permitted("git log --output=x", allow, ["*--output*"])


# --------------------------------------------------------------------------------------------------------------
# N-08: the KU bindings say who enforces them today, bind the added components, and keep the clauses' bytes
# --------------------------------------------------------------------------------------------------------------
KU_SHA = {"KU-01": "bb3670a36b9f2c101c21b9c2e246c218495ff90efa177b8eefb3f0a2328f5936",
          "KU-02": "196a7f9ca1d185efb40924df68695ce917ee07b37c1bbbe60f14c6d3b9fc74aa",
          "KU-03": "e0de304ed2e91a63225b0bc38d65fcf2fdceffa8ca48c1d3427c839cc96ddc8b"}


def test_n08_ku_bindings_name_their_present_enforcer_and_the_added_components():
    bind = json.loads((FLEET / "templates" / "ku_bindings.json").read_text(encoding="utf-8"))
    rule = bind["rule"]
    assert "kypacket.py" in rule and "B-1 deliverable" in rule and "until it exists" in rule and "by hand" in rule
    for ku, sha in KU_SHA.items():
        clause = bind["clauses"][ku]
        assert clause["text_sha256"] == sha == hashlib.sha256(clause["text"].encode()).hexdigest(), ku
    assert {"tracker-semantics", "preflight-v3", "kyverdicts"} <= set(bind["clauses"]["KU-01"]["required_in"])
    assert {"local-db", "kylock", "finalize-v3", "kyloop-crash-cleanup", "dispatcher-ready-receipts"} <= set(
        bind["clauses"]["KU-02"]["required_in"])
    md = (FLEET / "templates" / "KU_REPLACEMENTS_v2_7.md").read_text(encoding="utf-8")
    for ku, clause in bind["clauses"].items():
        section = md.split("## " + ku)[1].split("\n## ")[0]
        listed = re.findall(r"`([^`]+)`", section.split("**Packets (B-1 components):**")[1].split("\n")[0])
        assert listed == clause["required_in"], ku + ": the template and the bindings name different components"
        assert len(set(listed)) == len(listed)
    assert "by hand" in md.split("\n# ")[0], "the template's own rule says who checks the hashes today"
