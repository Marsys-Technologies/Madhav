---
artifact: REPIN_TOOL_THREAT_LIST
version: "1.0"
status: WORKING — written before the next Codex pass (steward ST-REPIN-CODEX-V18); checked against tool head 4061d3608
date: 2026-10-04
author: Stream B (Śāstra), session madhav-8b
tool: platform/python-sidecar/scripts/gochara/repin_dasha_contract.py (improved branch pravaha/b6-am10-repin-tool-declared-shape)
changelog:
  - "1.0 (2026-10-04): first version."
---

# AM-10 re-pin tool — threat list

Every pass so far found a NEW family because the checking was reactive. This list is the whole surface: every input, every output, every write, and what must hold for each. "Check" names the code and the regression that pins it.

## 1. Inputs
| id | input | what must hold | check |
|---|---|---|---|
| I1 | CLI strings (every flag value) | strict UTF-8 text, no NUL, never echoed in an error | `cli_string_problems` (first thing after argparse); `test_p1_4_*` |
| I2 | `--chart-id`, a W0 file's `chart_id`, a capture's `chart_id` | canonical lower-case hyphenated UUID text; compared only after that | `chart_id_problem` in `_main_impl`, `_import_w0`, `validate_capture`; `test_v18_4_*` |
| I3 | `--new-build-id` | one canonical UUID form before any comparison, any use in a file name | `_mode_error` (canon_uuid); tests of v1.4+ |
| I4 | `--settled-notice` JSON | strict JSON; exact key set; finite numeric shift/tolerance; refused fields named | `load_notice`, `strict_json_loads`; v1.4–1.6 tests |
| I5 | `--rulings` JSON | strict JSON; exact structure; every entry `path:line`; no entry in both lists | `validate_rulings`; v1.5 tests |
| I6 | `--old-rows` capture / a W0 file | strict JSON; checksum over identity + selection + rows + natal AND schema-strict rows and natal BEFORE any coercion (integer level, UUIDs, offset instants, boolean flags, finite decimal longitude in [0,360)) | `validate_capture`, `strict_rows_problems`, `strict_natal_problems`; `test_p1_1_*`, `test_v18_3_*` |
| I7 | database rows (new build, old build when no file) | read-only snapshot; the same row/natal schema; exactly one build; 45+1 partitions; verifier-predicate mirror | `fetch_*`, `read_levels`, `preflight_problems`; v1.2–1.4 tests |
| I8 | repository files read (permission.py, verifier, tests/l3/**, wide scan roots) | UTF-8 text; non-files skipped; offsets kept | `scan_test_spans`, `scan_wide_literals`; `test_p1_3_*` |
| I9 | environment (`DATABASE_URL`, `TZ`) | URL only from the environment, never printed; instants without an offset refused (never local time) | `_t`, `open_*_connection` |
| I10 | the forensic report | EXISTS and is NON-EMPTY only — and the report says so | `render` evidence line |

## 2. Outputs and writes
| id | write | what must hold | check |
|---|---|---|---|
| O1 | `--out` evidence | never the same file as any input, source, destination, another output (resolved path, symlink or hard link); with `--apply` written AFTER the apply, and a failed apply marks it `# !!! RE-PIN NOT APPLIED` | `io_collision_problems`; `test_v18_1_*`, `test_t_evidence_*` |
| O2 | `--capture-old` / `--capture-new` / `--w0-capture-out` | validated capture only (the loader's own validation, before the write); same collision rule | `validate_capture`, `io_collision_problems` |
| O3 | apply: permission.py, verifier pin, ruled tests/l3 lines, id rewrites | only the exact ruled spans of ruled lines change; every wrapped old id rewritten character for character; never a string replace over a line | `rewrite_spans`, `rewrite_wrapped_ids`; `test_p1_2_*` |
| O4 | apply: generated refusal test | written whole; an existing NON-identical file is refused (identical accepted); never rewritten by the id pass | `apply_repin`; `test_v18_2_*` |
| O5 | all writes | atomic per file (strict UTF-8, temp file + replace, destination a file in an existing directory); the complete plan validated BEFORE anything is reported or written; apply is all-or-restore (a failure restores written files and removes created ones) | `write_atomic`, `validate_write_plan`, `write_all_or_restore`; `test_p1_3_*`, `test_t_atomic_*` |

## 3. Invariants (what a CLEAN means)
| id | invariant | check |
|---|---|---|
| V1 | no write before the single validation phase ends; a STOP writes nothing (except the labelled failure evidence of a failed `--apply`) | `_main_impl` ordering tests |
| V2 | CLEAN is printed only if every named check passed; refusals that can be known before the report (rulings, destinations, collisions, existing generated test) are known before it | `stops`, `apply_repin(check_only=True)` runs the full plan |
| V3 | no top-level traceback: any exception is `STOP: <Type>: <reason>`, exit 3 | `main` |
| V4 | read-only database use: REPEATABLE READ READ ONLY, one snapshot, connection closed before a file is written | `_capture_build`, `open_*_connection` |
| V5 | the report claims only what was checked (forensic existence; Julian-day numbers not searched; wide scan report-only) | `render`, docstrings |
| V6 | no secret printed: the DSN, CLI values and file contents are never echoed | `cli_string_problems`, error paths |

## 4. Checked against the code on 2026-10-04 (head 4061d3608)
Found and fixed by this pass, beyond Codex's v1.8 four: (a) the id pass of the tests/l3 loop could rewrite the generated test's own OLD/NEW constants and listed it twice in the write plan (now skipped, tested); (b) `Decimal` accepted `1_0` and other lenient text (now a strict ASCII decimal pattern, tested); (c) a failed mid-apply left a half-re-pinned tree (all-or-restore, tested); (d) with `--apply` a CLEAN evidence file could stand beside a failed apply (written after the apply; failure header, tested); (e) the scans tried to read a directory named `*.py` (skipped). Residual, stated: the whole plan is validated before writes, but a concurrent change to the tree between validation and writing is not defended (single-operator tool); `os.replace` atomicity is per file, with restore on failure as the whole-plan mitigation.
