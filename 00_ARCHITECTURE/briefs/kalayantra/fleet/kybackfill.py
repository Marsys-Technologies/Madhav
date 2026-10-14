"""Fixed, write-free B-5 adapter to the repository governance schema validator.

(I) INTERPRETATION: schema_validator.py:1192-1250 has no backfill/banner CLI
mode. Invoke its existing detectors directly on the selected embedded blocks,
equivalent to --handshake and --close-checklist --session-open-for-close, plus
validate_session_log_entries and scope checks, as validate_backfill.py:47-85 in
X-20261013T111319Z-backfill did. No full-corpus green is claimed. The banner is
selected exactly inside §2 and bound to the close's measured CURRENT_STATE hash;
there is no repository detector for prose banner semantics. No report files or
temporary extracted YAML files are needed, including for kyfinal --dry.
"""
import importlib.util
import re
import sys
from pathlib import Path

STATE = "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
LOG = "00_ARCHITECTURE/SESSION_LOG.md"
VALIDATOR = "platform/scripts/governance/schema_validator.py"
HANDSHAKE = "00_ARCHITECTURE/briefs/kalayantra/sessions/SESSION_OPEN_kalayantra.yaml"


class Invalid(Exception):
    pass


def require(ok, detail):
    if not ok:
        raise Invalid(detail)


def named_file(repo, supplied, canonical, inputs):
    path = Path(supplied)
    if not path.is_absolute():
        path = repo / path
    require(path == repo / canonical, f"must select {canonical}")
    return inputs.file(path, "backfill_input"), path.read_text(encoding="utf-8")


def validate(repo, banner_file, session_log, entry_id, banner_id, inputs):
    state_ref, state = named_file(repo, banner_file, STATE, inputs)
    log_ref, log = named_file(repo, session_log, LOG, inputs)
    validator_ref = inputs.file(repo / VALIDATOR, "backfill_validator")
    loader_ref = inputs.file(repo / "platform/scripts/governance/_ca_loader.py", "backfill_validator")
    source_ref = inputs.file(repo / HANDSHAKE, "backfill_handshake")
    require(isinstance(entry_id, str) and re.fullmatch(r"[A-Za-z0-9_.\-]+", entry_id), "invalid entry identifier")
    require(isinstance(banner_id, str) and banner_id.strip(), "empty banner identifier")
    sections = state.split("## §2 — Canonical state block\n", 1)
    require(len(sections) == 2, "CURRENT_STATE canonical §2 missing")
    section = re.split(r"^## ", sections[1], maxsplit=1, flags=re.MULTILINE)[0]
    banners = re.findall(r"^> \*\*(.*?)\*\*\n(?:^>.*\n)*", section, re.MULTILINE)
    require(banners.count(banner_id) == 1, "named banner absent or ambiguous in CURRENT_STATE §2")
    # Require the named banner, rather than some other banner, to point to this entry.
    title = "> **" + banner_id + "**\n"
    block = section.split(title, 1)[1].split("\n\n", 1)[0]
    require("SESSION_LOG.md#" + entry_id in block, "banner does not bind the selected session entry")

    # Load the actual repository detector; never accept a supplied executable.
    spec = importlib.util.spec_from_file_location("ky_backfill_governance_validator", repo / VALIDATOR)
    validator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = validator  # dataclass registration needs its module.
    try:
        spec.loader.exec_module(validator)
    except (Exception, SystemExit) as e:
        raise Invalid(f"repository governance validator could not load ({type(e).__name__})") from e
    for name in ("validate_handshake_yaml", "validate_close_checklist_yaml", "validate_scope_boundary",
                 "validate_session_log_entries", "compute_exit_code", "_split_session_log_post_adoption"):
        require(callable(getattr(validator, name, None)), f"repository governance detector missing: {name}")
    require(validator._ADOPTION_MARKER_RE.search(log), "SESSION_LOG schema adoption marker missing")
    entries = [body for sid, body in validator._split_session_log_post_adoption(log) if sid == entry_id]
    require(len(entries) == 1, "named session entry absent or ambiguous")
    entry = entries[0]
    blocks = [m.group(1) for m in validator._YAML_FENCE_RE.finditer(entry)]
    require(len(blocks) == 2, "expected exactly one embedded open and close")
    opened, closed = [validator.yaml.safe_load(raw) for raw in blocks]
    require(isinstance(opened, dict) and set(opened) == {"session_open"} and
            isinstance(closed, dict) and set(closed) == {"session_close"}, "embedded open/body/close order invalid")
    require(isinstance(opened["session_open"], dict) and isinstance(closed["session_close"], dict),
            "embedded open/close must be mappings")
    require(opened["session_open"].get("session_id") == closed["session_close"].get("session_id") == entry_id,
            "embedded session identifiers disagree")
    require(blocks[0].rstrip() == (repo / HANDSHAKE).read_text(encoding="utf-8").rstrip(),
            "embedded campaign handshake differs from the named source handshake")
    close = closed["session_close"]
    for name in ("current_state_updated", "session_log_appended", "close_criteria_met"):
        require(close.get(name) is True, f"{name} must explicitly be true")
    touched = close.get("files_touched")
    require(isinstance(touched, list) and len(touched) == 2 and
            all(isinstance(row, dict) for row in touched) and {row.get("path") for row in touched} == {STATE, LOG},
            "close must name exactly the banner and session log artefacts")
    state_row = next(row for row in touched if row["path"] == STATE)
    require(state_row.get("sha256_after") == state_ref["sha256"], "close's banner artefact sha256 differs")
    checks = {
        "handshake": validator.validate_handshake_yaml(blocks[0]),
        "close_checklist": validator.validate_close_checklist_yaml(blocks[1]),
        "scope_boundary": validator.validate_scope_boundary(opened, closed),
        "session_entry": [v for v in validator.validate_session_log_entries(repo) if v.path == LOG + "#" + entry_id],
    }
    violations = [v for findings in checks.values() for v in findings]
    exit_code = validator.compute_exit_code(violations)
    require(exit_code == 0 and not violations,
            "governance validator rejected selected inputs: " + ", ".join(v.rule for v in violations))
    return {"schema": "ky.backfill_validation/2", "cwd": str(repo), "exit_code": exit_code,
            "validator": validator_ref, "validator_dependencies": [loader_ref],
            "artifacts": {"banner": dict(state_ref, identifier=banner_id),
                          "session_log": dict(log_ref, entry_id=entry_id), "handshake": source_ref},
            "checks": {name: {"violations": len(findings), "exit_code": validator.compute_exit_code(findings)}
                       for name, findings in checks.items()},
            "scope": "named B-5 banner, embedded campaign open/close, scope and session entry; not full corpus"}
